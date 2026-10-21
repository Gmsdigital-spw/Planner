"""Distribution planning (add-on Phase 6): every product needs a plan before its launch is complete.

`build_plan()` turns a product + evidence into a DistributionPlan with: target customer, dated evidence,
channels chosen by lane with a written reason each (V7 keep-list only), channel assets derived from one
source asset, a validated Etsy destination URL and CTA, a schedule in America/Chicago inside each channel's
posting window and free daily cap, a measurable hypothesis with success criteria, a campaign id for tracking.
Approval: a plan is `approved` only when an APPROVED publish_public approval is attached.

`funnel()` reports the real stages — created → quality approved → planned → scheduled → published → reached →
clicks → sales — each one a number only when something recorded it, otherwise "unknown". Nothing is
fabricated, and sales are never attributed to a channel unless the record says so.

`record_results()` stores real numbers and `next_action()` recommends repeat / improve / pause / test from them.
"""
from __future__ import annotations

import re
import typing as t
from datetime import datetime, timedelta

from .contracts import ApprovalStatus, Capability, Channel, DistributionPlan, ProductManifest, new_id, now_iso
from .store import Store

TZ = "America/Chicago"
# channels per lane, with the reason the plan writes down. V7 keep-list only: no Gumroad, no Funnel.
LANE_CHANNELS: dict[str, list[tuple[Channel, str]]] = {
    "planner": [(Channel.PINTEREST, "planner buyers search Pinterest; pins keep sending clicks for months"),
                (Channel.INSTAGRAM, "flip-through Reels show every page and the cozy desk look"),
                (Channel.FACEBOOK, "budget and family planner groups share printables")],
    "wallart": [(Channel.PINTEREST, "room-styling searches; wall art pins save well"),
                (Channel.INSTAGRAM, "framed-on-the-wall photos read instantly in the feed")],
    "mugwrap": [(Channel.PINTEREST, "sublimation crafters plan projects on Pinterest"),
                (Channel.TIKTOK, "pressing-a-mug videos are a proven craft format"),
                (Channel.FACEBOOK, "Cricut and sublimation groups")],
    "sticker": [(Channel.PINTEREST, "planner-sticker searches"), (Channel.INSTAGRAM, "sticker sheet flat-lays"), (Channel.TIKTOK, "print-and-cut process videos")],
    "invitation": [(Channel.PINTEREST, "party planning starts on Pinterest"), (Channel.FACEBOOK, "party and shower planning groups")],
    "game": [(Channel.PINTEREST, "party game searches spike before each holiday"),
             (Channel.TIKTOK, "play-the-game clips are shareable"),
             (Channel.FACEBOOK, "family and office party planners share game ideas"),
             (Channel.YOUTUBE_SHOP, "a 20-second how-to-play Short on the shop channel")],
}
# posting windows (local hour) and free daily caps the Factory already honours
WINDOWS: dict[Channel, tuple[int, int]] = {Channel.ETSY: (7, 7), Channel.PINTEREST: (8, 22), Channel.INSTAGRAM: (11, 20), Channel.FACEBOOK: (9, 20),
                                           Channel.TIKTOK: (17, 21), Channel.YOUTUBE_SHOP: (18, 20), Channel.GMULA: (19, 19)}
DAILY_CAP = {Channel.ETSY: 2, Channel.PINTEREST: 9, Channel.INSTAGRAM: 2, Channel.FACEBOOK: 1, Channel.TIKTOK: 2, Channel.YOUTUBE_SHOP: 1, Channel.GMULA: 1}
ETSY_URL = re.compile(r"^https://www\.etsy\.com/(listing/\d+|shop/[A-Za-z0-9_-]+)")


def validate_destination(url: str | None) -> tuple[bool, str]:
    if not url:
        return False, "no destination URL"
    if not ETSY_URL.match(url):
        return False, "destination must be the Etsy listing or shop URL"
    return True, "ok"


