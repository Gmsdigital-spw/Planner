from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from zoneinfo import ZoneInfo

from .models import Proposal, Refused, Settings, Snapshot, ZERO, number


@dataclass(frozen=True)
class Plan:
    allowed: bool
    reasons: tuple[str, ...]
    side: str
    symbol: str
    amount_usd: str
    quantity: str | None
    scenario_gain_usd: str | None
    scenario_loss_usd: str | None
    maximum_position_loss_usd: str
    note: str = "Scenarios are arithmetic, not forecasts. Entry halts and scenario budgets do not guarantee a loss limit."


def assess(settings: Settings, p: Proposal, s: Snapshot, store, day: str, settled_cash_usd=None) -> Plan:
    settings.validate()
    p.validate(s.fetched_at)
    reasons = []
    age = (s.fetched_at - s.clock_at).total_seconds()
    if s.duration_seconds > settings.max_snapshot_seconds or not -2 <= age <= settings.max_snapshot_seconds:
        reasons.append("Broker snapshot or market clock is stale")
    if not s.account_active or s.account_blocked or s.trading_blocked:
        reasons.append("Broker account is restricted or inactive")
    if not s.market_open:
        reasons.append("Regular market session is closed")
    if s.next_close <= s.fetched_at:
        reasons.append("Broker session close is invalid")
    if any(number(v) < 0 for v in (s.equity, s.cash, s.buying_power)):
        reasons.append("Negative balance or borrowed funds detected")
    if s.open_orders:
        reasons.append("Open broker orders must finish or be canceled and reconciled first")
    if store.unresolved():
        reasons.append("An earlier order outcome is unresolved")
    positions = [pos for pos in s.positions if pos.symbol == p.symbol]

    if p.side == "sell":
        # Entry halts, spread gates, floor gates and strategy gates do not block exits.
        if len(positions) != 1 or positions[0].qty <= 0:
            reasons.append("No single long position available to close")
        pos = positions[0] if len(positions) == 1 else None
        amount = abs(pos.market_value) if pos else ZERO
        return Plan(not reasons, tuple(reasons), "sell", p.symbol, str(amount),
                    str(pos.qty) if pos and pos.qty > 0 else None, None, None, str(amount))

    amount = number(p.notional_usd)
    entry_count, spent_today = store.day_entries(day)
    floor = settings.protected_equity_floor_usd
    start = number(store.get("initial_equity"))
    daily_reference = number(store.get("day_reference:" + day))
    if s.equity <= floor:
        reasons.append("Protected equity floor leaves no room for a new trade")
    if daily_reference - s.equity >= settings.max_daily_loss_usd:
        store.halt("Daily equity loss threshold reached")
    if start - s.equity >= settings.max_total_loss_usd:
        store.halt("Experiment equity loss threshold reached")
    halted = store.get("halt_reason")
    if halted:
        reasons.append("New entries are halted: " + halted)
    if p.symbol not in settings.allowed_symbols:
        reasons.append("Symbol is outside the explicit allowlist")
    if not s.asset_ok:
        reasons.append("Asset must be an active, tradable, fractionable US-listed equity")
    if any(pos.qty < 0 for pos in s.positions):
        reasons.append("Short exposure is unsupported")
    if s.positions:
        reasons.append("Only one position is permitted; close and reconcile it before adding risk")
    if (s.next_close - s.fetched_at).total_seconds() < 120:
        reasons.append("Too close to the session close to open a position")
    if amount > settings.max_order_usd:
        reasons.append("Order exceeds the fixed dollar order cap")
    exposure_limit = min(settings.max_exposure_usd, settings.capital_cap_usd, max(ZERO, s.equity - floor))
    if s.exposure + amount > exposure_limit:
        reasons.append("Exposure would exceed the capital cap or protected-equity headroom")
    if amount > min(s.cash, s.buying_power):
        reasons.append("Not enough unborrowed broker funds")
    if entry_count >= settings.max_entries_per_day:
        reasons.append("Daily entry count reached")
    if settings.mode == "live":
        if not settings.live_enabled:
            reasons.append("Live execution is disabled in configuration")
        if p.strategy_version not in settings.approved_strategy_versions:
            reasons.append("Strategy version has no explicit live approval")
        if settled_cash_usd is None:
            reasons.append("Live entry requires broker-confirmed start-of-day settled cash")
        else:
            settled = number(settled_cash_usd)
            if settled < 0 or amount > settled - spent_today:
                reasons.append("Entry exceeds remaining confirmed settled funds; sale proceeds are not recycled")

    spread = None
    if s.quote_at is None or s.bid is None or s.ask is None:
        reasons.append("A current bid and ask are required")
    else:
        quote_age = (s.fetched_at - s.quote_at).total_seconds()
        if not -2 <= quote_age <= settings.max_quote_age_seconds:
            reasons.append("Quote is stale or future-dated")
        if s.bid <= 0 or s.ask <= 0 or s.ask < s.bid:
            reasons.append("Quote is zero, negative or crossed")
        else:
            spread = (s.ask - s.bid) / ((s.ask + s.bid) / 2) * Decimal("10000")
            if spread > settings.max_spread_bps:
                reasons.append("Quoted spread exceeds the limit for this data feed")

    cost_bps = settings.assumed_cost_bps_per_side * 2 + (spread or ZERO)
    costs = amount * cost_bps / Decimal("10000")
    scenario_loss = amount * number(p.adverse_move_pct) + costs
    scenario_gain = amount * number(p.target_move_pct) - costs
    if scenario_loss > settings.max_scenario_loss_usd:
        reasons.append("Adverse-move scenario exceeds the dollar scenario budget")
    if scenario_gain <= 0:
        reasons.append("Target scenario does not cover assumed costs")
    return Plan(not reasons, tuple(reasons), "buy", p.symbol, str(amount), None,
                str(scenario_gain.quantize(Decimal("0.0001"))),
                str(scenario_loss.quantize(Decimal("0.0001"))), str(amount))
