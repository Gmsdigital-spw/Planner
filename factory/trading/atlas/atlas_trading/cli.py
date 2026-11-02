from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

from . import breakout, dashboard, research
from .broker import AlpacaBroker, BrokerError, DemoBroker
from .engine import Engine
from .models import Proposal, Refused, Settings, encoded, now_utc
from .store import Store


def demo(settings, reset=False):
    if settings.mode != "demo":
        raise Refused("demo requires demo configuration and can never use broker credentials")
    path = Path(settings.database)
    if path.exists():
        try:
            with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
                row = db.execute("SELECT value FROM metadata WHERE key='identity'").fetchone()
                identity = json.loads(row[0]) if row else None
                if not identity or identity.get("mode") != "demo":
                    raise Refused("Refusing to recreate a database that is not identified as synthetic demo data")
        except sqlite3.Error:
            raise Refused("Refusing to replace a database that is not a valid Atlas demo") from None
    if path.exists() and not reset:
        return {"message": "Synthetic demo already exists; use serve, or demo --reset to recreate only demo data"}
    if reset:
        for suffix in ("", "-wal", "-shm"):
            candidate = Path(str(path) + suffix)
            if candidate.exists():
                candidate.unlink()
    store = Store(str(path))
    broker = DemoBroker("50")
    engine = Engine(settings, store, broker)
    at = now_utc()
    p = Proposal("synthetic-entry", "SPY", "buy", "SYNTHETIC-EXAMPLE-v1", at.isoformat(), (at + timedelta(seconds=120)).isoformat(),
                 notional_usd="2", rationale="Synthetic order-lifecycle demonstration", evidence_ref="DEMO ONLY — no historical evidence")
    plan = engine.preview(p)
    entered = engine.execute(p)
    duplicate = engine.execute(p)
    exit_ = Proposal("synthetic-exit", "SPY", "sell", p.strategy_version, at.isoformat(), (at + timedelta(seconds=120)).isoformat())
    closed = engine.execute(exit_)
    store.capture(broker.snapshot("SPY"), settings)
    store.add_lesson(p.strategy_version, "A canceled or timed-out request must be reconciled by client order ID before another submission.", "Synthetic lifecycle demo; not strategy evidence")
    store.close()
    return {"synthetic": True, "starting_synthetic_equity_usd": "50", "plan": plan, "entry_status": entered["status"],
            "duplicate_prevented": duplicate["duplicate_prevented"], "exit_status": closed["status"], "message": "Demo fills are made-up infrastructure checks, not investment results"}


def parser():
    p = argparse.ArgumentParser(description="Atlas Trading Lab — bounded experiment tooling, no promised profits")
    p.add_argument("--config", default="config.example.json")
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("demo", help="Synthetic, offline order-lifecycle example")
    d.add_argument("--reset", action="store_true", help="Remove only the configured demo database before the example")
    s = sub.add_parser("serve", help="Local read-only dashboard")
    s.add_argument("--port", type=int, default=8765)
    sub.add_parser("status", help="Read local saved data without contacting the broker")
    ticket = sub.add_parser("ticket", help="Create a fresh proposal; does not submit")
    ticket.add_argument("--symbol", required=True)
    ticket.add_argument("--side", choices=["buy", "sell"], default="buy")
    ticket.add_argument("--strategy-version", required=True)
    ticket.add_argument("--notional", default="2")
    ticket.add_argument("--adverse-move", default="0.05")
    ticket.add_argument("--target-move", default="0.10")
    ticket.add_argument("--rationale", default="")
    ticket.add_argument("--evidence", default="")
    ticket.add_argument("--out", required=True)
    for command in ("preview", "execute"):
        action = sub.add_parser(command)
        action.add_argument("proposal")
        action.add_argument("--settled-cash-usd", help="Broker-confirmed start-of-day settled funds; do not replace with buying_power")
        if command == "execute":
            action.add_argument("--live-ack")
    sub.add_parser("reconcile", help="Read order outcomes by stable client IDs; never re-POST")
    halt = sub.add_parser("halt", help="Stop new entries locally; does not liquidate or cancel broker orders")
    halt.add_argument("--reason", default="Operator paused entries")
    resume = sub.add_parser("resume", help="Clear a reviewed local halt; limits still apply")
    resume.add_argument("--ack", required=True, choices=["REVIEWED"])
    lesson = sub.add_parser("lesson", help="Record a hypothesis without claiming it is validated")
    lesson.add_argument("--strategy-version", required=True)
    lesson.add_argument("--hypothesis", required=True)
    lesson.add_argument("--evidence", required=True)
    bt = sub.add_parser("backtest", help="Research-only breakout/ATR hypothesis on completed OHLCV bars")
    bt.add_argument("bars")
    bt.add_argument("--out", default="data/backtest-trades.csv")
    bt.add_argument("--capital", default="20")
    bt.add_argument("--notional", default="2")
    bt.add_argument("--cost-bps", default="10")
    bt.add_argument("--bar-seconds", type=int, default=60)
    a = sub.add_parser("analyze", help="Review completed trade records with chronological splits")
    a.add_argument("trades")
    a.add_argument("--capital", default="20")
    a.add_argument("--stress-bps", default="10")
    a.add_argument("--frozen-at")
    a.add_argument("--out", default="data/research-report.json")
    return p


