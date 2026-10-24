#!/usr/bin/env python3
"""studio/quality_gates.py: the Shorts scorecard, the Etsy cover check and the commercial blueprint.
V8 "The Turning Point" (Grayson, Oct 24, 2026). Nothing posts unless it passes. Fails get rebuilt, not skipped.

Three gates, all free (Python stdlib; Pillow + imagehash only for the cover uniqueness check):

  Shorts   python3 studio/quality_gates.py short ep17 [--write] [--root <repo>]
           Reads yt/jobs/ep17.json (the job), yt/out/ep17.json (what the free builder made) and, when it
           exists, yt/jobs/ep17.research.json (the crew's vidIQ title score and research notes). Every one
           of the 10 checks is decided from those files, with the evidence written next to it. --write saves
           yt/out/ep17.score.json {score, pass, checks, fixes}. Exit 0 = PASS (85+), 1 = FAIL, 2 = cannot judge.
  Cover    python3 studio/quality_gates.py cover new.png --recent <dir or files...> [--checks k=1,k=0,...]
           Perceptual-hash distance of the new cover against the first 20 covers given, newest first (unique = every distance >= 18)
           plus the five judged checks the inspector passes in with --checks. Exit 0 = PASS (92+), 1 = FAIL.
  Blueprint python3 studio/quality_gates.py blueprint       prints the 15 to 22 second commercial blueprint.
  Selftest  python3 studio/quality_gates.py --selftest      synthetic PASS and FAIL cases; exits non-zero on a bug.

Honesty: a check the files cannot prove is FALSE, never assumed. "unknown" costs the points; it never
passes quietly. The vidIQ title check is worth 5 points on purpose: when vidIQ credits are gone (2 left on
Oct 24, 2026, renews Nov 19) a Short can still reach 95, and the scorecard says the title was not scored.
"""
import json, os, re, sys, glob, datetime as dt

VERSION = "8.0"
PASS_SHORT = 85
PASS_COVER = 92

SHORTS_RUBRIC = {            # points; pass = 85+
    "hook_motion_first_1_5s": 15,   # something moves in the first 1.5 seconds
    "hook_text_question_or_shock": 10,
    "story_has_twist": 15,
    "ending_loops_to_start": 10,
    "new_beat_every_3s": 10,        # cut, angle change or action every 2-3s
    "real_animation_not_zoom": 15,
    "natural_voice": 10,
    "captions_in_safe_zone": 5,
    "length_20_to_45s": 5,
    "title_vidiq_score_70plus": 5,
}

def score_short(checks: dict) -> tuple:
    score = sum(pts for k, pts in SHORTS_RUBRIC.items() if checks.get(k))
    fixes = [k for k in SHORTS_RUBRIC if not checks.get(k)]
    return score, fixes          # fixes = what the Studio must redo

COVER_RUBRIC = {             # pass = 92+
    "real_product_pages_fill_frame": 20,
    "big_count_badge": 10,           # the count big and readable on the label card ("36 GAMES"); never a sticker (V8, Oct 24)
    "realistic_mockup": 20,          # hands, wall, tablet; never drawn/fake
    "unique_vs_last_20_covers": 20,  # perceptual-hash distance check below
    "readable_at_thumbnail_size": 15,
    "matches_season_and_buyer": 15,
}

def cover_is_unique(new_img_path, recent_paths, min_distance=18):
    """Blocks copy-paste covers: compares against the last 20 covers."""
    from PIL import Image
    import imagehash
    h = imagehash.phash(Image.open(new_img_path))
    return all(h - imagehash.phash(Image.open(p)) >= min_distance for p in recent_paths)

def cover_distances(new_img_path, recent_paths):
    """The same comparison, one row per recent cover (path, distance), nearest first."""
    from PIL import Image
    import imagehash
    h = imagehash.phash(Image.open(new_img_path))
    rows = [(p, int(h - imagehash.phash(Image.open(p)))) for p in recent_paths]
    return sorted(rows, key=lambda r: r[1])

def score_cover(checks: dict) -> tuple:
    score = sum(pts for k, pts in COVER_RUBRIC.items() if checks.get(k))
    return score, [k for k in COVER_RUBRIC if not checks.get(k)]

