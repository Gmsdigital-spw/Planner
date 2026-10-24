"""Ingestion adapters: the Factory's REAL approved sources into scoped memory (factory/learning, Phase 9).

Sources (explicitly listed, nothing bulk-scanned): the notebook lane files, LESSONS.md, qa/MISSES.md, every
skills/<agent>/SKILL.md "What I've learned" and "Quality checklist" line, the stage run notes, scores.jsonl,
notebook/results.jsonl, runlog.jsonl, the specs / stage references / playbooks / shared rules, and the trading lab
exports. Excluded on purpose: gw/ (vault, state, jobs), shared/accounts.md (ids), backups/, anything encrypted,
legacy prompts, the page source. Importing never verifies a claim: notebook "What works" lines arrive as lessons
with confidence "claimed", Grayson's rules as facts with authority "grayson", everything else as observations or
example chunks. Re-running is idempotent (content hashes); a changed file supersedes its older chunks.
"""
from __future__ import annotations

import json
import re
import typing as t
from pathlib import Path

from .brain import AgentBrain
from .rubric import RUBRICS, assess, from_legacy_score, legacy_caps, rubric_id_of

LANE_SCOPE = {"business": "shop", "etsy": "shop", "pins": "shop", "social": "shop", "trading": "trading", "shorts": "studio", "ops": "crew"}
FLOOR_SCOPE = {"product": "shop", "etsy": "shop", "marketing": "shop", "studio": "studio", "trading": "trading", "fleet": "crew", "ops": "crew", "funnel": "shop"}
TASK_SCOPE = {"night-shift": "shop", "bolt": "shop", "herald": "shop", "check-up": "shop", "pricing": "shop", "video-pin": "shop", "scout-intel": "shop",
              "studio": "studio", "trading-scan": "trading", "trading-close": "trading", "trading-lab": "trading", "mechanic": "crew", "atlas-prime": "crew"}
TASK_AGENT = {"night-shift": "night-shift", "bolt": "bolt", "herald": "herald", "check-up": "warden", "pricing": "ledger", "video-pin": "pixel", "scout-intel": "scout",
              "studio": "vega", "trading-scan": "bull", "trading-close": "vault", "trading-lab": "tape", "mechanic": "mechanic", "atlas-prime": "foreman"}
DOC_SOURCES = [  # (relative glob, scope or "by-path", kind, ttl days)
    ("factory/CLAUDE.md", "crew"), ("factory/CONTEXT.md", "crew"), ("factory/shared/rules.md", "crew"), ("factory/shared/database.md", "crew"),
    ("factory/shared/logging.md", "crew"), ("factory/shared/repo.md", "crew"), ("factory/shared/gateway.md", "crew"),
    ("factory/specs/*.md", "by-path"), ("factory/playbooks/*.md", "shop"),
    ("factory/stages/night-shift/references/*.md", "shop"), ("factory/stages/night-shift/*/CONTEXT.md", "shop"), ("factory/stages/night-shift/CONTEXT.md", "shop"),
    ("factory/stages/bolt/references/*.md", "shop"), ("factory/stages/bolt/*/CONTEXT.md", "shop"), ("factory/stages/bolt/CONTEXT.md", "shop"),
    ("factory/stages/herald/references/*.md", "shop"), ("factory/stages/herald/*/CONTEXT.md", "shop"), ("factory/stages/herald/CONTEXT.md", "shop"),
    ("factory/stages/studio/references/*.md", "studio"), ("factory/stages/studio/*/CONTEXT.md", "studio"), ("factory/stages/studio/CONTEXT.md", "studio"),
    ("factory/stages/mechanic/CONTEXT.md", "crew"), ("factory/notebook/README.md", "crew"), ("factory/engine/LIMITATIONS.md", "crew"),
]
EXCLUDE_PARTS = ("legacy-prompt", "legacy-prompts", "accounts.md", "/gw/", "backups", ".enc", "/page/")


def scope_for_path(rel: str) -> str:
    r = rel.lower()
    if "trading" in r:
        return "trading"
    if "studio" in r or "shorts" in r or "youtube" in r:
        return "studio"
    if "mechanic" in r or "engine/" in r or "shared/" in r or r.endswith("claude.md") or r.endswith("context.md") and r.count("/") == 1:
        return "crew"
    return "shop"


