"""Frozen rubrics, evidence-linked rating aggregation and the legacy-score adapter (factory/learning, Phase 9).

Rules baked in (shared/rules.md "Honesty" and the task that added this package):
- The rubric the crew already grades with is FROZEN here, weights and target unchanged, so every before/after
  comparison is on the same scale. Nothing in this file lowers a target or rewrites an old score.
- `assess()` only combines ratings that come with written evidence. A criterion with no rating or no evidence
  stays MISSING: the total is None and the item cannot pass. Blockers (critical failures) block acceptance even
  when the weighted total is high. Caps only ever move a rating DOWN; nothing here moves one up.
- A legacy score document (products/<id>.score as the Night Shift writes it) goes through ONE explicit adapter,
  `from_legacy_score()`, which keeps the points exactly as recorded and reports any arithmetic that does not add
  up instead of fixing it.
- Other scales (the Studio Judge's 1-10, the Idea Judge's /30) are registered as their OWN rubric ids with the
  adapter written next to them, so their numbers never mix with the product rubric in any statistic.
"""
from __future__ import annotations

import hashlib
import json
import math
import typing as t

# ---------------------------------------------------------------- helpers (from the reference, unchanged semantics)

def packed(value: t.Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, default=str)


def digest(value: t.Any) -> str:
    return hashlib.sha256(packed(value).encode()).hexdigest()


