"""Typed contracts for the GM Factory engine (add-on Phase 3).

Every record the engine stores is one of the dataclasses below. They are the single schema:
`to_json_schema()` exports JSON Schema, `to_typescript()` exports `ts/contracts.d.ts`, and
`store.py` maps them to SQLite tables. No third-party dependencies.

Rules baked in:
- unknown numbers are `None` and are printed as "unknown", never 0 (`fmt_num`);
- a task may only use tools on its agent's allow-list (`AgentContract.tools`);
- consequential capabilities (publish, spend, credentials, live trading) need an approval id;
- nothing here knows a secret; `scrub()` removes anything token-shaped before it is logged.
"""
from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import re
import typing as t
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

SCHEMA_VERSION = 1


# ------------------------------------------------------------------ helpers
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def fmt_num(v: t.Optional[float], unit: str = "") -> str:
    """Real numbers only: None is 'unknown', never 0."""
    if v is None:
        return "unknown"
    return f"{v:,.2f}{unit}" if isinstance(v, float) and not v.is_integer() else f"{int(v):,}{unit}"


_SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9]{8,}|ghp_[a-z0-9]{20,}|xox[baprs]-[a-z0-9-]{10,}|AKIA[0-9A-Z]{16}|"
    r"ey[a-z0-9_-]{20,}\.[a-z0-9_-]{10,}\.[a-z0-9_-]{10,}|"
    r"(?:api[_-]?key|secret|token|password|authorization)\s*[=:]\s*['\"]?[^\s'\",]{6,})"
)


def scrub(text: t.Any) -> str:
    """Secret-safe logging: anything token-shaped becomes [redacted]."""
    s = text if isinstance(text, str) else json.dumps(text, default=str)
    return _SECRET_RE.sub("[redacted]", s)


def idempotency_key(*parts: t.Any) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ------------------------------------------------------------------ enums
class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_APPROVAL = "needs_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL = {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED}

# legal transitions (from → to). Anything else raises in the engine.
TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.QUEUED: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.NEEDS_APPROVAL, TaskStatus.QUEUED, TaskStatus.CANCELLED},
    TaskStatus.NEEDS_APPROVAL: {TaskStatus.QUEUED, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.SUCCEEDED: set(),
    TaskStatus.FAILED: {TaskStatus.QUEUED},  # explicit retry by an operator only
    TaskStatus.CANCELLED: set(),
}


