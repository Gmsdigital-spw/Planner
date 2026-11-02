"""Offline harness for the autopilot's LIVE profile (Nov 2, 2026) with a fake Alpaca: no network, no keys, no orders.
Writes only under tests/out/. Run: python3 factory/trading/tests/test_live_mode.py

Scenarios (ALPACA_LIVE on, profile live-aggressive): an all-in ORB entry with a client_order_id and a read-before-POST
lookup; the duplicate guard; the $5 floor; the $5 daily loss; a non-fractionable name dropped; the crew's avoid list;
one position at a time; and paper mode unchanged (ALPACA_LIVE off = the Oct 21 rules and the crew's watchlist)."""
import json, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TRADING = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TRADING))
import autopilot as ap  # noqa: E402
import backtest  # noqa: E402

CT = ZoneInfo("America/Chicago")
DAY = "2026-11-03"   # a Tuesday in CST: 8:30 CT = 14:30Z


def bars_orb():
    """Opening range 8:30-8:40 CT (high 60.00, low 59.00), then a breakout bar at 9:15 CT closing 60.50 on big volume."""
    out = []
    rows = [(14, 30, 59.2, 60.0, 59.0, 59.8, 1000), (14, 35, 59.8, 59.95, 59.3, 59.5, 900), (14, 40, 59.5, 59.9, 59.2, 59.7, 950),
            (14, 45, 59.7, 59.9, 59.4, 59.6, 800), (14, 50, 59.6, 59.95, 59.5, 59.9, 850), (14, 55, 59.9, 60.0, 59.6, 59.8, 800),
            (15, 0, 59.8, 59.95, 59.5, 59.7, 700), (15, 5, 59.7, 59.9, 59.6, 59.85, 750), (15, 10, 59.85, 60.0, 59.7, 59.95, 900),
            (15, 15, 60.0, 60.6, 59.95, 60.5, 4000)]
    for h, mi, o, hi, lo, c, v in rows:
        out.append({"t": f"{DAY}T{h:02d}:{mi:02d}:00Z", "o": o, "h": hi, "l": lo, "c": c, "v": v})
    return out


class Fake:
    """Minimal live Alpaca seen through the gateway: a $25 account, no positions unless the scenario says so."""
    def __init__(self, scenario):
        self.scenario = scenario
        self.calls = []
        self.equity = {"floor": 4.9, "daily_loss": 19.9}.get(scenario, 25.0)
        self.cash = self.equity

    def __call__(self, o, st):
        m, path = o.get("method", "GET").upper(), o["path"]
        self.calls.append((m, path, o.get("body")))
        if o.get("data"):
            if path.startswith("/stocks/bars"):
                return 200, {"bars": {"TQQQ": bars_orb()}}
            if "/trades/latest" in path:
                return 200, {"trade": {"p": 40.2 if "/SOXL/" in path else 60.55}}
            return 200, {}
        if path == "/clock":
            return 200, {"is_open": True}
        if path == "/bankroll":
            return 200, {"mode": "live", "profile": "live-aggressive", "equity": self.equity, "cash": self.cash,
                         "realEquity": self.equity, "accountId": "…ab12", "tradingBlocked": False}
        if path == "/positions":
            if self.scenario == "one_position":
                return 200, [{"symbol": "SOXL", "qty": "0.5", "qty_available": "0", "avg_entry_price": "40.00"}]
            return 200, []
        if path == "/orders?status=open":
            if self.scenario == "one_position":
                return 200, [{"id": "stop-soxl", "symbol": "SOXL", "side": "sell", "type": "stop", "stop_price": "39.50", "qty": "0.5"}]
            return 200, []
        if path == "/orders/stop-soxl":
            return 200, {"id": "stop-soxl", "status": "accepted"}
        if path == "/positions/SOXL":
            return 200, {"symbol": "SOXL", "qty": "0.5", "qty_available": "0", "avg_entry_price": "40.00"}
        if path.startswith("/assets/"):
            sym = path.rsplit("/", 1)[1]
            frac = not (self.scenario == "not_fractionable" and sym == "TQQQ")
            return 200, {"symbol": sym, "status": "active", "tradable": True, "fractionable": frac, "class": "us_equity"}
        if path.startswith("/orders:by_client_order_id"):
            if self.scenario == "dup_guard":
                return 200, {"id": "o-earlier", "status": "accepted", "client_order_id": path.split("=")[-1]}
            return 404, {"code": 40410000, "message": "order not found"}
        if m == "DELETE":
            return 204, {}
        if m == "POST" and path == "/orders":
            b = o["body"]
            if b.get("side") == "buy":
                qty = round(float(b["notional"]) / 60.56, 9)
                return 200, {"entry": {"id": "buy-1", "status": "filled", "filled_avg_price": "60.56", "filled_qty": str(qty),
                                       "client_order_id": b.get("client_order_id")},
                             "stop": {"id": "stop-1", "status": "accepted"}, "takeProfit": b["protect"]["take_profit"]}
            return 200, {"id": "sell-1", "status": "accepted"}
        return 200, {}


