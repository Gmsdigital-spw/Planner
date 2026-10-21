"""Phase 4 tests: registry versions, orchestrator graphs, provider adapters. All mocked; no network."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from factory.engine import Capability, Store, TaskEngine, TaskStatus
from factory.engine.orchestrator import PLANS, Orchestrator
from factory.engine.providers import AnthropicApiProvider, ClaudeSessionProvider, MockProvider, availability
from factory.engine.registry import AGENTS, sync


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name)).open()
        self.eng = TaskEngine(self.store, AGENTS, runner="test")
        self.orc = Orchestrator(self.eng)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()


class TestRegistry(Base):
    def test_sync_is_versioned_and_idempotent(self):
        first = sync(self.store)
        self.assertEqual(len(first), len(AGENTS))
        self.assertTrue(all(c["skill"] == "ok" for c in first), first)  # every contract points at a real SKILL.md
        self.assertEqual(sync(self.store), [])  # nothing changed → nothing written
        bolt = AGENTS["bolt"]
        bolt.responsibilities.append("verify the Zernio post id")
        changed = sync(self.store)
        self.assertEqual([c["id"] for c in changed], ["bolt"])
        self.assertEqual(self.store.get_agent("bolt").version, 2)
        self.assertEqual(self.store.get_agent("bolt", 1).version, 1)  # old version kept
        bolt.responsibilities.pop()

    def test_every_agent_role_is_covered_and_no_live_trading(self):
        roles = {a.role.value for a in AGENTS.values()}
        self.assertEqual(len(roles), 10)
        for a in AGENTS.values():
            self.assertNotIn(Capability.TRADE_LIVE, a.capabilities)
        self.assertNotIn("gumroad", " ".join(t for a in AGENTS.values() for t in a.tools))


class TestOrchestrator(Base):
    def test_plan_builds_graph_and_is_idempotent(self):
        p = self.orc.plan("launch_product", "briefs/abc")
        self.assertEqual([t["step"] for t in p["tasks"]], ["brief", "build", "inspect", "plan", "adapt", "publish", "measure"])
        self.assertEqual(self.orc.plan("launch_product", "briefs/abc")["id"], p["id"])
        self.assertEqual(self.store.counts()["queued"], 7)
        pr = self.orc.progress(p["id"])
        self.assertEqual(pr["done"], 0)
        self.assertEqual(len(pr["blocked"]), 6)  # everything but the brief waits on a dependency
        self.assertIn("brief is queued", pr["blocked"][0]["blocked_by"][0])

    def test_runs_in_order_and_parks_at_publish(self):
        order = []
        for step in PLANS["launch_product"]:
            self.eng.register(step.kind, lambda task, ctx, k=step.kind: order.append(k) or {"output_ref": "out/" + k})
        p = self.orc.plan("launch_product", "briefs/abc")
        for _ in range(10):
            self.eng.tick(max_tasks=1)
        self.assertEqual(order, ["research.brief", "product.build", "quality.inspect", "distribution.plan", "channel.adapt"])
        pr = self.orc.progress(p["id"])
        publish = next(r for r in pr["tasks"] if r["step"] == "publish")
        self.assertEqual(publish["status"], "needs_approval")
        self.assertIn("waiting on Grayson", publish["blocked_by"][0])
        v = self.orc.verify(p["id"])
        self.assertEqual(v["status"], "open")
        self.assertIn("publish: needs_approval", v["problems"])
        # Grayson approves → publish and measure run → verifiably complete
        a = self.store.approvals("proposed")[0]
        self.eng.decide(a.id, True)
        for _ in range(4):
            self.eng.tick(max_tasks=1)
        v = self.orc.verify(p["id"])
        self.assertEqual(v, {"project": p["id"], "status": "complete", "problems": []})
        self.assertEqual(self.store.get_project(p["id"])["status"], "complete")

    def test_verify_refuses_success_without_output(self):
        self.eng.register("research.ideas", lambda task, ctx: {})  # succeeded, but produced no output_ref
        p = self.orc.plan("research_lane", "lane/planner")
        self.eng.tick()
        v = self.orc.verify(p["id"])
        self.assertEqual(v["status"], "open")
        self.assertEqual(v["problems"], ["ideas: succeeded (no output_ref)"])

    def test_failed_step_marks_project_failed_with_reason(self):
        from factory.engine import PermanentError
        self.eng.register("engineering.inspect", lambda task, ctx: (_ for _ in ()).throw(PermanentError("tests red")))
        p = self.orc.plan("health_check", "repo")
        self.eng.tick()
        pr = self.orc.progress(p["id"])
        self.assertEqual(pr["blocked"][0]["blocked_by"], ["tests red"])
        self.assertEqual(self.orc.verify(p["id"])["status"], "failed")

    def test_unknown_goal(self):
        from factory.engine import EngineError
        with self.assertRaises(EngineError):
            self.orc.plan("make_money_fast", "x")

    def test_projects_survive_rebuild(self):
        p = self.orc.plan("research_lane", "lane/game")
        self.store.close()
        (Path(self.tmp.name) / "state.sqlite").unlink()
        self.store = Store(Path(self.tmp.name)).open()
        self.assertEqual(self.store.get_project(p["id"])["goal"], "research_lane")


class TestProviders(unittest.TestCase):
    def test_mock_reports_real_counts_and_no_cost(self):
        m = MockProvider(script={"hello": "hi there"})
        c = m.complete("say hello please", tier="quick")
        self.assertEqual(c.text, "hi there")
        self.assertEqual((c.usage.tokens_in, c.usage.tokens_out), (3, 2))
        self.assertIsNone(c.usage.cost_usd)
        self.assertTrue(c.meta["mocked"])
        self.assertEqual(m.models()["strong"], "mock-strong")

    def test_session_provider_only_inside_a_crew(self):
        env = dict(os.environ)
        os.environ.pop("GM_CLAUDE_SESSION", None)
        try:
            p = ClaudeSessionProvider(Path(tempfile.mkdtemp()))
            self.assertFalse(p.available())
            with self.assertRaises(RuntimeError):
                p.complete("x")
            os.environ["GM_CLAUDE_SESSION"] = "1"
            c = p.complete("secret token=abcdef123456 please")
            self.assertIn("handoff", c.meta)
            self.assertIsNone(c.usage.tokens_in)  # unknown, not 0
            written = next(p.dir.glob("*.json")).read_text()
            self.assertNotIn("abcdef123456", written)
        finally:
            os.environ.clear()
            os.environ.update(env)

    def test_paid_api_unavailable_without_key_and_never_hardcodes_models(self):
        env = dict(os.environ)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            p = AnthropicApiProvider()
            self.assertFalse(p.available())
            with self.assertRaises(RuntimeError):
                p.complete("x")
            av = availability()
            self.assertFalse(av["anthropic_api"]["available"])
            self.assertTrue(av["anthropic_api"]["paid"])
            self.assertEqual(av["anthropic_api"]["models"], {})
        finally:
            os.environ.clear()
            os.environ.update(env)


if __name__ == "__main__":
    unittest.main()
