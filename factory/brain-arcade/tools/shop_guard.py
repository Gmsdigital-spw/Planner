#!/usr/bin/env python3
"""Brain Arcade shop guard. Runs BEFORE every Etsy write. A block is final for that run.

  verify-connection <me.json> <shops.json>
      After the Make connection is authorized: me.json = Etsy GET /users/me answer,
      shops.json = GET /users/<user_id>/shops answer. PASS only if the shop name is
      BrainArcadeGames and it is NOT GM's Digital Creations. Prints the shop_id to save in lane.json.

  check-call --lane brain-arcade|main --method M --url U [--listing-ledger F]
      Every Etsy call this crew sends. Blocks: any /shops/<id> that is not the lane's own
      verified shop; any GM shop id for brain-arcade (or BA id for main); a brain-arcade write
      while lane.json has no verified shop_id; a /listings/<id> write on a listing this lane
      did not create (not in its ledger).

  check-dupe <listing.json>
      Never the same item in both shops: blocks a title too close to any GM's Digital
      Creations listing (shopcheck/views.json, newest day) or to a Brain Arcade listing
      already in the ledger.

  selftest

Exit 0 = OK, 2 = BLOCKED (the line starting "BLOCKED:" is the alert text for Grayson).
"""
import argparse, difflib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LANE = os.path.normpath(os.path.join(HERE, "..", "lane.json"))
LEDGER = os.path.normpath(os.path.join(HERE, "..", "listings.jsonl"))
MAIN_VIEWS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "shopcheck", "views.json"))
MAIN_SHOP_ID = 68605457


def block(msg):
    print("BLOCKED: " + msg)
    sys.exit(2)


def lane_cfg(path=LANE):
    return json.load(open(path))


def norm(name):
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def verify_connection(me, shops, cfg):
    want = norm(cfg["shop"]["name"])
    bad_names = {norm(n) for n in cfg["never_shops"]["names"]}
    bad_ids = set(cfg["never_shops"]["ids"])
    lst = shops.get("results", [shops]) if isinstance(shops, dict) else shops
    lst = [s for s in lst if s and s.get("shop_id")]
    if not lst:
        return False, "the connected Etsy account has no shop. Sign in as BrainArcadeGames and tap the link again."
    for s in lst:
        if s["shop_id"] in bad_ids or norm(s.get("shop_name")) in bad_names:
            return False, ("the Etsy link was authorized with GM's Digital Creations, not BrainArcadeGames. "
                           "Sign out of Etsy, sign in to BrainArcadeGames, and tap the link again.")
    for s in lst:
        if norm(s.get("shop_name")) == want:
            return True, s["shop_id"]
    return False, f"connected shop is '{lst[0].get('shop_name')}', not BrainArcadeGames."


def ledger_ids(path=LEDGER):
    ids = set()
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("listing_id"):
                    ids.add(str(r["listing_id"]))
    return ids


def check_call(lane, method, url, cfg, ledger=LEDGER, creating=None):
    method = method.upper()
    write = method in ("POST", "PUT", "PATCH", "DELETE")
    path = url.split("/v3/application", 1)[-1]
    if lane == "brain-arcade":
        own = cfg["shop"]["shop_id"]
        bad = set(cfg["never_shops"]["ids"])
        if any(int(s) in bad for s in re.findall(r"/shops/(\d+)", path)):
            return False, "Brain Arcade crew tried to use GM's Digital Creations. Post stopped."
        if own is None and write:
            return False, "BrainArcadeGames shop is not verified yet (connect the Etsy link first). Nothing was posted."
    else:  # main crew mode, offered to the main crew; not wired into its runs
        own = MAIN_SHOP_ID
        ba = cfg["shop"]["shop_id"]
        bad = {ba} if ba else set()
    for sid in re.findall(r"/shops/(\d+)", path):
        sid = int(sid)
        if sid in bad:
            return False, f"{lane} crew tried to use shop {sid}, which belongs to the other lane. Post stopped."
        if own is not None and sid != int(own):
            return False, f"{lane} crew tried to use shop {sid}; its only shop is {own}. Post stopped."
    if lane == "brain-arcade" and write:
        m = re.search(r"/listings/(\d+)", path)
        if m and m.group(1) not in ledger_ids(ledger) and m.group(1) != str(creating or ""):
            return False, f"listing {m.group(1)} was not created by the Brain Arcade crew. Write stopped."
        if not re.search(r"/shops/\d+", path) and not m:
            return False, f"write to {path} is not a shop or listing path this crew uses. Stopped."
    return True, "ok"


def main_titles(path=MAIN_VIEWS):
    try:
        v = json.load(open(path))
        day = sorted(v)[-1]
        return [x.get("title", "") for x in v[day].values()]
    except Exception:
        return []