def run_scenario(scenario, tmp, live=True, watch_file=None):
    fake = Fake(scenario)
    auto = tmp / scenario
    auto.mkdir(parents=True, exist_ok=True)
    for f in auto.glob("*.json"):
        f.unlink()
    if scenario == "daily_loss":
        (auto / f"{DAY}.json").write_text(json.dumps({"day": DAY, "mode": "live", "equityOpen": 25.0, "entries": 0, "lostToday": [],
                                                      "positions": {}, "trades": [], "actions": [], "done": None, "runs": 0, "lastSignal": {}}))
    here = tmp / f"here-{scenario}"
    here.mkdir(parents=True, exist_ok=True)
    (here / "watchlist.json").write_text(json.dumps(watch_file or {"day": DAY, "symbols": ["SPY", "QQQ"], "avoid": []}))
    ap.AUTO = auto
    ap.HERE = here
    ap.alpaca = fake
    ap.gw.ALPACA_LIVE = live
    ap.now_ct = lambda: datetime(2026, 11, 3, 9, 21, tzinfo=CT)
    ap.time.sleep = lambda s: None
    r = ap.run()
    day = json.loads((auto / f"{DAY}.json").read_text())
    posts = [(p, b) for (m, p, b) in fake.calls if m == "POST"]
    return r, day, fake, posts


