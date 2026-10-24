#!/usr/bin/env python3
"""Crypto paper bot (VIRTUAL). One cycle per run, every 5 minutes from .github/workflows/crypto-paper.yml.

Reads real crypto prices from Alpaca's free market data and simulates fills in its OWN ledger (state.json).
It never places an order and never reads or touches the Alpaca trading account the stock bot uses.
Mode is hard-coded "virtual"; there is no live switch.

A cycle: fetch the last ~4 days of 5m bars, replay every completed bar since the last run through the open
positions (stops/targets use each bar's high/low, so missed runs never skip an exit), then score the newest bar
and maybe enter at the live ask. Writes state.json, heartbeat.json, and last-error.json on error.
Reset after the $15 floor lock: set "floorLocked": false in state.json by hand (or delete state.json to restart at $25).
"""
import json, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402

CT = ZoneInfo("America/Chicago")
LOOKBACK = 4 * 86400  # enough for the 1h EMA50 and the 24h volume average
MAX_HISTORY = 500


def load_state(p):
    try:
        st = json.loads((HERE / "state.json").read_text())
        st.setdefault("lastExit", {}); st.setdefault("lastClose", {})
        st["mode"] = core.MODE
        return st
    except Exception:
        return core.new_state(p)


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1) + "\n")


def cycle(state, bars, quotes, now, p):
    """Pure: advance `state` with the bars completed by `now` (epoch s). quotes = {sym: {bid, ask}} live.
    Only the NEWEST completed bar may open a trade (catch-up bars after a missed run only manage exits)."""
    done = {s: [b for b in bl if b["t"] + core.BAR <= now] for s, bl in bars.items()}
    by_t = core.group_by_time(done, p)
    last = state.get("lastBarT")
    times = sorted(t for t in by_t if last is None or t > last)
    if last is None:
        times = times[-1:]  # first run: no history to replay
    newest = max(by_t) if by_t else None
    entries = []

    def quote_fn(sym):
        q = quotes.get(sym)
        if not q:
            return None
        mid = (q["bid"] + q["ask"]) / 2
        return q["ask"], (q["ask"] - q["bid"]) / 2 / mid

    for t in times:
        entries += core.run_time(state, t, by_t[t], quote_fn, p, allow_entries=(t == newest))
    return times, entries, by_t.get(newest, {}) if newest else {}


def main():
    p = core.load_params()
    started = datetime.now(CT)
    state = load_state(p)
    try:
        now = int(time.time())
        bars = core.fetch_bars(p["symbols"], now - LOOKBACK, now + 60)
        quotes = core.fetch_quotes(p["symbols"])
        missing = [s for s in p["symbols"] if not bars.get(s)]
        times, entries, latest = cycle(state, bars, quotes, now, p)
        state["history"] = state["history"][-MAX_HISTORY:]
        scores = {}
        for sym, (bl, ind, i) in latest.items():
            sc = core.score_at(bl, ind, i, p)
            if sc:
                scores[sym] = {"score": sc["score"], "rvol": sc["rvol"], "rsi": sc["rsi"], "thin": sc["thin"]}
        eq = core.equity(state)
        state.update({"updatedAt": started.isoformat(), "equity": round(eq, 4), "lastScores": scores,
                      "barsProcessed": len(times), "missingSymbols": missing})
        write("state.json", state)
        status = "floor-locked" if state["floorLocked"] else "ok"
        write("heartbeat.json", {"at": started.isoformat(), "lastRun": started.strftime("%H:%M"),
                                 "day": started.strftime("%Y-%m-%d"), "status": status, "equity": round(eq, 2),
                                 "openPositions": len(state["positions"]), "trades": len(state["history"]),
                                 "entriesThisRun": [e["sym"] for e in entries], "mode": core.MODE,
                                 "cadence": "every 5 minutes, 24/7"})
        print(json.dumps({"status": status, "equity": round(eq, 2), "bars": len(times),
                          "open": [x["sym"] for x in state["positions"]], "scores": scores}))
        print(f"::notice title=crypto bot::{status} equity {eq:.2f} open {len(state['positions'])} bars {len(times)} "
              f"missing {missing} scores {json.dumps({k: v['score'] for k, v in scores.items()})}")
        return 0
    except Exception as e:
        err = {"at": started.isoformat(), "error": f"{type(e).__name__}: {e}"[:500], "trace": traceback.format_exc()[-1500:]}
        write("last-error.json", err)
        write("heartbeat.json", {"at": started.isoformat(), "lastRun": started.strftime("%H:%M"),
                                 "day": started.strftime("%Y-%m-%d"), "status": "error", "error": err["error"],
                                 "equity": state.get("equity"), "openPositions": len(state.get("positions", [])),
                                 "mode": core.MODE, "cadence": "every 5 minutes, 24/7"})
        print(err["error"], file=sys.stderr)
        print("::error title=crypto bot::" + err["error"].replace("\n", " "))
        return 1


if __name__ == "__main__":
    sys.exit(main())
