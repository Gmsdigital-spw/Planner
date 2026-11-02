# Atlas Trading Lab

A Python trading-review module with an HTML/CSS/JavaScript dashboard and a SQLite audit trail. It can test an aggressive breakout hypothesis, analyze your agents' completed trades, and send a bounded order to Alpaca when deliberately configured. It does not turn stored knowledge, a high agent score, or a few paper wins into a proven edge.

**Start here:** give Claude Code `CLAUDE_START_HERE.md` and this folder. On a phone, the separate `Atlas_Trading_Claude_Paste.txt` contains the prompt and every source file in one document.

## Run the offline version

Requires Python 3.11+ on Linux/macOS. No pip installs, subscription, LLM calls, or broker credentials are needed. Run from this folder:

```bash
python3 -m unittest discover -s tests -q
python3 -m atlas_trading demo
python3 -m atlas_trading serve
```

Open `http://127.0.0.1:8765`. The demo starts with a clearly labeled **synthetic $50 balance**, performs a $2 example round trip, and prevents a duplicate order. It is an execution example, not a historical return. The configured experiment allocation is $20; that differs from the made-up account's $50 equity. Stop the server before `demo --reset`.

The dashboard reads saved records. Refreshing the page does not contact a broker or place an order. Unknown values stay unknown. Its local server must not be exposed publicly; add proper authentication and deployment hardening before integrating it into an online dashboard. On an iPhone, have Claude integrate the UI into your authenticated Factory dashboard or use a hosted development environment; the Python server does not run inside an ordinary iPhone browser.

## What is included

| File/module | What it does |
| --- | --- |
| `breakout.py` | Fixed research hypothesis: 20-bar breakout, volume filter, 50-bar trend filter, 14-bar ATR, two-ATR stop/four-ATR target in the backtest |
| `research.py` | Chronological trade checks, fees and extra execution costs, expectancy, profit factor, completed-trade drawdown and exploratory bootstrap interval |
| `risk.py` | Dollar caps, cash checks, quote/session checks, entry halts, symbol and strategy gates |
| `engine.py` | One-shot orders, durable client IDs, duplicate prevention, timeout reconciliation and partial-fill records |
| `broker.py` | Fixed Alpaca paper/live REST endpoints, isolated keys, no automatic order POST retries |
| `schema.sql` / `store.py` | Persistent order, equity, hypothesis and audit records |
| `web/` | Responsive, read-only HTML/CSS/JavaScript trading desk |
| `tests/` | Offline tests for failure cases and research integrity |

The breakout strategy is an **untested hypothesis**, not a recommendation to buy an example ticker. Its backtest stop and target are simulation rules. They are not attached to live broker orders.

## Defaults for your $20–$50 experiment

| Setting | Default | Meaning |
| --- | --- | --- |
| Capital cap | $20; absolute supported ceiling $50 | Maximum configured allocation/exposure; no automatic size growth after wins |
| Protected equity floor | $20 | Preserves the existing GM Factory rule |
| Order size | At most $2 | Gross notional of a new fractional-share buy |
| Open positions | One | No averaging down or stacking positions |
| Exposure ceiling | $5 | Additional ceiling; one $2 order is more restrictive with these defaults |
| Scenario loss budget | $0.20 | A calculation using the assumed adverse move and costs; **not** a guaranteed loss limit |
| Daily equity loss threshold | $1 | Latches a pause on new entries when observed |
| Experiment equity loss threshold | $3 from initial recorded equity | Latches a pause on new entries when observed |
| New entries | At most one per trading date | Failed submission attempts count conservatively; confirmed pre-POST refusals do not |
| Live execution | Disabled | Requires explicit configuration and CLI acknowledgment |

**A $20 account and a $20 protected floor leave no room for a new trade.** The default correctly blocks it. A $50 account with that floor has headroom, but order sizing remains capped. Do not have an agent silently remove the existing floor. A separate experiment's policy can be deliberately reviewed in configuration; editing a file does not make a strategy profitable.

Gain scenarios are arithmetic: 20% of a $20 position is $4 before costs; a 50% loss is $10. This package starts with much smaller positions. A target price is not a probability or a forecast. These limits do not make it sensible to use rent, bill or house savings.

## Research with your real records

Do not manufacture a history from an agent's claimed win rate. Export actual completed paper trades for one fixed strategy version:

```csv
trade_id,strategy_version,entry_time,exit_time,entry_price,exit_price,qty,fees_usd,split
paper-001,strategy-sha256-here,2026-08-03T14:00:00Z,2026-08-03T14:20:00Z,100,101,0.02,0,train
paper-002,strategy-sha256-here,2026-09-01T14:00:00Z,2026-09-01T14:20:00Z,100,99,0.02,0,validation
paper-003,strategy-sha256-here,2026-10-01T14:00:00Z,2026-10-01T14:20:00Z,100,101,0.02,0,test
```

