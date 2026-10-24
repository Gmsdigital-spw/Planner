"""Objective artifact checks for the inspection rubric (factory/learning, Phase 9).

Every check here looks at a REAL artifact on disk or a real copy / market record and returns
{"name", "ok": True | False | None, "note", "criterion", "severity"} where ok=None means "could not be checked
offline" (recorded as unknown, never as pass). Severities:
- "critical"  → a blocker: the item cannot be accepted whatever the total (rulesPass-type rules);
- "cap:<key>" → a downward cap from the rubric text (slop_fail, thumb_unreadable, layout_fault, side_by_side_fail);
- "minor"     → written next to the reviewer's rating as evidence; costs nothing by itself.

Nothing here raises a rating. Stdlib only; PIL and pypdf are used when importable (they are in the crews' sessions
and in the gateway runner), otherwise the dependent checks come back unknown and say so.
"""
from __future__ import annotations

import hashlib
import re
import struct
import typing as t
from pathlib import Path

AI_PHRASES = ("elevate", "unlock", "seamless", "game-changer", "game changer", "dive into", "whether you're", "whether you are",
              "look no further", "in today's busy world", "in today's fast-paced")
AI_LINE = "This design was created with AI assistance under the creative direction of the seller."
BANNED_CLAIMS = ("made $", "earn $", "guaranteed", "passive income in", "quit my job", "guaranteed sales", "bestseller", "top rated", "#1 ")
BRANDS = ("disney", "pixar", "marvel", "nintendo", "pokemon", "pokémon", "barbie", "hello kitty", "star wars", "harry potter",
          "minecraft", "fortnite", "roblox", "taylor swift", "grinch", "elf on the shelf", "peppa", "bluey", "paw patrol", "sonic")
LANE_PRICE = {  # 05-quill: single kits and planners 3.99-7.99, bundles 8-14, wall art 6.99-11.99; invitation spec 7.99-12.99 for sets
    ("planner", False): (3.99, 7.99), ("planner", True): (8.0, 14.0), ("game", False): (3.99, 7.99), ("game", True): (8.0, 14.0),
    ("wallart", False): (6.99, 11.99), ("wallart", True): (6.99, 14.0), ("invitation", False): (3.99, 12.99), ("invitation", True): (7.99, 14.0),
}
PAGE_RANGE_LANES = {"planner", "game"}  # preflight.md: 6-16 content pages + the thank-you page
COVER_SIZES = {(2000, 1500), (2000, 1600)}  # fun/varied covers; wall art real-frame covers
THUMB_INK_LIMIT = 0.08  # factory/qa/listing_audit.py SQUARE_CLIP: safe renders 0.00-0.02, clipped live covers 0.15-0.45
EMPTY_BAND_SHARE = 0.18  # preflight: "no empty band over about 15% of the page height at the bottom"


def _c(name: str, ok: t.Optional[bool], note: str = "", criterion: str = "file", severity: str = "minor") -> dict:
    return {"name": name, "ok": ok, "note": note[:300], "criterion": criterion, "severity": severity}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- images (stdlib size parsing + optional PIL)

def image_size(p: Path) -> tuple[int, int] | None:
    """Width, height of a JPEG or PNG from its headers (no PIL needed)."""
    try:
        data = p.read_bytes()
    except OSError:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return int(w), int(h)
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return int(w), int(h)
        i += 2 + seg_len
    return None


def _pil():
    try:
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False


def square_edge_ink(p: Path) -> float | None:
    """Share of 'ink' on the left edge of the centred square of a 4:3 cover (the SQUARE_CLIP proxy from
    factory/qa/listing_audit.py). Safe renders measure 0.00-0.02; covers whose title crosses the edge 0.15-0.45."""
    if not _pil():
        return None
    from PIL import Image
    import statistics as st
    im = Image.open(p).convert("RGB")
    w0, h0 = im.size
    if w0 <= h0:
        return 0.0  # a square or portrait image has no left band to clip
    im = im.resize((570, max(1, round(570 * h0 / w0))))
    w, h = im.size
    x0 = (w - h) // 2
    px = im.load()
    pts = [px[x, y] for x in range(max(0, x0 - 5), min(w, x0 + 5)) for y in range(int(h * .08), int(h * .40))]
    if not pts:
        return None
    med = [st.median(c[i] for c in pts) for i in range(3)]
    return round(sum(1 for q in pts if sum(abs(q[i] - med[i]) for i in range(3)) > 120) / len(pts), 3)


