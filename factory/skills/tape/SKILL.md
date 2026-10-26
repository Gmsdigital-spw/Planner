---
name: tape
floor: trading
role: Reporting
judged_on: report accuracy
updated: 2026-10-23
---
# Tape — Reporting

## Job
Daily P&L, verified from Alpaca only.

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

## The read sets the bias and the avoid list, nothing else (Grayson, Oct 23, 2026)
- The morning read (WebSearch + one gateway snapshots job) decides two things only: the day's bias (bullish / bearish / choppy, with the SPY and QQQ numbers from the snapshots) and the avoid list (earnings today or after close, halts, gaps over 5% (threshold set Oct 23, 2026; the Oct 21 read excluded a −6% gap), the FOMC hour). Write them to `factory/trading/watchlist.json` = {"day": <Central day key>, "symbols": [...], "avoid": [...]} (the autopilot ignores a file whose `day` is not today, avoid list included) and ledger.tape.
- Never a price target, an entry, a stop or a level: no "SPY to 775", no "buy QQQ above 720". Levels come only from Bull's bars fetched that run.
- Own the clock: the daily plan checklist in factory/specs/trading-floor-v6.md (pre-market 8:00–8:30, open 8:30, first scan 8:41, hourly scans to 14:41, last entry 14:00, close run about 14:30 and finishing after the 14:45 flat, lab 00:25 UTC = 7:25 PM CDT, 6:25 PM CST from Nov 1) says what each run does and where its numbers come from; note the time of each item in the ledger.
- Refresh the read mid-day only when the mood clearly changed (SPY crossed its open the other way, or a calendar event hit), and say what changed with the numbers.

## What I've learned (append-only, newest last)
- 2026-10-21: SPY opened at its high (771.20) and slipped under VWAP; gap names (SMCI +12%, NFLX -6%, ISRG -7%) excluded. Tomorrow: add the 9:30 CT oil-inventory print to the calendar line and recheck XLE spread (0.015% today) as a candidate.
- 2026-10-21 (close): SPY +0.48% (772.80) at 14:43, off its 774.30 high; QQQ +1.13%, NVDA and XLK led all day. Tomorrow: note in the morning read when QQQ leads SPY by 2x or more, since today's QQQ gain gave back first.
- 2026-10-22: Earnings-after-close (META -6.8%, TSLA -1.1%) pulled QQQ -1.8% vs SPY -0.97% (QQQ fell ~2x SPY) and chips gapped hardest (AMD -5.2%); defensives led. Tomorrow: on a 2x-weak QQQ morning, list QQQ in the read as 'trend down, longs only on a clear reclaim of its open'.
- 2026-10-22 (close): SPY 762.04 -1.43%, QQQ -3.11% (2.2x SPY, weak to the close), MSFT -2.3%; KO +2.75%, WMT +2.58%, XLV +1.39% held gains all day. Tomorrow: check premarket whether QQQ's -3% extends or reverses before keeping defensives at the top of the list.
- 2026-10-23: open read SPY 760.28 -0.49%, QQQ -0.15% (QQQ stronger than SPY, reverse of Oct 22), DIA -1.00% with banks weakest (JPM -1.39%) and XLE +1.21% leading; 4 of 26 snapshot names showed IEX spreads over 1% (XOM 7%, TSLA 3.7%) and were left off. Tomorrow: filter the watchlist by spread under 0.1% from the snapshot before ranking by move.
- 2026-10-23 (14:43 last scan): SPY 760.15 -0.51%, within 0.3% of the 08:41 read all day; XLE +2.77% and KO -2.73% held their direction from open to close (energy in, staples out). Tomorrow: keep the day's leaders and laggards from this close on Monday's list only if the premarket confirms them.
- 2026-10-26 (08:47 first scan): open read SPY 762.87 +0.40%, QQQ +0.39%, IWM +0.35%, DIA +0.35% (all four within 0.05%, broad and calm vs Friday's split); NVDA +1.9%, BAC +1.7%, SMH +1.4% led, AAPL -1.7% and META -1.2% lagged; 4 of 26 snapshot names (TSLA, JPM, AMD, XOM) showed IEX spreads over 3%, avoided. Quiet calendar today, Fed Wednesday. Change today: refresh only if SPY falls back below its 762.70 first-bar close.
- 2026-10-26 (14:43 last scan): SPY 765.69 +0.77% at close vs +0.40% at 08:47, held +0.6 to +0.9% all day; QQQ +1.31%, XLK +1.96% led (tech in), IWM +0.50% lagged. Tomorrow: Fed decision is Wednesday, so note on Tuesday's read whether moves shrink ahead of it.
