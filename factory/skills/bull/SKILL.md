---
name: bull
floor: trading
role: Signals
judged_on: win rate (paper)
updated: 2026-10-20
---
# Bull — Signals

## Job
Momentum/mean-reversion entries, market hours only.

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
- 2026-10-21: Scan at 8:43 CT had only 3 five-minute bars; 6 of 7 names were under VWAP or the 20-bar average, AAPL had no pullback. Tomorrow: fetch bars with start=prior day + sort=desc (default returns today only) and skip names until 4+ bars after the open.
- 2026-10-21 (close): autopilot opened SPY $9.98 and QQQ $5.99 at 10:54; QQQ stopped at -1R (722.61) after a midday +1.4% run faded to +1.1%, SPY sat +0.1R into the close. Tomorrow: size the second same-direction index entry at half, since SPY and QQQ move together and doubled the risk.
- 2026-10-21 (lab): on 10 unseen past days the pullback setup made 25 trades, 44% wins, avg +0.09R, -$0.30 (all 8 tweaks also lost on holdout); the new ORB setup won tune +$0.07 but lost holdout -$0.52. Tomorrow: test ORB with a 30-minute range and a stop at the range low, plus pullback entries only when the name is above its opening-range high.
- 2026-10-22: Tape tells the autopilot to watch WMT/KO/XLV/XLF, which stayed green (+0.5% to +1.3%) while SMH fell 3.7% and QQQ 1.8%; 08:42 scan found no A+ setup in 6 names. Tomorrow: check whether the autopilot's 'watch' list actually picked up the full watchlist (day file showed only 6 names at 08:42).
- 2026-10-22 (close): 4 entries, 2 wins (XLF +1.37R, WMT +1.62R), 2 stops (XLV, DIA -1R), net +$0.02; both winners were defensive names that stayed green all day while index ETFs lost. Tomorrow: on a risk-off morning rank defensive leaders (green vs a red SPY) ahead of index ETFs on the watchlist.
- 2026-10-22 (lab): on 10 new unseen past days the default pullback made 28 trades, 14% wins, -0.29R, -$0.54; pullback only above the 15-min opening-range high with a 30-bar average cut it to 25 trades, 40% wins, -0.08R, -$0.32 (adoptable once), and 30-min ORB with a range-low stop lost least (-$0.19) but on only 16 trades. Tomorrow: retest pullback_orh+SMA30/4 on a fresh holdout and add 30-min ORB variants across 14+ names so it reaches 20 trades.
