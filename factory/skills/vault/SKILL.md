---
name: vault
floor: trading
role: Ledger + kill switch
judged_on: floor never breached
updated: 2026-10-23
---
# Vault — Ledger + kill switch

## Job
Floor = deposits. Touch it: flatten + lock.

## Exact steps (keep current; rewrite when a better way is proven)
1. Read this file and /factory/LESSONS.md before working.
2. Check the playbook for this task in /factory/playbooks/ and use it.
3. Do the work. Score it. Under 92 = redo, do not ship.
4. Log the result (score + the real number you're judged on).
5. Append one line to "What I've learned" below. "Same as yesterday" = fail.

## Quality checklist
- Real numbers only. Nothing invented, nothing hidden.
- No number without data: every number names the source read this run (gateway result, day file, heartbeat, lab file or the database record). Missing = "unknown (source: ...)", never a guess.
- Looks like a top seller's work, not a template. Warm, real, clear.
- One thing measurably better than last run.

## Nightly trade-journal review (close run; Grayson, Oct 23, 2026)
1. After the flatten and the ledger, read `factory/trading/auto/<day>.json`: `trades[]` (entry, exit, r, why), `actions[]` (times, status codes, qty, stop), `equityOpen` → `equity`, `entries`, `watch`, `avoid`, `lastNote`. Exit times from `/orders?status=closed` (filled_at) when the day file has none.
2. Find recurring errors: anything that happened twice today or on 2 of the last 3 journals: refused orders (status ≥ 300), exits with why `no stop` or `trail refused`, combined index risk over 2% (the one-bet rule), a −1R stop within 15 minutes of entry, an entry in the last 30 minutes of the window (13:30 to 14:00), a winner sold under 2R without a trailed stop, a name traded while on the avoid list (the 15- and 30-minute thresholds were set by Grayson's Oct 23, 2026 review and move only on journal evidence). Read both journal locations for the 2-of-3 check. Quote times, symbols and numbers.
3. Write `factory/trading/journal/<day>.md`: the day's numbers (trades, W/L, net $, equity open → close, breaches), a trade table, "Recurring errors" with evidence, and exactly 3 rules for tomorrow. Each rule names the number it rests on and the check that proves it tomorrow (e.g. "0 actions with status ≥ 300 in tomorrow's day file"). A rule may tighten, never loosen, a money rule or LOCKED knob, and never tells the autopilot a price. (If the close task's write list does not yet allow that folder, write `factory/skills/vault/journal-<day>.md` and say so in the ledger.)
4. No-trade day: say so with the reason from `lastNote`, carry yesterday's 3 rules forward and mark each held / not held. Invent nothing.
5. One dated line in "What I've learned" below: the journal file and the single most important rule.

## What I've learned (append-only, newest last)
- 2026-10-21: equityOpen $25.00 from /bankroll (paper $100k shown as realEquity, ignored). Tomorrow: write equityOpen in the same batch as the gate note so the ledger is never created half-filled.
- 2026-10-21 (close, 14:43): day -$0.03, 1 trade, 0 wins, 1 loss (QQQ -1R), SPY still open pre-flatten; autopilot day file has no stop-fill time, so the ledger logs it as 'by 14:41'. Tomorrow: diff the day file's trades list every run so each exit gets an exact time.
- 2026-10-22: equityOpen $24.96 (total -$0.04 vs $25, from /bankroll pnl); ledger opened in one batch with tape, gate notes and report, per yesterday's fix. Tomorrow: record the first autopilot entry time straight from the actions list so the board and ledger match to the minute.
- 2026-10-22 (close): equity $24.98 (open $24.96), day +$0.02, total -$0.02, 4 trades 2W/2L; day file has no stop-fill times for XLV/DIA, so the board left them out instead of guessing. Tomorrow: read each stop order's filled_at via /orders?status=closed so stop exits get real times.
- 2026-10-22 (close run 14:47): paperDay was still 0 after two traded paper days because the Oct 21 close never wrote it; set to 1 today and maxDrawdown 0.04 (25.00 peak -> 24.96 low) where the board showed 0. Tomorrow: the close run checks report.paperDay against the count of ledger days with orders before adding 1.
- 2026-10-23: equityOpen $24.96 from /bankroll while report/main still said $24.98 from the Oct 22 close; logged the gap in ledger notes instead of choosing one. Tomorrow: at the close run, compare report equity to /bankroll and record /bankroll as the number of record.
- 2026-10-23 (14:43 last scan): /bankroll $24.97 matched the autopilot day file ($24.97, day +$0.01); IWM +$0.013, BAC -$0.007 open, 0 closed trades before the 2:45 flat; 5-min bars came back with SPY missing and IWM 3 bars because limit 78 is shared across symbols. Tomorrow: one bars op per symbol so the live board gets full SPY and position charts.
- 2026-10-23 (close): /bankroll $24.96 open and close (day $0.00), IWM +0.30R / BAC -0.18R both flattened at 2:45 under +1R; paperDay set to 3 by counting ledger days with orders (Oct 21-23), paper report: 8 trades, 50% wins, avg +0.03R, mechanics OK; journal-2026-10-23.md. Tomorrow: record each trade's high since entry in R so 'drifted to the flatten' is a number, not a feel.
- 2026-10-26 (08:47 first scan): /bankroll $24.94 at the open vs $24.96 in Friday's close report with 0 positions over the weekend (a $0.02 gap, likely fractional-share fill/fee settling). Ledger opened at equityOpen $24.94 from /bankroll, totalPnl -$0.06. Change today: at the close run, read /orders?status=closed for Oct 23 to explain the $0.02 before writing the paper report.
- 2026-10-26 (close): /bankroll $24.94 open -> $24.90 close (day -$0.04), trades 3 (IWM -$0.046, XLE +$0.009, SPY -$0.004), report totals 11 trades, 5 wins, 6 losses, totalPnl -$0.10. Tomorrow: take exit prices from /orders closed fills (IWM was 277.372, not the 277.38 stop in the day file).
- 2026-10-26 (close): /bankroll $24.94 -> $24.90 (day -$0.04, total -$0.10), 3 trades 1W/2L (IWM -1.01R, XLE +0.35R after a +1.20R high, SPY -0.15R), paperDay 4; journal-2026-10-26.md. Trade sum over 4 days is -$0.04 vs /bankroll -$0.10, a $0.06 gap. Change tomorrow: first scan reads /orders?status=closed for Oct 21-23 and names the source of that $0.06 before the paper report is quoted again.
- 2026-10-27 (08:57 first scan): /bankroll $24.88, pnl -$0.12 vs report totalPnl -$0.10 yesterday ($0.02 drift from Oct 26 close $24.90 to today's open $24.88, no trades in between). Change today: record equityOpen from the day file next to the close equity so overnight drift is visible.
- 2026-10-27 (14:44 last hourly scan): /bankroll $24.92 (open $24.88, day +$0.04), 2 open: SPY +$0.014 (770.80 vs 769.69), QQQ +$0.022 (722.49 vs 719.82); /bankroll pnl -$0.08 matches report totalPnl -$0.08. Change tomorrow: book the 2:45 exits from /orders closed fills, not the day file's last price.
- 2026-10-27 (close): /bankroll $24.88 -> $24.92 (day +$0.04, total -$0.08), 2 trades 2W/0L by closed-order fills (SPY 771.014 +0.43R +$0.017, QQQ 722.704 +0.81R +$0.024), paperDay 5, report 13 trades 7W/6L avg +0.054R, maxDrawdown 0.12 (25.00 -> 24.88 open today); journal-2026-10-27.md, key rule: flag a second index ETF over half the first's risk. Change tomorrow: record each trade's target distance in % next to SPY's day range so 'flattened under 1R' (6 trades in 3 days) has a number.
- 2026-10-28 (08:48 first scan): /bankroll $24.90 (pnl -$0.10) vs Oct 27 close $24.92: -$0.02 overnight drift for the 2nd time this week with no trades between (Oct 26->27 also -$0.02). Change today: ledger keeps equityOpen beside yesterday's close so the drift sum is checkable at the close run.
- 2026-10-28 (close): SPY +0.02R (771.196 -> 771.242), XLF -0.07R (56.118 -> 56.102), day $0.00, total -$0.10 over 6 paper days, 15 trades 8W/7L. Best R before exit: SPY 0.89R, XLF 0.69R; stops never moved, both gave back the whole move into the 2:45 flat. Change tomorrow: log best R and exit R side by side for every trade so the give-back is a number in the report.
- 2026-10-28 (close): /bankroll $24.90 -> $24.90 (day $0.00, total -$0.10), 2 trades 1W/1L by closed fills (SPY 771.242 +0.02R, XLF 56.102 -0.07R), paperDay 6, report 15 trades 8W/7L avg +0.043R; journal-2026-10-28.md, key rule: count trades that reach +0.7R and close under +0.1R (2 of 2 today). Change tomorrow: book the overnight drift ($24.90 close vs next open) as its own ledger line.
- 2026-10-29 (09:03 first scan): open $24.88 (/bankroll) vs Oct 28 close $24.90: -$0.02 overnight drift for the 3rd night in a row with no trades between, total drift -$0.06 this week. Change today: at the close run read /orders?status=closed for Oct 28 fills vs report trades to locate the $0.02 per night.
- 2026-10-29 (14:44 last scan): equity $24.88 open -> $24.89, day +$0.01, record now 18 trades 9W/9L, total -$0.11. Bars read again returned only SPY (78-bar limit is shared and eaten by premarket bars). Change tomorrow: request bars with start=today 08:30 CT so the limit covers market hours and the open position gets bars.
- 2026-10-29 (close): /bankroll $24.88 -> $24.89 (day +$0.01, total -$0.11), 4 trades 2W/2L by closed fills (XLY -1.02R, WMT +0.96R, XLI -1.00R, KO +2.06R), paperDay 7, report 19 trades 10W/9L avg +0.087R, maxDrawdown $0.18 (24.82 at 12:43); journal-2026-10-29.md, key rule: every trade that reaches +1R exits at +0.9R or better (today 2 of 2). Change tomorrow: compare Oct 29 close $24.89 with Oct 30 open to see if the -$0.02 drift repeats a 4th night.
- 2026-10-30 (09:28 first scan): bankroll $24.87 vs report $24.89 at yesterday's close (-$0.02 overnight with 0 positions), so totalPnl is -0.13, not -0.11. Change: on the close run, reconcile report.equity against /bankroll after flatten and log any gap in notes.
- 2026-10-30 (14:42 last scan): equity $24.88, day +$0.01, totalPnl -0.12 (equity minus 25), report now 22 trades 12W/10L (PFE +0.02R counted a win). Change tomorrow: count trades under +0.1R as scratches, not wins, so the win rate stops flattering breakeven exits.
- 2026-10-30 (close): /bankroll $24.87 -> $24.88, day +$0.01 (WMT +0.63R, KO -1.02R, PFE +0.05R by closed fills), paperDay 8, report 22 trades 12W/10L avg +0.06R, total -$0.12; journal-2026-10-30.md, key finding: the 2 trades that reached +1R gave back 1.00R on average. Change Monday: compare Oct 30 close $24.88 with Nov 2 open; a 5th -$0.02 night means asking the gateway for /account/activities to find it.
- 2026-11-02 (live go): keep paper and live ledgers apart by the day file's mode field (paper days end when Grayson flips the variable; live days say mode live, profile live-aggressive). Live equityOpen comes from /bankroll real equity, never the $25 bankroll constant. Atlas research on the real record: factory/trading/atlas/factory_import.py --mode live --out data/factory-live-trades.csv, then python3 -m atlas_trading analyze ... --capital 25 --stress-bps 10 (paper needs --drop-overlaps: two positions at once). Tomorrow: the first live close journal carries the account hint and mode in its header, and peak R next to exit R per trade from /orders?status=closed fills. Predict: the journal header says mode live.
