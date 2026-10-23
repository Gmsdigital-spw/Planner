"""Dry-run harness for autopilot.py's raise-stop path with a fake Alpaca (no network, no orders).
Replays Oct 22, 2026: XLF bought 0.176549913 sh at 56.358, stop 56.13 (R=0.228), price now 56.72 (1.59R):
the trail must move the stop to 56.52 with the WHOLE position quantity, never "0".
Run: python3 factory/trading/tests/test_trail_stop.py   (no network, no keys, no orders; writes only under tests/out/)
Added Oct 23, 2026 with the trail-stop fix. Pass --expect-old-bug only against a pre-fix autopilot.py."""
import importlib, json, sys, types
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TRADING = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path(__file__).resolve().parent.parent
EXPECT_OLD = "--expect-old-bug" in sys.argv
sys.path.insert(0, str(TRADING))
import autopilot as ap  # noqa: E402

CT = ZoneInfo("America/Chicago")
QTY = "0.176549913"


class Fake:
    """Minimal Alpaca: one XLF position held by one open stop order."""
    def __init__(self, scenario):
        self.scenario = scenario          # trail | target | refuse | filled_in_race | unknown_cancel | partial | transport
        self.calls = []
        self.canceled = {}
        self.stop_posts = 0
        self.px = {"target": 56.90}.get(scenario, 56.72)

    def __call__(self, o, st):
        m, path = o.get("method", "GET").upper(), o["path"]
        self.calls.append((m, path, o.get("body")))
        if o.get("data"):
            if path.startswith("/stocks/bars"):
                bars = [{"t": f"2026-10-22T{h:02d}:{mi:02d}:00Z", "o": 56.4, "h": hi, "l": 56.3, "c": 56.5, "v": 1000}
                        for (h, mi, hi) in [(15, 20, 56.40), (15, 30, 56.50), (16, 0, 56.60), (16, 15, 56.75)]]
                return 200, {"bars": {"XLF": bars}}
            if "/trades/latest" in path:
                return 200, {"trade": {"p": self.px}}
            return 200, {}
        if path == "/clock":
            return 200, {"is_open": True}
        if path == "/bankroll":
            return 200, {"equity": 24.97, "cash": 15.0}
        if path == "/positions":
            return 200, [{"symbol": "XLF", "qty": QTY, "qty_available": "0", "avg_entry_price": "56.358"}]
        if path == "/positions/XLF":
            if self.scenario == "filled_in_race":
                return 404, {"message": "position does not exist"}
            if self.scenario == "transport":
                raise RuntimeError("ConnectionError: read timed out (test)")
            q = "0.100000000" if self.scenario == "partial" else QTY
            avail = q if self.canceled.get("stop-1") else "0"
            return 200, {"symbol": "XLF", "qty": q, "qty_available": avail, "avg_entry_price": "56.358"}
        if path == "/orders?status=open":
            return 200, [{"id": "stop-1", "symbol": "XLF", "side": "sell", "type": "stop", "stop_price": "56.13", "qty": QTY}]
        if path == "/orders/stop-1" and m == "GET":
            if self.scenario == "filled_in_race":
                return 200, {"id": "stop-1", "status": "filled", "filled_qty": QTY, "filled_avg_price": "56.11"}
            if self.scenario == "unknown_cancel":
                return 200, {"id": "stop-1", "status": "pending_cancel"}
            if self.scenario == "partial" and self.canceled.get("stop-1"):
                return 200, {"id": "stop-1", "status": "canceled", "filled_qty": "0.076549913", "filled_avg_price": "56.12"}
            return 200, {"id": "stop-1", "status": "canceled" if self.canceled.get("stop-1") else "accepted"}
        if m == "DELETE" and path.startswith("/orders/"):
            self.canceled[path.rsplit("/", 1)[1]] = True
            return 204, {}
        if m == "POST" and path == "/orders":
            b = o["body"]
            if float(b.get("qty") or 0) <= 0:
                return 422, {"code": 42210000, "message": "qty must be > 0"}
            if b["type"] == "stop":
                self.stop_posts += 1
                if self.scenario == "refuse":
                    return 422, {"code": 42210000, "message": "stop refused (test)"}
                return 200, {"id": f"stop-{self.stop_posts + 1}", "status": "accepted", "qty": b["qty"], "stop_price": b["stop_price"]}
            return 200, {"id": "mkt-1", "status": "accepted", "qty": b["qty"]}
        return 200, {}


