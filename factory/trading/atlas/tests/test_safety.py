from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from atlas_trading.broker import AlpacaBroker, BrokerError, BrokerRejected, DemoBroker
from atlas_trading.cli import demo
from atlas_trading.dashboard import state
from atlas_trading.engine import Engine, LIVE_ACK
from atlas_trading.models import Position, Proposal, Refused, Settings, now_utc, number
from atlas_trading.risk import assess
from atlas_trading.store import Store


def proposal(id="p1", side="buy", **kwargs):
    at = now_utc() - timedelta(seconds=1)
    return Proposal(id, "SPY", side, "frozen-v1", at.isoformat(), (at + timedelta(seconds=120)).isoformat(),
                    notional_usd="2" if side == "buy" else "0", rationale="Recorded hypothesis", evidence_ref="logs/trades-1-200.csv", **kwargs)


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(mode="paper", database=self.tmp.name + "/state.sqlite3", expected_account_id="SYNTHETIC-DEMO")
        self.store = Store(self.settings.database)
        self.broker = DemoBroker()
        self.snapshot = self.broker.snapshot("SPY")
        self.day = self.store.capture(self.snapshot, self.settings)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def check_plan(self, snapshot=None, p=None, settings=None, settled=None):
        return assess(settings or self.settings, p or proposal(), snapshot or self.snapshot, self.store, self.day, settled)

    def test_valid_small_order_has_explicit_gain_loss_and_full_capital_at_risk(self):
        plan = self.check_plan()
        self.assertTrue(plan.allowed)
        self.assertEqual(plan.scenario_gain_usd, "0.1956")
        self.assertEqual(plan.scenario_loss_usd, "0.1044")
        self.assertEqual(plan.maximum_position_loss_usd, "2")

    def test_preserved_floor_blocks_a_twenty_dollar_account(self):
        plan = self.check_plan(replace(self.snapshot, equity=number("20"), cash=number("20")))
        self.assertFalse(plan.allowed)
        self.assertTrue(any("floor" in reason for reason in plan.reasons))

    def test_entire_notional_must_fit_above_protected_floor(self):
        self.assertFalse(self.check_plan(replace(self.snapshot, equity=number("21"))).allowed)

    def test_cannot_use_margin_buying_power_instead_of_cash(self):
        self.assertFalse(self.check_plan(replace(self.snapshot, cash=number("1"), buying_power=number("1000"))).allowed)

    def test_fixed_order_cap_rejects_large_trade(self):
        p = replace(proposal(), notional_usd="20")
        self.assertFalse(self.check_plan(p=p).allowed)

    def test_stale_future_crossed_wide_and_zero_quotes_fail(self):
        snapshots = [replace(self.snapshot, quote_at=self.snapshot.fetched_at - timedelta(seconds=30)),
                     replace(self.snapshot, quote_at=self.snapshot.fetched_at + timedelta(seconds=30)),
                     replace(self.snapshot, bid=number("102"), ask=number("100")),
                     replace(self.snapshot, bid=number("99"), ask=number("101")),
                     replace(self.snapshot, bid=number("0"))]
        for snapshot in snapshots:
            with self.subTest(snapshot=snapshot):
                self.assertFalse(self.check_plan(snapshot).allowed)

    def test_closed_market_and_slow_snapshot_fail(self):
        for snapshot in (replace(self.snapshot, market_open=False), replace(self.snapshot, duration_seconds=20), replace(self.snapshot, next_close=self.snapshot.fetched_at + timedelta(seconds=30))):
            self.assertFalse(self.check_plan(snapshot).allowed)

    def test_open_orders_and_existing_positions_block_new_entries(self):
        for snapshot in (replace(self.snapshot, open_orders=({"status":"new"},)), replace(self.snapshot, positions=(Position("SPY", number(".02"), number("2")),))):
            self.assertFalse(self.check_plan(snapshot).allowed)

    def test_daily_breach_latches_even_after_equity_recovers(self):
        self.assertFalse(self.check_plan(replace(self.snapshot, equity=number("48.5"))).allowed)
        self.assertIn("Daily", self.store.get("halt_reason"))
        self.assertFalse(self.check_plan().allowed)

    def test_total_breach_is_persisted(self):
        self.check_plan(replace(self.snapshot, equity=number("46")))
        self.assertIn("Experiment", self.store.get("halt_reason"))

    def test_pause_floor_and_wide_spread_do_not_block_a_long_exit(self):
        self.store.halt("review")
        snapshot = replace(self.snapshot, equity=number("19"), positions=(Position("SPY", number("0.02"), number("1.90")),), quote_at=None, bid=None, ask=None)
        plan = self.check_plan(snapshot, p=proposal(side="sell"))
        self.assertTrue(plan.allowed, plan.reasons)
        self.assertEqual(plan.quantity, "0.02")

    def test_exit_cannot_short_an_absent_position(self):
        self.assertFalse(self.check_plan(p=proposal(side="sell")).allowed)

    def test_huge_target_is_not_treated_as_confidence(self):
        low_target = self.check_plan(p=replace(proposal(), target_move_pct="0.10"))
        high_target = self.check_plan(p=replace(proposal(), target_move_pct="1"))
        self.assertEqual(low_target.amount_usd, high_target.amount_usd)
        self.assertEqual(low_target.maximum_position_loss_usd, high_target.maximum_position_loss_usd)

    def test_non_finite_and_booleans_are_rejected(self):
        for value in ("NaN", "Infinity", True, None):
            with self.subTest(value=value), self.assertRaises(Refused):
                number(value)

    def test_expired_and_naive_proposals_are_rejected(self):
        p = proposal()
        with self.assertRaises(Refused):
            self.check_plan(p=replace(p, expires_at=(now_utc()-timedelta(seconds=1)).isoformat()))
        with self.assertRaises(Refused):
            self.check_plan(p=replace(p, created_at="2026-01-01T12:00:00"))

    def test_non_cent_order_is_rejected(self):
        with self.assertRaises(Refused):
            self.check_plan(p=replace(proposal(), notional_usd="1.999"))

    def test_absolute_fifty_dollar_ceiling(self):
        with self.assertRaises(Refused):
            replace(self.settings, capital_cap_usd=number("51")).validate()

    def test_stored_identity_prevents_cross_account_or_mode_reconciliation(self):
        for settings in (replace(self.settings, mode="live"), replace(self.settings, expected_account_id="different")):
            with self.assertRaises(Refused):
                Engine(settings, self.store, self.broker)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(mode="paper", database=self.tmp.name + "/state.sqlite3", expected_account_id="SYNTHETIC-DEMO")
        self.store = Store(self.settings.database)
        self.broker = DemoBroker()
        self.engine = Engine(self.settings, self.store, self.broker)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_repeated_identical_proposal_submits_once(self):
        p = proposal()
        self.assertEqual(self.engine.execute(p)["status"], "filled")
        self.assertTrue(self.engine.execute(p)["duplicate_prevented"])
        self.assertEqual(self.broker.post_count, 1)

    def test_changed_intent_with_same_id_is_refused(self):
        p = proposal()
        self.engine.execute(p)
        with self.assertRaises(Refused):
            self.engine.execute(replace(p, notional_usd="1"))
        self.assertEqual(self.broker.post_count, 1)

    def test_timeout_after_acceptance_reconciles_without_second_post(self):
        original_submit = self.broker.submit
        def delayed(payload):
            original_submit(payload)
            raise BrokerError("timeout")
        self.broker.submit = delayed
        p = proposal()
        with self.assertRaises(Refused):
            self.engine.execute(p)
        self.assertEqual(self.store.order(p.proposal_id)["status"], "unknown")
        result = self.engine.execute(p)
        self.assertEqual(result["status"], "filled")
        self.assertEqual(self.broker.post_count, 1)

    def test_unknown_outcome_never_blindly_retries_or_opens_new_risk(self):
        calls = []
        def unavailable(payload):
            calls.append(payload)
            raise BrokerError("timeout before result")
        self.broker.submit = unavailable
        p = proposal()
        with self.assertRaises(Refused):
            self.engine.execute(p)
        self.assertTrue(self.engine.execute(p)["duplicate_prevented"])
        with self.assertRaises(Refused):
            self.engine.execute(proposal("different"))
        self.assertEqual(len(calls), 1)

    def test_known_rejection_is_recorded_without_automatic_retry(self):
        def rejected(payload):
            raise BrokerRejected("HTTP 403")
        self.broker.submit = rejected
        p = proposal()
        with self.assertRaises(Refused):
            self.engine.execute(p)
        self.assertEqual(self.store.order(p.proposal_id)["status"], "rejected")
        self.assertTrue(self.engine.execute(p)["duplicate_prevented"])

    def test_pre_post_staleness_is_not_misreported_as_an_unknown_fill(self):
        p = proposal()
        with patch("atlas_trading.engine.now_utc", return_value=now_utc()+timedelta(seconds=15)):
            with self.assertRaises(Refused):
                self.engine.execute(p)
        self.assertEqual(self.broker.post_count, 0)
        self.assertEqual(self.store.order(p.proposal_id)["status"], "not_submitted")
        self.assertFalse(self.store.unresolved())
        self.assertEqual(self.engine.execute(proposal("fresh"))["status"], "filled")

    def test_partial_fill_canceled_order_keeps_exposure_visible(self):
        original_submit = self.broker.submit
        def partial(payload):
            raw = original_submit(payload)
            self.broker.positions = (Position("SPY", number(".01"), number("1")),)
            raw.update(status="canceled", filled_qty=".01")
            return raw
        self.broker.submit = partial
        self.engine.execute(proposal())
        with self.assertRaises(Refused):
            self.engine.execute(proposal("new-entry"))
        self.assertEqual(self.broker.post_count, 1)

    def test_daily_entry_limit_survives_a_completed_round_trip(self):
        self.engine.execute(proposal())
        self.engine.execute(proposal("exit", "sell"))
        with self.assertRaises(Refused):
            self.engine.execute(proposal("next-entry"))
        self.assertEqual(self.broker.post_count, 2)

    def test_live_disabled_and_no_ack_cannot_send_any_order(self):
        live = replace(self.settings, mode="live", live_enabled=True, approved_strategy_versions=("frozen-v1",))
        engine = Engine(live, self.store, self.broker)
        with self.assertRaises(Refused):
            engine.execute(proposal(), settled_cash_usd="20")
        disabled = Engine(replace(live, live_enabled=False), self.store, self.broker)
        with self.assertRaises(Refused):
            disabled.execute(proposal(), live_ack=LIVE_ACK, settled_cash_usd="20")
        self.assertEqual(self.broker.post_count, 0)

    def test_live_requires_version_approval_and_confirmed_settled_funds(self):
        live = replace(self.settings, mode="live", live_enabled=True)
        engine = Engine(live, self.store, self.broker)
        with self.assertRaises(Refused):
            engine.execute(proposal(), live_ack=LIVE_ACK)
        self.assertEqual(self.broker.post_count, 0)

    def test_sale_proceeds_cannot_replenish_attested_day_funds(self):
        live = replace(self.settings, mode="live", live_enabled=True, approved_strategy_versions=("frozen-v1",), max_entries_per_day=2)
        engine = Engine(live, self.store, self.broker)
        engine.execute(proposal(), live_ack=LIVE_ACK, settled_cash_usd="2")
        engine.execute(proposal("exit", "sell"), live_ack=LIVE_ACK)
        with self.assertRaises(Refused):
            engine.execute(proposal("next"), live_ack=LIVE_ACK, settled_cash_usd="2")
        self.assertEqual(self.broker.post_count, 2)

    def test_wrong_broker_identity_refuses_before_order(self):
        settings = replace(self.settings, expected_account_id="wrong")
        with self.assertRaises(Refused):
            Engine(settings, self.store, self.broker).execute(proposal())
        self.assertEqual(self.broker.post_count, 0)

    def test_dashboard_uses_unknown_instead_of_invented_zeroes(self):
        result = state(self.settings)
        self.assertIsNone(result["equity_usd"])
        self.assertIsNone(result["day_pnl_usd"])
        self.assertIsNone(result["research"])

    def test_lesson_cannot_be_declared_validated_by_agent(self):
        self.store.add_lesson("v1", "Test hypothesis", "logs/1")
        row = self.store.db.execute("SELECT status FROM lessons").fetchone()
        self.assertEqual(row[0], "unverified")

    def test_demo_reset_will_not_delete_broker_history(self):
        self.store.capture(self.broker.snapshot("SPY"), self.settings)
        with self.assertRaises(Refused):
            demo(replace(self.settings, mode="demo"), reset=True)
        self.assertEqual(self.store.get("identity")["mode"], "paper")

    def test_fixed_hosts_and_separate_keys(self):
        with patch.dict(os.environ, {"ALPACA_PAPER_KEY_ID":"fake", "ALPACA_PAPER_SECRET_KEY":"fake", "ALPACA_LIVE_KEY_ID":"fake", "ALPACA_LIVE_SECRET_KEY":"fake"}):
            self.assertEqual(AlpacaBroker(self.settings).base, "https://paper-api.alpaca.markets")
            self.assertEqual(AlpacaBroker(replace(self.settings, mode="live")).base, "https://api.alpaca.markets")

    def adapter_fixtures(self):
        at = now_utc()
        return [
            {"id":"SYNTHETIC-DEMO", "equity":"50", "cash":"50", "buying_power":"1000", "non_marginable_buying_power":"50", "last_equity":"50", "status":"ACTIVE", "account_blocked":False,"trading_blocked":False,"trade_suspended_by_user":False},
            [], [],
            {"class":"us_equity","status":"active","tradable":True,"fractionable":True,"exchange":"NYSE"},
            {"quote":{"t":at.isoformat(),"bp":99.99,"ap":100.01}},
            {"is_open":True,"timestamp":at.isoformat(),"next_close":(at+timedelta(hours=6)).isoformat()},
        ]

    def test_adapter_maps_required_fields_and_explicit_free_feed(self):
        with patch.dict(os.environ, {"ALPACA_PAPER_KEY_ID":"fake", "ALPACA_PAPER_SECRET_KEY":"fake"}):
            broker = AlpacaBroker(self.settings)
        with patch.object(broker,"_request",side_effect=self.adapter_fixtures()) as request:
            snapshot = broker.snapshot("SPY")
        self.assertEqual(snapshot.buying_power, number("50"))
        self.assertTrue(snapshot.asset_ok)
        self.assertEqual(snapshot.ask, number("100.01"))
        self.assertIn("feed=iex", request.call_args_list[4].args[1])

    def test_adapter_fails_closed_on_missing_restriction_flags(self):
        fixtures = self.adapter_fixtures()
        del fixtures[0]["account_blocked"]
        with patch.dict(os.environ, {"ALPACA_PAPER_KEY_ID":"fake", "ALPACA_PAPER_SECRET_KEY":"fake"}):
            broker = AlpacaBroker(self.settings)
        with patch.object(broker,"_request",side_effect=fixtures), self.assertRaises(Refused):
            broker.snapshot("SPY")

    def test_missing_paper_keys_do_not_fall_back_to_live_keys(self):
        with patch.dict(os.environ, {"ALPACA_LIVE_KEY_ID":"fake", "ALPACA_LIVE_SECRET_KEY":"fake"}, clear=True):
            with self.assertRaises(Refused):
                AlpacaBroker(self.settings)

    def test_unknown_config_keys_are_rejected(self):
        path = Path(self.tmp.name) / "config.json"
        path.write_text(json.dumps({"api_base_url":"https://other.example"}))
        with self.assertRaises(Refused):
            Settings.load(path)


if __name__ == "__main__":
    unittest.main()
