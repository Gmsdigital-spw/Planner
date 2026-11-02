"""Offline checks of the gateway's Alpaca money rules (gw/run.py op_alpaca) in paper and live mode with a fake
`requests`: no network, no keys of Grayson's, no orders. Run: python3 factory/trading/tests/test_gateway_rules.py

Covers: live mode needs its own key pair (never the paper pair); live buys only from the autopilot's own process
(ALPACA_LIVE_BUYS); the pinned-account check on every order (the pin may be the dashboard account number or the API
id); the blocked-account check on buys; a broken live profile refuses buys; the floor, size cap and hours from the
profile for each mode; the repo-variable overrides (ALPACA_FLOOR paper only, ALPACA_LIVE_FLOOR / ALPACA_LIVE_ACCOUNT_ID
live only; a non-numeric floor is ignored, never fatal); GET /account in live mode answers with the hint view."""
import datetime as _dt
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GW = REPO / "gw" / "run.py"


class Resp:
    def __init__(self, code, body):
        self.status_code, self._body, self.text = code, body, json.dumps(body)

    def json(self):
        return self._body


class FakeRequests:
    """Routes the few Alpaca calls op_alpaca makes."""
    def __init__(self, acct, positions=None):
        self.acct, self.positions, self.log = acct, positions or [], []

    def get(self, url, headers=None, timeout=None, **kw):
        self.log.append(("GET", url))
        if url.endswith("/account"):
            return Resp(200, self.acct)
        if url.endswith("/positions"):
            return Resp(200, self.positions)
        if "/orders/" in url:
            return Resp(200, {"id": url.rsplit("/", 1)[1], "status": "filled", "filled_qty": "0.4", "filled_avg_price": "60.5"})
        return Resp(200, {})

    def post(self, url, headers=None, json=None, timeout=None, **kw):
        self.log.append(("POST", url, json))
        if json.get("type") == "stop":
            return Resp(200, {"id": "stop-1", "status": "accepted"})
        return Resp(200, {"id": "buy-1", "status": "accepted", "client_order_id": json.get("client_order_id")})

    def delete(self, url, headers=None, timeout=None, **kw):
        self.log.append(("DELETE", url))
        return Resp(204, {})

    def request(self, method, url, headers=None, json=None, timeout=None, **kw):
        self.log.append((method, url, json))
        return Resp(200, {"ok": True})


class FixedDT(_dt.datetime):
    """10:00 AM Central (16:00Z, CST) on Tuesday Nov 3, 2026, whatever the real clock says: the hours rule is tested, not the wall clock."""
    @classmethod
    def now(cls, tz=None):
        base = _dt.datetime(2026, 11, 3, 16, 0, tzinfo=_dt.timezone.utc)
        return base.astimezone(tz) if tz else base.replace(tzinfo=None)


def load_gw(env):
    for k in ("ALPACA_LIVE", "ALPACA_KEY_ID", "ALPACA_SECRET_KEY", "ALPACA_LIVE_KEY_ID", "ALPACA_LIVE_SECRET_KEY",
              "ALPACA_FLOOR", "ALPACA_LIVE_FLOOR", "ALPACA_LIVE_ACCOUNT_ID", "ALPACA_BANKROLL", "STARSHIP_KEY", "ALPACA_LIVE_BUYS"):
        os.environ.pop(k, None)
    os.environ.update(env)
    spec = importlib.util.spec_from_file_location("gw_run_test", GW)
    gw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gw)
    return gw


def buy(gw, notional, sym="TQQQ"):
    return gw.op_alpaca({"op": "alpaca", "method": "POST", "path": "/orders", "body": {
        "symbol": sym, "notional": f"{notional:.2f}", "side": "buy", "type": "market", "time_in_force": "day",
        "client_order_id": "gm-test-1", "protect": {"stop_price": "59.44", "take_profit": "63.88"}}}, {})


