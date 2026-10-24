# factory/learning: how the crews remember, get graded and get better (Phase 9, Oct 24, 2026)

What this is: external memory plus honest bookkeeping for the agents that already exist. It does not train a
model, it makes no model calls of its own, and it is not a background worker. It rides on the Factory's existing
durable store (`factory/engine/state/journal.jsonl`, committed to git; a SQLite index rebuilt from it) through
migration v5, so it survives every fresh session and every GitHub runner.

## The loop every crew runs

1. **Before work** `python3 factory/notebook/nb.py show --lane <lane> --agent <you> --task "<what you are about to do>" --run <job id>`
   prints the lane notebook as before PLUS up to 6 relevant memory chunks (6,000 characters): your private memory,
   your business's shared memory, Grayson's rules, and explicitly TESTED general lessons. Memory is DATA. It never
   changes a permission, a cap or a stage CONTEXT. `learn.py recall` is the same call without the notebook.
2. **The work** happens exactly as the stage CONTEXT says.
3. **Review (products, posts, Shorts)** a FRESH worker that did not build the item grades each criterion in points with
   one line of evidence, guided by `stages/night-shift/references/rubric-anchors.md` (no pass mark inside). It then runs
   `python3 factory/learning/learn.py score ...` with the artifact paths, the copy, the market record and its by-eye slop /
   side-by-side verdicts. Code runs the objective checks (file validity, page count, thank-you page, 2000 px photos, no
   repeated photo, cover inside the centred square, bold colour, empty bands, title / tags / description limits, the AI
   line, AI phrases, em-dash runs, brands, revenue claims, lane price range, market evidence present), applies the rubric's
   downward caps and blockers, combines on the FROZEN rubric and prints PASS/FAIL, the ranked lost points and the
   repair list. A criterion without evidence stays unscored; a critical failure blocks whatever the total.
4. **Repair** the coordinator sends the Builder the repair list. At most TWO repair rounds after the first build; the
   third `score` call for the same `--job` is refused. A 92 is recorded as 92 with its remaining blockers.
5. **After work** `runlog.py add` (unchanged command) also records the run in the learning store with a stable id, with
   the loaded-bytes token proxy and the NEEDS YOU line; a failed or paused run leaves one mistake memory. Engine tasks
   do the same through `TaskEngine._learn` (tool errors, timeouts and budget stops are recorded without a score).
6. **Ideas** `learn.py diagnose --scope shop --agent atlas` prints the prompt pack (ranked losses, repeated failures,
   successful examples, open ideas). The crew's OWN Claude session (the existing model call) turns it into at most three
   ideas and queues them with `learn.py propose` (every idea: hypothesis, one change, baseline, metric, success, stop,
   budget, real source ids; deduplicated per business across agents; 3 new per business per day). The engine's
   `learning.diagnose` handler does the same through the router (free session hand-off first; the paid API never
   without an approved spend).
7. **Experiments** `learn.py experiment start|record|decide`: results are stored apart from the proposal, per arm,
   with sample counts and conflicts; `keep` needs 3+ candidate samples, a baseline result and no open conflict.
8. **Promotion** `learn.py verify <memory id> --experiment <exp>` turns a lesson into TESTED (and `--share` copies it
   to the shared scope); `learn.py workflow promote` activates a prompt / checklist version only on a kept experiment
   and keeps the previous version for `workflow rollback`.

## Scopes (businesses never share data)
`shop` (Etsy products, pins, socials, pricing, check-ups), `studio` (Gmula Shorts), `trading` (paper floor), `crew`
(the crew itself); `grayson` holds his rules in his words for everyone; `shared` holds only explicitly verified lessons.
Private memory is (scope, agent); business memory is (scope, '*'). Holdout eval cases are never retrievable.

