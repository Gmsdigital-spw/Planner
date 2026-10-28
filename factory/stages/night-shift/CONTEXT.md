# Night Shift pipeline

Eleven sub-stages, in order, run by FRESH WORKERS so no worker carries another's context. You
(the scheduled session) are the coordinator: you keep almost nothing in your own context. The
Night Shift researches, builds, writes, photographs, inspects and prepares listings while
Grayson sleeps. It NEVER publishes anything anywhere (no Etsy, no Pinterest, no drafts, no
cover swaps on live listings): Bolt publishes batched products at 7:13 AM, 12:13 PM and 4:13 PM
Central (2 a day); Warden swaps live covers. Never ads.

## How the coordinator runs it
1. Read this file. Do stage 00 yourself (it is tiny): it also fetches the kit into
   `/home/claude/kit`. Note runId, day key and the settings (buildsPerRun, batchSize,
   autoApprove, holidayMode).
2. For each worker below, launch one fresh agent (the Agent tool, a general-purpose agent, in
   the foreground, one at a time) with this brief, filled in, and nothing else:

   "You are the Night Shift's <WORKER> for <day key>, runId <runId>. The repo is at
   /home/claude/planner (already pulled; do not pull again; do not push, EXCEPT the Research
   worker may commit and push gw/jobs/scout-*.json read-only Etsy GET jobs for market proof). FIRST read
   factory/CLAUDE.md, factory/shared/database.md, factory/shared/rules.md and
   factory/stages/night-shift/CONTEXT.md (its Run notes, Load map and Conflicts sections
   bind you; a skill's own "Exact steps" never override them). Then read
   factory/stages/night-shift/<stage folder>/CONTEXT.md for each of your stages in order, and
   load ONLY what each Inputs table names (the sections it names). Settings for tonight:
   buildsPerRun <n>, batchSize <n>, autoApprove <true/false>, holidayMode <on/off, target>.
   <PRODUCT LINE: for the Builder only: "Your product: products/<id>, title <title>, lane
   <kind>. Work on this product only.">
   The kit lives in /home/claude/kit (gm_style.py, mockup.py, wall_art.py; fetch it as
   references/house-style.md says if a file is missing). Write your outputs where each stage's
   Outputs table says; after each stage append one line to events/<day key> (shape in
   database.md) and append your section to factory/stages/night-shift/output/<day key>-run.md
   under the heading the stage names. Report back in at most 12 plain lines: what you did,
   the numbers, what failed, and the list of instruction files you loaded."

   Workers share the machine: the kit, rendered pages and downloaded assets stay on disk.
3. After each worker: read its report and the run notes file, update runs/<runId>.log and
   counts, and decide the next worker. A failed worker is retried once with the failure in
   its brief; a second failure marks the run failed at that stage (later workers still run
   where they can: Review and Report always run).
3b. INDEPENDENT JUDGE (Oct 28, 2026). You, the coordinator, launch the Judge yourself as its own fresh
   worker; workers cannot launch agents, so never leave inspection to the Builder. The Judge gets
   the PRODUCT LINE and reads only 07-inspect's Inputs. The 85 floor and the 92 aim are unchanged:
   an honest judge must not be softer than the builder was.
4. If the Agent tool is not available in this session: run the stages yourself in order,
   loading each stage's CONTEXT.md only when you reach it, and say so in the run log.

## Workers (grouped so each loads a small, related set of files)

| Worker | Stages | Runs | Skip when |
|--------|--------|------|-----------|
| Research | 01-scout, 02-judge, 03-pick | once | never (02 is skipped inside when autoApprove is false) |
| Builder | 04-forge, 05-quill, 06-lens | once PER product in the build list (03 writes it), in order, with the PRODUCT LINE | build list empty |
| Judge | 07-inspect (and its fix rounds: send fixes back to a fresh Builder brief, then re-judge) | once PER built product, right after its Builder, a DIFFERENT fresh agent than the Builder (Grayson, Oct 28, 2026: the builder grading its own work 4 runs in a row was not an honest score) | product not built |
| Pins | 08-batch-pins | once | no passed or batched product without pins, no imageless pins, and the queue holds a day of pins |
| Review | 09-review | once | never (sub-steps have their own skips) |
| Report | 10-report | once | never |

## Run notes (`output/<day key>-run.md`, under 120 lines; every worker appends, Report reads it whole)
Headings, in order: `# Night Shift <day key>` (00), `## Settings` (00), `## Scout` (01),
`## Judge` (02), `## Build list` (03: one line per product: id, title, lane, theme), then per
product `## Build: <title>` (04), `## Copy: <title>` (05), `## Photos: <title>` (06),
`## Inspect: <title>` (07: PASS/FAIL, the six scores, slop fails), then `## Pins` (08),
`## Money` (09), `## Next move` (09). Plain text, numbers only, no prose padding.

## Load map (what each stage's Inputs table points to; every worker also has CLAUDE.md, database.md, rules.md)

| Stage | Loads |
|-------|-------|
| 00 | `specs/thrive-plan-2026-10-23.md` (full: wins over push-week on conflict; the coordinator puts the 8 moves and the focus list into every worker's brief), `shared/repo.md` ("Getting it"), `specs/push-week-2026-10-23.md` ("Daily targets": the coordinator puts each worker's line into its brief) |
| 01 | `notebook/etsy.md` (full) + `notebook/business.md` (Grayson's rules), `notebook/winners.md` (full), `notebook/buyer-voice.md` (full), `specs/product-floor-v6.md` (Idea Engine, lanes, Holiday Mode, SALES PUSH), `skills/scout/SKILL.md`, `skills/judge_ideas/SKILL.md`, `LESSONS.md`; `references/wall-art.md` (Scout section) |
| 02 | wall-art.md (Auto-approver section) for a wall art brief |
| 03 | `notebook/winners.md` ("Pattern", "Copy this" lines), `references/database-fields.md` ("products", "missions"), `specs/cover-styles.md` (newest section) |
| 04 | `notebook/etsy.md` ("Grayson's rules", "Proven"), `references/preflight.md` ("File"), `references/house-style.md` ("The kit", "PDF pages"), `skills/forge/SKILL.md`, `LESSONS.md`, `specs/product-floor-v6.md` (THANK-YOU PAGE; the lane's spec); wall-art.md (Forge) for wallart |
| 05 | `notebook/etsy.md` ("Grayson's rules", "Proven"), `notebook/buyer-voice.md` (full), `skills/quill/SKILL.md`, `specs/product-floor-v6.md` (SEARCH-FIRST COPY, PRICES) |
| 06 | `notebook/etsy.md` ("Grayson's rules", "Proven"), `notebook/winners.md` ("Cover at sale" lines), `references/preflight.md` (full: the gate before inspection), `specs/cover-styles.md` (newest section first), `playbooks/fun-listing-cover.md` (steps 1 to 4 only), `references/house-style.md` ("Photos 2 to 5", "Text safe zone"), `skills/lens/SKILL.md`, `LESSONS.md` |
| 07 | `notebook/etsy.md` ("Grayson's rules", "Proven"), `notebook/predictions.md` ("Calibration"), `notebook/scoreboard.md` ("By lane"), `references/rubric.md` (full), `references/preflight.md` (full), `skills/atlas/SKILL.md` |
| 08 | `notebook/pins.md` (full), `notebook/buyer-voice.md` ("What our buyers liked", rival words for the product's lane), `notebook/predictions.md` ("Calibration"), `specs/cover-styles.md` ("Pins"), `specs/foreman-rules.md` (3, 4), `skills/pixel/SKILL.md`, `playbooks/tablet-mockup-pin.md`, `shared/accounts.md` ("Pinterest"), `LESSONS.md` |
| 09 | `notebook/README.md`, all `notebook/*.md` (for step G; G(f) to G(h) run notebook/buyer_voice.py and notebook/grade.py), `references/database-fields.md` (experiments, sprint, lessons, nextmove, ads), `specs/product-floor-v6.md` (SALES PUSH last bullet) |
| 10 | `notebook/predictions.md` and `notebook/winners.md` (Sundays, step 5b), `specs/foreman-rules.md`, `skills/foreman/SKILL.md`, `shared/logging.md`, `shared/repo.md` ("Committing", Night Shift write paths), `specs/push-week-2026-10-23.md` ("Scoreboard", "Daily targets": target vs actual in the report and the standup) |

Do NOT load: every skill, every playbook, the other floors' specs, `gm_factory_v6.py`,
`references/legacy-prompt-*.md`, `yt/`, `social/`. A skill's "Exact steps" line that says to
browse every playbook is overridden by this map. If a stage file cannot be read, stop that
stage, write the run doc failed with the reason, and tell Grayson in one line.

## Handoffs
- Products move through DB stages: queued, building, copy, images, inspection, passed, batched
  (then Bolt: publishing, published). Side stages: sentback, scrapped, ready, publishing
  (Bolt's: never touch). Never change a product with an etsy field or stage published/publishing.
- Grayson's edit surface is the app: approve or reject a brief, send a product back, approve a
  mission, decide an experiment. The pipeline reads whatever state he left; his call wins.

## Time budget and conflicts
About 75 minutes of work (Grayson, Oct 28, 2026: raised from 50 so the second product gets its full build instead of being skipped every night; Oct 23: 25 minutes made every build rush and fail). Quality
first: ONE product that passes beats two that fail, so the first product gets its full build,
pre-flight and all three fix rounds before the second product starts. Over budget: skip 01's
intel refresh, then 08's extra pins, then the second product in the build list (it stays
queued and is built first next run); say so in the log. Any single wait: 5 minutes max.
`specs/cover-styles.md` NEWEST DATED SECTION wins (Oct 23, 2026 for covers: variety gate, the
fun_covers card retired as the default; Oct 27, 2026 for pins: 08 step 2 PIN STANDARD, fun_pins
at most 1 in 6). Fixed Oct 27: this line used to say the Oct 21 fun_covers/fun_pins look wins,
which is why every pin kept coming out as the same retired card. cover_styles.py is not used for new covers or pins. SALES PUSH wins over older spec lines. `shared/rules.md` wins over anything softer.
The task prompt wins over all.