def main():
    fails = []

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond:
            fails.append(msg)

    LIVE_ACCT = {"id": "acct-live-0001", "equity": "25.00", "cash": "25.00", "buying_power": "25.00",
                 "non_marginable_buying_power": "25.00", "status": "ACTIVE", "trading_blocked": False,
                 "account_blocked": False, "trade_suspended_by_user": False, "multiplier": "1"}
    PAPER = {"ALPACA_KEY_ID": "paper-key", "ALPACA_SECRET_KEY": "paper-secret"}
    LIVE_NOBUY = {"ALPACA_LIVE": "1", "ALPACA_KEY_ID": "paper-key", "ALPACA_SECRET_KEY": "paper-secret",
                  "ALPACA_LIVE_KEY_ID": "live-key", "ALPACA_LIVE_SECRET_KEY": "live-secret"}
    LIVE = {**LIVE_NOBUY, "ALPACA_LIVE_BUYS": "1"}   # what the Trading autopilot workflow sets
    # 10:00 CT on a Tuesday for the hours rule, whatever the real clock says
    _dt.datetime = FixedDT
    try:
        print("== live mode without its own key pair")
        gw = load_gw({"ALPACA_LIVE": "1", "ALPACA_KEY_ID": "paper-key", "ALPACA_SECRET_KEY": "paper-secret"})
        check(gw.ALPACA_LIVE and gw.AKEY == "" and gw.ASEC == "", "the paper pair is NOT picked up in live mode")
        check(gw.ALPACA.startswith("https://api.alpaca.markets"), f"live endpoint: {gw.ALPACA}")
        try:
            buy(gw, 24.98)
            check(False, "op_alpaca should refuse to run without live keys")
        except RuntimeError as e:
            check("ALPACA_LIVE_KEY_ID" in str(e) and "never falls back" in str(e), f"refused: {e}")

        print("== live mode: a crew gateway job (no ALPACA_LIVE_BUYS) may read, cancel and flatten but never buy")
        gw = load_gw(LIVE_NOBUY)
        gw.requests = FakeRequests(dict(LIVE_ACCT))
        code, body = buy(gw, 10)
        check(code == 423 and body.get("refused") == "buyer" and not [x for x in gw.requests.log if x[0] == "POST"], f"buy refused, nothing posted: {code} {body.get('refused')}")
        code, body = gw.op_alpaca({"op": "alpaca", "method": "DELETE", "path": "/positions?cancel_orders=true"}, {})
        check(code < 300 and gw.requests.log[-1][0] == "DELETE", f"flatten still allowed ({code})")
        code, body = gw.op_alpaca({"op": "alpaca", "path": "/account"}, {})
        check(code == 200 and body.get("mode") == "live" and "id" not in body and "account_number" not in body and body.get("accountId") == "…0001", f"live GET /account = the hint view, never the full record: {body}")
        check(gw.scrub({"account_number": "PA3URSYHA", "id": "x", "nested": {"account_number": "y"}}) == {"account_number": "[hidden]", "id": "x", "nested": {"account_number": "[hidden]"}}, "scrub hides account_number everywhere")

        print("== live mode: keys, profile, pinned account, blocked account")
        gw = load_gw(LIVE)
        check(gw.AKEY == "live-key" and gw.PROFILE == "live-aggressive", f"live keys in use, profile {gw.PROFILE}")
        rules = gw.money_rules()
        check(rules["floor"] == 5.0 and rules["max_pos_pct"] == 100.0 and rules["start_ct"] == "08:35" and rules["flat_ct"] == "14:45", f"live rules from the profile: {rules}")
        gw.requests = FakeRequests(dict(LIVE_ACCT))
        code, body = buy(gw, 24.98)
        posts = [x for x in gw.requests.log if x[0] == "POST"]
        check(code == 200 and posts and posts[0][2]["notional"] == "24.98" and posts[0][2]["client_order_id"] == "gm-test-1", f"all-in buy accepted at 100% cap: {code} {posts and posts[0][2]}")
        check(any(x[2].get("type") == "stop" and x[2]["qty"] == "0.4" for x in posts), "protective stop placed for the filled qty")
        gw.requests = FakeRequests(dict(LIVE_ACCT))
        code, body = buy(gw, 25.50)
        check(code == 422 and body.get("refused") == "size" and "100%" in body["message"], f"over 100% of cash refused: {code} {body}")

        gw = load_gw({**LIVE, "ALPACA_LIVE_ACCOUNT_ID": "acct-live-0001"})
        gw.requests = FakeRequests(dict(LIVE_ACCT))
        code, body = buy(gw, 10)
        check(code == 200, f"pinned account matches: buy goes through ({code})")
        gw.requests = FakeRequests({**LIVE_ACCT, "id": "acct-other-9999"})
        code, body = buy(gw, 10)
        check(code == 423 and body.get("refused") == "account" and body.get("account") == "…9999", f"other account refused, hint only: {code} {body}")
        check(not [x for x in gw.requests.log if x[0] == "POST"], "no POST reached Alpaca")
        code, body = gw.op_alpaca({"op": "alpaca", "method": "DELETE", "path": "/positions"}, {})
        check(code == 423 and body.get("refused") == "account", f"flatten on the wrong account refused too: {code}")
        both = {**LIVE_ACCT, "id": "6dbbc996-5e5f-4328-b003-92c43773422a", "account_number": "PA3URSYHA"}
        gw = load_gw({**LIVE, "ALPACA_LIVE_ACCOUNT_ID": "pa3ursyha "})
        gw.requests = FakeRequests(dict(both))
        code, body = buy(gw, 10)
        check(code == 200, f"the pin may be the dashboard account number (any case, stray space): buy goes through ({code})")
        _, view = gw.op_alpaca({"op": "alpaca", "path": "/bankroll"}, {})
        check(view["accountId"] == "…SYHA", f"the hint is the account number's last 4 (what the dashboard shows): {view['accountId']}")
        gw = load_gw({**LIVE, "ALPACA_LIVE_ACCOUNT_ID": "6dbbc996-5e5f-4328-b003-92c43773422a"})
        gw.requests = FakeRequests(dict(both))
        check(buy(gw, 10)[0] == 200, "the pin may be the API id too")
        gw.requests = FakeRequests({**both, "account_number": "PA9OTHER1", "id": "other-uuid"})
        code, body = buy(gw, 10)
        check(code == 423 and body.get("account") == "…HER1", f"neither matches: refused with the number's hint ({body.get('account')})")
        gw = load_gw(LIVE)
        gw.requests = FakeRequests({**LIVE_ACCT, "trading_blocked": True})
        code, body = buy(gw, 10)
        check(code == 423 and body.get("refused") == "blocked", f"blocked account: no buy ({code} {body.get('refused')})")
        code, body = gw.op_alpaca({"op": "alpaca", "method": "DELETE", "path": "/positions"}, {})
        check(code < 300 and gw.requests.log[-1][0] == "DELETE", f"a blocked account can still be flattened (risk-reducing): {code}")

        print("== live mode: the $5 floor, and the ALPACA_LIVE_FLOOR override")
        gw = load_gw(LIVE)
        gw.requests = FakeRequests({**LIVE_ACCT, "equity": "4.50", "cash": "4.50"})
        code, body = buy(gw, 4.0)
        check(code == 423 and body.get("refused") == "floor" and body["floor"] == 5.0, f"equity $4.50 vs $5 floor: {code} {body.get('refused')} floor {body.get('floor')}")
        gw = load_gw({**LIVE, "ALPACA_LIVE_FLOOR": "8", "ALPACA_FLOOR": "20"})
        check(gw.money_rules()["floor"] == 8.0, "ALPACA_LIVE_FLOOR=8 wins in live mode; ALPACA_FLOOR (paper) is ignored")
        gw.requests = FakeRequests({**LIVE_ACCT, "equity": "7.00", "cash": "7.00"})
        code, body = buy(gw, 6.0)
        check(code == 423 and body["floor"] == 8.0, f"$7 equity under the $8 live floor: refused ({code})")
        _, view = gw.op_alpaca({"op": "alpaca", "path": "/bankroll"}, {})
        check(view["mode"] == "live" and view["profile"] == "live-aggressive" and view["accountId"] == "…0001" and view["equity"] == 7.0, f"/bankroll live view: {view}")

        gw = load_gw({**LIVE, "ALPACA_LIVE_FLOOR": "$5"})
        rules = gw.money_rules()
        check(rules["floor"] == 5.0 and "not a number" in rules["floorWarning"], f"ALPACA_LIVE_FLOOR='$5' ignored with a warning, profile floor kept: {rules['floor']}")
        gw.requests = FakeRequests(dict(LIVE_ACCT))
        code, body = gw.op_alpaca({"op": "alpaca", "method": "DELETE", "path": "/orders/stop-1"}, {})
        check(code < 300, f"a bad floor variable never blocks a cancel or a sell ({code})")

        print("== live mode: a broken live profile refuses every buy, allows the flatten")
        gw = load_gw(LIVE)
        bad_root = Path(__file__).parent / "out" / "gw-broken" / "gw"
        (bad_root.parent / "factory" / "trading" / "profiles").mkdir(parents=True, exist_ok=True)
        (bad_root.parent / "factory" / "trading" / "profiles" / "live-aggressive.json").write_text('{"params": {"floor": 5.0,}}')
        gw.ROOT = bad_root
        rules = gw.money_rules()
        check(rules.get("broken", "").startswith("live profile"), f"rules marked broken: {rules.get('broken', '')[:70]}")
        gw.requests = FakeRequests(dict(LIVE_ACCT))
        code, body = buy(gw, 10)
        check(code == 423 and body.get("refused") == "profile" and not [x for x in gw.requests.log if x[0] == "POST"], f"buy refused ({code} {body.get('refused')})")
        code, body = gw.op_alpaca({"op": "alpaca", "method": "DELETE", "path": "/positions?cancel_orders=true"}, {})
        check(code < 300, f"flatten allowed ({code})")
        gw = load_gw(PAPER)
        gw.ROOT = bad_root
        check(gw.money_rules()["floor"] == 20.0 and not gw.money_rules().get("broken"), "paper with a missing profile file = the paper defaults, not broken")
        print("== paper mode: unchanged rules (40% cap, $20 floor, paper keys), ALPACA_FLOOR override")
        gw = load_gw({**PAPER, "ALPACA_LIVE_KEY_ID": "live-key", "ALPACA_LIVE_SECRET_KEY": "live-secret", "ALPACA_LIVE_FLOOR": "8"})
        check(not gw.ALPACA_LIVE and gw.AKEY == "paper-key" and gw.PROFILE == "paper", "paper keys and paper profile when ALPACA_LIVE is unset")
        check(gw.ALPACA.startswith("https://paper-api"), f"paper endpoint: {gw.ALPACA}")
        rules = gw.money_rules()
        check(rules["floor"] == 20.0 and rules["max_pos_pct"] == 40.0, f"paper rules: {rules}")
        check(gw.money_rules()["floor"] == 20.0, "ALPACA_LIVE_FLOOR does not touch paper")
        paper_acct = {**LIVE_ACCT, "id": "paper-acct", "equity": "100000", "cash": "100000"}
        gw.requests = FakeRequests(paper_acct)
        code, body = buy(gw, 15.0)
        check(code == 422 and body.get("refused") == "size" and "40%" in body["message"], f"$15 of $25 virtual cash refused at 40%: {code} {body}")
        gw.requests = FakeRequests(paper_acct)
        code, body = buy(gw, 9.0)
        check(code == 200, f"$9 of $25 passes the 40% cap ({code})")
        gw = load_gw({**PAPER, "ALPACA_FLOOR": "22"})
        check(gw.money_rules()["floor"] == 22.0, "ALPACA_FLOOR=22 overrides the paper floor")
        gw.requests = FakeRequests(paper_acct)
        code, body = buy(gw, 5.0)
        check(code == 200, f"virtual equity $25 is above the $22 override floor: buy allowed ({code})")
        gw = load_gw({**PAPER, "ALPACA_FLOOR": "22", "ALPACA_BANKROLL": "21"})
        gw.requests = FakeRequests(paper_acct)
        code, body = buy(gw, 5.0)
        check(code == 423 and body.get("refused") == "floor" and body["floor"] == 22.0, f"virtual equity $21 at/below the $22 override floor: refused ({code} {body.get('refused')})")

        print("== hours: outside the profile window, no buy")
        class LateDT(FixedDT):
            @classmethod
            def now(cls, tz=None):
                base = _dt.datetime(2026, 11, 3, 21, 0, tzinfo=_dt.timezone.utc)   # 3:00 PM CT
                return base.astimezone(tz) if tz else base.replace(tzinfo=None)
        _dt.datetime = LateDT
        gw = load_gw(LIVE)
        gw.requests = FakeRequests(dict(LIVE_ACCT))
        code, body = buy(gw, 10)
        check(code == 422 and body.get("refused") == "hours" and "08:35 to 14:45" in body["message"], f"3:00 PM CT buy refused: {code} {body.get('message')}")
    finally:
        _dt.datetime = FixedDT.__mro__[1]
        for k in ("ALPACA_LIVE", "ALPACA_KEY_ID", "ALPACA_SECRET_KEY", "ALPACA_LIVE_KEY_ID", "ALPACA_LIVE_SECRET_KEY", "ALPACA_FLOOR", "ALPACA_LIVE_FLOOR", "ALPACA_LIVE_ACCOUNT_ID", "ALPACA_LIVE_BUYS"):
            os.environ.pop(k, None)

    print()
    print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