COMMERCIAL_BLUEPRINT = [     # the Etsy promo video, 15-22 seconds (media-rules.md)
    ("0.0-1.5s", "Hook: the finished product in hand + bold 4-word caption"),
    ("1.5-6s",   "Phone screen: scroll the real Etsy listing"),
    ("6-12s",    "Tap in: show 3 real pages up close, quick cuts"),
    ("12-18s",   "Voiceover benefit: who it's for, why it saves time"),
    ("18-22s",   "Price/sale badge + 'Link in bio'"),
    ("rules",    "Cool natural voice, hype music low, captions never cover the product, animated background, new style daily"),
]

# ----------------------------------------------------------------------------------------------- Shorts
# What the free builder (yt/build/make_short.py) records, and the limits the checks use.
SHOCK_WORDS = {"NEVER", "SECRET", "CAUGHT", "LIED", "LIE", "REVENGE", "FIRED", "STOLE", "STOLEN", "BANNED", "EXPOSED",
               "RUINED", "DESTROYED", "WRONG", "MISTAKE", "WORST", "LAST", "FINAL", "GONE", "LOST", "FAILED", "FAIL",
               "BROKE", "CHEATED", "BLAMED", "QUIT", "KICKED", "WARNED", "HP", "PAID", "OWE", "OWED", "REGRET", "SORRY"}
SAFE_TOP_PCT = 10.0          # YouTube Shorts UI: the top ~10% (search, camera) and bottom ~25% (title, buttons)
SAFE_BOTTOM_PCT = 75.0
# make_short.py renders at 1080x1920: captions bottom-aligned with MarginV 600 (bottom edge at 68.75% of the
# height), the hook top-aligned with MarginV 230 (12.0% down). Newer builds write these into yt/out/<id>.json.
BUILDER_CAPTIONS = {"cap_bottom_pct": 68.75, "hook_top_pct": 11.98, "source": "make_short.py ASS styles"}
MAX_SCENE_S = 4.0            # a still scene longer than this is a slow beat
MAX_ANIM_SCENE_S = 5.5       # a scene with real motion may run a little longer
MEAN_SCENE_S = 3.5           # "a new beat every 2 to 3 seconds"
MIN_S, MAX_S = 20.0, 45.0
ANIM_RE = re.compile(r"line (\d+): real motion from the free animation lane")

def _words(s):
    return [w for w in re.split(r"\s+", str(s or "").strip()) if w]

def _prompt(line):
    return re.sub(r"\s+", " ", str(((line or {}).get("image") or {}).get("prompt") or "")).strip().lower()

def anim_lines(out):
    """Line indexes (0-based, as the builder numbers them) that got real motion from the free Hugging Face lane."""
    found = set()
    for w in out.get("warnings") or []:
        m = ANIM_RE.match(str(w))
        if m:
            found.add(int(m.group(1)))
    for i in out.get("animLines") or []:
        try:
            found.add(int(i))
        except (TypeError, ValueError):
            pass
    return found

def scene_spans(out):
    """Seconds each scene is on screen: from its voice start to the next scene's voice start (the last one to the end)."""
    wins = out.get("lines") or []
    try:
        dur = float(out.get("duration") or 0)
    except (TypeError, ValueError):
        dur = 0.0
    spans = []
    for i, w in enumerate(wins):
        try:
            s = 0.0 if i == 0 else float(w[0])          # scene 1 runs from t=0, not from the first word
            nxt = float(wins[i + 1][0]) if i + 1 < len(wins) else dur
        except (TypeError, ValueError, IndexError):
            continue
        spans.append(max(0.0, nxt - s))
    return spans

