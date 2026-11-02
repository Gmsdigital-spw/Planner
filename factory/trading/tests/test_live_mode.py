"""Offline harness for the autopilot's LIVE profile (Nov 2, 2026) with a fake Alpaca: no network, no keys, no orders.
Writes only under tests/out/. Run: python3 factory/trading/tests/test_live_mode.py

Scenarios (ALPACA_LIVE on, profile live-aggressive): an all-in ORB entry with a client_order_id and a read-before-POST
lookup; the duplicate guard; a lookup that fails (no blind POST); the $5 floor; an unfunded account (waits, never locks);
the $5 daily loss; a flatten Alpaca did NOT complete (the day stays open and retries until /positions is empty); an
early-close day (flat 15 minutes before next_close); a position carried past the close; a mode switch during the day
(the paper record is archived, live starts fresh); a stop that filled between cycles (Alpaca's fill time and price in
the journal); a gateway 207 (stop refused, sold at once: an entry, never a position); a broken live profile (the bot
stops, no paper fallback); a non-numeric floor variable; a non-fractionable name dropped; the crew's avoid list; one
position at a time; and paper mode unchanged (ALPACA_LIVE off = the Oct 21 rules and the crew's watchlist)."""
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


TQQQ_HELD = {"symbol": "TQQQ", "qty": "0.4", "qty_available": "0", "avg_entry_price": "60.56"}
TQQQ_REC = {"entry": 60.56, "stop0": 59.44, "stop": 59.44, "target": 63.92, "high": 60.6, "stopId": "stop-1", "since": f"{DAY}T15:15:00Z", "qty": "0.4"}


class Fake:
    """Minimal live Alpaca seen through the gateway: a $25 account, no positions unless the scenario says so.
    Knobs (set by run_scenario): equity, positions, clock, delete_positions (code, body) and whether it empties the
    positions, stop_order (GET /orders/stop-1), closed_sells, lookup (code, body), buy (code, body)."""
    def __init__(self, scenario):
        self.scenario = scenario
        self.calls = []
        self.equity = {"floor": 4.9, "daily_loss": 19.9, "flatten_failed": 19.5, "unfunded": 0.0}.get(scenario, 25.0)
        self.cash = self.equity
        self.positions = []
        self.clock = {"is_open": True}
        self.delete_positions = (207, [{"symbol": "TQQQ", "status": 200}])
        self.delete_empties = True
        self.stop_order = {"id": "stop-1", "status": "accepted"}
        self.closed_sells = []
        self.lookup = None
        self.buy = None

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
            return 200, self.clock
        if path == "/bankroll":
            return 200, {"mode": "live", "profile": "live-aggressive", "equity": self.equity, "cash": self.cash,
                         "realEquity": self.equity, "accountId": "…ab12", "tradingBlocked": False}
        if path == "/positions":
            return 200, list(self.positions)
        if path == "/orders?status=open":
            if self.scenario == "one_position":
                return 200, [{"id": "stop-soxl", "symbol": "SOXL", "side": "sell", "type": "stop", "stop_price": "39.50", "qty": "0.5"}]
            return 200, []
        if path.startswith("/orders?status=closed"):
            return 200, list(self.closed_sells)
        if path == "/orders/stop-soxl":
            return 200, {"id": "stop-soxl", "status": "accepted"}
        if path == "/orders/stop-1":
            return 200, dict(self.stop_order)
        if path == "/positions/SOXL":
            return 200, {"symbol": "SOXL", "qty": "0.5", "qty_available": "0", "avg_entry_price": "40.00"}
        if path.startswith("/assets/"):
            sym = path.rsplit("/", 1)[1]
            frac = not (self.scenario == "not_fractionable" and sym == "TQQQ")
            return 200, {"symbol": sym, "status": "active", "tradable": True, "fractionable": frac, "class": "us_equity"}
        if path.startswith("/orders:by_client_order_id"):
            if self.lookup:
                return self.lookup
            if self.scenario == "dup_guard":
                return 200, {"id": "o-earlier", "status": "accepted", "client_order_id": path.split("=")[-1]}
            return 404, {"code": 40410000, "message": "order not found"}
        if m == "DELETE":
            if path.startswith("/positions"):
                if self.delete_empties:
                    self.positions = []
                return self.delete_positions
            return 204, {}
        if m == "POST" and path == "/orders":
            b = o["body"]
            if b.get("side") == "buy":
                if self.buy:
                    return self.buy
                qty = round(float(b["notional"]) / 60.56, 9)
                return 200, {"entry": {"id": "buy-1", "status": "filled", "filled_avg_price": "60.56", "filled_qty": str(qty),
                                       "client_order_id": b.get("client_order_id")},
                             "stop": {"id": "stop-1", "status": "accepted"}, "takeProfit": b["protect"]["take_profit"]}
            return 200, {"id": "sell-1", "status": "accepted"}
        return 200, {}


