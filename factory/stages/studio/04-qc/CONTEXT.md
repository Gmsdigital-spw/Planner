# 04 QC the file

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/qc.md` | Full file | The checks |
| Reference | `../references/job-format.md` | "Dry run, push, wait, rebuild" | Only if a rebuild is needed |
| Files | yt/out/<id>.mp4, yt/out/<id>.json | | What to check |

## Process
1. Run every check in qc.md; Read all 6 frames yourself. A bad scene: reword and rebuild only
   if today's rebuild is unused; otherwise do not post, log, and the coordinator messages
   Grayson in one line.
2. Write `## QC` in the run notes: PASS/FAIL, duration, size, what you saw in the frames.
   Save pipeline/<id>.qc.file = {pass, duration, mb, frames (one line each), rebuilt, at}
   (update with if_version; keep qc.judge).

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| QC verdict | run notes `## QC`; pipeline/<id>.qc | PASS/FAIL + reasons |
