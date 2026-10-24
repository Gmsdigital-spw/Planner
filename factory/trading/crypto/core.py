"""Crypto paper bot: shared logic for bot.py and backtest.py (one copy, so the lab tests what the bot trades).

VIRTUAL ONLY. Nothing here, in bot.py or in backtest.py, talks to an order or account endpoint. Prices come from
Alpaca's free crypto market data (v1beta3); every fill is simulated in our own ledger with the taker fee and half
the spread. It shares nothing with the stock bot's Alpaca paper account.
"""
import json, math, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

MODE = "virtual"  # hard-coded. There is no live mode and no order code.
HERE = Path(__file__).resolve().parent
DATA = "https://data.alpaca.markets/v1beta3/crypto/us"
BAR = 300  # seconds in a 5-minute bar

DEFAULTS = {
    "symbols": ["BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD", "AVAX/USD"],
    "startBalance": 25.0,
    "floor": 15.0,
    "feePct": 0.25,             # Alpaca crypto taker fee, per side, percent
    "assumedSpreadPct": 0.10,   # full spread used by the backtest (no historical quotes); the bot uses the live quote
    "maxSpreadPct": 0.50,       # bot skips an entry when the live spread is wider than this
    "minScore": 75,
    "maxPositionPct": 50,       # of virtual equity per trade
    "maxOpen": 2,
    "stopAtr": 1.5,
    "targetR": 2.0,
    "takeFraction": 0.5,
    "trailAtr": 2.0,
    "timeStopHours": 24,
    "emaFast": 20, "emaFastSlopeBars": 3, "emaHourly": 50,
    "breakoutBars": 12, "rsiLen": 14, "rsiMax": 75, "atrLen": 14,
    "rvolBars": 288, "rvolTop": 1.5,
    "minBars24h": 200,          # a symbol with fewer 5m bars in the last 24h is skipped (thin data)
    "cooldownBars": 1,
    "weights": {"aboveHourlyEma": 13, "fastEmaRising": 12, "breakout": 25, "rvol": 30, "rsiOk": 20},
}


def load_params():
    p = json.loads(json.dumps(DEFAULTS))
    try:
        user = json.loads((HERE / "params.json").read_text()).get("params", {})
    except Exception:
        user = {}
    for k, v in user.items():
        if k == "weights" and isinstance(v, dict):
            p["weights"].update(v)
        elif k in p:
            p[k] = v
    return p


