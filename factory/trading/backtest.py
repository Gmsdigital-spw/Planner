#!/usr/bin/env python3
"""
Trading Floor lab: replay the crew's exact strategy on real past market days it has not seen.

Runs inside the free GitHub Action "Trading lab" (it has the Alpaca keys); reads historical 5-minute bars
from Alpaca's free IEX feed, simulates the $25 account with every rule (2% risk, 2:1, 40% cap, 2 positions,
4 entries/day, $1.50 daily loss limit, flat by 2:45 PM CT, $20 floor) plus a realistic cost per trade
(spread + slippage), and writes results to factory/trading/lab/<id>.json. Each result carries trades, win rate,
average R, profit factor (gross profit / gross loss; added Oct 23, 2026), net P/L, max drawdown and breaches.

Walk-forward test (the honest kind): the job picks TUNE days and HOLDOUT days that do not overlap.
Every candidate parameter set is scored on TUNE days; the best one is then judged on HOLDOUT days the
search never saw. A candidate is only "adoptable" if it beats the current params on HOLDOUT with at least
20 holdout trades and no worse max drawdown. Adoption itself is done by the Trading lab run, never here.

Job file factory/trading/lab/jobs/<id>.json:
  {"id":"lab-2026-10-21","symbols":["SPY","QQQ",...],"tune":["2026-03-02",...],"holdout":["2026-06-10",...],
   "candidates":[{...param overrides...}, ...]}      # current params always included as the baseline
"""
import json, os, sys, math, time, itertools, random, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.abspath(__file__))
CT = ZoneInfo("America/Chicago")
PARAMS_FILE = os.path.join(ROOT, "params.json")
DEFAULT = {
    "bankroll": 25.0, "floor": 20.0, "risk_pct": 2.0, "min_rr": 2.0, "max_pos_pct": 40.0, "max_positions": 2,
    "max_entries": 4, "daily_loss": 1.5, "sma_len": 20, "pullback_bars": 6, "pullback_pct": 0.25,
    "min_stop_pct": 0.30, "be_at_r": 1.0, "trail_at_r": 1.5, "trail_r": 1.0, "target_r": 2.0,
    "start_ct": "08:35", "last_entry_ct": "14:00", "flat_ct": "14:45", "cost_bps": 6.0, "min_price": 5.0,
    "setup": "pullback",   # entry rule: "pullback" (default), "orb" (opening-range breakout), "pullback_orh"
    "orb_min": 15,         # opening-range length in minutes (orb, pullback_orh)
    "orb_stop": "mid",     # orb stop: "mid" (range midpoint) or "low" (range low)
}
# Hard limits the lab may never change (the money rules belong to Grayson)
LOCKED = {"bankroll", "floor", "risk_pct", "max_pos_pct", "max_positions", "daily_loss", "flat_ct", "min_rr"}

def load_params():
    p = dict(DEFAULT)
    if os.path.exists(PARAMS_FILE):
        try:
            p.update({k: v for k, v in json.load(open(PARAMS_FILE)).get("params", {}).items() if k not in LOCKED})
        except Exception:
            pass
    return p

# ---------------- data ----------------
def fetch_bars(symbols, day):
    """5-minute bars for one trading day (regular hours), {sym: [bar,...]}; bar keys t,o,h,l,c,v,vw."""
    key, sec = os.environ.get("ALPACA_KEY_ID", "").strip(), os.environ.get("ALPACA_SECRET_KEY", "").strip()
    if not (key and sec):
        raise SystemExit("ALPACA_KEY_ID / ALPACA_SECRET_KEY missing")
    d = datetime.fromisoformat(day).replace(tzinfo=CT)
    start = d.replace(hour=8, minute=30).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = d.replace(hour=15, minute=0).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out, token = {s: [] for s in symbols}, None
    for _ in range(30):
        q = {"symbols": ",".join(symbols), "timeframe": "5Min", "start": start, "end": end, "limit": 10000,
             "feed": "iex", "adjustment": "raw"}
        if token:
            q["page_token"] = token
        req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q),
                                     headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec})
        with urllib.request.urlopen(req, timeout=60) as r:
            js = json.load(r)
        for s, bars in (js.get("bars") or {}).items():
            out.setdefault(s, []).extend(bars)
        token = js.get("next_page_token")
        if not token:
            break
    return out

