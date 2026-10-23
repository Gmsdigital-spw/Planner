#!/usr/bin/env python3
"""The Notebook helper (Grayson, Oct 23, 2026). See factory/notebook/README.md.

  nb.py show --lane etsy               print the lane file (+ business rules) to read before working
  nb.py add --lane etsy --kind listing --id 123 --what "..." --tags layout=collage,price=4.99
  nb.py pending [--days 7]             items 7+ days old with no outcome yet (keeper fills these)
  nb.py outcome --id 123 --set views=12,favs=1,sales=0
  nb.py compare --lane etsy --tag layout --metric favs    group outcomes by a tag
"""
import argparse, datetime, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results.jsonl")
LANES = ["business", "etsy", "pins", "social", "trading"]


def today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/Chicago")).date().isoformat()
    except Exception:
        return datetime.date.today().isoformat()


def kv(s):
    out = {}
    for part in (s or "").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            v = v.strip()
            try:
                v = float(v) if "." in v else int(v)
            except ValueError:
                pass
            out[k.strip()] = v
    return out


def load():
    if not os.path.exists(RESULTS):
        return []
    rows = []
    with open(RESULTS) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def save(rows):
    with open(RESULTS, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def cmd_show(a):
    biz = open(os.path.join(HERE, "business.md")).read()
    print(biz.split("## Proven")[0].strip())  # business rules only
    if a.lane != "business":
        print("\n" + open(os.path.join(HERE, a.lane + ".md")).read().strip())
    rows = [r for r in load() if r.get("lane") == a.lane]
    if rows:
        print(f"\n## Last {min(10, len(rows))} {a.lane} results")
        for r in rows[-10:]:
            print("-", r.get("day"), r.get("kind"), r.get("id"), "|", r.get("what"),
                  "|", json.dumps(r.get("tags", {})), "| outcome:", json.dumps(r.get("outcome")) if r.get("outcome") else "pending")


def cmd_add(a):
    rows = load()
    rows.append({"day": a.day or today(), "lane": a.lane, "kind": a.kind, "id": str(a.id),
                 "what": a.what[:200], "tags": kv(a.tags), "outcome": None, "checked": None})
    save(rows)
    print("added")


def cmd_pending(a):
    cut = (datetime.date.fromisoformat(today()) - datetime.timedelta(days=a.days)).isoformat()
    for r in load():
        if not r.get("outcome") and r.get("day", "9999") <= cut:
            print(json.dumps(r, ensure_ascii=False))


def cmd_outcome(a):
    rows, hit = load(), 0
    for r in rows:
        if r.get("id") == str(a.id) and (not a.lane or r.get("lane") == a.lane):
            r["outcome"] = {**(r.get("outcome") or {}), **kv(a.set)}
            r["checked"] = today()
            hit += 1
    save(rows)
    print(f"updated {hit}")


def cmd_compare(a):
    g = defaultdict(list)
    for r in load():
        if r.get("lane") == a.lane and r.get("outcome") and a.tag in r.get("tags", {}):
            g[str(r["tags"][a.tag])].append(r["outcome"].get(a.metric))
    for k, vals in sorted(g.items()):
        nums = [v for v in vals if isinstance(v, (int, float))]
        avg = sum(nums) / len(nums) if nums else None
        print(f"{a.tag}={k}: n={len(nums)} avg {a.metric}={avg if avg is None else round(avg, 2)}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("show"); x.add_argument("--lane", choices=LANES, required=True); x.set_defaults(f=cmd_show)
    x = s.add_parser("add"); x.add_argument("--lane", choices=LANES, required=True)
    x.add_argument("--kind", required=True); x.add_argument("--id", required=True)
    x.add_argument("--what", required=True); x.add_argument("--tags", default="")
    x.add_argument("--day"); x.set_defaults(f=cmd_add)
    x = s.add_parser("pending"); x.add_argument("--days", type=int, default=7); x.set_defaults(f=cmd_pending)
    x = s.add_parser("outcome"); x.add_argument("--id", required=True); x.add_argument("--lane")
    x.add_argument("--set", required=True); x.set_defaults(f=cmd_outcome)
    x = s.add_parser("compare"); x.add_argument("--lane", choices=LANES, required=True)
    x.add_argument("--tag", required=True); x.add_argument("--metric", required=True); x.set_defaults(f=cmd_compare)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
