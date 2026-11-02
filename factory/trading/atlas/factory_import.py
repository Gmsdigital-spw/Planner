#!/usr/bin/env python3
"""Bridge from the Factory's autopilot records to the Atlas research tools (Nov 2, 2026).

Reads factory/trading/auto/<day>.json (the autopilot's day files: every completed trade with its real entry and
exit prices, R and reason) for ONE mode (paper or live) and writes the Atlas trade CSV
(trade_id,strategy_version,entry_time,exit_time,entry_price,exit_price,qty,fees_usd,split), so

    python3 -m atlas_trading analyze data/factory-live-trades.csv --capital 25 --stress-bps 10

can grade the real record with Atlas's chronological splits, cost stress and research filters. Paper and live days
are never mixed: pick one with --mode. The strategy_version is "<profile>@<sha256 of the EFFECTIVE params>" (the
profile over the lab's params.json, plus the universe), so a changed money rule or knob starts a new version.

Exit times, most exact first: the trade's "exitAt" (Alpaca's filled_at, written by the autopilot since Nov 2, 2026),
its "t" (the cycle that journaled it), the matching filled sell/flatten action, else the day's flatten time, capped
at the next buy's time that day (a placeholder may never run past a later real entry, or Atlas refuses the record).
Refused sells (status >= 300) are never exits. A partial stop fill plus its follow-up row never sum to more than
the position. Fees are 0 (Alpaca charges none on stocks; regulatory sell fees are not in the day file, so
--stress-bps is the way to account for them).

The all-in live profile re-invests every dollar, so after one winner the next notional is above the deposit and
Atlas's fixed-capital model refuses "--capital 25". The output JSON carries "capital_needed": pass that number to
analyze (--capital <capital_needed>); it is the peak notional the record ever needed, not a claim about the deposit.

Run from factory/trading/atlas:  python3 factory_import.py --mode live --out data/factory-live-trades.csv
"""
import argparse, csv, hashlib, json, math, sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
TRADING = HERE.parent
CT = ZoneInfo("America/Chicago")
COLUMNS = ["trade_id", "strategy_version", "entry_time", "exit_time", "entry_price", "exit_price", "qty", "fees_usd", "split"]


def strategy_version(profile):
    """<profile>@<hash of the parameters the bot actually runs with>: backtest.load_params(profile) (DEFAULT, then
    the lab's params.json, then the profile) plus the profile's universe."""
    sys.path.insert(0, str(TRADING))
    import backtest  # noqa: E402
    prof = backtest.load_profile(profile)
    eff = {"params": backtest.load_params(profile), "universe": prof.get("universe")}
    digest = hashlib.sha256(json.dumps(eff, sort_keys=True).encode()).hexdigest()[:12]
    return f"{profile}@{digest}"


def day_files(mode):
    """Every day file of one mode: <day>.json and the archived <day>-<mode>.json a mode switch leaves behind."""
    out = []
    for p in sorted((TRADING / "auto").glob("20??-??-??*.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if isinstance(d, dict) and d.get("day") and d.get("mode", "paper") == mode:
            out.append(d)
    return out


def ct_iso(day, hm):
    h, m = hm.split(":")
    return datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), int(h), int(m), tzinfo=CT).astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")


