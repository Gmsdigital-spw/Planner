# 05 Rocket: post it

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/tools.md` | "Make: post" | The upload and confirmation |
| Reference | `../references/db.md` | "pipeline" | What to save |
| Skill | `../../../skills/rocket/SKILL.md` | Full file | Checklist |
| Previous stages | run notes `## QC`; pipeline/<id> | | Only post a PASS with no videoId |

## Process
Skip (status "built-awaiting-launch") when settings.autopilot is false, the build has an
error, QC failed, or pipeline/<id> already has a videoId (never upload the same episode twice).
1. Set crew/rocket working. Upload with the Make "youtube" action (tools.md): fileData
   https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/yt/out/<id>.mp4, fileName =
   title, body = description, nameKey = comma tags, nameValue "private", rank = the next free
   posting window as UTC ISO. On an upload error with no id, retry once after 2 minutes; if it
   returns an id, never upload again. Confirm privacyStatus and publishAt as tools.md says.
2. Save pipeline/<id>: {made:{clips:true,voice:true,edit:true}, videoId, videoTitle,
   privacy:"scheduled", duration:"PT<n>S", launch:{mode:"schedule", privacy:"private",
   publishAt, at}, qc, autoVideo:{url, note:"Built free in the factory", credits:0}}. Update
   factory/main.postedThisWeek and stats/channel.vidiqCredits. Crew idle.
3. Write `## Launch` in the run notes: videoId, publishAt (Central), or why not posted.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Scheduled Short | pipeline/<id> | videoId + launch |