def check_short(job, out, research=None):
    """Decide the 10 checks from the job, the builder's output and the crew's research sidecar.
    Returns (checks, evidence) where evidence[k] says what was seen and, on a fail, what to redo."""
    lines = [l for l in (job.get("lines") or []) if isinstance(l, dict)]
    n = len(lines)
    warnings = [str(w) for w in (out.get("warnings") or [])]
    anim = anim_lines(out)
    clips = {i for i, l in enumerate(lines) if isinstance(l.get("clip"), dict) and l["clip"].get("url")}
    moving = anim | clips
    checks, ev = {}, {}

    # 1. hook motion in the first 1.5 s: line 1 is a real-motion clip (free animation lane) or a real video clip
    checks["hook_motion_first_1_5s"] = n > 0 and 0 in moving
    ev["hook_motion_first_1_5s"] = ("line 1 has real motion from the free animation lane" if 0 in anim else
                                    "line 1 is a real clip" if 0 in clips else
                                    "line 1 is a still (parallax only): put anim:true on line 1 or give it a real clip")

    # 2. hook text: 3 to 8 words with a question, a number or a shock word
    hook = str(job.get("hook") or "").strip()
    hw = _words(hook)
    shock = ("?" in hook) or bool(re.search(r"\d", hook)) or any(w.strip("?!.,'\"").upper() in SHOCK_WORDS for w in hw)
    checks["hook_text_question_or_shock"] = 3 <= len(hw) <= 8 and shock
    ev["hook_text_question_or_shock"] = (f"hook \"{hook}\" ({len(hw)} words)" + ("" if checks["hook_text_question_or_shock"] else
                                         ": needs 3 to 8 words with a question mark, a number or a shock word"))

    # 3. twist: a "punch" scene that is neither the opening nor the loop line
    punch = [i for i, l in enumerate(lines) if isinstance(l.get("image"), dict) and l["image"].get("motion") == "punch"]
    twist = sorted([i for i in punch if 1 <= i < n - 1], key=lambda i: i not in anim)   # an animated punch line is the twist
    checks["story_has_twist"] = bool(twist)
    ev["story_has_twist"] = (f"twist at line {twist[0] + 1} (punch)" if twist else
                             "no twist line: mark the reveal with motion \"punch\" (not the first or last line)")

    # 4. loop: loop true, the last line reuses line 1's scene and cuts straight back (pause <= 0.1)
    try:
        last_pause = float(lines[-1].get("pause", 0.28)) if n else 9      # the builder's default pause is 0.28 s
    except (TypeError, ValueError):
        last_pause = 9
    same = n >= 2 and _prompt(lines[0]) == _prompt(lines[-1]) and _prompt(lines[0]) != ""
    checks["ending_loops_to_start"] = bool(job.get("loop", True)) and same and last_pause <= 0.1   # the builder defaults loop to true
    ev["ending_loops_to_start"] = ("loop true, last scene = first scene, last pause %.2f" % last_pause if checks["ending_loops_to_start"] else
                                   "loop needs: loop true, the last line's image prompt identical to line 1's, last pause 0.05")

    # 5. a new beat every 2 to 3 s: no still scene over 4.0 s (5.5 s with real motion), mean under 3.5 s
    spans = scene_spans(out)
    long_ = [(i + 1, round(s, 1)) for i, s in enumerate(spans) if s > (MAX_ANIM_SCENE_S if i in moving else MAX_SCENE_S)]
    mean = (sum(spans) / len(spans)) if spans else 0.0
    checks["new_beat_every_3s"] = bool(spans) and not long_ and mean <= MEAN_SCENE_S
    ev["new_beat_every_3s"] = (f"{len(spans)} scenes, mean {mean:.1f} s, longest {max(spans):.1f} s" if spans else "no scene timings in the build output") + \
                              ("" if checks["new_beat_every_3s"] else
                               (f"; too long: lines {', '.join(f'{i} ({s} s)' for i, s in long_)}" if long_ else "; mean over 3.5 s") +
                               ". Split long lines (9 words or fewer each) so every scene is a new beat")

    # 6. real animation, not a slideshow: the twist line and at least one more line got real motion; no zoom fallback
    zoom_fallback = [w for w in warnings if "used simple zoom" in w]
    anim_fail = [w for w in warnings if "animation lane unavailable" in w or "animation lane error" in w]
    checks["real_animation_not_zoom"] = 2 <= len(anim) <= 3 and bool(twist) and twist[0] in anim and not zoom_fallback
    checks["_twist_moved"] = bool(twist) and twist[0] in anim      # V8 rule 4: a hard gate, not points
    ev["real_animation_not_zoom"] = (f"real motion on lines {', '.join(str(i + 1) for i in sorted(anim))}" if anim else "no line got real motion") + \
                                    ("" if checks["real_animation_not_zoom"] else
                                     ("; the free lane failed: " + anim_fail[0][:90] if anim_fail else "") +
                                     ("; a scene fell back to a simple zoom" if zoom_fallback else "") +
                                     ("; over 3 animated shots (the free quota rule)" if len(anim) > 3 else "") +
                                     ". Needs anim:true on the twist line and line 1 (max 3 animated shots) and a working HF_TOKEN")

    # 7. natural voice: the edge story voice at a natural speed, not the fallback engine, not a dry run
    try:
        speed = float(job.get("speed", 1.03))
    except (TypeError, ValueError):
        speed = 0
    tts = str(out.get("tts") or "")
    voice = str(job.get("voice", "andrew")).lower()
    checks["natural_voice"] = tts == "edge" and voice in ("andrew", "ava") and not out.get("fakeTts") and 0.95 <= speed <= 1.06 and not any("TTS edge failed" in w for w in warnings)
    ev["natural_voice"] = f"voice engine {tts or 'unknown'}, voice {voice}, speed {speed}" + ("" if checks["natural_voice"] else ": needs engine edge, voice andrew or ava, speed 0.95 to 1.06, real TTS")

    # 8. captions in the safe zone: the hook below the top 10%, the captions above the bottom 25%
    caps = out.get("captions") if isinstance(out.get("captions"), dict) else BUILDER_CAPTIONS
    try:
        top = float(caps.get("hook_top_pct")); bottom = float(caps.get("cap_bottom_pct"))
        checks["captions_in_safe_zone"] = SAFE_TOP_PCT <= top and bottom <= SAFE_BOTTOM_PCT
    except (TypeError, ValueError):
        top = bottom = None
        checks["captions_in_safe_zone"] = False
    ev["captions_in_safe_zone"] = (f"hook at {top}% from the top, captions end at {bottom}% ({caps.get('source', 'build output')})" if top is not None
                                   else "caption placement unknown") + ("" if checks["captions_in_safe_zone"] else ": keep text between 10% and 75% of the height")

    # 9. length 20 to 45 s
    try:
        dur = float(out.get("duration") or 0)
    except (TypeError, ValueError):
        dur = 0
    checks["length_20_to_45s"] = MIN_S <= dur <= MAX_S
    ev["length_20_to_45s"] = f"{dur:.1f} s" + ("" if checks["length_20_to_45s"] else f": needs {MIN_S:.0f} to {MAX_S:.0f} s (aim 25 to 40)")

    # 10. vidIQ title score 70+ (from the crew's research sidecar; 5 credits per score)
    r = research or {}
    ts = r.get("title_score", (job.get("vidiq") or {}).get("title_score") if isinstance(job.get("vidiq"), dict) else None)
    checks["title_vidiq_score_70plus"] = isinstance(ts, (int, float)) and not isinstance(ts, bool) and ts >= 70
    ev["title_vidiq_score_70plus"] = (f"vidIQ title score {ts}" if isinstance(ts, (int, float)) and not isinstance(ts, bool) else
                                      ("title_score must be a number" if ts is not None else "title not scored by vidIQ")) + \
                                     ("" if checks["title_vidiq_score_70plus"] else
                                      (f" ({r['why']})" if r.get("why") else (f" (credits {r['credits']})" if r.get("credits") is not None else "")) +
                                      ": score it with vidiq_score_title (type short) when 5 or more credits are left; 70+ passes")
    return checks, ev

