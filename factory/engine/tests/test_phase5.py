"""Phase 5 tests: routing, escalation, cache + invalidation, dedup, cost tracking, budgets, paid gate, loop guard.
All providers are MockProvider; nothing here calls a real model."""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from factory.engine import Approval, ApprovalStatus, Budget, Capability, Store, TaskEngine, TaskSpec, TaskStatus
from factory.engine.providers import AnthropicApiProvider, ClaudeSessionProvider, MockProvider
from factory.engine.router import BudgetExceeded, NoProvider, Router
from factory.engine.tests.test_engine import agent


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name)).open()
        self.mock = MockProvider(script={"classify": "pin"})
        self.now = datetime(2026, 10, 21, 18, 0, tzinfo=timezone.utc)
        self.router = Router(self.store, [self.mock], clock=lambda: self.now)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()


class TestRouting(Base):
    def test_tier_by_kind_hint_and_escalation(self):
        r = self.router
        self.assertEqual(r.tier_for("channel.adapt"), "quick")
        self.assertEqual(r.tier_for("research.brief"), "strong")
        self.assertEqual(r.tier_for("channel.adapt", model_hint="strong"), "strong")
        self.assertEqual(r.tier_for("channel.adapt", attempt=2), "strong")  # escalate after a failed validation
        self.assertEqual(r.tier_for("channel.adapt", uncertain=True), "strong")
        self.assertEqual(r.tier_for("nonsense.kind"), "quick")

    def test_pick_skips_unavailable_and_gates_paid(self):
        env = dict(os.environ)
        try:
            os.environ.pop("GM_CLAUDE_SESSION", None)
            os.environ["ANTHROPIC_API_KEY"] = "sk-test-not-a-real-key-000000"
            os.environ["GM_MODEL_QUICK"] = "configured-quick"
            r = Router(self.store, [ClaudeSessionProvider(Path(self.tmp.name) / "h"), AnthropicApiProvider()])
            with self.assertRaises(NoProvider) as cm:
                r.pick("quick")
            self.assertIn("needs an approved spend_money approval", str(cm.exception))
            a = Approval(id="apr_spend", task_id=None, capability=Capability.SPEND_MONEY, title="allow paid API", why="test", status=ApprovalStatus.APPROVED)
            self.store.put_approval(a)
            self.store.set_control("paid_provider_approval", "apr_spend")
            self.assertEqual(r.pick("quick").id, "anthropic_api")
            with self.assertRaises(NoProvider):
                r.pick("strong")  # GM_MODEL_STRONG unset → no model for that tier, never a guess
        finally:
            os.environ.clear()
            os.environ.update(env)

    def test_no_providers_is_a_clear_stop(self):
        r = Router(self.store, [])
        with self.assertRaises(NoProvider):
            r.complete("t1", "channel.adapt", "x")


class TestCache(Base):
    def test_hit_miss_expiry_and_data_version(self):
        c1 = self.router.complete("t1", "channel.adapt", "classify this pin", cacheable=True, ttl_s=60)
        self.assertFalse(c1.cached)
        self.router._inflight.clear()  # simulate a new process
        c2 = self.router.complete("t2", "channel.adapt", "classify this pin", cacheable=True)
        self.assertTrue(c2.cached)
        self.assertEqual(c2.meta["cache"], "hit")
        self.assertEqual(len(self.mock.calls), 1)
        # expiry
        self.now += timedelta(seconds=120)
        self.router._inflight.clear()
        c3 = self.router.complete("t3", "channel.adapt", "classify this pin", cacheable=True)
        self.assertFalse(c3.cached)
        self.assertEqual(len(self.mock.calls), 2)
        # data version bump invalidates everything older
        self.store.set_control("data_version", "2")
        self.router._inflight.clear()
        c4 = self.router.complete("t4", "channel.adapt", "classify this pin", cacheable=True)
        self.assertFalse(c4.cached)
        self.assertEqual(len(self.mock.calls), 3)
        self.assertGreaterEqual(self.store.cache_purge("2"), 1)

    def test_not_cacheable_always_calls(self):
        for _ in range(2):
            self.router._inflight.clear()
            self.router.complete("t1", "analytics.measure", "what are SPY prices now")
        self.assertEqual(len(self.mock.calls), 2)
        self.assertEqual(self.store.cache_stats()["entries"], 0)

    def test_dedup_within_process(self):
        self.router.complete("t1", "channel.adapt", "same question")
        c = self.router.complete("t2", "channel.adapt", "same question")
        self.assertTrue(c.cached)
        self.assertEqual(len(self.mock.calls), 1)
        self.assertEqual(self.store.usage_summary()["cached_calls"], 1)


