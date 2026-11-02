# Verification record

Prepared November 1, 2026 (America/Chicago).

## Passed

- `python3 -m unittest discover -s tests -q`: **50 tests passed** under Python 3.12.
- Python compilation of all application modules.
- JavaScript syntax check: `node --check web/app.js`.
- Offline synthetic lifecycle: preview, one buy, duplicate suppression, full long exit and persistent equity/audit records.
- The preserved $20 floor blocks a $20 account. Dollar exposure, available cash, fixed sizing, daily count, loss halts, invalid/stale/wide quotes and session restrictions have failure-case coverage.
- Timeout after acceptance reconciles the same client ID without a second POST. Unknown results block new risk. A known pre-POST staleness refusal is recorded as `not_submitted`, rather than inventing an uncertain fill.
- Canceled partial fills remain in the record and broker-reported exposure prevents a new entry. Entry halts do not themselves prevent an eligible long exit.
- Account/environment pinning, separate paper/live keys, live-disable/acknowledgment checks, strategy approval checks, manual settled-fund checks, and the prohibition on recycling the day's sale proceeds.
- CSV research rejects duplicate IDs, overlapping trades, nonfinite data, mixed strategy versions, chronology violations and impossible initial notional. Small winning samples fail the research filters. Cost stress can turn gross wins into net losses.
- Backtest signal uses completed history only, enters the next bar, charges adverse costs and resolves same-bar target/stop ambiguity against the strategy.
- Local HTTP smoke checks: HTML, CSS, JavaScript and saved-state JSON return HTTP 200 with content-security headers. An untrusted Host returns 403, unsupported write requests return 501, and a path traversal request returns 404.

## Not established

- No user brokerage account or credentials were used. No real or Alpaca paper orders were placed. REST mapping tests use synthetic fixtures, not authenticated contract tests.
- No actual agent trading logs or OHLCV dataset were supplied. The package has **no measured investment return and no validated strategy edge**. Synthetic fills are infrastructure checks only.
- No existing live Factory repository was modified. The earlier Factory file was read as context; this is a separate integration package.
- Browser rendering was unavailable in the execution environment. The responsive CSS is included, but desktop/mobile visual layout and accessibility need browser verification in the real integration. JavaScript syntax and HTTP resources were checked.
- Unattended live execution, broker-native protective stops, continuous monitoring, failover, transfer-adjusted equity accounting, settlement-data authentication and internet deployment hardening are not implemented.
- Local locks coordinate only a single persistent database on a POSIX local filesystem. They cannot coordinate independent executors or recover from intentionally deleted history.

Passing software tests does not establish trading profitability or guarantee a dollar loss limit. Live mode is disabled in the delivered configuration.