def _sections(text: str) -> list[tuple[str, int, str]]:
    """[(heading, line_no_of_heading, body)] for '## ' headings."""
    out, cur, buf, start = [], None, [], 0
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            if cur is not None:
                out.append((cur, start, "\n".join(buf)))
            cur, buf, start = line[3:].strip(), [], i
        else:
            buf.append(line)
    if cur is not None:
        out.append((cur, start, "\n".join(buf)))
    return out


def _bullets(body: str, start_line: int) -> list[tuple[int, str]]:
    out = []
    for j, line in enumerate(body.splitlines(), start_line + 1):
        s = line.strip()
        if s.startswith("- ") and not s.startswith("- (none"):
            out.append((j, s[2:].strip()))
    return out


def _date_in(s: str) -> str | None:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else None


# ---------------------------------------------------------------- notebook
def ingest_notebook(brain: AgentBrain, root: Path) -> list[dict]:
    out = []
    for lane, scope in LANE_SCOPE.items():
        p = root / "factory" / "notebook" / f"{lane}.md"
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        items = []
        for heading, ln, body in _sections(text):
            h = heading.lower()
            for j, b in _bullets(body, ln):
                day = _date_in(b)
                base = {"line": j, "tags": {"lane": lane, "section": heading, "day": day}}
                if h.startswith("grayson"):
                    items.append({**base, "scope": "grayson" if lane == "business" else scope, "agent": "*", "kind": "fact", "body": b, "ttl_days": 365, "confidence": "grayson",
                                  "tags": {**base["tags"], "authority": "grayson"}, "evidence": f"factory/notebook/{lane}.md line {j} (Grayson's rules{', ' + day if day else ''})"})
                elif h.startswith("what works"):
                    items.append({**base, "scope": scope, "agent": "*", "kind": "lesson", "body": b, "ttl_days": 180, "confidence": "claimed",
                                  "evidence": f"factory/notebook/{lane}.md line {j} (What works; claimed by the keeper, not verified by import)"})
                elif h.startswith("testing"):
                    items.append({**base, "scope": scope, "agent": "*", "kind": "hypothesis", "body": b, "ttl_days": 60, "confidence": "hypothesis",
                                  "evidence": f"factory/notebook/{lane}.md line {j} (Testing)"})
                elif h.startswith("what doesn't") or h.startswith("what doesnt"):
                    items.append({**base, "scope": scope, "agent": "*", "kind": "mistake", "body": b, "ttl_days": 365, "confidence": "observed",
                                  "evidence": f"factory/notebook/{lane}.md line {j} (What doesn't work)"})
        out.append(brain.ingest_items(scope, p, items, rel_to=root))
    return out


# ---------------------------------------------------------------- lessons, misses
def ingest_lessons(brain: AgentBrain, root: Path) -> dict | None:
    p = root / "factory" / "LESSONS.md"
    if not p.exists():
        return None
    items = []
    for j, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if not s.startswith("- "):
            continue
        body = s[2:]
        low = body.lower()
        scope = "trading" if any(k in low for k in ("trading", "holdout", "pullback", "backtest", "lab-", "sma ")) else ("studio" if "short" in low and "gmula" in low else "shop")
        m = re.search(r"evidence:\s*(.+)$", body, re.I)
        ev = (m.group(1).strip() if m else "no evidence clause on the line")
        kind = "fact" if "grayson's rule" in low else "lesson"
        items.append({"line": j, "scope": "grayson" if kind == "fact" else scope, "agent": "*", "kind": kind, "body": body, "ttl_days": 365 if kind == "fact" else 180,
                      "confidence": "grayson" if kind == "fact" else "claimed", "tags": {"day": _date_in(body), "authority": "grayson"} if kind == "fact" else {"day": _date_in(body)},
                      "evidence": f"factory/LESSONS.md line {j}: {ev[:200]}"})
    return brain.ingest_items("shop", p, items, rel_to=root)