## What is on file after `learn.py ingest`
Notebook lane files (Grayson's rules → facts with authority; What works → claimed lessons; Testing → hypotheses;
What doesn't work → mistakes), LESSONS.md, qa/MISSES.md, every skill's "What I've learned" and "Quality checklist" lines
(private to that agent), the stage run notes (chunks + every inspection as an observation and an eval case),
scores.jsonl (production score rows; total-only legacy rows say so), notebook/results.jsonl (buyer numbers),
runlog.jsonl (run rows), the specs / stage references / playbooks / shared rules (approved documents as reference chunks),
the trading lab exports. Each chunk carries source path, sha256, character offsets, timestamp, expiry, confidence and
tags. Re-ingesting is idempotent; a changed file supersedes its older chunks. Importing never verifies a claim.

## Where the data lives and its limits
- `factory/engine/state/journal.jsonl` is the truth (append-only, committed with each run; `.gitattributes` merges
  concurrent appends with `merge=union`). `state.sqlite` is derived and ignored by git. `GM_ENGINE_DB_DIR` overrides.
- There is NO persistent worker. Rows are written by the crews' own scheduled runs and by the hourly GitHub "Engine
  worker" (`python -m factory.engine worker`), which also ingests changed sources and rewrites `public/report.json`
  (the Engine room's "Agent learning" card). The crews' Claude sessions never expose token counts: the panel shows
  the loaded-bytes proxy from the run log and says so.
- Retrieval is lexical (term overlap + boosts), not semantic. Budget: 6 chunks / 6,000 characters per task; every
  recall is logged with its size and later joined to the task's outcome (`learn.py panel`: usefulness is correlation).
- Scores are inspections, never results. Buyer and market numbers stay in the notebook and the engine's metrics.

## Rubrics (frozen; see rubric.py)
`etsy-product-r2` (file 25, copy 20, images 20, market 15, price 10, polish 10; pass 92; caps: slop fail → images 12 /
polish 6, unreadable thumb → images 14, layout fault → images 14 / polish 7, side-by-side fail → total 80),
`herald-post-v6` (qc.md section B; pass 92), `studio-judge-x10` (the Judge's four 1-10 scores; adapter documented:
blockers "under 7" and "does not beat"), `idea-brief-30` (adapter ×100/30). Legacy `products/<id>.score` docs go
through `from_legacy_score()`, which keeps the points and reports arithmetic that does not add up.

## Commands
```
python3 factory/learning/learn.py recall   --scope shop --agent forge --task "Santa Mail letters cover" --run run-...:prod-...
python3 factory/learning/learn.py score    --scope shop --agent atlas --job <runId>:<product id> --item "<title>" --lane game \
    --ratings ratings.json --copy copy.json --market market.json --pdf <file.pdf> --cover <cover.jpg> --previews p2.jpg p3.jpg p4.jpg p5.jpg \
    --claims '{"spoiler_terms":["clem"],"public_pages":[2,3],"fillable":false}' --slop '{"pass":true,"fails":[]}' --side-by-side pass --rules-pass true --scores-jsonl
python3 factory/learning/learn.py score    --scope shop --agent herald --rubric herald-post-v6 --channel instagram --copy '{"caption":"...","link":"https://www.etsy.com/listing/..."}' --slop-gate pass --facts-checked true --ratings r.json --job <day>:<idem>
python3 factory/learning/learn.py score    --scope studio --agent judge --rubric studio-judge-x10 --ratings '{"hook":{"points":9,"evidence":"..."},...}' --beat 8.25 --job <day>:<ep>:A
python3 factory/learning/learn.py diagnose --scope shop --agent atlas          python3 factory/learning/learn.py propose --scope shop --agent atlas --idea idea.json
python3 factory/learning/learn.py panel    [--scope shop --agent atlas]        python3 factory/learning/learn.py compare --split train|holdout
python3 factory/learning/learn.py ingest   [--only notebook,runlog]            python3 -m factory.engine worker   (hourly: ingest + report)
python3 -m unittest factory.engine.tests.test_learning -v                      (the checks listed in the task; mocked, temp folders only)
```
`GM_LEARNING_OFF=1` silences the runlog hook; `--db <folder>` points any command at another store (tests).

## Rollback
Everything is additive: migration v5 only adds tables; the hooks in `nb.py`, `runlog.py` and `engine.py` swallow their
own errors. `git revert` the Phase 9 commit, or delete `factory/learning/` and the hook lines; the journal's learning
rows are ignored by an older store (unknown kinds are skipped on replay).
