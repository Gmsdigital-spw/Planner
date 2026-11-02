# Real money: the switch, the keys, the rules (Nov 2, 2026)

Grayson's go on Nov 2, 2026: "make my trading all with real money, big risky trades, start with $20-25." This page
is the whole runbook. Nothing trades real money until step 3 is done by Grayson himself; the crew never does it.

## What runs
The same all-day autopilot (`factory/trading/autopilot.py`, GitHub Action "Trading autopilot") that ran 8 clean
paper days, on the LIVE endpoint with its own key pair and the money rules in
`factory/trading/profiles/live-aggressive.json`:

| Rule | Live-aggressive | Paper (unchanged) |
|---|---|---|
| Position size | all-in: 100% of cash, one position at a time | 2% risk, 40% of cash, 2 positions |
| Names | 3x/2x ETFs: TQQQ SQQQ SOXL SOXS SPXL SPXS TNA TZA LABU LABD NVDL TSLL CONL (each checked daily for fractional trading at Alpaca; the crew's avoid list still applies) | the crew's daily watchlist |
| Entry | opening-range breakout (first 15 minutes), on completed 5-minute bars | pullback to the 20-bar average |
| Exit | stop under the range midpoint (at least 0.5% away), breakeven at 1R, trail 1R behind the high from 1.5R, target 3R, flat by 2:45 PM CT | same, target 2R |
| Entries a day | 6, never twice in a name that lost today | 4 |
| Hard floor | $5: equity at or below it = flatten and lock for the day (the gateway refuses every buy) | $20 |
| Daily loss | $5 down on the day = flatten, done for the day | $1.50 |
| Hours | buys 8:35 AM to 2:00 PM CT, flat at 2:45 PM, no overnight holds, day orders only | same |
| Duplicate protection | every buy carries a client_order_id and is looked up at Alpaca before the POST | same (added Nov 2) |
| Account pin | optional: ALPACA_LIVE_ACCOUNT_ID; any other account is refused for every order | n/a |

The floor and the daily loss are entry halts after the fact, not guaranteed loss limits: a 3x ETF can gap through a
stop, and a market sell fills where the market is. The account can lose all of it. Not financial advice.

Evidence: `factory/trading/lab/live-aggressive-2026-11-02.md`. On the last 60 trading days every variant of this
strategy lost money; the shipped ORB variant lost $2.37 of $25 with days of +$1.87 and -$1.14. There is no proven edge.

## Step 1: open and fund the live account
1. alpaca.markets, your existing login: open the LIVE brokerage account (individual), finish identity checks.
2. Deposit $20 to $25. No account minimum; with under $2,000 the account is 1x buying power (no margin), which is
   exactly what the bot assumes. Pattern-day-trader limits no longer exist (FINRA ended them June 4, 2026; Alpaca
   removed the counters July 6, 2026), so the bot may trade every day.
3. Make sure fractional trading is on for the account (Alpaca: account settings, "fractional trading"); the bot buys
   dollar amounts of 3x ETFs, which needs it.

## Step 2: live keys and variables in GitHub (repo Gmsdigital-spw/Planner, Settings, Secrets and variables, Actions)
Secrets (new, never the paper pair):
- `ALPACA_LIVE_KEY_ID` and `ALPACA_LIVE_SECRET_KEY`: generated on the LIVE account's API page, not the paper one.

Variables:
- `ALPACA_LIVE_ACCOUNT_ID` (recommended): the live account id. Alpaca shows it on the account page; the first live
  heartbeat (`factory/trading/auto/heartbeat.json`, field `accountId`) shows its last 4 characters so you can check.
- `ALPACA_LIVE_FLOOR` (optional): overrides the $5 floor. Leave it empty to use the profile.
- `ALPACA_FLOOR` and `ALPACA_BANKROLL` stay what they are: they only ever touch paper mode.

## Step 3: the switch
Set the repo variable `ALPACA_LIVE` to `1`. That is the only switch. Empty or `0` = paper, exactly as before.
From the next runner start (every 10 minutes 8:00 AM to 3:00 PM CT on weekdays, or run "Trading autopilot" by hand
from the Actions tab), the heartbeat shows `"mode": "live"`, `"profile": "live-aggressive"` and the Factory page's
Trading tab shows the red "Real money" pill, the money rules card and the account hint.

To stop: set `ALPACA_LIVE` to `0` (next runner is paper again), or set `"paused": true` in
`factory/trading/auto/control.json`, or disable the workflow. None of these closes an open position by itself: the
bot flattens at 2:45 PM CT; outside that, close it in the Alpaca app.

## What to watch on the phone
- Trading tab: equity, today's P/L, open trade with entry/stop/target, the feed, "Bot last checked" (late = red).
- `factory/trading/auto/<day>.json`: every action with its status code; `last-error.json` if anything broke.
- Vault's nightly journal: `factory/skills/vault/journal-<day>.md`.

## Crew rules in live mode
- The crew reads the real account through the gateway (`/bankroll` now returns `mode: live`, real equity and cash,
  the account hint, `tradingBlocked`). Numbers only; the crew never places a live buy. The close run may still verify
  `/positions` is empty after 2:45 PM and flatten only if the autopilot failed to.
- Nobody changes `profiles/live-aggressive.json`, the floor, the keys or the variable except Grayson. The safety
  guard still blocks any crew shell command that tries to set ALPACA_LIVE.
- Atlas research on the real record: from `factory/trading/atlas`, `python3 factory_import.py --mode live --out
  data/factory-live-trades.csv` then `python3 -m atlas_trading analyze data/factory-live-trades.csv --capital 25
  --stress-bps 10`. The report's `live_approved` is always false by design; it grades, it never approves.
