# 04 QC the file: the gate, then the eyes

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/qc.md` | Full file | The checks |
| Spec | `../../../specs/studio-floor-v8.md` | "The seven rules" 4 and 6 | The gate and the animation rule |
| Reference | `../references/tools.md` | "Scorecard" | The gate command and the ten checks |
| Reference | `../references/job-format.md` | "Dry run, push, wait, rebuild" | Only if a rebuild is needed |
| Files | yt/out/<id>.mp4, yt/out/<id>.json, yt/out/<id>.score.json, yt/jobs/<id>.json | | What to check and what to fix |

## Process
1. Run the gate: `python3 studio/quality_gates.py short <id> --write` (exit 0 = PASS 85+,
   1 = FAIL, 2 = cannot judge). 85 or more of 100 passes. Under 85: the card's `fixes` list
   names the checks to redo; fix exactly those in yt/jobs/<id>.json (anim true on line 1 and
   the twist, split a long line, the hook words, the loop prompt, the speed, the length),
   bump rev, and use the day's one rebuild (job-format.md; a rebuild already spent on a build
   error means there is none left), then run the gate again. Still under 85 = not posted:
   `## QC` says the score and the fixes, and the Writer's next episode starts from them. A
   missing score file or exit 2 is not a pass. A twist line with no real motion fails the
   gate the same way (rule 4). Never lower a check to pass.
2. Then the eyes: every check in qc.md; Read all 6 frames yourself. A bad scene: reword and
   rebuild only if today's rebuild is unused; otherwise do not post, log, and the coordinator
   messages Grayson in one line.
3. Write `## QC` in the run notes: PASS/FAIL, the gate score and its fixes (or "none"),
   duration, size, what you saw in the frames. Save pipeline/<id>.scorecard = {score, pass,
   fixes, at} and pipeline/<id>.qc.file = {pass, duration, mb, frames (one line each),
   rebuilt, at} (update with if_version; keep qc.judge).

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| QC verdict | run notes `## QC`; pipeline/<id>.qc (gate, file) | PASS/FAIL + score + fixes + reasons |
| Scorecard | yt/out/<id>.score.json | written by the gate (--write) |
