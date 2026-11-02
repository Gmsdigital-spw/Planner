# Claude Code — integrate Atlas Trading Lab into my Factory

I am Grayson. My existing trading agents have about two weeks of learning/paper results. I want to study higher-upside trades and eventually run a $20 initial / $50 maximum real-money experiment. I use my phone. Treat this attachment as actual source code and a working starter; integrate it with my repository rather than responding only with advice or another specification.

## Preserve my existing Factory

1. Inspect the real project and its AGENTS.md instructions first. Back up the existing code and persistent trading state. Present the backup path. Make a focused branch if the repository supports it.
2. The earlier `gm_factory_v7.py` is a build brief, not the actual trading backend. Do not pretend it supplies my current strategy, trade history, API integration or results. Locate those in the real project. Keep Etsy, YouTube, marketing, Mechanic, other businesses and unrelated UI intact.
3. Preserve credentials, schedules, existing records and the $20 protected floor. The new request permits preparing a live-trading capability, but does not authorize placing orders, depositing money or changing unrelated settings during this build. Do not silently enable live execution.
4. A $20 balance with a protected $20 floor must be blocked from new risk. Explain that exact conflict in the finished interface. Do not remove the floor, invent funds, raise the budget, or tell me to deposit more just to make a test pass.
5. No new paid API, account, market-data subscription or LLM call is needed by this starter. Use my existing integrations. Do not hide missing data with fake numbers.

## Implement the attached code

The source is Python for research/risk/execution, SQL/SQLite for persistent records, and HTML/CSS/JavaScript for the mobile trading desk. Use the parts that fit my stack and preserve their contracts. Do not replace the deterministic risk checks with an LLM opinion.

- Run the offline tests and demo first. A synthetic example balance is not trading evidence.
- Inspect my actual broker, account type, data entitlements, strategy source, agent messages, order lifecycle and logs. Alpaca Trading API is the assumed adapter; if my real setup differs, write and contract-test a compatible adapter with the same safety behavior.
- Wire Scout to timestamped market data and stored snapshots. Wire the strategy agent to fixed, versioned hypotheses. Wire the risk/execution agent to `Engine.preview()` and paper execution. Wire Ledger to the SQLite records and genuine broker fills.
- Reuse my agents' learning files as evidence references and hypotheses. Do not claim that saving notes updated model weights, or that an agent's 95/100 score means a 95% chance of a winning trade.
- Import actual trades with strategy version, UTC timestamps, side, entry/exit fill prices, quantity, fees, order ID and data provenance. Preserve failed and rejected trades. Keep paper, backtest and live histories separate.
- The included breakout/ATR strategy is an aggressive research baseline, not a validated edge. You may compare my existing strategy against it using untouched chronological test data. Do not optimize repeatedly against the final test period, promise profits or force trades.
- For each candidate, show gross dollars exposed, assumed target gain, adverse-move scenario, all costs and full-notional downside. A large upside target must not raise position size by itself. Risk limits and the capital cap do not expand after wins.

## Execution requirements

- Default to demo/paper. Keep the live adapter off during implementation. After paper integration, leave a concrete configuration and one-order review flow that I can inspect.
- Keep paper/live API keys and databases separate. Pin the actual account ID. Use one persistent local database and one executor for the dedicated account; do not mix other bots/manual trading into it.
- Never use margin buying power as cash, trade shorts/options, average down, double stakes after a loss, or recycle unsettled sale proceeds. Do not bypass a broker restriction or change account settings to avoid rejection.
- Require an exact reviewed strategy version for a new live buy. Do not approve a strategy because it passed the starter's research filter. The report explicitly leaves live approval false.
- Live settled-fund input must come from the user's broker-confirmed start-of-day amount, not an agent estimate. If the actual broker has an authoritative field/integration, implement and verify it; otherwise preserve the explicit operator input. Never call `cash` or `buying_power` settled cash.
- Keep fixed dollar caps, one position, quote freshness/spread checks, regular-session checks, durable duplicate protection and read-before-retry reconciliation. Record partial fills, canceled partial fills, rejections and unknown outcomes.
- An unknown submission outcome must not generate another POST. Reconcile the original client ID. A new proposal ID must not defeat the daily limits or unknown-order gate.
- The loss thresholds halt new entries when observed; they do not guarantee a dollar loss limit or close positions. Do not label them guaranteed stops.
- Valid risk-reducing exits must remain possible after an entry halt, subject to actual broker/session/open-order constraints. Never imply that a local halt canceled or liquidated anything.
- Unattended live trading is not supplied here. The prior Factory relied on a GitHub scheduler with potentially long delays. Do not use it as live trade protection. Do not claim an ATR stop in the backtest is a broker stop on a live fractional order. Validate actual supported protection and monitoring separately before adding any unattended live path.

## UI integration

Build the attached visual design into my existing authenticated Trading tab. Keep it usable at 375px. Show real equity, cash, open exposure, saved-data age, paper/live mode, order status, strategy version, unknown values, unverified lessons and out-of-sample evidence. Keep research scores separate from broker P&L. Never show a demo curve as real results. Keep secrets server-side. The supplied local HTTP server is read-only and is not an internet deployment server.

## Finish with evidence

Run the included tests plus meaningful tests of the real integration. Test a timeout after broker acceptance, a timeout before the result is known, duplicate proposals, stale/wide quotes, partial fills, a preserved-floor refusal, a closing order after a pause, settlement checks and account/environment mismatch. Complete paper-only broker contract tests; do not place a live test order. Check the UI at 375px and desktop sizes, report any unavailable verification, and distinguish infrastructure tests from strategy profitability.

Then give me a short handoff: what changed, what you actually verified, the dashboard link or run command, the exact money-rule values, and any real blocker. Leave live execution disabled. Do the implementation now instead of just describing how I could build it.