def run_scenario(scenario, tmp):
    fake = Fake(scenario)
    auto = tmp / scenario
    auto.mkdir(parents=True, exist_ok=True)
    (auto / "2026-10-22.json").write_text(json.dumps({
        "day": "2026-10-22", "mode": "paper", "equityOpen": 24.96, "entries": 1, "lostToday": [],
        "positions": {"XLF": {"entry": 56.358, "stop0": 56.13, "stop": 56.13, "target": 56.814, "high": 56.358,
                              "stopId": "stop-1", "since": "2026-10-22T15:20:00Z", "qty": QTY}},
        "trades": [], "actions": [], "done": None, "runs": 1, "lastSignal": {}}))
    ap.AUTO = auto
    ap.alpaca = fake
    ap.now_ct = lambda: datetime(2026, 10, 22, 11, 29, tzinfo=CT)
    ap.watchlist = lambda day: ([], [])
    ap.time.sleep = lambda s: None
    if scenario == "unknown_cancel":
        clock = {"t": 1000.0}
        def fake_time():
            clock["t"] += 3.0
            return clock["t"]
        ap.time.time = fake_time
    r = ap.run()
    day = json.loads((auto / "2026-10-22.json").read_text())
    posts = [(m, b) for (m, p, b) in fake.calls if m == "POST" and p == "/orders"]
    return r, day, fake, posts


