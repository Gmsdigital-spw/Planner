from __future__ import annotations

import csv
import hashlib
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .models import Refused, ZERO, number, timestamp

TRADE_COLUMNS = ["trade_id", "strategy_version", "entry_time", "exit_time", "entry_price", "exit_price", "qty", "fees_usd", "split"]


@dataclass(frozen=True)
class Trade:
    trade_id: str
    strategy_version: str
    entry_time: str
    exit_time: str
    entry_price: Decimal
    exit_price: Decimal
    qty: Decimal
    fees_usd: Decimal
    split: str

    def pnl(self, stress_bps_per_side):
        stress = (self.entry_price + self.exit_price) * self.qty * stress_bps_per_side / Decimal("10000")
        return (self.exit_price - self.entry_price) * self.qty - self.fees_usd - stress


def read_trades(path):
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not set(TRADE_COLUMNS) <= set(reader.fieldnames or []):
            raise Refused("Trade CSV needs columns: " + ",".join(TRADE_COLUMNS))
        rows = list(reader)
    trades, ids = [], set()
    for r in rows:
        if not r["trade_id"] or r["trade_id"] in ids:
            raise Refused("Trade IDs must be nonempty and unique")
        ids.add(r["trade_id"])
        entry, exit_ = timestamp(r["entry_time"]), timestamp(r["exit_time"])
        if entry >= exit_:
            raise Refused("Each exit must follow its entry")
        if r["split"] not in {"train", "validation", "test"}:
            raise Refused("Every trade needs an explicit chronological split")
        prices_qty = [number(r[k]) for k in ("entry_price", "exit_price", "qty")]
        if any(v <= 0 for v in prices_qty) or number(r["fees_usd"]) < 0:
            raise Refused("Invalid trade price, quantity, or fee")
        if not r["strategy_version"].strip():
            raise Refused("A fixed strategy version is required")
        trades.append(Trade(r["trade_id"], r["strategy_version"], entry.isoformat(), exit_.isoformat(), *prices_qty, number(r["fees_usd"]), r["split"]))
    if not trades:
        raise Refused("No completed trades were supplied")
    if len({t.strategy_version for t in trades}) != 1:
        raise Refused("Analyze one immutable strategy version at a time")
    trades.sort(key=lambda t: timestamp(t.entry_time))
    ranks = {"train": 0, "validation": 1, "test": 2}
    for previous, current in zip(trades, trades[1:]):
        if timestamp(previous.exit_time) > timestamp(current.entry_time):
            raise Refused("Overlapping trades conflict with this one-position research model")
        if ranks[current.split] < ranks[previous.split]:
            raise Refused("Train/validation/test data must be chronological and separated")
    return trades


def block_interval(trades, pnl):
    """Exploratory circular day-block bootstrap; does not correct strategy selection."""
    grouped = defaultdict(list)
    for t, p in zip(trades, pnl):
        grouped[timestamp(t.exit_time).date().isoformat()].append(float(p))
    days = list(grouped.values())
    if len(days) < 5:
        return None
    rng = random.Random(9301)
    block = max(2, math.ceil(math.sqrt(len(days))))
    means = []
    for _ in range(1500):
        sampled_days = []
        while len(sampled_days) < len(days):
            start = rng.randrange(len(days))
            sampled_days.extend(days[(start + j) % len(days)] for j in range(block))
        sampled = [p for d in sampled_days[:len(days)] for p in d]
        means.append(statistics.mean(sampled))
    means.sort()
    return [round(means[int(len(means) * .025)], 6), round(means[int(len(means) * .975)], 6)]


