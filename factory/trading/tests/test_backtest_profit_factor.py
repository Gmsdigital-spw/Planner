"""Invariants of backtest.simulate()'s profit factor (added Oct 23, 2026). Synthetic random-walk bars are a TEST
FIXTURE only, never a result: profitFactor == grossProfit / grossLoss (None when no trade lost), and
grossProfit - grossLoss == netPnl. Run: python3 factory/trading/tests/test_backtest_profit_factor.py"""
import random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import backtest  # noqa: E402

CT = ZoneInfo("America/Chicago")


def day_bars(day, seed, drift):
    rnd = random.Random(seed); px = 100 + rnd.random() * 50; out = []
    t = datetime.fromisoformat(day).replace(hour=8, minute=30, tzinfo=CT)
    for i in range(78):
        o = px; path = [o]
        for _ in range(5):
            path.append(path[-1] + rnd.gauss(drift, 0.08))
        c = path[-1]; h = max(path) + abs(rnd.gauss(0, 0.03)); l = min(path) - abs(rnd.gauss(0, 0.03))
        out.append({"t": (t + timedelta(minutes=5 * i)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "o": round(o, 3), "h": round(h, 3), "l": round(l, 3), "c": round(c, 3), "v": rnd.randint(500, 5000)})
        px = c
    return out


def main():
    fails = checked = 0
    days = [f"2026-09-{d:02d}" for d in (1, 2, 3, 4, 8, 9)]
    for seed in range(40):
        data = [(d, {s: day_bars(d, seed * 100 + k * 7 + i, 0.01 * (k % 3)) for k, s in enumerate(["AAA", "BBB", "CCC", "DDD"])})
                for i, d in enumerate(days)]
        for setup in ("pullback", "orb", "pullback_orh"):
            P = dict(backtest.DEFAULT); P["setup"] = setup
            r = backtest.simulate(data, P)
            gp, gl, pf = r["grossProfit"], r["grossLoss"], r["profitFactor"]
            if gl > 0 and pf != round(gp / gl, 3):
                print("FAIL profitFactor", seed, setup, gp, gl, pf); fails += 1
            if gl == 0 and pf is not None:
                print("FAIL profitFactor should be None with no losing trade", seed, setup); fails += 1
            if abs((gp - gl) - r["netPnl"]) > 0.002:
                print("FAIL gross vs netPnl", seed, setup, gp, gl, r["netPnl"]); fails += 1
            if r["trades"] and gl > 0 and gp > 0:
                checked += 1
    print(f"cases with both wins and losses: {checked}; failures: {fails}")
    print("RESULT:", "PASS" if not fails else "FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