def number(value: t.Any, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("Expected a finite number")
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Number {value} outside allowed range {low}..{high}")
    return float(value)


# ---------------------------------------------------------------- the rubrics (frozen)

FALLBACK_RUBRIC = {"correctness": 25, "evidence": 20, "completion": 20, "usefulness": 20, "usability": 10, "efficiency": 5}

RUBRICS: dict[str, dict] = {
    # The Night Shift's inspection rubric (stages/night-shift/references/rubric.md). Points per criterion ARE the
    # weights (they sum to 100), so the weighted total equals the sum of points the crew already writes.
    "etsy-product-r2": {
        "name": "Inspection rubric 2 (Atlas, Night Shift stage 07)",
        "criteria": {"file": 25, "copy": 20, "images": 20, "market": 15, "price": 10, "polish": 10},
        "target": 92, "aim": 95, "legacy_rubric_field": 2,
        "source": "factory/stages/night-shift/references/rubric.md",
        # downward caps the rubric text already imposes; applied by code, never by the reviewer's mood
        "caps": {
            "slop_fail": {"images": 12, "polish": 6},          # "A fail caps images at 12 and polish at 6"
            "thumb_unreadable": {"images": 14},                # "title or count not readable at 300 px: at most 14"
            "layout_fault": {"images": 14, "polish": 7},       # "overlap, clipped text, cramped spacing or a cheap cover"
            "side_by_side_fail": {"total": 80},                # specs/cover-styles.md Oct 23: same template as a live cover = cap 80
        },
        "critical": ["rulesPass false", "slop check fail", "file missing or unreadable", "fewer than cover + 4 previews",
                     "title over 140", "not exactly 13 tags of 20 max", "description under 300", "brand, character or copied content"],
    },
    # Herald's post QC (stages/herald/references/qc.md section B). Same 92 target, its own criteria.
    "herald-post-v6": {
        "name": "Social post QC (Herald stage 06, graded by Atlas)",
        "criteria": {"accuracy": 25, "fit": 20, "platform": 15, "hook_cta": 10, "visual": 10, "search_link": 10, "compliance": 10},
        "target": 92, "aim": 95,
        "source": "factory/stages/herald/references/qc.md",
        "caps": {},
        "critical": ["slop gate fail", "wrong fact", "broken or non-Etsy link", "invented claim", "against platform rules"],
    },
    # The Studio Judge (stages/studio/references/episode-rules.md "Two drafts"): hook/story/twist/logic 1-10 each.
    # ADAPTER (documented): each 1-10 score is kept as points out of 10 (weights 25 each when normalised to 100);
    # the bar is NOT 92: "every score 7+" is a blocker, and "beat the last posted episode" is a blocker when the
    # caller passes the score to beat. target 70 = a 7.0 average; it exists only so the row has a number to pass.
    "studio-judge-x10": {
        "name": "Studio Judge, two drafts (hook, story, twist, logic 1-10)",
        "criteria": {"hook": 10, "story": 10, "twist": 10, "logic": 10},
        "target": 70, "aim": 82.5, "adapter": "points /10 per criterion; weights equal; blockers: any score under 7, average not above the score to beat",
        "source": "factory/stages/studio/references/episode-rules.md",
        "caps": {}, "critical": ["any score under 7", "no emotional beat drawn", "repeats a premise"],
    },
    # The Idea Judge's brief score (/30, six 0-5 scores; approve at 21+). ADAPTER: points /5 per criterion, target 70 = 21/30.
    "idea-brief-30": {
        "name": "Idea brief score (Scout + Idea Judge, /30)",
        "criteria": {"demand": 5, "competition": 5, "timing": 5, "shopFit": 5, "buildable": 5, "price": 5},
        "target": 70, "aim": 80, "adapter": "points /5 per criterion; approve needs demand, timing, buildable 4+ and shopFit 3+ (blockers)",
        "source": "factory/stages/night-shift/02-judge/CONTEXT.md",
        "caps": {}, "critical": ["fewer than 2 opened item pages with 100+ reviews", "no written gap", "trademark / lyrics / character"],
    },
}


def rubric(rubric_id: str | None = None, custom: dict | None = None) -> dict:
    """The frozen rubric by id, a caller-supplied one, or the generic fallback (only when the project has none)."""
    if custom:
        r = dict(custom)
        r.setdefault("name", "custom")
        r.setdefault("target", 95)
        r.setdefault("caps", {})
        r["criteria"] = dict(r.get("criteria") or r.get("weights") or {})
        return r
    if rubric_id is None:
        return {"name": "fallback (generic)", "criteria": dict(FALLBACK_RUBRIC), "target": 95, "caps": {}, "source": "reference agent_learning.py"}
    if rubric_id not in RUBRICS:
        raise ValueError(f"unknown rubric {rubric_id!r}; known: {sorted(RUBRICS)}")
    return RUBRICS[rubric_id]


def weights_of(r: dict) -> dict[str, float]:
    """Criterion weights that sum to 100 (points scaled when the rubric's points do not already sum to 100)."""
    crit = {k: number(v, 0.000001, 1000) for k, v in r["criteria"].items()}
    total = sum(crit.values())
    if total <= 0:
        raise ValueError("Rubric needs positive criteria")
    return {k: v * 100.0 / total for k, v in crit.items()}


def rubric_id_of(r: dict) -> str:
    """Stable id: weights + target only, so a renamed rubric with the same numbers keeps its history."""
    return digest({"weights": weights_of(r), "target": number(r.get("target", 95), 0, 100)})[:16]


# ---------------------------------------------------------------- assess (reference semantics, points-aware)

def assess(ratings: dict, rubric_ref: str | dict | None = None, blockers: t.Sequence[str] = (), target: float | None = None,
           caps: dict | None = None, points: bool = True) -> dict:
    """Weight external ratings. An evidence string is NOT evidence verification; that happens upstream (checks.py).

    ratings: {criterion: {"points": p, "evidence": "..."}} when points=True (p in 0..max points of that criterion),
             or {criterion: {"score": 0..100, "evidence": "..."}} when points=False (the reference's shape).
    caps: {criterion: max_points} and/or {"total": max_total} applied DOWNWARD only; every cap that bit is listed.
    """
    r = rubric(rubric_ref) if isinstance(rubric_ref, str) or rubric_ref is None else rubric(custom=rubric_ref)
    crit = {k: number(v, 0.000001, 1000) for k, v in r["criteria"].items()}
    weights = weights_of(r)
    tgt = number(r.get("target", 95) if target is None else target, 0, 100)
    if not isinstance(ratings, dict) or set(ratings) - set(weights):
        raise ValueError(f"Ratings must use this rubric's criteria {sorted(weights)}; got {sorted(ratings) if isinstance(ratings, dict) else type(ratings)}")
    if not isinstance(blockers, (list, tuple)) or any(not isinstance(b, str) or not b.strip() for b in blockers):
        raise ValueError("Blockers must be a list of explanations")
    blockers = list(blockers)
    caps = dict(caps or {})
    missing, gaps, total, capped, final_points = [], [], 0.0, [], {}
    for name, weight in weights.items():
        rating = ratings.get(name)
        if not isinstance(rating, dict):
            missing.append(name)
            continue
        evidence = rating.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            missing.append(name)
            continue
        if points:
            if rating.get("points") is None:
                missing.append(name)
                continue
            p = number(rating["points"], 0, crit[name])
        else:
            if rating.get("score") is None:
                missing.append(name)
                continue
            p = number(rating["score"], 0, 100) * crit[name] / 100.0
        cap = caps.get(name)
        if cap is not None and p > number(cap, 0, crit[name]):
            capped.append({"criterion": name, "from": p, "to": float(cap)})
            p = float(cap)
        final_points[name] = p
        total += weight * (p / crit[name])
        gaps.append({"criterion": name, "points": p, "max": crit[name], "lost_points": round(weight * (1 - p / crit[name]), 4), "evidence": evidence.strip()[:400]})
    if "total" in caps and not missing and total > number(caps["total"], 0, 100):
        capped.append({"criterion": "total", "from": round(total, 4), "to": float(caps["total"])})
        total = float(caps["total"])
    score = None if missing else round(total, 4)
    return {
        "score": score,
        "passed": bool(not missing and not blockers and score is not None and score >= tgt),
        "target": tgt,
        "aim": r.get("aim"),
        "missing": missing,
        "blockers": blockers,
        "capped": capped,
        "gaps": sorted(gaps, key=lambda g: g["lost_points"], reverse=True),
        "rubric_id": rubric_id_of(r),
        "rubric_name": r.get("name"),
        "weights": weights,
        "points": final_points,
        "ratings": ratings,
    }


# ---------------------------------------------------------------- legacy adapter

LEGACY_FIELDS = ("file", "copy", "images", "market", "price", "polish")


def from_legacy_score(score_doc: dict, product_ref: str = "") -> dict:
    """products/<id>.score  →  {"ratings", "blockers", "discrepancies"} for assess('etsy-product-r2').

    Points are copied exactly as recorded. Evidence is the verdict / slop fails the crew wrote (so a legacy row is
    scored but marked legacy). rulesPass false and a failed slopCheck become blockers. If the recorded total does
    not equal the sum of the six parts, that is reported in `discrepancies`; nothing is corrected silently."""
    if not isinstance(score_doc, dict):
        raise ValueError("score document must be an object")
    verdict = str(score_doc.get("verdict") or "").strip()
    slop = score_doc.get("slopCheck") or {}
    fails = [str(x) for x in (slop.get("fails") or [])]
    base_ev = f"legacy products.score {product_ref}".strip() + (f": {verdict[:200]}" if verdict else " (no verdict recorded)")
    ratings, missing = {}, []
    for k in LEGACY_FIELDS:
        v = score_doc.get(k)
        if v is None:
            missing.append(k)
            continue
        ev = base_ev
        if k in ("images", "polish") and fails:
            ev += " | slop fails: " + "; ".join(fails)[:200]
        ratings[k] = {"points": float(v), "evidence": ev}
    blockers = []
    if score_doc.get("rulesPass") is False:
        blockers.append("rulesPass false (legacy score doc)")
    if slop and slop.get("pass") is False:
        blockers.append("slop check failed: " + ("; ".join(fails)[:300] or "no reasons recorded"))
    discrepancies = []
    recorded = score_doc.get("total")
    parts = [score_doc.get(k) for k in LEGACY_FIELDS]
    if recorded is not None and all(p is not None for p in parts) and abs(float(recorded) - sum(float(p) for p in parts)) > 1e-9:
        discrepancies.append(f"recorded total {recorded} != sum of parts {sum(float(p) for p in parts)}")
    if str(score_doc.get("rubric", "2")) not in ("2", "2.0"):
        discrepancies.append(f"rubric field is {score_doc.get('rubric')!r}, not 2: scored before Oct 19, 2026 (pass was 85/90); kept apart")
    if missing:
        discrepancies.append("missing criteria in legacy doc: " + ", ".join(missing))
    return {"ratings": ratings, "blockers": blockers, "discrepancies": discrepancies, "legacy_total": recorded,
            "slop": {"pass": slop.get("pass"), "fails": fails} if slop else None}


def legacy_caps(score_doc: dict) -> dict:
    """Caps the rubric text imposes on a legacy doc: a failed slop check caps images 12 / polish 6 (downward only)."""
    slop = score_doc.get("slopCheck") or {}
    return dict(RUBRICS["etsy-product-r2"]["caps"]["slop_fail"]) if slop and slop.get("pass") is False else {}


# ---------------------------------------------------------------- anchors (reviewer-facing, no target stated)

ANCHORS: dict[str, dict[str, list[str]]] = {
    "etsy-product-r2": {
        "file": [
            "25: every page full and framed, nothing within 0.25 in of a box edge, every answer key / uniqueness claim verified by code, fillable fields typed to max length and rendered clean, page count inside the lane range with the thank-you page last, no spoiler on a host-facing page.",
            "22-23: one or two of: a page with an empty band over ~15% at the bottom, a footer or signature touching its box, a field that clips at max length, a cover page with an empty band (Oct 23: bingo 23, word search 23, Santa Mail 23, murder mystery 22).",
            "18-20: a layout fault on several pages, a key not verified, or filler / repeated content on a page.",
            "under 18: the file is incomplete, does not open, or breaks the lane's file rules.",
        ],
        "copy": [
            "20: title opens with a phrase shoppers really type (autocomplete checked and recorded), 13 real search-phrase tags, description opens with what it is and who it is for, an exact page list with counts, how to print/edit, the AI line last, no AI phrases, no em-dash runs.",
            "18-19: one of: autocomplete not checked (phrase taken from a search page), a generic opening line, a tag that only describes one page, a claim the file does not back (Oct 23: 18, 18, 18, 19).",
            "15-17: generic description without the page list, keyword soup, or a title that does not lead with the buyer phrase.",
            "under 15: a limit broken (title, tags, description) or an invented claim.",
        ],
        "images": [
            "20: cover in a layout family not on the last 5 covers, real pages the biggest thing (about 40%+ of the centred square), title and count readable at 300 px, photos 2-5 each show something different with pages filling the frame, text inside x 260-1740.",
            "17-19: photos 2-5 a little small or one repeats the cover's page; cover hero around 38-41% of the square (Oct 23: 17, 18, 18, 19).",
            "14 at most: title or count not readable at 300 px, or overlap / clipped text / cramped spacing / a cheap-looking cover (rubric rule).",
            "12 at most: the slop check failed on any line (rubric rule).",
        ],
        "market": [
            "15: three opened Etsy item pages with 100+ item reviews each, prices and contents recorded, and one plain line naming the gap that is visible in our file, photos and copy.",
            "13-14: two 100+ review rivals opened and a written gap (Oct 23 Santa Mail 13: the only no-Canva PDF rival had 58 reviews).",
            "11-12: one 100+ rival or only search cards; the gap is asserted, not visible (Oct 23: bingo 11, murder mystery 11).",
            "9-10: no opened 100+ review rival, non-Etsy links, a 'free everywhere' lane (Oct 23 word search 9).",
        ],
        "price": [
            "10: inside the lane range, justified in one line against the three opened rivals' prices and contents.",
            "8-9: inside the range but justified against fewer rivals or a thinner comparison (Oct 23: 8, 8, 9, 9).",
            "under 8: outside the lane range, or no justification at all.",
        ],
        "polish": [
            "10: one font family and palette across every page, same margins everywhere, no cramped or half-empty page, cover and photos consistent with the pages.",
            "8-9: one small inconsistency (a margin, a weight, one slightly tight block) (Oct 23: 8, 9, 9).",
            "7 at most: any layout fault or a cheap-looking cover (rubric rule). 6 at most: the slop check failed.",
        ],
    },
}


def anchors_markdown(rubric_id: str = "etsy-product-r2") -> str:
    """Reviewer-facing anchors. Deliberately omits the pass threshold: the reviewer grades, the code decides."""
    r = RUBRICS[rubric_id]
    out = [f"# Criterion anchors: {r['name']}", "",
           "For the reviewer (a FRESH worker that did not build the item). Grade each criterion in points with one line",
           "of evidence you can point at (a page, a photo, a URL, a measured number). Do not look up or aim for a pass",
           "mark: `python3 factory/learning/learn.py score` combines the points, applies the rubric's caps and decides.", ""]
    for crit, mx in r["criteria"].items():
        out.append(f"## {crit} (0 to {mx})")
        for line in ANCHORS.get(rubric_id, {}).get(crit, []):
            out.append(f"- {line}")
        out.append("")
    out += ["## What the code checks on its own (you do not need to re-measure these)",
            "File exists and is a real PDF; page count; thank-you page last; cover + 4 previews at 2000 px wide; no repeated photo;",
            "cover title inside the centred square (edge-ink proxy); bold colour share; empty band at the bottom of a preview;",
            "title / tags / description limits; the AI line last; AI phrases; em-dash runs; brand names; revenue claims; price",
            "inside the lane range; market evidence present (opened item pages with review counts). Each check writes its",
            "result next to your rating; a critical failure blocks acceptance whatever the total.", ""]
    return "\n".join(out)
