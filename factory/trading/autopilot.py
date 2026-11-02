#!/usr/bin/env python3
"""Trading Floor autopilot: runs ALL DAY in the free GitHub Action "Trading autopilot".

V7 (Oct 21, 2026): `python autopilot.py --loop 330` keeps one runner alive for up to 5.5 hours and checks the
market EVERY MINUTE (GitHub's cron fires only every 30-40 minutes, so the old 5-minute schedule was never 5 minutes).
Each cycle = one run(); the loop writes factory/trading/auto/heartbeat.json every cycle and commits the day's
state to the repo when something happened (and at least every 5 minutes as a heartbeat). When the runner's time
is up the workflow hands off to a fresh runner, so the bot is on the floor from the opening bell to the close.
`python autopilot.py` (no flag) still does a single cycle, same as before.

Why: the Claude crew runs only a few times a day, so it misses setups and can't trail stops in between.
This script trades the SAME strategy the Trading lab backtests (backtest.setup_at + the same exits), all day:
  - manages open positions every run: breakeven at 1R, trailing stop from 1.5R, sell at the 2R target
  - looks for new long setups on completed 5-minute bars (watchlist from factory/trading/watchlist.json)
  - every order goes through the gateway's op_alpaca (gw/run.py), so the hard rules are enforced in code:
    $20 floor, stop on every buy, 40% cash cap, day orders only, buys 8:35 AM-2:45 PM CT, paper unless ALPACA_LIVE=1
  - Bear rules here too: $1.50 daily loss limit, max 2 positions, max 4 entries a day, no re-entry after a loss,
    flat by 2:45 PM CT, floor hit = flatten + lock for the day.
  - Oct 23, 2026 fix: a stop re-place (breakeven, trail) sends the WHOLE position qty and waits for the old stop's cancel
    to be confirmed. On Oct 22 both re-places used Alpaca's qty_available, which is "0" while the stop order holds the
    shares, so they were refused (422) and both winners were dumped at market without a stop.
V8 (Nov 2, 2026, Grayson's live go): the money rules come from a PROFILE, factory/trading/profiles/<name>.json.
  paper (repo variable ALPACA_LIVE empty) = the rules above, unchanged. live (ALPACA_LIVE set to 1, separate live key
  pair) = "live-aggressive": one all-in position, 3x ETF universe, opening-range-breakout entry, 3R target, $5 daily
  loss, $5 floor, 6 entries a day. Every entry carries a client_order_id and is looked up by it before the POST, so a
  cycle that died after Alpaca accepted a buy never buys twice. Live names are checked once a day against /assets
  (active, tradable, fractionable). The gateway enforces the same profile's floor, size cap, hours and account pin.
  Review fixes (Nov 2, 2026, before the first real dollar): a flatten is "flat" only once GET /positions comes back
  empty (Alpaca answers DELETE /positions 207 whether each leg worked or not), and the day locks only when flat, else
  the next cycle retries. The flat time is the earlier of the profile's flat_ct and 15 minutes before Alpaca's
  next_close (early-close days). The day file is per mode: flipping ALPACA_LIVE during the day archives the other
  mode's record as <day>-<mode>.json and starts fresh from THIS account. A live profile that is missing or broken
  stops the bot (real money never falls back to the paper rules or the crew's stock list). The buy lookup fails
  closed (an unknown answer = no POST this cycle). A gateway 207 (stop refused, sold at once) is journaled, never
  kept as a position. Stop fills carry Alpaca's filled_at and filled_avg_price; flatten exits are read back from
  the closed orders, never invented.
Pause it: set "paused": true in factory/trading/auto/control.json (or disable the workflow in GitHub).
Writes factory/trading/auto/<day>.json (state + every action) so the crew and the Factory can show it.
Not financial advice: this can lose money. It never adds money, changes the floor, or switches itself to live.
"""
import importlib.util, json, os, subprocess, sys, time, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import backtest  # noqa: E402  (same strategy code the lab tests)

spec = importlib.util.spec_from_file_location("gw_run", REPO / "gw" / "run.py")
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)

CT = ZoneInfo("America/Chicago")
AUTO = HERE / "auto"
DRY = os.environ.get("AUTOPILOT_DRY") == "1"
DEFAULT_WATCH = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF"]  # ETFs only when the crew hasn't written today's list
LAST = {}   # last account hint read this runner (for the heartbeat; never a secret)


def now_ct():
    return datetime.now(CT)


def profile_name():
    """The money profile for the mode the gateway is in: live-aggressive when ALPACA_LIVE is set, else paper."""
    return "live-aggressive" if gw.ALPACA_LIVE else "paper"


