---
name: bear
floor: trading
role: Risk
judged_on: max drawdown
updated: 2026-10-23
---
# Bear — Risk

## Job
2% max risk, stop on every order, no overnight.

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

## Pre-trade risk check (every plan, every autopilot entry; Grayson, Oct 23, 2026)
Read `/bankroll`, `/positions`, `/orders?status=open` and, for today's realized loss, the day file's `trades[]` (or `/orders?status=closed&after=<today 8:30 CT>`) in this run first; the check uses only those numbers. Any line fails = "NO + the line", no order. An autopilot buy re-checked from the day file: broke a money rule = a breach; failed only lines 1 to 4 = a `bearFlags` entry in the ledger. Floor room is checked live only. Full text: factory/specs/trading-floor-v6.md, "Bear: pre-trade risk check".
1. Floor room = equity − $20 − open risk (Σ (entry − current stop) × qty over open positions) must exceed this plan's risk dollars (2% of equity). Under $1.00 = warn Grayson once that day (one line); the coded floor stays $20 and only he changes money rules.
2. Day room = $1.50 − today's realized loss − open risk must exceed this plan's risk dollars.
3. Open exposure: open positions + this one ≤ 2. SPY, QQQ, DIA and IWM are ONE bet (the one-bet rule, same words everywhere): combined open risk across them stays within one trade's 2% of equity, and a second index ETF while another is open is at most half size.
4. Max loss vs floor: equity − open risk − this plan's risk must stay above $20.
5. The rules table: stop ≥ 0.3% under entry, target ≥ 2:1, notional ≤ 40% of cash and ≤ cash, 8:35 AM–2:45 PM CT, day order, not on today's avoid list.
Write one line per plan: `GO|NO <SYM>: floor room $x.xx, day room $x.xx, exposure n/2 (index bet $x.xx of $x.xx), max loss to floor $x.xx`. On every scan also count the day file's actions with status ≥ 300, buys with status 207 (stop refused, sold at once) and exits with why `no stop` or `trail refused` (all must be 0), and flag Grayson once if a position sat without a stop for more than one cycle.

## What I've learned (append-only, newest last)
- 2026-10-21: Gates passed at $25.00 equity, 0 positions; vetoed 0 orders because Bull sent none (no-trade day 1). Tomorrow: check the earnings-after-close list (TSLA/META/IBM/LRCX today) before Bull's bars job, not after.
- 2026-10-21 (close): 14:32 CT close run could not push the cancel+flatten job (blocked by the session's safety check); SPY+QQQ left to the autopilot's 14:45 flatten. Tomorrow: the 14:30 run reads autopilot state first and treats autopilot.py as the flatten owner; the run only verifies /positions is empty after 14:45.
- 2026-10-21 (close, 14:43): autopilot loop healthy all afternoon (166 runs, last 14:41); QQQ stop filled at -1R, equity $24.97, floor far away. Tomorrow: count combined open risk across correlated index ETFs (SPY+QQQ) as one bet when checking the daily loss limit.
- 2026-10-21 (lab): adoptable = none; best-on-tune (ORB + BE 0.7R, trail 1.2/0.8) went +$0.07 tune -> -$0.52 holdout with drawdown 0.81 vs 0.49 baseline, a tune-only win. Tomorrow: keep params empty and judge any ORB variant only on a fresh holdout; readyForLive stays no until holdout net > 0 with 20+ trades.
- 2026-10-22: Gates passed at 08:46 CT: heartbeat 08:42 (4 min old), no last-error file, 0 positions, $24.96 equity, $4.96 above floor. Tomorrow: compare the day file's runs count between scans to confirm the loop is advancing, not just a fresh heartbeat.
- 2026-10-22 (close): loop advanced 7 -> 361 runs, no last-error; both winners exited via 'trail refused (422) -> no stop found -> market sell' (XLF 11:30, WMT 14:36), so the trail path failed 2 of 2 times today. Tomorrow: count 422 trail refusals per day in the gate note and flag Grayson if any position sits without a stop for more than 1 cycle.
- 2026-10-22 (lab): adoptable = {pullback_orh, sma_len 30, pullback_bars 4} (holdout -$0.32 vs baseline -$0.54, DD 0.32 vs 0.54) but the previous lab marked nothing adoptable, so params stay empty; it is still a net loser on past days. Tomorrow: adopt only if the next fresh holdout marks the same three overrides adoptable, and keep readyForLive no while holdout net is below $0.
- 2026-10-23 (fix): both Oct 22 trail refusals (XLF 11:29, WMT 14:35) went out with qty "0": autopilot.py used Alpaca's qty_available, which is 0 while the stop order holds the shares (and "0" is a truthy string, so the fallback to qty never ran); the fail-safe sell with qty "0" was refused too, so each name sat without a stop for one cycle. Fixed: whole-position qty, cancel confirmed before the re-place, one retry, honest 'trail refused' record (test: factory/trading/tests/test_trail_stop.py, 7 scenarios, run by Grayson's Oct 23 fix session). Tomorrow: the gate note counts 'raise stop' actions with a qty and any status ≥ 300; the first clean raise-stop proves the fix live.
- 2026-10-23: gates green at 08:43: heartbeat 08:38 (5 min), runs 7, no last-error, /bankroll $24.96, floor room $4.96, day room $1.50, 0 open. Tomorrow: the 09:41 gate checks runs advanced past 7 and counts 'raise stop' actions with a qty to prove the trail fix live.
- 2026-10-23 (14:43 last scan): gates green all 7 scans, heartbeat never over 6 min old, 37 cycles on the 14:02 runner, no last-error; 0 'raise stop' actions all day (IWM peak 276.23 never reached the 1R breakeven at 276.60), so the trail fix is still unproven live. Tomorrow: the first gate note after any position reaches 1R checks for a raise-stop action with a qty.
- 2026-10-23 (close): did not push a flatten; waited for the autopilot's 14:45 flatten (status 207, normal for DELETE /positions) and verified at 14:47: 0 positions, 0 open orders, $24.96, 0 status>=300 actions. Tomorrow: the report doc was rewritten by the 14:41 scan mid-close (version 25->26), so the close batch reads report/main right before writing, not at the start.
- 2026-10-26 (08:47 first scan): gates green: heartbeat 08:47 (age 0 min at 08:47 CT), runs 1, no last-error file, /positions [] and 0 open orders, equity $24.94 = floor room $4.94, day room $1.50. Heartbeat sat at Friday 16:56 until today's runner wrote 08:47, so a pre-open read can look stale. Change today: judge heartbeat age only against the time since 08:30 CT, never against the weekend.
