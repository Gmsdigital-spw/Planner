"""Bounded, callback-based improvement loop (factory/learning, Phase 9).

`improve()` wires the project's EXISTING model / tools / timeouts / budget gate through three callbacks:
    make(task, memory_json) -> artifact            (the producer; a Night Shift builder, an engine handler, a mock)
    judge(artifact) -> {"ratings", "blockers"?, "caps"?, "slop"?, "side_by_side"?, "unscored"?}   (a SEPARATE review role)
    repair(artifact, evaluation, memory_json) -> artifact
plus an optional `checks(artifact) -> check_product()-style dict` for objective evidence (file validity, limits, market
evidence...). The judge is never told the target score; the code combines, caps downward, applies blockers and decides.

Bounds: one generation, at most MAX_REPAIRS (2) repairs, so at most three evaluations per job, inside the caller's
time budget. It stops when the item passes or the limit is reached; the last result is recorded as final with its
remaining blockers (a 92 stays a 92). A callback that raises is recorded as an error row with NO score.
"""
from __future__ import annotations

import time
import traceback
import typing as t
import uuid

from .brain import AgentBrain
from .rubric import assess, packed

MAX_REPAIRS = 2


def plan_repairs(result: dict, top: int = 2) -> dict:
    """Rank lost weighted points, name the `top` criteria furthest from full marks and every blocker: what to fix first."""
    gaps = [g for g in (result.get("gaps") or []) if g.get("lost_points", 0) > 0]
    return {"fix_first": [{"criterion": g["criterion"], "lost_points": g["lost_points"], "points": g.get("points"), "max": g.get("max"), "evidence": g.get("evidence")} for g in gaps[:top]],
            "blockers": list(result.get("blockers") or []), "missing": list(result.get("missing") or []), "capped": list(result.get("capped") or []),
            "score": result.get("score"), "target": result.get("target")}


def merge_review(review: dict, checks: dict | None) -> tuple[dict, list[str], dict]:
    """Fold objective check results into the reviewer's ratings: blockers add, caps take the minimum, unscored criteria
    lose their rating (they stay missing until evidence exists). Never raises a rating."""
    ratings = dict(review.get("ratings") or {})
    blockers = list(review.get("blockers") or [])
    caps = dict(review.get("caps") or {})
    if checks:
        blockers += [b for b in checks.get("blockers") or [] if b not in blockers]
        for k, v in (checks.get("caps") or {}).items():
            caps[k] = min(caps.get(k, v), v)
        for crit in checks.get("unscored") or []:
            ratings.pop(crit, None)
        for crit, lines in (checks.get("notes") or {}).items():
            if crit in ratings and isinstance(ratings[crit], dict) and ratings[crit].get("evidence"):
                fails = [ln for ln in lines if ": FAIL" in ln][:3]
                if fails:
                    ratings[crit] = dict(ratings[crit], evidence=str(ratings[crit]["evidence"]) + " | code: " + "; ".join(fails))
    return ratings, blockers, caps


