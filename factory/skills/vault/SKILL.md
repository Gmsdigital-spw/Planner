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
