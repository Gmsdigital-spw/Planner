from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

from .models import Position, Refused, Settings, Snapshot, now_utc, number, timestamp


class BrokerError(RuntimeError):
    pass


class NotFound(BrokerError):
    pass


class BrokerRejected(BrokerError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        # Never forward API credentials to a redirect target.
        raise BrokerError("Broker redirect refused")


def required_bool(raw: dict, key: str) -> bool:
    if type(raw.get(key)) is not bool:
        raise Refused("Broker omitted a required boolean field: " + key)
    return raw[key]


class AlpacaBroker:
    """REST adapter. No automatic POST retries, no custom hosts, no credentials in logs."""

    def __init__(self, settings: Settings):
        if settings.mode not in {"paper", "live"}:
            raise Refused("Alpaca adapter requires paper or live mode")
        if not settings.expected_account_id:
            raise Refused("Pin expected_account_id before connecting a broker")
        prefix = "ALPACA_PAPER" if settings.mode == "paper" else "ALPACA_LIVE"
        key, secret = os.getenv(prefix + "_KEY_ID"), os.getenv(prefix + "_SECRET_KEY")
        if not key or not secret:
            raise Refused(f"Set {prefix}_KEY_ID and {prefix}_SECRET_KEY on the server")
        self.settings = settings
        self.base = "https://paper-api.alpaca.markets" if settings.mode == "paper" else "https://api.alpaca.markets"
        self.headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "Content-Type": "application/json"}
        self.opener = urllib.request.build_opener(NoRedirect())

    def _request(self, method: str, path: str, payload=None, *, data=False):
        base = "https://data.alpaca.markets" if data else self.base
        body = None if payload is None else json.dumps(payload, allow_nan=False).encode()
        req = urllib.request.Request(base + path, data=body, headers=self.headers, method=method)
        try:
            with self.opener.open(req, timeout=3) as response:
                raw = response.read(4_000_001)
                if len(raw) > 4_000_000:
                    raise BrokerError("Broker response exceeded size limit")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            # Deliberately do not expose raw response bodies or request headers.
            if exc.code == 404:
                raise NotFound("Broker resource not found") from None
            if method == "POST" and exc.code in {400, 401, 403, 422}:
                raise BrokerRejected(f"Broker rejected order (HTTP {exc.code}); do not bypass") from None
            raise BrokerError(f"Broker request failed (HTTP {exc.code}); reconcile state") from None
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            raise BrokerError("Broker response unavailable; order outcome may be unknown") from None

    def snapshot(self, symbol: str, need_quote: bool = True) -> Snapshot:
        started = time.monotonic()
        account = self._request("GET", "/v2/account")
        if account.get("id") != self.settings.expected_account_id:
            raise Refused("Broker account does not match expected_account_id")
        positions = self._request("GET", "/v2/positions")
        orders = self._request("GET", "/v2/orders?status=open&limit=500&nested=false")
        # A full page cannot establish that we saw every order.
        if not isinstance(positions, list) or not isinstance(orders, list) or len(orders) >= 500:
            raise Refused("Incomplete broker position/order inventory")
        asset = self._request("GET", "/v2/assets/" + urllib.parse.quote(symbol, safe=""))
        quote = None
        if need_quote:
            quote = self._request("GET", "/v2/stocks/" + urllib.parse.quote(symbol, safe="") + "/quotes/latest?feed=" + self.settings.data_feed, data=True)["quote"]
        clock = self._request("GET", "/v2/clock")
        return Snapshot(
            account_id=account["id"], equity=number(account["equity"]),
            cash=number(account["cash"]),
            buying_power=min(number(account["buying_power"]), number(account["non_marginable_buying_power"])),
            last_equity=number(account["last_equity"]),
            account_active=account.get("status") == "ACTIVE",
            account_blocked=required_bool(account, "account_blocked"),
            trading_blocked=(required_bool(account, "trading_blocked") or required_bool(account, "trade_suspended_by_user")),
            positions=tuple(Position(p["symbol"], number(p["qty"]), number(p["market_value"])) for p in positions),
            open_orders=tuple(orders), market_open=required_bool(clock, "is_open"),
            next_close=timestamp(clock["next_close"]), clock_at=timestamp(clock["timestamp"]),
            quote_at=timestamp(quote["t"]) if quote else None,
            bid=number(quote["bp"]) if quote else None,
            ask=number(quote["ap"]) if quote else None,
            asset_ok=(asset.get("class") == "us_equity" and asset.get("status") == "active" and asset.get("tradable") is True and asset.get("fractionable") is True and asset.get("exchange") != "OTC"),
            fetched_at=now_utc(), duration_seconds=time.monotonic() - started,
        )

    def lookup(self, client_id: str):
        return self._request("GET", "/v2/orders:by_client_order_id?" + urllib.parse.urlencode({"client_order_id": client_id}))

    def submit(self, payload: dict):
        # Exactly one POST. Any ambiguous outcome must be reconciled by client ID.
        return self._request("POST", "/v2/orders", payload)


class DemoBroker:
    """In-memory synthetic execution for examples and tests. Not market evidence."""

    def __init__(self, equity="50"):
        self.equity = number(equity)
        self.cash = self.equity
        self.positions = ()
        self.orders = {}
        self.post_count = 0
        self.open_orders = ()
        self.last_equity = self.equity

    def snapshot(self, symbol, need_quote=True):
        at = now_utc()
        return Snapshot(
            account_id="SYNTHETIC-DEMO", equity=self.equity, cash=self.cash,
            buying_power=self.cash, last_equity=self.last_equity, account_active=True,
            account_blocked=False, trading_blocked=False, positions=self.positions,
            open_orders=self.open_orders, market_open=True,
            next_close=at + timedelta(hours=6), clock_at=at,
            quote_at=at if need_quote else None,
            bid=number("99.99") if need_quote else None,
            ask=number("100.01") if need_quote else None,
            asset_ok=True, fetched_at=at,
        )

    def lookup(self, client_id):
        if client_id not in self.orders:
            raise NotFound("No such synthetic order")
        return self.orders[client_id]

    def submit(self, payload):
        self.post_count += 1
        client_id, symbol = payload["client_order_id"], payload["symbol"]
        if client_id in self.orders:
            raise BrokerRejected("Duplicate synthetic client ID")
        if payload["side"] == "buy":
            qty = number(payload["notional"]) / number("100.01")
            self.cash -= number(payload["notional"])
            self.positions = (Position(symbol, qty, qty * number("100")),)
            price = "100.01"
        else:
            qty = number(payload["qty"])
            self.cash += qty * number("99.99")
            self.positions = ()
            price = "99.99"
        self.equity = self.cash + sum((p.market_value for p in self.positions), number("0"))
        order = {**payload, "id": "demo-" + client_id, "status": "filled", "filled_qty": str(qty), "filled_avg_price": price, "filled_at": now_utc().isoformat()}
        self.orders[client_id] = order
        return order
