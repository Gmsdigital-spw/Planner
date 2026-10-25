#!/usr/bin/env python3
"""Brain Arcade logs: run log, notes on everything, sales log, stats, and the morning-report line.

  ba_log.py run    --task ba-night|ba-publish|ba-learn --started ISO --finished ISO --outcome done|failed|blocked|waiting
                   --note "..." [--needs-you "..."]
  ba_log.py note   --kind listing|view|fav|sale|pin|post|price|build|qa|error|fix|idea --id X --what "..." [--tags k=v,k=v]
  ba_log.py sale   --listing-id N --receipt R --amount 4.99 --day YYYY-MM-DD
  ba_log.py stats  <active_listings.json>      (Etsy GET /shops/<id>/listings/active answer) -> stats/<day>.json
  ba_log.py status                              last run of each ba-* task
  ba_log.py report                              the Brain Arcade section of the morning report (2 lines)
"""
import argparse, datetime as dt, json, os, sys
from zoneinfo import ZoneInfo

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = lambda *a: os.path.join(ROOT, *a)


def day():
    return dt.datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")


def append(f, row):
    with open(P(f), "a") as fh:
        fh.write(json.dumps(row) + "\n")
    print(json.dumps(row))


def rows(f):
    if not os.path.exists(P(f)):
        return []
    return [json.loads(l) for l in open(P(f)) if l.strip()]


def stats_snap(path):
    d = json.load(open(path))
    snap = {str(r["listing_id"]): {"title": r.get("title"), "views": r.get("views"), "favs": r.get("num_favorers"),
                                   "price": (r.get("price") or {}).get("amount", 0) / max((r.get("price") or {}).get("divisor", 100), 1)}
            for r in d.get("results", [])}
    os.makedirs(P("stats"), exist_ok=True)
    json.dump({"day": day(), "listings": snap}, open(P("stats", day() + ".json"), "w"), indent=1)
    print(f"stats/{day()}.json: {len(snap)} listings")


def report():
    listings = rows("listings.jsonl")
    since = (dt.date.fromisoformat(day()) - dt.timedelta(days=1)).isoformat()
    posted = [r for r in listings if r.get("day", "") >= since and r.get("state") == "active"]
    snaps = sorted(f for f in os.listdir(P("stats"))) if os.path.isdir(P("stats")) else []
    views = favs = None
    if snaps:
        s = json.load(open(P("stats", snaps[-1])))["listings"]
        views = sum(v.get("views") or 0 for v in s.values()); favs = sum(v.get("favs") or 0 for v in s.values())
    sales = rows("sales-log.jsonl")
    lesson = next((l.strip("- \n") for l in reversed(open(P("LESSONS.md")).read().split("## Proven by this lane's numbers")[-1].splitlines()) if l.strip().startswith("-")), None)
    nxt = None
    try:
        q = json.load(open(P("products", "queue.json")))
        nxt = next((i["slug"] for i in q["items"] if i["status"] != "live"), None)
    except Exception:
        pass
    runs = {}
    for r in rows("runlog.jsonl"):
        runs[r["task"]] = r
    need = [r["needsYou"] for r in runs.values() if r.get("needsYou")]
    f = lambda x: "unknown" if x is None else x
    print(f"🕹️ Brain Arcade: {len(posted)} listed · {f(views)} views · {f(favs)} favs · {len(sales)} sales total")
    print(f"Lesson: {lesson or 'none proven yet'} · Next: {need[0] if need else (nxt or 'research next season')}")


def main():
    ap = argparse.ArgumentParser(); s = ap.add_subparsers(dest="cmd", required=True)
    r = s.add_parser("run")
    for k in ("--task", "--started", "--finished", "--outcome", "--note"):
        r.add_argument(k, required=True)
    r.add_argument("--needs-you", default="")
    n = s.add_parser("note")
    for k in ("--kind", "--id", "--what"):
        n.add_argument(k, required=True)
    n.add_argument("--tags", default="")
    sa = s.add_parser("sale")
    for k in ("--listing-id", "--receipt", "--amount", "--day"):
        sa.add_argument(k, required=True)
    st = s.add_parser("stats"); st.add_argument("file")
    s.add_parser("status"); s.add_parser("report")
    a = ap.parse_args()
    if a.cmd == "run":
        mins = round((dt.datetime.fromisoformat(a.finished.replace("Z", "+00:00")) -
                      dt.datetime.fromisoformat(a.started.replace("Z", "+00:00"))).total_seconds() / 60, 1)
        append("runlog.jsonl", {"task": a.task, "day": day(), "started": a.started, "finished": a.finished, "minutes": mins,
                                "outcome": a.outcome, "note": a.note, "needsYou": a.needs_you})
    elif a.cmd == "note":
        tags = dict(kv.split("=", 1) for kv in a.tags.split(",") if "=" in kv)
        append("results.jsonl", {"day": day(), "lane": "brain-arcade", "kind": a.kind, "id": a.id, "what": a.what, "tags": tags})
    elif a.cmd == "sale":
        if any(x.get("receipt") == a.receipt for x in rows("sales-log.jsonl")):
            print("already logged"); return
        append("sales-log.jsonl", {"day": a.day, "listing_id": a.listing_id, "receipt": a.receipt, "amount": float(a.amount)})
    elif a.cmd == "stats":
        stats_snap(a.file)
    elif a.cmd == "status":
        last = {}
        for x in rows("runlog.jsonl"):
            last[x["task"]] = x
        for t, x in sorted(last.items()):
            print(f"{t}: {x['day']} {x['outcome']} ({x['minutes']} min) {x['note'][:80]} {('NEEDS YOU: ' + x['needsYou']) if x['needsYou'] else ''}")
        if not last:
            print("no Brain Arcade runs yet")
    else:
        report()


if __name__ == "__main__":
    main()
