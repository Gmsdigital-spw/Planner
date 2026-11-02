# Live-aggressive profile: past-day replay (Nov 2, 2026)

Full numbers: `live-aggressive-2026-11-02.json`. Data: Yahoo Finance 5-minute bars, regular hours, the last 60
trading days (Aug 7 to Oct 31, 2026), plus 2 years of daily bars. Not the Alpaca IEX feed the bot trades on, so
fills and spreads differ a little. Strategy code: `factory/trading/backtest.simulate`, the autopilot's exact setups
and exits. No parameter search was run; seven fixed variants were replayed once each. Past days only: a strategy
that lost on past days can win tomorrow and the other way round. The account can lose money. Not financial advice.

| Variant | Trades | Win % | Avg R | Profit factor | Net on $25 | Max drawdown | Worst day | Best day | Last-third net |
|---|---|---|---|---|---|---|---|---|---|
| Paper rules on SPY/QQQ (control; like the nightly lab) | 101 | 26.7 | -0.18 | 0.17 | -$1.42 | $1.42 | -$0.08 | +$0.07 | -$0.56 |
| Paper rules on the 3x universe | 208 | 30.8 | -0.14 | 0.55 | -$3.35 | $3.59 | -$0.30 | +$0.43 | -$0.62 |
| **Live-aggressive, pullback entry** (all-in, 1 position, 6 entries, $5 daily loss, $5 floor, 3R) | 116 | 23.3 | -0.26 | 0.34 | **-$8.95** | $9.12 | -$0.84 | +$0.43 | -$3.07 |
| Live-aggressive on the core 4 (TQQQ SQQQ SOXL SOXS) | 103 | 27.2 | -0.20 | 0.40 | -$8.00 | $8.61 | -$0.72 | +$0.62 | +$0.16 |
| Live-aggressive, 2R target | 119 | 23.5 | -0.24 | 0.35 | -$8.95 | $9.15 | -$0.84 | +$0.43 | -$2.98 |
| **Live-aggressive, ORB entry** (the shipped profile) | 72 | 29.2 | -0.07 | **0.81** | **-$2.37** | $3.49 | -$1.14 | **+$1.87** | -$3.22 |
| Live-aggressive, half size (50% of cash) | 116 | 23.3 | -0.26 | 0.35 | -$4.94 | $5.05 | -$0.45 | +$0.26 | -$1.57 |

What this says, plainly:
- Every variant lost money on these 60 days. The bot's entries have had no edge on past days; the nightly lab has
  said the same since Oct 20 (holdout net negative on every run).
- Going all-in on 3x ETFs makes the swings bigger in both directions. The pullback entry all-in lost $8.95 of $25;
  the ORB entry lost $2.37 with the biggest single days (+$1.87, -$1.14). That is why the shipped live profile uses
  ORB: it is the least-bad variant AND the one with the big days Grayson asked for. It was picked on the same 60
  days it was tested on, so treat it as a hypothesis, not a proven setting.
- "Big profits" on $25 means dollars, not hundreds: the best day in any variant was +$1.87. Compounding only helps
  if the expectancy turns positive first.

Atlas breakout/ATR hypothesis on DAILY bars (multi-day holds, $10 fixed size, 2 years): TQQQ 0 trades, SOXL 1
trade -$1.29, SPXL 3 trades -$0.19, TNA 3 trades -$0.05, NVDL 5 trades -$0.61. Too few trades to say anything; the
live profile does not hold overnight, so this is background only.

Next honest steps (the lab can do them nightly; add `"profile": "live-aggressive"` to a lab job):
1. Replay the live profile on fresh holdout days on the IEX feed every night; adopt nothing that is not positive on
   two different holdouts with 20+ trades.
2. Journal every live day (Vault) with peak R and exit R per trade; the Oct 29-30 giveback finding applies.
3. If the live account loses $5 in a day the bot stops for the day; at $5 equity it stops for good until Grayson
   resets it. Those are entry halts after the fact, not guaranteed loss limits.
