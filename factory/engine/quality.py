"""Product quality gate (add-on Phase 6).

The ten-stage pipeline from the add-on, enforced in order on a versioned ProductManifest:
  hypothesis → evidence → spec → generate → validate → review → assets → distribution → publish → measure

`validate()` runs the automated checks that can be done from the repo and the manifest: file integrity
(exists, non-empty, sha256 matches, real PDF/PNG/SVG header), format allowed for the lane, the Etsy copy rules
the Factory already enforces (title ≤ 140, exactly 13 tags ≤ 20 chars, description ≥ 300), banned revenue
claims, and the originality guard (no brand or character names). A check that cannot be done offline (a link
resolving, a formula in a spreadsheet nobody opened) is recorded as **unknown**, never as pass.

`gate()` decides whether a human must look: any failed check → rejected; any unknown check, a new lane, or a
score under PASS_SCORE → needs review; otherwise approved. `advance()` moves a product one stage at a time and
refuses to skip; `publish` requires validation ok, review done when required, and an approved distribution plan.
Every change writes a NEW manifest version. Released versions are never overwritten (the store enforces it).
"""
from __future__ import annotations

import hashlib
import re
import typing as t
from pathlib import Path

from .contracts import FileRef, ProductManifest, new_id, now_iso
from .store import Store

PASS_SCORE = 92
STAGES = ["hypothesis", "evidence", "spec", "generate", "validate", "review", "assets", "distribution", "publish", "measure"]
LANE_FORMATS = {"planner": {"pdf"}, "wallart": {"pdf", "png", "jpg"}, "mugwrap": {"png", "svg", "pdf"}, "sticker": {"png", "svg", "pdf"},
                "invitation": {"pdf", "jpg"}, "game": {"pdf"}}
MAGIC = {"pdf": b"%PDF", "png": b"\x89PNG", "jpg": b"\xff\xd8", "svg": b"<"}
BANNED_CLAIMS = ("made $", "earn $", "guaranteed", "passive income in", "quit my job", "guaranteed sales")
# Originality guard: a short list the Factory already refuses; extend in the playbooks, never remove.
BRANDS = ("disney", "pixar", "marvel", "nintendo", "pokemon", "pokémon", "barbie", "hello kitty", "star wars", "harry potter",
          "minecraft", "fortnite", "roblox", "taylor swift", "grinch", "elf on the shelf", "peppa", "bluey", "paw patrol", "sonic")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def file_ref(p: Path, root: Path | None = None) -> FileRef:
    rel = str(p.relative_to(root)) if root else str(p)
    return FileRef(path=rel, sha256=sha256_file(p), bytes=p.stat().st_size, format=p.suffix.lower().lstrip("."))


def _check(name: str, ok: t.Optional[bool], note: str = "") -> dict:
    return {"name": name, "ok": ok, "note": note}


def validate(m: ProductManifest, copy: dict | None = None, root: Path | None = None, score: int | None = None) -> dict:
    """Automated validation. Returns {"ok": bool|None, "checks": [...], "unknown": n, "failed": n}.
    ok is False when any check failed, None when none failed but some are unknown, True otherwise."""
    checks: list[dict] = []
    root = root or Path(".")
    allowed = LANE_FORMATS.get(m.lane)
    checks.append(_check("lane known", allowed is not None, m.lane))
    if not m.files:
        checks.append(_check("files present", False, "manifest lists no files"))
    for f in m.files:
        p = (root / f.path)
        if not p.exists():
            checks.append(_check(f"file exists: {f.path}", False, "missing on disk"))
            continue
        size = p.stat().st_size
        checks.append(_check(f"file non-empty: {f.path}", size > 0, f"{size} bytes"))
        checks.append(_check(f"sha256 matches: {f.path}", sha256_file(p) == f.sha256))
        magic = MAGIC.get(f.format)
        if magic is None:
            checks.append(_check(f"format known: {f.path}", False, f".{f.format} is not a format this gate knows"))
        else:
            with p.open("rb") as fh:
                head = fh.read(8)
            checks.append(_check(f"real {f.format}: {f.path}", head.startswith(magic), "header check"))
        if allowed is not None:
            checks.append(_check(f"format allowed for lane: {f.path}", f.format in allowed, f"{m.lane} allows {sorted(allowed)}"))
    c = copy or {}
    if c:
        title = str(c.get("title", ""))
        tags = c.get("tags") or []
        desc = str(c.get("description", ""))
        checks.append(_check("title 1..140", 0 < len(title) <= 140, f"{len(title)} chars"))
        checks.append(_check("13 tags ≤ 20 chars", len(tags) == 13 and all(len(str(x)) <= 20 for x in tags), f"{len(tags)} tags"))
        checks.append(_check("description ≥ 300", len(desc) >= 300, f"{len(desc)} chars"))
        blob = " ".join([title, desc] + [str(x) for x in tags]).lower()
        hits = [b for b in BANNED_CLAIMS if b in blob]
        checks.append(_check("no revenue claims", not hits, ", ".join(hits)))
        brands = [b for b in BRANDS if re.search(r"\b" + re.escape(b) + r"\b", blob)]
        checks.append(_check("original (no brands / characters)", not brands, ", ".join(brands)))
        links = re.findall(r"https?://\S+", desc)
        if links:
            checks.append(_check("links resolve", None, f"{len(links)} link(s) not checked offline"))
    else:
        checks.append(_check("listing copy", None, "no copy supplied; copy rules not checked"))
    if m.format == "xlsx":
        checks.append(_check("spreadsheet formulas", None, "formula check needs the workbook opened; not done here"))
    checks.append(_check("score ≥ %d" % PASS_SCORE, None if score is None else score >= PASS_SCORE, "unscored" if score is None else str(score)))
    checks.append(_check("known limitations listed", bool(m.known_limitations), "" if m.known_limitations else "every product lists what it cannot do"))
    failed = sum(1 for x in checks if x["ok"] is False)
    unknown = sum(1 for x in checks if x["ok"] is None)
    ok: t.Optional[bool] = False if failed else (None if unknown else True)
    return {"ok": ok, "checks": checks, "failed": failed, "unknown": unknown, "at": now_iso(), "score": score}


