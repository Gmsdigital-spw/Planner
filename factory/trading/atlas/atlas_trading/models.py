from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ZERO = Decimal("0")
CENT = Decimal("0.01")


class Refused(ValueError):
    """An input or trading condition does not satisfy policy."""


def number(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise Refused("Missing or invalid numeric value")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise Refused("Invalid numeric value") from None
    if not result.is_finite():
        raise Refused("Non-finite numbers are forbidden")
    return result


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        raise Refused("Expected an ISO-8601 timestamp with a timezone") from None
    if dt.tzinfo is None:
        raise Refused("A timestamp needs a timezone")
    return dt.astimezone(timezone.utc)


def encoded(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True, allow_nan=False)


@dataclass(frozen=True)
class Settings:
    mode: str = "demo"
    database: str = "data/atlas-demo.sqlite3"
    capital_cap_usd: Decimal = Decimal("20")
    protected_equity_floor_usd: Decimal = Decimal("20")
    max_order_usd: Decimal = Decimal("2")
    max_exposure_usd: Decimal = Decimal("5")
    max_scenario_loss_usd: Decimal = Decimal("0.20")
    max_daily_loss_usd: Decimal = Decimal("1")
    max_total_loss_usd: Decimal = Decimal("3")
    max_entries_per_day: int = 1
    max_spread_bps: Decimal = Decimal("25")
    assumed_cost_bps_per_side: Decimal = Decimal("10")
    max_quote_age_seconds: int = 5
    max_snapshot_seconds: int = 10
    live_enabled: bool = False
    expected_account_id: str = ""
    approved_strategy_versions: tuple[str, ...] = ()
    allowed_symbols: tuple[str, ...] = ("SPY", "QQQ")
    data_feed: str = "iex"

    def validate(self) -> None:
        if self.mode not in {"demo", "paper", "live"}:
            raise Refused("mode must be demo, paper, or live")
        for name, value in asdict(self).items():
            if isinstance(value, Decimal) and (not value.is_finite() or value < 0):
                raise Refused(f"Invalid policy field: {name}")
        if not ZERO < self.capital_cap_usd <= Decimal("50"):
            raise Refused("This experiment has an absolute $50 capital ceiling")
        if not Decimal("1") <= self.max_order_usd <= self.capital_cap_usd:
            raise Refused("max_order_usd must be between $1 and the capital cap")
        if not self.max_order_usd <= self.max_exposure_usd <= self.capital_cap_usd:
            raise Refused("Exposure must cover an order and stay within the capital cap")
        if not ZERO < self.max_daily_loss_usd <= self.max_total_loss_usd <= self.capital_cap_usd:
            raise Refused("Daily and total entry-halt thresholds must be positive and bounded")
        if self.max_scenario_loss_usd <= 0:
            raise Refused("Scenario risk budget must be positive")
        for name in ("max_entries_per_day", "max_quote_age_seconds", "max_snapshot_seconds"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 120:
                raise Refused(f"Invalid policy field: {name}")
        if type(self.live_enabled) is not bool:
            raise Refused("live_enabled must be a JSON boolean")
        if self.data_feed not in {"iex", "sip"}:
            raise Refused("Only explicit IEX or SIP feeds are supported")
        if not self.allowed_symbols or not all(re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", s) for s in self.allowed_symbols):
            raise Refused("Invalid symbol allowlist")

    @classmethod
    def load(cls, path: str | Path) -> "Settings":
        raw = json.loads(Path(path).read_text())
        fields = cls.__dataclass_fields__
        unknown = set(raw) - set(fields)
        if unknown:
            raise Refused("Unknown configuration fields: " + ", ".join(sorted(unknown)))
        for name, default in asdict(cls()).items():
            if name in raw and isinstance(default, Decimal):
                raw[name] = number(raw[name])
        for name in ("approved_strategy_versions", "allowed_symbols"):
            if name in raw:
                if not isinstance(raw[name], list) or not all(isinstance(v, str) for v in raw[name]):
                    raise Refused(f"{name} must be a list of strings")
                raw[name] = tuple(raw[name])
        result = cls(**raw)
        result.validate()
        return result


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    symbol: str
    side: str
    strategy_version: str
    created_at: str
    expires_at: str
    notional_usd: str = "0"
    adverse_move_pct: str = "0.05"
    target_move_pct: str = "0.10"
    rationale: str = ""
    evidence_ref: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "Proposal":
        try:
            return cls(**json.loads(Path(path).read_text()))
        except (TypeError, json.JSONDecodeError):
            raise Refused("Proposal JSON does not match the documented schema") from None

    def validate(self, at: datetime) -> None:
        if not isinstance(self.proposal_id, str) or not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", self.proposal_id):
            raise Refused("Invalid proposal_id")
        if self.side not in {"buy", "sell"}:
            raise Refused("Only buy or sell is supported")
        if not isinstance(self.symbol, str) or not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", self.symbol):
            raise Refused("Invalid equity symbol")
        if not isinstance(self.strategy_version, str) or not self.strategy_version.strip():
            raise Refused("A fixed strategy version is required")
        created, expires = timestamp(self.created_at), timestamp(self.expires_at)
        if not 0 < (expires - created).total_seconds() <= 120:
            raise Refused("A proposal must expire within 120 seconds")
        if created > at or at > expires:
            raise Refused("Proposal is future-dated or expired")
        if self.side == "buy":
            amount = number(self.notional_usd)
            if amount < 1 or amount.quantize(CENT) != amount:
                raise Refused("Buy notional must be at least $1, to whole cents")
            if not ZERO < number(self.adverse_move_pct) <= Decimal("0.50"):
                raise Refused("adverse_move_pct must be between 0 and 0.50")
            if not ZERO < number(self.target_move_pct) <= Decimal("1"):
                raise Refused("target_move_pct must be between 0 and 1")
            if not self.rationale.strip() or not self.evidence_ref.strip():
                raise Refused("A buy needs a rationale and evidence reference")

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(encoded(asdict(self)).encode()).hexdigest()


@dataclass(frozen=True)
class Position:
    symbol: str
    qty: Decimal
    market_value: Decimal


@dataclass(frozen=True)
class Snapshot:
    account_id: str
    equity: Decimal
    cash: Decimal
    buying_power: Decimal
    last_equity: Decimal
    account_active: bool
    account_blocked: bool
    trading_blocked: bool
    positions: tuple[Position, ...]
    open_orders: tuple[dict, ...]
    market_open: bool
    next_close: datetime
    clock_at: datetime
    quote_at: datetime | None
    bid: Decimal | None
    ask: Decimal | None
    asset_ok: bool
    fetched_at: datetime
    duration_seconds: float = 0.0

    @property
    def exposure(self) -> Decimal:
        return sum((abs(p.market_value) for p in self.positions), ZERO)
