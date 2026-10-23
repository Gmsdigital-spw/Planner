# Trading notebook (paper money; not financial advice)

## Grayson's rules
- 2026-10-21: Day trading is lane two; make it smoother and keep improving the bot. Paper until Grayson says "live go".

## What works (proven by numbers)
- 2026-10-21: The default pullback setup loses on unseen past days — evidence: holdout 30 trades / 20% wins / -$1.06 and 25 trades / 44% wins / -$0.30 (past days only). Held: 2 times.
- 2026-10-22: A slower trend filter (SMA 30, 4-bar pullback) loses less but still loses — evidence: -$0.22 vs -$0.30 and -$0.32 vs -$0.54 (past days only). Held: 2 times.

## Testing (not proven yet)
- Opening-range breakout and VWAP reclaim setups in the nightly lab. Prove: positive holdout net on 2 different holdout sets with 20+ trades each.

## What doesn't work (tried, failed, or Grayson rejected)
- (none yet)
