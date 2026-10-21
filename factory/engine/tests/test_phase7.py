"""Phase 7 tests: publishing adapters (gateway job shape, drafts, idempotency, verify from gw/out, kill switch),
channel adaptation, evidence-based analytics, and the full promote_product path through the orchestrator.
Everything is MOCKED: the gateway is a temp folder, nothing is sent anywhere."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from factory.engine import Approval, ApprovalStatus, Capability, Channel, Store, TaskEngine, TaskStatus
from factory.engine import analytics as A
from factory.engine import distribution as D
from factory.engine import publishing as P
from factory.engine.orchestrator import Orchestrator
from factory.engine.registry import AGENTS, demo_handlers
from factory.engine.tests.test_phase6 import GOOD_COPY, make_product

MEDIA = {"default": [{"type": "image", "url": "https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/pins/x.jpg"}],
         "tiktok": [{"type": "video", "url": "https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/social/x/video.mp4"}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / "db").open()
        self.gw = P.GatewayAdapter(self.root / "gw" / "jobs", self.root / "gw" / "out")
        self.draft = P.DraftAdapter(self.root / "drafts")
        self.pub = P.Publisher(self.store, self.gw, self.draft)
        self.m = make_product(self.root)
        self.store.put_product(self.m)
        self.plan = D.build_plan(self.m, target_customer="party hosts", evidence=["etsy search 2026-10-18"], destination_url="https://www.etsy.com/listing/999",
                                 start=datetime(2026, 11, 1, 6), days=1)
        self.store.put_plan(self.plan)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def approve(self):
        self.store.put_approval(Approval(id="apr_pub", task_id=None, capability=Capability.PUBLISH_PUBLIC, title="go", why="t", status=ApprovalStatus.APPROVED))
        D.approve_plan(self.store, self.plan, "apr_pub")
        return self.plan

    def assets(self):
        return {a.channel: a for a in P.adapt(self.plan, GOOD_COPY, MEDIA, boards={"pinterest": "1096274802985595723"})}


class TestAdapt(Base):
    def test_assets_fit_each_channel(self):
        aa = self.assets()
        self.assertEqual(set(aa), set(self.plan.channels))
        self.assertLessEqual(len(aa[Channel.TIKTOK].text), 150)
        self.assertIn("Link in bio", aa[Channel.TIKTOK].text)
        self.assertEqual(aa[Channel.TIKTOK].media[0]["type"], "video")
        self.assertEqual(aa[Channel.PINTEREST].board_id, "1096274802985595723")
        self.assertTrue(aa[Channel.PINTEREST].scheduled_for.endswith("Z"))
        self.assertEqual(aa[Channel.PINTEREST].link, "https://www.etsy.com/listing/999")
        long = dict(GOOD_COPY, description="word " * 300)
        a = {x.channel: x for x in P.adapt(self.plan, long, MEDIA)}
        self.assertLessEqual(len(a[Channel.PINTEREST].text), 500)


class TestPublisher(Base):
    def test_refuses_unapproved_plan_and_kill_switch(self):
        a = self.assets()[Channel.PINTEREST]
        with self.assertRaises(PermissionError):
            self.pub.publish(self.plan, a)
        self.approve()
        self.store.set_control("kill", True)
        with self.assertRaises(PermissionError):
            self.pub.publish(self.plan, a)
        self.store.set_control("kill", False)
        self.assertEqual(self.pub.publish(self.plan, a).status, "queued")

    def test_gateway_job_matches_gw_run_shape_and_is_idempotent(self):
        self.approve()
        a = self.assets()[Channel.PINTEREST]
        r1 = self.pub.publish(self.plan, a)
        r2 = self.pub.publish(self.plan, a)
        self.assertEqual(r1.id, r2.id)  # never twice
        self.assertEqual(len(list((self.root / "gw" / "jobs").glob("*.json"))), 1)
        job = json.loads(next((self.root / "gw" / "jobs").glob("*.json")).read_text())
        op = job["ops"][0]
        self.assertEqual((op["op"], op["method"], op["path"]), ("zernio", "POST", "/posts"))
        self.assertEqual(op["idem"], r1.idem_key)
        self.assertEqual(op["body"]["platforms"][0]["platform"], "pinterest")
        self.assertEqual(op["body"]["platforms"][0]["platformSpecificData"]["boardId"], "1096274802985595723")
        self.assertEqual(op["body"]["platforms"][0]["platformSpecificData"]["link"], "https://www.etsy.com/listing/999")
        self.assertIn("scheduledFor", op["body"])
        self.assertNotIn("Authorization", json.dumps(job))
        self.assertIsNone(r1.verified)
        self.assertEqual(r1.status, "queued")

    def test_verify_reads_real_gateway_result(self):
        self.approve()
        r = self.pub.publish(self.plan, self.assets()[Channel.PINTEREST])
        self.assertEqual(self.pub.refresh(r).status, "queued")  # no result yet
        (self.root / "gw" / "out").mkdir(parents=True)
        (self.root / "gw" / "out" / f"{r.job_id}.json").write_text(json.dumps({"id": r.job_id, "ok": True, "results": [
            {"op": "zernio", "status": 201, "ok": True, "data": {"post": {"_id": "6ad8f37e8c105982dc04aff4", "scheduledFor": "2026-11-01T14:00:00Z"}}}]}))
        r = self.pub.refresh(r)
        self.assertEqual((r.status, r.verified, r.external_id), ("scheduled", True, "6ad8f37e8c105982dc04aff4"))
        (self.root / "gw" / "out" / f"{r.job_id}.json").write_text(json.dumps({"id": r.job_id, "ok": False, "results": [
            {"op": "zernio", "status": 401, "ok": False, "data": {"error": "bad token=abcdef123456"}}]}))
        r = self.pub.refresh(r)
        self.assertEqual((r.status, r.verified), ("failed", False))
        self.assertNotIn("abcdef123456", r.note)
        # a failed one may be retried: a new publication is created
        r3 = self.pub.publish(self.plan, self.assets()[Channel.PINTEREST])
        self.assertNotEqual(r3.id, r.id)

    def test_make_channels_become_drafts_never_published(self):
        self.approve()
        a = self.assets()[Channel.FACEBOOK]
        r = self.pub.publish(self.plan, a)
        self.assertEqual((r.status, r.adapter, r.verified), ("draft", "draft", None))
        self.assertTrue(Path(self.root / "drafts").exists())
        self.assertEqual(self.pub.refresh(r).status, "draft")
        h = {x.id: x for x in self.pub.health()}
        self.assertEqual(h["make"].state.value, "missing")
        self.assertEqual(h["gateway"].state.value, "unverified")  # no gw/out results in the temp gateway

    def test_etsy_listing_job(self):
        plan = D.build_plan(self.m, target_customer="x", evidence=["x 2026-10-01"], destination_url="https://www.etsy.com/listing/999", extra_channels=[Channel.ETSY])
        self.store.put_plan(plan)
        self.store.put_approval(Approval(id="apr2", task_id=None, capability=Capability.PUBLISH_PUBLIC, title="go", why="t", status=ApprovalStatus.APPROVED))
        D.approve_plan(self.store, plan, "apr2")
        with self.assertRaises(ValueError):
            self.pub.publish(plan, P.Asset(channel=Channel.ETSY, text=""))
        r = self.pub.publish(plan, P.Asset(channel=Channel.ETSY, text="", listing_id="4597749137"))
        op = json.loads((self.root / "gw" / "jobs" / f"{r.job_id}.json").read_text())["ops"][0]
        self.assertEqual((op["op"], op["method"], op["body"]), ("etsy", "PATCH", {"state": "active"}))


class TestAnalytics(Base):
    def test_record_ingest_compare_recommend(self):
        with self.assertRaises(ValueError):
            A.record(self.store, channel="pinterest", ref="p1", values={"clicks": 0}, source="x")
        n = A.ingest_pins(self.store, [{"id": "p1", "status": "posted", "pinterestId": "111", "productId": "prod1", "stats": {"impressions": 900, "saves": 12, "outboundClicks": 30, "at": "2026-10-20T10:00:00Z"}},
                                      {"id": "p2", "status": "queued", "stats": None}])
        self.assertEqual(n, 3)
        A.ingest_social(self.store, [{"id": "s1", "platform": "instagram", "status": "posted", "postUrl": "https://instagram.com/p/1", "metrics": {"availability": "available", "views": 600, "clicks": 3, "retrievedAt": "2026-10-20T11:00:00Z"}},
                                     {"id": "s2", "platform": "facebook", "status": "posted", "metrics": {"availability": "unavailable", "views": 0}}])
        A.ingest_youtube(self.store, {"ep1": {"videoId": "abc", "stats": {"views": 40, "at": "2026-10-20T12:00:00Z"}}, "ep2": {"videoId": "def", "stats": {}}})
        c = A.compare(self.store, "channel", days=30)
        g = c["groups"]
        self.assertEqual(g["pinterest"]["clicks"], 30)
        self.assertEqual(g["pinterest"]["sales"], "unknown")
        self.assertNotIn("facebook", g)  # unavailable metrics never become numbers
        self.assertEqual(g["gmula"]["views"], 40)
        self.assertIn("clicks", g["gmula"]["unknown_kinds"])
        recs = {r["group"]: r for r in A.recommend(c)}
        self.assertEqual((recs["pinterest"]["action"], recs["pinterest"]["basis"]), ("improve", "demonstrated"))
        self.assertEqual((recs["instagram"]["action"], recs["instagram"]["basis"]), ("improve", "demonstrated"))
        self.assertEqual(recs["gmula"]["basis"], "hypothesis")

    def test_measure_plan_folds_into_phase6_results(self):
        A.record(self.store, channel="pinterest", ref="111", values={"impressions": 1500, "clicks": 2}, source="pinterest via Day Watch", plan_id=self.plan.id)
        pl = A.measure_plan(self.store, self.plan)
        self.assertEqual((pl.results["impressions"], pl.results["clicks"]), (1500, 2))
        self.assertIn("improve the hook", pl.next_action)
        f = D.funnel(self.store, pl)
        self.assertEqual(f["conversions_or_sales"], "unknown")


class TestEndToEnd(Base):
    def test_promote_product_through_orchestrator_with_mock_gateway(self):
        eng = TaskEngine(self.store, AGENTS, runner="test")
        handlers = demo_handlers()
        for k, h in handlers.items():
            eng.register(k, h)
        P.Publisher.__init__.__defaults__  # noqa: B018 (defaults are the real repo paths; patch below)
        orig = P.GatewayAdapter.__init__
        P.GatewayAdapter.__init__ = lambda s, jobs=self.root / "gw" / "jobs", out=self.root / "gw" / "out": orig(s, jobs, out)
        origd = P.DraftAdapter.__init__
        P.DraftAdapter.__init__ = lambda s, drafts=self.root / "drafts": origd(s, drafts)
        try:
            orc = Orchestrator(eng)
            p = orc.plan("promote_product", "products/prod1", meta={"copy": GOOD_COPY, "media": MEDIA, "boards": {"pinterest": "109"}, "target_customer": "hosts",
                                                                      "evidence": ["etsy search 2026-10-18"], "destination_url": "https://www.etsy.com/listing/999"})
            for _ in range(3):
                eng.tick(max_tasks=1)
            pr = orc.progress(p["id"])
            steps = {r["step"]: r for r in pr["tasks"]}
            self.assertEqual(steps["plan"]["status"], "succeeded")
            self.assertEqual(steps["adapt"]["status"], "succeeded")
            self.assertEqual(steps["publish"]["status"], "needs_approval")
            a = self.store.approvals("proposed")[0]
            self.assertEqual(a.capability, Capability.PUBLISH_PUBLIC)
            eng.decide(a.id, True)
            for _ in range(3):
                eng.tick(max_tasks=1)
            steps = {r["step"]: r for r in orc.progress(p["id"])["tasks"]}
            self.assertEqual(steps["publish"]["status"], "succeeded", steps["publish"])
            pubs = P.Publisher(self.store).publications()
            by = {x.channel.value: x for x in pubs}
            self.assertEqual(by["pinterest"].status, "queued")
            self.assertEqual(by["tiktok"].status, "queued")
            self.assertEqual(by["facebook"].status, "draft")
            self.assertEqual(by["youtube_shop"].status, "draft")
            self.assertEqual(len(list((self.root / "gw" / "jobs").glob("*.json"))), 2)
            self.assertEqual(steps["measure"]["status"], "succeeded")
            run = self.store.runs_for(steps["measure"]["task_id"])[-1]
            self.assertIn("known: nothing yet", run.validation["checks"][0])
            self.assertEqual(orc.verify(p["id"])["status"], "complete")
            self.assertEqual(self.store.get_plan(steps["plan"]["output_ref"].split("/")[-1]).status, "scheduled")  # never 'published' without the gateway's word
        finally:
            P.GatewayAdapter.__init__ = orig
            P.DraftAdapter.__init__ = origd


if __name__ == "__main__":
    unittest.main()
