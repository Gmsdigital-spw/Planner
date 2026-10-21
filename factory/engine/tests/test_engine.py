"""Engine tests (unittest, no deps). Every guarantee in engine.py has a test here.
All external integrations are MOCKED: nothing here touches Etsy, Make, Zernio, Alpaca or the artifact DB."""
from __future__ import annotations

import json
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from factory.engine import (AgentContract, AgentRole, ApprovalStatus, Budget, Capability, Channel, DistributionPlan, EngineError,
                            ErrorPolicy, FileRef, IntegrationHealth, IntegrationState, ModelUsage, NeedsApproval, PermanentError,
                            ProductManifest, Store, TaskEngine, TaskSpec, TaskStatus, TransientError, fmt_num, scrub)
from factory.engine import contracts
from factory.engine.registry import AGENTS


def agent(id="tester", caps=(), tools=("tool.a", "tool.b"), retries=2, timeout=5):
    return AgentContract(id=id, name=id, role=AgentRole.ENGINEERING, responsibilities=["test"], inputs=["x"], outputs=["y"],
                         tools=list(tools), capabilities=list(caps), error_policy=ErrorPolicy(max_retries=retries, backoff_base_s=0.01, timeout_s=timeout, stalled_after_s=1),
                         budget=Budget(max_calls_per_task=3))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name)).open()
        self.pub = agent("publisher", caps=[Capability.PUBLISH_PUBLIC], tools=["gateway.job"])
        self.eng = TaskEngine(self.store, {"tester": agent(), "publisher": self.pub}, runner="test")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def spec(self, kind="demo.ok", agent_id="tester", **kw):
        return TaskSpec(agent_id=agent_id, kind=kind, input_ref=kw.pop("input_ref", "doc/1"), **kw)


class TestContracts(Base):
    def test_round_trip_and_schema(self):
        a = AGENTS["bolt"]
        d = a.to_dict()
        b = AgentContract.from_dict(json.loads(json.dumps(d)))
        self.assertEqual(a.to_json(), b.to_json())
        schema = contracts.to_json_schema()
        self.assertIn("Task", schema["$defs"])
        self.assertEqual(schema["$defs"]["TaskStatus"]["enum"][0], "queued")
        ts = contracts.to_typescript()
        self.assertIn("export interface DistributionPlan", ts)
        self.assertIn('export type Channel = "etsy" | "pinterest"', ts)

    def test_no_agent_has_trade_live_and_no_parked_channels(self):
        for a in AGENTS.values():
            self.assertNotIn(Capability.TRADE_LIVE, a.capabilities)
        with self.assertRaises(ValueError):
            agent(caps=[Capability.TRADE_LIVE]).validate()
        self.assertEqual({c.value for c in Channel}, {"etsy", "pinterest", "instagram", "facebook", "tiktok", "youtube_shop", "gmula"})

    def test_unknown_stays_unknown(self):
        self.assertEqual(fmt_num(None), "unknown")
        self.assertEqual(fmt_num(0), "0")
        u = ModelUsage(provider="claude", model="quick")
        self.assertIsNone(u.tokens_in)
        self.store.put_usage(None, u)
        self.store.put_usage(None, ModelUsage(provider="claude", model="quick", tokens_in=10, tokens_out=5, cost_usd=0.01))
        s = self.store.usage_summary()
        self.assertEqual(s["calls"], 2)
        self.assertEqual(s["cost_unknown_calls"], 1)
        self.assertEqual(s["cost_usd_known"], 0.01)

    def test_scrub_hides_secrets(self):
        s = scrub("token=abcdef123456 and sk-0123456789abcdef ok")
        self.assertNotIn("abcdef123456", s)
        self.assertNotIn("sk-0123456789abcdef", s)
        self.assertIn("[redacted]", s)

    def test_distribution_plan_validation(self):
        with self.assertRaises(ValueError):
            DistributionPlan(id="p", product_id="x", product_version=1, target_customer="moms", evidence=["https://e (2026-10-01)"],
                             channels=[Channel.PINTEREST], channel_reasons={}).validate()