class AgentRole(str, enum.Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    PRODUCT_FACTORY = "product_factory"
    QUALITY = "quality"
    DISTRIBUTION = "distribution"
    CHANNEL_ADAPTER = "channel_adapter"
    PUBLISHING = "publishing"
    ANALYTICS = "analytics"
    MODEL_COST = "model_cost"
    ENGINEERING = "engineering"


class Capability(str, enum.Enum):
    """Consequential things an agent may be allowed to do. Each needs an approval id on the task."""
    PUBLISH_PUBLIC = "publish_public"
    SPEND_MONEY = "spend_money"
    CHANGE_CREDENTIALS = "change_credentials"
    DESTRUCTIVE_CHANGE = "destructive_change"
    TRADE_LIVE = "trade_live"  # exists so tests can prove nobody has it


class Channel(str, enum.Enum):
    """V7 keep-list only. No Gumroad, no Funnel."""
    ETSY = "etsy"
    PINTEREST = "pinterest"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE_SHOP = "youtube_shop"
    GMULA = "gmula"


class ApprovalStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    DECLINED = "declined"
    EXPIRED = "expired"


class IntegrationState(str, enum.Enum):
    CONNECTED = "connected"
    MOCKED = "mocked"
    MISSING = "missing"
    UNVERIFIED = "unverified"


# ------------------------------------------------------------------ base
class Record:
    """Mixin: dict/JSON round-trip and light validation for every contract."""

    def to_dict(self) -> dict:
        def conv(v):
            if isinstance(v, enum.Enum):
                return v.value
            if dataclasses.is_dataclass(v):
                return v.to_dict() if isinstance(v, Record) else dataclasses.asdict(v)
            if isinstance(v, list):
                return [conv(x) for x in v]
            if isinstance(v, dict):
                return {k: conv(x) for k, x in v.items()}
            return v

        return {f.name: conv(getattr(self, f.name)) for f in dataclasses.fields(self)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    @classmethod
    def from_dict(cls, d: dict):
        kw = {}
        for f in dataclasses.fields(cls):
            if f.name not in d:
                continue
            v = d[f.name]
            kw[f.name] = _coerce(f.type, v)
        obj = cls(**kw)  # type: ignore[arg-type]
        obj.validate()
        return obj

    def validate(self) -> None:  # overridden where it matters
        return


def _coerce(tp: t.Any, v: t.Any):
    """Turn plain JSON back into enums / nested records using the annotation."""
    if v is None:
        return None
    origin = t.get_origin(tp)
    args = t.get_args(tp)
    if isinstance(tp, str):  # from __future__ annotations: resolve by name
        tp = _resolve(tp)
        origin, args = t.get_origin(tp), t.get_args(tp)
    if origin is t.Union or (origin is not None and str(origin) == "<class 'types.UnionType'>"):
        inner = [a for a in args if a is not type(None)]
        return _coerce(inner[0], v) if len(inner) == 1 else v
    if origin is list:
        return [_coerce(args[0], x) for x in v] if args else list(v)
    if origin is dict:
        return dict(v)
    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        return tp(v)
    if isinstance(tp, type) and dataclasses.is_dataclass(tp) and isinstance(v, dict):
        return tp.from_dict(v) if issubclass(tp, Record) else tp(**v)
    return v


def _resolve(name: str):
    ns = globals()
    try:
        return eval(name, {"t": t, "Optional": t.Optional, "list": list, "dict": dict, **ns})  # noqa: S307 (own module names only)
    except Exception:
        return t.Any


# ------------------------------------------------------------------ contracts
@dataclass
class ErrorPolicy(Record):
    max_retries: int = 3
    backoff_base_s: float = 2.0  # delay = base * 2**attempt, capped
    backoff_cap_s: float = 300.0
    timeout_s: int = 600
    stalled_after_s: int = 1800  # running with no heartbeat for this long = stalled
    retry_on: list[str] = field(default_factory=lambda: ["transient", "rate_limited", "timeout"])

    def validate(self) -> None:
        if self.max_retries < 0 or self.max_retries > 10:
            raise ValueError("max_retries must be 0..10")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be positive")

    def delay_for(self, attempt: int) -> float:
        return min(self.backoff_cap_s, self.backoff_base_s * (2 ** max(0, attempt)))


@dataclass
class Budget(Record):
    """Per-task and per-day ceilings. None = not limited (reported, not assumed)."""
    max_calls_per_task: t.Optional[int] = 20
    max_tokens_per_task: t.Optional[int] = None
    max_usd_per_task: t.Optional[float] = None
    max_usd_per_day: t.Optional[float] = None


@dataclass
class AgentContract(Record):
    id: str
    name: str
    role: AgentRole
    responsibilities: list[str]
    inputs: list[str]  # named input kinds, e.g. "brief", "product_manifest"
    outputs: list[str]
    tools: list[str]  # allow-list; a task naming any other tool is rejected
    capabilities: list[Capability] = field(default_factory=list)
    error_policy: ErrorPolicy = field(default_factory=ErrorPolicy)
    budget: Budget = field(default_factory=Budget)
    skill_path: t.Optional[str] = None  # factory/skills/<agent>/SKILL.md
    version: int = 1

    def validate(self) -> None:
        if not self.id or not re.fullmatch(r"[a-z][a-z0-9_]{1,30}", self.id):
            raise ValueError("agent id must be lowercase snake_case")
        if Capability.TRADE_LIVE in self.capabilities:
            raise ValueError("TRADE_LIVE is never granted to an agent (separate authorization path)")
        self.error_policy.validate()

    def allows_tool(self, tool: str) -> bool:
        return tool in self.tools

    def has(self, cap: Capability) -> bool:
        return cap in self.capabilities


@dataclass
class TaskSpec(Record):
    """What to do. Immutable after submit (the engine copies it into a Task)."""
    agent_id: str
    kind: str  # e.g. "research.brief", "publish.pin"
    input_ref: str  # path/doc id of the input, never the payload itself
    tools: list[str] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    idempotency_key: t.Optional[str] = None
    depends_on: list[str] = field(default_factory=list)  # task ids
    priority: int = 5  # 1 high .. 9 low
    model_hint: t.Optional[str] = None  # "quick" | "strong" | None (router decides, Phase 5)
    meta: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not self.kind or "." not in self.kind:
            raise ValueError("kind must look like 'area.action'")
        if not 1 <= self.priority <= 9:
            raise ValueError("priority 1..9")
        if any(not isinstance(x, str) for x in self.tools):
            raise ValueError("tools must be strings")


@dataclass
class Task(Record):
    id: str
    spec: TaskSpec
    status: TaskStatus
    created_at: str
    updated_at: str
    attempts: int = 0
    run_ids: list[str] = field(default_factory=list)
    approval_id: t.Optional[str] = None
    last_error: t.Optional[str] = None
    checkpoint: dict = field(default_factory=dict)  # last successful checkpoint, resumable
    next_eligible_at: t.Optional[str] = None  # backoff gate
    output_ref: t.Optional[str] = None

    def validate(self) -> None:
        self.spec.validate()


@dataclass
class ModelUsage(Record):
    provider: str
    model: str
    tokens_in: t.Optional[int] = None  # None = provider didn't report it → "unknown"
    tokens_out: t.Optional[int] = None
    cost_usd: t.Optional[float] = None  # never estimated here
    cached: bool = False
    calls: int = 1


@dataclass
class Run(Record):
    id: str
    task_id: str
    agent_id: str
    attempt: int
    started_at: str
    finished_at: t.Optional[str] = None
    status: t.Optional[TaskStatus] = None  # outcome of this attempt
    model: t.Optional[str] = None
    usage: t.Optional[ModelUsage] = None
    validation: dict = field(default_factory=dict)  # {"ok": bool, "checks": [...]}
    output_ref: t.Optional[str] = None
    error: t.Optional[str] = None  # scrubbed
    error_class: t.Optional[str] = None  # transient | rate_limited | timeout | permanent | needs_approval
    recovery: t.Optional[str] = None  # plain-English next step
    heartbeat_at: t.Optional[str] = None
    runner: t.Optional[str] = None  # e.g. "github-actions:12345" or "claude-task:trig_…"


@dataclass
class Approval(Record):
    id: str
    task_id: t.Optional[str]
    capability: Capability
    title: str
    why: str
    status: ApprovalStatus = ApprovalStatus.PROPOSED
    requested_at: str = field(default_factory=now_iso)
    decided_at: t.Optional[str] = None
    decided_by: t.Optional[str] = None
    expires_at: t.Optional[str] = None
    cost: t.Optional[str] = None
    risk: t.Optional[str] = None


@dataclass
class AuditEvent(Record):
    id: str
    at: str
    who: str  # agent id, "grayson", "engine"
    action: str
    subject: str  # task id / product id / integration id
    detail: str = ""  # scrubbed

    @classmethod
    def make(cls, who: str, action: str, subject: str, detail: str = "") -> "AuditEvent":
        return cls(id=new_id("aud"), at=now_iso(), who=who, action=action, subject=subject, detail=scrub(detail)[:500])


@dataclass
class FileRef(Record):
    path: str
    sha256: str
    bytes: int
    format: str  # pdf, png, mp4 …


@dataclass
class ProductManifest(Record):
    """Versioned. A new version is a new row; old versions are never overwritten."""
    product_id: str
    version: int
    created_at: str
    files: list[FileRef]
    format: str
    title: str
    lane: str  # planner, wallart, mugwrap, sticker, invitation, game
    validation: dict = field(default_factory=dict)
    known_limitations: list[str] = field(default_factory=list)
    listing_status: str = "draft"  # draft | review | listed | retired
    distribution_status: str = "none"  # none | planned | scheduled | published | measured
    supersedes: t.Optional[int] = None

    def validate(self) -> None:
        if self.version < 1:
            raise ValueError("version starts at 1")


@dataclass
class DistributionPlan(Record):
    id: str
    product_id: str
    product_version: int
    target_customer: str
    evidence: list[str]  # source links / doc ids with dates in the text
    channels: list[Channel]
    channel_reasons: dict  # channel → why
    assets: dict = field(default_factory=dict)  # channel → asset refs
    destination_url: t.Optional[str] = None
    cta: t.Optional[str] = None
    schedule: list[dict] = field(default_factory=list)  # [{"channel","at","tz"}]
    timezone: str = "America/Chicago"
    hypothesis: str = ""
    success_criteria: str = ""
    approval_id: t.Optional[str] = None
    status: str = "planned"  # planned | approved | scheduled | published | measured
    tracking: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)  # real numbers only; missing = absent key
    next_action: t.Optional[str] = None

    def validate(self) -> None:
        if not self.channels:
            raise ValueError("a distribution plan needs at least one channel")
        for c in self.channels:
            if c.value not in self.channel_reasons:
                raise ValueError(f"channel {c.value} has no reason")


@dataclass
class IntegrationHealth(Record):
    id: str  # "make", "zernio", "etsy", "alpaca", "youtube_api", "vidiq", "artifact_db"
    state: IntegrationState
    last_ok_at: t.Optional[str] = None
    last_error: t.Optional[str] = None
    checked_at: t.Optional[str] = None
    note: str = ""


# ------------------------------------------------------------------ exports
CONTRACTS: list[type] = [
    ErrorPolicy, Budget, AgentContract, TaskSpec, Task, ModelUsage, Run, Approval, AuditEvent,
    FileRef, ProductManifest, DistributionPlan, IntegrationHealth,
]
ENUMS: list[type] = [TaskStatus, AgentRole, Capability, Channel, ApprovalStatus, IntegrationState]


def _py_to_schema(tp: t.Any) -> dict:
    if isinstance(tp, str):
        tp = _resolve(tp)
    origin, args = t.get_origin(tp), t.get_args(tp)
    if origin is t.Union or (origin is not None and str(origin) == "<class 'types.UnionType'>"):
        inner = [a for a in args if a is not type(None)]
        s = _py_to_schema(inner[0]) if len(inner) == 1 else {"anyOf": [_py_to_schema(a) for a in inner]}
        return {"anyOf": [s, {"type": "null"}]}
    if origin is list:
        return {"type": "array", "items": _py_to_schema(args[0]) if args else {}}
    if origin is dict or tp is dict:
        return {"type": "object"}
    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        return {"$ref": f"#/$defs/{tp.__name__}"}
    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        return {"$ref": f"#/$defs/{tp.__name__}"}
    return {str: {"type": "string"}, int: {"type": "integer"}, float: {"type": "number"}, bool: {"type": "boolean"}}.get(tp, {})


def to_json_schema() -> dict:
    defs: dict = {}
    for e in ENUMS:
        defs[e.__name__] = {"type": "string", "enum": [m.value for m in e]}
    for c in CONTRACTS:
        props, req = {}, []
        for f in dataclasses.fields(c):
            props[f.name] = _py_to_schema(f.type)
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:  # type: ignore[attr-defined]
                req.append(f.name)
        defs[c.__name__] = {"type": "object", "properties": props, "required": req, "additionalProperties": False}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "GM Factory engine contracts",
            "version": SCHEMA_VERSION, "$defs": defs}