def build_plan(m: ProductManifest, *, target_customer: str, evidence: list[str], destination_url: str, cta: str = "Download it on Etsy",
               start: datetime | None = None, days: int = 7, source_asset: str | None = None, holiday: str | None = None,
               extra_channels: list[Channel] | None = None) -> DistributionPlan:
    if not evidence:
        raise ValueError("a plan needs evidence (dated source links or doc ids)")
    undated = [e for e in evidence if not re.search(r"20\d\d-\d\d-\d\d|\(20\d\d\)|20\d\d-\d\d", e)]
    if undated:
        raise ValueError(f"evidence needs a date: {undated[:2]}")
    ok, why = validate_destination(destination_url)
    if not ok:
        raise ValueError(why)
    pairs = list(LANE_CHANNELS.get(m.lane) or [(Channel.PINTEREST, "default: pins for every printable")])
    for c in extra_channels or []:
        if c not in [p[0] for p in pairs]:
            pairs.append((c, "added by the planner"))
    channels = [c for c, _ in pairs]
    reasons = {c.value: r for c, r in pairs}
    src = source_asset or (m.files[0].path if m.files else "")
    assets = {c.value: {"source": src, "needs": _asset_need(c), "status": "to_make"} for c in channels}
    start = start or datetime.now()
    schedule = []
    for day in range(days):
        for c in channels:
            lo, hi = WINDOWS[c]
            per_day = 1 if c != Channel.PINTEREST else min(3, DAILY_CAP[c])
            for k in range(per_day):
                hour = lo + (k * max(1, (hi - lo) // max(1, per_day)))
                at = (start + timedelta(days=day)).replace(hour=min(hour, hi), minute=0, second=0, microsecond=0)
                schedule.append({"channel": c.value, "at": at.isoformat(timespec="minutes"), "tz": TZ, "status": "planned"})
    camp = f"{m.product_id}-v{m.version}-{start:%Y%m%d}"
    hyp = (f"{m.title} reaches {target_customer} through {', '.join(c.value for c in channels)}"
           + (f" during the {holiday} window" if holiday else "") + f"; posts clicking through to Etsy within {days} days.")
    crit = f"≥ 25 measured clicks to the listing and ≥ 1 verified sale within {days + 7} days of the first post; otherwise change the hook or the first image."
    return DistributionPlan(id=new_id("plan"), product_id=m.product_id, product_version=m.version, target_customer=target_customer, evidence=list(evidence),
                            channels=channels, channel_reasons=reasons, assets=assets, destination_url=destination_url, cta=cta, schedule=schedule,
                            timezone=TZ, hypothesis=hyp, success_criteria=crit, status="planned", tracking={"campaign": camp, "note": "Etsy strips UTM; clicks come from each platform's own stats"})


def _asset_need(c: Channel) -> str:
    return {Channel.PINTEREST: "1000x1500 pin, real pages on a warm desk", Channel.INSTAGRAM: "9:16 flip-through Reel + 3-slide carousel",
            Channel.FACEBOOK: "4:5 photo post, caption under 150 words", Channel.TIKTOK: "9:16 12–20 s video, caption ≤ 150 chars",
            Channel.YOUTUBE_SHOP: "9:16 Short ≤ 60 s, #shorts in the tags", Channel.GMULA: "not a shop channel",
            Channel.ETSY: "the listing itself: state → active"}[c]


def approve_plan(store: Store, plan: DistributionPlan, approval_id: str) -> DistributionPlan:
    a = store.get_approval(approval_id)
    if not a or a.status != ApprovalStatus.APPROVED or a.capability != Capability.PUBLISH_PUBLIC:
        raise ValueError("needs an APPROVED publish_public approval")
    plan.approval_id, plan.status = approval_id, "approved"
    store.put_plan(plan)
    return plan


def mark(store: Store, plan: DistributionPlan, status: str, when: str | None = None) -> DistributionPlan:
    order = ["planned", "approved", "scheduled", "published", "measured"]
    if order.index(status) != order.index(plan.status) + 1:
        raise ValueError(f"plan {plan.id}: {plan.status} → {status} skips a stage")
    plan.status = status
    plan.tracking[status + "_at"] = when or now_iso()
    store.put_plan(plan)
    return plan


def record_results(store: Store, plan: DistributionPlan, results: dict) -> DistributionPlan:
    """Real numbers only. Keys: impressions, views, clicks, saves, conversions, sales — absent means unknown.
    A value of 0 is only accepted when `results['measured']` says the platform reported it."""
    clean: dict = {}
    measured = set(results.get("measured") or [])
    for k in ("impressions", "views", "clicks", "saves", "conversions", "sales"):
        if k not in results or results[k] is None:
            continue
        v = results[k]
        if v == 0 and k not in measured:
            raise ValueError(f"{k}=0 needs {k!r} in results['measured'] (a zero the platform reported), otherwise leave it out = unknown")
        clean[k] = v
    clean["at"] = now_iso()
    if results.get("source"):
        clean["source"] = results["source"]
    plan.results.update(clean)
    plan.next_action = next_action(plan)
    store.put_plan(plan)
    return plan


def next_action(plan: DistributionPlan) -> str:
    r = plan.results
    if "clicks" not in r and "views" not in r and "impressions" not in r:
        return "measure first: no platform numbers recorded yet; nothing to judge"
    clicks, sales = r.get("clicks"), r.get("sales")
    if sales is not None and sales > 0:
        return "repeat: this plan produced a verified sale; run the same channels again and raise the pin count"
    if clicks is not None and clicks >= 25:
        return "improve the listing: traffic arrived (≥25 clicks) without a sale; change the first photo or the title's first phrase, then re-measure"
    if clicks is not None and clicks < 25:
        return "improve the hook: under 25 clicks; test a new first line / cover on the best-reach channel before adding channels"
    return "test: reach is recorded but clicks are unknown; wire click stats for this channel before deciding"


def funnel(store: Store, plan: DistributionPlan) -> dict:
    """Stage by stage, real or 'unknown'. Sales are never attributed to the plan unless results say so."""
    m = store.get_product(plan.product_id, plan.product_version)
    g = (m.validation.get("gate") or {}) if m else {}
    r = plan.results
    sched = [s for s in plan.schedule if s.get("status") == "scheduled"]
    pub = [s for s in plan.schedule if s.get("status") == "published"]
    return {
        "product_created": bool(m), "quality_approved": g.get("decision") == "approved" if g else "unknown",
        "distribution_planned": True, "scheduled": len(sched) if sched else ("unknown" if plan.status == "scheduled" else 0),
        "published": len(pub) if pub else ("unknown" if plan.status in ("published", "measured") else 0),
        "audience_reached": r.get("impressions", r.get("views", "unknown")), "clicks": r.get("clicks", "unknown"),
        "conversions_or_sales": r.get("sales", r.get("conversions", "unknown")), "source": r.get("source", "unknown"), "next_action": plan.next_action or next_action(plan),
    }