def floor_for(P):
    """The hard floor: the profile's, unless Grayson overrides it with the repo variable for THAT mode
    (ALPACA_LIVE_FLOOR for live, ALPACA_FLOOR for paper; the paper variable never reaches the live account).
    A value that is not a number ("$5") is ignored with a warning in the heartbeat: it must never stop a cycle,
    because the cycle is what manages an open position."""
    var = "ALPACA_LIVE_FLOOR" if gw.ALPACA_LIVE else "ALPACA_FLOOR"
    raw = (os.environ.get(var) or "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            LAST["floorWarning"] = f"{var}={raw!r} is not a number; the profile floor ${float(P['floor']):.2f} applies"
    return float(P["floor"])


def profile(strict=None):
    """The active profile's JSON. Live = strict: a file that is missing, broken or incomplete raises, so real money
    never runs on the paper rules or the crew's stock list by accident."""
    return backtest.load_profile(profile_name(), strict=gw.ALPACA_LIVE if strict is None else strict)


def rules_summary(P=None):
    """What the Factory page shows under 'Real money' / 'Paper money': the active profile and its money rules."""
    name = profile_name()
    P = P or backtest.load_params(name)
    prof = profile(strict=False)
    return {"profile": name, "mode": "live" if gw.ALPACA_LIVE else "paper", "floor": floor_for(P),
            "dailyLoss": P["daily_loss"], "maxPosPct": P["max_pos_pct"], "maxPositions": P["max_positions"],
            "maxEntries": P["max_entries"], "riskPct": P["risk_pct"], "targetR": P["target_r"],
            "setup": P.get("setup", "pullback"), "hours": f"{P['start_ct']}-{P['flat_ct']} CT",
            "universe": prof.get("universe"), "setBy": prof.get("set_by")}


def safe_rules():
    try:
        return rules_summary()
    except Exception:
        return None


def alpaca(o, st):
    """One op through the gateway (rules enforced there). Returns (status, data)."""
    if DRY and o.get("method", "GET").upper() in ("POST", "DELETE"):
        return 200, {"dry": True, "op": o}
    return gw.op_alpaca(o, st)


def load_json(p, default):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


def watchlist(day):
    w = load_json(HERE / "watchlist.json", {})
    avoid = set(s.upper() for s in w.get("avoid", [])) if w.get("day") == day else set()
    universe = [str(s).upper() for s in (profile().get("universe") or [])]
    if universe:   # a profile universe (live): Grayson's list; the crew's avoid list for today still applies
        syms = universe
    else:
        syms = [s.upper() for s in w.get("symbols", [])] if w.get("day") == day else []
        syms = syms or DEFAULT_WATCH
    return [s for s in dict.fromkeys(syms) if s not in avoid][:20], sorted(avoid)


def tradable(symbols, st, day):
    """Profile universes only: keep the names Alpaca reports as active, tradable AND fractionable (one /assets read
    per name per day, cached in the day file). A read error keeps the name: Alpaca's own order check then decides."""
    cache = day.setdefault("assets", {})
    keep = []
    for s in symbols:
        if s not in cache:
            try:
                code, a = alpaca({"op": "alpaca", "path": f"/assets/{s}"}, st)
                if code >= 300 or not isinstance(a, dict) or "tradable" not in a:
                    cache[s] = None
                else:
                    cache[s] = bool(a.get("tradable") and a.get("fractionable") and str(a.get("status", "active")) == "active")
            except Exception:
                cache[s] = None
        if cache[s] is not False:
            keep.append(s)
    return keep


def today_bars(symbols, st, now):
    """Completed 5-minute bars since today's open, {sym: [bar,...]} oldest first."""
    start = now.replace(hour=8, minute=30, second=0, microsecond=0).astimezone(timezone.utc)
    q = {"symbols": ",".join(symbols), "timeframe": "5Min", "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "limit": 10000, "feed": "iex", "adjustment": "raw"}
    code, js = alpaca({"op": "alpaca", "data": True, "path": "/stocks/bars?" + urllib.parse.urlencode(q)}, st)
    if code >= 300 or not isinstance(js, dict):
        raise RuntimeError(f"bars failed: {code} {str(js)[:200]}")
    out = {}
    cutoff = now.astimezone(timezone.utc)
    for s, bars in (js.get("bars") or {}).items():
        done = [b for b in bars
                if datetime.fromisoformat(b["t"].replace("Z", "+00:00")) + timedelta(minutes=5) <= cutoff]
        out[s] = sorted(done, key=lambda b: b["t"])
    return out


def last_price(sym, bars, st):
    code, js = alpaca({"op": "alpaca", "data": True, "path": f"/stocks/{sym}/trades/latest?feed=iex"}, st)
    try:
        return float(js["trade"]["p"])
    except Exception:
        b = bars.get(sym) or []
        return float(b[-1]["c"]) if b else None


def position_qty(p):
    """The whole position as Alpaca reports it ("qty"). Never "qty_available": while the protective stop order
    holds the shares it is "0" (a truthy string, so `qty_available or qty` kept it). Oct 22, 2026: both trail
    re-places went out with qty "0", were refused (422), and the fail-safe sell with qty "0" was refused too."""
    q = p.get("qty")
    return str(q) if q not in (None, "") else str(p.get("qty_available") or "0")


def cancel_order(order_id, st, wait=8.0):
    """Cancel one order and wait until Alpaca confirms it. Cancels are asynchronous: the shares an order holds are
    released only once its status is 'canceled', so a stop re-placed straight after the DELETE can be refused.
    Returns (outcome, order): outcome 'canceled' | 'filled' (it filled before the cancel landed) | 'unknown' (no
    confirmation in `wait` s); order = the last order JSON read back (filled_qty / filled_avg_price when it filled,
    in part or in full), or None."""
    if not order_id:
        return "unknown", None
    alpaca({"op": "alpaca", "method": "DELETE", "path": f"/orders/{order_id}"}, st)
    if DRY:
        return "canceled", None
    t0 = time.time()
    last = None
    while True:
        time.sleep(1.0)
        code, js = alpaca({"op": "alpaca", "path": f"/orders/{order_id}"}, st)
        last = js if isinstance(js, dict) else last
        status = js.get("status") if isinstance(js, dict) else None
        if status in ("canceled", "expired", "rejected", "replaced") or code == 404:
            return "canceled", last
        if status == "filled":
            return "filled", last
        if time.time() - t0 >= wait:
            return "unknown", last


def fill_of(order, default_px):
    """(filled_qty, filled_avg_price) of an order read back from Alpaca; the stop price stands in when Alpaca gave
    no fill price, so the journal never invents a number it did not read."""
    if not isinstance(order, dict):
        return 0.0, default_px
    try:
        q = float(order.get("filled_qty") or 0)
    except (TypeError, ValueError):
        q = 0.0
    try:
        px = float(order.get("filled_avg_price")) if order.get("filled_avg_price") else default_px
    except (TypeError, ValueError):
        px = default_px
    return q, px


def live_qty(sym, st, fallback):
    """Quantity that can be sold right now, read fresh from /positions/<sym> after a cancel.
    None = the position is gone (its stop filled first). Falls back to the cycle's snapshot qty on any read error."""
    if DRY:
        return fallback
    code, p = alpaca({"op": "alpaca", "path": f"/positions/{sym}"}, st)
    if code == 404:
        return None
    if not isinstance(p, dict) or not p.get("qty"):
        return fallback
    try:
        qty, avail = float(p["qty"]), float(p.get("qty_available") or 0)
    except (TypeError, ValueError):
        return fallback
    return str(p["qty"]) if avail <= 0 or avail >= qty else str(p["qty_available"])


def cancel_and_sell(sym, qty, stop_id, st, why, day, stop_px=None):
    """Cancel the stop (and wait for it), then sell the whole position at market. Returns a dict:
    code (HTTP status of the sell, 200 when nothing had to be sent), qty (what was sold; None when the position was
    already gone because the stop filled first), fill (price the old stop filled at, when it did, else stop_px),
    partial (qty the old stop filled before the cancel landed, 0.0 when none)."""
    fill_px, partial, filled_at = stop_px, 0.0, None
    if stop_id:
        outcome, order = cancel_order(stop_id, st)
        pq, fill_px = fill_of(order, stop_px)
        filled_at = order.get("filled_at") if isinstance(order, dict) else None
        if outcome == "filled":
            return {"code": 200, "qty": None, "fill": fill_px, "partial": 0.0, "filledAt": filled_at}
        partial = pq
        qty = live_qty(sym, st, qty)
        if qty is None:
            return {"code": 200, "qty": None, "fill": fill_px, "partial": 0.0, "filledAt": filled_at}
    code, js = alpaca({"op": "alpaca", "method": "POST", "path": "/orders", "body": {
        "symbol": sym, "qty": str(qty), "side": "sell", "type": "market", "time_in_force": "day"}}, st)
    day["actions"].append({"t": now_ct().strftime("%H:%M"), "do": "sell", "sym": sym, "qty": qty, "why": why,
                           "status": code, "id": (js or {}).get("id") if isinstance(js, dict) else None})
    return {"code": code, "qty": qty, "fill": fill_px, "partial": partial, "filledAt": filled_at}


def journal_exit(day, sym, rec, exit_px, why, R, qty=None, at=None):
    """One trades[] line with the real exit price and R (None when no price could be read: never invented), the
    cycle time "t" and Alpaca's fill time "exitAt" when known; a losing exit marks the name as lost for today."""
    r = round((exit_px - rec["entry"]) / R, 2) if (exit_px is not None and R) else None
    t = {"sym": sym, "entry": rec["entry"], "exit": exit_px, "r": r, "why": why, "t": now_ct().strftime("%H:%M")}
    if qty is not None:
        t["qty"] = qty
    if at:
        t["exitAt"] = at
    day["trades"].append(t)
    if exit_px is not None and exit_px < rec["entry"] and sym not in day["lostToday"]:
        day["lostToday"].append(sym)


def closed_sells(st, limit=50):
    """{symbol: its latest FILLED sell order} from GET /orders?status=closed, for exits the bot did not watch fill
    (a flatten, a stop that filled between cycles, a close by hand). {} on any read error: the journal then says
    "fill not read" instead of inventing a price."""
    try:
        code, orders = alpaca({"op": "alpaca", "path": f"/orders?status=closed&limit={limit}&direction=desc"}, st)
    except Exception:
        return {}
    out = {}
    if code >= 300 or not isinstance(orders, list):
        return out
    for o in orders:
        if isinstance(o, dict) and o.get("side") == "sell" and o.get("status") == "filled" and o.get("symbol") not in out:
            out[o["symbol"]] = o
    return out


def journal_closed(day, sym, rec, sells, why):
    """A position closed by a flatten (or by hand): the exit is Alpaca's filled sell when it can be read, else the
    row says so (exit None; the Atlas importer skips it) rather than carrying a made-up number."""
    R = (rec["entry"] - rec["stop0"]) if rec.get("stop0") is not None else None
    o = sells.get(sym)
    if o and o.get("filled_avg_price"):
        q, px = fill_of(o, None)
        journal_exit(day, sym, rec, px, why, R, qty=(q or rec.get("qty")), at=o.get("filled_at"))
    else:
        journal_exit(day, sym, rec, None, f"{why} (fill not read)", R, qty=rec.get("qty"))


def flatten(st, day, why):
    """Cancel every open order and close every position, then CHECK before believing it. Alpaca answers
    DELETE /positions with 207 whether each leg worked or not (a leg is refused, for one, while a stop still holds
    the shares), so the day file says "flat" only once a fresh GET /positions comes back empty. Returns True when
    flat. Not flat = the names still held stay in day["positions"] and the caller leaves the day open, so the next
    cycle tries again: a real-money position is never written off as closed on a status code."""
    hm = now_ct().strftime("%H:%M")
    alpaca({"op": "alpaca", "method": "DELETE", "path": "/orders"}, st)
    time.sleep(1.5)
    act = {"t": hm, "do": "flatten", "why": why}
    still = None
    for attempt in range(2):
        if attempt:
            time.sleep(3.0)
        code, body = alpaca({"op": "alpaca", "method": "DELETE", "path": "/positions?cancel_orders=true"}, st)
        act["status"] = code
        legs = [x for x in body if isinstance(x, dict)] if isinstance(body, list) else []
        failed = [f"{x.get('symbol')}:{x.get('status')}" for x in legs if str(x.get("status") or "").isdigit() and int(x["status"]) >= 300]
        if failed:
            act["failed"] = failed[:10]
        if DRY:
            still = []
            break
        time.sleep(2.0)
        c2, pos = alpaca({"op": "alpaca", "path": "/positions"}, st)
        if c2 < 300 and isinstance(pos, list):
            still = sorted(str(p.get("symbol")) for p in pos if isinstance(p, dict) and p.get("symbol"))
            if not still:
                break
        else:
            still = None
            act["check"] = f"positions read failed ({c2})"
    flat = still == []
    act["flat"] = flat
    if still:
        act["still"] = still
    day["actions"].append(act)
    if not flat:
        day["flattenFailed"] = {"t": hm, "why": why, "still": still}
        if still is not None:   # the names that did close are journaled; the rest stay open on the record
            closed = [s for s in list(day["positions"]) if s not in still]
            sells = closed_sells(st) if closed else {}
            for sym in closed:
                journal_closed(day, sym, day["positions"].pop(sym), sells, f"flat: {why}")
        return False
    day.pop("flattenFailed", None)
    sells = closed_sells(st) if day["positions"] else {}
    for sym in list(day["positions"]):
        journal_closed(day, sym, day["positions"].pop(sym), sells, f"flat: {why}")
    return True


def flat_time(now, P, clock):
    """When today's flatten happens: the profile's flat_ct, or 15 minutes before Alpaca's next_close when that is
    earlier (early-close days: the day after Thanksgiving, Christmas Eve). Returns (datetime, "HH:MM")."""
    h, mi = (int(x) for x in str(P["flat_ct"]).split(":"))
    flat_at = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    nc = clock.get("next_close") if isinstance(clock, dict) else None
    if nc:
        try:
            close_at = datetime.fromisoformat(str(nc).replace("Z", "+00:00")).astimezone(CT)
            if close_at.date() == now.date() and close_at - timedelta(minutes=15) < flat_at:
                flat_at = (close_at - timedelta(minutes=15)).replace(second=0, microsecond=0)
        except ValueError:
            pass
    return flat_at, flat_at.strftime("%H:%M")


def new_day(key, mode):
    return {"day": key, "mode": mode, "profile": profile_name(), "equityOpen": None, "entries": 0, "lostToday": [],
            "positions": {}, "trades": [], "actions": [], "done": None, "runs": 0, "lastSignal": {}}


def switch_mode(old, key, mode):
    """ALPACA_LIVE changed during the day: the other mode's record is kept as <day>-<mode>.json (never mixed into
    this account's equityOpen, entries, positions or lostToday) and this mode starts a fresh day file. Positions the
    other mode still had open are nobody's now: say so loudly."""
    old_mode = str(old.get("mode") or "paper")
    n, arch = 1, AUTO / f"{key}-{old_mode}.json"
    while arch.exists():
        n += 1
        arch = AUTO / f"{key}-{old_mode}{n}.json"
    arch.write_text(json.dumps(old, indent=1))
    day = new_day(key, mode)
    note = f"switched from {old_mode} to {mode}; the {old_mode} record is {arch.name}"
    if old.get("positions"):
        note += f"; {old_mode} still held {', '.join(sorted(old['positions']))}: NOBODY manages them now, close them in the Alpaca app"
    day["actions"].append({"t": now_ct().strftime("%H:%M"), "do": "mode switch", "why": note})
    day["switchedFrom"] = {"mode": old_mode, "file": arch.name, "positions": sorted(old.get("positions") or [])}
    return day


def run():
    now = now_ct()
    key = now.strftime("%Y-%m-%d")
    AUTO.mkdir(parents=True, exist_ok=True)
    mode = "live" if gw.ALPACA_LIVE else "paper"
    path = AUTO / f"{key}.json"
    day = load_json(path, None)
    if isinstance(day, dict) and str(day.get("mode") or "paper") != mode:
        day = switch_mode(day, key, mode)   # the other mode's record is archived; this account starts fresh
    if not isinstance(day, dict):
        day = new_day(key, mode)
    day["mode"] = mode
    day["runs"] += 1
    day["lastRun"] = now.strftime("%H:%M")
    hm = now.strftime("%H:%M")

    n_actions = len(day["actions"])

    def save(note=None, status="ok"):
        """Write the day file; returns the cycle status the loop reads: ok | paused | closed | waiting | done."""
        if note:
            day["lastNote"] = note
        day["actions"] = day["actions"][-300:]
        path.write_text(json.dumps(day, indent=1))
        print(f"{key} {now:%H:%M} CT: {day.get('lastNote', '')}")
        return {"status": status, "note": day.get("lastNote", ""), "acted": len(day["actions"]) > n_actions, "day": key}

    if load_json(AUTO / "control.json", {}).get("paused"):
        return save("paused (control.json)", "paused")
    if now.weekday() > 4 or (now.hour, now.minute) > (15, 0):
        return save("outside market hours", "closed")
    if (now.hour, now.minute) < (8, 30):
        return save("waiting for the open (8:30 CT)", "waiting")
    if day.get("done"):
        return save(f"done for today: {day['done']}", "done")

    try:
        st = gw.load_state() if gw.SKEY else {}
    except Exception:
        st = {}
    code, clock = alpaca({"op": "alpaca", "path": "/clock"}, st)
    clock = clock if isinstance(clock, dict) else {}
    if not clock.get("is_open"):
        if day["positions"] and (now.hour, now.minute) >= (9, 0):
            # carried past the close (an early close before the flat time, or no runner alive at the end): nothing
            # can fill now and the day stop has expired; the next open's first cycle sells it at market
            names = sorted(day["positions"])
            if day.get("heldAfterClose") != names:
                day["heldAfterClose"] = names
                day["actions"].append({"t": hm, "do": "held after close", "sym": ",".join(names),
                                       "why": "market closed before the flatten; sold at the next open"})
            return save(f"market closed with {', '.join(names)} still held: sold at the next open", "closed")
        # a weekday with the market shut (holiday) or the open not reached yet: wait, don't quit
        return save("market closed", "waiting" if (now.hour, now.minute) < (9, 0) else "closed")

    # live = strict: a missing or broken live profile raises here, before any order (never the paper rules by accident)
    P = backtest.load_params(profile_name(), strict=gw.ALPACA_LIVE)
    prof = profile()
    if gw.ALPACA_LIVE and not prof.get("universe"):
        raise RuntimeError(f"live profile {profile_name()} has no universe: no trading")
    floor = floor_for(P)
    day["profile"] = profile_name()
    flat_at, flat_hm = flat_time(now, P, clock)
    day["flatAt"] = LAST["flatAt"] = flat_hm
    _, acct = alpaca({"op": "alpaca", "path": "/bankroll"}, st)
    equity, cash = float(acct["equity"]), float(acct["cash"])
    LAST["accountId"] = acct.get("accountId") if isinstance(acct, dict) else None
    if LAST["accountId"]:
        day["accountId"] = LAST["accountId"]   # last 4 characters only, so the page can confirm which account trades
    if day["equityOpen"] is None:
        day["equityOpen"] = equity
    day["equity"] = equity
    day["dayPnl"] = round(equity - day["equityOpen"], 2)

    # ---- Bear's hard stops (the day locks only once the flatten is CONFIRMED; otherwise the next cycle retries) ----
    if equity <= floor:
        if gw.ALPACA_LIVE and equity < 1.0:   # an unfunded live account: nothing to flatten or lock; check again next cycle
            return save(f"under the ${floor:.2f} floor at ${equity:.2f}: no trading until the account is funded above it", "waiting")
        day["floorLocked"] = True; day["locked"] = "floor"
        if flatten(st, day, f"floor hit at ${equity:.2f}"):
            day["done"] = "floor"
            return save(f"FLOOR HIT ${equity:.2f}: flattened and locked", "done")
        return save(f"FLOOR HIT ${equity:.2f}: flatten NOT confirmed ({day['flattenFailed'].get('still')}); retrying next cycle")
    if day["dayPnl"] <= -P["daily_loss"]:
        day["locked"] = "daily loss limit"
        if flatten(st, day, "daily loss limit"):
            day["done"] = "daily loss limit"
            return save(f"daily loss limit hit ({day['dayPnl']}); flat for the day", "done")
        return save(f"daily loss limit hit ({day['dayPnl']}): flatten NOT confirmed ({day['flattenFailed'].get('still')}); retrying next cycle")
    if now >= flat_at:
        day["locked"] = "flat time"
        if flatten(st, day, f"{flat_hm} flat"):
            day["done"] = "closed for the day"
            return save(f"flat for the day, P/L {day['dayPnl']}", "done")
        return save(f"flat time {flat_hm}: flatten NOT confirmed ({day['flattenFailed'].get('still')}); retrying next cycle")

    _, positions = alpaca({"op": "alpaca", "path": "/positions"}, st)
    _, orders = alpaca({"op": "alpaca", "path": "/orders?status=open"}, st)
    positions = positions if isinstance(positions, list) else []
    orders = orders if isinstance(orders, list) else []
    held = {p["symbol"]: p for p in positions}
    stops = {o["symbol"]: o for o in orders if o.get("side") == "sell" and o.get("type") == "stop"}

    # positions that disappeared since last run = closed by their stop (or by hand): read the real fill back
    gone = [sym for sym in list(day["positions"]) if sym not in held]
    sells = closed_sells(st) if gone else {}
    for sym in gone:
        rec = day["positions"].pop(sym)
        R = rec["entry"] - rec["stop0"]
        o = None
        if rec.get("stopId"):
            c3, o = alpaca({"op": "alpaca", "path": f"/orders/{rec['stopId']}"}, st)
            o = o if (c3 < 300 and isinstance(o, dict)) else None
        if o and o.get("status") == "filled":
            q, px = fill_of(o, rec.get("stop"))
            journal_exit(day, sym, rec, px, "stop filled", R, qty=(q or rec.get("qty")), at=o.get("filled_at"))
        elif sym in sells:   # closed some other way (by hand, by the crew): the last filled sell is the exit
            journal_closed(day, sym, rec, sells, "closed outside the bot")
        elif o is None and rec.get("stopId") is None:
            journal_closed(day, sym, rec, sells, "closed outside the bot")
        else:   # the stop is gone and no fill could be read: the stop price stands in, marked as such
            journal_exit(day, sym, rec, rec.get("stop"), "stop filled (fill not read; stop price assumed)", R, qty=rec.get("qty"))

    watch, avoid = watchlist(key)
    if prof.get("universe"):   # live: only names Alpaca will fill fractionally
        watch = tradable(watch, st, day)
    bars = today_bars(sorted(set(watch) | set(held)), st, now)

    # ---- manage open positions (same exits as the backtest) ----
    for sym, p in held.items():
        qty = position_qty(p)
        rec = day["positions"].get(sym)
        so = stops.get(sym)
        if not rec:   # opened outside the autopilot: adopt it using its stop
            entry = float(p["avg_entry_price"])
            s0 = float(so["stop_price"]) if so else entry * (1 - P["min_stop_pct"] / 100)
            rec = day["positions"][sym] = {"entry": entry, "stop0": s0, "stop": s0, "high": entry,
                                           "target": entry + P["target_r"] * (entry - s0), "adopted": True}
        if so:
            rec["stopId"] = so["id"]
        px = last_price(sym, bars, st)
        if px is None:
            continue
        for b in bars.get(sym, []):
            if b["t"] >= rec.get("since", ""):
                rec["high"] = max(rec["high"], b["h"])
        rec["high"] = max(rec["high"], px)
        R = rec["entry"] - rec["stop0"]
        if px >= rec["target"]:
            r = cancel_and_sell(sym, qty, rec.get("stopId"), st, f"target {rec['target']:.2f} hit", day,
                                stop_px=float(so["stop_price"]) if so else rec["stop"])
            if r["partial"] > 0:   # part of the position left at the old stop before the cancel landed
                journal_exit(day, sym, rec, r["fill"], "stop filled (partial)", R, qty=r["partial"], at=r.get("filledAt"))
            if r["qty"] is None:   # the stop filled while we were canceling it
                journal_exit(day, sym, rec, r["fill"], "stop filled", R, qty=rec.get("qty"), at=r.get("filledAt"))
            elif r["code"] < 300:
                journal_exit(day, sym, rec, px, "target", R, qty=r["qty"])
            else:   # sell refused; the stop is gone, so the next cycle's "no stop found" exit takes over
                rec["stopId"] = None
                continue
            day["positions"].pop(sym, None)
            continue
        if not so:   # never hold without a stop
            r = cancel_and_sell(sym, qty, None, st, "no stop found", day)
            if r["code"] >= 300:   # refused: keep the record and try again next cycle
                continue
            journal_exit(day, sym, rec, px, "no stop", R, qty=r["qty"])
            day["positions"].pop(sym, None)
            continue
        gain_r = (rec["high"] - rec["entry"]) / R if R > 0 else 0
        new_stop = rec["stop"]
        if gain_r >= P["trail_at_r"]:
            new_stop = max(new_stop, rec["high"] - P["trail_r"] * R)
        elif gain_r >= P["be_at_r"]:
            new_stop = max(new_stop, rec["entry"])
        new_stop = round(min(new_stop, px * 0.999), 2)
        if new_stop > float(so["stop_price"]) + 0.01:
            # cancel the old stop, WAIT for Alpaca to confirm it, then re-place it for the whole position
            outcome, old = cancel_order(so["id"], st)
            if outcome == "unknown":   # no confirmation in 8 s: the old stop is still live, so re-read next cycle
                day["actions"].append({"t": hm, "do": "cancel unconfirmed", "sym": sym, "id": so["id"]})
                continue
            part_qty, fill_px = fill_of(old, float(so["stop_price"]))
            old_at = old.get("filled_at") if isinstance(old, dict) else None
            if outcome == "filled":   # the old stop filled while we were canceling it
                journal_exit(day, sym, rec, fill_px, "stop filled", R, qty=(part_qty or rec.get("qty")), at=old_at)
                day["positions"].pop(sym, None)
                continue
            if part_qty > 0:   # part of the position left at the old stop before the cancel landed
                journal_exit(day, sym, rec, fill_px, "stop filled (partial)", R, qty=part_qty, at=old_at)
            sell_qty, c, js = qty, 0, None
            try:
                sell_qty = live_qty(sym, st, qty)
                if sell_qty is None:   # position gone after all
                    journal_exit(day, sym, rec, fill_px, "stop filled", R, qty=rec.get("qty"), at=old_at)
                    day["positions"].pop(sym, None)
                    continue
                for attempt in range(2):   # one retry: a cancel can take a moment to release the shares
                    if attempt:
                        time.sleep(2)
                    c, js = alpaca({"op": "alpaca", "method": "POST", "path": "/orders", "body": {
                        "symbol": sym, "qty": sell_qty, "side": "sell", "type": "stop",
                        "stop_price": f"{new_stop:.2f}", "time_in_force": "day"}}, st)
                    if c < 300:
                        break
            except Exception as e:   # a transport error here must still end with a stop or a sell, never a bare hold
                c, js = 599, scrub(f"{type(e).__name__}: {e}")
                sell_qty = sell_qty or qty
            if c >= 300:   # could not re-protect: get out (never hold without a stop)
                day["actions"].append({"t": hm, "do": "trail refused", "sym": sym, "qty": sell_qty, "stop": new_stop,
                                       "status": c, "result": str(js)[:200]})
                r = cancel_and_sell(sym, sell_qty, None, st, "trail stop refused", day)
                if r["code"] >= 300:   # even the sell was refused: the next cycle's "no stop found" exit takes over
                    rec["stopId"] = None
                    continue
                journal_exit(day, sym, rec, px, "trail refused", R, qty=r["qty"])
                day["positions"].pop(sym, None)
                continue
            rec["stop"], rec["qty"] = new_stop, sell_qty
            rec["stopId"] = js.get("id") if isinstance(js, dict) else None
            day["actions"].append({"t": hm, "do": "raise stop", "sym": sym, "stop": new_stop, "qty": sell_qty,
                                   "gainR": round(gain_r, 2)})

    # ---- new entries (Bull's setup, Bear's limits) ----
    open_n = len(day["positions"])
    # no entry after the profile's last entry time, within 30 minutes of today's flat time (early closes), or once
    # a floor / daily-loss / flat-time lock is on (even when its flatten is still being retried)
    can_enter = P["start_ct"] <= hm <= P["last_entry_ct"] and now < flat_at - timedelta(minutes=30) and not day.get("locked")
    scanned = 0
    # the entry rule the profile/lab names ("pullback" default, "orb", "pullback_orh"), exactly as backtest.simulate
    setup_fn = backtest.SETUPS.get(P.get("setup", "pullback"), backtest.setup_at)
    for sym in watch:
        if not can_enter or open_n >= P["max_positions"] or day["entries"] >= P["max_entries"]:
            break
        if sym in held or sym in day["positions"] or sym in day["lostToday"]:
            continue
        b = bars.get(sym) or []
        if not b:
            continue
        scanned += 1
        if day["lastSignal"].get(sym) == b[-1]["t"]:
            continue
        s = setup_fn(b, len(b) - 1, P)
        if not s:
            continue
        day["lastSignal"][sym] = b[-1]["t"]
        _, stop = s
        px = last_price(sym, bars, st) or b[-1]["c"]
        if px <= stop * 1.001:
            continue
        stop = round(stop, 2)
        target = round(px + P["target_r"] * (px - stop), 2)
        risk = equity * P["risk_pct"] / 100
        notional = min(risk / ((px - stop) / px), cash * P["max_pos_pct"] / 100 - 0.02, cash)
        if notional < 1.0:
            day["actions"].append({"t": hm, "do": "skip", "sym": sym, "why": f"size ${notional:.2f} under $1"})
            continue
        # One durable id per (day, name, signal bar). If an earlier cycle died after Alpaca accepted this buy, the
        # lookup finds it and nothing is sent twice (read before you retry; never a blind second POST).
        coid = f"gm-{key}-{sym}-{str(b[-1]['t'])[11:16].replace(':', '')}"[:48]
        c0, prior = alpaca({"op": "alpaca", "path": "/orders:by_client_order_id?" +
                            urllib.parse.urlencode({"client_order_id": coid})}, st)
        if c0 < 300 and isinstance(prior, dict) and prior.get("id") and prior.get("status") not in ("canceled", "expired", "rejected"):
            day["actions"].append({"t": hm, "do": "skip", "sym": sym, "why": f"order {coid} already at Alpaca ({prior.get('status')})",
                                   "id": prior.get("id")})
            continue
        if not (c0 == 404 or (c0 < 300 and isinstance(prior, dict))):
            # the lookup did not answer (5xx, 429, junk): fail CLOSED, no blind POST; the same bar is tried again next minute
            day["actions"].append({"t": hm, "do": "skip", "sym": sym, "why": f"lookup of {coid} failed ({c0}); no order sent, retry next cycle"})
            day["lastSignal"].pop(sym, None)
            continue
        c, js = alpaca({"op": "alpaca", "method": "POST", "path": "/orders", "tag": f"buy-{sym}", "body": {
            "symbol": sym, "notional": f"{notional:.2f}", "side": "buy", "type": "market", "time_in_force": "day",
            "client_order_id": coid, "protect": {"stop_price": f"{stop:.2f}", "take_profit": f"{target:.2f}"}}}, st)
        act = {"t": hm, "do": "buy", "sym": sym, "notional": round(notional, 2), "stop": stop, "target": target,
               "status": c, "coid": coid}
        entry = (js or {}).get("entry") if isinstance(js, dict) else None
        stop_o = (js or {}).get("stop") if isinstance(js, dict) else None
        if c == 200 and isinstance(entry, dict) and entry.get("status") == "filled" and isinstance(stop_o, dict) and stop_o.get("id"):
            fill = float(entry["filled_avg_price"])
            target = round(fill + P["target_r"] * (fill - stop), 2)
            day["positions"][sym] = {"entry": fill, "stop0": stop, "stop": stop, "target": target, "high": fill,
                                     "stopId": stop_o.get("id"), "since": b[-1]["t"], "qty": entry.get("filled_qty")}
            day["entries"] += 1; open_n += 1
            act.update({"fill": fill, "target": target})
        elif c == 207 and isinstance(entry, dict) and entry.get("status") == "filled":
            # the gateway could not place the stop and sold the fill at once: an entry, never a position. The sell's
            # fill is read back next cycle (closed_sells); if the sell itself was refused, the next cycle adopts the
            # unprotected position and sells it ("no stop found").
            fx = js.get("flattened") if isinstance(js.get("flattened"), dict) else {}
            fill = float(entry.get("filled_avg_price") or px)
            day["entries"] += 1
            if sym not in day["lostToday"]:
                day["lostToday"].append(sym)   # no second try in a name whose stop Alpaca refused today
            act.update({"fill": fill, "stopRefused": str(stop_o)[:160], "sold": fx.get("status"), "sellId": fx.get("id")})
            day["trades"].append({"sym": sym, "entry": fill, "exit": None, "r": None, "t": hm,
                                  "why": "stop refused, sold at once" + ("" if fx.get("id") else " (sell NOT confirmed)"),
                                  "qty": entry.get("filled_qty")})
        elif DRY:
            act["dry"] = True
        else:
            act["result"] = str(js)[:300]
        day["actions"].append(act)
        cash = max(0.0, cash - notional)

    note = f"equity ${equity:.2f}, day {day['dayPnl']:+.2f}, {len(day['positions'])} open, {day['entries']} entries"
    if can_enter and not day["positions"] and scanned:
        note += f"; scanned {scanned} names, no A+ setup"
    elif not can_enter:
        note += "; no new entries now (8:35-2:00 CT window)"
    day["watch"], day["avoid"] = watch, avoid
    return save(note)


# ---------------------------------------------------------------------------------------------
# V7: always-on loop. One runner, one cycle a minute, heartbeat + state pushed to the repo.
# ---------------------------------------------------------------------------------------------
HEART = AUTO / "heartbeat.json"
KICK = AUTO.parent / "kick"


def scrub(msg):
    for sec in (gw.AKEY, gw.ASEC):
        if sec and len(sec) > 6:
            msg = msg.replace(sec, "[hidden]")
    return msg


def record_error(e):
    msg = scrub(f"{type(e).__name__}: {e}")
    print("autopilot error:", msg[:500])
    AUTO.mkdir(parents=True, exist_ok=True)
    (AUTO / "last-error.json").write_text(json.dumps({"at": now_ct().isoformat(), "error": msg[:500]}))
    return msg


def heartbeat(status, note, cycles, started, until):
    """factory/trading/auto/heartbeat.json: what the Factory page reads for 'Bot last checked'."""
    now = now_ct()
    AUTO.mkdir(parents=True, exist_ok=True)
    HEART.write_text(json.dumps({
        "at": now.isoformat(), "lastRun": now.strftime("%H:%M"), "day": now.strftime("%Y-%m-%d"),
        "status": status, "note": str(note)[:160], "loop": True, "cycles": cycles,
        "runnerStarted": started.isoformat(), "runnerUntil": until.isoformat(),
        "cadence": "every minute during market hours", "mode": "live" if gw.ALPACA_LIVE else "paper",
        "profile": profile_name(), "rules": safe_rules(), "accountId": LAST.get("accountId"),
        "flatAt": LAST.get("flatAt"), "floorWarning": LAST.get("floorWarning")}, indent=1))


def git(*args, check=False):
    r = subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError((r.stderr or r.stdout)[-300:])
    return r


def git_save(msg):
    """Commit the trading state and push it: pull --rebase first, up to 3 tries. Never raises; a failed push
    is retried on the next cycle because the files stay on disk."""
    if os.environ.get("AUTOPILOT_NO_GIT") == "1" or not (REPO / ".git").exists():
        return False
    try:
        git("config", "user.name", "trading-autopilot")
        git("config", "user.email", "trading-autopilot@users.noreply.github.com")
        git("add", "factory/trading/auto", "gw/state")
        # prune kick files older than 2 days so the folder never grows
        if KICK.exists():
            keep = {(now_ct() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)}
            for f in KICK.glob("*.txt"):
                if f.name[:10] not in keep:
                    git("rm", "-q", "--cached", str(f.relative_to(REPO)))
                    f.unlink(missing_ok=True)
        if git("diff", "--cached", "--quiet").returncode == 0:
            return True
        git("commit", "-qm", msg, check=True)
        for i in range(1, 4):
            if git("pull", "-q", "--rebase", "origin", "main").returncode == 0 and \
               git("push", "-q", "origin", "HEAD:main").returncode == 0:
                return True
            git("rebase", "--abort")
            time.sleep(i * 5)
        print("git_save: push failed 3 times; will retry next cycle")
    except Exception as e:
        print("git_save:", scrub(str(e))[:200])
    return False


def loop(max_minutes):
    """Run cycles every minute until the market closes, the day is done, the bot is paused, or the runner's
    time is up (then the workflow hands off to a fresh runner). Returns the final status."""
    started = now_ct()
    until = started + timedelta(minutes=max_minutes)
    last_push = 0.0
    cycles = 0
    status = "ok"
    while now_ct() < until:
        t0 = time.time()
        cycles += 1
        try:
            r = run() or {"status": "ok", "note": "", "acted": False}
        except Exception as e:
            r = {"status": "error", "note": record_error(e), "acted": True}
        status = r["status"]
        heartbeat(status, r.get("note", ""), cycles, started, until)
        if status in ("paused", "closed", "done"):
            git_save(f"trading autopilot: {status} {now_ct():%H:%M} CT")
            print(f"loop: {status}; runner stops")
            return status
        if r.get("acted") or time.time() - last_push > 300:
            if git_save(f"trading autopilot: {now_ct():%H:%M} CT"):
                last_push = time.time()
        # waiting for the open: check twice a minute, otherwise one cycle a minute
        pause = 30 if status == "waiting" else 60
        time.sleep(max(3.0, pause - (time.time() - t0)))
    git_save(f"trading autopilot: handoff {now_ct():%H:%M} CT")
    print("loop: runner time is up; handing off")
    return "handoff"


if __name__ == "__main__":
    if "--loop" in sys.argv:
        try:
            mins = int(sys.argv[sys.argv.index("--loop") + 1])
        except (IndexError, ValueError):
            mins = 330
        final = loop(mins)
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a") as f:
                f.write(f"status={final}\n")
    else:
        try:
            r = run()
            heartbeat(r["status"], r.get("note", ""), 1, now_ct(), now_ct())
        except Exception as e:
            record_error(e)