def ingest_misses(brain: AgentBrain, root: Path) -> dict | None:
    p = root / "factory" / "qa" / "MISSES.md"
    if not p.exists():
        return None
    items = []
    for j, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|") or line.startswith("| Date") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        date, found_by, wrong, why, check = cells[:5]
        items.append({"line": j, "scope": "shop", "agent": "warden", "kind": "mistake", "ttl_days": 365, "confidence": "observed",
                      "body": f"{date}: {wrong}. Missed because: {why}. Check added: {check}", "tags": {"day": date, "found_by": found_by},
                      "evidence": f"factory/qa/MISSES.md line {j} (found by {found_by})"})
    return brain.ingest_items("shop", p, items, rel_to=root)


# ---------------------------------------------------------------- skills
def ingest_skills(brain: AgentBrain, root: Path) -> list[dict]:
    out = []
    for p in sorted((root / "factory" / "skills").glob("*/SKILL.md")):
        agent = p.parent.name
        if agent.startswith("funnel_"):
            continue  # parked lane (V7)
        text = p.read_text(encoding="utf-8")
        fm = re.search(r"^floor:\s*(\w+)", text, re.M)
        scope = FLOOR_SCOPE.get(fm.group(1).lower(), "shop") if fm else ("crew" if agent in ("foreman", "mechanic", "medic") else "shop")
        items = []
        for heading, ln, body in _sections(text):
            h = heading.lower()
            if h.startswith("what i've learned") or h.startswith("what i have learned"):
                for j, b in _bullets(body, ln):
                    items.append({"line": j, "scope": scope, "agent": agent, "kind": "observation", "body": b, "ttl_days": 120, "confidence": "self-reported",
                                  "tags": {"day": _date_in(b), "section": "learned"}, "evidence": f"factory/skills/{agent}/SKILL.md line {j} (What I've learned)"})
            elif h.startswith("quality checklist"):
                for j, b in _bullets(body, ln):
                    if len(b) < 60:
                        continue  # the three generic template lines carry no evidence
                    items.append({"line": j, "scope": scope, "agent": agent, "kind": "lesson", "body": b, "ttl_days": 180, "confidence": "claimed",
                                  "tags": {"section": "checklist"}, "evidence": f"factory/skills/{agent}/SKILL.md line {j} (Quality checklist; cites its own evidence)"})
        if items:
            out.append(brain.ingest_items(scope, p, items, rel_to=root))
    return out


# ---------------------------------------------------------------- run notes → observations + eval cases
INSPECT_RE = re.compile(r"^(PASS|FAIL)\s+(\d{2,3})\b", re.I)
PARTS_RE = re.compile(r"file\s+(\d+),\s*copy\s+(\d+),\s*images\s+(\d+),\s*market\s+(\d+),\s*price\s+(\d+),\s*polish\s+(\d+)", re.I)


def parse_inspections(text: str, day: str) -> list[dict]:
    """Every '## Inspect: <title>' / '## Day run: Inspect:' / 'Re-inspect:' section with its six scores → a case."""
    cases = []
    for heading, ln, body in _sections(text):
        m = re.match(r"(?:Day run:\s*)?(Re-)?[Ii]nspect:\s*(.+)$", heading)
        if not m:
            continue
        first = body.strip().splitlines()[0] if body.strip() else ""
        v = INSPECT_RE.search(first)
        parts = PARTS_RE.search(body)
        if not v or not parts:
            continue
        rules = None
        if re.search(r"rulesPass\s*(yes|true)", body, re.I):
            rules = True
        elif re.search(r"rulesPass\s*(false|no)", body, re.I):
            rules = False
        slop_fail = bool(re.search(r"slop\s*(check\s*)?FAIL", body, re.I)) and not re.search(r"slop\s*(check\s*)?pass", body, re.I)
        fails = []
        if slop_fail:
            mm = re.search(r"slop\s*FAIL:\s*([^)]*)\)", body, re.I)
            fails = [mm.group(1).strip()] if mm else ["slop check failed (see run notes)"]
        total = int(v.group(2))
        f, c, i, mk, pr, po = (int(x) for x in parts.groups())
        cases.append({"title": m.group(2).strip(), "day": day, "reinspect": bool(m.group(1)), "line": ln, "verdict_line": first[:200],
                      "score": {"rubric": 2, "file": f, "copy": c, "images": i, "market": mk, "price": pr, "polish": po, "total": total, "rulesPass": rules,
                                "slopCheck": {"pass": not slop_fail, "fails": fails}, "verdict": first[:300]},
                      "parts_sum": f + c + i + mk + pr + po})
    return cases


