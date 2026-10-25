# 00 Start: gates and the run doc

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/database.md` | Full file | Tool, if_version, day key, log docs |
| Shared | `../../../shared/rules.md` | Full file | The rules that never bend |
| Shared | `../../../shared/repo.md` | "Getting it", "Committing" | Pull the repo first |
| Database | settings/main, requests/nightshift | Full docs | Gates |
| Database | crew (all docs) | state, rank | Leave everyone idle |

## Process
1. ToolSearch `select:ArtifactData,Artifact,SendUserMessage`. `cd /home/claude/planner && git pull --rebase`.
2. Note the start time (UTC) and the day key. runId = "run-" + day key + "-" + HHMM UTC.
3. Read settings/main and requests/nightshift. If settings.paused is true: create runs/<runId>
   with status "paused" and summary "Pause all is on; nothing ran.", set every crew doc idle,
   set requests/nightshift status "done" if it was "requested", write the run-log line
   (outcome paused) and stop.
4. Otherwise create runs/<runId> {startedAt, status:"running", trigger ("manual" if
   requests/nightshift was "requested", else "scheduled"), log:[], counts:{briefs:0, built:0,
   passed:0, scrapped:0, pins:0}}. Update the run doc after each major stage so the app shows
   progress (one log line per step, newest last).
5. Create `../output/<day key>-run.md` (stages/night-shift/output/) with the header line "# Night Shift <day key>" and the
   settings you will use: buildsPerRun (default 2), batchSize (5), autoApprove (missing = on),
   holidayMode (from the spec's calendar and today's date).
6. Fetch the kit once for every worker: mkdir -p /home/claude/kit, then Artifact read with
   url = the artifact url, out_dir = /home/claude/kit, path "917d03e4f21b576da506766f0aa992f8"
   (gm_style), then path "d2fe939ea8bd7975733326b0cc836a6c" (mockup), then path
   "d0b1821fc580b42db28e2c22b005fb85" (wall_art); one path per call; copy each saved .txt to
   /home/claude/kit/gm_style.py, mockup.py, wall_art.py. If a read fails, note it in the run
   doc; the Builder falls back as house-style.md says.
7. Remember for the run log: every instruction file you load from here on.
8. SCOREBOARD (Grayson, Oct 24, 2026: "I want them to full on learn everything"). ArtifactData
   list stats (limit 60) and list sales (limit 500), both with out_dir /tmp/sb; then
   `python3 factory/notebook/scoreboard.py /tmp/sb > factory/notebook/scoreboard.md`. Commit it
   ("scoreboard <day key>") and push before the workers start, so tonight's workers AND every
   daytime crew read today's buyer numbers. Never edit the file by hand.
9. SCOUT LESSONS SYNC (Scout Intel cannot push to GitHub, so its learning lives only in the
   database). For each lessons doc with source "Scout Intel", status "active" and no synced
   field: append one dated line to "What I've learned" in factory/skills/pixel/SKILL.md
   ("- <day>: <text> (evidence: <evidence>)"); when its confidence is "high", also append it to
   factory/LESSONS.md. Then update the doc {synced:true} (read first, pass if_version). Also
   add today's 1-3 most useful Scout intel findings (intel docs, newest 12) to the "Testing"
   section of factory/notebook/etsy.md with `nb.py add`, tagged source=scout-intel.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Run doc | runs/<runId> | status running |
| Run notes | `../output/<day key>-run.md` | Plain text |

Settings rule: never change anything in settings/main except schedule.applied (stage 10).