def main():
    tmp = Path(__file__).parent / "out"
    fails = []

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond:
            fails.append(msg)

    print("== scenario: trail (price 56.72 = 1.59R; stop should move to 56.52)")
    r, day, fake, posts = run_scenario("trail", tmp)
    stop_posts = [b for m, b in posts if b["type"] == "stop"]
    mkt_posts = [b for m, b in posts if b["type"] == "market"]
    for b in posts:
        print("   POST /orders", json.dumps(b[1]))
    if EXPECT_OLD:
        check(stop_posts and stop_posts[0]["qty"] == "0", "old code sends the new stop with qty '0' (the Oct 22 bug)")
        check(any(a.get("status") == 422 for a in day["actions"]), "old code logs a 422 refusal")
    else:
        check(len(stop_posts) == 1, "exactly one new stop order posted")
        check(stop_posts and stop_posts[0]["qty"] == QTY, f"new stop carries the whole position qty {QTY}")
        check(stop_posts and stop_posts[0]["stop_price"] == "56.52", "new stop price is 56.52 (high 56.75 - 1R)")
        check(not mkt_posts, "no market sell: the winner stays on with its new stop")
        check(("DELETE", "/orders/stop-1", None) in fake.calls, "old stop was canceled first")
        check(fake.calls.index(("DELETE", "/orders/stop-1", None)) < fake.calls.index(("POST", "/orders", stop_posts[0])) if stop_posts else False,
              "cancel came before the re-place")
        check(any(("GET", "/orders/stop-1") == (m, p) for m, p, _ in fake.calls), "cancel was confirmed by reading the order back")
        pos = day["positions"].get("XLF") or {}
        check(pos.get("stop") == 56.52 and pos.get("stopId") == "stop-2", f"day file: stop {pos.get('stop')} id {pos.get('stopId')}")
        check(any(a.get("do") == "raise stop" and a.get("qty") == QTY for a in day["actions"]), "action 'raise stop' recorded with qty")
        check(not any(a.get("status", 200) >= 300 for a in day["actions"]), "no refused action in the day file")

        print("== scenario: target (price 56.90 >= target 56.814; sell the whole position)")
        r, day, fake, posts = run_scenario("target", tmp)
        mkt_posts = [b for m, b in posts if b["type"] == "market"]
        for b in posts:
            print("   POST /orders", json.dumps(b[1]))
        check(len(mkt_posts) == 1 and mkt_posts[0]["qty"] == QTY, f"market sell for the whole qty {QTY}")
        check(day["trades"] and day["trades"][0]["why"] == "target" and day["trades"][0]["r"] > 2, f"trade recorded: {day['trades']}")
        check("XLF" not in day["positions"], "position removed from the day file")

        print("== scenario: refuse (Alpaca refuses every new stop; fail-safe must sell the right qty)")
        r, day, fake, posts = run_scenario("refuse", tmp)
        stop_posts = [b for m, b in posts if b["type"] == "stop"]
        mkt_posts = [b for m, b in posts if b["type"] == "market"]
        for b in posts:
            print("   POST /orders", json.dumps(b[1]))
        check(len(stop_posts) == 2, "stop re-place retried once before giving up")
        check(len(mkt_posts) == 1 and mkt_posts[0]["qty"] == QTY, "fail-safe market sell carries the whole qty")
        check(day["trades"] and day["trades"][0]["why"] == "trail refused" and abs(day["trades"][0]["r"] - 1.59) < 0.02,
              f"trade recorded honestly with the real R: {day['trades']}")
        check("XLF" not in day["positions"], "position removed after the sell")

        print("== scenario: filled_in_race (the old stop fills while we cancel; nothing else may be sent)")
        r, day, fake, posts = run_scenario("filled_in_race", tmp)
        for b in posts:
            print("   POST /orders", json.dumps(b[1]))
        check(not posts, "no order posted at all")
        check(day["trades"] and day["trades"][0]["why"] == "stop filled" and day["trades"][0]["exit"] == 56.11, f"recorded as stop filled at the REAL fill 56.11: {day['trades']}")
        check("XLF" not in day["positions"], "position removed")

        print("== scenario: unknown_cancel (Alpaca never confirms the cancel in 8 s; nothing may be posted, retry next cycle)")
        r, day, fake, posts = run_scenario("unknown_cancel", tmp)
        for b in posts:
            print("   POST /orders", json.dumps(b[1]))
        check(not posts, "no order posted while the old stop is still live")
        check(any(a.get("do") == "cancel unconfirmed" for a in day["actions"]), "action 'cancel unconfirmed' recorded")
        check("XLF" in day["positions"], "position kept for the next cycle")
        check(not day["trades"], "no trade journaled")

        print("== scenario: partial (old stop filled 0.0765 sh at 56.12 before the cancel landed; re-place the remaining 0.1)")
        r, day, fake, posts = run_scenario("partial", tmp)
        stop_posts = [b for m, b in posts if b["type"] == "stop"]
        for b in posts:
            print("   POST /orders", json.dumps(b[1]))
        check(len(stop_posts) == 1 and stop_posts[0]["qty"] == "0.100000000", "new stop covers the remaining qty 0.1")
        partials = [t for t in day["trades"] if t["why"] == "stop filled (partial)"]
        check(len(partials) == 1 and partials[0]["exit"] == 56.12 and abs(partials[0]["qty"] - 0.076549913) < 1e-9, f"partial fill journaled at the real price: {partials}")
        check("XLF" in day["positions"] and day["positions"]["XLF"]["stop"] == 56.52, "remaining position kept with the raised stop")

        print("== scenario: transport (the position re-read raises after the cancel; fail-safe must still sell)")
        r, day, fake, posts = run_scenario("transport", tmp)
        mkt_posts = [b for m, b in posts if b["type"] == "market"]
        for b in posts:
            print("   POST /orders", json.dumps(b[1]))
        check(len(mkt_posts) == 1 and mkt_posts[0]["qty"] == QTY, "fail-safe market sell with the snapshot qty")
        check(any(a.get("do") == "trail refused" and a.get("status") == 599 for a in day["actions"]), "status 599 recorded for the transport error")
        check(day["trades"] and day["trades"][0]["why"] == "trail refused", f"trade journaled: {day['trades']}")
        check("XLF" not in day["positions"], "position removed after the sell")

    print()
    print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