def day_file(**kw):
    d = {"day": DAY, "mode": "live", "profile": "live-aggressive", "equityOpen": 25.0, "entries": 0, "lostToday": [],
         "positions": {}, "trades": [], "actions": [], "done": None, "runs": 0, "lastSignal": {}}
    d.update(kw)
    return d


def run_scenario(scenario, tmp, live=True, watch_file=None, day=None, now=None, setup=None, fake=None, keep=False):
    fake = fake or Fake(scenario)
    auto = tmp / scenario
    auto.mkdir(parents=True, exist_ok=True)
    if not keep:
        for f in auto.glob("*.json"):
            f.unlink()
    if day is not None:
        (auto / f"{DAY}.json").write_text(json.dumps(day))
    here = tmp / f"here-{scenario}"
    here.mkdir(parents=True, exist_ok=True)
    (here / "watchlist.json").write_text(json.dumps(watch_file or {"day": DAY, "symbols": ["SPY", "QQQ"], "avoid": []}))
    if setup:
        setup(fake)
    ap.AUTO = auto
    ap.HERE = here
    ap.alpaca = fake
    ap.gw.ALPACA_LIVE = live
    ap.now_ct = lambda: now or datetime(2026, 11, 3, 9, 21, tzinfo=CT)
    ap.time.sleep = lambda s: None
    r = ap.run()
    d = json.loads((auto / f"{DAY}.json").read_text())
    posts = [(p, b) for (m, p, b) in fake.calls if m == "POST"]
    return r, d, fake, posts