def check_dupe(listing, ledger=LEDGER, main_path=MAIN_VIEWS):
    t = re.sub(r"[^a-z0-9 ]", " ", listing["title"].lower())
    others = [("GM's Digital Creations", x) for x in main_titles(main_path)]
    if os.path.exists(ledger):
        for line in open(ledger):
            if line.strip():
                r = json.loads(line)
                if r.get("product_id") != listing.get("product_id"):
                    others.append(("Brain Arcade", r.get("title", "")))
    for shop, o in others:
        o2 = re.sub(r"[^a-z0-9 ]", " ", o.lower())
        if difflib.SequenceMatcher(None, t.split(), o2.split()).ratio() >= 0.8:
            return False, f"'{listing['title'][:60]}' is too close to a {shop} listing ('{o[:60]}'). Not posted."
    return True, "ok"


def selftest():
    import tempfile
    cfg = {"shop": {"name": "BrainArcadeGames", "shop_id": None},
           "never_shops": {"ids": [MAIN_SHOP_ID], "names": ["GMsDigitalCreations"]}}
    ok, why = verify_connection({}, {"results": [{"shop_id": MAIN_SHOP_ID, "shop_name": "GMsDigitalCreations"}]}, cfg)
    assert not ok and "GM's" in why
    ok, sid = verify_connection({}, {"results": [{"shop_id": 999, "shop_name": "BrainArcadeGames"}]}, cfg)
    assert ok and sid == 999
    assert not check_call("brain-arcade", "POST", "/v3/application/shops/999/listings", cfg)[0], "unverified must block"
    cfg["shop"]["shop_id"] = 999
    d = tempfile.mkdtemp(); led = os.path.join(d, "l.jsonl")
    open(led, "w").write(json.dumps({"listing_id": 555, "product_id": "p1", "title": "Thanksgiving Math Escape Room 3rd Grade"}) + "\n")
    assert check_call("brain-arcade", "POST", "/v3/application/shops/999/listings", cfg, led)[0]
    assert not check_call("brain-arcade", "POST", f"/v3/application/shops/{MAIN_SHOP_ID}/listings", cfg, led)[0]
    assert not check_call("brain-arcade", "POST", "/v3/application/shops/123/listings", cfg, led)[0]
    assert check_call("brain-arcade", "POST", "/v3/application/shops/999/listings/555/images", cfg, led)[0]
    assert not check_call("brain-arcade", "PATCH", "/v3/application/shops/999/listings/777", cfg, led)[0]
    assert check_call("brain-arcade", "PATCH", "/v3/application/shops/999/listings/777", cfg, led, creating=777)[0]
    assert check_call("brain-arcade", "GET", "/v3/application/listings/active?keywords=math", cfg, led)[0]
    assert not check_call("main", "POST", "/v3/application/shops/999/listings", cfg, led)[0]
    assert check_call("main", "POST", f"/v3/application/shops/{MAIN_SHOP_ID}/listings", cfg, led)[0]
    mv = os.path.join(d, "v.json")
    json.dump({"2026-10-20": {"1": {"title": "Christmas Party Games Bundle, 36 Printable Games"}}}, open(mv, "w"))
    assert check_dupe({"title": "Thanksgiving Math Escape Room 3rd Grade", "product_id": "p1"}, led, mv)[0], "own re-check is fine"
    assert not check_dupe({"title": "Thanksgiving Math Escape Room 3rd Grade", "product_id": "p2"}, led, mv)[0]
    assert not check_dupe({"title": "Christmas Party Games Bundle, 36 Printable Games", "product_id": "p3"}, led, mv)[0]
    assert check_dupe({"title": "Winter Multiplication Bingo 4th Grade", "product_id": "p4"}, led, mv)[0]
    print("selftest PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["verify-connection", "check-call", "check-dupe", "selftest"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--lane", default="brain-arcade", choices=["brain-arcade", "main"])
    ap.add_argument("--method", default="GET")
    ap.add_argument("--url", default="")
    ap.add_argument("--creating", default=None, help="listing id created earlier in this same run")
    a = ap.parse_args()
    if a.cmd == "selftest":
        selftest(); sys.exit(0)
    cfg = lane_cfg()
    if a.cmd == "verify-connection":
        ok, r = verify_connection(json.load(open(a.files[0])), json.load(open(a.files[1])), cfg)
        if not ok:
            block(r)
        print(f"VERIFIED: BrainArcadeGames shop_id {r}")
    elif a.cmd == "check-call":
        ok, r = check_call(a.lane, a.method, a.url, cfg, creating=a.creating)
        if not ok:
            block(r)
        print("OK")
    else:
        ok, r = check_dupe(json.load(open(a.files[0])))
        if not ok:
            block(r)
        print("OK: not in either shop yet")