def holdout_split(cases: list[dict], every: int = 3) -> tuple[list[dict], list[dict]]:
    """Deterministic: sort by title, every `every`-th case (starting at the 2nd) is held out."""
    ordered = sorted(cases, key=lambda c: (c["title"], c["day"], c["line"]))
    train, hold = [], []
    for k, c in enumerate(ordered):
        (hold if k % every == 1 else train).append(c)
    return train, hold


def ingest_run_notes(brain: AgentBrain, root: Path) -> dict:
    """Run notes: inspection sections become observations (and eval cases, train / holdout); the whole file is also
    chunked as reference text, with chunks that contain a HOLDOUT case's section tagged holdout (never retrieved)."""
    summary = {"files": 0, "cases_train": 0, "cases_holdout": 0, "chunks": 0, "superseded": 0}
    r2 = rubric_id_of(RUBRICS["etsy-product-r2"])
    for stage, scope, agent in (("night-shift", "shop", "atlas"), ("studio", "studio", "judge"), ("herald", "shop", "herald"), ("bolt", "shop", "bolt")):
        for p in sorted((root / "factory" / "stages" / stage / "output").glob("*-run.md")):
            day = p.name[:10]
            raw = p.read_bytes()
            rel = str(p.relative_to(root))
            if brain.store.rows("SELECT 1 FROM memories WHERE source_path=? AND source_sha=? LIMIT 1", (rel, __import__("hashlib").sha256(raw).hexdigest())):
                continue  # unchanged since the last ingest: cases, observations and chunks are already on file
            text = raw.decode("utf-8-sig", errors="replace")
            cases = parse_inspections(text, day) if stage == "night-shift" else []
            train, hold = holdout_split(cases)
            hold_titles = {c["title"] for c in hold}
            items = []
            for c in cases:
                split = "holdout" if c["title"] in hold_titles else "train"
                cid = brain.eval_case_put(scope, agent, split=split, task={"title": c["title"], "day": c["day"], "reinspect": c["reinspect"], "source": f"{rel} line {c['line']}"},
                                          expected=c["score"], source=rel, rubric_id=r2, case_id="case_" + re.sub(r"[^a-z0-9]+", "-", f"{c['day']}-{c['title'][:40]}-{c['line']}".lower()).strip("-"))
                summary["cases_train" if split == "train" else "cases_holdout"] += 1
                # the inspection itself is a real PRODUCTION evaluation with its six-point breakdown (legacy adapter, points kept)
                slug = re.sub(r"[^a-z0-9]+", "-", c["title"][:50].lower()).strip("-")
                eid = f"runnotes:{c['day']}:{slug}:{c['line']}"
                if not brain.store.rows("SELECT 1 FROM evaluations WHERE id=?", (eid,)):
                    leg = from_legacy_score(c["score"], c["title"])
                    ev = assess(leg["ratings"], "etsy-product-r2", leg["blockers"], caps=legacy_caps(c["score"]))
                    ev["legacy"] = "run notes inspection (points as recorded)"
                    ev["discrepancies"] = leg["discrepancies"]
                    brain.log(eid, scope, agent, "night-shift-07:legacy", {"item": c["title"], "day": c["day"], "reinspect": c["reinspect"], "source": f"{rel} line {c['line']}"}, None, ev,
                              mode="production", final=True, kind="score", artifact_ref=f"{rel} line {c['line']}", task_id=slug, extra={"holdout": split == "holdout", "case": cid})
                    summary["evaluations"] = summary.get("evaluations", 0) + 1
                if split == "train":
                    s = c["score"]
                    items.append({"line": c["line"], "scope": scope, "agent": agent, "kind": "observation", "ttl_days": 120, "confidence": "recorded",
                                  "body": f"{c['day']} inspection of '{c['title']}': {c['verdict_line'][:160]} (file {s['file']}/25 copy {s['copy']}/20 images {s['images']}/20 market {s['market']}/15 price {s['price']}/10 polish {s['polish']}/10)",
                                  "tags": {"day": c["day"], "criterion": min((k for k in ("file", "copy", "images", "market", "price", "polish")), key=lambda k: s[k] / RUBRICS["etsy-product-r2"]["criteria"][k]), "case": cid},
                                  "evidence": f"{rel} line {c['line']} ('## Inspect: {c['title'][:60]}')"})
            # reference chunks of the whole file, holdout-tagged where a held-out inspection section sits
            chunk_size, step = 1600, 1400
            for off in range(0, len(text), step):
                chunk = text[off:off + chunk_size]
                if not chunk.strip():
                    continue
                is_hold = any(f"Inspect: {ti}" in chunk for ti in hold_titles)
                items.append({"offset": off, "scope": scope, "agent": "*", "kind": "example", "ttl_days": 90, "confidence": "run-notes",
                              "body": chunk, "tags": {"day": day, "stage": stage, **({"holdout": 1} if is_hold else {})},
                              "evidence": f"{rel}; characters {off}:{off + len(chunk)}"})
                if off + chunk_size >= len(text):
                    break
            res = brain.ingest_items(scope, p, items, rel_to=root)
            summary["files"] += 1
            summary["chunks"] += len(res["new"])
            summary["superseded"] += res["superseded"]
    return summary