def scorecard(job, out, research=None):
    checks, ev = check_short(job, out, research)
    score, fixes = score_short(checks)
    twist_moved = bool(checks.get("_twist_moved"))
    return {"schema": "shorts-scorecard/1", "version": VERSION, "id": job.get("id") or out.get("id"), "score": score,
            "pass": score >= PASS_SHORT and twist_moved, "passmark": PASS_SHORT,
            "hard_gate": {"twist_has_real_motion": twist_moved}, "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checks": {k: {"ok": bool(checks.get(k)), "pts": SHORTS_RUBRIC[k], "evidence": ev.get(k, "")} for k in SHORTS_RUBRIC},
            "fixes": fixes}

def _load(path):
    with open(path) as f:
        return json.load(f)

def gate_short(root, ep, write=False):
    jp = os.path.join(root, "yt", "jobs", f"{ep}.json")
    op = os.path.join(root, "yt", "out", f"{ep}.json")
    rp = os.path.join(root, "yt", "jobs", f"{ep}.research.json")
    if not os.path.exists(jp) or not os.path.exists(op):
        return None, f"cannot judge {ep}: missing " + ", ".join(p for p in (jp, op) if not os.path.exists(p))
    job, out = _load(jp), _load(op)
    if out.get("error"):
        return None, f"cannot judge {ep}: the build failed ({str(out.get('error'))[:160]})"
    research = _load(rp) if os.path.exists(rp) else None
    card = scorecard(job, out, research)
    if write:
        sp = os.path.join(root, "yt", "out", f"{ep}.score.json")
        with open(sp, "w") as f:
            json.dump(card, f, indent=1)
        card["saved"] = os.path.relpath(sp, root)
    return card, None