def color_stats(p: Path) -> dict | None:
    """bold / theme colour share and brightness (BLAND_COVER / DARK_COVER proxies from listing_audit.py) + a dhash."""
    if not _pil():
        return None
    import colorsys
    from PIL import Image
    im = Image.open(p).convert("RGB").resize((64, 48))
    px = list(im.getdata())
    hsv = [colorsys.rgb_to_hsv(r / 255, g / 255, b / 255) for r, g, b in px]
    bold = sum(1 for h, s, v in hsv if s > 0.45 and v > 0.35) / len(px)
    theme = sum(1 for h, s, v in hsv if s > 0.25 and v > 0.35 and not (0.04 < h < 0.14 and s < 0.6)) / len(px)
    bright = sum(v for _, _, v in hsv) / len(px)
    g = Image.open(p).convert("L").resize((33, 32))
    gp = list(g.getdata())
    dhash = "".join("1" if gp[y * 33 + x] > gp[y * 33 + x + 1] else "0" for y in range(32) for x in range(32))
    return {"bold": round(bold, 3), "theme": round(theme, 3), "bright": round(bright, 3), "dhash": dhash}


def bottom_empty_share(p: Path, band: float = EMPTY_BAND_SHARE) -> float | None:
    """How uniform the bottom `band` of a preview is (1.0 = a flat empty band). Proxy for 'half-empty photo'."""
    if not _pil():
        return None
    from PIL import Image
    import statistics as st
    im = Image.open(p).convert("RGB").resize((200, 150))
    w, h = im.size
    px = im.load()
    pts = [px[x, y] for x in range(w) for y in range(int(h * (1 - band)), h)]
    med = [st.median(c[i] for c in pts) for i in range(3)]
    return round(sum(1 for q in pts if sum(abs(q[i] - med[i]) for i in range(3)) <= 45) / len(pts), 3)