# ---------------------------------------------------------------- jsonl exports
def ingest_scores(brain: AgentBrain, root: Path) -> dict:
    """scores.jsonl: every scored line (score not null) becomes a PRODUCTION evaluation row with a stable id. Only the
    total is on file, so the row says so (legacy total-only); idea scores (/30) go to their own rubric id."""
    p = root / "factory" / "scores.jsonl"
    n_new = n_seen = 0
    if not p.exists():
        return {"new": 0, "seen": 0}
    r2 = rubric_id_of(RUBRICS["etsy-product-r2"])
    r30 = rubric_id_of(RUBRICS["idea-brief-30"])
    seen_keys: dict[str, int] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("score") is None:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", str(d.get("item", ""))[:50].lower()).strip("-")
        base = f"scores:{d.get('d')}:{d.get('agent')}:{slug}"
        k = seen_keys.get(base, 0)
        seen_keys[base] = k + 1
        rid = base if k == 0 else f"{base}:{k}"
        n_seen += 1
        if brain.store.rows("SELECT 1 FROM evaluations WHERE id=?", (rid,)):
            continue
        if d.get("kind") == "product":
            total = float(d["score"])
            # the same inspection already on file WITH its breakdown (run notes)? then the total-only line adds nothing.
            # Titles differ in length between the two files ("Santa Mail Bundle" vs the full title): match on the shorter slug.
            same_day = brain.store.rows("SELECT id FROM evaluations WHERE kind='score' AND agent='atlas' AND score=? AND id LIKE ?", (total, f"runnotes:{d.get('d')}:%"))
            dup = False
            for r in same_day:
                other = r["id"].split(":")[2]
                short = min(len(other), len(slug), 17)
                if short >= 8 and other[:short] == slug[:short]:
                    dup = True
                    break
            if dup:
                continue
            result = {"score": total, "passed": total >= 92, "target": 92, "aim": 95, "rubric_id": r2, "rubric_name": RUBRICS["etsy-product-r2"]["name"],
                      "legacy": "total-only (scores.jsonl has no breakdown)", "missing": [], "blockers": [], "gaps": []}
            brain.log(rid, "shop", str(d.get("agent") or "atlas"), "legacy-scores.jsonl", {"item": d.get("item"), "day": d.get("d"), "kind": "product"}, None, result,
                      mode="production", final=True, kind="score", artifact_ref=f"factory/scores.jsonl ({d.get('d')})", task_id=slug)
        elif d.get("kind") == "idea":
            total = float(d["score"]) * 100.0 / 30.0
            result = {"score": round(total, 2), "passed": float(d["score"]) >= 21, "target": 70, "aim": 80, "rubric_id": r30, "rubric_name": RUBRICS["idea-brief-30"]["name"],
                      "legacy": f"brief score {d['score']}/30 via adapter x100/30", "missing": [], "blockers": [], "gaps": [], "metric": d.get("metric")}
            brain.log(rid, "shop", str(d.get("agent") or "judge_ideas"), "legacy-scores.jsonl", {"item": d.get("item"), "day": d.get("d"), "kind": "idea"}, None, result,
                      mode="production", final=True, kind="score", artifact_ref=f"factory/scores.jsonl ({d.get('d')})", task_id=slug)
        else:
            continue
        n_new += 1
    return {"new": n_new, "seen": n_seen}


