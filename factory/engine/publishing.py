"""Publishing adapters (add-on Phase 7). Authorized integrations only; a draft is never called "published".

Routes (what the Factory already uses, nothing new):
- Pinterest, TikTok  → Zernio through the free GitHub gateway (`gw/jobs/<id>.json` → gw.yml → `gw/out/<id>.json`).
  The adapter writes the job in exactly the shape `gw/run.py op_zernio` runs today (POST /posts with an
  Idempotency-Key). It cannot run the job itself: the result is `queued` until the gateway run lands, then
  `verify()` reads `gw/out` and marks `scheduled` / `published` / `failed` from the real response.
- Etsy listing  → the gateway's `etsy` op (PATCH listing state → active). Same queued → verify flow.
- Instagram, Facebook, shop YouTube → Make lanes. There is no Make token in this runtime (the page and the
  crews call Make through the Claude connector), so from Python these channels get a **review-ready draft**
  (`factory/engine/drafts/<id>.json`) with everything the crew needs; status `draft`, verified None.
- Gmula Shorts → the Studio Floor's own Make YouTube lane; same draft path here.

Rules enforced in `publish()`: the plan must be approved/scheduled; the kill switch stops everything; the same
(plan, channel, asset) is never sent twice (idempotency key, also sent to Zernio); every attempt is a
`Publication` row + audit line; secrets never appear (account ids are not secrets; API keys live only in
GitHub Actions secrets and never pass through here).
"""
from __future__ import annotations

import hashlib
import json
import os
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from .contracts import AuditEvent, Channel, DistributionPlan, IntegrationHealth, IntegrationState, Record, new_id, now_iso, scrub
from .store import Store

REPO = Path(__file__).resolve().parents[2]
GW_JOBS, GW_OUT = REPO / "gw" / "jobs", REPO / "gw" / "out"
DRAFTS = Path(os.environ.get("GM_ENGINE_DRAFTS", REPO / "factory" / "engine" / "drafts"))
# Zernio account ids already present in this public repo's gateway jobs (identifiers, not credentials)
ZERNIO_ACCOUNTS = {Channel.PINTEREST: os.environ.get("ZERNIO_PINTEREST_ACCOUNT", "6ad7b245350e86dff5e25133"),
                   Channel.TIKTOK: os.environ.get("ZERNIO_TIKTOK_ACCOUNT", "6ad7a7ecea18e081fb3894d2")}
GATEWAY_CHANNELS = {Channel.PINTEREST, Channel.TIKTOK, Channel.ETSY}
MAKE_CHANNELS = {Channel.INSTAGRAM, Channel.FACEBOOK, Channel.YOUTUBE_SHOP, Channel.GMULA}


@dataclass
class Asset(Record):
    """One channel-ready piece: text + media URL(s) + where it points."""
    channel: Channel
    text: str
    media: list[dict] = field(default_factory=list)  # [{"type":"image"|"video","url":...}]
    link: t.Optional[str] = None
    title: str = ""
    board_id: t.Optional[str] = None
    scheduled_for: t.Optional[str] = None  # ISO UTC
    listing_id: t.Optional[str] = None  # Etsy only

    def sha(self) -> str:
        return hashlib.sha256(self.to_json().encode()).hexdigest()[:16]


@dataclass
class Publication(Record):
    id: str
    plan_id: str
    channel: Channel
    idem_key: str
    status: str  # draft | queued | scheduled | published | failed
    adapter: str
    created_at: str
    job_id: t.Optional[str] = None
    external_id: t.Optional[str] = None
    url: t.Optional[str] = None
    verified: t.Optional[bool] = None  # None until the platform confirmed or denied
    checked_at: t.Optional[str] = None
    note: str = ""
    draft_path: t.Optional[str] = None


