"""Agent contracts for the existing crews (Phase 3: contracts only; Phase 4 wires the orchestrator).

Each contract names the real crew that already does the job, the tools it may touch, the consequential
capabilities it may ask for (each still needs an approval id at run time), its timeout and its budget.
Nobody gets TRADE_LIVE. No Gumroad, no Funnel, no Ridgeline.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .contracts import AgentContract, AgentRole, Budget, Capability, ErrorPolicy

REPO = Path(__file__).resolve().parents[2]

# tools are *names*; a handler calls ctx.use_tool(name) before touching anything outside the repo
T_WEB = ["web.search", "web.fetch"]
T_DB = ["artifact_db.read", "artifact_db.write"]
T_GIT = ["git.read", "git.commit"]
T_MAKE = ["make.scenario_run"]
T_GW = ["gateway.job"]  # gw/jobs/<id>.json → GitHub Actions gateway (Etsy, Zernio)
T_VIDIQ = ["vidiq.read", "vidiq.update_video"]
T_FILES = ["files.read", "files.write"]

AGENTS: dict[str, AgentContract] = {a.id: a for a in [
    AgentContract(id="foreman", name="The Foreman", role=AgentRole.ORCHESTRATOR,
                  responsibilities=["break goals into tasks", "build the dependency graph", "assign to agents", "track blocked work", "verify before marking done"],
                  inputs=["goal", "fleet_state"], outputs=["task_graph", "verdict"], tools=T_DB + ["git.read"],
                  error_policy=ErrorPolicy(max_retries=1, timeout_s=900), budget=Budget(max_calls_per_task=40),
                  skill_path="factory/skills/foreman/SKILL.md"),
    AgentContract(id="scout", name="Scout", role=AgentRole.RESEARCH,
                  responsibilities=["15 ideas → 3 briefs with 2+ dated evidence links", "mark estimates as estimates", "say unknown instead of inventing"],
                  inputs=["lane", "holiday_state"], outputs=["brief"], tools=T_WEB + T_DB,
                  error_policy=ErrorPolicy(max_retries=2, timeout_s=1200), budget=Budget(max_calls_per_task=60),
                  skill_path="factory/skills/scout/SKILL.md"),
    AgentContract(id="forge", name="Forge + Quill + Lens", role=AgentRole.PRODUCT_FACTORY,
                  responsibilities=["build the file, copy and photos to the lane spec", "write a versioned manifest", "validate before handing to QC"],
                  inputs=["brief"], outputs=["product_manifest"], tools=T_FILES + T_DB + T_GIT,
                  error_policy=ErrorPolicy(max_retries=2, timeout_s=1800), budget=Budget(max_calls_per_task=30),
                  skill_path="factory/skills/forge/SKILL.md"),
    AgentContract(id="atlas", name="Atlas (inspection)", role=AgentRole.QUALITY,
                  responsibilities=["rubric v2, 90+ and rules pass/fail", "reject incomplete or unsupported work", "re-check after fixes"],
                  inputs=["product_manifest"], outputs=["scorecard"], tools=T_DB + T_FILES,
                  error_policy=ErrorPolicy(max_retries=1, timeout_s=600), budget=Budget(max_calls_per_task=20),
                  skill_path="factory/skills/atlas/SKILL.md"),
    AgentContract(id="hawk", name="Hawk + Santa", role=AgentRole.DISTRIBUTION,
                  responsibilities=["plan from the numbers", "choose channels with a reason each", "one measurable hypothesis per plan", "holiday share"],
                  inputs=["product_manifest", "stats"], outputs=["distribution_plan"], tools=T_DB,
                  error_policy=ErrorPolicy(max_retries=1, timeout_s=600), budget=Budget(max_calls_per_task=20),
                  skill_path="factory/skills/hawk/SKILL.md"),
    AgentContract(id="herald", name="Herald + Pixel + Tick", role=AgentRole.CHANNEL_ADAPTER,
                  responsibilities=["one source asset → channel versions (Pinterest, IG, FB, TikTok, shop YouTube)", "respect each platform's rules", "92+ or rewrite once"],
                  inputs=["distribution_plan"], outputs=["channel_assets"], tools=T_FILES + T_DB,
                  error_policy=ErrorPolicy(max_retries=2, timeout_s=1200), budget=Budget(max_calls_per_task=40),
                  skill_path="factory/skills/herald/SKILL.md"),
    AgentContract(id="bolt", name="Bolt + Rocket", role=AgentRole.PUBLISHING,
                  responsibilities=["publish only through authorized integrations", "verify status when the platform allows", "draft when an integration is missing; never claim 'published' for a draft"],
                  inputs=["channel_assets", "approval"], outputs=["publication"], tools=T_GW + T_MAKE + T_VIDIQ + T_DB,
                  capabilities=[Capability.PUBLISH_PUBLIC],
                  error_policy=ErrorPolicy(max_retries=3, timeout_s=900), budget=Budget(max_calls_per_task=25),
                  skill_path="factory/skills/bolt/SKILL.md"),
    AgentContract(id="graph", name="Graph + Medic (analytics)", role=AgentRole.ANALYTICS,
                  responsibilities=["read real impressions/views/clicks/saves/sales", "compare across channels and time", "unknown stays unknown", "separate hypotheses from results"],
                  inputs=["publication"], outputs=["metrics", "lesson"], tools=T_MAKE + T_VIDIQ + T_GW + T_DB,
                  error_policy=ErrorPolicy(max_retries=2, timeout_s=900), budget=Budget(max_calls_per_task=30),
                  skill_path="factory/skills/graph/SKILL.md"),
    AgentContract(id="ledger", name="Ledger (model + cost)", role=AgentRole.MODEL_COST,
                  responsibilities=["route by complexity (Phase 5)", "cache safe repeatable work", "track real usage; estimates labelled", "enforce budgets and stop runaway loops"],
                  inputs=["task"], outputs=["route", "usage"], tools=T_DB,
                  error_policy=ErrorPolicy(max_retries=0, timeout_s=120), budget=Budget(max_calls_per_task=5),
                  skill_path="factory/skills/ledger/SKILL.md"),
    AgentContract(id="mechanic", name="Mechanic", role=AgentRole.ENGINEERING,
                  responsibilities=["inspect code, run tests, detect regressions", "small reversible steps", "never weaken a safeguard to make a test pass"],
                  inputs=["repo"], outputs=["report", "fix"], tools=T_GIT + T_FILES + T_DB,
                  capabilities=[Capability.DESTRUCTIVE_CHANGE],
                  error_policy=ErrorPolicy(max_retries=1, timeout_s=1800), budget=Budget(max_calls_per_task=60),
                  skill_path="factory/skills/medic/SKILL.md"),
]}


def _without_version(a: AgentContract) -> dict:
    d = a.to_dict()
    d.pop("version", None)
    return d


def skill_sha(agent: AgentContract) -> str | None:
    """sha256 of the agent's SKILL.md (so a changed skill shows up as a new registry row), or None if missing."""
    if not agent.skill_path:
        return None
    p = REPO / agent.skill_path
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else None


