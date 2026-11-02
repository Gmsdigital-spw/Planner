from __future__ import annotations

import hashlib
from dataclasses import asdict

from .broker import BrokerError, BrokerRejected, NotFound
from .models import Proposal, Refused, Settings, now_utc, number
from .risk import assess

LIVE_ACK = "I_ACCEPT_MARKET_RISK"


class Engine:
    def __init__(self, settings: Settings, store, broker):
        self.settings, self.store, self.broker = settings, store, broker
        identity = store.get("identity")
        if identity and (identity["mode"] != settings.mode or (settings.mode != "demo" and identity["account_id"] != settings.expected_account_id)):
            raise Refused("Stored environment/account differs from configuration; use its original configuration")

    def _check_broker_order(self, raw, client_id):
        if not isinstance(raw, dict) or raw.get("client_order_id") != client_id or not isinstance(raw.get("status"), str) or not raw.get("id") or "filled_qty" not in raw:
            raise BrokerError("Broker returned an incomplete or mismatched order")
        # Fills, including partial fills on canceled orders, stay in the audit record.
        if "filled_qty" in raw:
            if number(raw["filled_qty"]) < 0:
                raise BrokerError("Invalid broker fill quantity")
        if raw["status"] == "filled" and number(raw["filled_qty"]) <= 0:
            raise BrokerError("Filled order has no filled quantity")
        return raw

    def _reconcile(self):
        outcomes = []
        for row in self.store.unresolved():
            client_id = row["client_order_id"]
            try:
                order = self._check_broker_order(self.broker.lookup(client_id), client_id)
                self.store.update_order(client_id, order["status"], order)
                outcomes.append({"client_order_id": client_id, "status": order["status"]})
            except NotFound:
                # An empty lookup after a timeout is not proof that POST never arrived.
                self.store.update_order(client_id, "unknown")
                outcomes.append({"client_order_id": client_id, "status": "unknown"})
            except BrokerError:
                outcomes.append({"client_order_id": client_id, "status": "unavailable"})
        return outcomes

    def reconcile(self):
        with self.store.locked():
            return self._reconcile()

    def _snapshot_plan(self, p, settled_cash_usd):
        snapshot = self.broker.snapshot(p.symbol, need_quote=p.side == "buy")
        if self.settings.mode != "demo" and snapshot.account_id != self.settings.expected_account_id:
            raise Refused("Account identity mismatch")
        day = self.store.capture(snapshot, self.settings)
        plan = assess(self.settings, p, snapshot, self.store, day, settled_cash_usd)
        return snapshot, plan, day

    def preview(self, p: Proposal, settled_cash_usd=None):
        with self.store.locked():
            self._reconcile()
            _, plan, _ = self._snapshot_plan(p, settled_cash_usd)
            self.store.event("preview", {"proposal_id": p.proposal_id, "plan": asdict(plan)})
            return asdict(plan)

    def execute(self, p: Proposal, *, live_ack=None, settled_cash_usd=None):
        if self.settings.mode == "live" and (not self.settings.live_enabled or live_ack != LIVE_ACK):
            raise Refused("Live submission requires live_enabled and the explicit CLI acknowledgment")
        with self.store.locked():
            existing = self.store.order(p.proposal_id)
            if existing:
                if existing["fingerprint"] != p.fingerprint:
                    raise Refused("An existing proposal_id cannot be reused with changed intent")
                self._reconcile()
                current = self.store.order(p.proposal_id)
                return {"duplicate_prevented": True, "client_order_id": current["client_order_id"], "status": current["status"]}
            self._reconcile()
            snapshot, plan, day = self._snapshot_plan(p, settled_cash_usd)
            if not plan.allowed:
                self.store.event("refused", {"proposal_id": p.proposal_id, "reasons": plan.reasons})
                raise Refused("; ".join(plan.reasons))
            digest = hashlib.sha256((self.settings.mode + "|" + snapshot.account_id + "|" + p.proposal_id).encode()).hexdigest()[:36]
            client_id = "atlas-" + digest
            payload = {"client_order_id": client_id, "symbol": p.symbol, "side": p.side,
                       "type": "market", "time_in_force": "day", "extended_hours": False,
                       "order_class": "simple"}
            if p.side == "buy":
                payload["notional"] = p.notional_usd
            else:
                payload["qty"] = plan.quantity
            # Persist first. A crash or transport timeout can never cause blind POST retry.
            self.store.reserve(p, payload, day)
            try:
                existing_remote = self.broker.lookup(client_id)
            except NotFound:
                existing_remote = None
            except BrokerError:
                self.store.update_order(client_id, "unknown")
                raise Refused("Preflight lookup failed; no order was submitted; reconcile before continuing") from None
            if existing_remote is None:
                try:
                    # No stale preview authorizes an order: check expiry again immediately.
                    at_submit = now_utc()
                    p.validate(at_submit)
                    if (at_submit - snapshot.fetched_at).total_seconds() > self.settings.max_snapshot_seconds:
                        raise Refused("Snapshot aged during preflight")
                    if p.side == "buy" and (at_submit - snapshot.quote_at).total_seconds() > self.settings.max_quote_age_seconds:
                        raise Refused("Quote aged during preflight")
                except Refused as exc:
                    # We know POST has not been called. Do not invent an unknown fill.
                    self.store.update_order(client_id, "not_submitted")
                    self.store.event("not_submitted", {"client_order_id": client_id, "reason": str(exc)})
                    raise Refused("No order submitted: " + str(exc)) from None
            try:
                if existing_remote is None:
                    order = self.broker.submit(payload)
                else:
                    order = existing_remote
                order = self._check_broker_order(order, client_id)
                self.store.update_order(client_id, order["status"], order)
                self.store.event("order_result", {"client_order_id": client_id, "status": order["status"]})
                return {"client_order_id": client_id, "status": order["status"], "broker_order": order}
            except BrokerRejected as exc:
                self.store.update_order(client_id, "rejected")
                self.store.event("broker_rejected", {"client_order_id": client_id})
                raise Refused(str(exc)) from None
            except (BrokerError, Refused):
                self.store.update_order(client_id, "unknown")
                self.store.event("unknown_order_outcome", {"client_order_id": client_id})
                raise Refused("Order outcome is unknown; do not resubmit; run reconcile and inspect the broker") from None
