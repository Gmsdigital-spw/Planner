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
6. Remember for the run log: every instruction file you load from here on.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Run doc | runs/<runId> | status running |
| Run notes | `../output/<day key>-run.md` | Plain text |

Settings rule: never change anything in settings/main except schedule.applied (stage 10).
