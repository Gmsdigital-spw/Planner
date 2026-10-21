# 01 Scout: Idea Engine and briefs (room "lab", then "intel")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Spec | `../../../specs/product-floor-v6.md` | Idea Engine, lanes, Holiday Mode, SALES PUSH | The standing order for ideas |
| Skill | `../../../skills/scout/SKILL.md` | Full file | Scout's checklist and lessons |
| Skill | `../../../skills/judge_ideas/SKILL.md` | Full file | The Idea Judge works in this stage |
| Lessons | `../../../LESSONS.md` | Full file | Numbers-only lessons |
| Database | briefs (newest 60), products (newest 60) | title, niche, lane, status, rejectReason | Never repeat a niche; learn from rejections |
| Database | sprint/main, lessons (status active), ideas (newest 3) | flags, text | Score shopFit from real results |
| Reference | `../references/wall-art.md` | "Scout" section only | Only when writing the wall art idea |

## Process
1. Set crew/scout working ("Researching: <niche>"). Read the inputs above. The 60 briefs and
   60 products come in through `out_dir` (database.md "BULK READS"): save them to a folder and
   build `../output/catalog.md` with Python, one line per item (id, lane, status, decidedBy,
   score, title, rejectReason if any). Read the catalog, never the raw docs.
2. Research with WebSearch (several searches in one turn): what digital printables are selling
   now on Etsy and Pinterest, seasonal timing from today's date, price points, competition.
3. Idea Engine (spec): write 15 ideas across the lanes (planner, wallart, mugwrap, sticker,
   invitation, game). Holiday Mode: inside a holiday's window and more than 10 days out, the
   spec's share of ideas aims at that holiday (Christmas 60%); inside 10 days nothing new for it.
   One idea each run is a wall art set (see wall-art.md, Scout section).
4. Products must be buildable: text-based printables made with text, tables, checklists, lists
   and simple boxes (planners, trackers, checklists, party games, worksheets, journals,
   budgets, meal plans, kids activities, templates), or the other lanes to the spec's sizes.
   No art-heavy products except the wall art lane, no characters, brands, trademarks, medical
   or legal claims.
5. The Idea Judge (judge_ideas, in this stage, with the auto-approver's reject rules from
   stage 02's Process step 2) gives each idea a verdict: drop, hold (good but no slot or window
   not open yet), or brief for exactly 3 (the strongest; one a wall art set; SALES PUSH: until
   Dec 15 at least 2 of the 3 are Christmas or New Year products, each modeled on a real
   bestselling listing in its evidence). Then research the 3 and file them as
   full briefs: briefs/<id> {title, niche, lane, buyer, competition, season, priceRange,
   score:{demand, competition, timing, shopFit, buildable, price} each 0 to 5, total (0 to 30),
   evidence:[{label, url}] (2 or more real links you really opened), summary (plain text),
   status:"proposed", createdAt, source:"Scout · Night Shift <day>"}. Never invent sales
   figures; mark estimates as estimates.
6. Write ideas/<day key> {day, createdAt, holidayMode, target, items:[{title, lane, buyer,
   holiday, why, verdict, reason, briefId}], note, source}.
7. Intel refresh (room "intel"), only if intel/etsy or intel/pinterest has lastChecked older
   than 14 days or a docs entry still "unverified": open each doc URL with WebFetch (WebSearch
   first if it fails), mark it verified with checkedAt (or leave it unverified with a note),
   refresh rules ONLY from what the official page says, in plain sentences. Never state ranking
   weights or hidden signals; unproven goes in unknowns. Append one history line. Hard cap 8
   minutes; over it, skip and log.
8. Append one JSON line per idea verdict to `factory/scores.jsonl`: {"d":"<day key>",
   "agent":"judge_ideas","kind":"idea","item":<title>,"score":<total or null>,"metric":<verdict>}.
9. Set crew/scout idle. Log one event (crew "Scout", "Judged 15 ideas: 3 briefs, N held, N
   dropped") and write the counts under `## Scout` in `../output/<day key>-run.md`.

## Audit

| Check | Pass condition |
|-------|---------------|
| Evidence | Every brief has 2 or more links you opened this run |
| No repeats | No brief shares buyer + use with a product or a brief from the last 60 |
| Lanes | Every idea and brief carries a lane |
| Holiday share | The spec's share holds, or the note says why not |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| 15 ideas with verdicts | ideas/<day key> | Spec shape |
| 3 briefs | briefs/<id> | status proposed |
| Run notes | `../output/<day key>-run.md` | "## Scout" section: 3 titles + lanes |