class GatewayAdapter:
    """Zernio (Pinterest, TikTok) + Etsy through gw/run.py. Writes jobs; never calls the APIs itself."""
    id = "gateway"

    def __init__(self, jobs: Path = GW_JOBS, out: Path = GW_OUT):
        self.jobs, self.out = Path(jobs), Path(out)

    def health(self) -> IntegrationHealth:
        """Connected only if the gateway has produced a successful result recently; it cannot see the secrets."""
        last_ok, last_err = None, None
        if self.out.exists():
            for p in sorted(self.out.glob("*.json"))[-40:]:
                try:
                    d = json.loads(p.read_text())
                except Exception:
                    continue
                if d.get("ok"):
                    last_ok = max(last_ok or "", str(d.get("at", "")))
                else:
                    last_err = str(d.get("at", "")) + " " + p.name
        state = IntegrationState.CONNECTED if last_ok else IntegrationState.UNVERIFIED
        return IntegrationHealth(id="gateway", state=state, last_ok_at=last_ok or None, last_error=last_err, checked_at=now_iso(),
                                 note="GitHub Actions gw.yml; secrets live there only")

    def submit(self, asset: Asset, idem: str, tag: str) -> Publication:
        jid = f"engine-{now_iso()[:10]}-{asset.channel.value}-{idem[:6]}"
        if asset.channel == Channel.ETSY:
            if not asset.listing_id:
                raise ValueError("Etsy publish needs listing_id")
            op = {"op": "etsy", "method": "PATCH", "path": f"/shops/68605457/listings/{asset.listing_id}", "body": {"state": "active"}, "tag": tag}
        else:
            if not asset.media:
                raise ValueError(f"{asset.channel.value} needs at least one media item")
            psd: dict = {}
            if asset.channel == Channel.PINTEREST:
                psd = {"boardId": asset.board_id or "", "title": asset.title[:100], "link": asset.link or ""}
            elif asset.channel == Channel.TIKTOK:
                psd = {"tiktokSettings": {"privacy_level": "PUBLIC_TO_EVERYONE", "allow_comment": True, "allow_duet": True, "allow_stitch": True,
                                          "content_preview_confirmed": True, "express_consent_given": True, "commercial_content_type": "your_brand"}}
            body = {"content": asset.text, "mediaItems": list(asset.media),
                    "platforms": [{"platform": asset.channel.value, "accountId": ZERNIO_ACCOUNTS[asset.channel], "platformSpecificData": psd}]}
            if asset.scheduled_for:
                body["scheduledFor"] = asset.scheduled_for
            op = {"op": "zernio", "method": "POST", "path": "/posts", "idem": idem, "tag": tag, "body": body}
        self.jobs.mkdir(parents=True, exist_ok=True)
        (self.jobs / f"{jid}.json").write_text(json.dumps({"id": jid, "stopOnError": True, "ops": [op]}, indent=1), encoding="utf-8")
        return Publication(id=new_id("pub"), plan_id="", channel=asset.channel, idem_key=idem, status="queued", adapter=self.id, created_at=now_iso(),
                           job_id=jid, note="gateway job written; the GitHub Actions run sends it")

    def verify(self, pub: Publication) -> Publication:
        p = self.out / f"{pub.job_id}.json"
        pub.checked_at = now_iso()
        if not p.exists():
            pub.note = "no gateway result yet"
            return pub
        d = json.loads(p.read_text())
        r = (d.get("results") or [{}])[0]
        data = r.get("data") or {}
        if r.get("ok"):
            post = data.get("post") if isinstance(data, dict) else None
            if post:
                pub.external_id = post.get("_id")
                pub.status = "scheduled" if post.get("scheduledFor") or post.get("status") == "scheduled" else "published"
                pub.url = post.get("url") or post.get("permalink") or pub.url
            elif pub.channel == Channel.ETSY:
                pub.status = "published" if data.get("state") == "active" else "failed"
                pub.url = data.get("url") or pub.url
            else:
                pub.status = "published"
            pub.verified = True
            pub.note = f"gateway {r.get('status')} ok"
        else:
            pub.status, pub.verified = "failed", False
            pub.note = scrub(f"gateway {r.get('status')}: {json.dumps(data)[:200]}")
        return pub


class DraftAdapter:
    """Review-ready drafts for channels this runtime cannot reach (Make lanes). Never 'published'."""
    id = "draft"

    def __init__(self, drafts: Path = DRAFTS):
        self.drafts = Path(drafts)

    def health(self) -> IntegrationHealth:
        return IntegrationHealth(id="make", state=IntegrationState.MISSING, checked_at=now_iso(),
                                 note="Make is reachable only from the Factory page / crews (Claude connector); Python writes drafts")

    def submit(self, asset: Asset, idem: str, tag: str) -> Publication:
        self.drafts.mkdir(parents=True, exist_ok=True)
        pid = new_id("pub")
        path = self.drafts / f"{pid}.json"
        path.write_text(json.dumps({"id": pid, "channel": asset.channel.value, "idem": idem, "asset": asset.to_dict(), "at": now_iso(),
                                    "how": "Herald/Rocket post this through the Make lane in their next run, or Grayson posts it by hand"}, indent=1), encoding="utf-8")
        return Publication(id=pid, plan_id="", channel=asset.channel, idem_key=idem, status="draft", adapter=self.id, created_at=now_iso(),
                           draft_path=str(path.relative_to(REPO)) if str(path).startswith(str(REPO)) else str(path), note="draft only: not published")

    def verify(self, pub: Publication) -> Publication:
        pub.checked_at = now_iso()
        pub.note = "draft: nothing to verify until a crew posts it"
        return pub


