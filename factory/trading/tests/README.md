# Trading Floor tests (added Oct 23, 2026)

Offline checks a run can execute without keys, network or orders; they write only under `tests/out/`.
- `test_trail_stop.py`: a fake Alpaca replays the Oct 22, 2026 XLF trail scenario through `autopilot.run()`
  (7 scenarios: trail, target, refused stop, stop filled during the cancel, unconfirmed cancel, partial fill,
  transport error). Every sell must carry the whole position qty, never `"0"`.
- `test_backtest_profit_factor.py`: profit factor = gross profit / gross loss, `None` when no trade lost,
  and gross profit minus gross loss equals net P/L (synthetic fixture bars, never results).
- `test_live_mode.py` (Nov 2, 2026): the live-aggressive profile through `autopilot.run()` with a fake live Alpaca
  (8 scenarios: all-in ORB entry with a client_order_id and the read-before-POST lookup, the duplicate guard, the $5
  floor, the $5 daily loss, a non-fractionable name dropped, the crew's avoid list, one position at a time, paper
  mode unchanged).
- `test_gateway_rules.py` (Nov 2, 2026): `gw/run.py` money rules with a fake `requests` in paper and live mode (live
  needs its own key pair, the pinned-account refusal on every order, the blocked-account refusal on buys, the floor,
  size cap and hours from each profile, the ALPACA_FLOOR / ALPACA_LIVE_FLOOR overrides).
Run all four before any change to autopilot.py, backtest.py, gw/run.py or a profile (the Action "Trading tests"
runs them on every push): `for t in test_trail_stop test_live_mode test_gateway_rules test_backtest_profit_factor;
do python3 factory/trading/tests/$t.py || break; done`. The Atlas suite: `cd factory/trading/atlas && python3 -m
unittest discover -s tests -q` (50 tests).