# ---------------- data (read-only market data) ----------------

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(path, q):
    url = f"{DATA}{path}?{urllib.parse.urlencode(q)}"
    hdr = {"Accept": "application/json", "User-Agent": "gm-crypto-paper"}
    k, s = (os.environ.get("ALPACA_KEY_ID") or "").strip(), (os.environ.get("ALPACA_SECRET_KEY") or "").strip()
    if k and s:
        hdr.update({"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s})
    with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_bars(symbols, start, end):
    """5-minute bars {sym: [{t,o,h,l,c,v}, ...]} oldest first, start <= t < end (epoch seconds)."""
    out = {s: [] for s in symbols}
    token = None
    for _ in range(200):
        q = {"symbols": ",".join(symbols), "timeframe": "5Min", "start": iso(start), "end": iso(end),
             "limit": 10000, "sort": "asc"}
        if token:
            q["page_token"] = token
        js = _get("/bars", q)
        for s, bars in (js.get("bars") or {}).items():
            for b in bars:
                out.setdefault(s, []).append({"t": ts(b["t"]), "o": float(b["o"]), "h": float(b["h"]),
                                              "l": float(b["l"]), "c": float(b["c"]), "v": float(b.get("v") or 0)})
        token = js.get("next_page_token")
        if not token:
            break
    for s in out:
        seen = {}
        for b in out[s]:
            seen[b["t"]] = b
        out[s] = [seen[t] for t in sorted(seen) if t < end]
    return out


def fetch_quotes(symbols):
    js = _get("/latest/quotes", {"symbols": ",".join(symbols)})
    q = {}
    for s, v in (js.get("quotes") or {}).items():
        try:
            bp, ap = float(v["bp"]), float(v["ap"])
            if bp > 0 and ap >= bp:
                q[s] = {"bid": bp, "ask": ap}
        except Exception:
            pass
    return q


# ---------------- indicators ----------------

def ema(vals, n):
    out, k, e = [], 2.0 / (n + 1), None
    for v in vals:
        e = v if e is None else e + k * (v - e)
        out.append(e)
    return out


def wilder(vals, n):
    out, a = [], None
    for i, v in enumerate(vals):
        if i < n - 1:
            out.append(None)
            continue
        a = sum(vals[i - n + 1:i + 1]) / n if a is None else (a * (n - 1) + v) / n
        out.append(a)
    return out


def indicators(bars, p):
    """Arrays aligned with bars: emaF, emaH (1h EMA of completed hours), atr, rsi, hi12 (prior high), rvol, n24."""
    n = len(bars)
    c = [b["c"] for b in bars]
    emaF = ema(c, p["emaFast"])
    tr = [bars[0]["h"] - bars[0]["l"]] + [max(bars[i]["h"] - bars[i]["l"], abs(bars[i]["h"] - c[i - 1]),
                                              abs(bars[i]["l"] - c[i - 1])) for i in range(1, n)]
    atr = wilder(tr, p["atrLen"])
    gains = [0.0] + [max(c[i] - c[i - 1], 0) for i in range(1, n)]
    losses = [0.0] + [max(c[i - 1] - c[i], 0) for i in range(1, n)]
    ag, al = wilder(gains, p["rsiLen"]), wilder(losses, p["rsiLen"])
    rsi = [None if g is None else (100.0 if l == 0 else 100 - 100 / (1 + g / l)) for g, l in zip(ag, al)]
    # hourly closes: last 5m close inside each clock hour; an hour counts once it has fully ended
    hours, hclose = [], []
    for b in bars:
        h = b["t"] // 3600
        if hours and hours[-1] == h:
            hclose[-1] = b["c"]
        else:
            hours.append(h); hclose.append(b["c"])
    hema = ema(hclose, p["emaHourly"])
    emaH, j = [], -1
    for b in bars:
        done_before = (b["t"] + BAR) // 3600  # hours strictly before this one are complete at this bar's close
        while j + 1 < len(hours) and hours[j + 1] < done_before:
            j += 1
        emaH.append(hema[j] if j + 1 >= p["emaHourly"] else None)
    k = p["breakoutBars"]
    hi = [max(b["h"] for b in bars[i - k:i]) if i >= k else None for i in range(n)]
    m = p["rvolBars"]
    rvol, s = [], 0.0
    vols = [b["v"] for b in bars]
    for i in range(n):
        if i >= m:
            avg = s / m
            rvol.append(vols[i] / avg if avg > 0 else 0.0)
            s += vols[i] - vols[i - m]
        else:
            rvol.append(None)
            s += vols[i]
    n24, lo = [], 0
    for i in range(n):
        while bars[lo]["t"] <= bars[i]["t"] - 86400:
            lo += 1
        n24.append(i - lo + 1)
    return {"emaF": emaF, "emaH": emaH, "atr": atr, "rsi": rsi, "hi": hi, "rvol": rvol, "n24": n24}


def score_at(bars, ind, i, p):
    """Confidence score 0-100 for a long on bar i's close, with the parts so it can be explained."""
    w, k = p["weights"], p["emaFastSlopeBars"]
    if i < max(k, p["breakoutBars"]) or ind["emaH"][i] is None or ind["atr"][i] is None or ind["rsi"][i] is None \
            or ind["rvol"][i] is None:
        return None
    c = bars[i]["c"]
    parts = {
        "aboveHourlyEma": w["aboveHourlyEma"] if c > ind["emaH"][i] else 0,
        "fastEmaRising": w["fastEmaRising"] if ind["emaF"][i] > ind["emaF"][i - k] else 0,
        "breakout": w["breakout"] if c > ind["hi"][i] else 0,
        "rvol": round(w["rvol"] * min(max((ind["rvol"][i] - 1.0) / (p["rvolTop"] - 1.0), 0.0), 1.0), 1),
        "rsiOk": w["rsiOk"] if ind["rsi"][i] < p["rsiMax"] else 0,
    }
    return {"score": round(sum(parts.values()), 1), "parts": parts, "rvol": round(ind["rvol"][i], 2),
            "rsi": round(ind["rsi"][i], 1), "atr": ind["atr"][i], "close": c, "thin": ind["n24"][i] < p["minBars24h"]}


# ---------------- virtual ledger (same code path for bot and backtest) ----------------

def new_state(p):
    return {"mode": MODE, "startBalance": p["startBalance"], "cash": p["startBalance"], "positions": [],
            "history": [], "floorLocked": False, "lastBarT": None, "lastClose": {}, "lastExit": {}}


def _sell(pos, qty, px, why, t, p):
    bid = px * (1 - pos["hs"])
    net = qty * bid * (1 - p["feePct"] / 100.0)
    pos["qty"] -= qty
    pos["proceeds"] += net
    pos["fills"].append({"t": t, "px": round(bid, 8), "qty": qty, "why": why})
    return net


def step_bar(pos, bar, atr, p):
    """Apply one completed 5m bar to an open position (exits use the bar's LOW/HIGH, so a missed run never skips a stop).
    Returns (cash received, exit reason or None). Inside a bar (conservative): stop first, then the +2R partial,
    then the time stop on the close; the trail is raised from the bar's high after the bar, for the next bar."""
    cash, t_end = 0.0, bar["t"] + BAR
    if bar["l"] <= pos["stop"]:
        why = "trail" if pos["half"] else "stop"
        cash += _sell(pos, pos["qty"], min(bar["o"], pos["stop"]), why, t_end, p)  # a gap through fills at the open
        return cash, why
    target = pos["entry"] + p["targetR"] * pos["R"]
    if not pos["half"] and bar["h"] >= target:
        cash += _sell(pos, pos["qty0"] * p["takeFraction"], max(bar["o"], target), "target", t_end, p)
        pos["half"] = True
    pos["high"] = max(pos["high"], bar["h"])
    if t_end - pos["t"] >= p["timeStopHours"] * 3600:
        cash += _sell(pos, pos["qty"], bar["c"], "time", t_end, p)
        return cash, "time"
    if pos["half"] and atr:
        pos["stop"] = max(pos["stop"], pos["high"] - p["trailAtr"] * atr)
    return cash, None


def close_record(pos, why, t):
    pnl = pos["proceeds"] - pos["cost"]
    risk = pos["qty0"] * pos["R"]
    q = sum(f["qty"] for f in pos["fills"]) or 1e-12
    return {"sym": pos["sym"], "entryAt": iso(pos["t"]), "exitAt": iso(t), "entry": round(pos["entry"], 6),
            "exit": round(sum(f["px"] * f["qty"] for f in pos["fills"]) / q, 6), "stop0": round(pos["stop0"], 6),
            "cost": round(pos["cost"], 4), "pnl": round(pnl, 4), "R": round(pnl / risk, 2) if risk > 0 else None,
            "score": pos["score"], "reason": why, "partial": pos["half"]}


def equity(state):
    e = state["cash"]
    for pos in state["positions"]:
        px = state["lastClose"].get(pos["sym"], pos["entry"])
        e += pos["qty"] * px * (1 - pos["hs"])  # marked at the bid; the exit fee is charged when it sells
    return e


def flatten(state, t, why, p):
    for pos in list(state["positions"]):
        px = state["lastClose"].get(pos["sym"], pos["entry"])
        state["cash"] += _sell(pos, pos["qty"], px, why, t, p)
        state["history"].append(close_record(pos, why, t))
        state["positions"].remove(pos)


def run_time(state, t, at, quote_fn, p, allow_entries=True, picker=None):
    """Process the 5m bars that START at time t (they closed at t+300).
    at = {sym: (bars, ind, i)} for symbols that have a bar at t. quote_fn(sym) -> (ask, halfSpreadFraction) or None
    is the price an entry would fill at right after this bar. picker(cands) may reorder/replace candidates
    (the random baseline uses it). Returns the list of entries made."""
    t_end = t + BAR
    for sym, (bars, ind, i) in at.items():
        state["lastClose"][sym] = bars[i]["c"]
    for pos in list(state["positions"]):
        if pos["sym"] not in at:
            continue
        bars, ind, i = at[pos["sym"]]
        if bars[i]["t"] <= pos["lastBarT"]:
            continue
        cash, why = step_bar(pos, bars[i], ind["atr"][i], p)
        pos["lastBarT"] = bars[i]["t"]
        state["cash"] += cash
        if why:
            state["history"].append(close_record(pos, why, t_end))
            state["positions"].remove(pos)
            state["lastExit"][pos["sym"]] = t
    state["lastBarT"] = t
    if state["floorLocked"]:
        return []
    if equity(state) <= p["floor"]:
        flatten(state, t_end, "floor", p)
        state["floorLocked"] = True
        return []
    if not allow_entries:
        return []
    held = {x["sym"] for x in state["positions"]}
    cands = []
    for sym, (bars, ind, i) in at.items():
        if sym in held or t - state["lastExit"].get(sym, -10**12) < p["cooldownBars"] * BAR:
            continue
        sc = score_at(bars, ind, i, p)
        if sc and not sc["thin"]:
            cands.append((sc["score"], sym, sc))
    cands.sort(key=lambda c: (-c[0], c[1]))
    cands = [c for c in cands if c[0] >= p["minScore"]]
    if picker:
        cands = picker(cands, at, state)
    made = []
    for s, sym, sc in cands:
        if len(state["positions"]) >= p["maxOpen"]:
            break
        q = quote_fn(sym)
        if not q:
            continue
        ask, hs = q
        if 2 * hs * 100 > p["maxSpreadPct"]:
            continue
        eq = equity(state)
        notional = min(eq * p["maxPositionPct"] / 100.0, state["cash"])
        if notional < 1.0 or not sc["atr"] or sc["atr"] <= 0:
            continue
        qty = notional * (1 - p["feePct"] / 100.0) / ask
        stop = ask - p["stopAtr"] * sc["atr"]
        pos = {"sym": sym, "qty": qty, "qty0": qty, "entry": ask, "stop": stop, "stop0": stop, "R": ask - stop,
               "hs": hs, "cost": notional, "proceeds": 0.0, "half": False, "high": ask, "t": t_end, "lastBarT": t,
               "score": s, "parts": sc["parts"], "fills": []}
        state["cash"] -= notional
        state["positions"].append(pos)
        made.append(pos)
    return made


def group_by_time(bars_by_sym, p):
    """{t: {sym: (bars, ind, i)}} plus the indicator arrays, for every symbol."""
    inds = {s: indicators(b, p) for s, b in bars_by_sym.items() if b}
    by_t = {}
    for s, bars in bars_by_sym.items():
        if not bars:
            continue
        for i, b in enumerate(bars):
            by_t.setdefault(b["t"], {})[s] = (bars, inds[s], i)
    return by_t