def improve(brain: AgentBrain, *, scope: str, agent: str, task: str, version: str, make: t.Callable, judge: t.Callable, repair: t.Callable,
            rubric: str | dict | None = "etsy-product-r2", checks: t.Callable | None = None, max_repairs: int = MAX_REPAIRS, mode: str = "offline",
            job_id: str | None = None, artifact_ref: str = "", max_seconds: float | None = None, clock: t.Callable[[], float] = time.time,
            memory_limit: int = 6, memory_chars: int = 6000) -> dict:
    if type(max_repairs) is not int or not 0 <= max_repairs <= MAX_REPAIRS:
        raise ValueError(f"Allow zero to {MAX_REPAIRS} repair attempts")
    job_id = job_id or uuid.uuid4().hex
    t0 = clock()
    memory = brain.context(scope, agent, task, limit=memory_limit, max_chars=memory_chars, run_ref=job_id)
    memory_json = packed(memory)
    trace: dict = {"job_id": job_id, "memory_items": len(memory), "memory_chars": len(memory_json), "attempts": [], "stopped": None, "draft": None, "result": None}
    try:
        draft = make(task, memory_json)
    except Exception as e:  # the producer's tool failed: no score is invented
        rid = f"{job_id}:0"
        brain.log_error(rid, scope, agent, task=task[:500], error=f"make failed: {type(e).__name__}: {e}", error_class="tool", mode=mode, version=version, attempt=0, task_id=job_id)
        brain.remember(scope, agent, "mistake", packed({"task": task[:300], "error": f"generation failed: {type(e).__name__}: {str(e)[:200]}"}), f"evaluation {rid}; suspected cause requires validation")
        trace.update(stopped="error", error=str(e)[:300])
        return trace
    trace["draft"] = draft
    for attempt in range(max_repairs + 1):
        rid = f"{job_id}:{attempt}"
        try:
            review = judge(draft)
            ck = checks(draft) if checks else None
        except Exception as e:
            brain.log_error(rid, scope, agent, task=task[:500], error=f"judge failed: {type(e).__name__}: {e}", error_class="tool", mode=mode, version=version, attempt=attempt, task_id=job_id)
            trace["attempts"].append({"attempt": attempt, "error": str(e)[:300]})
            trace.update(stopped="error")
            return trace
        ratings, blockers, caps = merge_review(review or {}, ck)
        result = assess(ratings, rubric, blockers, caps=caps)
        if ck:
            result["checks"] = ck.get("summary")
            result["check_lines"] = [c for c in ck.get("checks", []) if c.get("ok") is not True][:20]
        elapsed = clock() - t0
        out_of_time = max_seconds is not None and elapsed >= max_seconds
        final = bool(result["passed"] or attempt == max_repairs or out_of_time)
        if out_of_time and not result["passed"]:
            result["blockers"] = list(result["blockers"]) + [f"time budget reached ({int(elapsed)}s of {int(max_seconds)}s): no further repair this run"]
            result["passed"] = False
        brain.log(rid, scope, agent, version, task, draft, result, mode=mode, final=final, artifact_ref=artifact_ref, kind="score", task_id=job_id, attempt=attempt)
        plan = plan_repairs(result)
        trace["attempts"].append({"attempt": attempt, "score": result["score"], "passed": result["passed"], "blockers": result["blockers"], "missing": result["missing"], "plan": plan})
        if not result["passed"]:
            brain.remember(scope, agent, "mistake", packed({"task": task[:300], "attempt": attempt, "score": result["score"], "gaps": result["gaps"][:3], "missing": result["missing"], "blockers": result["blockers"][:5]})[:12000],
                           f"evaluation {rid}; suspected cause requires validation", tags={"criterion": (result["gaps"][0]["criterion"] if result.get("gaps") else None)})
        if final:
            trace.update(result=result, stopped="passed" if result["passed"] else ("budget" if out_of_time else "limit"))
            return trace
        try:
            draft = repair(draft, dict(result, repair_plan=plan), memory_json)
            trace["draft"] = draft
        except Exception as e:
            brain.log_error(f"{rid}:repair", scope, agent, task=task[:500], error=f"repair failed: {type(e).__name__}: {e}", error_class="tool", mode=mode, version=version, attempt=attempt, task_id=job_id)
            trace.update(result=result, stopped="error", error=str(e)[:300])
            return trace
    return trace  # unreachable: the loop always returns on final


def next_attempt(brain: AgentBrain, job_id: str) -> int:
    """For the coordinator-driven loop (CLI): which attempt comes next for this job, or -1 when the bound is spent."""
    rows = brain.store.rows("SELECT attempt, passed, final FROM evaluations WHERE task_id=? AND kind='score' ORDER BY attempt", (job_id,))
    if not rows:
        return 0
    if any(r["passed"] for r in rows) or any(r["final"] for r in rows):
        return -1
    nxt = max(int(r["attempt"] or 0) for r in rows) + 1
    return nxt if nxt <= MAX_REPAIRS else -1