def run(args):
    settings = Settings.load(args.config)
    if args.command == "demo":
        return demo(settings, args.reset)
    if args.command == "status":
        return dashboard.state(settings)
    if args.command == "serve":
        dashboard.serve(settings, args.port)
        return None
    if args.command == "backtest":
        return breakout.backtest(args.bars, args.out, capital=args.capital, notional=args.notional, cost_bps_per_side=args.cost_bps, bar_seconds=args.bar_seconds)
    if args.command == "analyze":
        report = research.analyze(args.trades, capital=args.capital, stress_bps=args.stress_bps, frozen_at=args.frozen_at)
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2))
        return report
    if args.command == "ticket":
        at = now_utc()
        proposal = Proposal(uuid.uuid4().hex, args.symbol, args.side, args.strategy_version, at.isoformat(), (at + timedelta(seconds=120)).isoformat(),
                            notional_usd=args.notional, adverse_move_pct=args.adverse_move, target_move_pct=args.target_move,
                            rationale=args.rationale, evidence_ref=args.evidence)
        proposal.validate(at)
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(proposal), indent=2))
        return {"proposal": str(path), "expires_at": proposal.expires_at, "submitted": False}
    store = Store(settings.database)
    try:
        if args.command == "halt":
            with store.locked():
                store.halt(args.reason)
            return {"entries_halted": True, "broker_orders_changed": False}
        if args.command == "resume":
            with store.locked():
                if store.unresolved():
                    raise Refused("Reconcile unresolved orders before resuming")
                store.set("halt_reason", None)
                store.event("operator_resumed", {"thresholds_unchanged": True})
            return {"entries_halted": False, "limits_unchanged": True}
        if args.command == "lesson":
            store.add_lesson(args.strategy_version, args.hypothesis, args.evidence)
            return {"recorded": True, "status": "unverified"}
        if settings.mode == "demo":
            raise Refused("Use the demo command for synthetic execution; broker commands require a separate paper/live config")
        broker = AlpacaBroker(settings)
        engine = Engine(settings, store, broker)
        if args.command == "reconcile":
            return {"outcomes": engine.reconcile()}
        proposal = Proposal.load(args.proposal)
        if args.command == "preview":
            return engine.preview(proposal, args.settled_cash_usd)
        return engine.execute(proposal, live_ack=args.live_ack, settled_cash_usd=args.settled_cash_usd)
    finally:
        store.close()


def main():
    args = parser().parse_args()
    try:
        result = run(args)
        if result is not None:
            print(encoded(result))
    except (Refused, BrokerError, OSError, ValueError, KeyError, TypeError) as exc:
        print(encoded({"ok": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2) from None
