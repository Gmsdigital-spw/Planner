# 03 Cutter: the job file, dry run, build

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/job-format.md` | Full file | The job schema and the build loop |
| Example | `yt/jobs/ep12.json` | "style" and "cast" | Copy style exactly; cast shape |
| Builder | `yt/build/make_short.py` | docstring only | The format |
| Reference | `../references/tools.md` | "GitHub build" | Push rules, Cloudflare |
| Skill | `../../../skills/cutter/SKILL.md` | Full file | Checklist |
| Database | episodes/<id> | | The script |

## Process
1. Set crew/cutter working. Write yt/jobs/<id>.json per job-format.md from episodes/<id>.
2. Dry-run, push only a passing job (commit "Studio <day key>: <id>", pull --rebase, push),
   wait for the build, one rebuild at most, exactly as job-format.md says.
3. Update modules/youtube/factory/main {lastBuildAt, lastBuildId, lastDuration, lastMb,
   lastError (or ""), builtThisWeek, totalBuilt, usedClips, nextRun:"tomorrow 8:12 PM CT",
   tts}. Crew idle. Write `## Build` in the run notes (duration, MB, rebuilds, warnings).

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Built Short | yt/out/<id>.mp4, yt/out/<id>.json | from the Action |
| Factory state | modules/youtube/factory/main | |
