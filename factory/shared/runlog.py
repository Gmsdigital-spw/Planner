#!/usr/bin/env python3
"""Run log for the GM Factory workspace (see factory/shared/logging.md).

  add       append one run line (measures loaded file sizes itself)
  --status  last run per task
  --summary N   per-task averages over the last N days

No dependencies. Run from anywhere; paths are resolved from this file's location.
"""
import argparse, json, os, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))      # repo root
LOG = os.path.join(ROOT, "factory", "runlog.jsonl")


def _iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _central_day(iso):
    """Grayson's day key: the Central date of the run start (DST-safe via zoneinfo)."""
    try:
        from zoneinfo import ZoneInfo
        return _iso(iso).astimezone(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")
    except Exception:
        return None


def _split(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def add(a):
    loaded = []
    for f in _split(a.loaded):
        p = f if os.path.isabs(f) else os.path.join(ROOT, f)
        try:
            b = os.path.getsize(p)
        except OSError:
            b = None
        loaded.append({"f": f, "b": b})
    known = [x["b"] for x in loaded if x["b"] is not None]
    loaded_bytes = sum(known)
    started, finished = a.started, a.finished or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    minutes = None
    try:
        minutes = round((_iso(finished) - _iso(started)).total_seconds() / 60, 1)
    except Exception:
        pass
    line = {
        "task": a.task,
        "day": a.day or _central_day(started),
        "run": a.run or "",
        "started": started,
        "finished": finished,
        "minutes": minutes,
        "model": a.model or "unknown",
        "stages": _split(a.stages),
        "skipped": _split(a.skipped),
        "loaded": loaded,
        "loadedBytes": loaded_bytes,
        "estTokens": loaded_bytes // 4,
        "unmeasured": [x["f"] for x in loaded if x["b"] is None],
        "gatewayJobs": a.gateway_jobs,
        "dbWrites": a.db_writes,
        "outcome": a.outcome,
        "note": (a.note or "")[:200],
        "needsYou": (a.needs_you or "")[:200],
    }
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(json.dumps(line, ensure_ascii=False))
    record_learning(line)


TASK_SCOPE = {"night-shift": "shop", "bolt": "shop", "herald": "shop", "check-up": "shop", "pricing": "shop", "video-pin": "shop", "scout-intel": "shop",
              "studio": "studio", "trading-scan": "trading", "trading-close": "trading", "trading-lab": "trading", "mechanic": "crew", "atlas-prime": "crew"}
TASK_AGENT = {"night-shift": "night-shift", "bolt": "bolt", "herald": "herald", "check-up": "warden", "pricing": "ledger", "video-pin": "pixel", "scout-intel": "scout",
              "studio": "vega", "trading-scan": "bull", "trading-close": "vault", "trading-lab": "tape", "mechanic": "mechanic", "atlas-prime": "foreman"}


def record_learning(line):
    """Learning hook (Phase 9): the same run line becomes one evaluation row (kind run, no invented score) in the
    durable learning store, keyed by task + start time so a re-run of this command never duplicates it. A failed
    or paused run, or a NEEDS YOU line, also leaves one mistake memory for the agent. Never breaks the run log."""
    if os.environ.get("GM_LEARNING_OFF") == "1":
        return
    try:
        sys.path.insert(0, ROOT)
        from factory.learning.brain import AgentBrain
        task = str(line.get("task") or "unknown")
        scope, agent = TASK_SCOPE.get(task, "crew"), TASK_AGENT.get(task, task)
        rid = f"runlog:{task}:{line.get('started')}"
        with AgentBrain() as b:
            b.log_run(rid, scope, agent, task=task, outcome=str(line.get("outcome") or "unknown"), mode="production", version=f"runlog:{line.get('model') or 'unknown'}",
                      minutes=line.get("minutes"), est_tokens=line.get("estTokens"), loaded_bytes=line.get("loadedBytes"), note=str(line.get("note") or ""),
                      needs_you=str(line.get("needsYou") or ""), started=line.get("started"), finished=line.get("finished"), stages=line.get("stages"), skipped=line.get("skipped"),
                      extra={"day": line.get("day"), "run": line.get("run"), "gatewayJobs": line.get("gatewayJobs"), "dbWrites": line.get("dbWrites")})
            if line.get("outcome") in ("failed", "paused") or line.get("needsYou"):
                b.remember(scope, agent, "mistake", f"{task} run {line.get('outcome')}" + (f": {line.get('note')}" if line.get("note") else "") +
                           (f" | needs you: {line.get('needsYou')}" if line.get("needsYou") else ""), f"run log {rid}", tags={"task": task, "outcome": line.get("outcome"), "day": line.get("day")})
        print(json.dumps({"learning": rid}))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"learning": "unavailable", "why": f"{type(e).__name__}: {str(e)[:120]}"}))


def _read():
    if not os.path.exists(LOG):
        return []
    out = []
    with open(LOG, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def status():
    rows = _read()
    if not rows:
        print("no runs logged yet"); return
    last = {}
    for r in rows:
        last[r.get("task")] = r
    print(f"{'task':<16} {'day':<10} {'min':>6} {'estTok':>7} {'outcome':<8} note")
    for t, r in sorted(last.items()):
        print(f"{t:<16} {r.get('day') or '':<10} {str(r.get('minutes') or ''):>6} {str(r.get('estTokens') or ''):>7} {r.get('outcome') or '':<8} {r.get('note') or ''}")


def summary(days):
    rows = _read()
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    by = {}
    for r in rows:
        if (r.get("day") or "") < cutoff:
            continue
        by.setdefault(r.get("task"), []).append(r)
    if not by:
        print(f"no runs in the last {days} days"); return
    print(f"{'task':<16} {'runs':>4} {'avg min':>8} {'avg estTok':>10} {'failed':>6}")
    for t, rs in sorted(by.items()):
        mins = [r["minutes"] for r in rs if isinstance(r.get("minutes"), (int, float))]
        toks = [r["estTokens"] for r in rs if isinstance(r.get("estTokens"), int)]
        failed = sum(1 for r in rs if r.get("outcome") == "failed")
        am = round(sum(mins) / len(mins), 1) if mins else ""
        at = round(sum(toks) / len(toks)) if toks else ""
        print(f"{t:<16} {len(rs):>4} {str(am):>8} {str(at):>10} {failed:>6}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    a = sub.add_parser("add")
    a.add_argument("--task", required=True)
    a.add_argument("--day")
    a.add_argument("--run")
    a.add_argument("--started", required=True)
    a.add_argument("--finished")
    a.add_argument("--model")
    a.add_argument("--stages", default="")
    a.add_argument("--skipped", default="")
    a.add_argument("--loaded", default="")
    a.add_argument("--gateway-jobs", type=int, default=0)
    a.add_argument("--db-writes", type=int, default=0)
    a.add_argument("--outcome", default="done", choices=["done", "failed", "paused", "skipped"])
    a.add_argument("--note", default="")
    a.add_argument("--needs-you", default="")
    p.add_argument("--status", action="store_true")
    p.add_argument("--summary", type=int, metavar="DAYS")
    args = p.parse_args()
    if args.cmd == "add":
        add(args)
    elif args.status:
        status()
    elif args.summary:
        summary(args.summary)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
