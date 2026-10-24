"""Durable task engine (add-on Phase 3).

Lifecycle: queued → running → needs_approval → succeeded | failed | cancelled.
Every transition is written to the journal and SQLite before anything else happens.

Guarantees (each one has a test in tests/test_engine.py):
- idempotency: the same `idempotency_key` never creates a second task;
- tool allow-list: a task may only name tools its agent contract permits;
- capability gate: publish / spend / credentials / destructive need an APPROVED approval id; the
  task parks in needs_approval until a human decides, then re-queues;
- bounded retries with exponential backoff for transient errors; permanent errors fail at once;
- timeouts: a handler that overruns `timeout_s` is recorded as a timeout and retried like transient;
- kill switch: `control.kill=true` stops every new action (claims return None) without deleting anything;
- pause/resume per agent, cancel at any non-terminal stage;
- stalled detection: running tasks whose run heartbeat is older than `stalled_after_s` are re-queued
  (or failed once retries are spent) by `recover()`, which also runs on every `open()`;
- secret-safe logging: errors and audit detail pass through `scrub()`.

It does NOT run in the background by itself. A worker is whatever calls `tick()`: a GitHub Actions
step, a Claude scheduled task, or `python -m factory.engine tick`. `status()` says when the last
tick happened so nobody mistakes a quiet engine for a running one.
"""
from __future__ import annotations

import threading
import time
import traceback
import typing as t
from datetime import datetime, timedelta, timezone

from .contracts import (TERMINAL, TRANSITIONS, AgentContract, Approval, ApprovalStatus, AuditEvent, Capability,
                        ModelUsage, Run, Task, TaskSpec, TaskStatus, idempotency_key, new_id, now_iso, scrub)
from .store import Store

GATED = {Capability.PUBLISH_PUBLIC, Capability.SPEND_MONEY, Capability.CHANGE_CREDENTIALS, Capability.DESTRUCTIVE_CHANGE, Capability.TRADE_LIVE}


class EngineError(Exception):
    pass


class TransientError(Exception):
    """Raise from a handler for something worth retrying (network, 5xx, rate limit)."""
    error_class = "transient"


class RateLimited(TransientError):
    error_class = "rate_limited"


class PermanentError(Exception):
    """Raise from a handler when retrying cannot help (bad input, policy)."""
    error_class = "permanent"


class NeedsApproval(Exception):
    """Raise from a handler when it discovers mid-run that a human must decide."""
    def __init__(self, capability: Capability, title: str, why: str, cost: str | None = None, risk: str | None = None):
        super().__init__(title)
        self.capability, self.title, self.why, self.cost, self.risk = capability, title, why, cost, risk


Handler = t.Callable[[Task, "RunContext"], dict]


