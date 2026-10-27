---
name: bull
floor: trading
role: Signals
judged_on: win rate (paper)
updated: 2026-10-23
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
- No number without data: every number names the source read this run (gateway result, day file, heartbeat, lab file or the database record). Missing = "unknown (source: ...)", never a guess.
- Looks like a top seller's work, not a template. Warm, real, clear.
- One thing measurably better than last run.

## Chart analysis: only from bars fetched this run (Grayson, Oct 23, 2026)
- Every level (VWAP, 20-bar average, pullback low, opening-range high and low, entry, stop, target) is computed from 5-minute bars fetched through the gateway in this run (`/stocks/bars?symbols=...&timeframe=5Min&feed=iex`, start = today's 8:30 CT open) plus the latest trade (`/stocks/<SYM>/trades/latest?feed=iex`). Name the bar time each level came from.
- Fewer than 4 completed bars since the open, or a failed bars job = `no data: <reason>`, no plan. A 20-bar average exists only once 20 completed bars exist today (10:10 CT); before that it is `unknown (source: bars)` and no pullback plan is possible (the autopilot's own setup fires from the 22nd bar, about 10:20). Never yesterday's bars, a remembered level, a round number, or a level from the news or Tape's read (this supersedes the Oct 21 line below about start = prior day).
- A TradePlan lists: symbol, bars used (count, first and last bar time), entry, stop (which bar's low it sits under), target, R:R, size, one-sentence reason, confidence. Decision → number → next action.
- SPY, QQQ, DIA and IWM are one bet (the one-bet rule, same words everywhere): combined open risk across them stays within one trade's 2% of equity, and a second index ETF while another is open is at most half size, and only if Bear's pre-trade check says GO.
- On the scans, review each autopilot entry against this rule with bars fetched this run (was the setup on that bar?) and say so in one line with the bar time.

## What I've learned (append-only, newest last)
- 2026-10-21: Scan at 8:43 CT had only 3 five-minute bars; 6 of 7 names were under VWAP or the 20-bar average, AAPL had no pullback. Tomorrow: fetch bars with start=prior day + sort=desc (default returns today only) and skip names until 4+ bars after the open.
- 2026-10-21 (close): autopilot opened SPY $9.98 and QQQ $5.99 at 10:54; QQQ stopped at -1R (722.61) after a midday +1.4% run faded to +1.1%, SPY sat +0.1R into the close. Tomorrow: size the second same-direction index entry at half, since SPY and QQQ move together and doubled the risk.
- 2026-10-21 (lab): on 10 unseen past days the pullback setup made 25 trades, 44% wins, avg +0.09R, -$0.30 (all 8 tweaks also lost on holdout); the new ORB setup won tune +$0.07 but lost holdout -$0.52. Tomorrow: test ORB with a 30-minute range and a stop at the range low, plus pullback entries only when the name is above its opening-range high.
- 2026-10-22: Tape tells the autopilot to watch WMT/KO/XLV/XLF, which stayed green (+0.5% to +1.3%) while SMH fell 3.7% and QQQ 1.8%; 08:42 scan found no A+ setup in 6 names. Tomorrow: check whether the autopilot's 'watch' list actually picked up the full watchlist (day file showed only 6 names at 08:42).
- 2026-10-22 (close): 4 entries, 2 wins (XLF +1.37R, WMT +1.62R), 2 stops (XLV, DIA -1R), net +$0.02; both winners were defensive names that stayed green all day while index ETFs lost. Tomorrow: on a risk-off morning rank defensive leaders (green vs a red SPY) ahead of index ETFs on the watchlist.
- 2026-10-22 (lab): on 10 new unseen past days the default pullback made 28 trades, 14% wins, -0.29R, -$0.54; pullback only above the 15-min opening-range high with a 30-bar average cut it to 25 trades, 40% wins, -0.08R, -$0.32 (adoptable once), and 30-min ORB with a range-low stop lost least (-$0.19) but on only 16 trades. Tomorrow: retest pullback_orh+SMA30/4 on a fresh holdout and add 30-min ORB variants across 14+ names so it reaches 20 trades.
- 2026-10-23: 08:41 SPY had 3 five-minute bars (last one still forming); no plan possible before the 20-bar average exists (~10:10 CT), and the day file's watch was still the 6 default names. Tomorrow: confirm at the 09:41 scan that the autopilot's watch list switched to Tape's 14 names.
- 2026-10-26 (08:47 first scan): SPY had 4 five-minute bars from 08:30 (762.70 -> 762.37); no plan possible before the 20-bar average (~10:10 CT). The autopilot's day file still scanned only its 6 default names at 08:47, so the 15-name watchlist lands on its next cycle. Change today: on the 09:4x scan, check the day file's watch list matches watchlist.json before reviewing any entry.
- 2026-10-26 (14:43 last scan): 3 entries, 1 win: IWM -1R stopped 12:41, XLE +0.35R and SPY -0.15R both flattened at 2:45 under target; SPY bought 12:55 had under 2 hours to reach its 2R target (771.68, +0.7%) and got -0.15R. Tomorrow: flag in the ledger any entry after 12:30 whose target needs more than SPY's typical afternoon range.
- 2026-10-27 (close): autopilot's SPY and QQQ both entered on the 10:20 bar (3rd day running on that bar) and topped at +0.44R and +0.81R, flattened at 2:45 (SPY +0.43R, QQQ +0.81R); their 2R targets needed +0.80% and +0.99% vs SPY's 0.77% whole-day range. Change tomorrow: on each scan write the open trade's target distance in % next to SPY's range so far.