class TestStore(Base):
    def test_migrations_and_rebuild_from_journal(self):
        self.assertEqual(self.store.schema_version(), 4)
        t = self.eng.submit(self.spec())
        self.store.put_integration(IntegrationHealth(id="make", state=IntegrationState.UNVERIFIED, note="no call this session"))
        # simulate a lost sqlite: delete it and reopen → rebuilt from the journal
        self.store.close()
        (Path(self.tmp.name) / "state.sqlite").unlink()
        st2 = Store(Path(self.tmp.name)).open()
        self.assertIsNotNone(st2.get_task(t.id))
        self.assertEqual(st2.integrations()[0]["state"], "unverified")
        st2.close()
        self.store = Store(Path(self.tmp.name)).open()

    def test_torn_journal_line_is_ignored(self):
        self.eng.submit(self.spec())
        with (Path(self.tmp.name) / "journal.jsonl").open("a") as f:
            f.write('{"v":1,"kind":"task","data":{"id":"brok')  # crash mid-write
        n = self.store.rebuild()
        self.assertGreaterEqual(n, 1)

    def test_product_versions_are_preserved(self):
        f = [FileRef(path="a.pdf", sha256="x" * 64, bytes=10, format="pdf")]
        self.store.put_product(ProductManifest(product_id="prod1", version=1, created_at="2026-10-21T00:00:00Z", files=f, format="pdf", title="A", lane="planner"))
        with self.assertRaises(ValueError):  # a release is never overwritten
            self.store.put_product(ProductManifest(product_id="prod1", version=1, created_at="2026-10-21T01:00:00Z", files=f, format="pdf", title="A2", lane="planner"))
        self.store.put_product(ProductManifest(product_id="prod1", version=2, created_at="2026-10-21T01:00:00Z", files=f, format="pdf", title="A2", lane="planner", supersedes=1))
        self.assertEqual(self.store.product_versions("prod1"), [1, 2])
        self.assertEqual(self.store.get_product("prod1", 1).title, "A")
        self.assertEqual(self.store.get_product("prod1").version, 2)


