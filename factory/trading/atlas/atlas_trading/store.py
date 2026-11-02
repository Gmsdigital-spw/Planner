from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import Proposal, Refused, Settings, Snapshot, encoded, now_utc, number

TERMINAL = {"filled", "canceled", "expired", "rejected", "not_submitted"}


class Store:
    """One durable database per dedicated brokerage account and environment."""

    def __init__(self, path: str):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=15)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(Path(__file__).with_name("schema.sql").read_text())
        self.db.commit()
        os.chmod(self.path, 0o600)

    def close(self):
        self.db.close()

    @contextmanager
    def locked(self):
        # Process-wide serialization survives a crash; use a local POSIX disk, not NFS.
        try:
            import fcntl
        except ImportError:
            raise Refused("Broker submission requires Linux/macOS with file locking") from None
        lock_path = str(self.path) + ".lock"
        with open(lock_path, "a") as handle:
            os.chmod(lock_path, 0o600)
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def get(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key: str, value):
        with self.db:
            self.db.execute("INSERT INTO metadata(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, encoded(value)))

    def event(self, kind: str, detail):
        with self.db:
            self.db.execute("INSERT INTO events(at,kind,detail_json) VALUES(?,?,?)", (now_utc().isoformat(), kind, encoded(detail)))

    def halt(self, reason: str):
        self.set("halt_reason", reason)
        self.event("entries_halted", {"reason": reason})

    def capture(self, snapshot: Snapshot, settings: Settings):
        identity = {"mode": settings.mode, "account_id": snapshot.account_id}
        existing = self.get("identity")
        if existing and existing != identity:
            raise Refused("Database is pinned to a different account or mode; do not reuse it")
        if existing is None:
            self.set("identity", identity)
            self.set("initial_equity", str(snapshot.equity))
        day = snapshot.fetched_at.astimezone(ZoneInfo("America/New_York")).date().isoformat()
        key = "day_reference:" + day
        if self.get(key) is None:
            self.set(key, str(max(snapshot.equity, snapshot.last_equity)))
        with self.db:
            self.db.execute("INSERT INTO snapshots(at,trading_day,equity_usd,cash_usd,exposure_usd) VALUES(?,?,?,?,?)", (snapshot.fetched_at.isoformat(), day, str(snapshot.equity), str(snapshot.cash), str(snapshot.exposure)))
        return day

    def order(self, proposal_id: str):
        row = self.db.execute("SELECT * FROM orders WHERE proposal_id=?", (proposal_id,)).fetchone()
        return dict(row) if row else None

    def unresolved(self):
        rows = self.db.execute("SELECT * FROM orders ORDER BY created_at").fetchall()
        return [dict(r) for r in rows if r["status"] not in TERMINAL]

    def reserve(self, p: Proposal, payload: dict, day: str):
        at = now_utc().isoformat()
        with self.db:
            self.db.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
                payload["client_order_id"], p.proposal_id, p.fingerprint, encoded(asdict(p)),
                encoded(payload), p.side, p.notional_usd if p.side == "buy" else "0",
                "submitting", at, day, None, at,
            ))
        # This durable reservation must be committed BEFORE the HTTP POST.

    def update_order(self, client_id: str, status: str, broker_data: dict | None = None):
        with self.db:
            self.db.execute("UPDATE orders SET status=?,broker_json=?,updated_at=? WHERE client_order_id=?", (status, encoded(broker_data) if broker_data is not None else None, now_utc().isoformat(), client_id))

    def day_entries(self, day: str):
        # Conservative: every submission attempt counts, even if later canceled.
        rows = self.db.execute("SELECT notional_usd FROM orders WHERE trading_day=? AND side='buy' AND status!='not_submitted'", (day,)).fetchall()
        return len(rows), sum((number(r[0]) for r in rows), number("0"))

    def add_lesson(self, strategy_version: str, hypothesis: str, evidence_ref: str):
        if not all(isinstance(v, str) and v.strip() for v in (strategy_version, hypothesis, evidence_ref)):
            raise Refused("A lesson needs a strategy version, hypothesis and evidence reference")
        with self.db:
            self.db.execute("INSERT INTO lessons(at,strategy_version,hypothesis,evidence_ref) VALUES(?,?,?,?)", (now_utc().isoformat(), strategy_version, hypothesis, evidence_ref))