class RunContext:
    """What a handler gets: a heartbeat, a checkpoint writer, a usage recorder, a tool gate."""

    def __init__(self, engine: "TaskEngine", task: Task, run: Run, contract: AgentContract):
        self.engine, self.task, self.run, self.contract = engine, task, run, contract
        self.calls = 0
        self.memory_items: int | None = None  # set by recall(); merged into the run's validation

    def heartbeat(self) -> None:
        self.run.heartbeat_at = now_iso()
        self.engine.store.put_run(self.run)

    def checkpoint(self, data: dict) -> None:
        self.task.checkpoint = dict(data)
        self.task.updated_at = now_iso()
        self.engine.store.put_task(self.task)

    def record_usage(self, usage: ModelUsage) -> None:
        self.run.usage = usage
        self.engine.store.put_usage(self.run.id, usage)

    def use_tool(self, tool: str) -> None:
        """Every external call goes through here: allow-list + per-task call budget."""
        if not self.contract.allows_tool(tool):
            raise PermanentError(f"agent {self.contract.id} may not use tool {tool!r}")
        self.calls += 1
        cap = self.contract.budget.max_calls_per_task
        if cap is not None and self.calls > cap:
            raise PermanentError(f"call budget exceeded ({cap} per task)")

    def llm(self, prompt: str, *, cacheable: bool = False, uncertain: bool = False, system: str | None = None, max_tokens: int = 800, ttl_s: int | None = None):
        """Ask a model through the router (Phase 5): tier by task kind, escalation on retries, cache, budgets.
        Raises BudgetExceeded (a PermanentError) when a hard limit is hit, so the task fails safely."""
        router = self.engine.router
        if router is None:
            raise PermanentError("no model router configured on this engine")
        kw = dict(budget=self.contract.budget, model_hint=self.task.spec.model_hint, attempt=self.task.attempts, uncertain=uncertain,
                  cacheable=cacheable, system=system, max_tokens=max_tokens, run_id=self.run.id)
        if ttl_s is not None:
            kw["ttl_s"] = ttl_s
        c = router.complete(self.task.id, self.task.spec.kind, prompt, **kw)
        self.run.usage = c.usage
        self.run.model = c.model
        self.heartbeat()
        return c

    def recall(self, task_text: str = "", *, scope: str | None = None, limit: int = 6, max_chars: int = 6000) -> list[dict]:
        """Learning hook (Phase 9): the scoped memory for this agent BEFORE it works. Data, not instructions; the
        allow-lists and approvals above are untouched by anything a memory says. Recorded against this task id so the
        result can be matched to what was shown."""
        from factory.learning.brain import AgentBrain  # local import: the engine never needs it at import time
        sc = scope or self.task.spec.meta.get("scope") or self.engine.scope_for(self.contract.id)
        items = AgentBrain(self.engine.store).context(sc, self.contract.id, task_text or f"{self.task.spec.kind} {self.task.spec.input_ref}", limit=limit, max_chars=max_chars, run_ref=self.task.id)
        self.memory_items = len(items)
        return items

    def require(self, cap: Capability, title: str, why: str, cost: str | None = None, risk: str | None = None) -> None:
        """Ask for a gated capability. Approved → continue; otherwise park the task."""
        if not self.contract.has(cap):
            raise PermanentError(f"agent {self.contract.id} is not allowed {cap.value}")
        a = self.engine.store.get_approval(self.task.approval_id) if self.task.approval_id else None
        if a and a.status == ApprovalStatus.APPROVED and a.capability == cap:
            return
        raise NeedsApproval(cap, title, why, cost, risk)


