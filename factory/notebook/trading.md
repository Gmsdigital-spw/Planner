# Trading notebook (paper money; not financial advice)

## Grayson's rules
- 2026-10-21: Day trading is lane two; make it smoother and keep improving the bot. Paper until Grayson says "live go".
- 2026-11-02: Live go. "Make my trading all with real money, big risky trades, start with $20-25." Real money runs on the live-aggressive profile (all-in one position, 3x ETFs, $5 floor, $5 daily loss) once Grayson sets the ALPACA_LIVE variable himself. The crew never places a live buy, never sets the variable, never edits a profile; the autopilot does the trading.

## What works (proven by numbers)
- 2026-10-21: The default pullback setup loses on unseen past days — evidence: holdout 30 trades / 20% wins / -$1.06 and 25 trades / 44% wins / -$0.30 (past days only). Held: 2 times.
- 2026-10-22: A slower trend filter (SMA 30, 4-bar pullback) loses less but still loses — evidence: -$0.22 vs -$0.30 and -$0.32 vs -$0.54 (past days only). Held: 2 times.

## Testing (not proven yet)
- Opening-range breakout and VWAP reclaim setups in the nightly lab. Prove: positive holdout net on 2 different holdout sets with 20+ trades each.

## What doesn't work (tried, failed, or Grayson rejected)
- 2026-11-02: On the last 60 past days (Yahoo 5-minute bars) no variant of the bot's strategy was positive: paper rules on SPY/QQQ -$1.42 (101 trades), all-in 3x pullback -$8.95 (116 trades, PF 0.34), all-in 3x ORB -$2.37 (72 trades, PF 0.81, best day +$1.87). Evidence: factory/trading/lab/live-aggressive-2026-11-02.md. Past days only.
