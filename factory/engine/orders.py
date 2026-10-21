"""Orders from the phone (add-on Phase 8).

The Factory page has no git credentials (and never will), so a tap on Approve / Retry / Kill cannot change the
engine directly. Instead a tap becomes an *order*: a small JSON file in `factory/engine/orders/` that a crew
run commits, or a doc the crew copies there from the artifact DB. The worker applies every order it finds,
records the outcome in the audit log and in `orders/done/`, and the next report shows what happened.

Order file: {"action": "approve|decline|retry|cancel|kill_on|kill_off|pause|resume", "id": "<approval/task/agent id>",
             "by": "grayson", "at": "<iso>", "note": "..."}  — one order per file; the file name is the order id.
Unknown actions and unknown ids are refused, never guessed. Nothing here spends money or publishes by itself:
an approval only lets an already-gated task continue through the same checks as before.
"""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import AuditEvent, now_iso, scrub
from .engine import EngineError, TaskEngine

HERE = Path(__file__).resolve().parent
ORDERS = HERE / "orders"
ACTIONS = ("approve", "decline", "retry", "cancel", "kill_on", "kill_off", "pause", "resume")


def apply_order(eng: TaskEngine, order: dict) -> dict:
    """Apply one order. Returns {ok, action, id, result|error}."""
    action = str(order.get("action") or "")
    oid = str(order.get("id") or "")
    who = str(order.get("by") or "grayson")
    out = {"action": action, "id": oid, "by": who, "at": now_iso(), "ok": False}
    if action not in ACTIONS:
        out["error"] = f"unknown action {action!r}; allowed: {', '.join(ACTIONS)}"
        return out
    try:
        if action in ("approve", "decline"):
            a = eng.decide(oid, action == "approve", who=who)
            out["result"] = f"approval {a.id} {a.status.value}"
        elif action == "retry":
            tk = eng.retry(oid, who=who)
            out["result"] = f"task {tk.id} back in the queue"
        elif action == "cancel":
            tk = eng.cancel(oid, who=who, why=str(order.get("note") or "cancelled from the phone"))
            out["result"] = f"task {tk.id} cancelled"
        elif action in ("kill_on", "kill_off"):
            eng.kill(action == "kill_on", who=who)
            out["result"] = "kill switch " + ("ON: no new actions" if eng.killed() else "off")
        elif action in ("pause", "resume"):
            if oid not in eng.agents:
                raise EngineError(f"unknown agent {oid!r}")
            eng.pause_agent(oid, action == "pause", who=who)
            out["result"] = f"agent {oid} {'paused' if action == 'pause' else 'resumed'}"
        out["ok"] = True
    except EngineError as e:
        out["error"] = scrub(str(e))
    except Exception as e:  # never let one bad order stop the worker
        out["error"] = scrub(f"{type(e).__name__}: {e}")
    eng.store.audit(AuditEvent.make(who, "order_" + ("applied" if out["ok"] else "refused"), oid or action, out.get("result") or out.get("error") or ""))
    return out


def apply_orders(eng: TaskEngine, folder: Path | str = ORDERS) -> list[dict]:
    """Apply every *.json order in `folder` (oldest first) and move each to folder/done/ with its outcome."""
    folder = Path(folder)
    done = folder / "done"
    results = []
    if not folder.exists():
        return results
    for p in sorted(folder.glob("*.json")):
        try:
            order = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(order, dict):
                raise ValueError("order must be a JSON object")
        except Exception as e:
            order = {"action": "", "id": p.stem, "by": "unknown"}
            res = {"action": "", "id": p.stem, "by": "unknown", "at": now_iso(), "ok": False, "error": scrub(f"unreadable order file: {e}")}
            eng.store.audit(AuditEvent.make("engine", "order_refused", p.stem, res["error"]))
        else:
            res = apply_order(eng, order)
        res["order_id"] = p.stem
        done.mkdir(parents=True, exist_ok=True)
        (done / p.name).write_text(json.dumps({"order": order, "outcome": res}, indent=1) + "\n", encoding="utf-8")
        p.unlink()
        results.append(res)
    return results


def recent_outcomes(folder: Path | str = ORDERS, n: int = 20) -> list[dict]:
    done = Path(folder) / "done"
    if not done.exists():
        return []
    out = []
    for p in sorted(done.glob("*.json"))[-n:]:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            out.append(d.get("outcome") or {})
        except Exception:
            continue
    return out


def cleanup_done(folder: Path | str = ORDERS, keep: int = 200) -> int:
    """Keep the newest `keep` outcomes so the folder never grows without bound."""
    done = Path(folder) / "done"
    if not done.exists():
        return 0
    files = sorted(done.glob("*.json"))
    for p in files[:-keep] if len(files) > keep else []:
        p.unlink()
    return max(0, len(files) - keep)