# ---------------- strategy ----------------
def ct_hm(ts):
    t = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(CT)
    return t.strftime("%H:%M")

def setup_at(bars, i, P):
    """Bull's rule at bar i (bars[:i+1] known). Returns (entry, stop) or None."""
    n = P["sma_len"]
    if i < max(n, P["pullback_bars"]) + 1:
        return None
    b = bars[i]
    closes = [x["c"] for x in bars[i - n + 1:i + 1]]
    sma = sum(closes) / n
    # session VWAP up to bar i
    pv = sum(((x["h"] + x["l"] + x["c"]) / 3) * x["v"] for x in bars[:i + 1]); vol = sum(x["v"] for x in bars[:i + 1])
    vwap = pv / vol if vol else b["c"]
    if b["c"] < P["min_price"] or not (b["c"] > vwap and b["c"] > sma):
        return None
    # trend: SMA rising over the window
    prev_sma = sum(x["c"] for x in bars[i - n:i]) / n
    if sma <= prev_sma:
        return None
    # pullback: within the last k bars the low touched within pullback_pct of the SMA, and held above it
    k = P["pullback_bars"]; recent = bars[i - k:i]
    pb_low = min(x["l"] for x in recent)
    touched = any(abs(x["l"] - sma) / sma * 100 <= P["pullback_pct"] or x["l"] <= sma for x in recent)
    if not touched or pb_low < vwap * 0.997:
        return None
    if not (b["c"] > b["o"] and b["c"] > bars[i - 1]["h"]):    # green bar closing above the prior high
        return None
    entry = b["c"]
    stop = min(pb_low * 0.999, entry * (1 - P["min_stop_pct"] / 100))
    if stop >= entry:
        return None
    return entry, stop

def setup_orb(bars, i, P):
    """Opening-range breakout at bar i: the range is the first 15 minutes (bars before 08:45 CT).
    Entry on the first green bar that closes above the range high with volume above the session's
    average bar volume so far; stop under the range midpoint (at least min_stop_pct away)."""
    cut = orb_cut(P)
    rng = [x for x in bars[:i + 1] if ct_hm(x["t"]) < cut]
    if len(rng) < 2 or ct_hm(bars[i]["t"]) < cut:
        return None
    b = bars[i]; prev = bars[i - 1]
    hi = max(x["h"] for x in rng); lo = min(x["l"] for x in rng)
    mid = lo if P.get("orb_stop", "mid") == "low" else (hi + lo) / 2
    if b["c"] < P["min_price"] or not (b["c"] > hi and b["c"] > b["o"] and prev["c"] <= hi):
        return None
    avg_v = sum(x["v"] for x in bars[:i]) / i
    if b["v"] <= avg_v:
        return None
    entry = b["c"]
    stop = min(mid * 0.999, entry * (1 - P["min_stop_pct"] / 100))
    if stop >= entry:
        return None
    return entry, stop

def orb_cut(P):
    """CT time (HH:MM) when the opening range ends: 08:30 + orb_min minutes (15 -> 08:45)."""
    m = 8 * 60 + 30 + int(P.get("orb_min", 15))
    return f"{m // 60:02d}:{m % 60:02d}"

def setup_pullback_orh(bars, i, P):
    """Pullback setup, taken only while the name trades above its opening-range high (first orb_min minutes):
    the same entry and stop as setup_at, plus the bar must close above that range high."""
    cut = orb_cut(P)
    if ct_hm(bars[i]["t"]) < cut:
        return None
    rng = [x for x in bars[:i + 1] if ct_hm(x["t"]) < cut]
    if len(rng) < 2 or bars[i]["c"] <= max(x["h"] for x in rng):
        return None
    return setup_at(bars, i, P)

SETUPS = {"pullback": setup_at, "orb": setup_orb, "pullback_orh": setup_pullback_orh}