def check_images(cover: Path | None, previews: list[Path], lane: str = "game") -> list[dict]:
    out: list[dict] = []
    if not cover or not Path(cover).exists():
        out.append(_c("cover present", False, "no cover file", "images", "critical"))
        return out
    cover = Path(cover)
    previews = [Path(x) for x in previews]
    missing = [str(x) for x in previews if not x.exists()]
    if missing:
        out.append(_c("preview files present", False, "missing: " + ", ".join(missing)[:200], "images", "critical"))
    previews = [x for x in previews if x.exists()]
    out.append(_c("cover + 4 previews", len(previews) >= 4, f"cover + {len(previews)} previews", "images", "critical"))
    sz = image_size(cover)
    if sz is None:
        out.append(_c("cover is a real JPEG/PNG", False, "header not recognised", "images", "critical"))
    else:
        out.append(_c("cover 2000 px wide", sz[0] == 2000, f"{sz[0]}x{sz[1]}", "images", "critical"))
        out.append(_c("cover size is a cover size", tuple(sz) in COVER_SIZES, f"{sz[0]}x{sz[1]} (2000x1500 card or 2000x1600 wall art)", "images", "minor"))
    for x in previews:
        s = image_size(x)
        out.append(_c(f"preview 2000 px wide: {x.name}", None if s is None else s[0] == 2000, "unreadable header" if s is None else f"{s[0]}x{s[1]}", "images", "critical" if s is not None else "minor"))
    # duplicates: identical bytes always; near-identical pictures when PIL is there
    shas = {}
    for x in [cover] + previews:
        shas.setdefault(sha256_file(x), []).append(x.name)
    dups = [v for v in shas.values() if len(v) > 1]
    out.append(_c("no photo repeats another (bytes)", not dups, "; ".join(" = ".join(v) for v in dups) if dups else f"{len(shas)} distinct files", "images", "critical" if dups else "minor"))
    if _pil():
        stats = {x.name: color_stats(x) for x in [cover] + previews}
        names = list(stats)
        near = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = stats[names[i]], stats[names[j]]
                if a and b and sum(p != q for p, q in zip(a["dhash"], b["dhash"])) <= 40:
                    near.append(f"{names[i]} ~ {names[j]}")
        out.append(_c("no photo looks like another (dhash)", not near, "; ".join(near) if near else "all distinct", "images", "cap:layout_fault" if near else "minor"))
        ink = square_edge_ink(cover)
        if ink is not None:
            out.append(_c("cover title inside the centred square (edge ink)", ink <= THUMB_INK_LIMIT, f"edge ink {ink} (safe <= 0.02, clipped covers 0.15-0.45; proxy, confirm by eye)", "images",
                          "critical" if ink > THUMB_INK_LIMIT else "minor"))
        cs = stats[cover.name]
        if cs:
            if lane != "wallart":
                bland = cs["bold"] < 0.30 and cs["theme"] < 0.30
                out.append(_c("cover is bold / on-theme colour", not bland, f"bold {int(cs['bold']*100)}% theme {int(cs['theme']*100)}% (needs 30%+)", "images", "cap:slop_fail" if bland else "minor"))
            out.append(_c("cover bright enough for a thumbnail", cs["bright"] >= 0.35, f"brightness {cs['bright']}", "images", "cap:thumb_unreadable" if cs["bright"] < 0.35 else "minor"))
        for x in previews:
            e = bottom_empty_share(x)
            if e is not None:
                if e >= 0.99:
                    out.append(_c(f"no empty band at the bottom: {x.name}", False, f"bottom {int(EMPTY_BAND_SHARE*100)}% is {int(e*100)}% one flat colour", "images", "cap:layout_fault"))
                elif e >= 0.95:
                    out.append(_c(f"no empty band at the bottom: {x.name}", None, f"bottom band {int(e*100)}% flat: looks empty, confirm by eye", "images", "minor"))
                else:
                    out.append(_c(f"no empty band at the bottom: {x.name}", True, f"bottom band {int(e*100)}% flat", "images", "minor"))
    else:
        out.append(_c("cover title inside the centred square (edge ink)", None, "PIL not available here; check the 300 px thumb by eye", "images", "minor"))
    return out


# ---------------------------------------------------------------- PDF

def pdf_info(p: Path) -> dict:
    info: dict = {"exists": p.exists(), "pages": None, "fields": None, "last_text": None, "texts": None, "sha256": None, "bytes": None, "header": False, "lib": "none"}
    if not p.exists():
        return info
    data = p.read_bytes()
    info["bytes"] = len(data)
    info["sha256"] = hashlib.sha256(data).hexdigest()
    info["header"] = data[:5] == b"%PDF-"
    if not info["header"]:
        return info
    try:
        import pypdf  # type: ignore
        r = pypdf.PdfReader(str(p))
        info["pages"] = len(r.pages)
        try:
            info["fields"] = len(r.get_fields() or {})
        except Exception:
            info["fields"] = None
        try:
            texts = [(pg.extract_text() or "") for pg in r.pages]
            info["texts"] = texts
            info["last_text"] = texts[-1] if texts else ""
        except Exception:
            pass
        info["lib"] = "pypdf"
    except Exception:
        info["pages"] = len(re.findall(rb"/Type\s*/Page(?![s/a-zA-Z])", data)) or None
        info["fields"] = len(re.findall(rb"/FT\s*/", data))
        info["lib"] = "regex"
    return info