class TaskEngine:
    def __init__(self, store: Store, agents: dict[str, AgentContract], runner: str = "local", clock: t.Callable[[], float] = time.time, router=None):
        self.store = store
        self.agents = dict(agents)
        self.router = router  # a router.Router; None = handlers cannot call models
        self.handlers: dict[str, Handler] = {}  # task kind → handler
        self.runner = runner
        self.clock = clock
        for a in self.agents.values():
            a.validate()
        self.learning = True  # Phase 9: every finished run is also recorded in the learning store (set False in tests that want silence)
        self.recover()

    AGENT_SCOPE = {"foreman": "crew", "mechanic": "crew", "ledger": "crew", "graph": "shop", "scout": "shop", "forge": "shop", "atlas": "shop", "hawk": "shop", "herald": "shop", "bolt": "shop"}

    def scope_for(self, agent_id: str) -> str:
        return self.AGENT_SCOPE.get(agent_id, "crew")

    # ---------------------------------------------------------------- registration
    def register(self, kind: str, handler: Handler) -> None:
        self.handlers[kind] = handler

    # ---------------------------------------------------------------- controls
    def kill(self, on: bool, who: str = "grayson") -> None:
        self.store.set_control("kill", bool(on))
        self.store.audit(AuditEvent.make(who, "kill_switch", "engine", "ON: no new actions" if on else "OFF"))

    def killed(self) -> bool:
        return bool(self.store.control("kill", False))

    def pause_agent(self, agent_id: str, on: bool, who: str = "grayson") -> None:
        paused = set(self.store.control("paused_agents", []))
        (paused.add if on else paused.discard)(agent_id)
        self.store.set_control("paused_agents", sorted(paused))
        self.store.audit(AuditEvent.make(who, "pause" if on else "resume", agent_id))

    def paused(self, agent_id: str) -> bool:
        return agent_id in set(self.store.control("paused_agents", []))

    # ---------------------------------------------------------------- submit
    def submit(self, spec: TaskSpec, who: str = "engine") -> Task:
        spec.validate()
        contract = self.agents.get(spec.agent_id)
        if not contract:
            raise EngineError(f"unknown agent {spec.agent_id!r}")
        bad = [x for x in spec.tools if not contract.allows_tool(x)]
        if bad:
            raise EngineError(f"agent {contract.id} may not use tools {bad}")
        for cap in spec.capabilities:
            if not contract.has(cap):
                raise EngineError(f"agent {contract.id} is not allowed {cap.value}")
        if spec.idempotency_key is None:
            spec.idempotency_key = idempotency_key(spec.agent_id, spec.kind, spec.input_ref)
        existing = self.store.find_task_by_key(spec.idempotency_key)
        if existing:
            return existing  # never a second task for the same work
        ts = now_iso()
        task = Task(id=new_id("task"), spec=spec, status=TaskStatus.QUEUED, created_at=ts, updated_at=ts)
        self.store.put_task(task)
        self.store.audit(AuditEvent.make(who, "submit", task.id, f"{spec.kind} for {spec.agent_id}"))
        return task

    # ---------------------------------------------------------------- transitions
    def _move(self, task: Task, to: TaskStatus, who: str = "engine", detail: str = "") -> Task:
        if to not in TRANSITIONS[task.status]:
            raise EngineError(f"illegal transition {task.status.value} → {to.value} for {task.id}")
        task.status = to
        task.updated_at = now_iso()
        self.store.put_task(task)
        self.store.audit(AuditEvent.make(who, to.value, task.id, detail))
        return task

    def cancel(self, task_id: str, who: str = "grayson", why: str = "") -> Task:
        task = self._need(task_id)
        if task.status in TERMINAL:
            raise EngineError(f"{task_id} is already {task.status.value}")
        return self._move(task, TaskStatus.CANCELLED, who, why)

    def retry(self, task_id: str, who: str = "grayson") -> Task:
        """Operator-only: put a failed task back in the queue with a fresh retry budget."""
        task = self._need(task_id)
        if task.status != TaskStatus.FAILED:
            raise EngineError("only failed tasks can be retried by hand")
        task.attempts = 0
        task.next_eligible_at = None
        return self._move(task, TaskStatus.QUEUED, who, "manual retry")

    def decide(self, approval_id: str, approve: bool, who: str = "grayson") -> Approval:
        a = self.store.get_approval(approval_id)
        if not a:
            raise EngineError("no such approval")
        if a.status != ApprovalStatus.PROPOSED:
            raise EngineError(f"approval already {a.status.value}")
        a.status = ApprovalStatus.APPROVED if approve else ApprovalStatus.DECLINED
        a.decided_at, a.decided_by = now_iso(), who
        self.store.put_approval(a)
        self.store.audit(AuditEvent.make(who, "approve" if approve else "decline", a.id, a.title))
        if a.task_id:
            task = self._need(a.task_id)
            if task.status == TaskStatus.NEEDS_APPROVAL:
                self._move(task, TaskStatus.QUEUED if approve else TaskStatus.CANCELLED, who, f"approval {a.status.value}")
        return a

    # ---------------------------------------------------------------- claiming + running
    def _eligible(self, task: Task) -> bool:
        if self.paused(task.spec.agent_id):
            return False
        if task.next_eligible_at and task.next_eligible_at > now_iso():
            return False
        for dep in task.spec.depends_on:
            d = self.store.get_task(dep)
            if not d or d.status != TaskStatus.SUCCEEDED:
                return False
        return True

    def claim(self) -> t.Optional[Task]:
        """Next runnable task, or None. Honors the kill switch, pauses, backoff and dependencies."""
        if self.killed():
            return None
        for task in self.store.tasks(TaskStatus.QUEUED):
            if self._eligible(task):
                return task
        return None

    def run_task(self, task: Task) -> Run:
        contract = self.agents[task.spec.agent_id]
        handler = self.handlers.get(task.spec.kind)
        attempt = task.attempts + 1
        run = Run(id=new_id("run"), task_id=task.id, agent_id=contract.id, attempt=attempt, started_at=now_iso(),
                  heartbeat_at=now_iso(), runner=self.runner, model=task.spec.model_hint)
        task.attempts = attempt
        task.run_ids.append(run.id)
        self.store.put_run(run)
        self._move(task, TaskStatus.RUNNING, detail=f"attempt {attempt} run {run.id}")
        ctx = RunContext(self, task, run, contract)
        pol = contract.error_policy
        if handler is None:
            return self._finish(task, run, TaskStatus.FAILED, error=f"no handler registered for kind {task.spec.kind!r}", error_class="permanent",
                                recovery="Register a handler for this kind, then retry the task.")
        try:
            # pre-flight gate: a spec that declares a gated capability needs an approved id before any work.
            for cap in task.spec.capabilities:
                if cap in GATED:
                    ctx.require(cap, f"{task.spec.kind} needs {cap.value}", f"Task {task.id} for agent {contract.id} declares {cap.value}.")
            out = _with_timeout(lambda: handler(task, ctx), pol.timeout_s)
            if not isinstance(out, dict):
                raise PermanentError("handler must return a dict")
            validation = out.get("validation") or {"ok": True, "checks": []}
            if validation.get("ok") is False:
                raise PermanentError("validation failed: " + "; ".join(str(c) for c in validation.get("checks", []) if c))
            if ctx.memory_items is not None:
                validation = dict(validation, memory_items=ctx.memory_items)
            run.validation = validation
            task.output_ref = out.get("output_ref")
            return self._finish(task, run, TaskStatus.SUCCEEDED, output_ref=out.get("output_ref"))
        except NeedsApproval as e:
            a = Approval(id=new_id("apr"), task_id=task.id, capability=e.capability, title=e.title, why=e.why, cost=e.cost, risk=e.risk,
                         expires_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds").replace("+00:00", "Z"))
            self.store.put_approval(a)
            task.approval_id = a.id
            task.attempts -= 1  # waiting on a human is not a failed attempt
            return self._finish(task, run, TaskStatus.NEEDS_APPROVAL, error=e.title, error_class="needs_approval",
                                recovery="Approve or decline it in the Factory (More → Inbox) or with: python -m factory.engine approve " + a.id)
        except _Timeout:
            return self._fail_or_retry(task, run, pol, "timeout", f"handler exceeded {pol.timeout_s}s", "Nothing to do: it retries with backoff. If it keeps timing out, raise timeout_s on the agent contract.")
        except TransientError as e:
            return self._fail_or_retry(task, run, pol, getattr(e, "error_class", "transient"), str(e), "Nothing to do: it retries with backoff.")
        except PermanentError as e:
            return self._finish(task, run, TaskStatus.FAILED, error=str(e), error_class="permanent",
                                recovery="Fix the input or the contract, then: python -m factory.engine retry " + task.id)
        except Exception as e:  # unknown: treat as transient but bounded
            return self._fail_or_retry(task, run, pol, "transient", f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}",
                                       "Unexpected error; retries with backoff. Check the run's error in the journal.")

    def _fail_or_retry(self, task: Task, run: Run, pol, error_class: str, error: str, recovery: str) -> Run:
        retriable = error_class in pol.retry_on and task.attempts <= pol.max_retries
        if retriable:
            delay = pol.delay_for(task.attempts - 1)
            task.next_eligible_at = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat(timespec="seconds").replace("+00:00", "Z")
            run.status, run.finished_at, run.error, run.error_class, run.recovery = TaskStatus.QUEUED, now_iso(), scrub(error)[:1000], error_class, f"retry {task.attempts}/{pol.max_retries} in {delay:.0f}s"
            self.store.put_run(run)
            task.last_error = run.error
            self._move(task, TaskStatus.QUEUED, detail=f"{error_class}; retry in {delay:.0f}s")
            return run
        return self._finish(task, run, TaskStatus.FAILED, error=error, error_class=error_class,
                            recovery=recovery if task.attempts <= pol.max_retries else f"retries exhausted ({pol.max_retries}). " + recovery)

    def _finish(self, task: Task, run: Run, status: TaskStatus, error: str | None = None, error_class: str | None = None,
                recovery: str | None = None, output_ref: str | None = None) -> Run:
        run.status, run.finished_at = status, now_iso()
        run.error = scrub(error)[:1000] if error else None
        run.error_class, run.recovery, run.output_ref = error_class, recovery, output_ref
        self.store.put_run(run)
        task.last_error = run.error
        if task.status != status:
            self._move(task, status, detail=run.error or (output_ref or ""))
        self._learn(task, run, status)
        return run

    def _learn(self, task: Task, run: Run, status: TaskStatus) -> None:
        """Phase 9 after-work hook on the shared runner: every terminal or parked attempt leaves one row in the learning
        store with the run id as its stable key (a replay never duplicates it). Tool errors, timeouts and budget stops
        are recorded WITHOUT a score; a handler that returned a real evaluation (validation["evaluation"]) keeps it.
        Nothing here can fail the task: a learning-store problem is audited and swallowed."""
        if not getattr(self, "learning", False) or status == TaskStatus.QUEUED:
            return
        try:
            from factory.learning.brain import AgentBrain
            brain = AgentBrain(self.store)
            scope = task.spec.meta.get("scope") or self.scope_for(task.spec.agent_id)
            mode = task.spec.meta.get("mode") or ("offline" if self.runner in ("test", "mock") else "production")
            version = f"{task.spec.kind}@{self.agents[task.spec.agent_id].version}"
            usage = run.usage.to_dict() if run.usage else None
            ev = (run.validation or {}).get("evaluation") if isinstance(run.validation, dict) else None
            if status == TaskStatus.SUCCEEDED and isinstance(ev, dict) and ev.get("rubric_id"):
                brain.log(run.id, scope, task.spec.agent_id, version, {"kind": task.spec.kind, "input_ref": task.spec.input_ref}, run.output_ref, ev, mode=mode, final=True,
                          artifact_ref=run.output_ref or "", kind="score", task_id=task.id, attempt=run.attempt, usage=usage)
                if not ev.get("passed"):
                    brain.remember(scope, task.spec.agent_id, "mistake", scrub({"kind": task.spec.kind, "input_ref": task.spec.input_ref, "score": ev.get("score"), "gaps": (ev.get("gaps") or [])[:3], "blockers": (ev.get("blockers") or [])[:5]})[:12000],
                                   f"evaluation {run.id}; suspected cause requires validation")
            elif status == TaskStatus.SUCCEEDED:
                brain.log_run(run.id, scope, task.spec.agent_id, task=task.spec.kind, outcome="done", mode=mode, version=version, started=run.started_at, finished=run.finished_at,
                              extra={"task_id": task.id, "input_ref": task.spec.input_ref, "output_ref": run.output_ref, "checks": (run.validation or {}).get("checks", [])[:10], "usage": usage})
            elif status == TaskStatus.NEEDS_APPROVAL:
                brain.log_run(run.id, scope, task.spec.agent_id, task=task.spec.kind, outcome="paused", mode=mode, version=version, needs_you=run.error or "approval", started=run.started_at,
                              finished=run.finished_at, extra={"task_id": task.id, "approval_id": task.approval_id})
            else:  # FAILED: tool / permanent / timeout / budget: no score is invented
                brain.log_error(run.id, scope, task.spec.agent_id, task={"kind": task.spec.kind, "input_ref": task.spec.input_ref}, error=run.error or "failed",
                                error_class=run.error_class or "permanent", mode=mode, version=version, attempt=run.attempt, task_id=task.id)
                brain.remember(scope, task.spec.agent_id, "mistake", f"{task.spec.kind} on {task.spec.input_ref} failed ({run.error_class}): {(run.error or '')[:300]}", f"engine run {run.id}",
                               tags={"error_class": run.error_class, "kind": task.spec.kind})
        except Exception as e:  # noqa: BLE001
            self.store.audit(AuditEvent.make("engine", "learning_hook_failed", run.id, scrub(f"{type(e).__name__}: {e}")))

    # ---------------------------------------------------------------- loop + recovery
    def tick(self, max_tasks: int = 10) -> list[Run]:
        """One worker pass: claim and run up to `max_tasks`. Records the pass as a heartbeat."""
        self.store.set_control("last_tick", {"at": now_iso(), "runner": self.runner})
        done: list[Run] = []
        for _ in range(max_tasks):
            task = self.claim()
            if not task:
                break
            done.append(self.run_task(task))
        return done

    def recover(self) -> list[str]:
        """Stalled RUNNING tasks (no heartbeat within stalled_after_s) go back to the queue or fail."""
        fixed = []
        for task in self.store.tasks(TaskStatus.RUNNING):
            contract = self.agents.get(task.spec.agent_id)
            if not contract:
                continue
            runs = self.store.runs_for(task.id)
            run = runs[-1] if runs else None
            hb = run.heartbeat_at if run and run.heartbeat_at else task.updated_at
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(hb.replace("Z", "+00:00"))).total_seconds()
            if age <= contract.error_policy.stalled_after_s:
                continue
            if run:
                self._fail_or_retry(task, run, contract.error_policy, "timeout", f"stalled: no heartbeat for {int(age)}s",
                                    "The runner died mid-task. It retries from its last checkpoint.")
            else:
                self._move(task, TaskStatus.QUEUED, detail="stalled with no run record")
            fixed.append(task.id)
        if fixed:
            self.store.audit(AuditEvent.make("engine", "recover", "engine", f"re-queued {len(fixed)} stalled task(s)"))
        return fixed

    def status(self) -> dict:
        last = self.store.control("last_tick")
        return {"schema": self.store.schema_version(), "kill": self.killed(), "paused_agents": self.store.control("paused_agents", []),
                "counts": self.store.counts(), "last_tick": last, "pending_approvals": len(self.store.approvals("proposed")),
                "usage_today": self.store.usage_summary(now_iso()[:10]), "note": "runs only when something calls tick(); last_tick is the truth"}

    # ---------------------------------------------------------------- utils
    def _need(self, task_id: str) -> Task:
        task = self.store.get_task(task_id)
        if not task:
            raise EngineError(f"no task {task_id}")
        return task


class _Timeout(Exception):
    pass


def _with_timeout(fn: t.Callable[[], dict], seconds: int) -> dict:
    """Run fn in a thread and give up after `seconds`. The thread is left to finish on its own
    (daemon) — it cannot be killed in Python — but its result is discarded and the run is recorded as a timeout."""
    box: dict = {}

    def target():
        try:
            box["out"] = fn()
        except BaseException as e:  # noqa: BLE001
            box["err"] = e

    th = threading.Thread(target=target, daemon=True)
    th.start()
    th.join(seconds)
    if th.is_alive():
        raise _Timeout()
    if "err" in box:
        raise box["err"]
    return box.get("out", {})
