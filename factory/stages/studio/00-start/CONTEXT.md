# 00 Start (coordinator)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/db.md` | Full file | Doc shapes |
| Reference | `../references/tools.md` | "vidIQ budget", "Drop zone" | Credits and clips |
| Database | modules/youtube/settings/main, factory/main, intel/trends, episodes (ids + loglines via out_dir + script), pipeline (newest 5) | | The state |

## Process
1. ToolSearch `select:ArtifactData,SendUserMessage,mcp__Make__scenarios_run,mcp__vidIQ__vidiq_balance,mcp__vidIQ__vidiq_outliers`.
   cd /home/claude/planner && git pull --rebase. Note the start time and day key.
2. Read settings (autopilot), factory/main, intel/trends, the episode list (ids, loglines,
   premises; through out_dir), pipeline newest 5. vidiq_balance. Next episode id = one more
   than the highest ep number in episodes/ and yt/jobs/.
3. Drop zone (tools.md): note any unused clip for the Writer's brief.
4. Set modules/youtube/crew/vega working ("Running the daily Short"). Create
   `../output/<day key>-run.md` with the header and the settings line. If settings.autopilot
   is false: still build, but stage 05 does not post (pipeline status "built-awaiting-launch").

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Tonight's brief values | local note | episode id, autopilot, credits, clip |
| Run notes | `../output/<day key>-run.md` | header |