def _py_to_ts(tp: t.Any) -> str:
    if isinstance(tp, str):
        tp = _resolve(tp)
    origin, args = t.get_origin(tp), t.get_args(tp)
    if origin is t.Union or (origin is not None and str(origin) == "<class 'types.UnionType'>"):
        inner = [a for a in args if a is not type(None)]
        return " | ".join(_py_to_ts(a) for a in inner) + " | null"
    if origin is list:
        return f"{_py_to_ts(args[0]) if args else 'unknown'}[]"
    if origin is dict or tp is dict:
        return "Record<string, unknown>"
    if isinstance(tp, type) and (issubclass(tp, enum.Enum) or dataclasses.is_dataclass(tp)):
        return tp.__name__
    return {str: "string", int: "number", float: "number", bool: "boolean"}.get(tp, "unknown")


def to_typescript() -> str:
    out = ["// Generated from factory/engine/contracts.py — do not edit by hand.",
           "// Regenerate: python -m factory.engine export-ts", f"export const SCHEMA_VERSION = {SCHEMA_VERSION};", ""]
    for e in ENUMS:
        out.append(f"export type {e.__name__} = " + " | ".join(json.dumps(m.value) for m in e) + ";")
    out.append("")
    for c in CONTRACTS:
        out.append(f"export interface {c.__name__} {{")
        for f in dataclasses.fields(c):
            optional = not (f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING)  # type: ignore[attr-defined]
            out.append(f"  {f.name}{'?' if optional else ''}: {_py_to_ts(f.type)};")
        out.append("}\n")
    return "\n".join(out)
