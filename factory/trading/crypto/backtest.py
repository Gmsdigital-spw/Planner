#!/usr/bin/env python3
"""Crypto paper bot backtest: the SAME core.run_time (score, entries, exits, fees) over historical Alpaca crypto bars.

Costs: 0.25% taker fee per side + half the spread (assumedSpreadPct, since there are no free historical quotes).
Entries fill at the NEXT bar's open + half spread (the bot fills at the live ask just after the bar closes).
Also runs a random-entry baseline: same entry frequency, same sizing, same exits, random symbol and time.

  python3 backtest.py --start 2026-08-25 --end 2026-09-24          # one range, prints a summary
  python3 backtest.py --first-test                                 # last 60 days: tune 30 / holdout 30 -> lab/first-test.json
Not financial advice. Places no orders; reads market data only.
"""
import argparse, itertools, json, random, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402

WARMUP = 4 * 86400


def day_ts(s):
    return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def simulate(bars, start, end, p, rng=None, rate=None):
    """Replay bars; trades may open only for bars starting in [start, end). Open positions at `end` are closed at
    the last close ("end"). rng+rate = random baseline: each bar, with probability `rate`, enter a random symbol."""
    by_t = core.group_by_time(bars, p)
    times = sorted(by_t)
    nxt = {s: {b["t"]: b for b in bl} for s, bl in bars.items()}
    hs = p["assumedSpreadPct"] / 200.0
    state = core.new_state(p)
    curve, peak, mdd = [], p["startBalance"], 0.0
    bars_in = 0
    cur = {"t": None}

    def quote_fn(sym):
        b = nxt[sym].get(cur["t"] + core.BAR)
        return (b["o"] * (1 + hs), hs) if b else None

    def picker(cands, at, st):
        if rng.random() >= rate:
            return []
        held = {x["sym"] for x in st["positions"]}
        syms = [s for s in sorted(at) if s not in held]
        if not syms:
            return []
        s = rng.choice(syms)
        bl, ind, i = at[s]
        sc = core.score_at(bl, ind, i, p)
        return [(sc["score"], s, sc)] if sc and not sc["thin"] else []

    for t in times:
        if t >= end:
            break
        cur["t"] = t
        allow = t >= start
        if allow:
            bars_in += 1
        core.run_time(state, t, by_t[t], quote_fn, p, allow_entries=allow, picker=picker if rng else None)
        if allow:
            e = core.equity(state)
            peak = max(peak, e)
            mdd = max(mdd, (peak - e) / peak if peak > 0 else 0)
    core.flatten(state, end, "end", p)
    trades = [h for h in state["history"] if h["entryAt"] >= core.iso(start)]
    return summarize(trades, state, p, mdd, bars_in)


def summarize(trades, state, p, mdd, bars_in):
    wins = [t for t in trades if t["pnl"] > 0]
    rs = [t["R"] for t in trades if t["R"] is not None]
    gp = sum(t["pnl"] for t in wins)
    gl = -sum(t["pnl"] for t in trades if t["pnl"] <= 0)
    by = {}
    for t in trades:
        by.setdefault(t["reason"], 0)
        by[t["reason"]] += 1
    return {"trades": len(trades), "winRate": round(len(wins) / len(trades), 3) if trades else None,
            "avgR": round(sum(rs) / len(rs), 3) if rs else None,
            "netPnl": round(state["cash"] - p["startBalance"], 2), "endEquity": round(state["cash"], 2),
            "maxDrawdownPct": round(mdd * 100, 1), "profitFactor": round(gp / gl, 2) if gl > 0 else None,
            "exits": by, "floorLocked": state["floorLocked"], "bars": bars_in, "list": trades}