class TestEngine(Base):
    def test_transitions_and_success(self):
        self.eng.register("demo.ok", lambda task, ctx: {"output_ref": "out/1", "validation": {"ok": True, "checks": []}})
        t = self.eng.submit(self.spec())
        self.assertEqual(t.status, TaskStatus.QUEUED)
        runs = self.eng.tick()
        self.assertEqual(len(runs), 1)
        t = self.store.get_task(t.id)
        self.assertEqual(t.status, TaskStatus.SUCCEEDED)
        self.assertEqual(t.output_ref, "out/1")
        with self.assertRaises(EngineError):  # terminal: no cancel, no illegal move
            self.eng.cancel(t.id)
        actions = [a["action"] for a in self.store.audit_tail()]
        self.assertIn("submit", actions)
        self.assertIn("running", actions)
        self.assertIn("succeeded", actions)

    def test_idempotency(self):
        a = self.eng.submit(self.spec(input_ref="pin/42"))
        b = self.eng.submit(self.spec(input_ref="pin/42"))
        self.assertEqual(a.id, b.id)
        self.assertEqual(self.store.counts()["queued"], 1)

    def test_tool_allow_list_and_call_budget(self):
        with self.assertRaises(EngineError):
            self.eng.submit(self.spec(tools=["gateway.job"]))  # tester may not
        calls = {"n": 0}

        def greedy(task, ctx):
            for _ in range(5):
                ctx.use_tool("tool.a")
                calls["n"] += 1
            return {}
        self.eng.register("demo.greedy", greedy)
        t = self.eng.submit(self.spec(kind="demo.greedy"))
        self.eng.tick()
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.FAILED)
        self.assertEqual(calls["n"], 3)  # stopped at the budget
        self.assertIn("budget", self.store.get_task(t.id).last_error)

    def test_retry_with_backoff_then_fail(self):
        n = {"i": 0}

        def flaky(task, ctx):
            n["i"] += 1
            raise TransientError("503")
        self.eng.register("demo.flaky", flaky)
        t = self.eng.submit(self.spec(kind="demo.flaky"))
        for _ in range(6):
            time.sleep(0.05)
            self.eng.tick()
        t = self.store.get_task(t.id)
        self.assertEqual(t.status, TaskStatus.FAILED)
        self.assertEqual(t.attempts, 3)  # 1 + max_retries(2)
        runs = self.store.runs_for(t.id)
        self.assertEqual([r.attempt for r in runs], [1, 2, 3])
        self.assertEqual(runs[0].error_class, "transient")
        self.assertIn("retries exhausted", runs[-1].recovery)
        # operator retry resets the budget
        self.eng.retry(t.id)
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.QUEUED)
        self.assertEqual(self.store.get_task(t.id).attempts, 0)

    def test_permanent_error_fails_at_once(self):
        self.eng.register("demo.bad", lambda task, ctx: (_ for _ in ()).throw(PermanentError("bad input")))
        t = self.eng.submit(self.spec(kind="demo.bad"))
        self.eng.tick()
        t = self.store.get_task(t.id)
        self.assertEqual((t.status, t.attempts), (TaskStatus.FAILED, 1))

    def test_timeout_is_bounded(self):
        slow = agent("slow", timeout=1, retries=0)
        eng = TaskEngine(self.store, {"slow": slow}, runner="test")
        eng.register("demo.slow", lambda task, ctx: time.sleep(3) or {})
        t = eng.submit(TaskSpec(agent_id="slow", kind="demo.slow", input_ref="x"))
        t0 = time.time()
        eng.tick()
        self.assertLess(time.time() - t0, 2.5)
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.FAILED)
        self.assertEqual(self.store.runs_for(t.id)[-1].error_class, "timeout")

    def test_approval_gate(self):
        self.eng.register("publish.pin", lambda task, ctx: {"output_ref": "pin/42/posted"})
        t = self.eng.submit(self.spec(kind="publish.pin", agent_id="publisher", capabilities=[Capability.PUBLISH_PUBLIC], tools=["gateway.job"]))
        self.eng.tick()
        t = self.store.get_task(t.id)
        self.assertEqual(t.status, TaskStatus.NEEDS_APPROVAL)
        self.assertEqual(t.attempts, 0)  # waiting is not a failed attempt
        pend = self.store.approvals("proposed")
        self.assertEqual(len(pend), 1)
        self.assertEqual(pend[0].capability, Capability.PUBLISH_PUBLIC)
        self.assertEqual(self.eng.tick(), [])  # parked: nothing runs
        self.eng.decide(pend[0].id, True)
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.QUEUED)
        self.eng.tick()
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.SUCCEEDED)
        # an agent without the capability can never even ask for it
        with self.assertRaises(EngineError):
            self.eng.submit(self.spec(kind="publish.pin", capabilities=[Capability.PUBLISH_PUBLIC]))

    def test_declined_approval_cancels(self):
        self.eng.register("publish.pin", lambda task, ctx: {})
        t = self.eng.submit(self.spec(kind="publish.pin", agent_id="publisher", capabilities=[Capability.PUBLISH_PUBLIC]))
        self.eng.tick()
        a = self.store.approvals("proposed")[0]
        self.eng.decide(a.id, False)
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.CANCELLED)
        with self.assertRaises(EngineError):
            self.eng.decide(a.id, True)  # already decided

    def test_mid_run_needs_approval(self):
        def h(task, ctx):
            ctx.require(Capability.PUBLISH_PUBLIC, "Post pin 42", "It goes public.")
            return {"output_ref": "done"}
        self.eng.register("publish.late", h)
        t = self.eng.submit(self.spec(kind="publish.late", agent_id="publisher"))
        self.eng.tick()
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.NEEDS_APPROVAL)

    def test_kill_switch_pause_cancel(self):
        self.eng.register("demo.ok", lambda task, ctx: {})
        t = self.eng.submit(self.spec())
        self.eng.kill(True)
        self.assertEqual(self.eng.tick(), [])
        self.assertIsNotNone(self.store.get_task(t.id))  # nothing deleted
        self.eng.kill(False)
        self.eng.pause_agent("tester", True)
        self.assertEqual(self.eng.tick(), [])
        self.eng.pause_agent("tester", False)
        self.eng.cancel(t.id, why="changed my mind")
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.CANCELLED)
        self.assertEqual(self.eng.tick(), [])

    def test_dependencies_order(self):
        order = []
        self.eng.register("demo.ok", lambda task, ctx: order.append(task.spec.input_ref) or {})
        a = self.eng.submit(self.spec(input_ref="A", priority=9))
        b = self.eng.submit(self.spec(input_ref="B", priority=1, depends_on=[a.id]))
        self.eng.tick(max_tasks=1)
        self.assertEqual(order, ["A"])  # B waited even though it is higher priority
        self.eng.tick(max_tasks=1)
        self.assertEqual(order, ["A", "B"])

    def test_stalled_recovery_from_checkpoint(self):
        def h(task, ctx):
            ctx.checkpoint({"step": 2})
            raise KeyboardInterrupt  # the runner dies mid-task
        self.eng.register("demo.die", h)
        t = self.eng.submit(self.spec(kind="demo.die"))
        try:
            self.eng.run_task(self.store.get_task(t.id))
        except KeyboardInterrupt:
            pass
        self.assertEqual(self.store.get_task(t.id).status, TaskStatus.RUNNING)
        # age the heartbeat past stalled_after_s (1s) and bring a fresh engine up, as a new runner would
        run = self.store.runs_for(t.id)[-1]
        run.heartbeat_at = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat(timespec="seconds").replace("+00:00", "Z")
        self.store.put_run(run)
        eng2 = TaskEngine(self.store, {"tester": agent()}, runner="test2")
        t2 = self.store.get_task(t.id)
        self.assertEqual(t2.status, TaskStatus.QUEUED)
        self.assertEqual(t2.checkpoint, {"step": 2})
        self.assertIn("recover", [a["action"] for a in self.store.audit_tail()])

    def test_errors_are_scrubbed(self):
        self.eng.register("demo.leak", lambda task, ctx: (_ for _ in ()).throw(PermanentError("auth failed token=abcdef123456")))
        t = self.eng.submit(self.spec(kind="demo.leak"))
        self.eng.tick()
        self.assertNotIn("abcdef123456", self.store.get_task(t.id).last_error)
        self.assertNotIn("abcdef123456", (Path(self.tmp.name) / "journal.jsonl").read_text())

    def test_status_reports_last_tick_not_a_promise(self):
        s = self.eng.status()
        self.assertIsNone(s["last_tick"])
        self.eng.tick()
        self.assertEqual(self.eng.status()["last_tick"]["runner"], "test")
        self.assertIn("last_tick is the truth", self.eng.status()["note"])


if __name__ == "__main__":
    unittest.main()
