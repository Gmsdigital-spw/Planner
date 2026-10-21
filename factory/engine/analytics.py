"""Evidence-based analytics (add-on Phase 7).

Every number here was reported by a platform and carries its source and retrieval time. Missing is missing.
- `record()` stores metric rows (impressions, views, clicks, saves, conversions, sales) for a ref (a pin id,
  a post id, a listing id) tied to a plan/product. A zero is accepted only when the platform reported it
  (`measured`), exactly as Phase 6's record_results does.
- `ingest_pins()` / `ingest_social()` / `ingest_youtube()` turn the Factory's existing records (the artifact DB's
  `pins`, `social`, `modules/youtube/pipeline` docs, as the crews export them) into metric rows: the same
  availability rules the page uses (social `metrics.availability == "available"`, pins `stats`, episodes
  `stats.views`). Nothing is read over the network here; the crews hand the docs in.
- `compare()` groups known metrics by channel / product / campaign over a window and counts what is unknown.
- `recommend()` labels each line **demonstrated** (enough measured data) or **hypothesis** (thin or missing data)
  and says what to repeat, improve, pause or test. Correlation is never written as cause.
- `measure_plan()` folds the rows for a plan into `DistributionPlan.results` through Phase 6's record_results,
  so the funnel and next action stay consistent.
"""
from __future__ import annotations

import typing as t
from datetime import datetime, timedelta, timezone

from .contracts import DistributionPlan, new_id, now_iso
from .distribution import record_results
from .store import Store

KINDS = ("impressions", "views", "clicks", "saves", "conversions", "sales")
MIN_DEMONSTRATED = {"impressions": 500, "views": 500, "clicks": 25, "saves": 10, "sales": 1}


def record(store: Store, *, channel: str, ref: str, values: dict, source: str, plan_id: str | None = None, product_id: str | None = None,
           at: str | None = None, measured: t.Iterable[str] = ()) -> list[dict]:
    rows = []
    measured = set(measured)
    for k in KINDS:
        if k not in values or values[k] is None:
            continue
        v = float(values[k])
        if v == 0 and k not in measured:
            raise ValueError(f"{k}=0 must be a platform-reported zero (list it in measured); otherwise leave it out")
        row = {"id": new_id("met"), "at": at or now_iso(), "channel": channel, "ref": ref, "plan_id": plan_id, "product_id": product_id,
               "kind": k, "value": v, "source": source, "retrieved_at": now_iso()}
        store.put_metric(row)
        rows.append(row)
    return rows


# ---------------------------------------------------------------- ingest from the Factory's own records
def ingest_pins(store: Store, pins: list[dict], plan_lookup: t.Callable[[dict], tuple[str | None, str | None]] | None = None) -> int:
    """pins docs: {id, status, pinterestId, stats:{impressions, saves, pinClicks, outboundClicks, at}}."""
    n = 0
    for p in pins:
        st = p.get("stats")
        if not st or p.get("status") != "posted":
            continue
        vals = {"impressions": st.get("impressions"), "saves": st.get("saves"), "clicks": st.get("outboundClicks", st.get("pinClicks"))}
        measured = [k for k, v in vals.items() if v == 0]  # the Day Watch mirrors Pinterest's own numbers, zeros included
        plan_id, product_id = plan_lookup(p) if plan_lookup else (None, p.get("productId"))
        n += len(record(store, channel="pinterest", ref=str(p.get("pinterestId") or p.get("id")), values=vals, source="pinterest via Day Watch",
                        plan_id=plan_id, product_id=product_id, at=st.get("at"), measured=measured))
    return n


def ingest_social(store: Store, posts: list[dict], plan_lookup=None) -> int:
    """social docs: {id, platform, status, postUrl, metrics:{availability, views, reach, saves, clicks, retrievedAt}}."""
    n = 0
    for x in posts:
        m = x.get("metrics") or {}
        if x.get("status") != "posted" or m.get("availability") != "available":
            continue
        ch = "youtube_shop" if x.get("platform") == "youtube" else x.get("platform")
        vals = {"views": m.get("views"), "impressions": m.get("reach"), "saves": m.get("saves"), "clicks": m.get("clicks")}
        measured = [k for k, v in vals.items() if v == 0]
        plan_id, product_id = plan_lookup(x) if plan_lookup else (None, x.get("productId"))
        n += len(record(store, channel=str(ch), ref=str(x.get("postUrl") or x.get("id")), values=vals, source=f"{ch} via Make", plan_id=plan_id,
                        product_id=product_id, at=m.get("retrievedAt"), measured=measured))
    return n


