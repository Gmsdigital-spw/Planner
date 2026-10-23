# Trading Floor tests (added Oct 23, 2026)

Offline checks a run can execute without keys, network or orders; they write only under `tests/out/`.
- `test_trail_stop.py`: a fake Alpaca replays the Oct 22, 2026 XLF trail scenario through `autopilot.run()`
  (7 scenarios: trail, target, refused stop, stop filled during the cancel, unconfirmed cancel, partial fill,
  transport error). Every sell must carry the whole position qty, never `"0"`.
- `test_backtest_profit_factor.py`: profit factor = gross profit / gross loss, `None` when no trade lost,
  and gross profit minus gross loss equals net P/L (synthetic fixture bars, never results).
Run both before any change to autopilot.py or backtest.py: `python3 factory/trading/tests/test_trail_stop.py &&
python3 factory/trading/tests/test_backtest_profit_factor.py`.
