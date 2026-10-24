# 05 Rocket: post it

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/tools.md` | "Make: post", "vidIQ budget" | The upload and confirmation; when a title may be scored |
| Spec | `../../../specs/studio-floor-v8.md` | "Title, description and tags", "One great Short a day" | Title scoring, the posting window, the sidecar |
| Reference | `../references/db.md` | "pipeline", "Sidecars in the repo" | What to save |
| Skill | `../../../skills/rocket/SKILL.md` | Full file | Checklist |
| Previous stages | run notes header (credits), `## QC`; pipeline/<id> (scorecard, qc.judge) | | Only post a gate PASS (85+) and Judge 7+ with no videoId |
| Database | episodes/<id> (ytTitle, titleCandidates, description, tags), intel/trends.windowNote, stats/channel.vidiqCredits | | What to upload with; the window; the credits |

## Process
Skip (status "built-awaiting-launch") when settings.autopilot is false, the build has an
error, the gate failed (pipeline/<id>.scorecard.pass false, or no yt/out/<id>.score.json), QC
failed, or pipeline/<id> already has a videoId (never upload the same episode twice). A
skipped gate day writes `## Launch`: "not posted: gate <score>, fixes <list>" in one line.
1. Title. With 5 or more vidIQ credits (stats/channel.vidiqCredits): vidiq_score_title (type
   short, channelId UCax9xpzMhvy8DXeyBi0czBg) on the first title candidate; 70 or more
   passes; under 70, one rewrite from the other candidates and one more score (10 credits a
   day at most). With fewer than 5 credits (today 2, renews Nov 19, 2026): no call; the title
   follows the hook rule by hand (a question or a shock, under 60 characters, ends " #shorts").
   Either way write the sidecar yt/jobs/<id>.research.json {title, title_score (a number or
   null), scored_at, credits_before, credits_after, why ("credits N of 5" when not scored)}
   so the gate can read it; then run `python3 studio/quality_gates.py short <id> --write`
   once more so yt/out/<id>.score.json carries the title check (the score can only go up).
   Stage 06 commits the sidecar and the score file.
2. Set crew/rocket working. Upload with the Make "youtube" action (tools.md): fileData
   https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/yt/out/<id>.mp4, fileName =
   title, body = description, nameKey = comma tags, nameValue "private", rank = the next free
   posting window as UTC ISO. On an upload error with no id, retry once after 2 minutes; if it
   returns an id, never upload again. Confirm privacyStatus and publishAt as tools.md says.
   The window rule: weekdays 7:00 PM CT, weekends 11:30 AM CT, unless intel/trends.windowNote
   moved it on a Sunday with numbers; one midday test (12:30 PM CT) is allowed per week and
   is logged as a test (launch.window "test-midday"; none in the last 7 days first).
3. Save pipeline/<id>: {made:{clips:true,voice:true,edit:true}, videoId, videoTitle,
   privacy:"scheduled", duration:"PT<n>S", launch:{mode:"schedule", privacy:"private",
   publishAt, window ("weekday-7pm"|"weekend-1130am"|"test-midday"), at}, qc (judge, file,
   gate), titleScore (the sidecar's title_score or null), autoVideo:{url, note:"Built free in
   the factory; real motion on lines <n>", credits:0}}. Update factory/main.postedThisWeek.
   Crew idle.
4. Write `## Launch` in the run notes: videoId, publishAt (Central) and the window, the title
   and its score (or "not scored: credits N of 5"), the gate score, or why not posted.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Scheduled Short | pipeline/<id> | videoId + launch + titleScore |
| Title sidecar | yt/jobs/<id>.research.json | {title, title_score, scored_at, credits_before, credits_after, why} |