def ingest_youtube(store: Store, pipeline: dict, plan_lookup=None) -> int:
    """modules/youtube/pipeline: {id: {videoId, stats:{views, likes, comments, at}}}."""
    n = 0
    for eid, p in pipeline.items():
        st = p.get("stats") or {}
        if not p.get("videoId") or st.get("views") is None:
            continue
        plan_id, product_id = plan_lookup(p) if plan_lookup else (None, None)
        n += len(record(store, channel="gmula", ref=str(p["videoId"]), values={"views": st["views"]}, source="YouTube API via Make", plan_id=plan_id,
                        product_id=product_id, at=st.get("at"), measured=["views"] if st["views"] == 0 else []))
    return n


# ---------------------------------------------------------------- compare + recommend
def compare(store: Store, by: str = "channel", days: int = 14, plan_lookup: dict[str, str] | None = None) -> dict:
    """Sum of known metrics per group plus which kinds are unknown. by: channel | product | plan."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds").replace("+00:00", "Z")
    rows = store.metrics(since=since)
    key = {"channel": "channel", "product": "product_id", "plan": "plan_id"}[by]
    groups: dict[str, dict] = {}
    for r in rows:
        g = groups.setdefault(str(r.get(key) or "unknown"), {k: None for k in KINDS} | {"refs": set(), "sources": set(), "latest": ""})
        g[r["kind"]] = (g[r["kind"]] or 0) + r["value"]
        g["refs"].add(r["ref"])
        g["sources"].add(r["source"])
        g["latest"] = max(g["latest"], r["at"])
    out = {}
    for name, g in groups.items():
        out[name] = {k: (g[k] if g[k] is not None else "unknown") for k in KINDS} | {"items": len(g["refs"]), "sources": sorted(g["sources"]), "latest": g["latest"],
                                                                                        "unknown_kinds": [k for k in KINDS if g[k] is None]}
    return {"by": by, "days": days, "groups": out, "note": "sums of platform-reported numbers only; 'unknown' = nothing reported"}


def recommend(cmp: dict) -> list[dict]:
    """One line per group: what to do and whether the data demonstrates it or merely suggests it."""
    recs = []
    for name, g in cmp["groups"].items():
        clicks, sales, views, imp = g["clicks"], g["sales"], g["views"], g["impressions"]
        reach = views if views != "unknown" else imp
        if sales != "unknown" and sales >= MIN_DEMONSTRATED["sales"]:
            recs.append({"group": name, "action": "repeat", "basis": "demonstrated", "why": f"{int(sales)} verified sale(s) recorded; keep this running and add volume"})
        elif clicks != "unknown" and clicks >= MIN_DEMONSTRATED["clicks"]:
            recs.append({"group": name, "action": "improve", "basis": "demonstrated", "why": f"{int(clicks)} clicks with no recorded sale: the listing page, not the traffic, is the bottleneck"})
        elif reach != "unknown" and reach >= MIN_DEMONSTRATED["views"] and clicks != "unknown" and clicks < MIN_DEMONSTRATED["clicks"]:
            recs.append({"group": name, "action": "improve", "basis": "demonstrated", "why": f"reach {int(reach)} but only {int(clicks)} clicks: the hook or first image is not earning the tap"})
        elif reach != "unknown" and reach < 100 and g["items"] >= 3:
            recs.append({"group": name, "action": "pause", "basis": "hypothesis", "why": f"{g['items']} items reached {int(reach)} total; likely the format, but too little data to be sure"})
        elif clicks == "unknown" and reach != "unknown":
            recs.append({"group": name, "action": "test", "basis": "hypothesis", "why": "reach is measured but clicks are not wired for this channel; wire click stats before judging"})
        else:
            recs.append({"group": name, "action": "measure", "basis": "hypothesis", "why": "not enough platform-reported data to recommend anything"})
    return recs


def measure_plan(store: Store, plan: DistributionPlan) -> DistributionPlan:
    """Fold this plan's metric rows into plan.results (sums, known kinds only) through Phase 6's rules."""
    rows = store.metrics(plan_id=plan.id)
    if not rows:
        return plan
    sums: dict[str, float] = {}
    src = set()
    for r in rows:
        sums[r["kind"]] = sums.get(r["kind"], 0.0) + r["value"]
        src.add(r["source"])
    payload = {k: (int(v) if float(v).is_integer() else v) for k, v in sums.items()}
    payload["measured"] = [k for k, v in sums.items() if v == 0]
    payload["source"] = "; ".join(sorted(src))
    return record_results(store, plan, payload)
