"""Offline check (no network, no keys): bot.py's cycle and backtest.py's simulate trade the same synthetic bars the same way.
Run: python3 factory/trading/crypto/tests/test_agree.py
1) The bot run every 5 minutes (live ask = next bar's open + half spread) makes the same trades as the backtest.
2) Missed runs: a stop hit inside bars the bot never saw live is still taken, at the stop price, from the bar's low.
3) Nothing in the crypto folder names an order or account endpoint."""
import json, math, random, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core, bot, backtest  # noqa: E402


def synth(seed, n=2400, t0=1_790_000_000 // 300 * 300):
    rng = random.Random(seed)
    out, px = {}, {"AAA/USD": 100.0, "BBB/USD": 5.0}
    for s in px:
        bars, p = [], px[s]
        for i in range(n):
            drift = 0.004 if (i // 150) % 3 == 0 else -0.0005
            o = p
            c = o * (1 + drift / 10 + rng.gauss(0, 0.003))
            h, l = max(o, c) * (1 + abs(rng.gauss(0, 0.002))), min(o, c) * (1 - abs(rng.gauss(0, 0.002)))
            v = rng.uniform(5, 15) * (4 if rng.random() < 0.08 else 1)
            bars.append({"t": t0 + i * 300, "o": o, "h": h, "l": l, "c": c, "v": v})
            p = c
        out[s] = bars
    return out


def params():
    p = core.load_params()
    p["symbols"] = ["AAA/USD", "BBB/USD"]
    p["minScore"] = 60  # loose, so the synthetic data makes plenty of trades to compare
    return p


def run_bot(bars, p, start_i, every=1, skip=()):
    state = core.new_state(p)
    hs = p["assumedSpreadPct"] / 200.0
    n = len(next(iter(bars.values())))
    for i in range(start_i, n - 1, every):
        if i in skip:
            continue
        now = bars["AAA/USD"][i]["t"] + 300  # bar i just closed
        quotes = {}
        for s, bl in bars.items():
            o = bl[i + 1]["o"]
            ask = o * (1 + hs)
            bid = ask - 2 * (ask - o)
            quotes[s] = {"bid": bid, "ask": ask}
        visible = {s: bl[: i + 2] for s, bl in bars.items()}  # bar i+1 is still forming: cycle must drop it
        bot.cycle(state, visible, quotes, now, p)
    return state


def main():
    p = params()
    bars = synth(7)
    start_i = 1200
    start = bars["AAA/USD"][start_i]["t"]
    end = bars["AAA/USD"][-1]["t"]
    st = run_bot(bars, p, start_i)
    core.flatten(st, end, "end", p)
    bt = backtest.simulate({s: [b for b in bl if b["t"] < end] for s, bl in bars.items()}, start, end, p)
    a = [(t["sym"], t["entryAt"], t["reason"], round(t["pnl"], 6)) for t in st["history"]]
    b = [(t["sym"], t["entryAt"], t["reason"], round(t["pnl"], 6)) for t in bt["list"]]
    assert len(a) >= 5, f"synthetic data made too few trades to compare: {len(a)}"
    assert a == b, f"bot and backtest disagree:\nbot {a[:5]}\nbt  {b[:5]}\n({len(a)} vs {len(b)})"
    assert abs(st["cash"] - bt["endEquity"]) < 0.01, (st["cash"], bt["endEquity"])
    print(f"agree: {len(a)} trades, net ${st['cash'] - p['startBalance']:+.2f} both ways")

    # 2) missed runs: open a position by hand, then the bot sleeps through a crash bar
    s = core.new_state(p)
    i0 = 1500
    bl = bars["AAA/USD"]
    t_open = bl[i0]["t"]
    s["lastBarT"] = t_open
    s["positions"].append({"sym": "AAA/USD", "qty": 0.1, "qty0": 0.1, "entry": bl[i0]["c"], "stop": bl[i0]["c"] * 0.99,
                           "stop0": bl[i0]["c"] * 0.99, "R": bl[i0]["c"] * 0.01, "hs": 0.0005, "cost": 0.1 * bl[i0]["c"],
                           "proceeds": 0.0, "half": False, "high": bl[i0]["c"], "t": t_open + 300, "lastBarT": t_open,
                           "score": 80, "fills": []})
    crash = [dict(b) for b in bl]
    k = i0 + 3
    crash[k]["l"] = crash[k]["o"] * 0.95  # a wick far below the stop, then recovers
    crash[k]["h"] = max(crash[k]["h"], crash[k]["o"])
    view = {"AAA/USD": crash[: i0 + 9], "BBB/USD": bars["BBB/USD"][: i0 + 9]}
    now = crash[i0 + 8]["t"] + 300  # first run back after 8 missed bars
    bot.cycle(s, view, {}, now, p)
    assert not s["positions"], "missed-run stop was not taken"
    h = s["history"][-1]
    assert h["reason"] == "stop" and abs(h["exit"] - min(crash[k]["o"], bl[i0]["c"] * 0.99) * (1 - 0.0005)) < 1e-6, h
    print("missed runs: stop taken from the bar low:", h["exitAt"], h["reason"])

    # 3) no order / account endpoints anywhere
    for f in HERE.glob("*.py"):
        txt = f.read_text()
        assert not re.search(r"/v2/orders|/orders\b|/positions\b|/account\b|paper-api|api\.alpaca", txt), f"{f.name} names an order endpoint"
        assert 'MODE = "virtual"' in txt or f.name != "core.py"
    print("no order endpoints; mode virtual")
    print("ALL PASS")


if __name__ == "__main__":
    main()