class Publisher:
    def __init__(self, store: Store, gateway: GatewayAdapter | None = None, draft: DraftAdapter | None = None, adapters: dict[Channel, t.Any] | None = None):
        self.store = store
        self.gateway = gateway or GatewayAdapter()
        self.draft = draft or DraftAdapter()
        self.adapters = adapters or {}

    def adapter_for(self, ch: Channel):
        if ch in self.adapters:
            return self.adapters[ch]
        return self.gateway if ch in GATEWAY_CHANNELS else self.draft

    def health(self) -> list[IntegrationHealth]:
        hs = [self.gateway.health(), self.draft.health()]
        for h in hs:
            self.store.put_integration(h)
        return hs

    def publish(self, plan: DistributionPlan, asset: Asset, who: str = "bolt") -> Publication:
        if self.store.control("kill", False):
            raise PermissionError("kill switch is on: no new publishing")
        if plan.status not in ("approved", "scheduled", "published"):
            raise PermissionError(f"plan {plan.id} is {plan.status}; publishing needs an approved plan")
        if not plan.approval_id:
            raise PermissionError("plan carries no approval id")
        if asset.channel not in plan.channels:
            raise ValueError(f"{asset.channel.value} is not in the plan")
        if asset.link and plan.destination_url and not asset.link.startswith(plan.destination_url.split("?")[0][:40]):
            raise ValueError("asset link does not point at the plan's destination")
        base = hashlib.sha256(f"{plan.id}|{asset.channel.value}|{asset.sha()}".encode()).hexdigest()[:28]
        idem, n = base, 0
        while True:  # the same work is never sent twice; a FAILED attempt may be retried under a fresh key
            prior = self.find(idem)
            if prior is None:
                break
            if prior.status != "failed":
                return prior
            n += 1
            idem = f"{base}-r{n}"
        pub = self.adapter_for(asset.channel).submit(asset, idem, tag=f"{plan.product_id}-{asset.channel.value}")
        pub.plan_id = plan.id
        self.store.put_publication(pub)
        self.store.audit(AuditEvent.make(who, "publish_" + pub.status, pub.id, f"{asset.channel.value} via {pub.adapter}"))
        return pub

    def find(self, idem: str) -> Publication | None:
        return self.store.find_publication(idem)

    def refresh(self, pub: Publication) -> Publication:
        before = pub.status
        pub = self.adapter_for(pub.channel).verify(pub)
        self.store.put_publication(pub)
        if pub.status != before:
            self.store.audit(AuditEvent.make("engine", "publish_" + pub.status, pub.id, pub.note))
        return pub

    def publications(self, plan_id: str | None = None) -> list[Publication]:
        return self.store.publications(plan_id)


# ---------------------------------------------------------------- channel adaptation (deterministic)
LIMITS = {Channel.ETSY: 140, Channel.PINTEREST: 500, Channel.INSTAGRAM: 2200, Channel.FACEBOOK: 600, Channel.TIKTOK: 150, Channel.YOUTUBE_SHOP: 100, Channel.GMULA: 100}


def adapt(plan: DistributionPlan, copy: dict, media: dict[str, list[dict]], boards: dict[str, str] | None = None) -> list[Asset]:
    """One source copy → one Asset per channel in the plan, inside each platform's limits. No model needed."""
    title = str(copy.get("title", ""))[:100]
    desc = " ".join(str(copy.get("description", "")).split())
    tags = [str(x).replace(" ", "") for x in (copy.get("tags") or [])][:5]
    out = []
    for ch in plan.channels:
        lim = LIMITS[ch]
        hashtags = (" " + " ".join("#" + x for x in tags)) if ch in (Channel.TIKTOK, Channel.INSTAGRAM, Channel.YOUTUBE_SHOP) else ""
        body = desc[: max(0, lim - len(hashtags) - 1)].rsplit(" ", 1)[0] if len(desc) + len(hashtags) > lim else desc
        text = (body + hashtags).strip()
        if ch == Channel.TIKTOK:
            text = (title + ". Link in bio." + hashtags)[:lim]
        first = next((s["at"] for s in plan.schedule if s["channel"] == ch.value), None)
        out.append(Asset(channel=ch, text=text, media=list(media.get(ch.value) or media.get("default") or []), link=plan.destination_url, title=title,
                         board_id=(boards or {}).get(ch.value), scheduled_for=_to_utc(first) if first else None))
    return out


def _to_utc(local_iso: str) -> str:
    """Plan times are America/Chicago; Zernio wants UTC. Done without third-party deps."""
    from datetime import datetime, timedelta, timezone
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.fromisoformat(local_iso).replace(tzinfo=ZoneInfo("America/Chicago"))
    except Exception:
        dt = datetime.fromisoformat(local_iso).replace(tzinfo=timezone(timedelta(hours=-5)))
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
