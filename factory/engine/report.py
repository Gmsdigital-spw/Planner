"""Dashboard report (add-on Phase 8).

One credential-free JSON document the Factory page reads (over raw.githubusercontent, the same way it reads
the trading heartbeat). Everything in it is read back from the engine's own records; nothing is estimated:
- health: schema, kill switch, paused agents, last tick, how old this report is, what runs the worker
- agents: every registered contract with its live state (paused / failing / idle) from real runs
- workflows: open and finished projects with progress and what blocks them
- tasks: queued / running / needs_approval / failed, each failed one with the error and a plain next step
- approvals: pending, with cost and risk as the agent wrote them
- products: latest version per product, stage, gate decision, listing + distribution status
- plans + publications: status, next action, funnel, every publish attempt and whether it was verified
- metrics: platform-reported sums per channel over the window, unknown kinds listed; recommendations labelled
- usage: real model usage today + the daily budget; unknown-cost calls are counted, never priced
- integrations: gateway / make as last observed (connected · unverified · missing)
- errors: the latest failed runs with their recovery note
- orders: what Grayson's taps did on the last worker pass (applied / refused)
Every string passes through scrub() so a token can never land on a public page.
"""
from __future__ import annotations

import json
import typing as t
from datetime import datetime, timezone
from pathlib import Path

from . import contracts as C
from .analytics import compare, recommend
from .contracts import TaskStatus, now_iso, scrub
from .distribution import funnel
from .engine import TaskEngine
from .orchestrator import Orchestrator
from .quality import Pipeline
from .store import Store

HERE = Path(__file__).resolve().parent
PUBLIC = HERE / "public" / "report.json"
STALE_AFTER_S = 2 * 3600  # the page calls the report late after this


def _age_s(iso: str | None, now: str | None = None) -> int | None:
    if not iso:
        return None
    try:
        a = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        b = datetime.fromisoformat((now or now_iso()).replace("Z", "+00:00"))
        return int((b - a).total_seconds())
    except ValueError:
        return None


def _next_step(task: C.Task, run: C.Run | None) -> str:
    """A plain next step for a failed task, from what the engine actually recorded."""
    if run and run.recovery:
        return run.recovery
    cls = (run.error_class if run else None) or ""
    if cls == "needs_approval":
        return "approve it in the Inbox, then retry"
    if cls in ("transient", "rate_limited", "timeout"):
        return "retry; it failed on something temporary"
    if "budget" in (task.last_error or "").lower():
        return "raise the daily budget or wait for tomorrow, then retry"
    return "read the error, fix the input, then retry"


