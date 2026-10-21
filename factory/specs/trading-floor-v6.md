# Trading Floor V6 spec — Alpaca day trading, paper first

_Standing instructions written with Grayson on Oct 20, 2026. Not financial advice: even with every rule here the account can lose the $25. The floor is built and gated; nothing trades until the key tap and a separate "paper go", and nothing trades real money until a separate "live go" with its own key._

## The money rules (enforced twice: in the gateway code `gw/run.py` op `alpaca`, and in the run prompt)
| Rule | Value |
|---|---|
| Deposit | $25 (paper money for the first 2 trading days) |
| Hard floor | $20: equity at or below the floor = every new buy is refused by the gateway, open positions are closed, the floor stays locked until Grayson resets it |
| Max total loss | $5, by construction (deposit − floor) |
| Risk per trade | 2% of equity ($0.50 on $25) |
| Stop-loss | on every buy, placed with the entry as a bracket order; a buy without one is refused |
| Take-profit | at least 2:1 reward-to-risk or the trade is skipped |
| Position size | risk ÷ (entry − stop) in notional dollars (fractional shares); max 40% of cash in one name; max 2 open positions |
| Hours | buys 9:35 AM to 2:45 PM Central only; everything flat by 2:45 PM; no overnight holds; day orders only |
| Daily loss limit | $1.50 (6% of $25): hit it and Bear closes the day |
| No margin | cash only; buying power = cash; never short, never options, never crypto |
| Paper → live | 2 paper trading days (Grayson shortened it from 14 on Oct 20, 2026) with the report below, then Grayson's separate "live go"; live uses a different key and the ALPACA_LIVE variable set to 1 by Grayson himself |

## The crew
- **Bull** — finds long setups in liquid large-cap names and ETFs only (price above $5, average volume high, tight spread): trend on the 5-minute chart + a pullback to a level, entry on the first green bar, stop under the pullback low, target at 2R. Writes each idea as a TradePlan: symbol, entry, stop, target, R:R, size, one-sentence reason, confidence (decision → number → next action).
- **Bear** — the risk officer. Checks every plan against the rules table before any order; owns the floor, the daily loss limit, the 2:45 PM flatten; the only one allowed to lock or (never without Grayson) unlock the floor. Bear's "no" ends the discussion.
- **Vault** — the ledger: every order, fill, fee, slippage, equity curve, drawdown; writes modules/trading/ledger/<day> and the running 14-day paper report (win rate, average R, max drawdown, biggest loss, rule breaches = must be 0).
- **Tape** — the morning read in plain English: what the market did yesterday, what is on the calendar today (earnings, Fed, CPI), what the crew will and will not touch. Uses the glossary words and explains each one the first time it appears in a day.

## Glossary (the words every agent uses correctly)
stocks, equities, ETF, portfolio, equity (account value), cash balance, buying power, bullish, bearish, trend, pullback, support, resistance, volatility, liquidity, spread, slippage, entry, market order, limit order, stop-loss, take-profit, bracket order, trailing stop, risk-to-reward (R:R), position sizing, max exposure, drawdown, daily loss limit, fractional shares, day trade, PDT rule (under $25k: at most 3 day trades in 5 business days on a margin account; this account is cash-only, so settlement rules apply instead), compounding, reinvestment, paper trading, fill, partial fill, flat.

## Data and orders (through the free GitHub gateway, never Make)
- Op: `{"op":"alpaca","method":"GET","path":"/account"}`, `/positions`, `/orders?status=open`, `/clock`; data reads `{"op":"alpaca","data":true,"path":"/stocks/<SYM>/bars?timeframe=5Min&limit=60"}`; a buy `{"op":"alpaca","method":"POST","path":"/orders","body":{"symbol":"SPY","notional":"9.50","side":"buy","type":"limit","limit_price":"...","time_in_force":"day","order_class":"bracket","stop_loss":{"stop_price":"..."},"take_profit":{"limit_price":"..."}}}`; flatten `{"op":"alpaca","method":"DELETE","path":"/positions"}`.
- Secrets Grayson adds in GitHub (repo Settings → Secrets → Actions): `ALPACA_KEY_ID`, `ALPACA_SECRET_KEY` (PAPER keys). Variables: `ALPACA_FLOOR` (default 20), `ALPACA_LIVE` (default empty = paper).

## The paper report (2 trading days) (Vault, in the app under the Trading Floor)
Per day: trades, wins, losses, net P/L, max drawdown, rule breaches. Totals: win rate, average R, expectancy, worst day, best day, breaches (must be 0 to be allowed to ask for live). The report never predicts; it describes.

## The Trading run (prompt saved here; created as a scheduled task only after "paper go")
Schedule: weekdays 9:25 AM Central (one run; a second run at 2:30 PM Central only to flatten and write the ledger). Prompt summary: read this spec and factory/skills/{bull,bear,vault,tape}/SKILL.md; read modules/trading/settings/main ({paused, paperDay, floorLocked}); if paused or floorLocked, write the ledger line and stop; Tape writes the read; Bull proposes at most 2 plans; Bear checks each against the table (any failure = skipped, logged with the rule); orders go through the gateway as bracket orders in notional dollars; Vault records fills and equity; at 2:30 PM flatten everything, write modules/trading/ledger/<day> and the running report, append one line to fleet/commander/audit/<day> (who "Bear", mod "trading"); message Grayson at most 3 lines only when a rule tripped, the floor locked, or the 2 paper days are done. Never add money, never change the floor, never switch to live, never trade outside the hours, never touch any other floor's collections.
