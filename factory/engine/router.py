"""Model router, cache, cost tracking and budgets (add-on Phase 5).

Routing
- `tier` comes from the task's `model_hint`, else from the kind: classification / extraction / formatting /
  adaptation → "quick"; research, review, planning, inspection, architecture → "strong" (`KIND_TIERS`).
- Escalation: a retry after a validation failure, or `uncertain=True` from the caller, bumps quick → strong.
- Providers are tried in order (free Claude-session hand-off first, paid API last) and only if `available()`.
  The paid provider is additionally gated: it is used only when control `paid_provider_approval` names an
  APPROVED approval with capability SPEND_MONEY. Without it the router says so and stops; it never silently
  skips to a paid vendor.

Cache
- Key = sha256(provider, model, prompt_version, data_version, system, prompt). A caller marks a call
  `cacheable=True` only for safe, repeatable work (classifying a fixed text, formatting); anything that
  depends on "now" (prices, stats, trends) must not be cached. Rows carry `data_version`: bump
  `GM_DATA_VERSION` (env or control) and every older row is ignored and purged. TTL per call (default 24h).
- Dedup: the same key inside one process is served from memory, so two agents asking the same question in
  one tick cost one call.

Cost tracking
- `ModelUsage` is recorded for every call with whatever the provider reported. Unknown stays None and the
  summary reports "unknown calls" separately; nothing is estimated and no price table exists here.

Budgets (hard stops → `BudgetExceeded`, a PermanentError so the task fails safely, nothing is deleted)
- per task: `Budget.max_calls_per_task` / `max_tokens_per_task` / `max_usd_per_task` from the agent contract;
- per day (project-wide): control `budget` = {"daily_calls": N, "daily_usd": X}; usd is enforced only
  against *known* cost, and the router also stops when `unknown_calls` exceed `daily_unknown_calls` so a
  provider that never reports cost cannot run away;
- runaway loops: `LOOP_GUARD` identical prompts in a row within one task stops the task.
"""
from __future__ import annotations

import hashlib
import os
import typing as t
from datetime import datetime, timedelta, timezone

from .contracts import ApprovalStatus, Budget, Capability, ModelUsage, now_iso
from .engine import PermanentError
from .providers import Completion, Provider, Tier, default_providers
from .store import Store

KIND_TIERS: dict[str, Tier] = {
    "research": "strong", "quality": "strong", "distribution": "strong", "engineering": "strong", "product": "strong",
    "channel": "quick", "publish": "quick", "analytics": "quick", "classify": "quick", "extract": "quick", "format": "quick", "engine": "quick",
}
DEFAULT_TTL_S = 24 * 3600
LOOP_GUARD = 4
PROMPT_VERSION = "2026-10-21"


class BudgetExceeded(PermanentError):
    pass


class NoProvider(PermanentError):
    pass


def data_version(store: Store | None = None) -> str:
    return os.environ.get("GM_DATA_VERSION") or (store.control("data_version", "1") if store else "1")


