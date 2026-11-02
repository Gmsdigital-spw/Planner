"""A fixed, experimental high-upside hypothesis; research only, never auto-promoted."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from datetime import timedelta
from pathlib import Path

from .models import Refused, ZERO, number, timestamp
from .research import TRADE_COLUMNS

VERSION = "breakout20-atr14-2R-v1"


@dataclass(frozen=True)
class Bar:
    at: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def read_bars(path):
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"timestamp", "open", "high", "low", "close", "volume"} <= set(reader.fieldnames or []):
            raise Refused("Bars need timestamp,open,high,low,close,volume")
        bars = []
        for row in reader:
            bar = Bar(timestamp(row["timestamp"]).isoformat(), *[number(row[k]) for k in ("open", "high", "low", "close", "volume")])
            if min(bar.open, bar.high, bar.low, bar.close) <= 0 or bar.volume < 0:
                raise Refused("Invalid OHLCV data")
            if not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high:
                raise Refused("Inconsistent OHLC prices")
            if bars and timestamp(bar.at) <= timestamp(bars[-1].at):
                raise Refused("Bars must be unique and strictly chronological")
            bars.append(bar)
    if len(bars) < 100:
        raise Refused("At least 100 completed, consistently spaced bars are required")
    return bars


def setup(bars, i):
    # The signal sees only completed bars through i. Nothing from the next bar.
    if i < 50:
        return None
    history = bars[i - 20:i]
    signal = bars[i]
    mean_volume = sum((b.volume for b in history), ZERO) / 20
    mean_close = sum((b.close for b in bars[i - 49:i + 1]), ZERO) / 50
    if not (signal.close > max(b.high for b in history) and signal.volume > mean_volume * Decimal("1.5") and signal.close > mean_close):
        return None
    true_ranges = [max(bars[j].high - bars[j].low, abs(bars[j].high - bars[j-1].close), abs(bars[j].low - bars[j-1].close)) for j in range(i - 13, i + 1)]
    atr = sum(true_ranges, ZERO) / 14
    return atr if atr > 0 else None


def backtest(path, output, *, capital="20", notional="2", cost_bps_per_side="10", bar_seconds=60):
    bars = read_bars(path)
    capital, notional, cost_bps = number(capital), number(notional), number(cost_bps_per_side)
    if not ZERO < notional <= capital or not ZERO <= cost_bps < 1000:
        raise Refused("Backtest notional must be positive and unleveraged; costs cannot be negative")
    if type(bar_seconds) is not int or not 1 <= bar_seconds <= 86400:
        raise Refused("Declare the actual bar duration in seconds")
    if any((timestamp(b.at) - timestamp(a.at)).total_seconds() < bar_seconds for a, b in zip(bars, bars[1:])):
        raise Refused("Bars overlap the declared bar duration")
    rows, cash, last_entry_day = [], capital, None
    i = 50
    boundaries = [int(len(bars) * .6), int(len(bars) * .8), len(bars)]
    while i < len(bars) - 1:
        atr = setup(bars, i)
        entry_index = i + 1
        entry_bar = bars[entry_index]
        segment = 0 if entry_index < boundaries[0] else (1 if entry_index < boundaries[1] else 2)
        day = timestamp(entry_bar.at).date()
        if atr is None or day == last_entry_day or cash < notional:
            i += 1
            continue
        # Next-bar open with adverse execution costs. Two ATR stop, four ATR target.
        entry = entry_bar.open * (1 + cost_bps / 10000)
        qty = (notional / entry).quantize(Decimal("0.000000001"), rounding=ROUND_DOWN)
        stop, target = entry - 2 * atr, entry + 4 * atr
        if stop <= 0 or qty <= 0:
            i += 1
            continue
        last = min(entry_index + 9, boundaries[segment] - 1)
        exit_price, exit_index = bars[last].close, last
        for j in range(entry_index, last + 1):
            b = bars[j]
            if b.open <= stop:
                exit_price, exit_index = b.open, j
                break
            if b.low <= stop:
                # If target and stop both occur in one bar, choose the adverse path.
                exit_price, exit_index = stop, j
                break
            if b.high >= target:
                exit_price, exit_index = target, j
                break
        exit_price *= 1 - cost_bps / 10000
        # Bar timestamps denote bar OPEN. Infer exit at bar end, never before entry.
        exit_at = timestamp(bars[exit_index].at) + timedelta(seconds=bar_seconds)
        row = dict(zip(TRADE_COLUMNS, [f"bt-{len(rows)+1}", VERSION, entry_bar.at, exit_at.isoformat(), str(entry), str(exit_price), str(qty), "0", ("train", "validation", "test")[segment]]))
        rows.append(row)
        cash += (exit_price - entry) * qty
        last_entry_day = day
        i = exit_index + 1
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRADE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return {"strategy_version": VERSION, "completed_trades": len(rows), "ending_closed_trade_equity_usd": str(cash), "cost_bps_per_side": str(cost_bps), "output": str(output),
            "research_only": True, "bar_seconds": bar_seconds, "notes": ["Use one symbol and a uniform bar timeframe. Supply only completed bars, with open timestamps and the actual bar duration.", "Survivorship bias, corporate actions and data quality are not corrected.", "Gap losses can exceed the intended stop; stop/target intrabar ties use the stop first.", "This backtest is not a broker order generator and never approves live trading."]}