def iso_utc(s):
    """Alpaca's filled_at ("2026-11-03T15:31:02.123456Z" or with an offset) as a UTC ISO string, None if unreadable."""
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt.astimezone(ZoneInfo("UTC")).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def rows_for(d, version):
    """One CSV row per completed trade in a day file. Entry time = the buy action's time. Exit time = the trade's
    exitAt (Alpaca's fill time), else its journal time "t", else the matching FILLED sell/flatten action, else the
    day's flatten time, never later than the next buy that day. qty from the trade, else from the buy's notional
    minus any partial already journaled for the same position."""
    day = d["day"]
    acts = d.get("actions", [])
    buys = [a for a in acts if a.get("do") == "buy" and a.get("fill")]
    ok = lambda a: (a.get("status") is None or int(a.get("status") or 0) < 300) and (a.get("do") != "sell" or a.get("id"))
    exits = [a for a in acts if a.get("do") in ("sell", "flatten") and ok(a)]
    flat_hm = d.get("flatAt") or "14:45"
    rows, emitted = [], {}
    for i, t in enumerate(d.get("trades", [])):
        if t.get("exit") is None or t.get("entry") is None:
            continue
        buy = next((a for a in buys if a.get("sym") == t["sym"] and abs(float(a["fill"]) - float(t["entry"])) < 1e-6), None)
        entry_hm = buy["t"] if buy else "08:35"
        entry_iso = ct_iso(day, entry_hm)
        exit_iso = iso_utc(t.get("exitAt")) if t.get("exitAt") else None
        if not exit_iso and t.get("t") and str(t["t"]) >= entry_hm:
            exit_iso = ct_iso(day, t["t"])
        if not exit_iso:
            sell = next((a for a in exits if a.get("sym") == t["sym"] and str(a.get("t", "")) > entry_hm), None) or \
                   next((a for a in exits if a.get("sym") is None and str(a.get("t", "")) > entry_hm), None)
            exit_hm = sell["t"] if sell else flat_hm
            later_buys = [str(a["t"]) for a in buys if str(a.get("t", "")) > entry_hm]
            if later_buys and not (sell and sell.get("sym") == t["sym"]):
                exit_hm = min(exit_hm, min(later_buys))   # a placeholder never runs past the next real entry
            exit_iso = ct_iso(day, exit_hm)
        key = (t["sym"], float(t["entry"]))
        qty = t.get("qty")
        if qty is None and buy and buy.get("notional"):
            qty = float(buy["notional"]) / float(t["entry"]) - emitted.get(key, 0.0)
        if not qty or float(qty) <= 0:
            continue
        emitted[key] = emitted.get(key, 0.0) + float(qty)
        rows.append({"trade_id": f"{day}-{t['sym']}-{i+1}", "strategy_version": version, "entry_time": entry_iso,
                     "exit_time": max(exit_iso, entry_iso), "entry_price": t["entry"], "exit_price": t["exit"], "qty": qty, "fees_usd": "0"})
    return rows


def capital_needed(rows, stress_bps):
    """The smallest --capital Atlas's fixed-capital, one-position model accepts for this record: the peak of
    (notional minus the stressed P/L banked before it), rounded up to the cent, plus one cent."""
    cum, need = 0.0, 0.0
    for r in rows:
        q, e, x = float(r["qty"]), float(r["entry_price"]), float(r["exit_price"])
        need = max(need, e * q - cum)
        cum += (x - e) * q - (e + x) * q * stress_bps / 10000.0
    return math.ceil(need * 100) / 100 + 0.01 if rows else 0.0


def main():
    ap = argparse.ArgumentParser(description="Factory day files -> Atlas trade CSV (one mode at a time)")
    ap.add_argument("--mode", choices=["paper", "live"], required=True)
    ap.add_argument("--profile", default=None, help="profile name for the strategy_version (default: paper or live-aggressive by mode)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--drop-overlaps", action="store_true",
                    help="paper runs 2 positions at once; Atlas is a one-position model and refuses overlaps. This keeps the first of any overlapping pair and reports how many were dropped.")
    ap.add_argument("--stress-bps", type=float, default=10.0, help="the per-side cost stress you will pass to analyze (for capital_needed)")
    args = ap.parse_args()
    profile = args.profile or ("live-aggressive" if args.mode == "live" else "paper")
    version = strategy_version(profile)
    rows = []
    for d in day_files(args.mode):
        rows.extend(rows_for(d, version))
    rows.sort(key=lambda r: r["entry_time"])
    dropped = 0
    if args.drop_overlaps:
        kept, last_exit = [], ""
        for r in rows:
            if r["entry_time"] < last_exit:
                dropped += 1
                continue
            kept.append(r)
            last_exit = max(last_exit, r["exit_time"])
        rows = kept
    # chronological 60/20/20 split by trade order; the Atlas analyzer refuses overlaps and out-of-order splits
    n = len(rows)
    for i, r in enumerate(rows):
        r["split"] = "train" if i < n * 0.6 else ("validation" if i < n * 0.8 else "test")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    cap = capital_needed(rows, args.stress_bps)
    print(json.dumps({"mode": args.mode, "strategy_version": version, "days": len(day_files(args.mode)), "trades": n, "dropped_overlaps": dropped,
                      "out": str(out), "capital_needed": cap,
                      "analyze": f"python3 -m atlas_trading analyze {out} --capital {cap:.2f} --stress-bps {args.stress_bps:g}",
                      "note": "Real records only; no number was invented. Exit times: Alpaca fill times when the day file has them, else journal/action times, else the flatten time capped at the next entry. capital_needed is the peak notional the record needed, not the deposit."}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
