"""Phase 6 tests: quality gate pipeline, versioning, distribution plans, funnel honesty, publish gates. No network."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from factory.engine import Approval, ApprovalStatus, Capability, Channel, ProductManifest, Store, TaskEngine, TaskStatus
from factory.engine import distribution as D
from factory.engine import quality as Q
from factory.engine.orchestrator import Orchestrator
from factory.engine.registry import AGENTS, demo_handlers

GOOD_COPY = {"title": "Christmas Party Games Bundle, 10 Printable Games for Family Night", "tags": [f"tag{i}" for i in range(13)],
             "description": "x" * 320}


def make_product(root: Path, pid="prod1", lane="game", fmt="pdf", content=b"%PDF-1.4 test", limits=("prints on Letter; A4 scales",)) -> ProductManifest:
    f = root / f"{pid}.{fmt}"
    f.write_bytes(content)
    return ProductManifest(product_id=pid, version=1, created_at="2026-10-21T00:00:00Z", files=[Q.file_ref(f, root)], format=fmt, title="Christmas Games",
                           lane=lane, known_limitations=list(limits), validation={"stage": "generate"})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / "db").open()
        self.pipe = Q.Pipeline(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def approved_publish(self, task_id=None):
        a = Approval(id="apr_pub", task_id=task_id, capability=Capability.PUBLISH_PUBLIC, title="publish", why="t", status=ApprovalStatus.APPROVED)
        self.store.put_approval(a)
        return a


class TestValidation(Base):
    def test_good_product_passes_with_score(self):
        m = make_product(self.root)
        res = Q.validate(m, GOOD_COPY, root=self.root, score=95)
        self.assertTrue(res["ok"], [c for c in res["checks"] if c["ok"] is not True])
        self.assertEqual(Q.gate(res)["decision"], "approved")

    def test_unknowns_force_human_review_not_pass(self):
        m = make_product(self.root)
        res = Q.validate(m, dict(GOOD_COPY, description="y" * 320 + " https://example.com/x"), root=self.root)  # unscored + a link
        self.assertIsNone(res["ok"])
        self.assertGreaterEqual(res["unknown"], 2)
        g = Q.gate(res)
        self.assertEqual(g["decision"], "needs_review")
        self.assertTrue(g["human_review"])
        self.assertTrue(any("score" in r for r in g["reasons"]))

    def test_failures_are_specific(self):
        m = make_product(self.root, content=b"not a pdf at all")
        bad_copy = {"title": "T" * 141, "tags": ["x"] * 12, "description": "Disney elf guaranteed sales " * 20}
        res = Q.validate(m, bad_copy, root=self.root, score=99)
        names = {c["name"] for c in res["checks"] if c["ok"] is False}
        self.assertIn("real pdf: prod1.pdf", names)
        self.assertIn("title 1..140", names)
        self.assertIn("13 tags ≤ 20 chars", names)
        self.assertIn("no revenue claims", names)
        self.assertIn("original (no brands / characters)", names)
        self.assertEqual(Q.gate(res)["decision"], "rejected")

    def test_missing_file_and_wrong_lane_format(self):
        m = make_product(self.root, lane="planner", fmt="png", content=b"\x89PNG\r\n")
        (self.root / "prod1.png").unlink()
        res = Q.validate(m, GOOD_COPY, root=self.root, score=95)
        self.assertFalse(res["ok"])
        m2 = make_product(self.root, pid="p2", lane="planner", fmt="png", content=b"\x89PNG\r\n")
        res2 = Q.validate(m2, GOOD_COPY, root=self.root, score=95)
        self.assertIn("format allowed for lane: p2.png", {c["name"] for c in res2["checks"] if c["ok"] is False})

    def test_no_limitations_listed_fails(self):
        m = make_product(self.root, limits=())
        res = Q.validate(m, GOOD_COPY, root=self.root, score=95)
        self.assertFalse(res["ok"])


class TestPipeline(Base):
    def _to_validate(self, score=95, copy=GOOD_COPY):
        m = make_product(self.root)
        self.store.put_product(m)
        res = Q.validate(m, copy, root=self.root, score=score)
        return self.pipe.advance("prod1", "validate", {"result": res})

    def test_stages_in_order_and_versions_preserved(self):
        m = self._to_validate()
        self.assertEqual((m.version, self.pipe.stage_of(m)), (2, "validate"))
        with self.assertRaises(ValueError):
            self.pipe.advance("prod1", "publish")  # no skipping
        with self.assertRaises(ValueError):
            self.pipe.advance("prod1", "generate")  # no going back
        self.assertEqual(self.store.product_versions("prod1"), [1, 2])
        self.assertEqual(self.store.get_product("prod1", 1).validation, {"stage": "generate"})  # v1 untouched

    def test_rejected_products_stop(self):
        m = self._to_validate(score=80)
        self.assertEqual(m.listing_status, "rejected")
        self.pipe.advance("prod1", "review")
        self.pipe.advance("prod1", "assets")
        with self.assertRaises(ValueError):
            self.pipe.advance("prod1", "distribution")  # no plan
        plan = D.build_plan(m, target_customer="moms", evidence=["https://x (2026-10-20)"], destination_url="https://www.etsy.com/listing/123")
        self.store.put_plan(plan)
        self.pipe.advance("prod1", "distribution", {"plan_id": plan.id})
        with self.assertRaises(ValueError) as cm:
            self.pipe.advance("prod1", "publish", {"approval_id": "apr_pub"})
        self.assertIn("validation failed", str(cm.exception))

    def test_human_review_required_then_full_publish_path(self):
        self._to_validate(score=None)  # unscored → review needed
        with self.assertRaises(ValueError):
            self.pipe.advance("prod1", "review")
        self.pipe.advance("prod1", "review", {"reviewer": "grayson", "verdict": "ok"})
        self.pipe.advance("prod1", "assets")
        m = self.store.get_product("prod1")
        plan = D.build_plan(m, target_customer="moms", evidence=["https://x (2026-10-20)"], destination_url="https://www.etsy.com/listing/123")
        self.store.put_plan(plan)
        self.pipe.advance("prod1", "distribution", {"plan_id": plan.id})
        with self.assertRaises(ValueError) as cm:
            self.pipe.advance("prod1", "publish", {"approval_id": "apr_pub"})
        self.assertIn("plan is not approved", str(cm.exception))
        self.approved_publish()
        D.approve_plan(self.store, plan, "apr_pub")
        with self.assertRaises(ValueError):
            self.pipe.advance("prod1", "publish")  # approval id still required on the product step
        m = self.pipe.advance("prod1", "publish", {"approval_id": "apr_pub"})
        self.assertEqual((m.listing_status, m.distribution_status), ("listed", "published"))
        self.assertEqual(len(self.store.product_versions("prod1")), 6)  # one new version per stage, nothing overwritten

    def test_review_rejection(self):
        self._to_validate(score=None)
        m = self.pipe.advance("prod1", "review", {"reviewer": "grayson", "verdict": "no: cover looks fake"})
        self.assertEqual(m.listing_status, "rejected")


class TestDistribution(Base):
    def setUp(self):
        super().setUp()
        self.m = make_product(self.root)
        self.store.put_product(self.m)

    def test_plan_has_reasons_schedule_and_valid_destination(self):
        p = D.build_plan(self.m, target_customer="party hosts", evidence=["etsy search 'christmas games' 2026-10-18"], destination_url="https://www.etsy.com/listing/999",
                         start=datetime(2026, 11, 1, 6), days=2, holiday="Christmas")
        self.assertEqual([c.value for c in p.channels], ["pinterest", "tiktok", "facebook", "youtube_shop"])
        for c in p.channels:
            self.assertTrue(p.channel_reasons[c.value])
        for s in p.schedule:
            lo, hi = D.WINDOWS[Channel(s["channel"])]
            self.assertTrue(lo <= datetime.fromisoformat(s["at"]).hour <= hi)
        per_day = sum(1 for s in p.schedule if s["channel"] == "pinterest") / 2
        self.assertLessEqual(per_day, D.DAILY_CAP[Channel.PINTEREST])
        self.assertIn("Christmas", p.hypothesis)
        self.assertIn("verified sale", p.success_criteria)
        self.assertNotIn("gumroad", p.to_json())
        self.assertEqual(p.status, "planned")

    def test_plan_refuses_bad_inputs(self):
        with self.assertRaises(ValueError):
            D.build_plan(self.m, target_customer="x", evidence=[], destination_url="https://www.etsy.com/listing/1")
        with self.assertRaises(ValueError):
            D.build_plan(self.m, target_customer="x", evidence=["a link with no date"], destination_url="https://www.etsy.com/listing/1")
        with self.assertRaises(ValueError):
            D.build_plan(self.m, target_customer="x", evidence=["x 2026-10-01"], destination_url="https://gumroad.com/l/abc")

    def test_stage_order_and_approval(self):
        p = D.build_plan(self.m, target_customer="x", evidence=["x 2026-10-01"], destination_url="https://www.etsy.com/listing/1")
        self.store.put_plan(p)
        with self.assertRaises(ValueError):
            D.mark(self.store, p, "published")
        with self.assertRaises(ValueError):
            D.approve_plan(self.store, p, "nope")
        self.approved_publish()
        D.approve_plan(self.store, p, "apr_pub")
        D.mark(self.store, p, "scheduled")
        D.mark(self.store, p, "published")
        self.assertEqual(self.store.get_plan(p.id).status, "published")

    def test_funnel_and_results_never_fabricate(self):
        p = D.build_plan(self.m, target_customer="x", evidence=["x 2026-10-01"], destination_url="https://www.etsy.com/listing/1")
        self.store.put_plan(p)
        f = D.funnel(self.store, p)
        self.assertEqual((f["audience_reached"], f["clicks"], f["conversions_or_sales"]), ("unknown", "unknown", "unknown"))
        self.assertIn("measure first", f["next_action"])
        with self.assertRaises(ValueError):
            D.record_results(self.store, p, {"clicks": 0})  # an unreported zero is not a zero
        D.record_results(self.store, p, {"impressions": 1200, "clicks": 0, "measured": ["clicks"], "source": "pinterest analytics 2026-10-30"})
        f = D.funnel(self.store, p)
        self.assertEqual((f["audience_reached"], f["clicks"], f["conversions_or_sales"]), (1200, 0, "unknown"))
        self.assertIn("improve the hook", p.next_action)
        D.record_results(self.store, p, {"clicks": 40})
        self.assertIn("improve the listing", p.next_action)
        D.record_results(self.store, p, {"sales": 1, "source": "etsy payments 2026-11-02"})
        self.assertIn("repeat", p.next_action)


class TestHandlers(Base):
    def test_inspect_and_plan_steps_run_for_real(self):
        m = make_product(self.root)
        self.store.put_product(m)
        eng = TaskEngine(self.store, AGENTS, runner="test")
        for k, h in demo_handlers().items():
            eng.register(k, h)
        orc = Orchestrator(eng)
        p = orc.plan("promote_product", "products/prod1", meta={"copy": GOOD_COPY, "root": str(self.root), "score": 95, "target_customer": "party hosts",
                                                                  "evidence": ["etsy search 2026-10-18"], "destination_url": "https://www.etsy.com/listing/999"})
        eng.tick(max_tasks=1)  # distribution.plan (first step of promote_product)
        pr = orc.progress(p["id"])
        plan_row = next(r for r in pr["tasks"] if r["step"] == "plan")
        self.assertEqual(plan_row["status"], "succeeded")
        self.assertTrue(plan_row["output_ref"].startswith("plans/plan_"))
        # quality.inspect via launch_product on the same product: real validation, product advanced to 'validate'
        p2 = orc.plan("launch_product", "products/prod1", meta={"copy": GOOD_COPY, "root": str(self.root), "score": 95})
        eng.register("research.brief", lambda task, ctx: {"output_ref": "briefs/x"})
        eng.register("product.build", lambda task, ctx: {"output_ref": "products/prod1/v1"})
        for _ in range(8):
            eng.tick(max_tasks=1)
        row = next(r for r in orc.progress(p2["id"])["tasks"] if r["step"] == "inspect")
        self.assertEqual(row["status"], "succeeded", row)
        self.assertEqual(self.pipe.stage_of(self.store.get_product("prod1")), "validate")
        run = self.store.runs_for(row["task_id"])[-1]
        self.assertEqual(run.validation["gate"]["decision"], "approved")

    def test_inspect_rejects_bad_product_and_project_shows_why(self):
        m = make_product(self.root, content=b"garbage")
        self.store.put_product(m)
        eng = TaskEngine(self.store, AGENTS, runner="test")
        for k, h in demo_handlers().items():
            eng.register(k, h)
        eng.register("research.brief", lambda task, ctx: {"output_ref": "b"})
        eng.register("product.build", lambda task, ctx: {"output_ref": "p"})
        orc = Orchestrator(eng)
        p = orc.plan("launch_product", "products/prod1", meta={"copy": GOOD_COPY, "root": str(self.root), "score": 95})
        for _ in range(3):
            eng.tick(max_tasks=1)
        pr = orc.progress(p["id"])
        row = next(r for r in pr["tasks"] if r["step"] == "inspect")
        self.assertEqual(row["status"], "failed")
        self.assertIn("real pdf", row["blocked_by"][0])
        self.assertEqual(self.store.get_product("prod1").listing_status, "rejected")
        self.assertEqual(orc.verify(p["id"])["status"], "failed")


if __name__ == "__main__":
    unittest.main()