def check_pdf(path: Path | None, lane: str = "game", claims: dict | None = None) -> list[dict]:
    """claims: {"fillable": bool, "pages_planned": int, "spoiler_terms": [...], "public_pages": [page numbers 1-based]}"""
    claims = claims or {}
    out: list[dict] = []
    if not path:
        out.append(_c("pdf present", False, "no file path given", "file", "critical"))
        return out
    p = Path(path)
    info = pdf_info(p)
    if not info["exists"]:
        out.append(_c("pdf present", False, f"missing on disk: {p}", "file", "critical"))
        return out
    out.append(_c("pdf non-empty", (info["bytes"] or 0) > 0, f"{info['bytes']} bytes", "file", "critical"))
    out.append(_c("real pdf header", info["header"], "%PDF" if info["header"] else "header is not %PDF", "file", "critical"))
    if not info["header"]:
        return out
    pages = info["pages"]
    if pages is None:
        out.append(_c("page count", None, "could not count pages offline", "file", "minor"))
    else:
        if lane in ("planner", "game"):
            out.append(_c("3+ pages plus thank-you", pages >= 4, f"{pages} pages ({info['lib']})", "file", "critical"))
            out.append(_c("content pages inside 6 to 16", 7 <= pages <= 17, f"{pages - 1} content pages + thank-you", "file", "minor"))
        else:
            out.append(_c("page count", True, f"{pages} pages ({info['lib']}); lane {lane} has its own page rule", "file", "minor"))
        planned = claims.get("pages_planned")
        if planned:
            out.append(_c("page count matches the plan", pages == int(planned) + 1 or pages == int(planned), f"{pages} pages vs planned {planned} (+ thank-you)", "file", "minor"))
    if info["last_text"] is not None:
        ok = "made my day" in info["last_text"].lower() and "review" in info["last_text"].lower()
        out.append(_c("thank-you page last", ok, "found the thank-you text on the last page" if ok else "last page has no thank-you text (product-floor-v6.md THANK-YOU PAGE)", "file", "critical" if not ok else "minor"))
    else:
        out.append(_c("thank-you page last", None, "pypdf not available; open the last page by eye", "file", "minor"))
    if claims.get("fillable"):
        f = info["fields"]
        out.append(_c("fillable fields present", None if f is None else f > 0, "field count unknown" if f is None else f"{f} fields", "file", "critical" if f == 0 else "minor"))
    terms = [str(x).lower() for x in (claims.get("spoiler_terms") or []) if str(x).strip()]
    public = claims.get("public_pages") or []
    if terms and public and info["texts"]:
        hits = []
        for n in public:
            try:
                txt = info["texts"][int(n) - 1].lower()
            except (IndexError, ValueError):
                continue
            for term in terms:
                if term in txt:
                    hits.append(f"page {n}: '{term}'")
        out.append(_c("no spoiler on a host-facing page", not hits, "; ".join(hits)[:250] if hits else f"checked pages {public} for {terms}", "file", "minor"))
    elif terms:
        out.append(_c("no spoiler on a host-facing page", None, "needs pypdf text and public_pages", "file", "minor"))
    return out


# ---------------------------------------------------------------- copy, price, market