class TestCostAndBudgets(Base):
    def test_usage_recorded_and_unknown_stays_unknown(self):
        self.router.complete("t1", "channel.adapt", "classify a thing")
        rep = self.router.report()
        self.assertEqual(rep["calls"], 1)
        self.assertIsNone(rep["cost_usd_known"])
        self.assertEqual(rep["cost_unknown_calls"], 1)
        self.assertIn("never priced", rep["cost_note"])
        self.assertEqual(rep["tokens_known"], 3 + 1)  # mock counts its own words: prompt 3, reply "pin" 1

    def test_per_task_call_budget(self):
        b = Budget(max_calls_per_task=2)
        self.router.complete("t1", "channel.adapt", "a", budget=b)
        self.router.complete("t1", "channel.adapt", "b", budget=b)
        with self.assertRaises(BudgetExceeded):
            self.router.complete("t1", "channel.adapt", "c", budget=b)
        self.router.complete("t2", "channel.adapt", "d", budget=b)  # another task is unaffected

    def test_per_task_token_budget(self):
        b = Budget(max_calls_per_task=None, max_tokens_per_task=5)
        self.router.complete("t1", "channel.adapt", "one two three four", budget=b)
        with self.assertRaises(BudgetExceeded):
            self.router.complete("t1", "channel.adapt", "five", budget=b)

    def test_daily_hard_limits(self):
        self.store.set_control("budget", {"daily_calls": 2})
        self.router.complete("t1", "channel.adapt", "a")
        self.router.complete("t2", "channel.adapt", "b")
        with self.assertRaises(BudgetExceeded) as cm:
            self.router.complete("t3", "channel.adapt", "c")
        self.assertIn("daily call budget", str(cm.exception))
        self.store.set_control("budget", {"daily_calls": 100, "daily_unknown_calls": 2})
        with self.assertRaises(BudgetExceeded) as cm:
            self.router.complete("t4", "channel.adapt", "d")
        self.assertIn("unknown cost", str(cm.exception))

    def test_loop_guard(self):
        with self.assertRaises(BudgetExceeded) as cm:
            for _ in range(10):
                self.router._inflight.clear()
                self.router.complete("t1", "channel.adapt", "again")
        self.assertIn("runaway loop", str(cm.exception))


class TestEngineIntegration(Base):
    def test_ctx_llm_records_usage_and_budget_stop_fails_task_safely(self):
        eng = TaskEngine(self.store, {"tester": agent(retries=0)}, runner="test", router=self.router)

        def h(task, ctx):
            c = ctx.llm("classify: is this a pin?", cacheable=True)
            return {"output_ref": "out/" + c.text}
        eng.register("demo.llm", h)
        t = eng.submit(TaskSpec(agent_id="tester", kind="demo.llm", input_ref="x"))
        eng.tick()
        t = self.store.get_task(t.id)
        self.assertEqual((t.status, t.output_ref), (TaskStatus.SUCCEEDED, "out/pin"))
        run = self.store.runs_for(t.id)[-1]
        self.assertEqual(run.model, "mock-quick")
        self.assertEqual(run.usage.tokens_out, 1)

        def greedy(task, ctx):
            for i in range(10):
                ctx.llm(f"question {i}")
            return {}
        eng.register("demo.greedy", greedy)
        t2 = eng.submit(TaskSpec(agent_id="tester", kind="demo.greedy", input_ref="y"))
        eng.tick()
        t2 = self.store.get_task(t2.id)
        self.assertEqual(t2.status, TaskStatus.FAILED)
        self.assertIn("call budget", t2.last_error)
        self.assertEqual(self.store.runs_for(t2.id)[-1].error_class, "permanent")

    def test_engine_without_router_refuses_llm(self):
        eng = TaskEngine(self.store, {"tester": agent(retries=0)}, runner="test")
        eng.register("demo.llm", lambda task, ctx: {"output_ref": ctx.llm("x").text})
        t = eng.submit(TaskSpec(agent_id="tester", kind="demo.llm", input_ref="x"))
        eng.tick()
        self.assertIn("no model router", self.store.get_task(t.id).last_error)


if __name__ == "__main__":
    unittest.main()
