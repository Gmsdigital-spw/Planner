# 00 Start (coordinator)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/db.md` | Full file | Doc shapes |
| Reference | `../references/tools.md` | "vidIQ budget", "Drop zone" | Credits and clips |
| Spec | `../../../specs/studio-floor-v8.md` | "The seven rules" (1), "Title, description and tags" | When vidIQ may be called; the free research path |
| Database | modules/youtube/settings/main, factory/main, intel/trends, episodes (ids + loglines via out_dir + script), pipeline (newest 7) | | The state |

## Process
1. ToolSearch `select:ArtifactData,SendUserMessage,mcp__Make__scenarios_run,mcp__vidIQ__vidiq_balance,mcp__vidIQ__vidiq_outliers`.
   cd /home/claude/planner && git pull --rebase. Note the start time and day key.
2. Read settings (autopilot), factory/main, intel/trends, the episode list (ids, loglines,
   premises; through out_dir), pipeline newest 7. vidiq_balance. Next episode id = one more
   than the highest ep number in episodes/ and yt/jobs/.
3. Drop zone (tools.md): note any unused clip for the Writer's brief. Write
   stats/channel.vidiqCredits from vidiq_balance (every run, read first, if_version). Decide
   the research path for the brief: under 5 credits (today 2; renewable 0 of 150, renews
   Nov 19, 2026) every 5-credit vidIQ call is skipped and the Analyst uses the free ytapi
   research path (tools.md "Research (free)"); 5 or more, vidIQ is allowed where a stage
   says so. Never buy credits.
4. Set modules/youtube/crew/vega working ("Running the daily Short"). Create
   `../output/<day key>-run.md` with the header, the settings line (autopilot, next episode
   id, vidIQ credits and "research: free ytapi path" or "research: vidIQ allowed", clip,
   last posted episode with its Judge and gate scores) and `## Premises` (one line
   per existing episode from the out_dir script: id, logline). If settings.autopilot is
   false: still build, but stage 05 does not post (pipeline status "built-awaiting-launch").

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Tonight's brief values | local note | episode id, autopilot, credits, research path (free or vidIQ), clip |
| Run notes | `../output/<day key>-run.md` | header |
