"""Orchestrator (add-on Phase 4): goals → dependency graphs of tasks, progress, blocked work, verification.

The Foreman's contract is the orchestrator role. This module is the deterministic part of that job:
it does not call a model. Given a goal it builds the task graph from PLANS, submits the tasks through the
engine (so every safeguard applies: allow-lists, approvals, idempotency), records a Project, and can tell
you at any time what is done, what is blocked and why, and whether the project is *verifiably* complete
(every task succeeded with an output_ref — never "probably done").

Goals today (each is a list of steps; a step may depend on earlier steps):
- launch_product   brief → build → inspect → plan distribution → adapt per channel → publish (gated) → measure
- promote_product  for a product that already exists: plan → adapt → publish (gated) → measure
- research_lane    scout ideas for one lane
- health_check     mechanic inspects the repo and the runs
"""
from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from .contracts import Capability, TaskSpec, TaskStatus, new_id, now_iso
from .engine import EngineError, TaskEngine


@dataclass
class Step:
    key: str
    agent: str
    kind: str
    after: list[str] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    priority: int = 5


PLANS: dict[str, list[Step]] = {
    "launch_product": [
        Step("brief", "scout", "research.brief", tools=["web.search", "web.fetch", "artifact_db.read"], priority=3),
        Step("build", "forge", "product.build", after=["brief"], tools=["files.write", "artifact_db.write"]),
        Step("inspect", "atlas", "quality.inspect", after=["build"], tools=["files.read", "artifact_db.read"]),
        Step("plan", "hawk", "distribution.plan", after=["inspect"], tools=["artifact_db.read"]),
        Step("adapt", "herald", "channel.adapt", after=["plan"], tools=["files.write", "artifact_db.write"]),
        Step("publish", "bolt", "publish.listing", after=["adapt"], capabilities=[Capability.PUBLISH_PUBLIC], tools=["gateway.job", "artifact_db.write"]),
        Step("measure", "graph", "analytics.measure", after=["publish"], tools=["make.scenario_run", "artifact_db.write"], priority=7),
    ],
    "promote_product": [
        Step("plan", "hawk", "distribution.plan", tools=["artifact_db.read"], priority=3),
        Step("adapt", "herald", "channel.adapt", after=["plan"], tools=["files.write", "artifact_db.write"]),
        Step("publish", "bolt", "publish.social", after=["adapt"], capabilities=[Capability.PUBLISH_PUBLIC], tools=["gateway.job", "make.scenario_run", "artifact_db.write"]),
        Step("measure", "graph", "analytics.measure", after=["publish"], tools=["make.scenario_run", "vidiq.read", "artifact_db.write"], priority=7),
    ],
    "research_lane": [Step("ideas", "scout", "research.ideas", tools=["web.search", "web.fetch", "artifact_db.read"], priority=4)],
    "health_check": [Step("inspect", "mechanic", "engineering.inspect", tools=["git.read", "files.read", "artifact_db.read"], priority=2)],
}


class Orchestrator:
    def __init__(self, engine: TaskEngine):
        self.engine = engine
        self.store = engine.store

    # ---------------------------------------------------------------- planning
    def plan(self, goal: str, input_ref: str, who: str = "foreman", meta: dict | None = None) -> dict:
        """Build and submit the task graph for `goal`. Idempotent per (goal, input_ref): planning twice returns the same project."""
        if goal not in PLANS:
            raise EngineError(f"unknown goal {goal!r}; known: {sorted(PLANS)}")
        pid = "proj_" + _slug(goal) + "_" + _slug(input_ref)
        existing = self.store.get_project(pid)
        if existing:
            return existing
        key_to_id: dict[str, str] = {}
        tasks: list[dict] = []
        for step in PLANS[goal]:
            missing = [a for a in step.after if a not in key_to_id]
            if missing:
                raise EngineError(f"plan {goal}: step {step.key} depends on unknown {missing}")
            spec = TaskSpec(agent_id=step.agent, kind=step.kind, input_ref=input_ref, tools=list(step.tools), capabilities=list(step.capabilities),
                            depends_on=[key_to_id[a] for a in step.after], priority=step.priority,
                            meta={"project": pid, "step": step.key, **(meta or {})})
            task = self.engine.submit(spec, who=who)
            key_to_id[step.key] = task.id
            tasks.append({"step": step.key, "task_id": task.id, "agent": step.agent, "after": list(step.after)})
        ts = now_iso()
        doc = {"id": pid, "goal": goal, "input_ref": input_ref, "status": "open", "tasks": tasks, "created_at": ts, "updated_at": ts, "by": who}
        self.store.put_project(doc)
        return doc

    # ---------------------------------------------------------------- tracking
    def progress(self, project_id: str) -> dict:
        """Done / running / blocked (with the reason) / failed, computed from the real task records."""
        p = self.store.get_project(project_id)
        if not p:
            raise EngineError(f"no project {project_id}")
        rows, counts = [], {s.value: 0 for s in TaskStatus}
        by_id = {}
        for tk in p["tasks"]:
            task = self.store.get_task(tk["task_id"])
            by_id[tk["task_id"]] = task
        for tk in p["tasks"]:
            task = by_id[tk["task_id"]]
            if task is None:
                rows.append({**tk, "status": "missing", "blocked_by": None})
                continue
            counts[task.status.value] += 1
            blocked_by = None
            if task.status == TaskStatus.QUEUED:
                deps = [by_id.get(d) for d in task.spec.depends_on]
                bad = [d for d in deps if d is None or d.status != TaskStatus.SUCCEEDED]
                if bad:
                    blocked_by = [f"{d.spec.meta.get('step', d.id)} is {d.status.value}" for d in bad if d]
                elif self.engine.paused(task.spec.agent_id):
                    blocked_by = [f"agent {task.spec.agent_id} is paused"]
                elif self.engine.killed():
                    blocked_by = ["kill switch is on"]
                elif task.next_eligible_at and task.next_eligible_at > now_iso():
                    blocked_by = [f"backoff until {task.next_eligible_at}"]
            elif task.status == TaskStatus.NEEDS_APPROVAL:
                blocked_by = [f"approval {task.approval_id} is waiting on Grayson"]
            elif task.status == TaskStatus.FAILED:
                blocked_by = [task.last_error or "failed"]
            rows.append({**tk, "status": task.status.value, "attempts": task.attempts, "blocked_by": blocked_by, "output_ref": task.output_ref})
        total = len(p["tasks"])
        return {"project": project_id, "goal": p["goal"], "status": p["status"], "total": total, "counts": counts,
                "done": counts["succeeded"], "blocked": [r for r in rows if r.get("blocked_by")], "tasks": rows}

    def verify(self, project_id: str, who: str = "foreman") -> dict:
        """Complete only when every task SUCCEEDED and carries an output_ref. Anything else stays open, with the reasons."""
        pr = self.progress(project_id)
        problems = [f"{r['step']}: {r['status']}" + (" (no output_ref)" if r["status"] == "succeeded" and not r.get("output_ref") else "")
                    for r in pr["tasks"] if r["status"] != "succeeded" or not r.get("output_ref")]
        p = self.store.get_project(project_id)
        assert p
        p["status"] = "complete" if not problems else ("failed" if pr["counts"]["failed"] or pr["counts"]["cancelled"] else "open")
        p["updated_at"] = now_iso()
        p["verified_at" if not problems else "last_verify"] = now_iso()
        p["problems"] = problems
        self.store.put_project(p)
        return {"project": project_id, "status": p["status"], "problems": problems}

    def open_projects(self) -> list[dict]:
        return self.store.projects("open")


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.lower())[:40].strip("_")