def check_copy(copy: dict | None, lane: str = "game", bundle: bool | None = None) -> list[dict]:
    out: list[dict] = []
    if not copy:
        out.append(_c("listing copy present", False, "no copy supplied", "copy", "critical"))
        return out
    title = str(copy.get("title") or "")
    tags = [str(x) for x in (copy.get("tags") or [])]
    desc = str(copy.get("description") or "")
    out.append(_c("title 1..140", 0 < len(title) <= 140, f"{len(title)} chars", "copy", "critical"))
    low = [x.lower().strip() for x in tags]
    out.append(_c("exactly 13 tags of 20 max, unique", len(tags) == 13 and all(len(x) <= 20 for x in tags) and len(set(low)) == len(low),
                  f"{len(tags)} tags, longest {max((len(x) for x in tags), default=0)}, {len(tags) - len(set(low))} duplicate(s)", "copy", "critical"))
    out.append(_c("no 'digital download' tag", "digital download" not in low, "", "copy", "minor"))
    out.append(_c("description 300+", len(desc) >= 300, f"{len(desc)} chars", "copy", "critical"))
    last = desc.strip().splitlines()[-1].strip() if desc.strip() else ""
    out.append(_c("AI line present, exact, last", last == AI_LINE, "ok" if last == AI_LINE else f"last line: {last[:80]!r}", "copy", "critical"))
    blob = " ".join([title, desc] + tags).lower()
    ai = [x for x in AI_PHRASES if x in blob]
    out.append(_c("no AI-sounding phrases", not ai, ", ".join(ai), "copy", "cap:slop_fail" if ai else "minor"))
    dashes = len(re.findall(r"\s—\s|—", desc + " " + title))
    out.append(_c("no em-dash runs", dashes <= 2, f"{dashes} em-dash(es)", "copy", "cap:slop_fail" if dashes > 2 else "minor"))
    brands = [b for b in BRANDS if re.search(r"\b" + re.escape(b) + r"\b", blob)]
    out.append(_c("original (no brand or character names)", not brands, ", ".join(brands), "copy", "critical" if brands else "minor"))
    claims = [c for c in BANNED_CLAIMS if c in blob]
    out.append(_c("no revenue / bestseller / review claims", not claims, ", ".join(claims), "copy", "cap:slop_fail" if claims else "minor"))
    emoji = len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", desc + title))
    out.append(_c("no emoji wall", emoji <= 3, f"{emoji} emoji", "copy", "cap:slop_fail" if emoji > 3 else "minor"))
    out.append(_c("autocomplete phrase checked", bool(copy.get("autocompleteChecked")), "copy.autocompleteChecked " + str(bool(copy.get("autocompleteChecked"))), "copy", "minor"))
    has_list = bool(re.search(r"\b\d+\s*(pages?|cards?|letters?|games?|puzzles?|prints?|tags?)\b", desc.lower()))
    out.append(_c("description names counts (page list)", has_list, "a count like '13 pages' found" if has_list else "no count found in the description", "copy", "minor"))
    price = copy.get("price")
    try:
        price_f = float(price)
    except (TypeError, ValueError):
        price_f = None
    out.append(_c("price > 0", price_f is not None and price_f > 0, str(price), "price", "critical"))
    if price_f:
        if bundle is None:
            bundle = "bundle" in title.lower()
        rng = LANE_PRICE.get((lane, bool(bundle)))
        if rng:
            out.append(_c("price inside the lane range", rng[0] <= price_f <= rng[1], f"${price_f:.2f} vs {rng[0]}-{rng[1]} ({'bundle' if bundle else 'single'} {lane})", "price", "minor"))
        else:
            out.append(_c("price inside the lane range", None, f"no range on file for lane {lane}", "price", "minor"))
        cents = round(price_f * 100) % 100
        out.append(_c("price ends .99 or .49", cents in (99, 49), f"${price_f:.2f}", "price", "minor"))
    return out


def market_listings(market: t.Any) -> list[dict]:
    """Accepts product.market (list or {listings:[...]}), brief.marketProof, or a list of {url, itemReviews|reviews, price}."""
    if market is None:
        return []
    rows = market.get("listings") if isinstance(market, dict) else market
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        rev = r.get("itemReviews", r.get("reviews", r.get("review_count")))
        try:
            rev = int(str(rev).replace(",", "").replace("+", "")) if rev is not None else None
        except ValueError:
            rev = None
        out.append({"url": str(r.get("url") or r.get("link") or ""), "reviews": rev, "price": r.get("price"), "what": r.get("whatItHas") or r.get("what") or ""})
    return out


def check_market(market: t.Any, gap: str | None = None) -> list[dict]:
    rows = market_listings(market)
    gap = gap or (market.get("gap") if isinstance(market, dict) else None)
    opened = [r for r in rows if "etsy.com/listing/" in r["url"] or "etsy.com/" in r["url"] and "/listing/" in r["url"]]
    big = [r for r in opened if r["reviews"] is not None and r["reviews"] >= 100]
    out = [_c("3 opened Etsy item pages recorded", len(opened) >= 3, f"{len(opened)} opened item page(s) of {len(rows)} rows", "market", "minor"),
           _c("at least one rival with 100+ item reviews", len(big) >= 1, f"{len(big)} with 100+ reviews" + (" (" + ", ".join(str(r['reviews']) for r in big[:3]) + ")" if big else ""), "market", "minor"),
           _c("review counts recorded for every opened page", all(r["reviews"] is not None for r in opened) if opened else None, "", "market", "minor"),
           _c("gap written in one line", bool(gap and str(gap).strip()), (str(gap)[:120] if gap else "no gap line"), "market", "minor")]
    if not opened:
        out.append(_c("market evidence exists", False, "no opened item page: the market rating cannot be scored from evidence", "market", "unscored"))
    return out