def build_report(store: Store, eng: TaskEngine, *, days: int = 14, orders: list[dict] | None = None, worker: str = "") -> dict:
    now = now_iso()
    status = eng.status()
    lt = status.get("last_tick") or {}
    last_tick = lt.get("at") if isinstance(lt, dict) else lt
    runner = lt.get("runner") if isinstance(lt, dict) else None
    # agents: contract + real state
    paused = set(status.get("paused_agents") or [])
    latest: dict[str, dict] = {}
    for a in store.agents():
        latest[a["id"]] = a  # ordered by version, so the last wins
    task_rows = store.tasks(limit=500)
    by_agent: dict[str, dict] = {}
    for tk in task_rows:
        g = by_agent.setdefault(tk.spec.agent_id, {"queued": 0, "running": 0, "needs_approval": 0, "succeeded": 0, "failed": 0, "cancelled": 0, "last": ""})
        g[tk.status.value] = g.get(tk.status.value, 0) + 1
        g["last"] = max(g["last"], tk.updated_at)
    agents = []
    for aid, a in sorted(latest.items()):
        g = by_agent.get(aid, {})
        state = "paused" if aid in paused else ("failing" if g.get("failed") else ("working" if g.get("running") else ("queued" if g.get("queued") else "idle")))
        agents.append({"id": aid, "name": a["name"], "role": a["role"], "version": a["version"], "state": state, "counts": {k: v for k, v in g.items() if k != "last"},
                       "last_activity": g.get("last") or None, "skill_sha": (a.get("skill_sha") or "")[:8] or None})
    # workflows (projects)
    orch = Orchestrator(eng)
    workflows = []
    for p in store.projects()[:20]:
        try:
            pr = orch.progress(p["id"])
        except Exception as e:  # a project whose tasks were purged still shows up, honestly
            pr = {"error": scrub(str(e))}
        workflows.append({"id": p["id"], "goal": p["goal"], "input_ref": p["input_ref"], "status": p["status"], "updated_at": p.get("updated_at"),
                          "done": pr.get("done"), "total": pr.get("total"), "counts": pr.get("counts"), "problems": p.get("problems") or [],
                          "blocked": [{"step": r.get("step"), "task_id": r.get("task_id"), "status": r.get("status"), "why": r.get("blocked_by")} for r in (pr.get("blocked") or [])]})
    # tasks
    def tk_row(tk: C.Task) -> dict:
        runs = store.runs_for(tk.id)
        run = runs[-1] if runs else None
        d = {"id": tk.id, "kind": tk.spec.kind, "agent": tk.spec.agent_id, "status": tk.status.value, "attempts": tk.attempts, "updated_at": tk.updated_at,
             "input_ref": tk.spec.input_ref, "output_ref": tk.output_ref, "approval_id": tk.approval_id, "next_eligible_at": tk.next_eligible_at}
        if tk.status == TaskStatus.FAILED:
            d["error"] = scrub(tk.last_error or (run.error if run else "") or "")[:300]
            d["error_class"] = run.error_class if run else None
            d["next_step"] = _next_step(tk, run)
            d["retry"] = f"python -m factory.engine retry {tk.id}"
        if tk.status == TaskStatus.NEEDS_APPROVAL:
            d["next_step"] = "approve or decline it in the Inbox"
        return d
    tasks = {s: [tk_row(tk) for tk in store.tasks(TaskStatus(s), limit=50)] for s in ("queued", "running", "needs_approval", "failed")}
    recent_done = [tk_row(tk) for tk in task_rows if tk.status == TaskStatus.SUCCEEDED][:10]
    approvals = [{"id": a.id, "task_id": a.task_id, "capability": a.capability.value, "title": a.title, "why": a.why, "cost": a.cost, "risk": a.risk,
                  "requested_at": a.requested_at, "expires_at": a.expires_at} for a in store.approvals("proposed")]
    # products
    pipe = Pipeline(store)
    products = []
    for r in store._rows("SELECT DISTINCT product_id FROM products ORDER BY product_id"):
        m = store.get_product(r["product_id"])
        if not m:
            continue
        v = m.validation or {}
        res = v.get("result") or {}
        g = v.get("gate") or {}
        products.append({"product_id": m.product_id, "version": m.version, "title": m.title, "lane": m.lane, "format": m.format, "stage": pipe.stage_of(m),
                         "gate": g.get("decision") or "not validated yet", "gate_reasons": (g.get("reasons") or [])[:5], "checks_failed": res.get("failed"), "checks_unknown": res.get("unknown"),
                         "score": res.get("score", "unknown") if res else "unknown", "listing_status": m.listing_status, "distribution_status": m.distribution_status,
                         "known_limitations": m.known_limitations[:3], "files": len(m.files), "created_at": m.created_at})
    # plans + publications
    plans = []
    for row in store._rows("SELECT doc FROM distribution_plans ORDER BY rowid DESC LIMIT 30"):
        pl = C.DistributionPlan.from_dict(json.loads(row["doc"]))
        pubs = store.publications(pl.id)
        plans.append({"id": pl.id, "product_id": pl.product_id, "product_version": pl.product_version, "status": pl.status, "channels": [c.value for c in pl.channels],
                      "channel_reasons": pl.channel_reasons, "target_customer": pl.target_customer, "destination_url": pl.destination_url, "hypothesis": pl.hypothesis,
                      "success_criteria": pl.success_criteria, "campaign": (pl.tracking or {}).get("campaign"), "approval_id": pl.approval_id, "funnel": funnel(store, pl),
                      "next_action": pl.next_action, "results": pl.results, "scheduled": sum(1 for s in pl.schedule if s.get("status") == "scheduled"),
                      "published": sum(1 for s in pl.schedule if s.get("status") == "published"),
                      "publications": [{"id": p.id, "channel": p.channel.value, "status": p.status, "adapter": p.adapter, "verified": p.verified, "url": p.url,
                                        "job_id": p.job_id, "draft_path": p.draft_path, "checked_at": p.checked_at, "note": scrub(p.note)[:200], "created_at": p.created_at} for p in pubs]})
    # metrics
    cmp = compare(store, "channel", days)
    metrics = {"days": days, "by_channel": cmp["groups"], "note": cmp["note"], "recommendations": recommend(cmp)}
    # usage + budget
    usage = eng.router.report(now[:10]) if eng.router else store.usage_summary(now[:10])
    budget = store.control("budget", {}) or {}
    usage_out = {"today": now[:10], "calls": usage.get("calls", 0), "cached_calls": usage.get("cached_calls", 0),
                 # no calls at all is a real zero (the engine made none); calls with no reported cost stay unknown
                 "cost_usd_known": (0.0 if not usage.get("calls") else (usage.get("cost_usd_known") if usage.get("cost_usd_known") is not None else "unknown")),
                 "cost_unknown_calls": usage.get("cost_unknown_calls", 0),
                 "tokens_known": (0 if not usage.get("calls") else (usage.get("tokens_known") if usage.get("tokens_known") is not None else "unknown")),
                 "budget": {"daily_calls": budget.get("daily_calls", 400), "daily_usd": budget.get("daily_usd", "unlimited (nothing paid is configured)"),
                            "daily_unknown_calls": budget.get("daily_unknown_calls", 400)},
                 "paid_provider_allowed": bool(eng.router and eng.router.paid_allowed()), "note": "model usage is what the provider reported; nothing is estimated"}
    integrations = [{"id": i["id"], "state": i["state"], "last_ok_at": i.get("last_ok_at"), "last_error": scrub(i.get("last_error") or "")[:200] or None,
                     "checked_at": i.get("checked_at"), "note": i.get("note") or ""} for i in store.integrations()]
    # errors: latest failed runs
    errors = []
    for row in store._rows("SELECT doc FROM runs WHERE status='failed' ORDER BY started_at DESC LIMIT 12"):
        r = C.Run.from_dict(json.loads(row["doc"]))
        errors.append({"run_id": r.id, "task_id": r.task_id, "agent": r.agent_id, "attempt": r.attempt, "at": r.finished_at or r.started_at, "error": scrub(r.error or "")[:300],
                       "error_class": r.error_class, "recovery": r.recovery})
    audit = [{"at": a["at"], "who": a["who"], "action": a["action"], "subject": a["subject"], "detail": scrub(a.get("detail") or "")[:200]} for a in store.audit_tail(40)]
    # Phase 9: the agents' learning panel (scored samples, pass / 95+ rates, weakest criteria, repeats, memory freshness,
    # tested lessons, experiments, token proxy); production and offline rows apart; unknown stays unknown.
    try:
        from factory.learning.brain import AgentBrain
        from factory.learning.panel import learning_section
        learning = learning_section(AgentBrain(store), days)
    except Exception as e:  # the report never fails over the panel
        learning = {"error": scrub(f"{type(e).__name__}: {e}")[:200], "note": "learning panel unavailable; see factory/learning/README.md"}
    rep = {
        "schema": 1, "generated_at": now, "worker": worker or "python -m factory.engine worker",
        "health": {"engine_schema": status.get("schema"), "kill": bool(status.get("kill")), "paused_agents": sorted(paused), "last_tick": last_tick, "last_runner": runner,
                   "last_tick_age_s": _age_s(last_tick, now), "counts": status.get("counts"), "pending_approvals": len(approvals), "stale_after_s": STALE_AFTER_S,
                   "note": "the engine runs only when the worker runs (GitHub Actions on a schedule, or a crew run); generated_at is the truth"},
        "agents": agents, "workflows": workflows, "tasks": tasks, "recent_done": recent_done, "approvals": approvals, "products": products, "plans": plans,
        "metrics": metrics, "usage": usage_out, "integrations": integrations, "errors": errors, "orders": orders or [], "audit": audit,
        "learning": learning,
    }
    # belt and braces: scrub the whole document once more
    return json.loads(scrub(json.dumps(rep, default=str)))


def write_report(rep: dict, path: Path | str = PUBLIC) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rep, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    return p
