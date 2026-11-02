from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from atlas_trading import breakout, research
from atlas_trading.models import Refused


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "trades.csv"
        at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.rows = []
        for i, split in enumerate(("train", "validation", "test", "test", "test")):
            entry = at + timedelta(days=i)
            self.rows.append(dict(zip(research.TRADE_COLUMNS, [str(i),"v1",entry.isoformat(),(entry+timedelta(hours=1)).isoformat(),"100","101",".02","0",split])))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self):
        with self.path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=research.TRADE_COLUMNS)
            writer.writeheader(); writer.writerows(self.rows)

    def test_a_few_wins_are_not_a_passing_research_sample(self):
        self.write()
        report = research.analyze(self.path)
        self.assertFalse(report["research_checks_passed"])
        self.assertFalse(report["live_approved"])
        self.assertIn("Fewer than 100 completed test trades", report["failures"])

    def test_costs_can_turn_gross_wins_into_net_losses(self):
        for row in self.rows:
            row["exit_price"] = "100.01"
        self.write()
        report = research.analyze(self.path, stress_bps="10")
        self.assertLess(float(report["splits"]["test"]["net_pnl_usd"]), 0)

    def test_duplicate_ids_nonfinite_and_overlap_are_rejected(self):
        original = [dict(r) for r in self.rows]
        for kind in ("duplicate", "nan", "overlap"):
            self.rows = [dict(r) for r in original]
            if kind == "duplicate": self.rows[1]["trade_id"] = self.rows[0]["trade_id"]
            if kind == "nan": self.rows[0]["qty"] = "NaN"
            if kind == "overlap": self.rows[0]["exit_time"] = self.rows[2]["exit_time"]
            self.write()
            with self.subTest(kind=kind), self.assertRaises(Refused):
                research.analyze(self.path)

    def test_test_data_cannot_precede_training(self):
        self.rows[0]["split"], self.rows[2]["split"] = "test", "train"
        self.write()
        with self.assertRaises(Refused): research.analyze(self.path)

    def test_mixed_strategy_versions_are_refused(self):
        self.rows[-1]["strategy_version"] = "v2"
        self.write()
        with self.assertRaises(Refused): research.analyze(self.path)

    def test_notional_cannot_exceed_starting_capital(self):
        self.rows[0]["qty"] = "1"
        self.write()
        with self.assertRaises(Refused): research.analyze(self.path, capital="20")

    def test_future_strategy_freeze_does_not_approve_holdout(self):
        self.write()
        report = research.analyze(self.path, frozen_at="2027-01-01T00:00:00Z")
        self.assertIn("Strategy freeze did not precede the test period", report["failures"])

    def test_empty_test_metrics_are_unknown_not_zero_profit(self):
        self.rows = self.rows[:2]
        self.write()
        report = research.analyze(self.path)
        self.assertIsNone(report["splits"]["test"]["net_pnl_usd"])
        self.assertIsNone(report["splits"]["test"]["win_rate"])

    def test_bootstrap_is_reproducible_and_labeled_exploratory(self):
        at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for i in range(5,15):
            row = dict(self.rows[-1]); row.update(trade_id=str(i), entry_time=(at+timedelta(days=i)).isoformat(),exit_time=(at+timedelta(days=i,hours=1)).isoformat())
            self.rows.append(row)
        self.write()
        a = research.analyze(self.path); b = research.analyze(self.path)
        self.assertEqual(a["splits"]["test"]["expectancy_interval_usd"], b["splits"]["test"]["expectancy_interval_usd"])
        self.assertTrue(any("exploratory" in x for x in a["limits"]))


class BreakoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "bars.csv"
        at = datetime(2026, 1, 1, 14, 30, tzinfo=timezone.utc)
        self.rows = []
        for i in range(160):
            # Daily bars with explicit 6.5-hour duration in the test; synthetic dates.
            self.rows.append({"timestamp":(at+timedelta(days=i)).isoformat(), "open":"100", "high":"101", "low":"99", "close":"100", "volume":"1000"})
        self.rows[55].update(open="104",high="106",low="104",close="105",volume="3000")
        self.rows[56].update(open="105",high="120",low="80",close="100")
        with self.path.open("w",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=self.rows[0].keys());writer.writeheader();writer.writerows(self.rows)

    def tearDown(self): self.tmp.cleanup()

    def test_signal_cannot_read_future_bars(self):
        bars=breakout.read_bars(self.path)
        self.assertEqual(breakout.setup(bars,55),breakout.setup(bars[:56],55))

    def test_next_bar_entry_costs_and_stop_first_on_ambiguous_bar(self):
        out=Path(self.tmp.name)/"out.csv"
        result=breakout.backtest(self.path,out,bar_seconds=23400)
        self.assertEqual(result["completed_trades"],1)
        trades=research.read_trades(out)
        self.assertEqual(trades[0].entry_time, self.rows[56]["timestamp"])
        self.assertGreater(float(trades[0].entry_price),105)
        self.assertLess(trades[0].exit_price,trades[0].entry_price)

    def test_bar_duration_cannot_overlap_next_bar(self):
        with self.assertRaises(Refused):
            breakout.backtest(self.path,Path(self.tmp.name)/"out.csv",bar_seconds=86401)


if __name__ == "__main__": unittest.main()
