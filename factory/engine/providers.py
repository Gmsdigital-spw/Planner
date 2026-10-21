"""Provider-neutral model interface (add-on Phase 4).

Agents never name a vendor. They ask the router (Phase 5) for a `tier` and get back a `Completion`
with whatever usage the provider actually reported. Rules:
- a provider is only "available" when its configuration is really present (`available()` checks env);
- usage that the provider did not report stays None (printed as "unknown"), never estimated;
- no prices live here. Cost is attached only when a provider returns it (none of ours do today);
- MockProvider is the only one tests use; it is labelled mocked in every record it writes.

Providers in this file:
- MockProvider            deterministic; for tests and `tick` demos. usage.tokens are real counts of the mock's own text.
- ClaudeSessionProvider   the crews run *inside* a Claude scheduled task on Grayson's plan: the model is the
                          session itself. This adapter cannot call a model from Python; it records a hand-off
                          request (`factory/engine/handoff/<id>.json`) that the running crew picks up, and reports
                          usage as unknown. Available only when GM_CLAUDE_SESSION=1 (set by a crew's STEP 0).
- AnthropicApiProvider    uses the Anthropic HTTP API *only if* ANTHROPIC_API_KEY is set. It is a paid service, so
                          the engine treats it as SPEND_MONEY-gated (Phase 5 routing will require an approved budget
                          before routing anything here). Today no key is configured → available() is False.
"""
from __future__ import annotations

import hashlib
import json
import os
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from .contracts import ModelUsage, new_id, now_iso, scrub

Tier = t.Literal["quick", "strong"]
HERE = Path(__file__).resolve().parent


@dataclass
class Completion:
    text: str
    usage: ModelUsage
    provider: str
    model: str
    cached: bool = False
    meta: dict = field(default_factory=dict)


class Provider(t.Protocol):
    id: str
    def available(self) -> bool: ...
    def models(self) -> dict[Tier, str]: ...
    def complete(self, prompt: str, tier: Tier = "quick", max_tokens: int = 800, system: str | None = None) -> Completion: ...


class MockProvider:
    """Deterministic. `script` maps a substring of the prompt → reply; otherwise it echoes a summary."""
    id = "mock"

    def __init__(self, script: dict[str, str] | None = None, fail_on: str | None = None):
        self.script = script or {}
        self.fail_on = fail_on
        self.calls: list[dict] = []

    def available(self) -> bool:
        return True

    def models(self) -> dict[Tier, str]:
        return {"quick": "mock-quick", "strong": "mock-strong"}

    def complete(self, prompt: str, tier: Tier = "quick", max_tokens: int = 800, system: str | None = None) -> Completion:
        self.calls.append({"tier": tier, "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:12]})
        if self.fail_on and self.fail_on in prompt:
            raise RuntimeError("mock provider failure: " + self.fail_on)
        reply = next((v for k, v in self.script.items() if k in prompt), None)
        if reply is None:
            reply = json.dumps({"mocked": True, "tier": tier, "prompt_chars": len(prompt)})
        model = self.models()[tier]
        return Completion(text=reply, provider=self.id, model=model,
                          usage=ModelUsage(provider=self.id, model=model, tokens_in=len(prompt.split()), tokens_out=len(reply.split()), cost_usd=None),
                          meta={"mocked": True})


class ClaudeSessionProvider:
    """Hand-off to the Claude session a crew is already running in. See module docstring."""
    id = "claude_session"

    def __init__(self, handoff_dir: Path | str = HERE / "handoff"):
        self.dir = Path(handoff_dir)

    def available(self) -> bool:
        return os.environ.get("GM_CLAUDE_SESSION") == "1"

    def models(self) -> dict[Tier, str]:
        return {"quick": "claude-session:quick", "strong": "claude-session:strong"}

    def complete(self, prompt: str, tier: Tier = "quick", max_tokens: int = 800, system: str | None = None) -> Completion:
        if not self.available():
            raise RuntimeError("claude_session provider is not available outside a Claude scheduled task (GM_CLAUDE_SESSION=1)")
        self.dir.mkdir(parents=True, exist_ok=True)
        hid = new_id("handoff")
        req = {"id": hid, "at": now_iso(), "tier": tier, "max_tokens": max_tokens, "system": system, "prompt": scrub(prompt)}
        (self.dir / f"{hid}.json").write_text(json.dumps(req, indent=1), encoding="utf-8")
        model = self.models()[tier]
        # The crew answers by writing <id>.reply.json; until then the text is the hand-off marker.
        reply = self.dir / f"{hid}.reply.json"
        text = json.loads(reply.read_text())["text"] if reply.exists() else f"[handoff {hid} written; the running crew answers it]"
        return Completion(text=text, provider=self.id, model=model, usage=ModelUsage(provider=self.id, model=model), meta={"handoff": hid})


class AnthropicApiProvider:
    """Paid API. Only usable with ANTHROPIC_API_KEY set AND (Phase 5) an approved budget. Never imports a key into logs."""
    id = "anthropic_api"
    ENDPOINT = "https://api.anthropic.com/v1/messages"

    def available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def models(self) -> dict[Tier, str]:
        # configuration, not an availability claim: the names come from env so nobody hard-codes a vendor's catalogue
        return {"quick": os.environ.get("GM_MODEL_QUICK", "unset"), "strong": os.environ.get("GM_MODEL_STRONG", "unset")}

    def complete(self, prompt: str, tier: Tier = "quick", max_tokens: int = 800, system: str | None = None) -> Completion:
        if not self.available():
            raise RuntimeError("anthropic_api provider is not configured (no ANTHROPIC_API_KEY)")
        model = self.models()[tier]
        if model == "unset":
            raise RuntimeError(f"no model configured for tier {tier!r} (set GM_MODEL_QUICK / GM_MODEL_STRONG)")
        import urllib.request
        body = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["system"] = system
        req = urllib.request.Request(self.ENDPOINT, data=json.dumps(body).encode(), method="POST",
                                     headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (fixed https endpoint)
            data = json.loads(r.read())
        text = "".join(p.get("text", "") for p in data.get("content", []) if p.get("type") == "text")
        u = data.get("usage") or {}
        usage = ModelUsage(provider=self.id, model=data.get("model", model), tokens_in=u.get("input_tokens"), tokens_out=u.get("output_tokens"), cost_usd=None)
        return Completion(text=text, provider=self.id, model=usage.model, usage=usage, meta={"id": data.get("id")})


def default_providers() -> list[Provider]:
    """Order matters for the router (Phase 5): free session first, paid API last. Mock is never in this list."""
    return [ClaudeSessionProvider(), AnthropicApiProvider()]


def availability() -> dict[str, dict]:
    """What is really configured right now. Used by `status` and the Phase 5 router."""
    out = {}
    for p in default_providers():
        out[p.id] = {"available": p.available(), "models": p.models() if p.available() else {}, "paid": p.id == "anthropic_api"}
    return out