def ingest_results(brain: AgentBrain, root: Path) -> dict | None:
    p = root / "factory" / "notebook" / "results.jsonl"
    if not p.exists():
        return None
    items = []
    for j, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        scope = LANE_SCOPE.get(str(d.get("lane")), "shop")
        outcome = d.get("outcome")
        body = f"{d.get('day')} {d.get('kind')} {d.get('id')}: {str(d.get('what'))[:160]} | tags {json.dumps(d.get('tags') or {}, sort_keys=True)} | outcome " + \
               (json.dumps(outcome, sort_keys=True) + f" (checked {d.get('checked')})" if outcome else "pending")
        items.append({"line": j, "scope": scope, "agent": "*", "kind": "observation", "ttl_days": 180, "confidence": "platform-numbers" if outcome else "pending",
                      "body": body, "tags": {"lane": d.get("lane"), "kind": d.get("kind"), "id": str(d.get("id")), **{k: str(v) for k, v in (d.get("tags") or {}).items()}},
                      "evidence": f"factory/notebook/results.jsonl line {j} (id {d.get('id')})"})
    return brain.ingest_items("shop", p, items, rel_to=root)


def ingest_runlog(brain: AgentBrain, root: Path) -> dict:
    p = root / "factory" / "runlog.jsonl"
    n_new = n_seen = 0
    if not p.exists():
        return {"new": 0, "seen": 0}
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        task = str(d.get("task") or "unknown")
        rid = f"runlog:{task}:{d.get('started')}"
        n_seen += 1
        if brain.store.rows("SELECT 1 FROM evaluations WHERE id=?", (rid,)):
            continue
        brain.log_run(rid, TASK_SCOPE.get(task, "crew"), TASK_AGENT.get(task, task), task=task, outcome=str(d.get("outcome") or "unknown"), mode="production",
                      version=f"runlog:{d.get('model') or 'unknown'}", minutes=d.get("minutes"), est_tokens=d.get("estTokens"), loaded_bytes=d.get("loadedBytes"),
                      note=str(d.get("note") or ""), needs_you=str(d.get("needsYou") or ""), started=d.get("started"), finished=d.get("finished"),
                      stages=d.get("stages"), skipped=d.get("skipped"), extra={"day": d.get("day"), "gatewayJobs": d.get("gatewayJobs"), "dbWrites": d.get("dbWrites")})
        n_new += 1
    return {"new": n_new, "seen": n_seen}


# ---------------------------------------------------------------- approved documents (reference chunks)
def ingest_docs(brain: AgentBrain, root: Path) -> list[dict]:
    out = []
    for pattern, scope in DOC_SOURCES:
        for p in sorted(root.glob(pattern)):
            rel = str(p.relative_to(root))
            if any(x in rel for x in EXCLUDE_PARTS):
                continue
            sc = scope_for_path(rel) if scope == "by-path" else scope
            out.append(brain.ingest_text(sc, p, agent="*", kind="example", ttl_days=180, tags={"doc": rel.split("/")[-1], "approved": 1}, confidence="approved-doc", rel_to=root))
    for p in sorted((root / "factory" / "trading" / "lab").glob("lab-*.json")):
        out.append(brain.ingest_text("trading", p, agent="*", kind="observation", ttl_days=180, tags={"doc": p.name, "lab": 1}, confidence="backtest-export", rel_to=root))
    return out


