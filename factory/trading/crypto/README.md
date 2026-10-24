# Crypto paper bot (virtual money only)
- Trades BTC, ETH, SOL, DOGE, AVAX on paper with a pretend $25. It never places a real order, on any account.
- Real prices come from Alpaca's free crypto data; fills are faked in state.json with a 0.25% fee each way plus half the spread.
- Every 5 minutes, 24/7 (GitHub Action "Crypto paper bot"). It only buys when the confidence score is 75 or more.
- Up to half the pretend money per trade, 2 at a time. Stop 1.5 ATR, half off at +2R, trail 2 ATR, out after 24h.
- If pretend money falls to $15 it sells everything and stops (floorLocked). Restart: set floorLocked false in state.json.
- heartbeat.json = is it alive; state.json = balance, open trades, closed-trade history; last-error.json = last problem.
- Knobs: params.json. Lab: `python3 backtest.py --first-test` (results in lab/first-test.json). Test: tests/test_agree.py.
- Separate from the stock bot: different files, different workflow, never touches its Alpaca account.
