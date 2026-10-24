"""Phase 9 tests: agent learning. Every check the brief asked for, mocked, temp folders only, no network, no model:
restart persistence, business / agent isolation, expiry, superseded sources, file ingestion, retrieval budget,
duplicate events, unchanged 92-point scoring, incomplete checks, critical failures, bounded repair, callback / tool
failures, version and test-vs-production separation, holdout cases never retrievable, hooks reached through the real
engine runner and through runlog.py / nb.py, the hourly worker's ingest step, and the legacy-vs-candidate comparison
on the saved real inspections."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

from factory.engine import Store, TaskEngine, TaskSpec, TaskStatus
from factory.engine.engine import PermanentError
from factory.engine.providers import MockProvider
from factory.engine.registry import AGENTS, demo_handlers, sync
from factory.engine.router import Router
from factory.learning import checks as C
from factory.learning import ingest as I
from factory.learning.brain import MAX_CONTEXT_CHARS, MAX_CONTEXT_ITEMS, AgentBrain
from factory.learning.improve import MAX_REPAIRS, improve, next_attempt
from factory.learning.panel import agent_panel, learning_section
from factory.learning.rubric import RUBRICS, assess, from_legacy_score, legacy_caps, rubric_id_of

REPO = Path(__file__).resolve().parents[3]
MM = REPO / "factory" / "stages" / "night-shift" / "output" / "2026-10-23-murder-mystery-build"
R2 = rubric_id_of(RUBRICS["etsy-product-r2"])


def pts(**kw):
    return {k: {"points": v, "evidence": f"evidence for {k}"} for k, v in kw.items()}


SANTA = dict(file=23, copy=19, images=19, market=13, price=9, polish=9)  # the real Oct 23 pass: 92


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / "db").open()
        self.brain = AgentBrain(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()


class TestRubric(unittest.TestCase):
    def test_frozen_weights_and_unchanged_92(self):
        r = assess(pts(**SANTA), "etsy-product-r2")
        self.assertEqual(r["score"], 92.0)
        self.assertTrue(r["passed"])
        self.assertEqual(r["rubric_id"], R2)
        self.assertEqual(RUBRICS["etsy-product-r2"]["criteria"], {"file": 25, "copy": 20, "images": 20, "market": 15, "price": 10, "polish": 10})
        self.assertEqual(RUBRICS["etsy-product-r2"]["target"], 92)
        # 91 stays 91 and fails; nothing is clamped upward
        r91 = assess(pts(**dict(SANTA, copy=18)), "etsy-product-r2")
        self.assertEqual(r91["score"], 91.0)
        self.assertFalse(r91["passed"])

    def test_missing_criterion_or_evidence_is_unscored(self):
        no_market = {k: v for k, v in pts(**SANTA).items() if k != "market"}
        r = assess(no_market, "etsy-product-r2")
        self.assertIsNone(r["score"])
        self.assertEqual(r["missing"], ["market"])
        self.assertFalse(r["passed"])
        blank = pts(**SANTA)
        blank["images"]["evidence"] = "   "
        self.assertEqual(assess(blank, "etsy-product-r2")["missing"], ["images"])
        with self.assertRaises(ValueError):
            assess({"nope": {"points": 1, "evidence": "x"}}, "etsy-product-r2")

    def test_critical_failure_blocks_even_a_high_total(self):
        r = assess(pts(file=25, copy=20, images=20, market=15, price=10, polish=10), "etsy-product-r2", blockers=["title over 140"])
        self.assertEqual(r["score"], 100.0)
        self.assertFalse(r["passed"])
        self.assertIn("title over 140", r["blockers"])

    def test_caps_only_move_down(self):
        r = assess(pts(**dict(SANTA, images=19, polish=9)), "etsy-product-r2", caps={"images": 12, "polish": 6})
        self.assertEqual(r["points"]["images"], 12.0)
        self.assertEqual(r["points"]["polish"], 6.0)
        self.assertEqual(len(r["capped"]), 2)
        r2 = assess(pts(**dict(SANTA, images=10)), "etsy-product-r2", caps={"images": 12})
        self.assertEqual(r2["points"]["images"], 10.0)  # a cap above the rating changes nothing
        r3 = assess(pts(**SANTA), "etsy-product-r2", caps={"total": 80})
        self.assertEqual(r3["score"], 80.0)
        self.assertFalse(r3["passed"])

    def test_legacy_adapter_keeps_points_and_reports_arithmetic(self):
        doc = {"rubric": 2, **SANTA, "total": 92, "rulesPass": True, "slopCheck": {"pass": True, "fails": []}, "verdict": "PASS 92"}
        leg = from_legacy_score(doc, "prod-santa-mail-bundle")
        self.assertEqual(assess(leg["ratings"], "etsy-product-r2", leg["blockers"], caps=legacy_caps(doc))["score"], 92.0)
        self.assertEqual(leg["discrepancies"], [])
        bad = dict(doc, total=95)
        self.assertTrue(any("!= sum" in d for d in from_legacy_score(bad)["discrepancies"]))
        murder = {"rubric": 2, "file": 22, "copy": 18, "images": 12, "market": 11, "price": 9, "polish": 6, "total": 78, "rulesPass": True,
                  "slopCheck": {"pass": False, "fails": ["(d) crop cuts footer"]}, "verdict": "FAIL 78"}
        leg = from_legacy_score(murder)
        r = assess(leg["ratings"], "etsy-product-r2", leg["blockers"], caps=legacy_caps(murder))
        self.assertEqual(r["score"], 78.0)
        self.assertFalse(r["passed"])
        self.assertTrue(any("slop" in b for b in r["blockers"]))

    def test_other_scales_have_their_own_rubric_ids(self):
        ids = {rubric_id_of(r) for r in RUBRICS.values()}
        self.assertEqual(len(ids), len(RUBRICS))
        judge = assess({k: {"points": v, "evidence": "e"} for k, v in dict(hook=9, story=8, twist=8, logic=8).items()}, "studio-judge-x10")
        self.assertEqual(judge["score"], 82.5)
        self.assertNotEqual(judge["rubric_id"], R2)


class TestChecks(unittest.TestCase):
    def test_copy_rules_and_slop_phrases(self):
        good = {"title": "Christmas Bingo Cards Printable, 50 Cards", "tags": [f"tag {i}" for i in range(13)], "description": "x" * 320 + "\n" + C.AI_LINE, "price": 3.99, "autocompleteChecked": True}
        res = {c["name"]: c for c in C.check_copy(good, "game")}
        self.assertTrue(res["title 1..140"]["ok"]); self.assertTrue(res["AI line present, exact, last"]["ok"]); self.assertTrue(res["price inside the lane range"]["ok"])
        bad = dict(good, title="T" * 141, tags=["a"] * 13, description="Elevate your Disney party, guaranteed sales — — — " * 10)
        res = {c["name"]: c for c in C.check_copy(bad, "game")}
        self.assertFalse(res["title 1..140"]["ok"]); self.assertEqual(res["title 1..140"]["severity"], "critical")
        self.assertFalse(res["exactly 13 tags of 20 max, unique"]["ok"])
        self.assertFalse(res["no AI-sounding phrases"]["ok"]); self.assertEqual(res["no AI-sounding phrases"]["severity"], "cap:slop_fail")
        self.assertFalse(res["original (no brand or character names)"]["ok"])
        self.assertFalse(res["AI line present, exact, last"]["ok"])

    def test_pdf_and_images_on_the_real_murder_mystery_artifacts(self):
        if not (MM / "christmas-murder-mystery-v2.pdf").exists():
            self.skipTest("real artifacts not in this checkout")
        info = C.pdf_info(MM / "christmas-murder-mystery-v2.pdf")
        self.assertTrue(info["header"])
        self.assertEqual(info["pages"], 17)
        self.assertEqual(C.image_size(MM / "cover_v2.jpg"), (2000, 1500))
        res = C.check_product(pdf=MM / "christmas-murder-mystery-v2.pdf", cover=MM / "cover_v2.jpg", previews=[MM / "photo2_v2.jpg", MM / "photo4_v2.jpg", MM / "photo5_v2.jpg"], lane="game",
                              copy={"title": "Christmas Murder Mystery Party Game for 8 Players", "tags": [f"t{i}" for i in range(13)], "description": "x" * 320 + "\n" + C.AI_LINE, "price": 7.99},
                              market={"listings": [{"url": "https://www.etsy.com/listing/1568083560", "itemReviews": 64, "price": 39.12}], "gap": "8 players"},
                              claims={"spoiler_terms": ["clem"], "public_pages": [2, 3]}, slop={"pass": True, "fails": []})
        names = {c["name"]: c for c in res["checks"]}
        self.assertTrue(names["thank-you page last"]["ok"])
        self.assertTrue(names["no spoiler on a host-facing page"]["ok"])
        self.assertIn("cover + 4 previews: cover + 3 previews", res["blockers"])  # only three previews were handed over
        self.assertFalse(names["at least one rival with 100+ item reviews"]["ok"])

    def test_missing_artifacts_block_unless_partial(self):
        full = C.check_product(copy=None, lane="game")
        self.assertTrue(any(b.startswith("pdf present") for b in full["blockers"]))
        part = C.check_product(copy=None, lane="game", partial=True)
        self.assertEqual(part["blockers"], [])
        self.assertTrue(all(c["ok"] is None for c in part["checks"]))

    def test_slop_fail_caps_and_market_without_evidence_is_unscored(self):
        res = C.check_product(partial=True, slop={"pass": False, "fails": ["(b) title twice"]}, market={"listings": []}, lane="game")
        self.assertEqual(res["caps"], {"images": 12, "polish": 6})
        self.assertTrue(any("slop check failed" in b for b in res["blockers"]))
        self.assertIn("market", res["unscored"])

    def test_post_checks(self):
        res = C.check_post(channel="facebook", caption="Real pages on a desk, link below", link="https://www.etsy.com/listing/1", slop_gate="pass", facts_checked=True)
        self.assertEqual(res["blockers"], [])
        bad = C.check_post(channel="tiktok", caption="x" * 151, link=None, slop_gate="fail", facts_checked=False)
        self.assertGreaterEqual(len(bad["blockers"]), 3)


class TestMemory(Base):
    def test_isolation_between_businesses_and_agents(self):
        self.brain.remember("shop", "atlas", "mistake", "cover title clipped in the square", "run 1")
        self.brain.remember("shop", "*", "lesson", "open 100+ review rivals before building", "LESSONS 10-23")
        self.brain.remember("studio", "judge", "mistake", "hook spoiled the twist", "run notes 10-21")
        self.brain.remember("shop", "forge", "mistake", "private to forge: cover square", "run 2")
        shop_atlas = self.brain.context("shop", "atlas", "cover square clipped rivals twist", record=False)
        self.assertTrue(all(m["scope"] == "shop" for m in shop_atlas))
        self.assertTrue(all(m["agent"] in ("atlas", "*") for m in shop_atlas))
        self.assertFalse(any("private to forge" in m["body"] for m in shop_atlas))
        studio = self.brain.context("studio", "judge", "cover square clipped rivals twist", record=False)
        self.assertEqual([m["scope"] for m in studio], ["studio"])
        self.assertIsNone(self.brain.memory(studio[0]["id"], "shop", "atlas"))  # the id does not bypass scope
        with self.assertRaises(ValueError):
            self.brain.context("shared", "*", "x")
        with self.assertRaises(ValueError):
            self.brain.remember("shared", "*", "lesson", "unverified cannot be shared", "x")
        with self.assertRaises(ValueError):
            self.brain.remember("grayson", "atlas", "fact", "rules are for everyone", "x")

    def test_grayson_rules_and_verified_shared_reach_every_business(self):
        self.brain.remember("grayson", "*", "fact", "Quality over volume: never ship slop", "business.md", tags={"authority": "grayson"})
        mid = self.brain.remember("shop", "*", "lesson", "a verified shared lesson about covers", "exp")
        self.brain.patch(mid, verified=1)
        self.brain.share(mid)
        for scope in ("shop", "studio", "trading"):
            kinds = {(m["scope"], m["kind"]) for m in self.brain.context(scope, "x", "slop covers quality", record=False)}
            self.assertIn(("grayson", "fact"), kinds)
            self.assertIn(("shared", "lesson"), kinds)

    def test_expiry(self):
        t = [time.time()]
        b = AgentBrain(self.store, clock=lambda: t[0])
        b.remember("shop", "atlas", "mistake", "an old mistake about pins", "run", ttl_days=1)
        self.assertEqual(len(b.context("shop", "atlas", "pins", record=False)), 1)
        t[0] += 2 * 86400
        self.assertEqual(b.context("shop", "atlas", "pins", record=False), [])
        self.assertEqual(b.freshness("shop", "atlas")["expired"], 1)

    def test_superseded_source_and_idempotent_ingest(self):
        f = self.root / "notes.md"
        f.write_text("# notes\nfirst version about covers and pins\n")
        r1 = self.brain.ingest_text("shop", f, rel_to=self.root)
        r1b = self.brain.ingest_text("shop", f, rel_to=self.root)
        self.assertTrue(r1b["unchanged"]); self.assertEqual(r1b["new"], [])
        f.write_text("# notes\nsecond version about covers and pins, now with badges\n")
        r2 = self.brain.ingest_text("shop", f, rel_to=self.root)
        self.assertEqual(r2["superseded"], len(r1["new"]))
        ctx = self.brain.context("shop", "x", "covers pins", record=False)
        self.assertEqual(len(ctx), 1)
        self.assertIn("second version", ctx[0]["body"])
        self.assertEqual(self.brain.get(r1["new"][0])["status"], "superseded")
        with self.assertRaises(ValueError):
            self.brain.ingest_text("shop", self.root / "x.pdf")

    def test_contradictions_are_listed_not_decided(self):
        self.brain.remember("shop", "*", "lesson", "Cream desk covers sell best", "old notebook")
        self.brain.remember("shop", "*", "mistake", "Cream desk covers sell best", "Grayson rejected them Oct 21")
        c = self.brain.contradictions("shop")
        self.assertEqual(len(c), 1)
        self.assertEqual(sorted(c[0]["kinds"]), ["lesson", "mistake"])

    def test_retrieval_budget_and_logging(self):
        for i in range(40):
            self.brain.remember("shop", "atlas", "observation", f"budget note {i} about covers " + "x" * 800, f"src {i}")
        items = self.brain.context("shop", "atlas", "covers budget", run_ref="job-7")
        self.assertLessEqual(len(items), MAX_CONTEXT_ITEMS)
        self.assertLessEqual(len(json.dumps(items, ensure_ascii=False, sort_keys=True)), MAX_CONTEXT_CHARS)
        small = self.brain.context("shop", "atlas", "covers budget", max_chars=1500, limit=3, record=False)
        self.assertLessEqual(len(small), 3)
        row = self.store.rows("SELECT * FROM retrievals WHERE run_ref='job-7'")
        self.assertEqual(len(row), 1)
        self.assertEqual(len(json.loads(row[0]["memory_ids"])), len(items))
        self.assertEqual(self.brain.context("shop", "atlas", "", record=False)[0]["kind"], "observation")  # recency mode, no terms

    def test_holdout_cases_and_chunks_are_never_retrievable(self):
        cid = self.brain.eval_case_put("shop", "atlas", split="holdout", task={"title": "Secret Holdout Kit"}, expected={"total": 92}, source="test")
        self.brain.remember("shop", "*", "example", "Inspect: Secret Holdout Kit PASS 92 file 23", "run notes", tags={"holdout": 1})
        self.brain.remember("shop", "*", "example", "Inspect: Visible Kit FAIL 83", "run notes")
        bodies = [m["body"] for m in self.brain.context("shop", "atlas", "Secret Holdout Kit Inspect", record=False)]
        self.assertFalse(any("Secret Holdout" in b for b in bodies))
        self.assertTrue(any("Visible Kit" in b for b in bodies))
        with self.assertRaises(ValueError):
            self.brain.eval_case_put("shop", "atlas", split="test", task={}, expected={}, source="x")
        self.assertEqual(self.brain.eval_cases("shop", split="holdout")[0]["id"], cid)


class TestEvaluations(Base):
    def test_duplicate_run_ids(self):
        res = assess(pts(**SANTA), "etsy-product-r2")
        self.brain.log("job:0", "shop", "atlas", "v1", "task", "artifact", res, mode="offline")
        self.brain.log("job:0", "shop", "atlas", "v1", "task", "artifact", res, mode="offline")  # same content: no-op
        self.assertEqual(len(self.store.rows("SELECT id FROM evaluations")), 1)
        with self.assertRaises(ValueError):
            self.brain.log("job:0", "shop", "atlas", "v1", "task", "artifact", assess(pts(**dict(SANTA, copy=18)), "etsy-product-r2"), mode="offline")
        with self.assertRaises(ValueError):
            self.brain.log("job:1", "shop", "atlas", "v1", "task", "artifact", res, mode="staging")

    def test_runs_and_errors_record_no_score(self):
        self.brain.log_run("runlog:bolt:t1", "shop", "bolt", task="bolt", outcome="failed", note="403", needs_you="GitHub access needs a look", est_tokens=1200)
        self.brain.log_error("task9:0", "shop", "scout", task="x", error="budget exceeded", error_class="budget")
        rows = {r["id"]: r for r in self.store.rows("SELECT id, kind, score, passed FROM evaluations")}
        self.assertIsNone(rows["runlog:bolt:t1"]["score"]); self.assertEqual(rows["runlog:bolt:t1"]["passed"], 0)
        self.assertEqual(rows["task9:0"]["kind"], "error"); self.assertIsNone(rows["task9:0"]["score"])
        st = {g["kind"]: g for g in self.brain.stats("shop")}
        self.assertEqual(st["error"]["errors"], 1)
        self.assertEqual(st["run"]["scored"], 0)

    def test_version_mode_and_rubric_separation_in_stats(self):
        r = assess(pts(**SANTA), "etsy-product-r2")
        self.brain.log("a:0", "shop", "atlas", "v1", "t", "x", r, mode="production")
        self.brain.log("b:0", "shop", "atlas", "v1", "t", "x", r, mode="offline")
        self.brain.log("c:0", "shop", "atlas", "v2", "t", "x", assess(pts(**dict(SANTA, copy=18)), "etsy-product-r2"), mode="production")
        self.brain.log("d:0", "shop", "atlas", "v1", "t", "x", assess({k: {"points": 8, "evidence": "e"} for k in ("hook", "story", "twist", "logic")}, "studio-judge-x10"), mode="production")
        groups = {(g["version"], g["mode"], g["rubric"]): g for g in self.brain.stats("shop", "atlas")}
        self.assertEqual(len(groups), 4)
        self.assertEqual(groups[("v1", "production", R2)]["mean_score"], 92.0)
        self.assertEqual(groups[("v2", "production", R2)]["mean_score"], 91.0)
        self.assertEqual(groups[("v1", "offline", R2)]["completed"], 1)
        prod_panel = agent_panel(self.brain, "shop", "atlas", "production")
        off_panel = agent_panel(self.brain, "shop", "atlas", "offline")
        self.assertEqual(prod_panel["scored_samples"], 3); self.assertEqual(off_panel["scored_samples"], 1)
        self.assertEqual(len(prod_panel["by_rubric"]), 3)  # two versions of r2 + the judge rubric, never merged

    def test_restart_persistence_rebuilds_everything_from_the_journal(self):
        mid = self.brain.remember("shop", "atlas", "lesson", "persisted lesson about covers", "src")
        self.brain.patch(mid, verified=1)
        self.brain.log("job:0", "shop", "atlas", "v1", "t", "x", assess(pts(**SANTA), "etsy-product-r2"), mode="production")
        key = self.brain.propose("shop", "atlas", {"hypothesis": "h", "change": "c", "baseline": "b", "metric": "m", "success": "s", "stop": "st", "budget": "0", "sources": ["job:0"]})
        eid = self.brain.experiment_start(key, baseline={"v": 1}, metric="m", success="s", stop="st", budget="0")
        self.brain.workflow_put("shop", "atlas", "prompt", {"t": 1}, status="active")
        self.brain.context("shop", "atlas", "covers", run_ref="job")
        self.store.close()
        (self.root / "db" / "state.sqlite").unlink()
        st2 = Store(self.root / "db").open()
        b2 = AgentBrain(st2)
        self.assertEqual(b2.get(mid)["verified"], 1)
        self.assertEqual(b2.stats("shop")[0]["mean_score"], 92.0)
        self.assertEqual(b2.idea(key)["status"], "running")
        self.assertEqual(b2.experiment(eid)["status"], "running")
        self.assertEqual(b2.workflow_active("shop", "atlas", "prompt")["version"], 1)
        self.assertEqual(len(st2.rows("SELECT id FROM retrievals")), 1)
        st2.close()
        self.store = Store(self.root / "db").open()


class TestImprove(Base):
    def judge_factory(self, scores_by_version):
        def judge(draft):
            v = int(draft["v"])
            s = scores_by_version[min(v, len(scores_by_version) - 1)]
            return {"ratings": pts(**s)}
        return judge

    def test_bounded_repairs_stop_at_pass(self):
        make = lambda task, mem: {"v": 0}  # noqa: E731
        repair = lambda draft, result, mem: {"v": draft["v"] + 1, "plan": result["repair_plan"]}  # noqa: E731
        tr = improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=make, judge=self.judge_factory([dict(SANTA, market=9), dict(SANTA, market=11), SANTA]), repair=repair, job_id="j1")
        self.assertEqual([a["score"] for a in tr["attempts"]], [88.0, 90.0, 92.0])
        self.assertEqual(tr["stopped"], "passed")
        self.assertEqual(tr["draft"]["plan"]["fix_first"][0]["criterion"], "market")
        rows = self.store.rows("SELECT id, final, passed FROM evaluations WHERE task_id='j1' ORDER BY attempt")
        self.assertEqual([(r["final"], r["passed"]) for r in rows], [(0, 0), (0, 0), (1, 1)])
        self.assertEqual(next_attempt(self.brain, "j1"), -1)

    def test_bound_is_two_repairs_and_a_92_stays_92(self):
        make = lambda task, mem: {"v": 0}  # noqa: E731
        repair = lambda draft, result, mem: {"v": draft["v"] + 1}  # noqa: E731
        tr = improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=make, judge=self.judge_factory([dict(SANTA, market=9), dict(SANTA, market=10), dict(SANTA, market=11), SANTA]), repair=repair, job_id="j2")
        self.assertEqual(len(tr["attempts"]), MAX_REPAIRS + 1)
        self.assertEqual(tr["stopped"], "limit")
        self.assertEqual(tr["result"]["score"], 90.0)
        self.assertFalse(tr["result"]["passed"])
        with self.assertRaises(ValueError):
            improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=make, judge=self.judge_factory([SANTA]), repair=repair, max_repairs=3)
        # the judge is never told the target: the callback gets only the draft
        seen = []
        improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=make, judge=lambda d: (seen.append(d), {"ratings": pts(**SANTA)})[1], repair=repair, job_id="j3")
        self.assertEqual(seen, [{"v": 0}])

    def test_critical_check_blocks_and_mistake_memory_is_left(self):
        checks = lambda draft: {"blockers": ["real pdf header: header is not %PDF"], "caps": {}, "unscored": [], "notes": {}, "summary": {"checks": 1, "failed": 1, "unknown": 0, "critical": 1, "caps": {}}}  # noqa: E731
        tr = improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=lambda t, m: {"v": 0}, judge=self.judge_factory([dict(file=25, copy=20, images=20, market=15, price=10, polish=10)]),
                     repair=lambda d, r, m: d, checks=checks, job_id="j4", max_repairs=0)
        self.assertEqual(tr["result"]["score"], 100.0)
        self.assertFalse(tr["result"]["passed"])
        self.assertTrue(self.store.rows("SELECT id FROM memories WHERE kind='mistake' AND agent='atlas'"))

    def test_callback_failures_record_errors_without_a_score(self):
        def boom(*a):
            raise RuntimeError("tool exploded")
        tr = improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=boom, judge=lambda d: {}, repair=lambda d, r, m: d, job_id="e1")
        self.assertEqual(tr["stopped"], "error")
        tr2 = improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=lambda t, m: {"v": 0}, judge=boom, repair=lambda d, r, m: d, job_id="e2")
        self.assertEqual(tr2["stopped"], "error")
        tr3 = improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=lambda t, m: {"v": 0}, judge=self.judge_factory([dict(SANTA, market=9)]), repair=boom, job_id="e3")
        self.assertEqual(tr3["stopped"], "error")
        self.assertEqual(tr3["result"]["score"], 88.0)
        errs = self.store.rows("SELECT id, score FROM evaluations WHERE kind='error'")
        self.assertEqual(len(errs), 3)
        self.assertTrue(all(r["score"] is None for r in errs))

    def test_time_budget_closes_the_job_with_the_blocker_recorded(self):
        t = [0.0]
        def clock():
            t[0] += 40
            return t[0]
        tr = improve(self.brain, scope="shop", agent="atlas", task="t", version="v1", make=lambda a, m: {"v": 0}, judge=self.judge_factory([dict(SANTA, market=9)]), repair=lambda d, r, m: {"v": 1},
                     job_id="b1", max_seconds=30, clock=clock)
        self.assertEqual(tr["stopped"], "budget")
        self.assertTrue(any("time budget" in b for b in tr["result"]["blockers"]))
        self.assertEqual(len(tr["attempts"]), 1)


class TestIdeasExperimentsPromotion(Base):
    def setUp(self):
        super().setUp()
        self.brain.log("fail:0", "shop", "atlas", "v1", "t", "x", assess(pts(**dict(SANTA, market=9)), "etsy-product-r2"), mode="production")
        self.idea = {"hypothesis": "market caps at 11 without an opened 100+ rival", "change": "02-judge requires two opened 100+ item pages", "baseline": "Oct 21-23 briefs", "metric": "market points",
                     "success": "median >= 13 over 3 builds", "stop": "3 builds", "budget": "0 calls", "sources": ["fail:0"]}

    def test_propose_validates_dedupes_and_budgets(self):
        with self.assertRaises(ValueError):
            self.brain.propose("shop", "atlas", {k: v for k, v in self.idea.items() if k != "budget"})
        with self.assertRaises(ValueError):
            self.brain.propose("shop", "atlas", dict(self.idea, sources=["not-a-real-id"]))
        k1 = self.brain.propose("shop", "atlas", self.idea)
        k2 = self.brain.propose("shop", "scout", dict(self.idea, change="  02-JUDGE requires two opened 100+ item pages "))
        self.assertEqual(k1, k2)  # same change, two agents: one idea
        self.brain.propose("shop", "atlas", dict(self.idea, change="change two"))
        self.brain.propose("shop", "atlas", dict(self.idea, change="change three"))
        with self.assertRaises(ValueError):
            self.brain.propose("shop", "atlas", dict(self.idea, change="change four"))
        self.assertEqual(len(self.brain.ideas("studio")), 0)

    def test_experiment_needs_samples_baseline_and_no_conflict_then_promotion_and_rollback(self):
        k = self.brain.propose("shop", "atlas", self.idea)
        eid = self.brain.experiment_start(k, baseline={"workflow": "02-judge v10-23"}, metric="market points", success="median>=13", stop="3 builds", budget="0")
        with self.assertRaises(ValueError):
            self.brain.experiment_decide(eid, "keep", by="atlas")  # 0 samples
        self.brain.experiment_record(eid, arm="candidate", value=13, n=1, source="run notes 10-24")
        with self.assertRaises(ValueError):
            self.brain.experiment_decide(eid, "keep", by="atlas")  # a one-off is not proof
        self.brain.experiment_record(eid, arm="candidate", value=14, n=2, source="run notes 10-25")
        with self.assertRaises(ValueError):
            self.brain.experiment_decide(eid, "keep", by="atlas")  # no baseline result yet
        self.brain.experiment_record(eid, arm="baseline", value=11, n=3, source="scores 10-23")
        self.brain.experiment_record(eid, arm="candidate", value=9, n=1, source="run notes 10-26", conflict=True)
        with self.assertRaises(ValueError):
            self.brain.experiment_decide(eid, "keep", by="atlas")  # open conflict
        self.brain.experiment_resolve_conflicts(eid, "atlas", "the 9 was a wall-art brief, a different lane")
        e = self.brain.experiment_decide(eid, "keep", by="atlas", note="median 13.5 over 4")
        self.assertEqual(e["decision"], "keep")
        self.assertEqual(self.brain.idea(k)["status"], "decided")
        # a lesson is verified only through the kept experiment (or Grayson's call); then it may be shared
        mid = self.brain.remember("shop", "*", "lesson", "Open two 100+ review rivals before building", "pending")
        with self.assertRaises(ValueError):
            self.brain.verify(mid)
        with self.assertRaises(ValueError):
            self.brain.verify(mid, by="atlas", reason="I think so")
        self.brain.verify(mid, experiment_id=eid, by="atlas")
        self.assertTrue(self.brain.get(mid)["verified"])
        sid = self.brain.share(mid)
        self.assertEqual(self.brain.get(sid)["scope"], "shared")
        # workflow versions: promote only on a kept experiment; the old version stays for rollback
        v1 = self.brain.workflow_put("shop", "atlas", "inspect-prompt", "v1 text", status="active")
        v2 = self.brain.workflow_put("shop", "atlas", "inspect-prompt", "v2 text")
        with self.assertRaises(ValueError):
            self.brain.workflow_promote("shop", "atlas", "inspect-prompt", 2, experiment_id="exp_nope")
        self.brain.workflow_promote("shop", "atlas", "inspect-prompt", 2, experiment_id=eid)
        self.assertEqual(self.brain.workflow_active("shop", "atlas", "inspect-prompt")["version"], 2)
        self.assertEqual([v["status"] for v in self.brain.workflow_versions("shop", "atlas", "inspect-prompt")], ["retired", "active"])
        self.brain.workflow_rollback("shop", "atlas", "inspect-prompt", 1, by="grayson", reason="v2 lost on holdout")
        self.assertEqual(self.brain.workflow_active("shop", "atlas", "inspect-prompt")["version"], 1)
        self.assertEqual(len(self.brain.workflow_versions("shop", "atlas", "inspect-prompt")), 2)
        self.assertIsNotNone(v1["id"]); self.assertIsNotNone(v2["id"])

    def test_hypothesis_is_never_verified(self):
        h = self.brain.remember("shop", "*", "hypothesis", "video pins beat still pins", "testing line")
        with self.assertRaises(ValueError):
            self.brain.verify(h, by="grayson", reason="feels right")


class TestRealSourcesAndComparison(Base):
    def test_ingest_real_repo_sources_idempotently_and_compare_cases(self):
        if not (REPO / "factory" / "notebook" / "etsy.md").exists():
            self.skipTest("repo files missing")
        out = I.ingest_all(self.brain, REPO, only=["notebook", "lessons", "misses", "runnotes", "scores"])
        s = I.summarize(out)
        self.assertGreater(s["notebook"]["new"], 20)
        self.assertGreaterEqual(s["runnotes"]["cases_train"] + s["runnotes"]["cases_holdout"], 6)
        self.assertGreaterEqual(s["scores"]["new"], 3)  # the idea scores; atlas totals that duplicate a run-notes inspection are skipped
        atlas_scores = self.store.rows("SELECT id, score FROM evaluations WHERE agent='atlas' AND kind='score'")
        self.assertTrue(all(r["id"].startswith("runnotes:") for r in atlas_scores), atlas_scores)  # one row per real inspection, with its breakdown
        self.assertEqual(len(atlas_scores), 6)
        again = I.summarize(I.ingest_all(self.brain, REPO, only=["notebook", "lessons", "misses", "runnotes", "scores"]))
        self.assertEqual(sum(v["new"] for v in again.values()), 0)
        # Grayson's rules carry authority; "What works" arrives as a CLAIMED lesson, not verified
        rules = self.store.rows("SELECT body FROM memories WHERE scope='grayson' AND kind='fact'")
        self.assertTrue(any("Quality over volume" in r["body"] for r in rules))
        claimed = self.store.rows("SELECT verified, confidence FROM memories WHERE kind='lesson' AND source_path LIKE 'factory/notebook/%'")
        self.assertTrue(claimed and all(r["verified"] == 0 for r in claimed))
        # legacy vs candidate on the saved real inspections: same totals, nothing raised, on both splits
        for split in ("train", "holdout"):
            cmp = I.compare_cases(self.brain, split)
            self.assertGreaterEqual(cmp["n"], 2)
            self.assertFalse(cmp["any_raised"])
            for r in cmp["rows"]:
                self.assertEqual(r["candidate_score"], r["legacy_total"])
        santa = [r for r in I.compare_cases(self.brain, "train")["rows"] if r["legacy_total"] == 92]
        self.assertTrue(santa and santa[0]["candidate_pass"])
        # the holdout inspections are not in retrievable memory
        hold_titles = [c["task"]["title"] for c in self.brain.eval_cases("shop", split="holdout")]
        for ti in hold_titles:
            for m in self.brain.context("shop", "atlas", ti, record=False):
                self.assertNotIn(f"Inspect: {ti}", m["body"])


class TestHooksThroughRealPaths(Base):
    def engine(self, provider=None):
        sync(self.store)
        eng = TaskEngine(self.store, AGENTS, runner="test", router=Router(self.store, providers=[provider or MockProvider()]))
        for k, h in demo_handlers().items():
            eng.register(k, h)
        return eng

    def test_engine_runner_records_score_error_and_recall(self):
        eng = self.engine()
        spec = TaskSpec(agent_id="atlas", kind="quality.score", input_ref="products/p1", tools=["files.read", "artifact_db.read"],
                        meta={"ratings": pts(**SANTA), "copy": None, "lane": "game", "item": "test kit", "mode": "offline", "partial": True})
        # no artifacts at all: pdf / cover / copy missing are blockers (not partial in the handler): the item cannot pass
        t = eng.submit(spec)
        run = eng.tick()[0]
        self.assertEqual(run.status, TaskStatus.SUCCEEDED)
        self.assertEqual(run.validation.get("memory_items"), 0)
        rows = self.store.rows("SELECT id, kind, agent, score, passed, mode FROM evaluations")
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["kind"], rows[0]["agent"], rows[0]["mode"]), ("score", "atlas", "offline"))
        self.assertEqual(rows[0]["passed"], 0)
        self.assertTrue(self.store.rows("SELECT id FROM retrievals WHERE run_ref=?", (t.id,)))
        # a failing handler leaves an error row with no score and a mistake memory; the task fails as before
        eng.register("engine.boom", lambda task, ctx: (_ for _ in ()).throw(PermanentError("tool exploded")))
        eng.submit(TaskSpec(agent_id="scout", kind="engine.boom", input_ref="in/2"))
        eng.tick()
        err = self.store.rows("SELECT id, score FROM evaluations WHERE kind='error'")
        self.assertEqual(len(err), 1); self.assertIsNone(err[0]["score"])
        self.assertTrue(self.store.rows("SELECT id FROM memories WHERE kind='mistake' AND agent='scout'"))
        # replaying the journal does not duplicate the rows
        n = len(self.store.rows("SELECT id FROM evaluations"))
        self.store.rebuild()
        self.assertEqual(len(self.store.rows("SELECT id FROM evaluations")), n)

    def test_engine_diagnose_queues_ideas_through_the_router_with_real_sources(self):
        self.brain.log("fail:0", "shop", "atlas", "v1", "t", "x", assess(pts(**dict(SANTA, market=9)), "etsy-product-r2"), mode="production")
        reply = json.dumps([{"hypothesis": "h", "change": "require opened rivals", "baseline": "b", "metric": "market", "success": "13+", "stop": "3 builds", "budget": "0", "sources": ["fail:0"]},
                            {"hypothesis": "h2", "change": "no sources", "baseline": "b", "metric": "m", "success": "s", "stop": "st", "budget": "0", "sources": ["ghost"]}])
        eng = self.engine(MockProvider(script={"You improve one agent": reply}))
        eng.submit(TaskSpec(agent_id="foreman", kind="learning.diagnose", input_ref="agents/atlas", tools=["artifact_db.read"], meta={"for_agent": "atlas", "scope": "shop"}))
        run = eng.tick()[0]
        self.assertEqual(run.status, TaskStatus.SUCCEEDED)
        self.assertIn("queued 1", run.validation["checks"])
        self.assertEqual(len(self.brain.ideas("shop", status="proposed")), 1)
        self.assertEqual(self.store.usage_summary()["calls"], 1)  # exactly one bounded model call

    def test_runlog_add_and_nb_show_hooks_via_subprocess(self):
        env = dict(os.environ, GM_ENGINE_DB_DIR=str(self.root / "db"))
        tmp_log = self.root / "runlog.jsonl"
        # runlog.py writes factory/runlog.jsonl in the repo; point it at a temp copy by running a copy of the module
        src = (REPO / "factory" / "shared" / "runlog.py").read_text().replace('LOG = os.path.join(ROOT, "factory", "runlog.jsonl")', f'LOG = {str(tmp_log)!r}')
        mod = self.root / "runlog_copy.py"
        mod.write_text(src.replace('ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))', f'ROOT = {str(REPO)!r}'))
        args = [sys.executable, str(mod), "add", "--task", "bolt", "--started", "2026-10-24T12:00:00Z", "--finished", "2026-10-24T12:03:00Z", "--outcome", "failed", "--note", "smoke", "--needs-you", "fix me"]
        o1 = subprocess.run(args, capture_output=True, text=True, env=env, cwd=str(REPO)).stdout
        o2 = subprocess.run(args, capture_output=True, text=True, env=env, cwd=str(REPO)).stdout
        self.assertIn('"learning": "runlog:bolt:2026-10-24T12:00:00Z"', o1)
        self.assertIn('"learning": "runlog:bolt:2026-10-24T12:00:00Z"', o2)
        self.store.close(); self.store = Store(self.root / "db").open(); self.brain = AgentBrain(self.store)
        self.store.rebuild()
        self.assertEqual(len(self.store.rows("SELECT id FROM evaluations WHERE kind='run'")), 1)
        self.assertTrue(self.store.rows("SELECT id FROM memories WHERE kind='mistake' AND agent='bolt'"))
        self.brain.remember("shop", "forge", "mistake", "Santa letters: third of the page empty, text 12.6 pt fixed it", "run notes 10-23")
        out = subprocess.run([sys.executable, str(REPO / "factory" / "notebook" / "nb.py"), "show", "--lane", "etsy", "--agent", "forge", "--task", "Santa letters page empty"],
                             capture_output=True, text=True, env=env, cwd=str(REPO)).stdout
        self.assertIn("## Relevant memory (shop/forge: 1 chunks", out)
        self.assertIn("third of the page empty", out)
        off = subprocess.run(args, capture_output=True, text=True, env=dict(env, GM_LEARNING_OFF="1"), cwd=str(REPO)).stdout
        self.assertNotIn('"learning"', off)

    def test_worker_learning_step_and_report_section(self):
        from factory.engine.cli import _learning_step
        from factory.engine.report import build_report
        res = _learning_step(self.store)
        self.assertIn("ingested", res)
        eng = self.engine()
        rep = build_report(self.store, eng)
        self.assertIn("learning", rep)
        self.assertIn("production", rep["learning"])
        self.assertIn("unknowns", rep["learning"])
        json.dumps(rep)  # serialisable, as the page needs it
        sec = learning_section(self.brain)
        self.assertEqual(sec["eval_cases"]["train"] + sec["eval_cases"]["holdout"], len(self.brain.eval_cases()))


class TestCli(Base):
    def run_cli(self, *args):
        from factory.learning.learn import main
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--db", str(self.root / "db"), *args])
        return rc, buf.getvalue()

    def test_score_bound_and_outputs(self):
        ratings = json.dumps(pts(**dict(SANTA, market=9)))
        copy = json.dumps({"title": "T", "tags": [f"t{i}" for i in range(13)], "description": "x" * 320 + "\n" + C.AI_LINE, "price": 4.99})
        market = json.dumps({"listings": [{"url": "https://www.etsy.com/listing/1", "itemReviews": 120, "price": 3.99}], "gap": "g"})
        common = ["score", "--scope", "shop", "--agent", "atlas", "--job", "run-x:p1", "--item", "kit", "--lane", "game", "--mode", "offline", "--ratings", ratings, "--copy", copy, "--market", market, "--partial", "--json"]
        rc, out = self.run_cli(*common)
        d = json.loads(out)
        self.assertEqual(rc, 1); self.assertEqual(d["score"], 88.0); self.assertFalse(d["final"]); self.assertEqual(d["recorded"], "run-x:p1:0")
        self.assertEqual(d["repair_plan"]["fix_first"][0]["criterion"], "market")
        rc, out = self.run_cli(*common); self.assertEqual(json.loads(out)["recorded"], "run-x:p1:1")
        rc, out = self.run_cli(*common); d = json.loads(out); self.assertEqual(d["recorded"], "run-x:p1:2"); self.assertTrue(d["final"])
        rc, out = self.run_cli(*common); self.assertEqual(rc, 2); self.assertIn("closed", json.loads(out)["error"])
        self.assertEqual(len(self.store.rows("SELECT id FROM evaluations WHERE task_id='run-x:p1'")), 3)
        rc, out = self.run_cli("score", "--scope", "shop", "--agent", "atlas", "--mode", "offline", "--legacy", json.dumps({"rubric": 2, **SANTA, "total": 92, "rulesPass": True, "slopCheck": {"pass": True, "fails": []}}), "--json")
        self.assertEqual(rc, 0); self.assertEqual(json.loads(out)["score"], 92.0)

    def test_recall_run_panel_and_anchors(self):
        rc, out = self.run_cli("run", "--scope", "shop", "--agent", "bolt", "--run-id", "r1", "--task", "bolt", "--outcome", "failed", "--note", "403 on push", "--est-tokens", "1500")
        self.assertEqual(rc, 0)
        rc, out = self.run_cli("recall", "--scope", "shop", "--agent", "bolt", "--task", "push 403")
        self.assertIn("403 on push", out)
        rc, out = self.run_cli("panel", "--scope", "shop", "--agent", "bolt")
        self.assertIn("runs 1", out)
        rc, out = self.run_cli("anchors")
        self.assertIn("## market (0 to 15)", out)
        self.assertNotIn("92", out)  # the reviewer anchors never state the pass mark


if __name__ == "__main__":
    unittest.main()
