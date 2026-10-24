"""AgentBrain: scoped, provenance-carrying memory + evidence-linked run records + ideas / experiments / promotion
(factory/learning, Phase 9). Adapted from the reference agent_learning.py onto the Factory's existing durable store
(factory/engine/store.py: append-only journal committed to git + a derived SQLite index, migration v5).

What it is: external memory and workflow bookkeeping for the crews. What it is not: a model, an evaluator, a
background worker, or model-weight training. Scores and evidence come from the separately tested evaluator
(rubric.py + checks.py); this module stores, scopes, retrieves and counts.

Scopes (businesses; data never crosses them):
  shop     GM's Digital Creations: Etsy products, pins, socials, pricing, listing check-ups
  studio   the Gmula Shorts channel
  trading  the paper trading floor
  crew     the crew itself (runs, tools, fixes)
  grayson  Grayson's own rules in his words (facts only, agent '*', readable by every scope: authority, not claims)
  shared   explicitly VERIFIED general lessons (agent '*'); nothing lands here by import
Agent-private memory is (scope, agent); business-shared is (scope, '*').
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import typing as t
from datetime import datetime, timedelta, timezone
from pathlib import Path

from factory.engine.contracts import AuditEvent, now_iso
from factory.engine.store import Store, resolve_db_dir

from .rubric import assess, digest, number, packed

KINDS = {"fact", "mistake", "lesson", "example", "hypothesis", "observation"}
BUSINESS_SCOPES = {"shop", "studio", "trading", "crew"}
SPECIAL_SCOPES = {"shared", "grayson"}
DEFAULT_TTL_DAYS = {"fact": 365, "lesson": 180, "example": 60, "mistake": 45, "observation": 45, "hypothesis": 30}
MAX_CONTEXT_ITEMS, MAX_CONTEXT_CHARS = 6, 6000
MAX_IDEAS_PER_DAY = 3
MIN_EXPERIMENT_SAMPLES = 3
STOP = {"the", "and", "for", "with", "from", "this", "that", "into", "have", "make", "are", "was", "were", "you", "your", "our",
        "not", "but", "all", "any", "can", "per", "its", "one", "two", "day", "run", "etsy", "product", "listing"}


def _iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts if ts is not None else time.time(), tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def terms_of(text: str, limit: int = 32) -> list[str]:
    return sorted(set(re.findall(r"[a-z0-9]{3,}", (text or "").lower())) - STOP)[:limit]


class AgentBrain:
    def __init__(self, store: Store | None = None, db_dir: Path | str | None = None, clock: t.Callable[[], float] = time.time):
        self._own = store is None
        self.store = store or Store(Path(db_dir) if db_dir else resolve_db_dir()).open()
        self.clock = clock

    def close(self) -> None:
        if self._own:
            self.store.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def now(self) -> str:
        return _iso(self.clock())

    # ---------------------------------------------------------------- memories
    def remember(self, scope: str, agent: str, kind: str, body: str, evidence: str, *, verified: bool = False, ttl_days: float | None = None,
                 source_path: str | None = None, source_sha: str | None = None, chunk: tuple[int, int] | None = None, confidence: str | None = None,
                 tags: dict | None = None, supersedes: str | None = None, created: str | None = None) -> str:
        if kind not in KINDS:
            raise ValueError(f"Unknown memory kind {kind!r}; allowed {sorted(KINDS)}")
        if any(not isinstance(s, str) or not s.strip() for s in (scope, agent, body, evidence)):
            raise ValueError("Scope, agent, body and source evidence are required")
        if len(body) > 12000 or len(evidence) > 3000:
            raise ValueError("Store a short chunk and a reference to the full source")
        if type(verified) is not bool or (kind == "hypothesis" and verified):
            raise ValueError("Hypotheses remain unverified")
        if scope == "shared" and (not verified or agent != "*"):
            raise ValueError("Only explicitly verified general lessons may be shared")
        if scope == "grayson" and (kind != "fact" or agent != "*"):
            raise ValueError("The grayson scope holds his rules as facts for everyone, nothing else")
        if scope not in BUSINESS_SCOPES | SPECIAL_SCOPES:
            raise ValueError(f"Unknown scope {scope!r}; businesses are {sorted(BUSINESS_SCOPES)} plus shared / grayson")
        ttl = number(DEFAULT_TTL_DAYS.get(kind, 30) if ttl_days is None else ttl_days, 0.000001, 730)
        key = digest([scope, agent, kind, body.strip(), evidence.strip()])
        now = created or self.now()
        row = {"id": key, "scope": scope, "agent": agent, "kind": kind, "status": "active", "body": body, "evidence": evidence,
               "source_path": source_path, "source_sha": source_sha, "chunk_start": chunk[0] if chunk else None, "chunk_end": chunk[1] if chunk else None,
               "confidence": confidence or ("tested" if verified else "unverified"), "verified": bool(verified), "tags": dict(tags or {}),
               "created": now, "expires": (_parse(now) + timedelta(days=ttl)).isoformat(timespec="seconds").replace("+00:00", "Z"),
               "supersedes": supersedes, "superseded_by": None, "version": 1}
        existing = self.get(key)
        if existing is None:
            self.store.put_learning("memory", row)
        if supersedes and supersedes != key:
            self.patch(supersedes, status="superseded", superseded_by=key)
        return key

    def patch(self, memory_id: str, **fields) -> None:
        allowed = {"status", "verified", "superseded_by", "confidence", "expires"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"cannot patch {sorted(bad)}")
        if "verified" in fields:
            fields["verified"] = int(bool(fields["verified"]))
        self.store.put_learning("memory", {"op": "patch", "id": memory_id, **fields})

    def get(self, memory_id: str) -> dict | None:
        r = self.store.rows("SELECT doc FROM memories WHERE id=?", (memory_id,))
        return json.loads(r[0]["doc"]) if r else None

    def memory(self, memory_id: str, scope: str, agent: str) -> dict | None:
        """Read one chunk by id WITHOUT bypassing scope or expiry: the same rule `context` uses."""
        r = self.store.rows(
            "SELECT doc FROM memories WHERE id=? AND status='active' AND expires>? AND ("
            "(scope=? AND agent IN (?, '*')) OR (scope='shared' AND verified=1 AND agent='*') OR (scope='grayson' AND agent='*'))",
            (memory_id, self.now(), scope, agent))
        return json.loads(r[0]["doc"]) if r else None

    def verify(self, memory_id: str, *, experiment_id: str | None = None, by: str | None = None, reason: str | None = None) -> dict:
        """A lesson becomes 'tested' only through an experiment that was decided KEEP with enough samples, or by
        Grayson's explicit call (recorded with his reason). Importing a file never verifies anything."""
        m = self.get(memory_id)
        if not m:
            raise ValueError(f"no memory {memory_id}")
        if m["kind"] == "hypothesis":
            raise ValueError("a hypothesis is never verified; promote it to a lesson through an experiment first")
        if experiment_id:
            e = self.experiment(experiment_id)
            if not e:
                raise ValueError(f"no experiment {experiment_id}")
            if e["decision"] != "keep":
                raise ValueError(f"experiment {experiment_id} was decided {e['decision']!r}, not keep")
            if int(e.get("samples", 0)) < MIN_EXPERIMENT_SAMPLES:
                raise ValueError(f"experiment {experiment_id} has {e.get('samples', 0)} samples; {MIN_EXPERIMENT_SAMPLES}+ needed")
            if e.get("conflicts"):
                raise ValueError("experiment has unresolved conflicting results; decide them first")
            why = f"experiment {experiment_id}: {e.get('metric')} {e.get('success')} met on {e['samples']} samples"
        elif by == "grayson" and reason and reason.strip():
            why = f"Grayson's call: {reason.strip()[:200]}"
        else:
            raise ValueError("verify needs an experiment decided keep, or by='grayson' with a reason")
        self.patch(memory_id, verified=1, confidence="tested")
        self.store.audit(AuditEvent.make(by or "engine", "memory_verified", memory_id, why))
        return {"id": memory_id, "verified": True, "why": why}

    def share(self, memory_id: str, by: str = "engine") -> str:
        """Copy a VERIFIED lesson into the shared scope (agent '*'); the original stays where it was."""
        m = self.get(memory_id)
        if not m or not m.get("verified"):
            raise ValueError("only a verified lesson can be shared")
        return self.remember("shared", "*", "lesson", m["body"], m["evidence"] + f" | shared from {m['scope']}/{m['agent']} by {by}", verified=True,
                             ttl_days=365, source_path=m.get("source_path"), source_sha=m.get("source_sha"), confidence="tested", tags={**(m.get("tags") or {}), "shared_from": memory_id})

    def retract(self, memory_id: str, reason: str, by: str = "engine") -> None:
        self.patch(memory_id, status="retracted")
        self.store.audit(AuditEvent.make(by, "memory_retracted", memory_id, reason[:300]))

    def contradictions(self, scope: str) -> list[dict]:
        """Same body text filed both as a lesson and as a mistake / 'doesn't work' line, or two sources that disagree
        on the same tag claim. Lexical only; it lists, it does not decide."""
        rows = self.store.rows("SELECT id, kind, body, source_path, tags FROM memories WHERE scope=? AND status='active'", (scope,))
        by_text: dict[str, list[dict]] = {}
        for r in rows:
            key = re.sub(r"\W+", " ", r["body"].lower()).strip()[:160]
            by_text.setdefault(key, []).append(r)
        out = []
        for key, group in by_text.items():
            kinds = {g["kind"] for g in group}
            if len(group) > 1 and ("lesson" in kinds and "mistake" in kinds):
                out.append({"text": key[:100], "ids": [g["id"] for g in group], "kinds": sorted(kinds), "sources": sorted({g["source_path"] or "" for g in group})})
        return out

    # ---------------------------------------------------------------- retrieval
    def context(self, scope: str, agent: str, task: str = "", *, max_chars: int = MAX_CONTEXT_CHARS, limit: int = MAX_CONTEXT_ITEMS,
                run_ref: str | None = None, record: bool = True) -> list[dict]:
        """Scoped, expiry-filtered lexical retrieval (not semantic search). Private (scope, agent) + business (scope, '*') +
        verified shared + Grayson's rules; holdout-tagged rows are never returned. Budget: `limit` items, `max_chars` packed."""
        if scope not in BUSINESS_SCOPES:
            raise ValueError(f"retrieve for a business scope {sorted(BUSINESS_SCOPES)}, not {scope!r}")
        max_chars = int(number(max_chars, 256, 20000))
        limit = int(number(limit, 1, 20))
        now = self.now()
        rows = self.store.rows(
            "SELECT doc FROM memories WHERE status='active' AND expires>? AND ("
            "(scope=? AND agent IN (?, '*')) OR (scope='shared' AND verified=1 AND agent='*') OR (scope='grayson' AND agent='*')) "
            "ORDER BY created DESC LIMIT 5000", (now, scope, agent))
        docs = [json.loads(r["doc"]) for r in rows]
        docs = [d for d in docs if not (d.get("tags") or {}).get("holdout")]
        terms = terms_of(task)
        recent_cut = (_parse(now) - timedelta(days=14)).isoformat(timespec="seconds").replace("+00:00", "Z")
        scored = []
        for d in docs:
            hay = (d["body"] + " " + d["evidence"] + " " + json.dumps(d.get("tags") or {})).lower()
            rel = sum(1 for tm in terms if tm in hay)
            if terms and rel == 0:
                continue
            boost = (1.0 if d.get("verified") else 0.0) + (1.5 if d["scope"] == "grayson" or (d.get("tags") or {}).get("authority") == "grayson" else 0.0)
            boost += 0.75 if d["kind"] == "mistake" and d["created"] >= recent_cut else 0.0
            boost += 0.5 if d["kind"] == "lesson" else 0.0
            boost += 0.5 if d["agent"] == agent else 0.0
            scored.append((rel + boost, int(bool(d.get("verified"))), d["created"], d))
        scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        selected: list[dict] = []
        for rel, _, _, d in scored:
            item = {k: d.get(k) for k in ("id", "scope", "agent", "kind", "verified", "confidence", "expires", "source_path", "chunk_start", "chunk_end")}
            item.update(body=d["body"][:900], evidence=d["evidence"][:400], relevance=round(rel, 2), tags={k: v for k, v in (d.get("tags") or {}).items() if k in ("authority", "section", "lane", "criterion")})
            if len(packed(selected + [item])) <= max_chars:
                selected.append(item)
            if len(selected) >= limit:
                break
        if record:
            chars = len(packed(selected))
            self.store.put_learning("retrieval", {"id": digest(["retrieval", scope, agent, task[:500], run_ref, now, [s["id"] for s in selected]])[:32], "scope": scope, "agent": agent,
                                                  "task_sha": digest(task[:2000])[:16], "run_ref": run_ref, "memory_ids": [s["id"] for s in selected], "chars": chars, "created": now})
        return selected

    def context_json(self, scope: str, agent: str, task: str = "", **kw) -> str:
        return packed(self.context(scope, agent, task, **kw))

    # ---------------------------------------------------------------- ingestion
    def source_versions(self, source_path: str) -> list[dict]:
        return self.store.rows("SELECT source_sha, status, COUNT(*) n, MIN(created) first FROM memories WHERE source_path=? GROUP BY source_sha, status ORDER BY first", (source_path,))

    def supersede_source(self, source_path: str, keep_sha: str) -> int:
        """Older versions of the same source file: every active chunk whose sha differs is marked superseded."""
        old = self.store.rows("SELECT id FROM memories WHERE source_path=? AND status='active' AND source_sha IS NOT NULL AND source_sha<>?", (source_path, keep_sha))
        for r in old:
            self.patch(r["id"], status="superseded", superseded_by=f"sha256:{keep_sha}")
        return len(old)

    def ingest_text(self, scope: str, path: Path | str, *, agent: str = "*", kind: str = "example", ttl_days: float | None = None, tags: dict | None = None,
                    confidence: str = "unverified", chunk_size: int = 1600, overlap: int = 200, rel_to: Path | None = None) -> dict:
        """Index one explicitly selected text file as UNVERIFIED data. Chunks carry path, sha256, char offsets, timestamp,
        expiry, confidence and tags. Re-ingesting a changed file supersedes the older chunks; an unchanged file is a no-op."""
        source = Path(path).resolve()
        if scope in ("shared",):
            raise ValueError("Select a business (or grayson) scope and a supported text file")
        if source.suffix.lower() not in {".md", ".txt", ".csv", ".json", ".jsonl"}:
            raise ValueError(f"unsupported file type {source.suffix}")
        raw = source.read_bytes()
        if len(raw) > 2_000_000:
            raise ValueError("Split large files before indexing")
        text = raw.decode("utf-8-sig", errors="replace")
        sha = hashlib.sha256(raw).hexdigest()
        rel = str(source.relative_to(rel_to)) if rel_to else str(source)
        if self.store.rows("SELECT 1 FROM memories WHERE source_path=? AND source_sha=? LIMIT 1", (rel, sha)):
            return {"source": rel, "sha": sha, "new": [], "unchanged": True, "superseded": 0}
        keys = []
        step = max(200, chunk_size - overlap)
        for off in range(0, len(text), step):
            chunk = text[off:off + chunk_size]
            if chunk.strip():
                keys.append(self.remember(scope, agent, kind, chunk, f"{rel}; sha256={sha[:16]}; characters {off}:{off + len(chunk)}", verified=False, ttl_days=ttl_days,
                                          source_path=rel, source_sha=sha, chunk=(off, off + len(chunk)), confidence=confidence, tags=tags))
            if off + chunk_size >= len(text):
                break
        superseded = self.supersede_source(rel, sha)
        return {"source": rel, "sha": sha, "new": keys, "unchanged": False, "superseded": superseded}

    def ingest_items(self, scope: str, source: Path | str, items: list[dict], *, rel_to: Path | None = None, default_kind: str = "observation",
                     default_agent: str = "*", default_ttl: float | None = None) -> dict:
        """Structured ingestion: one memory per parsed item {body, evidence?, kind?, agent?, tags?, confidence?, ttl_days?, offset?}.
        Used by ingest.py for notebook sections, learned lines, run notes and JSONL rows. Same supersede-by-sha rule."""
        src = Path(source).resolve()
        raw = src.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        rel = str(src.relative_to(rel_to)) if rel_to else str(src)
        if self.store.rows("SELECT 1 FROM memories WHERE source_path=? AND source_sha=? LIMIT 1", (rel, sha)):
            return {"source": rel, "sha": sha, "new": [], "unchanged": True, "superseded": 0}
        keys = []
        for it in items:
            body = str(it.get("body") or "").strip()
            if not body:
                continue
            off = it.get("offset")
            ev = str(it.get("evidence") or "").strip() or f"{rel}; sha256={sha[:16]}" + (f"; line {it.get('line')}" if it.get("line") else "")
            keys.append(self.remember(it.get("scope") or scope, it.get("agent") or default_agent, it.get("kind") or default_kind, body[:12000], ev[:3000],
                                      verified=False, ttl_days=it.get("ttl_days", default_ttl), source_path=rel, source_sha=sha,
                                      chunk=(off, off + len(body)) if isinstance(off, int) else None, confidence=it.get("confidence", "unverified"), tags=it.get("tags")))
        superseded = self.supersede_source(rel, sha)
        return {"source": rel, "sha": sha, "new": keys, "unchanged": False, "superseded": superseded}

    # ---------------------------------------------------------------- evaluations (runs)
    def log(self, run_id: str, scope: str, agent: str, version: str, task: t.Any, artifact: t.Any, result: dict, *, mode: str = "offline", final: bool = True,
            artifact_ref: str = "", kind: str = "score", task_id: str | None = None, attempt: int | None = None, usage: dict | None = None, extra: dict | None = None) -> str:
        """One row per evaluated attempt with a STABLE id. The same id with the same content is a no-op; the same id
        with different content is refused (never silently overwritten)."""
        if mode not in {"offline", "production"}:
            raise ValueError("Separate offline tests from production work")
        if kind not in {"score", "run", "error"}:
            raise ValueError("kind is score | run | error")
        if not run_id or not isinstance(run_id, str):
            raise ValueError("run_id is required and must be stable")
        payload = {"task": task, "artifact_hash": digest(artifact) if artifact is not None else None, "artifact_ref": artifact_ref, "evaluation": result,
                   "usage": usage or {"tokens": "unknown", "cost_usd": "unknown"}, "extra": extra or {}}
        signature = {"scope": scope, "agent": agent, "version": version, "rubric_id": result.get("rubric_id") if isinstance(result, dict) else None, "mode": mode,
                     "final": bool(final), "score": result.get("score") if isinstance(result, dict) else None, "passed": bool(result.get("passed")) if isinstance(result, dict) else False,
                     "kind": kind, "payload": payload}
        old = self.store.rows("SELECT doc FROM evaluations WHERE id=?", (run_id,))
        if old:
            od = json.loads(old[0]["doc"])
            osig = {k: od.get(k) for k in signature if k != "payload"}
            osig["payload"] = od.get("payload")
            if packed(osig) != packed(signature):
                raise ValueError(f"Run ID {run_id} already exists with different results")
            return run_id
        row = {"id": run_id, "task_id": task_id or run_id.split(":")[0], "attempt": attempt, "artifact_ref": artifact_ref, "artifact_hash": payload["artifact_hash"],
               "created": self.now(), **signature}
        self.store.put_learning("evaluation", row)
        return run_id

    def log_run(self, run_id: str, scope: str, agent: str, *, task: str, outcome: str, mode: str = "production", version: str | None = None, minutes: float | None = None,
                est_tokens: int | None = None, loaded_bytes: int | None = None, note: str = "", needs_you: str = "", started: str | None = None, finished: str | None = None,
                stages: list | None = None, skipped: list | None = None, extra: dict | None = None) -> str:
        """A completed crew run (from runlog.py). No score is invented: score stays None; outcome is what the run said."""
        result = {"score": None, "passed": outcome == "done" and not needs_you, "outcome": outcome, "rubric_id": None, "blockers": ([needs_you] if needs_you else []) + ([f"outcome {outcome}"] if outcome != "done" else []),
                  "missing": [], "gaps": []}
        usage = {"est_tokens_proxy": est_tokens, "loaded_bytes": loaded_bytes, "minutes": minutes, "note": "estTokens is loaded instruction bytes / 4 (shared/logging.md); provider tokens are not exposed"}
        return self.log(run_id, scope, agent, version or "runlog", {"task": task, "stages": stages or [], "skipped": skipped or [], "started": started, "finished": finished}, None, result,
                        mode=mode, final=True, kind="run", task_id=task, usage=usage, extra={"note": note[:300], "needs_you": needs_you[:300], **(extra or {})})

    def log_error(self, run_id: str, scope: str, agent: str, *, task: t.Any, error: str, error_class: str = "tool", mode: str = "offline", version: str = "unknown",
                  attempt: int | None = None, task_id: str | None = None) -> str:
        """A tool error, budget or time-limit failure: recorded with NO score (score None, passed False)."""
        result = {"score": None, "passed": False, "rubric_id": None, "blockers": [f"{error_class}: {str(error)[:300]}"], "missing": ["all"], "gaps": [], "error_class": error_class}
        return self.log(run_id, scope, agent, version, task, None, result, mode=mode, final=True, kind="error", task_id=task_id, attempt=attempt)

    def evaluations(self, scope: str | None = None, agent: str | None = None, *, mode: str | None = None, kind: str | None = None, rubric_id: str | None = None,
                    since: str | None = None, final_only: bool = True, limit: int = 2000, include_holdout: bool = True) -> list[dict]:
        """include_holdout=False drops rows tagged extra.holdout (saved held-out inspections): used by diagnose so no
        holdout answer reaches an idea prompt. Stats keep them: they are real production inspections."""
        sql, args = "SELECT doc FROM evaluations WHERE 1=1", []
        if not include_holdout:
            sql += " AND COALESCE(json_extract(doc,'$.payload.extra.holdout'),0) IN (0,'false')"
        for col, val in (("scope", scope), ("agent", agent), ("mode", mode), ("kind", kind), ("rubric_id", rubric_id)):
            if val is not None:
                sql += f" AND {col}=?"; args.append(val)
        if since:
            sql += " AND created>=?"; args.append(since)
        if final_only:
            sql += " AND final=1"
        sql += " ORDER BY created DESC LIMIT ?"; args.append(limit)
        return [json.loads(r["doc"]) for r in self.store.rows(sql, tuple(args))]

    def stats(self, scope: str | None = None, agent: str | None = None, mode: str | None = None) -> list[dict]:
        """Per (scope, agent, version, rubric, mode): completed, scored, mean, passed, pass rate, aim rate (95+ where the
        rubric aims there). Only final rows count; errors are counted apart. Incompatible rubrics never share a row."""
        rows = self.evaluations(scope, agent, mode=mode, final_only=True, limit=100000)
        groups: dict[tuple, dict] = {}
        for d in rows:
            ev = d.get("payload", {}).get("evaluation") or {}
            key = (d["scope"], d["agent"], d.get("version") or "", d.get("rubric_id") or "", d["mode"], d.get("kind") or "score")
            g = groups.setdefault(key, {"scope": key[0], "agent": key[1], "version": key[2], "rubric": key[3], "mode": key[4], "kind": key[5],
                                        "completed": 0, "scored": 0, "sum": 0.0, "passed": 0, "aim_hits": 0, "errors": 0, "aim": ev.get("aim"), "target": ev.get("target"), "last": ""})
            g["completed"] += 1
            if d.get("kind") == "error":
                g["errors"] += 1
            if d.get("score") is not None:
                g["scored"] += 1
                g["sum"] += float(d["score"])
                aim = ev.get("aim") or 95
                if float(d["score"]) >= float(aim):
                    g["aim_hits"] += 1
            if d.get("passed"):
                g["passed"] += 1
            g["last"] = max(g["last"], d.get("created") or "")
        out = []
        for g in groups.values():
            g["mean_score"] = round(g["sum"] / g["scored"], 2) if g["scored"] else None
            g["pass_rate"] = round(100.0 * g["passed"] / g["completed"], 1) if g["completed"] else None
            g["aim_rate"] = round(100.0 * g["aim_hits"] / g["scored"], 1) if g["scored"] else None
            g.pop("sum")
            out.append(g)
        return sorted(out, key=lambda g: (g["scope"], g["agent"], g["mode"], g["rubric"], g["version"]))

    def losses(self, scope: str, agent: str | None = None, *, rubric_id: str | None = None, mode: str | None = None, since: str | None = None) -> list[dict]:
        """Weighted points lost per criterion across scored, final evaluations: the ranked list the repair loop works from."""
        rows = self.evaluations(scope, agent, mode=mode, kind="score", rubric_id=rubric_id, since=since, limit=100000)
        acc: dict[str, dict] = {}
        for d in rows:
            ev = d.get("payload", {}).get("evaluation") or {}
            for g in ev.get("gaps") or []:
                a = acc.setdefault(g["criterion"], {"criterion": g["criterion"], "n": 0, "lost": 0.0, "worst": None, "evidence": []})
                a["n"] += 1
                a["lost"] += float(g.get("lost_points") or 0)
                if a["worst"] is None or g.get("lost_points", 0) > a["worst"]:
                    a["worst"] = g.get("lost_points")
                if g.get("evidence") and len(a["evidence"]) < 3:
                    a["evidence"].append(str(g["evidence"])[:160])
        out = [{**a, "avg_lost": round(a["lost"] / a["n"], 2), "lost": round(a["lost"], 2)} for a in acc.values()]
        return sorted(out, key=lambda a: a["avg_lost"], reverse=True)

    def repeated_failures(self, scope: str, agent: str | None = None, *, since: str | None = None, min_count: int = 2) -> list[dict]:
        """Blockers / top gaps that recur across final evaluations and mistake memories, normalised to a short key."""
        counts: dict[str, dict] = {}

        def bump(key: str, ref: str, when: str):
            k = re.sub(r"[^a-z ]+", " ", key.lower()).strip()
            k = re.sub(r"\s+", " ", k)[:70]
            if not k:
                return
            c = counts.setdefault(k, {"pattern": k, "count": 0, "refs": [], "last": ""})
            c["count"] += 1
            if len(c["refs"]) < 5:
                c["refs"].append(ref)
            c["last"] = max(c["last"], when or "")

        for d in self.evaluations(scope, agent, since=since, limit=100000):
            ev = d.get("payload", {}).get("evaluation") or {}
            for b in ev.get("blockers") or []:
                bump(str(b).split("(")[0], d["id"], d.get("created"))
            gaps = ev.get("gaps") or []
            if gaps and not ev.get("passed") and ev.get("score") is not None:
                top = gaps[0]
                bump(f"lost most on {top['criterion']}", d["id"], d.get("created"))
        sql, args = "SELECT id, body, created FROM memories WHERE scope=? AND kind='mistake' AND status='active'", [scope]
        if agent:
            sql += " AND agent IN (?, '*')"; args.append(agent)
        if since:
            sql += " AND created>=?"; args.append(since)
        for r in self.store.rows(sql, tuple(args)):
            body = r["body"]
            key = body[:80]
            if body.lstrip().startswith("{"):
                try:
                    d = json.loads(body)
                    gaps = d.get("gaps") or []
                    if d.get("blockers"):
                        key = "blocker: " + str(d["blockers"][0]).split("(")[0]
                    elif gaps:
                        key = f"lost most on {gaps[0].get('criterion')}"
                    elif d.get("error"):
                        key = "error: " + str(d["error"])[:60]
                except (json.JSONDecodeError, AttributeError):
                    pass
            bump(key, r["id"], r["created"])
        return sorted([c for c in counts.values() if c["count"] >= min_count], key=lambda c: (c["count"], c["last"]), reverse=True)

    def usefulness(self, scope: str, agent: str | None = None, since: str | None = None) -> list[dict]:
        """For every memory shown to a task: how many of those tasks later passed or failed (correlation, not cause)."""
        sql, args = "SELECT memory_ids, run_ref FROM retrievals WHERE scope=? AND run_ref IS NOT NULL", [scope]
        if agent:
            sql += " AND agent=?"; args.append(agent)
        if since:
            sql += " AND created>=?"; args.append(since)
        shown: dict[str, dict] = {}
        for r in self.store.rows(sql, tuple(args)):
            ev = self.store.rows("SELECT passed, score, kind FROM evaluations WHERE final=1 AND (task_id=? OR id=? OR id LIKE ?) ORDER BY created DESC LIMIT 1", (r["run_ref"], r["run_ref"], r["run_ref"] + ":%"))
            for mid in json.loads(r["memory_ids"]):
                s = shown.setdefault(mid, {"memory_id": mid, "retrieved": 0, "passed": 0, "failed": 0, "unknown": 0})
                s["retrieved"] += 1
                if not ev:
                    s["unknown"] += 1
                elif ev[0]["passed"]:
                    s["passed"] += 1
                else:
                    s["failed"] += 1
        return sorted(shown.values(), key=lambda s: s["retrieved"], reverse=True)

    def freshness(self, scope: str, agent: str | None = None) -> dict:
        now = self.now()
        sql, args = "SELECT status, verified, kind, created, expires, source_path FROM memories WHERE scope IN (?, 'grayson', 'shared')", [scope]
        if agent:
            sql += " AND agent IN (?, '*')"; args.append(agent)
        rows = self.store.rows(sql, tuple(args))
        active = [r for r in rows if r["status"] == "active" and r["expires"] > now]
        return {"active": len(active), "expired": sum(1 for r in rows if r["status"] == "active" and r["expires"] <= now),
                "superseded": sum(1 for r in rows if r["status"] == "superseded"), "retracted": sum(1 for r in rows if r["status"] == "retracted"),
                "verified": sum(1 for r in active if r["verified"]), "by_kind": {k: sum(1 for r in active if r["kind"] == k) for k in sorted(KINDS)},
                "newest": max((r["created"] for r in active), default=None), "oldest_active": min((r["created"] for r in active), default=None),
                "sources": len({r["source_path"] for r in active if r["source_path"]}), "retrieval_cost_chars_avg": self._avg_retrieval_chars(scope, agent)}

    def _avg_retrieval_chars(self, scope: str, agent: str | None) -> float | None:
        sql, args = "SELECT AVG(chars) a, COUNT(*) n FROM retrievals WHERE scope=?", [scope]
        if agent:
            sql += " AND agent=?"; args.append(agent)
        r = self.store.rows(sql, tuple(args))
        return round(r[0]["a"], 1) if r and r[0]["n"] else None

    # ---------------------------------------------------------------- ideas and experiments
    IDEA_FIELDS = {"hypothesis", "change", "baseline", "metric", "success", "stop", "budget", "sources"}

    def propose(self, scope: str, agent: str, proposal: dict, *, max_per_day: int = MAX_IDEAS_PER_DAY) -> str:
        """Queue an experiment idea. Proposing never runs or promotes anything. Every idea needs supporting observation /
        source ids that EXIST in this store, one concrete change, a baseline, a metric, success and stop conditions and a
        maximum test budget. Ideas are deduplicated across agents by their normalised change; at most `max_per_day`
        new ideas per scope per day."""
        if not isinstance(proposal, dict) or not self.IDEA_FIELDS <= set(proposal):
            raise ValueError("Idea needs: " + ", ".join(sorted(self.IDEA_FIELDS)))
        if any(not str(proposal[k]).strip() for k in self.IDEA_FIELDS):
            raise ValueError("Every experiment field needs a value")
        sources = proposal["sources"]
        if not isinstance(sources, list) or not sources or any(not isinstance(s, str) or not s.strip() for s in sources):
            raise ValueError("Ideas need real observation/source references")
        known = []
        for s in sources:
            if self.store.rows("SELECT 1 FROM memories WHERE id=?", (s,)) or self.store.rows("SELECT 1 FROM evaluations WHERE id=? OR task_id=?", (s, s)) \
                    or self.store.rows("SELECT 1 FROM experiments WHERE id=?", (s,)):
                known.append(s)
        if not known:
            raise ValueError("none of the cited sources is a memory, evaluation or experiment id in this store")
        normalized = " ".join(str(proposal["change"]).lower().split())
        key = digest([scope, normalized])[:24]
        if self.store.rows("SELECT 1 FROM ideas WHERE id=?", (key,)):
            return key  # same change already queued for this business (any agent)
        today = self.now()[:10]
        n_today = self.store.rows("SELECT COUNT(*) n FROM ideas WHERE scope=? AND substr(created,1,10)=?", (scope, today))[0]["n"]
        if n_today >= max_per_day:
            raise ValueError(f"idea budget reached: {max_per_day} new ideas per business per day")
        row = {"id": key, "scope": scope, "agent": agent, "status": "proposed", "created": self.now(), "updated": self.now(),
               "proposal": {k: proposal[k] for k in sorted(proposal)}, "sources_known": known, "sources_unknown": [s for s in sources if s not in known]}
        self.store.put_learning("idea", row)
        return key

    def ideas(self, scope: str | None = None, agent: str | None = None, status: str | None = None) -> list[dict]:
        sql, args = "SELECT doc FROM ideas WHERE 1=1", []
        for col, val in (("scope", scope), ("agent", agent), ("status", status)):
            if val is not None:
                sql += f" AND {col}=?"; args.append(val)
        return [json.loads(r["doc"]) for r in self.store.rows(sql + " ORDER BY created DESC", tuple(args))]

    def idea(self, idea_id: str) -> dict | None:
        r = self.store.rows("SELECT doc FROM ideas WHERE id=?", (idea_id,))
        return json.loads(r[0]["doc"]) if r else None

    def idea_status(self, idea_id: str, status: str, note: str = "") -> None:
        if status not in ("proposed", "running", "decided", "dropped"):
            raise ValueError("status is proposed | running | decided | dropped")
        d = self.idea(idea_id)
        if not d:
            raise ValueError(f"no idea {idea_id}")
        d["status"], d["updated"] = status, self.now()
        if note:
            d.setdefault("notes", []).append({"at": self.now(), "text": note[:300]})
        self.store.put_learning("idea", d)

    def experiment_start(self, idea_id: str, *, baseline: dict, metric: str, success: str, stop: str, budget: str | dict, holdout_case_ids: list[str] | None = None,
                         by: str = "engine", note: str = "") -> str:
        """Start a test for one idea against an UNCHANGED baseline. Results are stored apart from the proposal."""
        idea = self.idea(idea_id)
        if not idea:
            raise ValueError(f"no idea {idea_id}")
        if not isinstance(baseline, dict) or not baseline:
            raise ValueError("baseline must describe the unchanged version being compared against")
        for cid in holdout_case_ids or []:
            if not self.store.rows("SELECT 1 FROM eval_cases WHERE id=? AND split='holdout'", (cid,)):
                raise ValueError(f"{cid} is not a holdout eval case")
        eid = "exp_" + digest([idea_id, self.now(), by])[:12]
        row = {"id": eid, "idea_id": idea_id, "scope": idea["scope"], "agent": idea["agent"], "status": "running", "samples": 0, "decision": None,
               "baseline": baseline, "metric": metric, "success": success, "stop": stop, "budget": budget, "holdout_case_ids": list(holdout_case_ids or []),
               "results": [], "conflicts": [], "created": self.now(), "updated": self.now(), "by": by, "note": note[:300]}
        self.store.put_learning("experiment", row)
        self.idea_status(idea_id, "running", f"experiment {eid} started")
        return eid

    def experiment(self, exp_id: str) -> dict | None:
        r = self.store.rows("SELECT doc FROM experiments WHERE id=?", (exp_id,))
        return json.loads(r[0]["doc"]) if r else None

    def experiments(self, scope: str | None = None, status: str | None = None, agent: str | None = None) -> list[dict]:
        sql, args = "SELECT doc FROM experiments WHERE 1=1", []
        for col, val in (("scope", scope), ("status", status), ("agent", agent)):
            if val is not None:
                sql += f" AND {col}=?"; args.append(val)
        return [json.loads(r["doc"]) for r in self.store.rows(sql + " ORDER BY created DESC", tuple(args))]

    def experiment_record(self, exp_id: str, *, arm: str, value: float, n: int, source: str, note: str = "", conflict: bool = False) -> dict:
        """One observed result for one arm ('baseline' or 'candidate'). n = how many samples it covers. A one-off (n=1)
        is stored as a one-off; it never changes a decision by itself. `conflict=True` marks a result that disagrees
        with earlier ones; the experiment cannot be decided keep while a conflict is open."""
        e = self.experiment(exp_id)
        if not e:
            raise ValueError(f"no experiment {exp_id}")
        if e["status"] != "running":
            raise ValueError(f"experiment {exp_id} is {e['status']}")
        if arm not in ("baseline", "candidate"):
            raise ValueError("arm is baseline | candidate")
        n = int(number(n, 1, 1_000_000))
        if not source.strip():
            raise ValueError("a result needs its source (a doc id, a path, a URL)")
        rec = {"at": self.now(), "arm": arm, "value": float(value), "n": n, "source": source[:300], "note": note[:300], "conflict": bool(conflict)}
        e["results"].append(rec)
        e["samples"] = sum(int(r["n"]) for r in e["results"] if r["arm"] == "candidate")
        if conflict:
            e["conflicts"].append(rec)
        e["updated"] = self.now()
        self.store.put_learning("experiment", e)
        return e

    def experiment_resolve_conflicts(self, exp_id: str, by: str, note: str) -> None:
        e = self.experiment(exp_id)
        if not e:
            raise ValueError(f"no experiment {exp_id}")
        e["conflicts"] = []
        e.setdefault("notes", []).append({"at": self.now(), "by": by, "text": "conflicts resolved: " + note[:300]})
        e["updated"] = self.now()
        self.store.put_learning("experiment", e)

    def experiment_decide(self, exp_id: str, decision: str, *, by: str, note: str = "") -> dict:
        """keep | revert | inconclusive. keep requires MIN_EXPERIMENT_SAMPLES candidate samples and no open conflict."""
        if decision not in ("keep", "revert", "inconclusive"):
            raise ValueError("decision is keep | revert | inconclusive")
        e = self.experiment(exp_id)
        if not e:
            raise ValueError(f"no experiment {exp_id}")
        if decision == "keep":
            if int(e.get("samples", 0)) < MIN_EXPERIMENT_SAMPLES:
                raise ValueError(f"keep needs {MIN_EXPERIMENT_SAMPLES}+ candidate samples; have {e.get('samples', 0)}")
            if e.get("conflicts"):
                raise ValueError("keep is not allowed while results conflict; resolve them first")
            if not any(r["arm"] == "baseline" for r in e["results"]):
                raise ValueError("keep needs at least one baseline result to compare against")
        e["status"], e["decision"], e["decided_by"], e["decided_at"], e["decision_note"], e["updated"] = "decided", decision, by, self.now(), note[:300], self.now()
        self.store.put_learning("experiment", e)
        self.idea_status(e["idea_id"], "decided", f"{decision} by {by}")
        self.store.audit(AuditEvent.make(by, "experiment_decided", exp_id, f"{decision}: {note[:200]}"))
        return e

    # ---------------------------------------------------------------- workflow / prompt versions (promotion with rollback)
    def workflow_put(self, scope: str, agent: str, name: str, body: t.Any, *, status: str = "candidate", evidence: dict | None = None, by: str = "engine") -> dict:
        if status not in ("candidate", "active", "retired"):
            raise ValueError("status is candidate | active | retired")
        vs = self.workflow_versions(scope, agent, name)
        version = (max(v["version"] for v in vs) + 1) if vs else 1
        row = {"id": f"wf_{digest([scope, agent, name, version])[:12]}", "scope": scope, "agent": agent, "name": name, "version": version, "status": status,
               "body": body, "body_sha": digest(body)[:16], "evidence": evidence or {}, "created": self.now(), "by": by}
        if status == "active":
            for v in vs:
                if v["status"] == "active":
                    v["status"] = "retired"; v["retired_at"] = self.now(); v["retired_by"] = f"version {version}"
                    self.store.put_learning("workflow_version", v)
        self.store.put_learning("workflow_version", row)
        return row

    def workflow_versions(self, scope: str, agent: str, name: str) -> list[dict]:
        return [json.loads(r["doc"]) for r in self.store.rows("SELECT doc FROM workflow_versions WHERE scope=? AND agent=? AND name=? ORDER BY version", (scope, agent, name))]

    def workflow_active(self, scope: str, agent: str, name: str) -> dict | None:
        return next((v for v in reversed(self.workflow_versions(scope, agent, name)) if v["status"] == "active"), None)

    def workflow_promote(self, scope: str, agent: str, name: str, version: int, *, experiment_id: str, by: str = "engine") -> dict:
        """A candidate becomes active ONLY on an experiment decided keep with enough samples; the previous active
        version is retired, never deleted, so `workflow_rollback` can bring it back."""
        e = self.experiment(experiment_id)
        if not e or e["decision"] != "keep":
            raise ValueError("promotion needs an experiment decided keep")
        if int(e.get("samples", 0)) < MIN_EXPERIMENT_SAMPLES or e.get("conflicts"):
            raise ValueError("experiment lacks samples or has open conflicts")
        vs = self.workflow_versions(scope, agent, name)
        target = next((v for v in vs if v["version"] == version), None)
        if not target:
            raise ValueError(f"no version {version} of {name}")
        if target["status"] == "active":
            return target
        for v in vs:
            if v["status"] == "active":
                v["status"] = "retired"; v["retired_at"] = self.now(); v["retired_by"] = f"promotion of v{version} ({experiment_id})"
                self.store.put_learning("workflow_version", v)
        target["status"] = "active"; target["promoted_at"] = self.now(); target["promoted_by"] = by; target["experiment_id"] = experiment_id
        self.store.put_learning("workflow_version", target)
        self.store.audit(AuditEvent.make(by, "workflow_promoted", target["id"], f"{name} v{version} via {experiment_id}"))
        return target

    def workflow_rollback(self, scope: str, agent: str, name: str, to_version: int, *, by: str, reason: str) -> dict:
        vs = self.workflow_versions(scope, agent, name)
        target = next((v for v in vs if v["version"] == to_version), None)
        if not target:
            raise ValueError(f"no version {to_version} of {name}")
        for v in vs:
            if v["status"] == "active" and v["version"] != to_version:
                v["status"] = "retired"; v["retired_at"] = self.now(); v["retired_by"] = f"rollback to v{to_version}: {reason[:120]}"
                self.store.put_learning("workflow_version", v)
        target["status"] = "active"; target["rolled_back_at"] = self.now(); target["rolled_back_by"] = by
        self.store.put_learning("workflow_version", target)
        self.store.audit(AuditEvent.make(by, "workflow_rollback", target["id"], f"{name} back to v{to_version}: {reason[:200]}"))
        return target

    # ---------------------------------------------------------------- eval cases (saved real tasks + holdouts)
    def eval_case_put(self, scope: str, agent: str, *, split: str, task: dict, expected: dict, source: str, rubric_id: str | None = None, case_id: str | None = None) -> str:
        if split not in ("train", "holdout"):
            raise ValueError("split is train | holdout")
        cid = case_id or ("case_" + digest([scope, agent, split, task, expected])[:12])
        if self.store.rows("SELECT 1 FROM eval_cases WHERE id=?", (cid,)):
            return cid  # already on file: no second journal line
        self.store.put_learning("eval_case", {"id": cid, "scope": scope, "agent": agent, "split": split, "rubric_id": rubric_id, "task": task, "expected": expected,
                                              "source": source, "created": self.now()})
        return cid

    def eval_cases(self, scope: str | None = None, agent: str | None = None, split: str | None = None) -> list[dict]:
        sql, args = "SELECT doc FROM eval_cases WHERE 1=1", []
        for col, val in (("scope", scope), ("agent", agent), ("split", split)):
            if val is not None:
                sql += f" AND {col}=?"; args.append(val)
        return [json.loads(r["doc"]) for r in self.store.rows(sql + " ORDER BY created", tuple(args))]