def simulate(data_by_day, P):
    eq = P["bankroll"]; peak = eq; mdd = 0.0; trades = []; days = []; breaches = 0
    cost = P["cost_bps"] / 10000.0
    setup_fn = SETUPS.get(P.get("setup", "pullback"), setup_at)
    for day, data in data_by_day:
        if eq <= P["floor"]:
            days.append({"day": day, "pnl": 0.0, "locked": True}); continue
        day_start = eq; open_pos = []; entries = 0; stopped = set(); day_pnl = 0.0
        # merge timeline
        stamps = sorted({b["t"] for bars in data.values() for b in bars})
        idx = {s: {b["t"]: j for j, b in enumerate(bars)} for s, bars in data.items()}
        for ts in stamps:
            hm = ct_hm(ts)
            # manage open positions on this bar
            for pos in list(open_pos):
                j = idx[pos["sym"]].get(ts)
                if j is None:
                    continue
                b = data[pos["sym"]][j]
                R = pos["entry"] - pos["stop0"]
                exit_px = None
                if b["l"] <= pos["stop"]:
                    exit_px = min(pos["stop"], b["o"])              # gap through stop fills at the open
                elif b["h"] >= pos["target"]:
                    exit_px = pos["target"]
                elif hm >= P["flat_ct"]:
                    exit_px = b["c"]
                if exit_px is None:
                    pos["high"] = max(pos["high"], b["h"])
                    gain_r = (pos["high"] - pos["entry"]) / R
                    if gain_r >= P["trail_at_r"]:
                        pos["stop"] = max(pos["stop"], pos["high"] - P["trail_r"] * R)
                    elif gain_r >= P["be_at_r"]:
                        pos["stop"] = max(pos["stop"], pos["entry"])
                    continue
                pnl = pos["qty"] * (exit_px * (1 - cost) - pos["entry"] * (1 + cost))
                eq += pnl; day_pnl += pnl
                trades.append({"day": day, "sym": pos["sym"], "entry": round(pos["entry"], 4), "exit": round(exit_px, 4),
                               "r": round((exit_px - pos["entry"]) / R, 2), "pnl": round(pnl, 4)})
                if exit_px < pos["entry"]:
                    stopped.add(pos["sym"])
                open_pos.remove(pos)
            peak = max(peak, eq); mdd = max(mdd, peak - eq)
            if day_pnl <= -P["daily_loss"] or eq <= P["floor"]:
                for pos in list(open_pos):                          # Bear flattens at the next bar close
                    j = idx[pos["sym"]].get(ts)
                    px = data[pos["sym"]][j]["c"] if j is not None else pos["entry"]
                    pnl = pos["qty"] * (px * (1 - cost) - pos["entry"] * (1 + cost)); eq += pnl; day_pnl += pnl
                    trades.append({"day": day, "sym": pos["sym"], "entry": pos["entry"], "exit": px,
                                   "r": round((px - pos["entry"]) / (pos["entry"] - pos["stop0"]), 2), "pnl": round(pnl, 4)})
                    open_pos.remove(pos)
                break
            if hm < P["start_ct"] or hm > P["last_entry_ct"] or entries >= P["max_entries"] or len(open_pos) >= P["max_positions"]:
                continue
            for sym, bars in data.items():
                if len(open_pos) >= P["max_positions"] or entries >= P["max_entries"]:
                    break
                if sym in stopped or any(p["sym"] == sym for p in open_pos):
                    continue
                j = idx[sym].get(ts)
                if j is None:
                    continue
                s = setup_fn(bars, j, P)
                if not s:
                    continue
                entry, stop = s
                entry *= 1 + cost / 2                                # pay half the spread to get in
                target = entry + P["target_r"] * (entry - stop)
                if (target - entry) / (entry - stop) < P["min_rr"] - 1e-9:
                    continue
                risk = eq * P["risk_pct"] / 100
                cash = eq - sum(p["qty"] * p["entry"] for p in open_pos)
                notional = min(risk / ((entry - stop) / entry), cash * P["max_pos_pct"] / 100, cash)
                if notional < 1.0:
                    continue
                open_pos.append({"sym": sym, "entry": entry, "stop": stop, "stop0": stop, "target": target,
                                 "qty": notional / entry, "high": entry})
                entries += 1
        if open_pos:                                                  # never overnight
            for pos in open_pos:
                bars = data[pos["sym"]]; px = bars[-1]["c"] if bars else pos["entry"]
                pnl = pos["qty"] * (px * (1 - cost) - pos["entry"] * (1 + cost)); eq += pnl; day_pnl += pnl
                trades.append({"day": day, "sym": pos["sym"], "entry": pos["entry"], "exit": px,
                               "r": round((px - pos["entry"]) / (pos["entry"] - pos["stop0"]), 2), "pnl": round(pnl, 4)})
        peak = max(peak, eq); mdd = max(mdd, peak - eq)
        if day_pnl < -P["daily_loss"] - 0.25:
            breaches += 1
        days.append({"day": day, "pnl": round(day_pnl, 4), "equity": round(eq, 4)})
    wins = [t for t in trades if t["pnl"] > 0]
    n = len(trades)
    gross_profit = sum(t["pnl"] for t in wins)                       # dollars the winners made (after costs)
    gross_loss = -sum(t["pnl"] for t in trades if t["pnl"] < 0)      # dollars the losers lost (after costs)
    return {"trades": n, "wins": len(wins), "winRate": round(len(wins) / n * 100, 1) if n else None,
            "avgR": round(sum(t["r"] for t in trades) / n, 3) if n else None,
            # profit factor = gross profit / gross loss from the replayed trades; above 1.0 = winners paid for the
            # losers. None when there was no losing trade to divide by (never a made-up value).
            "profitFactor": round(gross_profit / gross_loss, 3) if gross_loss > 0 else None,
            "grossProfit": round(gross_profit, 4), "grossLoss": round(gross_loss, 4),
            "netPnl": round(eq - P["bankroll"], 4), "endEquity": round(eq, 4), "maxDrawdown": round(mdd, 4),
            "worstDay": min((d["pnl"] for d in days), default=0), "bestDay": max((d["pnl"] for d in days), default=0),
            "breaches": breaches, "days": days, "sample": trades[:40]}

