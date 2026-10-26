#!/usr/bin/env python3
"""Predict and grade (Grayson, Oct 26, 2026: "get better and better and better").

Before something goes out, the crew writes a guess into its results line as pred_* tags:
  listings (Atlas, lane etsy):  pred_views7, pred_favs7, pred_sales7
  pins (Pixel, lane pins):      pred_impressions7, pred_saves7
  posts (Herald, lane social):  pred_views7
When the keeper fills the 7-day outcome (views, favs, sales, impressions, saves), this script grades
every guess and rewrites notebook/predictions.md with each agent's hit rate and a
calibration line ("your view guesses run 3x too high: divide by 3"). Agents read that line
before their next guess, so their guesses get closer every week.

    python3 factory/notebook/grade.py           # rewrite predictions.md, print the summary
    python3 factory/notebook/grade.py --check   # print only

Hit = the real number is within 2x of the guess (or both are 1 or less). Real numbers only:
a missing outcome is "not graded yet", never 0.
"""
import json
import os
import statistics
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.environ.get("NB_RESULTS", os.path.join(HERE, "results.jsonl"))
OUT = os.environ.get("NB_PREDICTIONS", os.path.join(HERE, "predictions.md"))

METRICS = {  # pred tag -> outcome key
    "pred_views7": "views", "pred_favs7": "favs", "pred_sales7": "sales",
    "pred_impressions7": "impressions", "pred_saves7": "saves",
}
AGENT = {"etsy": "atlas", "pins": "pixel", "social": "herald"}
MIN_FOR_CALIBRATION = 3


def load():
    rows = []
    if os.path.exists(RESULTS):
        with open(RESULTS) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return rows


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def hit(pred, real):
    if pred <= 1 and real <= 1:
        return True
    lo, hi = min(pred, real), max(pred, real)
    return lo > 0 and hi / lo <= 2


def grade(rows):
    g = {}      # (agent, metric) -> list of (pred, real, id)
    open_ = {}  # agent -> count of guesses still waiting
    for r in rows:
        tags, out = r.get("tags") or {}, r.get("outcome") or {}
        agent = AGENT.get(r.get("lane"), r.get("lane") or "?")
        for tag, key in METRICS.items():
            p = num(tags.get(tag))
            if p is None:
                continue
            real = num(out.get(key))
            if real is None:
                open_[agent] = open_.get(agent, 0) + 1
                continue
            g.setdefault((agent, key), []).append((p, real, str(r.get("id"))))
    return g, open_


def summary(g, open_):
    lines = []
    for (agent, key), xs in sorted(g.items()):
        hits = sum(hit(p, a) for p, a, _ in xs)
        ratios = [a / p for p, a, _ in xs if p > 0]
        cal = "too few graded to calibrate"
        if len(xs) >= MIN_FOR_CALIBRATION and ratios:
            m = statistics.median(ratios)
            if 0.67 <= m <= 1.5:
                cal = "on target: keep guessing the same way"
            elif m < 0.67:
                cal = f"guesses run {1/m:.1f}x too high: divide your {key} guess by {1/m:.1f}" if m > 0 else f"real {key} were 0 every time: guess 0 to 1 until one moves"
            else:
                cal = f"guesses run {m:.1f}x too low: multiply your {key} guess by {m:.1f}"
        lines.append({"agent": agent, "metric": key, "graded": len(xs), "hits": hits,
                      "rate": round(100 * hits / len(xs)), "calibration": cal,
                      "worst": max(xs, key=lambda t: abs(t[1] - t[0]))})
    return lines


def write(lines, open_):
    today = datetime.date.today().isoformat()
    out = ["# Predictions: how good are the crew's guesses (rebuilt by notebook/grade.py; do not edit)",
           "",
           "Every agent guesses its numbers before something goes out (pred_* tags, see grade.py).",
           "Before your next guess, read your Calibration line and adjust. Hit = within 2x.",
           "",
           f"_Updated {today}_", "",
           "## Calibration (read this before guessing)"]
    if not lines:
        out.append("- nothing graded yet: guesses fill in 7 days after things go out")
    for x in lines:
        out.append(f'- {x["agent"]} · {x["metric"]}: {x["calibration"]}')
    out += ["", "## Scores", "| Agent | Metric | Graded | Hits | Hit rate | Worst miss (guess -> real, id) |",
            "|---|---|---|---|---|---|"]
    for x in lines:
        p, a, i = x["worst"]
        out.append(f'| {x["agent"]} | {x["metric"]} | {x["graded"]} | {x["hits"]} | {x["rate"]}% | {p} -> {a} ({i}) |')
    out += ["", "## Waiting to be graded"]
    if not open_:
        out.append("- none")
    for agent, n in sorted(open_.items()):
        out.append(f"- {agent}: {n} guess(es)")
    with open(OUT, "w") as f:
        f.write("\n".join(out) + "\n")


def main():
    g, open_ = grade(load())
    lines = summary(g, open_)
    for x in lines:
        print(f'{x["agent"]} {x["metric"]}: {x["hits"]}/{x["graded"]} hits ({x["rate"]}%), {x["calibration"]}')
    print("waiting:", open_ or "none")
    if "--check" not in sys.argv:
        write(lines, open_)


if __name__ == "__main__":
    main()