class Router:
    def __init__(self, store: Store, providers: list[Provider] | None = None, clock: t.Callable[[], datetime] | None = None):
        self.store = store
        self.providers = providers if providers is not None else default_providers()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._inflight: dict[str, Completion] = {}
        self._task_state: dict[str, dict] = {}  # task_id → {calls, tokens, usd, last_prompts}

    # ---------------------------------------------------------------- routing
    def tier_for(self, kind: str, model_hint: str | None = None, attempt: int = 1, uncertain: bool = False) -> Tier:
        tier: Tier = model_hint if model_hint in ("quick", "strong") else KIND_TIERS.get(kind.split(".")[0], "quick")  # type: ignore[assignment]
        if tier == "quick" and (attempt > 1 or uncertain):
            tier = "strong"  # escalate after a failed validation or when the caller is unsure
        return tier

    def paid_allowed(self) -> bool:
        aid = self.store.control("paid_provider_approval")
        a = self.store.get_approval(aid) if aid else None
        return bool(a and a.status == ApprovalStatus.APPROVED and a.capability == Capability.SPEND_MONEY)

    def pick(self, tier: Tier) -> Provider:
        skipped = []
        for p in self.providers:
            if not p.available():
                skipped.append(f"{p.id}: not configured")
                continue
            if getattr(p, "id", "") == "anthropic_api" and not self.paid_allowed():
                skipped.append("anthropic_api: paid; needs an approved spend_money approval (control paid_provider_approval)")
                continue
            if p.models().get(tier) in (None, "unset"):
                skipped.append(f"{p.id}: no model for tier {tier}")
                continue
            return p
        raise NoProvider("no model provider can take this call: " + "; ".join(skipped))

    # ---------------------------------------------------------------- budgets
    def _daily(self) -> dict:
        b = self.store.control("budget", {}) or {}
        return {"daily_calls": b.get("daily_calls", 400), "daily_usd": b.get("daily_usd"), "daily_unknown_calls": b.get("daily_unknown_calls", 400)}

    def check_budget(self, task_id: str, budget: Budget) -> None:
        st = self._task_state.setdefault(task_id, {"calls": 0, "tokens": 0, "usd": 0.0, "last_prompts": []})
        if budget.max_calls_per_task is not None and st["calls"] >= budget.max_calls_per_task:
            raise BudgetExceeded(f"task call budget reached ({budget.max_calls_per_task})")
        if budget.max_tokens_per_task is not None and st["tokens"] >= budget.max_tokens_per_task:
            raise BudgetExceeded(f"task token budget reached ({budget.max_tokens_per_task})")
        if budget.max_usd_per_task is not None and st["usd"] >= budget.max_usd_per_task:
            raise BudgetExceeded(f"task spend budget reached (${budget.max_usd_per_task})")
        d = self._daily()
        day = self.store.usage_summary(now_iso()[:10])
        if d["daily_calls"] is not None and day["calls"] >= d["daily_calls"]:
            raise BudgetExceeded(f"daily call budget reached ({d['daily_calls']})")
        if d["daily_usd"] is not None and (day["cost_usd_known"] or 0) >= d["daily_usd"]:
            raise BudgetExceeded(f"daily spend budget reached (${d['daily_usd']} known cost)")
        if d["daily_unknown_calls"] is not None and day["cost_unknown_calls"] >= d["daily_unknown_calls"]:
            raise BudgetExceeded(f"daily limit on calls with unknown cost reached ({d['daily_unknown_calls']}); set a provider that reports cost or raise budget.daily_unknown_calls")

    def _loop_guard(self, task_id: str, prompt_sha: str) -> None:
        st = self._task_state[task_id]
        lp = st["last_prompts"]
        lp.append(prompt_sha)
        del lp[:-LOOP_GUARD]
        if len(lp) == LOOP_GUARD and len(set(lp)) == 1:
            raise BudgetExceeded(f"runaway loop: the same prompt {LOOP_GUARD} times in a row")

    # ---------------------------------------------------------------- the call
    def complete(self, task_id: str, kind: str, prompt: str, *, budget: Budget | None = None, model_hint: str | None = None, attempt: int = 1,
                 uncertain: bool = False, cacheable: bool = False, ttl_s: int = DEFAULT_TTL_S, system: str | None = None,
                 max_tokens: int = 800, run_id: str | None = None) -> Completion:
        budget = budget or Budget()
        self.check_budget(task_id, budget)
        tier = self.tier_for(kind, model_hint, attempt, uncertain)
        provider = self.pick(tier)
        model = provider.models()[tier]
        dv = data_version(self.store)
        key = hashlib.sha256("\x1f".join([provider.id, model, PROMPT_VERSION, dv, system or "", prompt]).encode()).hexdigest()
        psha = key[:16]
        self._loop_guard(task_id, psha)
        st = self._task_state[task_id]
        if key in self._inflight:  # dedup inside this process
            c = self._inflight[key]
            self._record(task_id, run_id, ModelUsage(provider=c.provider, model=c.model, cached=True, calls=1), st)
            return Completion(text=c.text, usage=ModelUsage(provider=c.provider, model=c.model, cached=True), provider=c.provider, model=c.model, cached=True, meta=dict(c.meta))
        if cacheable:
            hit = self.store.cache_get(key, dv, self.clock().isoformat(timespec="seconds").replace("+00:00", "Z"))
            if hit:
                u = ModelUsage(provider=provider.id, model=model, cached=True, calls=1)
                self._record(task_id, run_id, u, st)
                return Completion(text=hit["text"], usage=u, provider=provider.id, model=model, cached=True, meta={"cache": "hit", "hits": hit["hits"] + 1})
        c = provider.complete(prompt, tier=tier, max_tokens=max_tokens, system=system)
        self._record(task_id, run_id, c.usage, st)
        self._inflight[key] = c
        if cacheable:
            exp = (self.clock() + timedelta(seconds=ttl_s)).isoformat(timespec="seconds").replace("+00:00", "Z")
            self.store.cache_put(key, provider.id, model, PROMPT_VERSION, dv, exp, c.text, c.usage.to_dict())
        return c

    def _record(self, task_id: str, run_id: str | None, u: ModelUsage, st: dict) -> None:
        self.store.put_usage(run_id, u)
        st["calls"] += u.calls
        st["tokens"] += (u.tokens_in or 0) + (u.tokens_out or 0)
        st["usd"] += u.cost_usd or 0.0

    # ---------------------------------------------------------------- reporting
    def report(self, day: str | None = None) -> dict:
        s = self.store.usage_summary(day)
        d = self._daily()
        s["budget"] = d
        s["cache"] = self.store.cache_stats()
        s["providers"] = {p.id: p.available() for p in self.providers}
        s["paid_allowed"] = self.paid_allowed()
        s["cost_note"] = "cost is only what providers reported; 'unknown' calls are counted, never priced"
        return s
