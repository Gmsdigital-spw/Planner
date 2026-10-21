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
DB_DIR = Path(os.environ.get("GM_ENGINE_DB_DIR", HERE / "db"))

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
        if fresh and self.journal.exists():
            self.rebuild()
        return self

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

    def rebuild(self) -> int:
        """Replay the journal into SQLite (idempotent: last write per id wins)."""
        assert self.con
        n = 0
        if not self.journal.exists():
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
        elif kind == "control":
            c.execute("INSERT INTO control(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                      (data["key"], json.dumps(data["value"]), data.get("at") or now_iso()))

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
