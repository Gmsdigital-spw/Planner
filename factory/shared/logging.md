# The run log

Canonical home for observability. Every run that uses this workspace ends with one line in
`factory/runlog.jsonl`, written with the helper below, committed with the run's other repo
writes (or on its own if the run writes nothing else). This is how Grayson, the Mechanic and
Atlas Prime see what ran, what it loaded and how long it took, without opening every app.

## What the provider exposes, honestly
- Token counts are NOT exposed to a scheduled session. The log records a proxy that is exact
  and comparable: the byte size of every instruction file the run loaded (prompt files, stage
  contracts, references, specs, skills), and an estimate of tokens from it (bytes / 4).
- Wall time is exact: the run's start and finish (and the scheduled task's own last_run gives
  the same numbers from outside).
- Model is what the scheduled task is set to; record it as the prompt names it or "unknown".
- Cost in dollars is unknown for model usage; only listing fees, ad spend and bills are real
  money and they are logged where they happen (spend/<month>, adlog, bills).

## The line (one JSON object per run)
{"task":"night-shift","day":"2026-10-22","run":"run-2026-10-22-0655","started":"...Z",
 "finished":"...Z","minutes":17.3,"model":"unknown","stages":["00-start","01-scout",...],
 "skipped":["04-forge/wall-art","09-review/experiments"],"loaded":[{"f":"factory/CLAUDE.md",
 "b":3120},...],"loadedBytes":41200,"estTokens":10300,"gatewayJobs":3,"dbWrites":41,
 "outcome":"done","note":"Built 2, passed 2 at 92/93, 6 pins","needsYou":""}

## Helper
`python3 factory/shared/runlog.py add --task <name> --started <iso> --finished <iso>
  --stages a,b,c --skipped x,y --loaded f1,f2,... --gateway-jobs N --db-writes N
  --outcome done|failed|paused --note "<one line>" --needs-you "<one line or empty>"`
It measures the loaded files' sizes itself, appends the line, and prints it. Keep the list of
loaded files honest: name every instruction file you opened, nothing you did not.

`python3 factory/shared/runlog.py --status` prints the last run per task.
`python3 factory/shared/runlog.py --summary 7` prints per-task averages for the last 7 days
(runs, minutes, estTokens, outcomes) so a before/after comparison is one command.

## Baseline (recorded Oct 21, 2026, from the scheduled tasks' own last_run timings, before any
workspace change; the comparison after the change is against these)
| Task | Last run minutes | Prompt chars | Notes |
|------|------------------|--------------|-------|
| Night Shift | 17.7 (run doc says 29.8 on Oct 21; 15.5 on Oct 20) | 61,559 | plus every skill, playbook and spec read at step 0 |
| Mechanic | 4.0 | 9,900 | 5 runs a day |
| Bolt | 10.1 | 14,700 | 3 runs a day |
| Herald | 13.1 | 14,300 | 2 runs a day |
| Studio Short | 29.4 | 13,500 | 1 a day |
| Trading scans | 3.0 | 8,100 | 7 a day on weekdays |
| Trading close | 2.9 | 8,400 | 1 a day on weekdays |
| Check-up (Warden) | 1.5 | 5,300 | 1 a day |
| Video pin | 2.8 | 4,900 | 1 a day |