def gate(validation: dict, new_lane: bool = False) -> dict:
    """Decide: approved | needs_review | rejected, with the reasons a human would want."""
    reasons = [c["name"] + (": " + c["note"] if c["note"] else "") for c in validation["checks"] if c["ok"] is False]
    if reasons:
        return {"decision": "rejected", "reasons": reasons, "human_review": False}
    why = [c["name"] + (": " + c["note"] if c["note"] else "") for c in validation["checks"] if c["ok"] is None]
    if new_lane:
        why.append("first product in this lane")
    if why:
        return {"decision": "needs_review", "reasons": why, "human_review": True}
    return {"decision": "approved", "reasons": [], "human_review": False}


class Pipeline:
    """Stage bookkeeping on top of the store. Each advance writes a new manifest version."""

    def __init__(self, store: Store):
        self.store = store

    def stage_of(self, m: ProductManifest) -> str:
        return str(m.validation.get("stage") or STAGES[0])

    def _bump(self, m: ProductManifest, **changes) -> ProductManifest:
        d = m.to_dict()
        d.update(changes)
        d["version"] = m.version + 1
        d["supersedes"] = m.version
        d["created_at"] = now_iso()
        nm = ProductManifest.from_dict(d)
        self.store.put_product(nm)
        return nm

    def advance(self, product_id: str, to: str, evidence: dict | None = None, who: str = "engine") -> ProductManifest:
        """Move one stage forward. Refuses to skip, to go backwards, or to publish without the gates."""
        m = self.store.get_product(product_id)
        if not m:
            raise ValueError(f"no product {product_id}")
        cur = self.stage_of(m)
        if to not in STAGES:
            raise ValueError(f"unknown stage {to}")
        if STAGES.index(to) != STAGES.index(cur) + 1:
            raise ValueError(f"cannot go {cur} → {to}; next stage is {STAGES[min(len(STAGES) - 1, STAGES.index(cur) + 1)]}")
        v = dict(m.validation)
        history = list(v.get("history") or [])
        history.append({"stage": to, "at": now_iso(), "by": who, "evidence": evidence or {}})
        v.update({"stage": to, "history": history})
        if to == "validate":
            if not evidence or "result" not in evidence:
                raise ValueError("validate needs evidence={'result': validate(...)} ")
            v["result"] = evidence["result"]
            v["gate"] = gate(evidence["result"], new_lane=bool(evidence.get("new_lane")))
            if v["gate"]["decision"] == "rejected":
                return self._bump(m, validation=v, listing_status="rejected")
        if to == "review":
            g = v.get("gate") or {}
            if g.get("human_review") and not (evidence and evidence.get("reviewer")):
                raise ValueError("this product needs a human review: pass evidence={'reviewer': 'grayson', 'verdict': 'ok'}")
            if evidence and evidence.get("verdict") not in (None, "ok"):
                return self._bump(m, validation=v, listing_status="rejected")
        if to == "distribution":
            plan_id = evidence and evidence.get("plan_id")
            if not plan_id or not self.store.get_plan(plan_id):
                raise ValueError("distribution needs evidence={'plan_id': <an existing DistributionPlan>}")
            return self._bump(m, validation=v, distribution_status="planned")
        if to == "publish":
            g = v.get("gate") or {}
            res = v.get("result") or {}
            if res.get("ok") is False or g.get("decision") == "rejected":
                raise ValueError("cannot publish: validation failed")
            if g.get("human_review") and not any(h["stage"] == "review" and h["evidence"].get("reviewer") for h in history):
                raise ValueError("cannot publish: human review required and not recorded")
            plan_id = next((h["evidence"].get("plan_id") for h in history if h["stage"] == "distribution"), None)
            plan = self.store.get_plan(plan_id) if plan_id else None
            if not plan or plan.status not in ("approved", "scheduled", "published", "measured"):
                raise ValueError("cannot publish: the distribution plan is not approved")
            if not evidence or not evidence.get("approval_id"):
                raise ValueError("cannot publish: needs evidence={'approval_id': <approved publish_public approval>}")
            a = self.store.get_approval(evidence["approval_id"])
            if not a or a.status.value != "approved" or a.capability.value != "publish_public":
                raise ValueError("cannot publish: approval is not an approved publish_public approval")
            return self._bump(m, validation=v, listing_status="listed", distribution_status="published")
        if to == "measure":
            return self._bump(m, validation=v, distribution_status="measured")
        return self._bump(m, validation=v)