# ---------------------------------------------------------------- composition

CAP_TABLE = {"slop_fail": {"images": 12, "polish": 6}, "thumb_unreadable": {"images": 14}, "layout_fault": {"images": 14, "polish": 7}, "side_by_side_fail": {"total": 80}}


def check_product(*, pdf: Path | None = None, cover: Path | None = None, previews: list[Path] | None = None, copy: dict | None = None,
                  market: t.Any = None, gap: str | None = None, lane: str = "game", claims: dict | None = None,
                  slop: dict | None = None, side_by_side: bool | None = None, rules_pass: bool | None = None, partial: bool = False) -> dict:
    """Run every objective check and fold in the reviewer's own slop / side-by-side verdicts (those need eyes).

    partial=True (a legacy score doc, or a re-check of one piece): an artifact that was not handed over is recorded as
    unknown instead of a blocker. Returns {"checks", "blockers", "caps", "unscored", "notes": {criterion: [lines]}, "summary"}."""
    checks: list[dict] = []
    if pdf or not partial:
        checks += check_pdf(pdf, lane, claims)
    else:
        checks.append(_c("pdf checks", None, "no file handed over (partial check)", "file", "minor"))
    if cover or previews or not partial:
        checks += check_images(cover, previews or [], lane)
    else:
        checks.append(_c("image checks", None, "no images handed over (partial check)", "images", "minor"))
    if copy or not partial:
        checks += check_copy(copy, lane, (claims or {}).get("bundle"))
    else:
        checks.append(_c("copy checks", None, "no copy handed over (partial check)", "copy", "minor"))
    if market is not None or not partial:
        checks += check_market(market, gap)
    else:
        checks.append(_c("market checks", None, "no market record handed over (partial check)", "market", "minor"))
    if slop is not None:
        fails = [str(x) for x in (slop.get("fails") or [])]
        ok = bool(slop.get("pass")) and not fails
        checks.append(_c("slop check (reviewer, by eye)", ok, "; ".join(fails)[:250] if fails else "pass", "images", "cap:slop_fail" if not ok else "minor"))
    else:
        checks.append(_c("slop check (reviewer, by eye)", None, "not recorded: the side-by-side and slop lines need eyes", "images", "minor"))
    if side_by_side is not None:
        checks.append(_c("side-by-side vs every live cover (reviewer, by eye)", bool(side_by_side), "" if side_by_side else "reads as the same template as a live cover", "images", "cap:side_by_side_fail" if not side_by_side else "minor"))
    if rules_pass is False:
        checks.append(_c("rulesPass (reviewer)", False, "reviewer recorded rulesPass false", "file", "critical"))
    blockers, caps, unscored = [], {}, set()
    for c in checks:
        if c["ok"] is False:
            if c["severity"] == "critical":
                blockers.append(f"{c['name']}: {c['note']}" if c["note"] else c["name"])
            elif c["severity"].startswith("cap:"):
                key = c["severity"][4:]
                for crit, mx in CAP_TABLE.get(key, {}).items():
                    caps[crit] = min(caps.get(crit, mx), mx)
            elif c["severity"] == "unscored":
                unscored.add(c["criterion"])
    # a failed slop check is also a blocker by the rubric's own words ("it fails and gets fixed in the same run")
    if any(c["name"].startswith("slop check") and c["ok"] is False for c in checks):
        blockers.append("slop check failed: " + next(c["note"] for c in checks if c["name"].startswith("slop check") and c["ok"] is False))
    notes: dict[str, list[str]] = {}
    for c in checks:
        mark = "ok" if c["ok"] else ("FAIL" if c["ok"] is False else "unknown")
        notes.setdefault(c["criterion"], []).append(f"{c['name']}: {mark}" + (f" ({c['note']})" if c["note"] else ""))
    failed = [c for c in checks if c["ok"] is False]
    unknown = [c for c in checks if c["ok"] is None]
    return {"checks": checks, "blockers": blockers, "caps": caps, "unscored": sorted(unscored), "notes": notes,
            "summary": {"checks": len(checks), "failed": len(failed), "unknown": len(unknown), "critical": len(blockers), "caps": caps}}