def main():
    tmp = Path(__file__).parent / "out" / "live"
    fails = []

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond:
            fails.append(msg)

    P = backtest.load_params("live-aggressive")
    print("== profile: live-aggressive loads over DEFAULT")
    check(P["floor"] == 5.0 and P["max_pos_pct"] == 100.0 and P["max_positions"] == 1 and P["daily_loss"] == 5.0, f"money rules: floor {P['floor']} cap {P['max_pos_pct']}% positions {P['max_positions']} daily loss {P['daily_loss']}")
    check(P["setup"] == "orb" and P["target_r"] == 3.0 and P["risk_pct"] == 100.0, f"knobs: setup {P['setup']} target {P['target_r']}R risk {P['risk_pct']}%")
    check(backtest.load_params("paper") == backtest.DEFAULT, "paper profile == backtest.DEFAULT (the Oct 21 rules, unchanged)")
    check(backtest.load_params() == backtest.DEFAULT, "no profile == backtest.DEFAULT (the lab is unchanged)")

    print("== scenario: live_buy (ORB breakout on TQQQ at 9:15 CT; all-in; id + lookup before the POST)")
    r, day, fake, posts = run_scenario("live_buy", tmp)
    buys = [b for p, b in posts if p == "/orders" and b.get("side") == "buy"]
    for p, b in posts:
        print("   POST", p, json.dumps(b))
    check(day["mode"] == "live" and day["profile"] == "live-aggressive", f"day file mode {day['mode']} profile {day.get('profile')}")
    check(len(buys) == 1, "exactly one buy posted")
    check(buys and buys[0]["notional"] == "24.98" and buys[0]["symbol"] == "TQQQ", f"all-in: notional {buys and buys[0]['notional']} of $25 cash")
    check(buys and buys[0].get("client_order_id", "").startswith(f"gm-{DAY}-TQQQ-"), f"client_order_id {buys and buys[0].get('client_order_id')}")
    check(buys and buys[0]["protect"]["stop_price"] == "59.44" and buys[0]["time_in_force"] == "day", f"stop {buys and buys[0]['protect']['stop_price']} (range mid 59.5 x 0.999), day order")
    lookups = [i for i, (m, p, b) in enumerate(fake.calls) if p.startswith("/orders:by_client_order_id")]
    post_i = [i for i, (m, p, b) in enumerate(fake.calls) if m == "POST" and p == "/orders"]
    check(lookups and post_i and lookups[0] < post_i[0], "the id lookup happened BEFORE the POST")
    check("TQQQ" in day["positions"] and day["entries"] == 1 and day["positions"]["TQQQ"]["stopId"] == "stop-1", f"position recorded with its stop: {day['positions'].get('TQQQ')}")
    check(day["positions"].get("TQQQ", {}).get("target") == round(60.56 + 3 * (60.56 - 59.44), 2), f"target = fill + 3R: {day['positions'].get('TQQQ', {}).get('target')}")
    check(all(v is True for v in day["assets"].values()) and len(day["assets"]) == 13, f"/assets checked once per name: {len(day['assets'])} names")
    check(day.get("accountId") == "…ab12", f"account hint recorded: {day.get('accountId')}")

    print("== scenario: dup_guard (the lookup finds an accepted order with this id; nothing may be posted)")
    r, day, fake, posts = run_scenario("dup_guard", tmp)
    check(not [b for p, b in posts if p == "/orders"], "no order posted")
    check(any(a.get("do") == "skip" and "already at Alpaca" in a.get("why", "") for a in day["actions"]), "skip action recorded with the reason")

    print("== scenario: floor (equity $4.90 <= $5 floor: flatten and lock)")
    r, day, fake, posts = run_scenario("floor", tmp)
    check(("DELETE", "/positions", None) in fake.calls, "DELETE /positions sent")
    check(day.get("done") == "floor" and day.get("floorLocked") is True, f"done={day.get('done')} floorLocked={day.get('floorLocked')}")
    check(not [b for p, b in posts if p == "/orders"], "no buy after the floor")

    print("== scenario: daily_loss (open $25, now $19.90: $5.10 down >= $5 limit; flatten, done)")
    r, day, fake, posts = run_scenario("daily_loss", tmp)
    check(("DELETE", "/positions", None) in fake.calls, "DELETE /positions sent")
    check(day.get("done") == "daily loss limit", f"done={day.get('done')}")

    print("== scenario: not_fractionable (/assets says TQQQ is not fractionable: never traded)")
    r, day, fake, posts = run_scenario("not_fractionable", tmp)
    check(not [b for p, b in posts if p == "/orders"], "no order posted")
    check(day["assets"].get("TQQQ") is False and "TQQQ" not in day.get("watch", []), f"TQQQ dropped: assets={day['assets'].get('TQQQ')} watch has it={('TQQQ' in day.get('watch', []))}")

    print("== scenario: avoid_list (the crew's avoid list for today names TQQQ)")
    r, day, fake, posts = run_scenario("avoid_list", tmp, watch_file={"day": DAY, "symbols": ["SPY"], "avoid": ["TQQQ"]})
    check(not [b for p, b in posts if p == "/orders"], "no order posted")
    check("TQQQ" not in day.get("watch", []) and "SOXL" in day.get("watch", []), "TQQQ out, the rest of the universe in")

    print("== scenario: one_position (SOXL already held with its stop: max_positions 1 blocks the TQQQ signal)")
    r, day, fake, posts = run_scenario("one_position", tmp)
    check(not [b for p, b in posts if p == "/orders" and b.get("side") == "buy"], "no second buy")
    check("SOXL" in day["positions"], "the held SOXL was adopted into the day file")

    print("== scenario: paper_unchanged (ALPACA_LIVE off: paper rules, the crew's watchlist, no /assets reads)")
    r, day, fake, posts = run_scenario("paper_unchanged", tmp, live=False, watch_file={"day": DAY, "symbols": ["SPY", "QQQ"], "avoid": []})
    check(day["mode"] == "paper" and day["profile"] == "paper", f"mode {day['mode']} profile {day.get('profile')}")
    check(day.get("watch") == ["SPY", "QQQ"], f"watch is the crew's list: {day.get('watch')}")
    check(not any(p.startswith("/assets/") for m, p, b in fake.calls), "no /assets reads in paper mode")
    check(not [b for p, b in posts if p == "/orders"], "no order (SPY/QQQ have no bars in this fake)")
    ap.gw.ALPACA_LIVE = False
    rs = ap.rules_summary()
    check(rs["profile"] == "paper" and rs["floor"] == 20.0 and rs["maxPosPct"] == 40.0, f"paper rules summary: {rs['floor']} floor, {rs['maxPosPct']}% cap")
    ap.gw.ALPACA_LIVE = True
    rs = ap.rules_summary()
    check(rs["profile"] == "live-aggressive" and rs["floor"] == 5.0 and rs["maxPosPct"] == 100.0 and rs["universe"][0] == "TQQQ", f"live rules summary: {rs['floor']} floor, {rs['maxPosPct']}% cap, {len(rs['universe'])} names")
    ap.gw.ALPACA_LIVE = False

    print()
    print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