def sync(store, agents: dict[str, AgentContract] | None = None) -> list[dict]:
    """Write every contract into the store's `agents` table. A contract is re-written as a new version only
    when its definition or its SKILL.md changed; unchanged contracts are left alone. Returns what changed."""
    changed = []
    for a in (agents or AGENTS).values():
        sha = skill_sha(a)
        cur = store.get_agent(a.id)
        cur_sha = next((r["skill_sha"] for r in store.agents() if r["id"] == a.id and r["version"] == (cur.version if cur else -1)), None)
        # Compare the contract WITHOUT its version number: the stored row carries the bumped version, the code
        # carries 1, so comparing the raw JSON re-registered every agent on every pass (journal grew by 10 lines a run).
        if cur and _without_version(cur) == _without_version(a) and cur_sha == sha:
            continue
        if cur and cur.version >= a.version:
            a.version = cur.version + 1
        store.put_agent(a, sha)
        changed.append({"id": a.id, "version": a.version, "skill": "ok" if sha else ("missing" if a.skill_path else "none")})
    return changed


def demo_handlers():
    """Handlers the CLI registers. Two are REAL (deterministic, no model, no network): quality.inspect runs the
    Phase-6 validation gate on a stored product manifest; distribution.plan builds and stores a distribution plan.
    Phase 7 adds channel.adapt (deterministic per-channel copy), publish.listing / publish.social (gateway jobs for
    Pinterest, TikTok, Etsy; review-ready drafts for Make channels; approval-gated) and analytics.measure (refresh
    gateway results, fold platform metrics into the plan). research.brief and product.build still have no handler:
    the Night Shift does that work. engine.noop is a placeholder."""
    from pathlib import Path as _P
    from . import distribution as D
    from . import quality as Q

    def noop(task, ctx):
        ctx.heartbeat()
        ctx.checkpoint({"step": "noop", "input_ref": task.spec.input_ref})
        return {"output_ref": None, "validation": {"ok": True, "checks": ["placeholder handler: no external work done"]}}

    def inspect(task, ctx):
        pid = task.spec.input_ref.split("/")[-1]
        m = ctx.engine.store.get_product(pid)
        if not m:
            raise __import__("factory.engine.engine", fromlist=["PermanentError"]).PermanentError(f"no product manifest {pid}")
        ctx.heartbeat()
        res = Q.validate(m, copy=task.spec.meta.get("copy"), root=_P(task.spec.meta.get("root") or REPO), score=task.spec.meta.get("score"))
        pipe = Q.Pipeline(ctx.engine.store)
        if pipe.stage_of(m) == "generate":
            m = pipe.advance(pid, "validate", {"result": res, "new_lane": bool(task.spec.meta.get("new_lane"))}, who=task.spec.agent_id)
        g = Q.gate(res, new_lane=bool(task.spec.meta.get("new_lane")))
        ctx.checkpoint({"validated": m.version, "gate": g["decision"]})
        return {"output_ref": f"products/{pid}/v{m.version}",
                "validation": {"ok": res["ok"] is not False, "checks": [c["name"] + ("" if c["ok"] else (" (unknown)" if c["ok"] is None else " FAILED")) for c in res["checks"]],
                               "gate": g}}

    def plan(task, ctx):
        pid = task.spec.input_ref.split("/")[-1]
        m = ctx.engine.store.get_product(pid)
        meta = task.spec.meta
        if not m:
            raise __import__("factory.engine.engine", fromlist=["PermanentError"]).PermanentError(f"no product manifest {pid}")
        missing = [k for k in ("target_customer", "evidence", "destination_url") if not meta.get(k)]
        if missing:
            raise __import__("factory.engine.engine", fromlist=["PermanentError"]).PermanentError(f"distribution.plan needs meta {missing}")
        ctx.heartbeat()
        p = D.build_plan(m, target_customer=meta["target_customer"], evidence=list(meta["evidence"]), destination_url=meta["destination_url"],
                         holiday=meta.get("holiday"), days=int(meta.get("days", 7)))
        ctx.engine.store.put_plan(p)
        ctx.checkpoint({"plan": p.id})
        return {"output_ref": f"plans/{p.id}", "validation": {"ok": True, "checks": [f"{len(p.channels)} channels with reasons", f"{len(p.schedule)} scheduled posts", "destination validated"]}}

    from . import analytics as A
    from . import publishing as P
    from .contracts import Capability as _Cap
    PE = __import__("factory.engine.engine", fromlist=["PermanentError"]).PermanentError

    def _plan_for(ctx, task):
        """The plan this task works on: meta.plan_id, else the newest plan for the product in input_ref."""
        store = ctx.engine.store
        pid = task.spec.meta.get("plan_id")
        if pid:
            pl = store.get_plan(pid)
        else:
            prod = task.spec.input_ref.split("/")[-1]
            rows = store._rows("SELECT id FROM distribution_plans WHERE product_id=? ORDER BY rowid DESC LIMIT 1", (prod,))
            pl = store.get_plan(rows[0]["id"]) if rows else None
        if not pl:
            raise PE("no distribution plan for this task (run distribution.plan first or pass meta.plan_id)")
        return pl

    def adapt(task, ctx):
        pl = _plan_for(ctx, task)
        meta = task.spec.meta
        if not meta.get("copy"):
            raise PE("channel.adapt needs meta.copy (title, description, tags)")
        ctx.heartbeat()
        assets = P.adapt(pl, meta["copy"], meta.get("media") or {}, meta.get("boards"))
        pl.assets = {a.channel.value: {"status": "ready", "asset": a.to_dict()} for a in assets}
        ctx.engine.store.put_plan(pl)
        ctx.checkpoint({"assets": len(assets)})
        return {"output_ref": f"plans/{pl.id}/assets", "validation": {"ok": True, "checks": [f"{a.channel.value}: {len(a.text)} chars" for a in assets]}}

    def publish(task, ctx):
        pl = _plan_for(ctx, task)
        store = ctx.engine.store
        ctx.require(_Cap.PUBLISH_PUBLIC, f"Publish {pl.product_id} to {', '.join(c.value for c in pl.channels)}", f"Plan {pl.id}: {pl.hypothesis}")
        from .distribution import approve_plan, mark
        if pl.status == "planned":
            if not task.approval_id:
                raise PE("plan is not approved and the task carries no approval")
            pl = approve_plan(store, pl, task.approval_id)
        if pl.status == "approved":
            pl = mark(store, pl, "scheduled")
        pub = P.Publisher(store)
        pub.health()
        out, checks = [], []
        for ch in pl.channels:
            a = (pl.assets.get(ch.value) or {}).get("asset")
            if not a:
                checks.append(f"{ch.value}: no asset (channel.adapt first)")
                continue
            ctx.use_tool("gateway.job" if ch in P.GATEWAY_CHANNELS else "artifact_db.write")
            r = pub.publish(pl, P.Asset.from_dict(a), who=task.spec.agent_id)
            out.append(r.id)
            checks.append(f"{ch.value}: {r.status} via {r.adapter}")
            ctx.heartbeat()
        ctx.checkpoint({"publications": out})
        any_sent = any("queued" in c or "scheduled" in c or "published" in c for c in checks)
        if any_sent and pl.status == "scheduled":
            pass  # 'published' is set by refresh() when the gateway confirms; never here
        return {"output_ref": f"plans/{pl.id}/publications", "validation": {"ok": bool(out), "checks": checks}}

    def measure(task, ctx):
        pl = _plan_for(ctx, task)
        store = ctx.engine.store
        ctx.heartbeat()
        pub = P.Publisher(store)
        for r in pub.publications(pl.id):
            if r.status in ("queued", "scheduled"):
                pub.refresh(r)
        pl = A.measure_plan(store, pl)
        f = __import__("factory.engine.distribution", fromlist=["funnel"]).funnel(store, pl)
        ctx.checkpoint({"funnel": f})
        known = [k for k in ("audience_reached", "clicks", "conversions_or_sales") if f[k] != "unknown"]
        return {"output_ref": f"plans/{pl.id}/results", "validation": {"ok": True, "checks": [f"known: {known or 'nothing yet'}", f"next: {f['next_action']}"]}}

    # ---- Phase 9: the learning hooks reached through the shared runner
    def score(task, ctx):
        """quality.score: the SEPARATE review step. meta carries the reviewer's ratings (points + evidence per criterion),
        the artifact paths (pdf, cover, previews), copy, market evidence, claims and the by-eye slop / side-by-side verdicts.
        Code runs the objective checks, applies blockers and downward caps, combines on the frozen rubric and returns the
        evaluation; the engine's after-work hook records it with the run id. The reviewer is never given the target."""
        from factory.learning import checks as LC
        from factory.learning.improve import merge_review, plan_repairs
        from factory.learning.rubric import assess
        meta = task.spec.meta
        ctx.recall(f"{meta.get('item') or task.spec.input_ref} {meta.get('lane') or ''}")
        ctx.heartbeat()
        root = _P(meta.get("root") or REPO)
        rub = meta.get("rubric") or "etsy-product-r2"
        if rub == "etsy-product-r2":
            ck = LC.check_product(pdf=root / meta["pdf"] if meta.get("pdf") else None, cover=root / meta["cover"] if meta.get("cover") else None,
                                  previews=[root / x for x in meta.get("previews") or []], copy=meta.get("copy"), market=meta.get("market"), gap=meta.get("gap"),
                                  lane=meta.get("lane") or "game", claims=meta.get("claims") or {}, slop=meta.get("slop"), side_by_side=meta.get("side_by_side"), rules_pass=meta.get("rules_pass"))
        elif rub == "herald-post-v6":
            c = meta.get("copy") or {}
            ck = LC.check_post(channel=meta.get("channel") or "instagram", caption=c.get("caption", ""), link=c.get("link"), title=c.get("title"), returned_id=c.get("returned_id"),
                               slop_gate=meta.get("slop_gate"), facts_checked=meta.get("facts_checked"))
        else:
            ck = None
        ratings, blockers, caps = merge_review({"ratings": meta.get("ratings") or {}, "blockers": meta.get("blockers") or [], "caps": meta.get("caps") or {}}, ck)
        ev = assess(ratings, rub, blockers, caps=caps)
        ev["checks"] = (ck or {}).get("summary")
        ev["repair_plan"] = plan_repairs(ev)
        ctx.checkpoint({"score": ev["score"], "passed": ev["passed"], "blockers": len(ev["blockers"])})
        lines = [f"score {ev['score']} target {ev['target']}", f"blockers {len(ev['blockers'])}", f"missing {ev['missing']}"] + [f"{c['name']} FAILED" for c in (ck or {}).get("checks", []) if c.get("ok") is False][:8]
        return {"output_ref": f"evaluations/{task.id}", "validation": {"ok": True, "checks": lines, "evaluation": ev}}

    def diagnose(task, ctx):
        """learning.diagnose: one bounded model call (through the router: free session hand-off first, paid never without
        an approved spend) that turns the ranked losses / repeated failures / successful examples into at most three
        experiment ideas, then queues them with brain.propose (dedup across agents, daily budget). The ideas are
        proposals, not changes; nothing runs until an experiment is started and decided."""
        import json as _json
        from factory.learning.brain import AgentBrain
        meta = task.spec.meta
        scope = meta.get("scope") or ctx.engine.scope_for(meta.get("for_agent") or task.spec.agent_id)
        agent = meta.get("for_agent") or task.spec.agent_id
        brain = AgentBrain(ctx.engine.store)
        losses = brain.losses(scope, agent, mode=meta.get("mode") or "production")[:6]
        repeats = brain.repeated_failures(scope, agent)[:6]
        wins = [d["id"] for d in brain.evaluations(scope, agent, kind="score", limit=100, include_holdout=False) if d.get("passed")][:5]
        fails = [d for d in brain.evaluations(scope, agent, kind="score", limit=100, include_holdout=False) if not d.get("passed") and d.get("score") is not None][:6]
        sources = [d["id"] for d in fails] + wins
        if not sources and not repeats:
            return {"output_ref": None, "validation": {"ok": True, "checks": ["nothing to diagnose: no scored failures or repeated patterns on file"]}}
        prompt = ("You improve one agent's workflow from evidence. Return ONLY a JSON list of at most 3 objects with keys hypothesis, change, baseline, metric, success, stop, budget, sources. "
                  "Each must cite source ids from the data. Prefer the cheapest useful test; include a distribution/timing/channel test if the losses point outside the artifact.\n"
                  + _json.dumps({"scope": scope, "agent": agent, "ranked_losses": losses, "repeated_failures": repeats, "failed_runs": [{"id": d["id"], "score": d["score"], "blockers": (d.get("payload", {}).get("evaluation") or {}).get("blockers", [])[:3]} for d in fails],
                                 "successful_runs": wins, "source_ids": sources}, default=str)[:6000])
        c = ctx.llm(prompt, max_tokens=int(meta.get("max_tokens") or 700), uncertain=True)
        try:
            ideas = _json.loads(c.text)
            if isinstance(ideas, dict):
                ideas = [ideas]
        except Exception:
            ideas = []
        queued, refused = [], []
        for idea in ideas[:3]:
            try:
                queued.append(brain.propose(scope, agent, idea))
            except ValueError as e:
                refused.append(str(e)[:120])
        ctx.checkpoint({"ideas": queued})
        return {"output_ref": f"ideas/{scope}/{agent}", "validation": {"ok": True, "checks": [f"model returned {len(ideas)} idea(s)", f"queued {len(queued)}", *[f"refused: {r}" for r in refused]]}}

    return {"engine.noop": noop, "quality.inspect": inspect, "distribution.plan": plan, "channel.adapt": adapt,
            "publish.listing": publish, "publish.social": publish, "analytics.measure": measure, "quality.score": score, "learning.diagnose": diagnose}
