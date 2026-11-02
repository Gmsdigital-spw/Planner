from __future__ import annotations

import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .models import encoded, number

WEB = Path(__file__).parent.parent / "web"


def state(settings):
    """Read only. No broker reads, order writes, keys or full account identifiers."""
    path = Path(settings.database).resolve()
    base = {"mode": settings.mode, "synthetic": settings.mode == "demo", "connected": False,
            "equity_usd": None, "cash_usd": None, "exposure_usd": None,
            "day_pnl_usd": None, "initial_pnl_usd": None, "updated_at": None,
            "history": [], "orders": [], "lessons": [], "halt_reason": None,
            "research": None, "policy": {"capital_cap_usd": str(settings.capital_cap_usd),
            "protected_floor_usd": str(settings.protected_equity_floor_usd),
            "order_cap_usd": str(settings.max_order_usd), "daily_entry_halt_usd": str(settings.max_daily_loss_usd),
            "total_entry_halt_usd": str(settings.max_total_loss_usd)},
            "live_enabled": settings.live_enabled}
    if not path.exists():
        return base
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2) as db:
        db.row_factory = sqlite3.Row
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"metadata", "snapshots", "orders", "lessons"} <= tables:
            return base
        meta = {r["key"]: json.loads(r["value"]) for r in db.execute("SELECT * FROM metadata")}
        identity = meta.get("identity")
        if identity and identity["mode"] != settings.mode:
            base["halt_reason"] = "Configuration and stored environment do not match"
            return base
        history = [dict(r) for r in db.execute("SELECT at,equity_usd,cash_usd,exposure_usd,trading_day FROM snapshots ORDER BY id DESC LIMIT 120")][::-1]
        orders = [dict(r) for r in db.execute("SELECT proposal_id,side,notional_usd,status,created_at,proposal_json FROM orders ORDER BY created_at DESC LIMIT 30")]
        for order in orders:
            proposal = json.loads(order.pop("proposal_json"))
            order["symbol"] = proposal["symbol"]
            order["strategy_version"] = proposal["strategy_version"]
            order["target_move_pct"] = proposal.get("target_move_pct")
        base["orders"] = orders
        base["lessons"] = [dict(r) for r in db.execute("SELECT at,strategy_version,hypothesis,evidence_ref,status FROM lessons ORDER BY id DESC LIMIT 12")]
        base["halt_reason"] = meta.get("halt_reason")
        base["history"] = history
        if history:
            last = history[-1]
            base.update({"connected": True, "updated_at": last["at"], "equity_usd": last["equity_usd"], "cash_usd": last["cash_usd"], "exposure_usd": last["exposure_usd"]})
            day_reference = meta.get("day_reference:" + last["trading_day"])
            if day_reference is not None:
                base["day_pnl_usd"] = str(number(last["equity_usd"]) - number(day_reference))
            if meta.get("initial_equity") is not None:
                base["initial_pnl_usd"] = str(number(last["equity_usd"]) - number(meta["initial_equity"]))
    report = path.parent / "research-report.json"
    if report.exists():
        try:
            base["research"] = json.loads(report.read_text())
        except (ValueError, OSError):
            pass
    return base


def serve(settings, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Deny DNS rebinding and serve only the four fixed local resources.
            if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            try:
                if path == "/api/state":
                    body, content_type = encoded(state(settings)).encode(), "application/json"
                elif path in {"/", "/index.html", "/styles.css", "/app.js"}:
                    filename = "index.html" if path == "/" else path[1:]
                    body = (WEB / filename).read_bytes()
                    content_type = {"html": "text/html", "css": "text/css", "js": "text/javascript"}[filename.rsplit(".", 1)[1]]
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", content_type + "; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(body)
            except (sqlite3.Error, OSError, ValueError):
                self.send_error(503, "Local data unavailable")

        def log_message(self, *args):
            pass

    print(f"Read-only dashboard: http://127.0.0.1:{port} — {settings.mode.upper()}", flush=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
