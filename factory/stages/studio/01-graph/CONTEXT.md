# 01 Graph (and Radar on Sundays): every video better than the last

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/tools.md` | "Make: stats", "vidIQ budget" | The calls |
| Skill | `../../../skills/graph/SKILL.md` | Full file | Checklist |
| Skill | `../../../skills/radar/SKILL.md` | Full file, Sundays only | Trend notes |
| Database | pipeline (newest 5 posted: videoId, stats), intel/trends | | The numbers |

## Process
1. Set crew/graph working. Pull the newest 5 posted episodes' stats in ONE ytapi call. Save
   views/likes/comments into pipeline/<id>.stats {views, likes, comments, at} and a one-line
   lesson (what the best one did right: hook, story type, length, posting time) into
   intel/trends.lessons (keep the newest 10). Sundays: compare posting windows over at least 4
   episodes; note in intel/trends.windowNote and adjust if clear.
2. Radar (Sundays only): one vidiq_outliers search (tools.md); save 3 observations to
   intel/trends.notes. Set crew idle.
3. Write `## Numbers` in the run notes: the 5 episodes' views, the lesson, the weakness of
   the last episode to fix tonight.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Stats and lesson | pipeline/<id>.stats, intel/trends.lessons | shapes in db.md |
