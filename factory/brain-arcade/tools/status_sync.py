#!/usr/bin/env python3
"""Build the two status documents every Brain Arcade run writes, from the lane's own files.

  python3 tools/status_sync.py --task ba-night --outcome done --note "..." [--needs "text|link" ...]
        [--views N --favs N] [--crew "Name|role|state|task" ...]

Writes /tmp/ba/room-status.json  -> ArtifactData set, room https://claude.ai/artifact/RuApFd8YnEgouX4ogv6D2i,
                                    collection "status", doc "main" (read first, pass if_version)
       /tmp/ba/hub-shop.json     -> ArtifactData set, Atlas Hub https://claude.ai/artifact/U91MrX9kzLUxLu9pnmgP5X,
                                    collection "shops", doc "brainarcade" (the Shop 2 tab; read first, pass if_version)
Both use file_path, so the run never retypes them. The hub doc is the ONLY thing this lane writes in
the main hub's database. Numbers come from listings.jsonl, sales-log.jsonl and stats/; views and
favorites only from --views/--favs or the newest stats/ file. Unknown stays null.
"""
import argparse, datetime as dt, glob, json, os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def rows(f):
    p = os.path.join(ROOT, f)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True); ap.add_argument("--outcome", required=True); ap.add_argument("--note", default="")
    ap.add_argument("--needs", action="append", default=[]); ap.add_argument("--crew", action="append", default=[])
    ap.add_argument("--views", type=int); ap.add_argument("--favs", type=int)
    a = ap.parse_args()
    from zoneinfo import ZoneInfo
    now = dt.datetime.now(dt.timezone.utc); day = now.astimezone(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")
    lane = json.load(open(os.path.join(ROOT, "lane.json")))
    live = [r for r in rows("listings.jsonl") if r.get("state") == "active"]
    sales = rows("sales-log.jsonl")
    views, favs = a.views, a.favs
    snaps = sorted(glob.glob(os.path.join(ROOT, "stats", "*.json")))
    if snaps and views is None:
        s = json.load(open(snaps[-1]))["listings"].values()
        views = sum(x.get("views") or 0 for x in s); favs = sum(x.get("favs") or 0 for x in s)
    lessons = open(os.path.join(ROOT, "LESSONS.md")).read().split("## Proven by this lane's numbers")[-1]
    top = next((l.strip("- ").strip() for l in reversed(lessons.splitlines()) if l.strip().startswith("-")), None)
    q = json.load(open(os.path.join(ROOT, "products", "queue.json")))
    nxt = next((i for i in q["items"] if i["status"] not in ("live", "scrapped")), None)
    needs = [dict(zip(("text", "link"), n.split("|", 1))) for n in a.needs]
    if lane["shop"]["shop_id"] is None and not any("Etsy" in n["text"] for n in needs):
        needs.insert(0, {"text": "Connect BrainArcadeGames Etsy (sign in as BrainArcadeGames, not GM's, then Allow)",
                      "link": lane["make"]["credential_request_link"]})
    crew = [dict(zip(("name", "role", "state", "task"), c.split("|", 3))) for c in a.crew]
    move = (needs[0]["text"].rstrip(".") + ". Then the Publisher puts the next passed game live.") if needs else \
        (f"Next: {nxt['slug'].replace('-', ' ')} ({nxt['status']})" if nxt else "Research the next season")
    month = day[:7]
    common = {"at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "shopVerified": lane["shop"]["shop_id"] is not None,
              "listedToday": sum(1 for r in live if r.get("day") == day), "listedTotal": len(live),
              "views": views, "favs": favs, "salesMonth": sum(1 for s in sales if str(s.get("day", "")).startswith(month)),
              "salesTotal": len(sales), "nextMove": move, "needsYou": needs}
    hub = dict(common, shop="BrainArcadeGames", crew=crew, crewSize=8, roomUrl=lane["room"]["url"], by="Brain Arcade crew")
    room = dict(common, sales=len(sales), topLesson=top, blocked=a.outcome == "blocked",
                headline=("Shop connected" if common["shopVerified"] else "Connect the shop") + f" · {len(live)} live",
                subline=a.note[:140], lessons=[top] if top else [],
                lastRun={"task": a.task, "outcome": a.outcome, "note": a.note[:200], "at": common["at"]})
    os.makedirs("/tmp/ba", exist_ok=True)
    json.dump(room, open("/tmp/ba/room-status.json", "w"), indent=1)
    json.dump(hub, open("/tmp/ba/hub-shop.json", "w"), indent=1)
    print("wrote /tmp/ba/room-status.json and /tmp/ba/hub-shop.json:", json.dumps({k: common[k] for k in ("listedTotal", "views", "favs", "salesMonth")}))


if __name__ == "__main__":
    main()