def check_post(*, channel: str, caption: str = "", link: str | None = None, title: str | None = None, returned_id: str | None = None,
               slop_gate: str | None = None, facts_checked: bool | None = None) -> dict:
    """Objective checks for a Herald post (herald-post-v6). Facts and frames need eyes; limits and links do not."""
    checks: list[dict] = []
    limits = {"instagram": 2200, "facebook": 63206, "tiktok": 150, "youtube_shop": 5000, "youtube": 5000}
    lim = limits.get(channel)
    if lim:
        checks.append(_c(f"caption within {channel} limit", len(caption) <= lim, f"{len(caption)} chars of {lim}", "platform", "critical" if len(caption) > lim else "minor"))
    if title is not None and channel.startswith("youtube"):
        checks.append(_c("YouTube title 100 max", 0 < len(title) <= 100, f"{len(title)} chars", "platform", "critical" if len(title) > 100 else "minor"))
    if channel in ("facebook", "youtube_shop", "youtube"):
        ok = bool(link) and "etsy.com" in (link or "")
        checks.append(_c("link points to Etsy", ok, link or "no link", "search_link", "critical" if not ok else "minor"))
    blob = (caption + " " + (title or "")).lower()
    ai = [x for x in AI_PHRASES if x in blob]
    checks.append(_c("no AI-sounding phrases", not ai, ", ".join(ai), "platform", "critical" if ai else "minor"))
    brands = [b for b in BRANDS if re.search(r"\b" + re.escape(b) + r"\b", blob)]
    checks.append(_c("original (no brand or character names)", not brands, ", ".join(brands), "compliance", "critical" if brands else "minor"))
    claims = [c for c in BANNED_CLAIMS if c in blob]
    checks.append(_c("no invented claims", not claims, ", ".join(claims), "accuracy", "critical" if claims else "minor"))
    if slop_gate is not None:
        checks.append(_c("slop gate (reviewer, frames by eye)", slop_gate == "pass", slop_gate, "visual", "critical" if slop_gate != "pass" else "minor"))
    else:
        checks.append(_c("slop gate (reviewer, frames by eye)", None, "not recorded", "visual", "minor"))
    checks.append(_c("facts checked against the listing", facts_checked, "" if facts_checked is not None else "not recorded", "accuracy", "critical" if facts_checked is False else "minor"))
    if returned_id is not None:
        checks.append(_c("returned id present when claiming posted", bool(str(returned_id).strip()), str(returned_id)[:40], "compliance", "critical" if not str(returned_id).strip() else "minor"))
    blockers = [f"{c['name']}: {c['note']}" if c["note"] else c["name"] for c in checks if c["ok"] is False and c["severity"] == "critical"]
    notes: dict[str, list[str]] = {}
    for c in checks:
        mark = "ok" if c["ok"] else ("FAIL" if c["ok"] is False else "unknown")
        notes.setdefault(c["criterion"], []).append(f"{c['name']}: {mark}" + (f" ({c['note']})" if c["note"] else ""))
    return {"checks": checks, "blockers": blockers, "caps": {}, "unscored": [], "notes": notes,
            "summary": {"checks": len(checks), "failed": sum(1 for c in checks if c["ok"] is False), "unknown": sum(1 for c in checks if c["ok"] is None), "critical": len(blockers), "caps": {}}}
