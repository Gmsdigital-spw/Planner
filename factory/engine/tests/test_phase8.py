"""Phase 8 tests: the dashboard report (credential-free, unknown stays unknown, real counts) and phone orders
(approve / retry / kill / pause applied from files, unknown ids refused, outcomes recorded). Everything is MOCKED:
temp folders only; nothing is sent anywhere."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from factory.engine import Approval, ApprovalStatus, Capability, Store, TaskEngine, TaskSpec, TaskStatus
from factory.engine import distribution as D
from factory.engine import publishing as P
from factory.engine import orders as O
from factory.engine.contracts import ModelUsage
from factory.engine.engine import PermanentError, TransientError
from factory.engine.orchestrator import Orchestrator
from factory.engine.registry import AGENTS, demo_handlers, sync
from factory.engine.report import build_report, write_report
from factory.engine.router import Router
from factory.engine.tests.test_phase6 import GOOD_COPY, make_product
from factory.engine.tests.test_phase7 import MEDIA

SECRET = "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnop"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / "db").open()
        sync(self.store)
        self.eng = TaskEngine(self.store, AGENTS, runner="test", router=Router(self.store))
        for k, h in demo_handlers().items():
            self.eng.register(k, h)
        self.orders = self.root / "orders"

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def order(self, name: str, **d):
        self.orders.mkdir(exist_ok=True)
        (self.orders / f"{name}.json").write_text(json.dumps(d))

    def report(self):
        return build_report(self.store, self.eng, orders=O.recent_outcomes(self.orders))


class TestReport(Base):
    def test_empty_engine_is_honest(self):
        r = self.report()
        self.assertEqual(r["health"]["counts"]["queued"], 0)
        self.assertFalse(r["health"]["kill"])
        self.assertEqual(len(r["agents"]), len(AGENTS))
        self.assertTrue(all(a["state"] == "idle" for a in r["agents"]))
        self.assertEqual(r["usage"]["calls"], 0)
        self.assertEqual(r["usage"]["cost_usd_known"], 0.0)  # no calls = a real zero
        self.assertEqual(r["products"], [])
        self.assertEqual(r["plans"], [])
        self.assertEqual(r["metrics"]["by_channel"], {})
        self.assertIn("generated_at", r)
        p = write_report(r, self.root / "public" / "report.json")
        self.assertTrue(p.exists())
        json.loads(p.read_text())

    def test_unknown_cost_stays_unknown_and_secrets_are_scrubbed(self):
        def boom(task, ctx):
            ctx.record_usage(ModelUsage(provider="x", model="m"))  # provider reported nothing
            raise PermanentError("provider said no; key was " + SECRET)
        self.eng.register("engine.boom", boom)
        tk = self.eng.submit(TaskSpec(agent_id="scout", kind="engine.boom", input_ref="in/1"))
        self.eng.tick()
        r = self.report()
        self.assertEqual(r["usage"]["calls"], 1)
        self.assertEqual(r["usage"]["cost_usd_known"], "unknown")
        self.assertEqual(r["usage"]["cost_unknown_calls"], 1)
        failed = r["tasks"]["failed"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["id"], tk.id)
        self.assertIn("retry", failed[0]["next_step"])
        self.assertEqual(failed[0]["retry"], f"python -m factory.engine retry {tk.id}")
        blob = json.dumps(r)
        self.assertNotIn(SECRET, blob)
        self.assertIn("[redacted]", blob)
        self.assertEqual(r["errors"][0]["task_id"], tk.id)
        agent = next(a for a in r["agents"] if a["id"] == "scout")
        self.assertEqual(agent["state"], "failing")

    def test_promote_product_shows_up_with_approval_plans_and_publications(self):
        m = make_product(self.root)
        self.store.put_product(m)
        orig, origd = P.GatewayAdapter.__init__, P.DraftAdapter.__init__
        P.GatewayAdapter.__init__ = lambda s, jobs=self.root / "gw" / "jobs", out=self.root / "gw" / "out": orig(s, jobs, out)
        P.DraftAdapter.__init__ = lambda s, drafts=self.root / "drafts": origd(s, drafts)
        try:
            orc = Orchestrator(self.eng)
            p = orc.plan("promote_product", "products/prod1", meta={"copy": GOOD_COPY, "media": MEDIA, "boards": {"pinterest": "109"}, "target_customer": "hosts",
                                                                     "evidence": ["etsy search 2026-10-18"], "destination_url": "https://www.etsy.com/listing/999"})
            for _ in range(3):
                self.eng.tick(max_tasks=1)
            r = self.report()
            self.assertEqual(len(r["approvals"]), 1)
            self.assertEqual(r["approvals"][0]["capability"], "publish_public")
            self.assertEqual(len(r["tasks"]["needs_approval"]), 1)
            wf = r["workflows"][0]
            self.assertEqual(wf["id"], p["id"])
            self.assertTrue(any("approval" in " ".join(b["why"] or []) for b in wf["blocked"]))
            self.assertEqual(r["plans"][0]["status"], "planned")
            self.assertEqual(r["plans"][0]["funnel"]["clicks"], "unknown")
            # approve through an order file, then let the worker pass finish it
            self.order("o1", action="approve", id=r["approvals"][0]["id"], by="grayson")
            out = O.apply_orders(self.eng, self.orders)
            self.assertTrue(out[0]["ok"], out)
            for _ in range(3):
                self.eng.tick(max_tasks=1)
            r = self.report()
            self.assertEqual(r["approvals"], [])
            pl = r["plans"][0]
            self.assertEqual(pl["status"], "scheduled")  # never "published" until the gateway says so
            st = {x["channel"]: x for x in pl["publications"]}
            self.assertEqual(st["pinterest"]["status"], "queued")
            self.assertIsNone(st["pinterest"]["verified"])
            self.assertEqual(st["facebook"]["status"], "draft")
            self.assertEqual(r["orders"][0]["action"], "approve")
            self.assertTrue(r["orders"][0]["ok"])
            self.assertEqual(r["products"][0]["product_id"], "prod1")
        finally:
            P.GatewayAdapter.__init__, P.DraftAdapter.__init__ = orig, origd


class TestOrders(Base):
    def test_retry_kill_pause_and_refusals(self):
        def flaky(task, ctx):
            raise PermanentError("nope")
        self.eng.register("engine.flaky", flaky)
        tk = self.eng.submit(TaskSpec(agent_id="scout", kind="engine.flaky", input_ref="in/2"))
        self.eng.tick()
        self.assertEqual(self.store.get_task(tk.id).status, TaskStatus.FAILED)
        self.order("a", action="retry", id=tk.id, by="grayson")
        self.order("b", action="retry", id="task_nope", by="grayson")
        self.order("c", action="kill_on", id="", by="grayson")
        self.order("d", action="pause", id="herald", by="grayson")
        self.order("e", action="pause", id="nobody", by="grayson")
        self.order("f", action="launch_nukes", id="x", by="grayson")
        (self.orders / "g.json").write_text("not json")
        res = {r["order_id"]: r for r in O.apply_orders(self.eng, self.orders)}
        self.assertTrue(res["a"]["ok"])
        self.assertEqual(self.store.get_task(tk.id).status, TaskStatus.QUEUED)
        self.assertFalse(res["b"]["ok"]); self.assertIn("no task", res["b"]["error"])
        self.assertTrue(res["c"]["ok"]); self.assertTrue(self.eng.killed())
        self.assertTrue(res["d"]["ok"]); self.assertTrue(self.eng.paused("herald"))
        self.assertFalse(res["e"]["ok"]); self.assertIn("unknown agent", res["e"]["error"])
        self.assertFalse(res["f"]["ok"]); self.assertIn("unknown action", res["f"]["error"])
        self.assertFalse(res["g"]["ok"]); self.assertIn("unreadable", res["g"]["error"])
        self.assertEqual(list(self.orders.glob("*.json")), [])  # every order moved to done/
        self.assertEqual(len(list((self.orders / "done").glob("*.json"))), 7)
        self.assertEqual(len(O.recent_outcomes(self.orders)), 7)
        acts = [a["action"] for a in self.store.audit_tail(20)]
        self.assertIn("order_applied", acts); self.assertIn("order_refused", acts)
        # the kill switch now blocks the retried task; the report says so
        self.eng.tick()
        self.assertEqual(self.store.get_task(tk.id).status, TaskStatus.QUEUED)
        r = self.report()
        self.assertTrue(r["health"]["kill"])
        self.assertEqual(r["health"]["paused_agents"], ["herald"])
        self.order("h", action="kill_off", id="", by="grayson")
        O.apply_orders(self.eng, self.orders)
        self.assertFalse(self.eng.killed())

    def test_decline_cancels_the_waiting_task(self):
        a = Approval(id="apr_x", task_id=None, capability=Capability.PUBLISH_PUBLIC, title="t", why="w")
        self.store.put_approval(a)
        self.order("a", action="decline", id="apr_x", by="grayson")
        res = O.apply_orders(self.eng, self.orders)
        self.assertTrue(res[0]["ok"])
        self.assertEqual(self.store.get_approval("apr_x").status, ApprovalStatus.DECLINED)
        self.order("b", action="approve", id="apr_x", by="grayson")
        res = O.apply_orders(self.eng, self.orders)
        self.assertFalse(res[0]["ok"]); self.assertIn("already declined", res[0]["error"])


if __name__ == "__main__":
    unittest.main()
