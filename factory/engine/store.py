"""Persistent store for the engine (add-on Phase 3).

Two layers, one truth:
- `journal.jsonl` — append-only, committed to git. Every write is one JSON line
  {"v":1,"at":…,"kind":"task|run|approval|audit|usage|product|plan|integration|control","data":{…}}.
  It merges across runners (append-only) and survives anything short of deleting the repo.
- `state.sqlite` — a derived SQL index rebuilt from the journal (`rebuild()`), ignored by git.
  Queries go here; writes go to BOTH (journal first, so a crash never loses a record).

Migrations are versioned in `MIGRATIONS`; `Store.open()` applies the missing ones and records them in
`schema_migrations`. No third-party dependencies.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import typing as t
from pathlib import Path

from .contracts import (SCHEMA_VERSION, AgentContract, Approval, AuditEvent, DistributionPlan, IntegrationHealth, ModelUsage,
                        ProductManifest, Run, Task, TaskStatus, now_iso, scrub)

HERE = Path(__file__).resolve().parent


def resolve_db_dir() -> Path:
    """Where the durable records live. GM_ENGINE_DB_DIR wins; otherwise the committed journal in
    factory/engine/state (what the GitHub worker and the crews share), else the local factory/engine/db."""
    env = os.environ.get("GM_ENGINE_DB_DIR")
    if env:
        return Path(env)
    state = HERE / "state"
    if (state / "journal.jsonl").exists():
        return state
    return HERE / "db"


DB_DIR = resolve_db_dir()

MIGRATIONS: list[tuple[int, str]] = [
    (1, """
    CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS tasks(
      id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL,
      priority INTEGER NOT NULL DEFAULT 5, idempotency_key TEXT, attempts INTEGER NOT NULL DEFAULT 0,
      approval_id TEXT, next_eligible_at TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      doc TEXT NOT NULL);
    CREATE UNIQUE INDEX IF NOT EXISTS tasks_idem ON tasks(idempotency_key) WHERE idempotency_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS tasks_status ON tasks(status, priority, created_at);
    CREATE TABLE IF NOT EXISTS runs(
      id TEXT PRIMARY KEY, task_id TEXT NOT NULL, agent_id TEXT NOT NULL, attempt INTEGER NOT NULL,
      status TEXT, started_at TEXT NOT NULL, finished_at TEXT, heartbeat_at TEXT, error_class TEXT,
      tokens_in INTEGER, tokens_out INTEGER, cost_usd REAL, doc TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS runs_task ON runs(task_id, attempt);
    CREATE TABLE IF NOT EXISTS approvals(
      id TEXT PRIMARY KEY, task_id TEXT, capability TEXT NOT NULL, status TEXT NOT NULL,
      requested_at TEXT NOT NULL, decided_at TEXT, doc TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit(
      id TEXT PRIMARY KEY, at TEXT NOT NULL, who TEXT NOT NULL, action TEXT NOT NULL, subject TEXT NOT NULL, detail TEXT);
    CREATE INDEX IF NOT EXISTS audit_at ON audit(at);
    CREATE TABLE IF NOT EXISTS model_usage(
      id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, run_id TEXT, provider TEXT NOT NULL, model TEXT NOT NULL,
      tokens_in INTEGER, tokens_out INTEGER, cost_usd REAL, cached INTEGER NOT NULL DEFAULT 0, calls INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS products(
      product_id TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL, title TEXT, lane TEXT,
      listing_status TEXT, distribution_status TEXT, doc TEXT NOT NULL, PRIMARY KEY(product_id, version));
    CREATE TABLE IF NOT EXISTS distribution_plans(
      id TEXT PRIMARY KEY, product_id TEXT NOT NULL, product_version INTEGER NOT NULL, status TEXT NOT NULL,
      approval_id TEXT, doc TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS integrations(
      id TEXT PRIMARY KEY, state TEXT NOT NULL, last_ok_at TEXT, last_error TEXT, checked_at TEXT, note TEXT);
    CREATE TABLE IF NOT EXISTS control(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
    """),
    (2, """
    CREATE TABLE IF NOT EXISTS agents(
      id TEXT NOT NULL, version INTEGER NOT NULL, role TEXT NOT NULL, name TEXT NOT NULL, registered_at TEXT NOT NULL,
      skill_sha TEXT, doc TEXT NOT NULL, PRIMARY KEY(id, version));
    CREATE TABLE IF NOT EXISTS projects(
      id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, doc TEXT NOT NULL);
    """),
    (3, """
    CREATE TABLE IF NOT EXISTS llm_cache(
      key TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL, prompt_version TEXT NOT NULL, data_version TEXT NOT NULL,
      created_at TEXT NOT NULL, expires_at TEXT NOT NULL, text TEXT NOT NULL, usage TEXT, hits INTEGER NOT NULL DEFAULT 0);
    CREATE INDEX IF NOT EXISTS llm_cache_exp ON llm_cache(expires_at);
    """),
    (4, """
    CREATE TABLE IF NOT EXISTS publications(
      id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, channel TEXT NOT NULL, idem_key TEXT NOT NULL UNIQUE, status TEXT NOT NULL,
      adapter TEXT NOT NULL, created_at TEXT NOT NULL, checked_at TEXT, verified INTEGER, external_id TEXT, doc TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS publications_plan ON publications(plan_id);
    CREATE TABLE IF NOT EXISTS metrics(
      id TEXT PRIMARY KEY, at TEXT NOT NULL, channel TEXT NOT NULL, ref TEXT NOT NULL, plan_id TEXT, product_id TEXT,
      kind TEXT NOT NULL, value REAL NOT NULL, source TEXT NOT NULL, retrieved_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS metrics_ref ON metrics(ref, kind, at);
    CREATE INDEX IF NOT EXISTS metrics_plan ON metrics(plan_id, kind);
    """),
    (5, """
    -- Phase 9: agent learning (factory/learning). Memories are scoped chunks with provenance; evaluations are
    -- one row per scored or logged run (stable ids, never silently overwritten); ideas and experiments are
    -- kept apart; retrievals record what each task was shown (context cost + later usefulness); workflow
    -- versions keep every prompt/checklist version for rollback; eval_cases hold saved real tasks and holdouts.
    CREATE TABLE IF NOT EXISTS memories(
      id TEXT PRIMARY KEY, scope TEXT NOT NULL, agent TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
      body TEXT NOT NULL, evidence TEXT NOT NULL, source_path TEXT, source_sha TEXT, chunk_start INTEGER, chunk_end INTEGER,
      confidence TEXT, verified INTEGER NOT NULL DEFAULT 0, tags TEXT, created TEXT NOT NULL, expires TEXT NOT NULL,
      supersedes TEXT, superseded_by TEXT, version INTEGER NOT NULL DEFAULT 1, doc TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS memories_scope ON memories(scope, agent, status, expires);
    CREATE INDEX IF NOT EXISTS memories_source ON memories(source_path, source_sha);
    CREATE TABLE IF NOT EXISTS evaluations(
      id TEXT PRIMARY KEY, scope TEXT NOT NULL, agent TEXT NOT NULL, kind TEXT NOT NULL, task_id TEXT, attempt INTEGER,
      version TEXT, rubric_id TEXT, mode TEXT NOT NULL, final INTEGER NOT NULL DEFAULT 1, score REAL, passed INTEGER NOT NULL DEFAULT 0,
      artifact_ref TEXT, artifact_hash TEXT, created TEXT NOT NULL, doc TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS evaluations_scope ON evaluations(scope, agent, mode, rubric_id, created);
    CREATE TABLE IF NOT EXISTS ideas(
      id TEXT PRIMARY KEY, scope TEXT NOT NULL, agent TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL, doc TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS experiments(
      id TEXT PRIMARY KEY, idea_id TEXT, scope TEXT NOT NULL, agent TEXT NOT NULL, status TEXT NOT NULL, samples INTEGER NOT NULL DEFAULT 0,
      decision TEXT, created TEXT NOT NULL, updated TEXT NOT NULL, doc TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS retrievals(
      id TEXT PRIMARY KEY, scope TEXT NOT NULL, agent TEXT NOT NULL, task_sha TEXT NOT NULL, run_ref TEXT, memory_ids TEXT NOT NULL,
      chars INTEGER NOT NULL, created TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS retrievals_run ON retrievals(run_ref);
    CREATE TABLE IF NOT EXISTS workflow_versions(
      id TEXT PRIMARY KEY, scope TEXT NOT NULL, agent TEXT NOT NULL, name TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL,
      created TEXT NOT NULL, doc TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS workflow_versions_name ON workflow_versions(scope, agent, name, version);
    CREATE TABLE IF NOT EXISTS eval_cases(
      id TEXT PRIMARY KEY, scope TEXT NOT NULL, agent TEXT NOT NULL, split TEXT NOT NULL, rubric_id TEXT, created TEXT NOT NULL, doc TEXT NOT NULL);
    """),
]


class Store:
    def __init__(self, db_dir: Path | str = DB_DIR):
        self.dir = Path(db_dir)
        self.journal = self.dir / "journal.jsonl"
        self.sqlite = self.dir / "state.sqlite"
        self.con: t.Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()  # handlers may run in a worker thread; one writer at a time

    # ---------------------------------------------------------------- lifecycle
    def open(self) -> "Store":
        self.dir.mkdir(parents=True, exist_ok=True)
        fresh = not self.sqlite.exists()
        self.con = sqlite3.connect(self.sqlite, isolation_level=None, check_same_thread=False)  # autocommit; guarded by _lock
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA journal_mode=WAL")
        self.migrate()
        # The index is derived: rebuild it when it is new, or when the journal changed behind its back (a git pull brought
        # another crew's lines, a crash cut a write). The marker file holds the journal size the index was built from.
        if self.journal.exists() and (fresh or self._marker_read() != self.journal.stat().st_size):
            self.rebuild()
        return self

    @property
    def _marker(self) -> Path:
        return self.dir / "state.sqlite-indexed"  # never -journal / -wal / -shm (SQLite reserves those); matches .gitignore state.sqlite-*

    def _marker_read(self) -> int | None:
        try:
            return int(self._marker.read_text().strip())
        except (OSError, ValueError):
            return None

    def _marker_write(self) -> None:
        try:
            self._marker.write_text(str(self.journal.stat().st_size if self.journal.exists() else 0))
        except OSError:
            pass

    def close(self) -> None:
        if self.con:
            self.con.close()
            self.con = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *a):
        self.close()

    def migrate(self) -> list[int]:
        assert self.con
        self.con.executescript(MIGRATIONS[0][1])  # creates schema_migrations + v1 tables
        done = {r[0] for r in self.con.execute("SELECT version FROM schema_migrations")}
        applied = []
        for v, sql in MIGRATIONS:
            if v in done:
                continue
            self.con.executescript(sql)
            self.con.execute("INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(?,?)", (v, now_iso()))
            applied.append(v)
        return applied

    def schema_version(self) -> int:
        assert self.con
        r = self.con.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
        return int(r[0] or 0)

    # ---------------------------------------------------------------- journal
    def _journal(self, kind: str, data: dict) -> None:
        line = json.dumps({"v": SCHEMA_VERSION, "at": now_iso(), "kind": kind, "data": data}, sort_keys=True, default=str)
        with self.journal.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        self._marker_write()

    DERIVED_TABLES = ("tasks", "runs", "approvals", "audit", "model_usage", "products", "distribution_plans", "integrations", "control", "agents", "projects",
                      "llm_cache", "publications", "metrics", "memories", "evaluations", "ideas", "experiments", "retrievals", "workflow_versions", "eval_cases")

    def rebuild(self) -> int:
        """Derive SQLite from the journal: the derived tables are cleared first, then every line is replayed (last write
        per id wins). Idempotent: rebuilding twice gives the same index (model_usage rows used to double on a second replay)."""
        assert self.con
        n = 0
        with self._lock:
            for tbl in self.DERIVED_TABLES:
                self.con.execute(f"DELETE FROM {tbl}")
        if not self.journal.exists():
            self._marker_write()
            return 0
        with self.journal.open(encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except json.JSONDecodeError:
                    continue  # a torn line from a crash never poisons the index
                self._apply(ev.get("kind"), ev.get("data") or {}, journal=False)
                n += 1
        self._marker_write()
        return n

    # ---------------------------------------------------------------- writes
    def _apply(self, kind: str, data: dict, journal: bool = True) -> None:
        with self._lock:
            self._apply_locked(kind, data, journal)

    def _apply_locked(self, kind: str, data: dict, journal: bool) -> None:
        assert self.con
        if journal:
            self._journal(kind, data)
        c = self.con
        if kind == "task":
            tk = Task.from_dict(data)
            c.execute("""INSERT INTO tasks(id,agent_id,kind,status,priority,idempotency_key,attempts,approval_id,next_eligible_at,created_at,updated_at,doc)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,attempts=excluded.attempts,
                         approval_id=excluded.approval_id,next_eligible_at=excluded.next_eligible_at,updated_at=excluded.updated_at,doc=excluded.doc""",
                      (tk.id, tk.spec.agent_id, tk.spec.kind, tk.status.value, tk.spec.priority, tk.spec.idempotency_key, tk.attempts,
                       tk.approval_id, tk.next_eligible_at, tk.created_at, tk.updated_at, tk.to_json()))
        elif kind == "run":
            r = Run.from_dict(data)
            u = r.usage
            c.execute("""INSERT INTO runs(id,task_id,agent_id,attempt,status,started_at,finished_at,heartbeat_at,error_class,tokens_in,tokens_out,cost_usd,doc)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,finished_at=excluded.finished_at,
                         heartbeat_at=excluded.heartbeat_at,error_class=excluded.error_class,tokens_in=excluded.tokens_in,tokens_out=excluded.tokens_out,
                         cost_usd=excluded.cost_usd,doc=excluded.doc""",
                      (r.id, r.task_id, r.agent_id, r.attempt, r.status.value if r.status else None, r.started_at, r.finished_at, r.heartbeat_at,
                       r.error_class, u.tokens_in if u else None, u.tokens_out if u else None, u.cost_usd if u else None, r.to_json()))
        elif kind == "approval":
            a = Approval.from_dict(data)
            c.execute("""INSERT INTO approvals(id,task_id,capability,status,requested_at,decided_at,doc) VALUES(?,?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET status=excluded.status,decided_at=excluded.decided_at,doc=excluded.doc""",
                      (a.id, a.task_id, a.capability.value, a.status.value, a.requested_at, a.decided_at, a.to_json()))
        elif kind == "audit":
            e = AuditEvent.from_dict(data)
            c.execute("INSERT OR IGNORE INTO audit(id,at,who,action,subject,detail) VALUES(?,?,?,?,?,?)",
                      (e.id, e.at, e.who, e.action, e.subject, e.detail))
        elif kind == "usage":
            u = ModelUsage.from_dict(data["usage"])
            c.execute("INSERT INTO model_usage(at,run_id,provider,model,tokens_in,tokens_out,cost_usd,cached,calls) VALUES(?,?,?,?,?,?,?,?,?)",
                      (data.get("at") or now_iso(), data.get("run_id"), u.provider, u.model, u.tokens_in, u.tokens_out, u.cost_usd, int(u.cached), u.calls))
        elif kind == "product":
            p = ProductManifest.from_dict(data)
            c.execute("""INSERT INTO products(product_id,version,created_at,title,lane,listing_status,distribution_status,doc) VALUES(?,?,?,?,?,?,?,?)
                         ON CONFLICT(product_id,version) DO UPDATE SET listing_status=excluded.listing_status,distribution_status=excluded.distribution_status,doc=excluded.doc""",
                      (p.product_id, p.version, p.created_at, p.title, p.lane, p.listing_status, p.distribution_status, p.to_json()))
        elif kind == "plan":
            d = DistributionPlan.from_dict(data)
            c.execute("""INSERT INTO distribution_plans(id,product_id,product_version,status,approval_id,doc) VALUES(?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET status=excluded.status,approval_id=excluded.approval_id,doc=excluded.doc""",
                      (d.id, d.product_id, d.product_version, d.status, d.approval_id, d.to_json()))
        elif kind == "integration":
            i = IntegrationHealth.from_dict(data)
            c.execute("""INSERT INTO integrations(id,state,last_ok_at,last_error,checked_at,note) VALUES(?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET state=excluded.state,last_ok_at=excluded.last_ok_at,last_error=excluded.last_error,checked_at=excluded.checked_at,note=excluded.note""",
                      (i.id, i.state.value, i.last_ok_at, scrub(i.last_error) if i.last_error else None, i.checked_at, i.note))
        elif kind == "agent":
            a = AgentContract.from_dict(data["contract"])
            c.execute("""INSERT INTO agents(id,version,role,name,registered_at,skill_sha,doc) VALUES(?,?,?,?,?,?,?)
                         ON CONFLICT(id,version) DO UPDATE SET skill_sha=excluded.skill_sha,doc=excluded.doc""",
                      (a.id, a.version, a.role.value, a.name, data.get("at") or now_iso(), data.get("skill_sha"), a.to_json()))
        elif kind == "project":
            c.execute("""INSERT INTO projects(id,goal,status,created_at,updated_at,doc) VALUES(?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET status=excluded.status,updated_at=excluded.updated_at,doc=excluded.doc""",
                      (data["id"], data["goal"], data["status"], data["created_at"], data["updated_at"], json.dumps(data, sort_keys=True)))
        elif kind == "cache":
            if data.get("op") == "hit":
                c.execute("UPDATE llm_cache SET hits=hits+1 WHERE key=?", (data["key"],))
            elif data.get("op") == "purge":
                c.execute("DELETE FROM llm_cache WHERE expires_at < ? OR data_version <> ?", (data.get("now") or now_iso(), data.get("keep_version", "")))
            else:
                c.execute("""INSERT INTO llm_cache(key,provider,model,prompt_version,data_version,created_at,expires_at,text,usage,hits) VALUES(?,?,?,?,?,?,?,?,?,0)
                             ON CONFLICT(key) DO UPDATE SET text=excluded.text,usage=excluded.usage,expires_at=excluded.expires_at,created_at=excluded.created_at""",
                          (data["key"], data["provider"], data["model"], data["prompt_version"], data["data_version"], data["created_at"], data["expires_at"], data["text"], json.dumps(data.get("usage"))))
        elif kind == "publication":
            d = data
            c.execute("""INSERT INTO publications(id,plan_id,channel,idem_key,status,adapter,created_at,checked_at,verified,external_id,doc) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET status=excluded.status,checked_at=excluded.checked_at,verified=excluded.verified,external_id=excluded.external_id,doc=excluded.doc""",
                      (d["id"], d["plan_id"], d["channel"], d["idem_key"], d["status"], d["adapter"], d["created_at"], d.get("checked_at"),
                       None if d.get("verified") is None else int(bool(d["verified"])), d.get("external_id"), json.dumps(d, sort_keys=True)))
        elif kind == "metric":
            d = data
            c.execute("INSERT OR IGNORE INTO metrics(id,at,channel,ref,plan_id,product_id,kind,value,source,retrieved_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (d["id"], d["at"], d["channel"], d["ref"], d.get("plan_id"), d.get("product_id"), d["kind"], float(d["value"]), d["source"], d["retrieved_at"]))
        elif kind == "control":
            c.execute("INSERT INTO control(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                      (data["key"], json.dumps(data["value"]), data.get("at") or now_iso()))
        # ---- Phase 9 learning rows (factory/learning). Each is {"op": "put"|"patch", ...}; a patch changes status-like
        # fields of an existing row only, so a replayed journal reaches the same end state.
        elif kind == "memory":
            d = data
            if d.get("op") == "patch":
                sets = {k: d[k] for k in ("status", "verified", "superseded_by", "confidence", "expires") if k in d}
                if sets:
                    c.execute("UPDATE memories SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?", (*sets.values(), d["id"]))
                    row = c.execute("SELECT doc FROM memories WHERE id=?", (d["id"],)).fetchone()
                    if row:
                        doc = json.loads(row["doc"]); doc.update(sets)
                        c.execute("UPDATE memories SET doc=? WHERE id=?", (json.dumps(doc, sort_keys=True), d["id"]))
            else:
                c.execute("""INSERT OR IGNORE INTO memories(id,scope,agent,kind,status,body,evidence,source_path,source_sha,chunk_start,chunk_end,confidence,verified,tags,
                             created,expires,supersedes,superseded_by,version,doc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (d["id"], d["scope"], d["agent"], d["kind"], d.get("status", "active"), d["body"], d["evidence"], d.get("source_path"), d.get("source_sha"),
                           d.get("chunk_start"), d.get("chunk_end"), d.get("confidence"), int(bool(d.get("verified"))), json.dumps(d.get("tags") or {}, sort_keys=True),
                           d["created"], d["expires"], d.get("supersedes"), d.get("superseded_by"), int(d.get("version", 1)), json.dumps(d, sort_keys=True)))
        elif kind == "evaluation":
            d = data
            c.execute("""INSERT OR IGNORE INTO evaluations(id,scope,agent,kind,task_id,attempt,version,rubric_id,mode,final,score,passed,artifact_ref,artifact_hash,created,doc)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (d["id"], d["scope"], d["agent"], d.get("kind", "score"), d.get("task_id"), d.get("attempt"), d.get("version"), d.get("rubric_id"), d["mode"],
                       int(bool(d.get("final", True))), d.get("score"), int(bool(d.get("passed"))), d.get("artifact_ref"), d.get("artifact_hash"), d["created"], json.dumps(d, sort_keys=True)))
        elif kind == "idea":
            d = data
            c.execute("""INSERT INTO ideas(id,scope,agent,status,created,updated,doc) VALUES(?,?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET status=excluded.status,updated=excluded.updated,doc=excluded.doc""",
                      (d["id"], d["scope"], d["agent"], d["status"], d["created"], d.get("updated") or d["created"], json.dumps(d, sort_keys=True)))
        elif kind == "experiment":
            d = data
            c.execute("""INSERT INTO experiments(id,idea_id,scope,agent,status,samples,decision,created,updated,doc) VALUES(?,?,?,?,?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET status=excluded.status,samples=excluded.samples,decision=excluded.decision,updated=excluded.updated,doc=excluded.doc""",
                      (d["id"], d.get("idea_id"), d["scope"], d["agent"], d["status"], int(d.get("samples", 0)), d.get("decision"), d["created"], d.get("updated") or d["created"], json.dumps(d, sort_keys=True)))
        elif kind == "retrieval":
            d = data
            c.execute("INSERT OR IGNORE INTO retrievals(id,scope,agent,task_sha,run_ref,memory_ids,chars,created) VALUES(?,?,?,?,?,?,?,?)",
                      (d["id"], d["scope"], d["agent"], d["task_sha"], d.get("run_ref"), json.dumps(d.get("memory_ids") or []), int(d.get("chars", 0)), d["created"]))
        elif kind == "workflow_version":
            d = data
            c.execute("""INSERT INTO workflow_versions(id,scope,agent,name,version,status,created,doc) VALUES(?,?,?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET status=excluded.status,doc=excluded.doc""",
                      (d["id"], d["scope"], d["agent"], d["name"], int(d["version"]), d["status"], d["created"], json.dumps(d, sort_keys=True)))
        elif kind == "eval_case":
            d = data
            c.execute("INSERT OR IGNORE INTO eval_cases(id,scope,agent,split,rubric_id,created,doc) VALUES(?,?,?,?,?,?,?)",
                      (d["id"], d["scope"], d["agent"], d["split"], d.get("rubric_id"), d["created"], json.dumps(d, sort_keys=True)))

    def put_task(self, tk: Task) -> None: self._apply("task", tk.to_dict())
    def put_run(self, r: Run) -> None: self._apply("run", r.to_dict())
    def put_approval(self, a: Approval) -> None: self._apply("approval", a.to_dict())
    def audit(self, e: AuditEvent) -> None: self._apply("audit", e.to_dict())
    def put_usage(self, run_id: t.Optional[str], u: ModelUsage) -> None: self._apply("usage", {"at": now_iso(), "run_id": run_id, "usage": u.to_dict()})
    def put_product(self, p: ProductManifest) -> None:
        if self.get_product(p.product_id, p.version) is not None and p.supersedes is None:
            raise ValueError(f"product {p.product_id} v{p.version} already exists; write a new version instead")
        self._apply("product", p.to_dict())
    def put_plan(self, d: DistributionPlan) -> None: self._apply("plan", d.to_dict())
    def put_integration(self, i: IntegrationHealth) -> None: self._apply("integration", i.to_dict())
    def set_control(self, key: str, value: t.Any) -> None: self._apply("control", {"key": key, "value": value, "at": now_iso()})
    def put_agent(self, a: AgentContract, skill_sha: t.Optional[str] = None) -> None: self._apply("agent", {"at": now_iso(), "skill_sha": skill_sha, "contract": a.to_dict()})
    def put_project(self, doc: dict) -> None: self._apply("project", doc)

    # cache (Phase 5). Cache rows ARE journaled so a rebuilt index keeps its hits; `purge` drops stale rows.
    def cache_put(self, key: str, provider: str, model: str, prompt_version: str, data_version: str, expires_at: str, text: str, usage: t.Optional[dict]) -> None:
        self._apply("cache", {"key": key, "provider": provider, "model": model, "prompt_version": prompt_version, "data_version": data_version,
                              "created_at": now_iso(), "expires_at": expires_at, "text": text, "usage": usage})

    def cache_get(self, key: str, data_version: str, now: t.Optional[str] = None) -> t.Optional[dict]:
        r = self._rows("SELECT * FROM llm_cache WHERE key=? AND data_version=? AND expires_at > ?", (key, data_version, now or now_iso()))
        if not r:
            return None
        self._apply("cache", {"op": "hit", "key": key})
        d = dict(r[0]); d["usage"] = json.loads(d["usage"]) if d.get("usage") else None
        return d

    def cache_purge(self, keep_version: str) -> int:
        n = len(self._rows("SELECT key FROM llm_cache WHERE expires_at < ? OR data_version <> ?", (now_iso(), keep_version)))
        self._apply("cache", {"op": "purge", "now": now_iso(), "keep_version": keep_version})
        return n

    def cache_stats(self) -> dict:
        r = self._rows("SELECT COUNT(*) n, COALESCE(SUM(hits),0) h, SUM(CASE WHEN expires_at < ? THEN 1 ELSE 0 END) e FROM llm_cache", (now_iso(),))[0]
        return {"entries": int(r["n"]), "hits": int(r["h"]), "expired": int(r["e"] or 0)}

    def usage_rows(self, day: t.Optional[str] = None) -> list[dict]:
        where, args = ("WHERE substr(at,1,10)=?", (day,)) if day else ("", ())
        return [dict(r) for r in self._rows(f"SELECT * FROM model_usage {where} ORDER BY at", args)]

    # publications + metrics (Phase 7)
    def put_publication(self, pub) -> None: self._apply("publication", pub.to_dict())

    def find_publication(self, idem: str):
        from .publishing import Publication
        r = self._rows("SELECT doc FROM publications WHERE idem_key=?", (idem,))
        return Publication.from_dict(json.loads(r[0]["doc"])) if r else None

    def publications(self, plan_id: t.Optional[str] = None) -> list:
        from .publishing import Publication
        rows = self._rows("SELECT doc FROM publications WHERE plan_id=? ORDER BY created_at", (plan_id,)) if plan_id else self._rows("SELECT doc FROM publications ORDER BY created_at")
        return [Publication.from_dict(json.loads(r["doc"])) for r in rows]

    def put_metric(self, d: dict) -> None: self._apply("metric", d)

    def metrics(self, plan_id: t.Optional[str] = None, ref: t.Optional[str] = None, since: t.Optional[str] = None) -> list[dict]:
        sql, args = "SELECT * FROM metrics WHERE 1=1", []
        if plan_id: sql += " AND plan_id=?"; args.append(plan_id)
        if ref: sql += " AND ref=?"; args.append(ref)
        if since: sql += " AND at>=?"; args.append(since)
        return [dict(r) for r in self._rows(sql + " ORDER BY at", tuple(args))]

    def agents(self) -> list[dict]:
        return [dict(r) for r in self._rows("SELECT id,version,role,name,registered_at,skill_sha FROM agents ORDER BY id, version")]

    def get_agent(self, agent_id: str, version: t.Optional[int] = None) -> t.Optional[AgentContract]:
        r = (self._rows("SELECT doc FROM agents WHERE id=? AND version=?", (agent_id, version)) if version is not None
             else self._rows("SELECT doc FROM agents WHERE id=? ORDER BY version DESC LIMIT 1", (agent_id,)))
        return AgentContract.from_dict(json.loads(r[0]["doc"])) if r else None

    def get_project(self, project_id: str) -> t.Optional[dict]:
        r = self._rows("SELECT doc FROM projects WHERE id=?", (project_id,))
        return json.loads(r[0]["doc"]) if r else None

    def projects(self, status: t.Optional[str] = None) -> list[dict]:
        rows = self._rows("SELECT doc FROM projects WHERE status=? ORDER BY updated_at DESC", (status,)) if status else self._rows("SELECT doc FROM projects ORDER BY updated_at DESC")
        return [json.loads(r["doc"]) for r in rows]

    # learning (Phase 9): the learning package writes through these so every row is journaled like the rest
    def put_learning(self, kind: str, data: dict) -> None:
        if kind not in ("memory", "evaluation", "idea", "experiment", "retrieval", "workflow_version", "eval_case"):
            raise ValueError(f"unknown learning kind {kind!r}")
        self._apply(kind, data)

    def rows(self, sql: str, args: tuple = ()) -> list[dict]:
        """Read-only query helper for the learning package (dict rows)."""
        if not sql.lstrip().lower().startswith("select"):
            raise ValueError("rows() is read-only")
        return [dict(r) for r in self._rows(sql, args)]

    # ---------------------------------------------------------------- reads
    def _rows(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        assert self.con
        with self._lock:
            return list(self.con.execute(sql, args))

    def get_task(self, task_id: str) -> t.Optional[Task]:
        r = self._rows("SELECT doc FROM tasks WHERE id=?", (task_id,))
        return Task.from_dict(json.loads(r[0]["doc"])) if r else None

    def find_task_by_key(self, key: str) -> t.Optional[Task]:
        r = self._rows("SELECT doc FROM tasks WHERE idempotency_key=?", (key,))
        return Task.from_dict(json.loads(r[0]["doc"])) if r else None

    def tasks(self, status: t.Optional[TaskStatus] = None, limit: int = 200) -> list[Task]:
        if status:
            rows = self._rows("SELECT doc FROM tasks WHERE status=? ORDER BY priority, created_at LIMIT ?", (status.value, limit))
        else:
            rows = self._rows("SELECT doc FROM tasks ORDER BY updated_at DESC LIMIT ?", (limit,))
        return [Task.from_dict(json.loads(r["doc"])) for r in rows]

    def runs_for(self, task_id: str) -> list[Run]:
        return [Run.from_dict(json.loads(r["doc"])) for r in self._rows("SELECT doc FROM runs WHERE task_id=? ORDER BY attempt", (task_id,))]

    def get_run(self, run_id: str) -> t.Optional[Run]:
        r = self._rows("SELECT doc FROM runs WHERE id=?", (run_id,))
        return Run.from_dict(json.loads(r[0]["doc"])) if r else None

    def get_approval(self, approval_id: str) -> t.Optional[Approval]:
        r = self._rows("SELECT doc FROM approvals WHERE id=?", (approval_id,))
        return Approval.from_dict(json.loads(r[0]["doc"])) if r else None

    def approvals(self, status: t.Optional[str] = None) -> list[Approval]:
        rows = self._rows("SELECT doc FROM approvals WHERE status=? ORDER BY requested_at DESC", (status,)) if status else self._rows("SELECT doc FROM approvals ORDER BY requested_at DESC")
        return [Approval.from_dict(json.loads(r["doc"])) for r in rows]

    def audit_tail(self, n: int = 50) -> list[dict]:
        return [dict(r) for r in self._rows("SELECT * FROM audit ORDER BY at DESC LIMIT ?", (n,))]

    def get_product(self, product_id: str, version: t.Optional[int] = None) -> t.Optional[ProductManifest]:
        if version is None:
            r = self._rows("SELECT doc FROM products WHERE product_id=? ORDER BY version DESC LIMIT 1", (product_id,))
        else:
            r = self._rows("SELECT doc FROM products WHERE product_id=? AND version=?", (product_id, version))
        return ProductManifest.from_dict(json.loads(r[0]["doc"])) if r else None

    def product_versions(self, product_id: str) -> list[int]:
        return [int(r["version"]) for r in self._rows("SELECT version FROM products WHERE product_id=? ORDER BY version", (product_id,))]

    def get_plan(self, plan_id: str) -> t.Optional[DistributionPlan]:
        r = self._rows("SELECT doc FROM distribution_plans WHERE id=?", (plan_id,))
        return DistributionPlan.from_dict(json.loads(r[0]["doc"])) if r else None

    def integrations(self) -> list[dict]:
        return [dict(r) for r in self._rows("SELECT * FROM integrations ORDER BY id")]

    def control(self, key: str, default: t.Any = None) -> t.Any:
        r = self._rows("SELECT value FROM control WHERE key=?", (key,))
        return json.loads(r[0]["value"]) if r else default

    def usage_summary(self, day: t.Optional[str] = None) -> dict:
        """Real usage only: separate known from unknown; never sum unknown as zero."""
        where, args = ("WHERE substr(at,1,10)=?", (day,)) if day else ("", ())
        rows = self._rows(f"SELECT tokens_in,tokens_out,cost_usd,calls,cached FROM model_usage {where}", args)
        calls = sum(int(r["calls"]) for r in rows)
        known_cost = [float(r["cost_usd"]) for r in rows if r["cost_usd"] is not None]
        known_tok = [int(r["tokens_in"] or 0) + int(r["tokens_out"] or 0) for r in rows if r["tokens_in"] is not None or r["tokens_out"] is not None]
        return {"calls": calls, "cached_calls": sum(int(r["cached"]) for r in rows),
                "cost_usd_known": round(sum(known_cost), 4) if known_cost else None, "cost_unknown_calls": len(rows) - len(known_cost),
                "tokens_known": sum(known_tok) if known_tok else None, "tokens_unknown_calls": len(rows) - len(known_tok)}

    def counts(self) -> dict:
        out = {s.value: 0 for s in TaskStatus}
        for r in self._rows("SELECT status, COUNT(*) n FROM tasks GROUP BY status"):
            out[r["status"]] = int(r["n"])
        return out