def main():
    tmp = Path(__file__).parent / "out" / "live"
    fails = []

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond:
            fails.append(msg)

    P = backtest.load_params("live-aggressive", strict=True)
    print("== profile: live-aggressive loads over DEFAULT (strict: every money rule present)")
    check(P["floor"] == 5.0 and P["max_pos_pct"] == 100.0 and P["max_positions"] == 1 and P["daily_loss"] == 5.0, f"money rules: floor {P['floor']} cap {P['max_pos_pct']}% positions {P['max_positions']} daily loss {P['daily_loss']}")
    check(P["setup"] == "orb" and P["target_r"] == 3.0 and P["risk_pct"] == 100.0, f"knobs: setup {P['setup']} target {P['target_r']}R risk {P['risk_pct']}%")
    locked = {k: backtest.load_params("paper")[k] for k in backtest.LOCKED}
    check(locked == {k: backtest.DEFAULT[k] for k in backtest.LOCKED}, f"paper profile's money rules == backtest.DEFAULT's (the Oct 21 rules): {locked}")
    check(backtest.load_params("paper") == backtest.load_params(), "paper profile adds nothing beyond params.json (a lab adoption still reaches the paper bot)")
    check(set(backtest.load_profile("paper")["params"]) <= backtest.LOCKED, "paper.json pins only LOCKED keys")
    check("expected_account_id" not in backtest.load_profile("paper") and "expected_account_id" not in backtest.load_profile("live-aggressive"), "no account id field in a committed profile")

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
    check(day.get("flatAt") == "14:45", f"flat time on a normal day: {day.get('flatAt')}")

    print("== scenario: dup_guard (the lookup finds an accepted order with this id; nothing may be posted)")
    r, day, fake, posts = run_scenario("dup_guard", tmp)
    check(not [b for p, b in posts if p == "/orders"], "no order posted")
    check(any(a.get("do") == "skip" and "already at Alpaca" in a.get("why", "") for a in day["actions"]), "skip action recorded with the reason")

    print("== scenario: lookup_failed (the lookup answers 500: fail closed, no blind POST, the bar is retried)")
    r, day, fake, posts = run_scenario("lookup_failed", tmp, setup=lambda f: setattr(f, "lookup", (500, "<html>Internal Server Error</html>")))
    check(not [b for p, b in posts if p == "/orders"], "no order posted")
    check(any(a.get("do") == "skip" and "lookup" in a.get("why", "") and "failed" in a.get("why", "") for a in day["actions"]), "skip action says the lookup failed")
    check("TQQQ" not in day["lastSignal"], "the signal bar is not marked as used, so the next cycle tries again")

    print("== scenario: floor (equity $4.90 <= $5 floor: flatten, confirm, lock)")
    r, day, fake, posts = run_scenario("floor", tmp)
    check(("DELETE", "/positions?cancel_orders=true", None) in fake.calls, "DELETE /positions?cancel_orders=true sent")
    check(("GET", "/positions", None) in fake.calls, "the flatten read /positions back before believing it")
    check(day.get("done") == "floor" and day.get("floorLocked") is True and day.get("locked") == "floor", f"done={day.get('done')} floorLocked={day.get('floorLocked')}")
    check(not [b for p, b in posts if p == "/orders"], "no buy after the floor")

    print("== scenario: unfunded (live equity $0.00: wait for the deposit, never lock the day)")
    r, day, fake, posts = run_scenario("unfunded", tmp)
    check(r["status"] == "waiting" and "funded" in r["note"], f"status {r['status']}: {r['note']}")
    check(not day.get("done") and not day.get("floorLocked") and not any(m == "DELETE" for m, p, b in fake.calls), "no lock, no flatten; the next cycle re-reads the account")

    print("== scenario: daily_loss (open $25, now $19.90: $5.10 down >= $5 limit; flatten, confirmed, done)")
    r, day, fake, posts = run_scenario("daily_loss", tmp, day=day_file(positions={"TQQQ": dict(TQQQ_REC)}),
                                       setup=lambda f: (setattr(f, "positions", [dict(TQQQ_HELD)]),
                                                        setattr(f, "closed_sells", [{"id": "cls-1", "symbol": "TQQQ", "side": "sell", "status": "filled", "filled_avg_price": "59.90", "filled_qty": "0.4", "filled_at": f"{DAY}T15:21:40Z"}])))
    check(("DELETE", "/positions?cancel_orders=true", None) in fake.calls, "DELETE /positions?cancel_orders=true sent")
    check(day.get("done") == "daily loss limit", f"done={day.get('done')}")
    tr = day["trades"][-1] if day["trades"] else {}
    check(tr.get("sym") == "TQQQ" and tr.get("exit") == 59.9 and tr.get("exitAt") == f"{DAY}T15:21:40Z" and tr.get("why", "").startswith("flat: daily loss"), f"the flatten exit is Alpaca's filled sell, with its time: {tr}")

    print("== scenario: flatten_failed (Alpaca answers 207 with a 403 leg and still holds TQQQ: the day must NOT lock)")
    fk = Fake("flatten_failed")
    fk.positions = [dict(TQQQ_HELD)]
    fk.delete_positions = (207, [{"symbol": "TQQQ", "status": 403, "body": {"message": "insufficient qty available for order (requested: 0.4, available: 0)"}}])
    fk.delete_empties = False
    r, day, fake, posts = run_scenario("flatten_failed", tmp, day=day_file(positions={"TQQQ": dict(TQQQ_REC)}), fake=fk)
    fl = [a for a in day["actions"] if a.get("do") == "flatten"]
    check(fl and fl[-1].get("flat") is False and fl[-1].get("still") == ["TQQQ"] and fl[-1].get("failed") == ["TQQQ:403"], f"flatten action records the failure: {fl and fl[-1]}")
    check(not day.get("done") and "TQQQ" in day["positions"] and day.get("locked") == "daily loss limit", f"day open (done={day.get('done')}), position kept, entries locked")
    check(r["status"] == "ok" and "NOT confirmed" in r["note"], f"cycle status {r['status']}: {r['note']}")
    check(fake.calls.count(("DELETE", "/positions?cancel_orders=true", None)) == 2, "the close was tried twice in the cycle")
    fk.delete_empties = True
    fk.delete_positions = (207, [{"symbol": "TQQQ", "status": 200}])
    fk.closed_sells = [{"id": "cls-2", "symbol": "TQQQ", "side": "sell", "status": "filled", "filled_avg_price": "59.50", "filled_qty": "0.4", "filled_at": f"{DAY}T15:22:30Z"}]
    r, day, fake, posts = run_scenario("flatten_failed", tmp, fake=fk, keep=True, now=datetime(2026, 11, 3, 9, 22, tzinfo=CT))
    check(day.get("done") == "daily loss limit" and not day["positions"] and not day.get("flattenFailed"), f"next cycle: flatten confirmed, done={day.get('done')}")
    check(day["trades"] and day["trades"][-1].get("exit") == 59.5, f"exit journaled from the closed sell: {day['trades'][-1] if day['trades'] else None}")

    print("== scenario: early_close (next_close 12:00 CT: flat at 11:45, not 2:45)")
    r, day, fake, posts = run_scenario("early_close", tmp, day=day_file(positions={"TQQQ": dict(TQQQ_REC)}), now=datetime(2026, 11, 3, 11, 46, tzinfo=CT),
                                       setup=lambda f: (setattr(f, "positions", [dict(TQQQ_HELD)]), setattr(f, "clock", {"is_open": True, "next_close": f"{DAY}T12:00:00-06:00"})))
    check(day.get("flatAt") == "11:45", f"flat time from next_close: {day.get('flatAt')}")
    check(("DELETE", "/positions?cancel_orders=true", None) in fake.calls and day.get("done") == "closed for the day", f"flattened and done at 11:46: done={day.get('done')}")
    r, day, fake, posts = run_scenario("early_close_entry", tmp, now=datetime(2026, 11, 3, 11, 20, tzinfo=CT),
                                       setup=lambda f: setattr(f, "clock", {"is_open": True, "next_close": f"{DAY}T12:00:00-06:00"}))
    check(not [b for p, b in posts if p == "/orders"], "no new entry within 30 minutes of an early flat time")

    print("== scenario: held_after_close (market closed at 12:05 CT with TQQQ still held: say so, sell at the next open)")
    r, day, fake, posts = run_scenario("held_after_close", tmp, day=day_file(positions={"TQQQ": dict(TQQQ_REC)}), now=datetime(2026, 11, 3, 12, 5, tzinfo=CT),
                                       setup=lambda f: setattr(f, "clock", {"is_open": False, "next_close": f"{DAY}T12:00:00-06:00"}))
    check(r["status"] == "closed" and "still held" in r["note"], f"status {r['status']}: {r['note']}")
    check(day.get("heldAfterClose") == ["TQQQ"] and not day.get("done") and any(a.get("do") == "held after close" for a in day["actions"]), "recorded, day not locked")

    print("== scenario: mode_switch (a paper day file exists with an open paper position; the live runner starts fresh)")
    paper_day = {"day": DAY, "mode": "paper", "profile": "paper", "equityOpen": 22.0, "entries": 2, "lostToday": ["QQQ"],
                 "positions": {"SPY": {"entry": 680.0, "stop0": 676.0, "stop": 676.0, "target": 688.0, "high": 681.0, "stopId": "p-1"}},
                 "trades": [], "actions": [], "done": None, "runs": 40, "lastSignal": {}}
    r, day, fake, posts = run_scenario("mode_switch", tmp, day=paper_day)
    arch = tmp / "mode_switch" / f"{DAY}-paper.json"
    check(arch.exists() and json.loads(arch.read_text())["equityOpen"] == 22.0, "the paper record is archived as <day>-paper.json")
    check(day["mode"] == "live" and day["equityOpen"] == 25.0 and day["lostToday"] == [] and "SPY" not in day["positions"], f"live starts fresh: equityOpen {day['equityOpen']}, lostToday {day['lostToday']}")
    sw = [a for a in day["actions"] if a.get("do") == "mode switch"]
    check(sw and "SPY" in sw[0]["why"] and "NOBODY manages" in sw[0]["why"], f"the orphaned paper position is called out: {sw and sw[0]['why']}")
    check(day["entries"] == 1 and "TQQQ" in day["positions"], "the live entry budget is the live account's own (first entry taken)")

    print("== scenario: stop_fill_time (TQQQ gone from /positions; its stop order reads back filled with a time)")
    r, day, fake, posts = run_scenario("stop_fill_time", tmp, day=day_file(positions={"TQQQ": dict(TQQQ_REC)}, entries=1),
                                       setup=lambda f: setattr(f, "stop_order", {"id": "stop-1", "status": "filled", "filled_avg_price": "59.40", "filled_qty": "0.4", "filled_at": f"{DAY}T15:31:02.5Z"}))
    tr = day["trades"][-1] if day["trades"] else {}
    check(tr.get("why") == "stop filled" and tr.get("exit") == 59.4 and tr.get("exitAt") == f"{DAY}T15:31:02.5Z" and tr.get("qty") == 0.4, f"journal carries Alpaca's fill: {tr}")
    check("TQQQ" in day["lostToday"] and not [b for p, b in posts if p == "/orders"], "lost for today: no re-entry in TQQQ")

    print("== scenario: stop_refused (gateway 207: entry filled, stop refused, sold at once: an entry, never a position)")
    r, day, fake, posts = run_scenario("stop_refused", tmp, setup=lambda f: setattr(f, "buy", (207, {
        "entry": {"id": "buy-1", "status": "filled", "filled_avg_price": "60.56", "filled_qty": "0.412"},
        "stop": {"code": 42210000, "message": "stop_price must be below the current price"},
        "flattened": {"id": "sell-x", "status": "accepted"}, "note": "stop order was refused, so the position was sold at once"})))
    check("TQQQ" not in day["positions"] and day["entries"] == 1 and "TQQQ" in day["lostToday"], f"no position kept, entry counted, no retry today: positions={list(day['positions'])} entries={day['entries']}")
    tr = day["trades"][-1] if day["trades"] else {}
    check(tr.get("why", "").startswith("stop refused") and tr.get("exit") is None, f"journaled honestly with no invented exit: {tr}")

    print("== scenario: broken_profile (live-aggressive.json unreadable: the bot stops, nothing is sent)")
    broken = tmp / "profiles-broken"
    broken.mkdir(parents=True, exist_ok=True)
    (broken / "live-aggressive.json").write_text('{"params": {"floor": 5.0,}}')
    good_dir = backtest.PROFILES_DIR
    backtest.PROFILES_DIR = str(broken)
    try:
        try:
            r, day, fake, posts = run_scenario("broken_profile", tmp)
            check(False, "run() should raise on a broken live profile")
        except backtest.ProfileError as e:
            check("could not be loaded" in str(e), f"ProfileError: {str(e)[:90]}")
        check(not (tmp / "broken_profile" / f"{DAY}.json").exists() or not json.loads((tmp / "broken_profile" / f"{DAY}.json").read_text()).get("positions"), "no order, no position")
        (broken / "live-aggressive.json").write_text(json.dumps({"params": {"floor": 5.0}}))
        try:
            run_scenario("broken_profile", tmp)
            check(False, "run() should raise on an incomplete live profile")
        except backtest.ProfileError as e:
            check("missing money rules" in str(e), f"ProfileError: {str(e)[:90]}")
        ap.gw.ALPACA_LIVE = False
        check(backtest.load_params("paper") == backtest.load_params(), "paper mode is not strict (no file = the paper rules as before)")
    finally:
        backtest.PROFILES_DIR = good_dir
        ap.gw.ALPACA_LIVE = True

    print("== scenario: bad_floor_var (ALPACA_LIVE_FLOOR='$5' must not stop the cycle)")
    ap.os.environ["ALPACA_LIVE_FLOOR"] = "$5"
    try:
        r, day, fake, posts = run_scenario("bad_floor_var", tmp)
        check(ap.floor_for({"floor": 5.0}) == 5.0 and "not a number" in str(ap.LAST.get("floorWarning")), f"profile floor applies, warning kept: {ap.LAST.get('floorWarning')}")
        check(r["status"] == "ok" and day["entries"] == 1, "the cycle ran and traded as usual")
    finally:
        ap.os.environ.pop("ALPACA_LIVE_FLOOR", None)
        ap.LAST.pop("floorWarning", None)

    print("== scenario: not_fractionable (/assets says TQQQ is not fractionable: never traded)")
    r, day, fake, posts = run_scenario("not_fractionable", tmp)
    check(not [b for p, b in posts if p == "/orders"], "no order posted")
    check(day["assets"].get("TQQQ") is False and "TQQQ" not in day.get("watch", []), f"TQQQ dropped: assets={day['assets'].get('TQQQ')} watch has it={('TQQQ' in day.get('watch', []))}")

    print("== scenario: avoid_list (the crew's avoid list for today names TQQQ)")
    r, day, fake, posts = run_scenario("avoid_list", tmp, watch_file={"day": DAY, "symbols": ["SPY"], "avoid": ["TQQQ"]})
    check(not [b for p, b in posts if p == "/orders"], "no order posted")
    check("TQQQ" not in day.get("watch", []) and "SOXL" in day.get("watch", []), "TQQQ out, the rest of the universe in")

    print("== scenario: one_position (SOXL already held with its stop: max_positions 1 blocks the TQQQ signal)")
    r, day, fake, posts = run_scenario("one_position", tmp, setup=lambda f: setattr(f, "positions", [{"symbol": "SOXL", "qty": "0.5", "qty_available": "0", "avg_entry_price": "40.00"}]))
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