These rows only illustrate the schema. They are not trading evidence. Use actual fills, correct quantities and all fees, with timezone-aware timestamps. Trades must not overlap because this starter supports one position. Train, validation and test periods must be chronological, with no cross-boundary positions. Keep the final test period untouched during development. Record a genuine pre-test strategy freeze; a timestamp in a command cannot authenticate that history.

```bash
python3 -m atlas_trading analyze your-trades.csv --capital 20 --stress-bps 10 --frozen-at 2026-09-30T00:00:00Z
```

`--stress-bps 10` deducts an extra 0.10% of notional at each side, in addition to reported fees and the recorded fill prices. Real fill prices may already include spread/slippage, so this is an explicit additional stress test. Choose and disclose your assumption before viewing the result. The default report is saved to `data/research-report.json`, where the demo dashboard reads it. For another database folder, write the report alongside that database.

Research filters require 100 completed test trades, 30 active test days, positive test net profit, profit factor at least 1.20, completed-trade test drawdown no more than 10% of supplied capital, and a positive lower exploratory expectancy bound. These are engineering filters, not statistical proof or a live-trading recommendation. The report always leaves `live_approved` false. It cannot authenticate the data, eliminate overfitting, correct repeated holdout reuse, or measure intratrade drawdown from closed-trade records alone.

### Test the aggressive example

Provide completed, consistent OHLCV bars for one symbol. `timestamp` is the **open** of each bar:

```csv
timestamp,open,high,low,close,volume
2026-09-01T13:30:00Z,100,101,99,100.5,1000
```

At least 100 actual bars are required. This one-row sample only shows the format. For one-minute bars:

```bash
python3 -m atlas_trading backtest your-bars.csv --bar-seconds 60 --capital 20 --notional 2 --cost-bps 10
python3 -m atlas_trading analyze data/backtest-trades.csv --capital 20 --stress-bps 10
```

Declare the real bar duration; for regular-session daily stock bars, use the appropriate session duration and handle shortened sessions in preprocessing. Do not feed incomplete candles. The backtest enters at the next bar's open, applies adverse execution costs, uses the stop first if target and stop both occur within one bar, fills a gap below the stop at the worse opening price, and limits holding time to ten bars. It splits by bar chronology 60/20/20 and closes trades at split boundaries. Prices, corporate actions, survivorship and data provenance must be checked independently. The extra analysis stress is additional to the backtest's costs.

This hypothesis may generate no trades or lose money. The code does not optimize parameters against the test period, force daily trades, or turn a target into an expected return.

## Connect Alpaca paper trading

Use a **dedicated account and one persistent database per account/environment**. Do not have another bot or manual trading process use that same account concurrently. The local lock only coordinates processes using the same database. Do not delete/reset its history, use a network filesystem, or reuse the demo database for paper/live trading.

Copy `config.example.json` to `config.paper.json` and explicitly set:

```json
{
  "mode": "paper",
  "database": "data/atlas-paper.sqlite3",
  "expected_account_id": "YOUR_PAPER_ACCOUNT_ID"
}
```

Edit those three values inside the complete copied configuration, rather than replacing the rest of it with this excerpt. Keep the $20 floor and other limits unless you deliberately review a change. Paper account funds should reflect the small experiment you are testing.

Set `ALPACA_PAPER_KEY_ID` and `ALPACA_PAPER_SECRET_KEY` in the server's environment/secret manager. `.env.example` is a reference; the application does not auto-load `.env`. Do not paste credentials into chat, source code, proposals or the browser. Create a fresh proposal from an actual strategy signal:

```bash
python3 -m atlas_trading ticket --symbol SPY --strategy-version YOUR_FROZEN_VERSION --notional 2 --adverse-move 0.05 --target-move 0.10 --rationale "Replace with the actual signal and invalidation reason" --evidence "Replace with actual trade/data references" --out data/proposal.json
python3 -m atlas_trading --config config.paper.json preview data/proposal.json
python3 -m atlas_trading --config config.paper.json execute data/proposal.json
```

`SPY` and `QQQ` are example allowlist symbols, not trade recommendations. IEX is the free single-exchange feed and is not a consolidated NBBO feed. The spread gate reflects the selected feed only. SIP availability depends on your Alpaca data entitlement; the application does not buy a subscription or silently switch feeds.

Orders use simple fractional **market/day** semantics, not leverage, shorts, options or extended-hours orders. This intentionally uses the conservative combination documented in the order API reference, rather than relying on conflicting descriptions of newer fractional limit-order support. Market fill prices can move and regulatory fees may add costs. The broker remains authoritative for account, session, buying-power, intraday and settlement restrictions. A broker rejection is recorded and never bypassed.

