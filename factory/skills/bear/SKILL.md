---
name: bear
floor: trading
role: Risk
judged_on: max drawdown
updated: 2026-10-20
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
- Looks like a top seller's work, not a template. Warm, real, clear.
- One thing measurably better than last run.

## What I've learned (append-only, newest last)
- 2026-10-21: Gates passed at $25.00 equity, 0 positions; vetoed 0 orders because Bull sent none (no-trade day 1). Tomorrow: check the earnings-after-close list (TSLA/META/IBM/LRCX today) before Bull's bars job, not after.
- 2026-10-21 (close): 14:32 CT close run could not push the cancel+flatten job (blocked by the session's safety check); SPY+QQQ left to the autopilot's 14:45 flatten. Tomorrow: the 14:30 run reads autopilot state first and treats autopilot.py as the flatten owner; the run only verifies /positions is empty after 14:45.
- 2026-10-21 (close, 14:43): autopilot loop healthy all afternoon (166 runs, last 14:41); QQQ stop filled at -1R, equity $24.97, floor far away. Tomorrow: count combined open risk across correlated index ETFs (SPY+QQQ) as one bet when checking the daily loss limit.
- 2026-10-21 (lab): adoptable = none; best-on-tune (ORB + BE 0.7R, trail 1.2/0.8) went +$0.07 tune -> -$0.52 holdout with drawdown 0.81 vs 0.49 baseline, a tune-only win. Tomorrow: keep params empty and judge any ORB variant only on a fresh holdout; readyForLive stays no until holdout net > 0 with 20+ trades.
- 2026-10-22: Gates passed at 08:46 CT: heartbeat 08:42 (4 min old), no last-error file, 0 positions, $24.96 equity, $4.96 above floor. Tomorrow: compare the day file's runs count between scans to confirm the loop is advancing, not just a fresh heartbeat.
- 2026-10-22 (close): loop advanced 7 -> 361 runs, no last-error; both winners exited via 'trail refused (422) -> no stop found -> market sell' (XLF 11:30, WMT 14:36), so the trail path failed 2 of 2 times today. Tomorrow: count 422 trail refusals per day in the gate note and flag Grayson if any position sits without a stop for more than 1 cycle.
- 2026-10-22 (lab): adoptable = {pullback_orh, sma_len 30, pullback_bars 4} (holdout -$0.32 vs baseline -$0.54, DD 0.32 vs 0.54) but the previous lab marked nothing adoptable, so params stay empty; it is still a net loser on past days. Tomorrow: adopt only if the next fresh holdout marks the same three overrides adoptable, and keep readyForLive no while holdout net is below $0.