def print_card(card):
    print(f"{card['id']}: {'PASS' if card['pass'] else 'FAIL'} {card['score']}/100 (pass {card['passmark']}+)")
    for k, c in card["checks"].items():
        print(f"  [{'x' if c['ok'] else ' '}] {c['pts']:>2} {k}: {c['evidence']}")
    if not card.get("hard_gate", {}).get("twist_has_real_motion", True):
        print("  hard gate: the twist line has no real motion (V8 rule 4): not a pass at any score")
    if card["fixes"]:
        print("  redo: " + ", ".join(card["fixes"]))
    if card.get("saved"):
        print("  saved " + card["saved"])

# ------------------------------------------------------------------------------------------------ cover
def gate_cover(new_path, recent, checks_arg="", min_distance=18, limit=20):
    paths = []
    for r in recent:
        if os.path.isdir(r):
            paths += [p for p in sorted(glob.glob(os.path.join(r, "*")), key=os.path.getmtime, reverse=True)
                      if p.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        else:
            paths += glob.glob(r)
    paths = [p for p in paths if os.path.abspath(p) != os.path.abspath(new_path)][:limit]
    rows = cover_distances(new_path, paths) if paths else []
    unique = all(d >= min_distance for _, d in rows)
    checks = {k: False for k in COVER_RUBRIC}
    for kv in [x for x in checks_arg.split(",") if x.strip()]:
        k, _, v = kv.partition("=")
        if k.strip() in checks:
            checks[k.strip()] = v.strip() in ("1", "true", "yes", "pass")
    checks["unique_vs_last_20_covers"] = unique and bool(paths)
    score, fixes = score_cover(checks)
    return {"schema": "cover-scorecard/1", "version": VERSION, "cover": new_path, "score": score, "pass": score >= PASS_COVER, "passmark": PASS_COVER,
            "compared": len(paths), "min_distance": min_distance, "unique": unique and bool(paths),
            "nearest": [{"path": p, "distance": d} for p, d in rows[:5]],
            "checks": checks, "fixes": fixes, "note": "" if paths else "no recent covers given: uniqueness cannot pass"}

# --------------------------------------------------------------------------------------------- selftest
def _synthetic(passing=True):
    prompt0 = "{rio} frozen on the couch at night, controller in hand, TV black"
    lines = [{"text": "Mom unplugged it at one HP... so I got revenge.", "image": {"prompt": prompt0, "motion": "push", "anim": True}, "pause": 0.25},
             {"text": "She did call me three times.", "image": {"prompt": "{mom} in the doorway, arms crossed", "motion": "panr"}, "pause": 0.25},
             {"text": "Sunday. Her show. One minute left.", "image": {"prompt": "{mom} leaning at the TV", "motion": "push"}, "pause": 0.25},
             {"text": "I pulled the Wi-Fi plug.", "image": {"prompt": "{rio} crouched by the router", "motion": "push"}, "pause": 0.25},
             {"text": "She just turned around... and smiled.", "image": {"prompt": "{mom} turning with a too-sweet smile", "motion": "orbit"}, "pause": 0.4},
             {"text": "New password: say sorry to your mother.", "image": {"prompt": "{rio} staring at his phone in horror", "motion": "punch", "anim": True}, "pause": 0.5},
             {"text": "Day four. Still not saying it, because...", "image": {"prompt": prompt0, "motion": "push"}, "pause": 0.05}]
    job = {"id": "selftest", "hook": "MOM UNPLUGGED IT AT 1 HP", "loop": True, "engine": "edge", "voice": "andrew", "speed": 1.03, "lines": lines}
    starts = [0.35, 3.6, 6.9, 9.8, 12.5, 15.9, 19.4]
    out = {"id": "selftest", "duration": 22.4, "lines": [[s, s + 2.6] for s in starts], "tts": "edge", "fakeTts": False,
           "warnings": ["line 0: real motion from the free animation lane", "line 5: real motion from the free animation lane"],
           "captions": {"cap_bottom_pct": 68.75, "hook_top_pct": 11.98, "source": "selftest"}}
    research = {"title_score": 74, "credits": 7}
    if not passing:
        job["hook"] = "A STORY ABOUT MY MOM"
        job["lines"][-1]["image"]["prompt"] = "something else"
        out["warnings"] = ["line 2: animation lane unavailable (rc 2); used the still"]
        out["lines"] = [[0.35, 6.2], [6.4, 9.0], [9.2, 12.0], [12.1, 14.0], [14.2, 20.5], [20.7, 24.0], [24.2, 26.0]]
        out["duration"] = 48.9
        out["tts"] = "kokoro"
        research = None
    return job, out, research

def selftest():
    job, out, research = _synthetic(True)
    card = scorecard(job, out, research)
    assert card["pass"] and card["score"] == 100, ("passing case should score 100", card["score"], card["fixes"])
    job, out, research = _synthetic(False)
    card = scorecard(job, out, research)
    expect = {"hook_motion_first_1_5s", "hook_text_question_or_shock", "ending_loops_to_start", "new_beat_every_3s",
              "real_animation_not_zoom", "natural_voice", "length_20_to_45s", "title_vidiq_score_70plus"}
    assert not card["pass"] and set(card["fixes"]) == expect, ("failing case fixes", card["fixes"])
    assert card["score"] == 15 + 5, card["score"]
    job, out, research = _synthetic(True)
    out["warnings"] = ["line 0: real motion from the free animation lane", "line 2: real motion from the free animation lane"]
    card = scorecard(job, out, research)
    assert card["score"] == 85 and not card["pass"] and card["hard_gate"]["twist_has_real_motion"] is False, ("twist without motion must not pass at 85", card["score"], card["pass"])
    # cover uniqueness: a colour swap of the same layout is NOT unique; a different layout is
    from PIL import Image, ImageDraw
    import tempfile, random
    d = tempfile.mkdtemp()
    def cover(path, bg, boxes, seed):
        im = Image.new("RGB", (600, 600), bg); dr = ImageDraw.Draw(im); rnd = random.Random(seed)
        for (x, y, w, h, col) in boxes:
            dr.rectangle([x, y, x + w, y + h], fill=col)
            for _ in range(40):
                px, py = x + rnd.randint(2, max(3, w - 3)), y + rnd.randint(2, max(3, h - 3))
                dr.rectangle([px, py, px + 6, py + 2], fill=(20, 20, 20))
        im.save(path)
    base_boxes = [(40, 60, 240, 300, (250, 250, 250)), (320, 60, 240, 300, (245, 245, 245)), (40, 400, 520, 150, (255, 255, 255))]
    cover(os.path.join(d, "old1.png"), (210, 60, 60), base_boxes, 1)
    cover(os.path.join(d, "swap.png"), (60, 120, 210), base_boxes, 1)                      # same layout, colour swapped
    cover(os.path.join(d, "new.png"), (235, 225, 200), [(60, 40, 480, 360, (255, 255, 255)), (200, 430, 200, 120, (30, 90, 50))], 7)
    assert not cover_is_unique(os.path.join(d, "swap.png"), [os.path.join(d, "old1.png")]), "colour swap must not count as unique"
    assert cover_is_unique(os.path.join(d, "new.png"), [os.path.join(d, "old1.png")]), "a different layout must count as unique"
    c = gate_cover(os.path.join(d, "new.png"), [d], "real_product_pages_fill_frame=1,big_count_badge=1,realistic_mockup=1,readable_at_thumbnail_size=1,matches_season_and_buyer=1")
    assert c["pass"] and c["score"] == 100, c
    c2 = gate_cover(os.path.join(d, "swap.png"), [os.path.join(d, "old1.png")], "real_product_pages_fill_frame=1,big_count_badge=1,realistic_mockup=1,readable_at_thumbnail_size=1,matches_season_and_buyer=1")
    assert not c2["pass"] and c2["fixes"] == ["unique_vs_last_20_covers"], c2
    print("selftest ok: Shorts 100 PASS / 20 FAIL with 8 named fixes; cover colour-swap caught, new layout passes")
    return 0

# -------------------------------------------------------------------------------------------------- CLI
def _find_root(start):
    p = os.path.abspath(start)
    for _ in range(6):
        if os.path.isdir(os.path.join(p, "yt")) and os.path.isdir(os.path.join(p, "studio")):
            return p
        p = os.path.dirname(p)
    return os.path.abspath(start)

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    if argv[0] == "--selftest":
        return selftest()
    if argv[0] == "blueprint":
        for t, what in COMMERCIAL_BLUEPRINT:
            print(f"{t:>9}  {what}")
        return 0
    if argv[0] == "short":
        if len(argv) < 2:
            print("usage: quality_gates.py short <ep id> [--write] [--root <repo>]"); return 2
        ep = argv[1]; write = "--write" in argv
        if not re.fullmatch(r"ep[A-Za-z0-9_-]{1,38}", ep):
            print(f"cannot judge {ep}: the Shorts gate is for ep* ids only"); return 2
        root = argv[argv.index("--root") + 1] if "--root" in argv else _find_root(os.path.dirname(__file__) or ".")
        try:
            card, err = gate_short(root, ep, write)
        except Exception as e:                      # a broken job or build file: cannot judge, never a pass
            print(f"cannot judge {ep}: {type(e).__name__}: {e}"); return 2
        if err:
            print(err); return 2
        print_card(card)
        return 0 if card["pass"] else 1
    if argv[0] == "cover":
        if len(argv) < 2:
            print("usage: quality_gates.py cover <new image> --recent <dir or files...> [--checks k=1,...] [--json]"); return 2
        new = argv[1]; recent = []; checks = ""; i = 2
        while i < len(argv):
            if argv[i] == "--recent":
                i += 1
                while i < len(argv) and not argv[i].startswith("--"):
                    recent.append(argv[i]); i += 1
                continue
            if argv[i] == "--checks":
                checks = argv[i + 1] if i + 1 < len(argv) else ""; i += 2; continue
            i += 1
        try:
            c = gate_cover(new, recent, checks)
        except Exception as e:                      # a file that is not an image: cannot judge, never a pass
            print(f"cannot judge {new}: {type(e).__name__}: {e}"); return 2
        if "--json" in argv:
            print(json.dumps(c, indent=1))
        else:
            print(f"cover: {'PASS' if c['pass'] else 'FAIL'} {c['score']}/100 (pass {c['passmark']}+) · compared with {c['compared']} covers · "
                  f"{'unique' if c['unique'] else 'NOT unique'} (min distance {c['min_distance']})")
            for r in c["nearest"]:
                print(f"  distance {r['distance']:>2}  {r['path']}")
            if c["fixes"]:
                print("  redo: " + ", ".join(c["fixes"]))
            if c["note"]:
                print("  " + c["note"])
        return 0 if c["pass"] else 1
    print("unknown command", argv[0]); return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
