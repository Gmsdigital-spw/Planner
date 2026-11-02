# Trading Floor tests (added Oct 23, 2026)

Offline checks a run can execute without keys, network or orders; they write only under `tests/out/`.
- `test_trail_stop.py`: a fake Alpaca replays the Oct 22, 2026 XLF trail scenario through `autopilot.run()`
  (7 scenarios: trail, target, refused stop, stop filled during the cancel, unconfirmed cancel, partial fill,
  transport error). Every sell must carry the whole position qty, never `"0"`.
- `test_backtest_profit_factor.py`: profit factor = gross profit / gross loss, `None` when no trade lost,
  and gross profit minus gross loss equals net P/L (synthetic fixture bars, never results).
- `test_live_mode.py` (Nov 2, 2026): the live-aggressive profile through `autopilot.run()` with a fake live Alpaca
  (20 scenarios: all-in ORB entry with a client_order_id and the read-before-POST lookup, the duplicate guard, a
  lookup that fails (no blind POST), the $5 floor, an unfunded account (waits, never locks), the $5 daily loss, a
  flatten Alpaca did NOT complete (the day stays open and retries until /positions is empty), an early-close day
  (flat 15 minutes before next_close), a position carried past the close, a mode switch during the day (the paper
  record is archived), a stop that filled between cycles (Alpaca's fill time in the journal), a gateway 207 (stop
  refused, sold at once), a broken live profile (the bot stops), a non-numeric floor variable, a non-fractionable
  name, the crew's avoid list, one position at a time, paper mode unchanged).
- `test_gateway_rules.py` (Nov 2, 2026): `gw/run.py` money rules with a fake `requests` in paper and live mode (live
  needs its own key pair; live buys only with ALPACA_LIVE_BUYS; the pinned-account refusal on every order, by account
  number or id; the blocked-account and broken-profile refusals on buys; the floor, size cap and hours from each
  profile; the ALPACA_FLOOR / ALPACA_LIVE_FLOOR overrides, a non-numeric one ignored; GET /account in live mode is
  the hint view; scrub hides account_number).
Run all four before any change to autopilot.py, backtest.py, gw/run.py or a profile (the Action "Trading tests"
runs them on every code push; the bot's own state commits do not trigger it): `for t in test_trail_stop
test_live_mode test_gateway_rules test_backtest_profit_factor; do python3 factory/trading/tests/$t.py || break; done`.
The Atlas suite: `cd factory/trading/atlas && python3 -m unittest discover -s tests -q` (50 tests).