## Live execution is an explicit, one-order workflow

The source includes a live adapter, but no live account was connected or tested while creating this package. The offline tests exercise fake broker responses. Complete Alpaca paper contract checks with your own account before considering the live path.

Use a separate `config.live.json`, separate database, live account ID, and `ALPACA_LIVE_KEY_ID` / `ALPACA_LIVE_SECRET_KEY`. New live buys need `live_enabled: true` and the exact strategy version listed in `approved_strategy_versions`. Source-hash your reviewed strategy. Agent-reported scores cannot approve it. `live_enabled` must also be true for live exits.

Live entries additionally require a broker-confirmed **start-of-day settled-cash amount**, entered by the operator. The API adapter does not claim that `cash` or `buying_power` proves settlement. Every reserved buy notional is subtracted from this daily amount; intraday sale proceeds are not recycled. A self-reported number is not verified settlement data, and does not bypass any broker rule. Do not let an agent invent or inflate it.

After creating and previewing a fresh live proposal, the one-order command is:

```bash
python3 -m atlas_trading --config config.live.json execute data/proposal.json --settled-cash-usd YOUR_CONFIRMED_START_OF_DAY_AMOUNT --live-ack I_ACCEPT_MARKET_RISK
```

This is a syntax example, not an instruction to enable it now. No real order is sent merely by reading or installing this package. Proposals expire within 120 seconds. Execution rechecks broker state; it does not trust an old preview.

### Exits, pauses and unknown outcomes

To request a close of the broker-reported long quantity, make a **new** sell ticket and use the correct account configuration:

```bash
python3 -m atlas_trading ticket --symbol SPY --side sell --strategy-version YOUR_FROZEN_VERSION --out data/exit.json
python3 -m atlas_trading --config config.paper.json preview data/exit.json
python3 -m atlas_trading --config config.paper.json execute data/exit.json
```

Live exits still require live configuration and the explicit acknowledgment. Entry halts and the equity floor do not prevent a valid closing order, but closed markets, broker restrictions and unresolved/open orders can prevent execution. Never send a blind second exit while another order might be filling.

```bash
python3 -m atlas_trading --config config.paper.json halt --reason "Review trading results"
python3 -m atlas_trading --config config.paper.json reconcile
python3 -m atlas_trading --config config.paper.json resume --ack REVIEWED
```

`halt` only pauses future entries locally. It **does not cancel pending broker orders, close holdings, attach stops, or protect a position during an outage**. Loss thresholds are checked on previews/submissions, not by a background watcher. The $3/$1 thresholds are entry-halt triggers, not guaranteed maximum losses. Existing positions can lose their entire gross notional plus costs. In a timeout, the engine retains the client order ID and queries its status. If it cannot establish the result, it blocks new entries and never automatically repeats the POST. Resolve discrepancies in the broker before continuing; do not erase the database to get past a block.

**Unattended live trading is not implemented.** The old Factory's scheduler can be delayed by tens of minutes. Do not repurpose that scheduler as a stop-loss system. A production upgrade would need validated broker-native protection supported for the actual order type, reliable monitoring, recovery drills, account reconciliation and authenticated operations. This package does not claim those are present.

## Agent memory

```bash
python3 -m atlas_trading lesson --strategy-version YOUR_VERSION --hypothesis "What appears to work and under which conditions" --evidence "Actual trade IDs and data snapshot"
```

Lessons remain labeled `unverified`. Storing notes does not retrain model weights or prove that a rule generalizes. Research agents can propose new versions; execution should use only the fixed, reviewed version. Never rewrite old failed experiments or tune against the same test period indefinitely.

## Verification and references

See `VERIFICATION.md` for exactly what was and was not checked. Current official documentation reviewed on November 1, 2026:

- [Alpaca paper trading and simulation limitations](https://docs.alpaca.markets/us/docs/paper-trading)
- [Alpaca create-order parameters](https://docs.alpaca.markets/us/reference/postorder)
- [Alpaca stable client-order-ID lookup](https://docs.alpaca.markets/us/reference/getorderbyclientorderid)
- [Alpaca account status and funds fields](https://docs.alpaca.markets/us/reference/getaccount-1)
- [Alpaca market-data feeds and entitlements](https://docs.alpaca.markets/us/docs/market-data-faq)
- [Alpaca account/order protections](https://docs.alpaca.markets/us/docs/user-protection)
- [FINRA frequent-trading and settlement considerations](https://syndication.finra.org/content/frequent-intraday-trading-understanding-basics)

Broker features and rules can change. The code makes a small set of API assumptions that must be contract-tested in paper mode with your account.
