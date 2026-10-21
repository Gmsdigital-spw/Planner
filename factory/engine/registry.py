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
        if cur and cur.to_json() == a.to_json() and cur_sha == sha:
            continue
        if cur and cur.version >= a.version:
            a.version = cur.version + 1
        store.put_agent(a, sha)
        changed.append({"id": a.id, "version": a.version, "skill": "ok" if sha else ("missing" if a.skill_path else "none")})
    return changed


def demo_handlers():
    """Phase-3 placeholders so the CLI `tick` has something to run. They do no external work and say so.
    Real handlers arrive with the orchestrator in Phase 4."""
    def noop(task, ctx):
        ctx.heartbeat()
        ctx.checkpoint({"step": "noop", "input_ref": task.spec.input_ref})
        return {"output_ref": None, "validation": {"ok": True, "checks": ["placeholder handler: no external work done"]}}
    return {"engine.noop": noop}
