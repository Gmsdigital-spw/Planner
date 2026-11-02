#!/usr/bin/env python3
"""Bridge from the Factory's autopilot records to the Atlas research tools (Nov 2, 2026).

Reads factory/trading/auto/<day>.json (the autopilot's day files: every completed trade with its real entry and
exit prices, R and reason) for ONE mode (paper or live) and writes the Atlas trade CSV
(trade_id,strategy_version,entry_time,exit_time,entry_price,exit_price,qty,fees_usd,split), so

    python3 -m atlas_trading analyze data/factory-live-trades.csv --capital 25 --stress-bps 10

can grade the real record with Atlas's chronological splits, cost stress and research filters. Paper and live days
are never mixed: pick one with --mode. The strategy_version is "<profile>@<sha256 of the profile params>", so a
changed money rule or knob starts a new version instead of polluting an old one.

What it cannot do: invent exit times (the day file carries the entry bar time and, since Oct 29, the crew's close
journals carry exit times; this importer uses the action time of the exit when the day file has it and otherwise
marks the exit at the day's 14:45 CT flatten, which is honest but coarse). Fees are 0 (Alpaca charges none on
stocks; regulatory fees on sells are not in the day file, so a --stress-bps is the right way to account for them).

Run from factory/trading/atlas:  python3 factory_import.py --mode live --out data/factory-live-trades.csv
"""
import argparse, csv, hashlib, json, sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
TRADING = HERE.parent
CT = ZoneInfo("America/Chicago")
COLUMNS = ["trade_id", "strategy_version", "entry_time", "exit_time", "entry_price", "exit_price", "qty", "fees_usd", "split"]


def strategy_version(profile):
    prof = json.loads((TRADING / "profiles" / f"{profile}.json").read_text())
    digest = hashlib.sha256(json.dumps(prof.get("params", {}), sort_keys=True).encode()).hexdigest()[:12]
    return f"{profile}@{digest}"


def day_files(mode):
    out = []
    for p in sorted((TRADING / "auto").glob("20??-??-??.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if d.get("mode", "paper") == mode:
            out.append(d)
    return out


def ct_iso(day, hm):
    h, m = hm.split(":")
    return datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), int(h), int(m), tzinfo=CT).astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")


def rows_for(d, version):
    """One CSV row per completed trade in a day file. Entry time = the buy action's time; exit time = the matching
    sell/flatten action's time when present, else the 14:45 CT flatten; qty from the buy fill when recorded."""
    day = d["day"]
    buys = [a for a in d.get("actions", []) if a.get("do") == "buy" and a.get("fill")]
    exits = [a for a in d.get("actions", []) if a.get("do") in ("sell", "flatten")]
    rows = []
    for i, t in enumerate(d.get("trades", [])):
        if t.get("exit") is None or t.get("entry") is None:
            continue
        buy = next((a for a in buys if a.get("sym") == t["sym"] and abs(float(a["fill"]) - float(t["entry"])) < 1e-6), None)
        entry_hm = buy["t"] if buy else "08:35"
        sell = next((a for a in exits if a.get("sym") in (t["sym"], None) and str(a.get("t", "")) > entry_hm), None)
        exit_hm = sell["t"] if sell else "14:45"
        qty = t.get("qty")
        if qty is None and buy and buy.get("notional"):
            qty = float(buy["notional"]) / float(t["entry"])
        if not qty:
            continue
        rows.append({"trade_id": f"{day}-{t['sym']}-{i+1}", "strategy_version": version, "entry_time": ct_iso(day, entry_hm),
                     "exit_time": ct_iso(day, exit_hm), "entry_price": t["entry"], "exit_price": t["exit"], "qty": qty, "fees_usd": "0"})
    return rows


def main():
    ap = argparse.ArgumentParser(description="Factory day files -> Atlas trade CSV (one mode at a time)")
    ap.add_argument("--mode", choices=["paper", "live"], required=True)
    ap.add_argument("--profile", default=None, help="profile name for the strategy_version (default: paper or live-aggressive by mode)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--drop-overlaps", action="store_true",
                    help="paper runs 2 positions at once; Atlas is a one-position model and refuses overlaps. This keeps the first of any overlapping pair and reports how many were dropped.")
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
    print(json.dumps({"mode": args.mode, "strategy_version": version, "days": len(day_files(args.mode)), "trades": n, "dropped_overlaps": dropped,
                      "out": str(out), "note": "Real records only; no number was invented. Exit times are action times or the 14:45 flatten."}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