def ingest_all(brain: AgentBrain, root: Path | str, only: t.Iterable[str] | None = None) -> dict:
    root = Path(root).resolve()
    want = set(only) if only else {"notebook", "lessons", "misses", "skills", "runnotes", "scores", "results", "runlog", "docs"}
    out: dict = {}
    if "notebook" in want:
        out["notebook"] = ingest_notebook(brain, root)
    if "lessons" in want:
        out["lessons"] = ingest_lessons(brain, root)
    if "misses" in want:
        out["misses"] = ingest_misses(brain, root)
    if "skills" in want:
        out["skills"] = ingest_skills(brain, root)
    if "runnotes" in want:
        out["runnotes"] = ingest_run_notes(brain, root)
    if "scores" in want:
        out["scores"] = ingest_scores(brain, root)
    if "results" in want:
        out["results"] = ingest_results(brain, root)
    if "runlog" in want:
        out["runlog"] = ingest_runlog(brain, root)
    if "docs" in want:
        out["docs"] = ingest_docs(brain, root)
    return out


def summarize(out: dict) -> dict:
    def cnt(x):
        if x is None:
            return {"new": 0, "superseded": 0, "files": 0}
        if isinstance(x, list):
            return {"new": sum(len(i.get("new", [])) for i in x), "superseded": sum(i.get("superseded", 0) for i in x), "files": len(x)}
        if "new" in x and isinstance(x["new"], list):
            return {"new": len(x["new"]), "superseded": x.get("superseded", 0), "files": 1}
        if "chunks" in x:  # run notes
            return {"new": x["chunks"], "superseded": x.get("superseded", 0), "files": x.get("files", 0), "cases_train": x.get("cases_train", 0), "cases_holdout": x.get("cases_holdout", 0)}
        return {"new": x.get("new", 0), "superseded": 0, "files": 1, **{k: v for k, v in x.items() if k != "new"}}
    return {k: cnt(v) for k, v in out.items()}


# ---------------------------------------------------------------- before / after comparison on saved real tasks
def compare_cases(brain: AgentBrain, split: str = "train", checks_for: t.Callable[[dict], dict | None] | None = None) -> dict:
    """Legacy behaviour (sum of the six points, pass at 92 and rulesPass) vs the candidate (same frozen rubric, plus
    blockers from rulesPass / slop, legacy slop caps, and objective checks where artifacts exist). Same scale, same cases."""
    rows = []
    for c in brain.eval_cases("shop", split=split):
        exp = c["expected"]
        leg = from_legacy_score(exp, c["task"]["title"])
        legacy_total = float(exp.get("total")) if exp.get("total") is not None else None
        legacy_pass = legacy_total is not None and legacy_total >= 92 and exp.get("rulesPass") is not False
        cand = assess(leg["ratings"], "etsy-product-r2", leg["blockers"], caps=legacy_caps(exp))
        ck = checks_for(c) if checks_for else None
        if ck:
            blockers = list(cand["blockers"]) + [b for b in ck.get("blockers", []) if b not in cand["blockers"]]
            caps = dict(legacy_caps(exp))
            for k, v in (ck.get("caps") or {}).items():
                caps[k] = min(caps.get(k, v), v)
            cand = assess(leg["ratings"], "etsy-product-r2", blockers, caps=caps)
        rows.append({"case": c["id"], "title": c["task"]["title"][:60], "day": c["task"]["day"], "legacy_total": legacy_total, "legacy_pass": legacy_pass,
                     "candidate_score": cand["score"], "candidate_pass": cand["passed"], "blockers": cand["blockers"], "capped": cand["capped"],
                     "discrepancies": leg["discrepancies"], "checks": (ck or {}).get("summary"), "raised": (cand["score"] or 0) > (legacy_total or 0) + 1e-9})
    return {"split": split, "n": len(rows), "rows": rows, "any_raised": any(r["raised"] for r in rows),
            "decisions_changed": sum(1 for r in rows if r["legacy_pass"] != r["candidate_pass"]),
            "note": "same frozen rubric on both sides; the candidate can only add blockers or caps, never points"}