def metrics(trades, capital, stress_bps):
    if not trades:
        return {"trades": 0, "net_pnl_usd": None, "win_rate": None, "profit_factor": None,
                "max_drawdown_usd": None, "expectancy_usd": None, "active_days": 0,
                "expectancy_interval_usd": None}
    pnl = [t.pnl(stress_bps) for t in trades]
    wins, losses = [p for p in pnl if p > 0], [-p for p in pnl if p < 0]
    equity = peak = capital
    max_drawdown = ZERO
    for p in pnl:
        equity += p
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return {
        "trades": len(trades), "active_days": len({timestamp(t.exit_time).date() for t in trades}),
        "net_pnl_usd": str(sum(pnl, ZERO)), "win_rate": len(wins) / len(trades),
        "avg_win_usd": str(sum(wins, ZERO) / len(wins)) if wins else None,
        "avg_loss_usd": str(sum(losses, ZERO) / len(losses)) if losses else None,
        "profit_factor": str(sum(wins, ZERO) / sum(losses, ZERO)) if losses else None,
        "expectancy_usd": str(sum(pnl, ZERO) / len(pnl)),
        "max_drawdown_usd": str(max_drawdown),
        "drawdown_scope": "Completed-trade equity only; intratrade mark-to-market drawdown is unknown",
        "expectancy_interval_usd": block_interval(trades, pnl),
    }


def analyze(path, *, capital="20", stress_bps="10", frozen_at=None):
    capital, stress_bps = number(capital), number(stress_bps)
    if capital <= 0 or stress_bps < 0:
        raise Refused("Capital must be positive and stress costs nonnegative")
    trades = read_trades(path)
    if any(t.entry_price * t.qty > capital for t in trades):
        raise Refused("A trade notional exceeds the stated unleveraged research capital")
    # Closed-trade equity solvency is a minimum check, not a mark-to-market audit.
    available = capital
    for t in trades:
        if t.entry_price * t.qty + t.fees_usd > available:
            raise Refused("Trade history requires more cash than the supplied starting capital")
        available += t.pnl(stress_bps)
    sections = {split: metrics([t for t in trades if t.split == split], capital, stress_bps) for split in ("train", "validation", "test")}
    test = sections["test"]
    failures = []
    if any(sections[k]["trades"] == 0 for k in sections):
        failures.append("All three chronological splits must have completed trades")
    if test["trades"] < 100:
        failures.append("Fewer than 100 completed test trades")
    if test["active_days"] < 30:
        failures.append("Fewer than 30 active test days")
    if test["net_pnl_usd"] is None or number(test["net_pnl_usd"]) <= 0:
        failures.append("Test net profit is not positive after declared costs")
    if test["profit_factor"] is None or number(test["profit_factor"]) < Decimal("1.20"):
        failures.append("Test profit factor is below 1.20 or cannot be estimated")
    if test["max_drawdown_usd"] is None or number(test["max_drawdown_usd"]) > capital * Decimal("0.10"):
        failures.append("Completed-trade test drawdown exceeds 10% or is unknown")
    interval = test["expectancy_interval_usd"]
    if interval is None or interval[0] <= 0:
        failures.append("Exploratory day-block expectancy interval does not stay above zero")
    test_trades = [t for t in trades if t.split == "test"]
    if frozen_at is None:
        failures.append("No independent pre-test strategy-freeze timestamp was supplied")
    elif test_trades and timestamp(frozen_at) >= min(timestamp(t.entry_time) for t in test_trades):
        failures.append("Strategy freeze did not precede the test period")
    return {
        "source_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "strategy_version": trades[0].strategy_version,
        "capital_usd": str(capital), "extra_cost_bps_per_side": str(stress_bps),
        "splits": sections, "research_checks_passed": not failures, "failures": failures,
        "live_approved": False,
        "limits": [
            "Thresholds are engineering filters, not proof of a profitable trading edge.",
            "Input provenance, genuine holdout separation and strategy freeze are not authenticated by a CSV.",
            "Bootstrap is exploratory; short samples, serial dependence, multiple testing and market changes can invalidate it.",
            "Actual fills may already include spread/slippage; extra costs are an explicit additional stress test.",
            "No annualized return, calibrated confidence, or future profit is inferred.",
        ],
    }