def baseline(bars, start, end, p, n_trades, bars_in, seeds=20):
    """Random entries at the strategy's own entry rate, averaged over `seeds` runs."""
    if not n_trades or not bars_in:
        return {"note": "strategy took no trades; no rate to match"}
    rate = n_trades / bars_in
    runs = [simulate(bars, start, end, p, rng=random.Random(s), rate=rate) for s in range(seeds)]
    net = [r["netPnl"] for r in runs]
    wr = [r["winRate"] for r in runs if r["winRate"] is not None]
    return {"seeds": seeds, "entryRatePerBar": round(rate, 5), "avgTrades": round(sum(r["trades"] for r in runs) / seeds, 1),
            "avgWinRate": round(sum(wr) / len(wr), 3) if wr else None, "avgNetPnl": round(sum(net) / seeds, 2),
            "medianNetPnl": sorted(net)[seeds // 2], "bestNetPnl": max(net), "worstNetPnl": min(net),
            "avgMaxDrawdownPct": round(sum(r["maxDrawdownPct"] for r in runs) / seeds, 1)}


def brief(r, keep_list=True):
    out = {k: v for k, v in r.items() if k != "list"}
    if keep_list:
        out["tradesList"] = [{k: t[k] for k in ("sym", "entryAt", "exitAt", "entry", "exit", "R", "pnl", "score", "reason")}
                             for t in r["list"]]
    return out


def first_test(p, out_path):
    end = (int(time.time()) // 86400) * 86400  # today 00:00 UTC
    mid, start = end - 30 * 86400, end - 60 * 86400
    bars = core.fetch_bars(p["symbols"], start - WARMUP, end)
    counts = {s: len(b) for s, b in bars.items()}
    syms = [s for s in p["symbols"] if counts.get(s, 0) > 1000]
    bars = {s: bars[s] for s in syms}
    res = {"made": datetime.now(timezone.utc).isoformat(), "mode": core.MODE, "symbols": syms, "barCounts": counts,
           "tune": {"from": core.iso(start), "to": core.iso(mid)}, "holdout": {"from": core.iso(mid), "to": core.iso(end)},
           "costs": {"feePctPerSide": p["feePct"], "assumedSpreadPct": p["assumedSpreadPct"]},
           "rules": "Defaults are Grayson's spec. The grid is scored on the tune window ONLY; the holdout is run once per "
                    "setting chosen, never used to choose."}
    # 1) spec defaults on both windows
    d_t = simulate(bars, start, mid, p)
    d_h = simulate(bars, mid, end, p)
    res["specDefaults"] = {"tune": brief(d_t), "tuneRandom": baseline(bars, start, mid, p, d_t["trades"], d_t["bars"]),
                           "holdout": brief(d_h), "holdoutRandom": baseline(bars, mid, end, p, d_h["trades"], d_h["bars"])}
    # 2) small grid on the tune window only
    grid = {"minScore": [75, 80, 90], "stopAtr": [1.5, 2.0], "trailAtr": [2.0, 3.0]}
    rows = []
    for vals in itertools.product(*grid.values()):
        q = json.loads(json.dumps(p))
        q.update(dict(zip(grid, vals)))
        r = simulate(bars, start, mid, q)
        rows.append({"set": dict(zip(grid, vals)), "trades": r["trades"], "winRate": r["winRate"], "netPnl": r["netPnl"],
                     "maxDrawdownPct": r["maxDrawdownPct"]})
    ok = [r for r in rows if r["trades"] >= 5] or rows
    best = max(ok, key=lambda r: r["netPnl"])
    q = json.loads(json.dumps(p)); q.update(best["set"])
    b_h = simulate(bars, mid, end, q)
    res["tuneGrid"] = {"grid": grid, "rows": rows, "pickedOnTune": best,
                       "pickedOnHoldout": brief(b_h),
                       "pickedHoldoutRandom": baseline(bars, mid, end, q, b_h["trades"], b_h["bars"])}
    Path(out_path).write_text(json.dumps(res, indent=1) + "\n")

    def line(name, r, rb):
        print(f"{name:22s} trades {r['trades']:3d}  win {r['winRate']}  avgR {r['avgR']}  net ${r['netPnl']:+.2f}  "
              f"maxDD {r['maxDrawdownPct']}%   | random avg net ${rb.get('avgNetPnl')} win {rb.get('avgWinRate')}")
    line("spec tune", d_t, res["specDefaults"]["tuneRandom"])
    line("spec holdout", d_h, res["specDefaults"]["holdoutRandom"])
    print("picked on tune:", best)
    line("picked holdout", b_h, res["tuneGrid"]["pickedHoldoutRandom"])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start"); ap.add_argument("--end")
    ap.add_argument("--first-test", action="store_true")
    ap.add_argument("--out", default=str(HERE / "lab" / "first-test.json"))
    a = ap.parse_args()
    p = core.load_params()
    if a.first_test:
        (HERE / "lab").mkdir(exist_ok=True)
        first_test(p, a.out)
        return
    s, e = day_ts(a.start), day_ts(a.end)
    bars = core.fetch_bars(p["symbols"], s - WARMUP, e)
    r = simulate(bars, s, e, p)
    for t in r["list"]:
        print(t)
    print(json.dumps({k: v for k, v in r.items() if k != "list"}))
    print("random:", json.dumps(baseline(bars, s, e, p, r["trades"], r["bars"])))


if __name__ == "__main__":
    main()