def main():
    if len(sys.argv) < 2:
        print("usage: backtest.py <job.json>"); return 2
    job = json.load(open(sys.argv[1]))
    jid = job.get("id") or os.path.splitext(os.path.basename(sys.argv[1]))[0]
    base = load_params()
    cands = [{}] + [c for c in job.get("candidates", []) if isinstance(c, dict)][:12]
    syms = job.get("symbols") or ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN", "META", "AMD", "TSLA"]
    cache = {}
    def days_data(days):
        out = []
        for d in days:
            if d not in cache:
                try:
                    cache[d] = fetch_bars(syms, d)
                except Exception as e:
                    print("bars failed", d, repr(e)[:200]); cache[d] = {}
                time.sleep(0.4)
            if any(cache[d].values()):
                out.append((d, cache[d]))
        return out
    tune, hold = days_data(job.get("tune", [])), days_data(job.get("holdout", []))
    results = []
    for c in cands:
        P = dict(base); P.update({k: v for k, v in c.items() if k not in LOCKED and k in DEFAULT})
        r_t = simulate(tune, P); r_h = simulate(hold, P)
        results.append({"overrides": {k: v for k, v in c.items() if k not in LOCKED and k in DEFAULT},
                        "tune": {k: v for k, v in r_t.items() if k not in ("days", "sample")},
                        "holdout": {k: v for k, v in r_h.items() if k != "sample"}, "holdoutSample": r_h["sample"][:15]})
    baseline = results[0]
    best = max(results[1:], key=lambda r: (r["tune"]["netPnl"], r["tune"]["avgR"] or -9), default=None)
    adopt = None
    if best:
        bh, ch = baseline["holdout"], best["holdout"]
        if (ch["trades"] >= 20 and ch["netPnl"] > bh["netPnl"] and ch["maxDrawdown"] <= bh["maxDrawdown"] + 0.10
                and (ch["avgR"] or -9) > (bh["avgR"] or -9) and ch["breaches"] == 0):
            adopt = best["overrides"]
    out = {"id": jid, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "symbols": syms,
           "tuneDays": [d for d, _ in tune], "holdoutDays": [d for d, _ in hold], "params": base,
           "baseline": baseline, "results": results, "bestOnTune": best["overrides"] if best else None,
           "adoptable": adopt,
           "note": "Past days only. A strategy that worked on past days can still lose on the next one."}
    os.makedirs(os.path.join(ROOT, "lab"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "lab", f"{jid}.json"), "w"), indent=1)
    print(json.dumps({"id": jid, "baselineHoldout": {k: baseline["holdout"][k] for k in ("trades", "winRate", "avgR", "profitFactor", "netPnl", "maxDrawdown")},
                      "adoptable": adopt}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
