# 10 Report, memory, the Foreman, run log (rooms "bridge", "core")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Previous stages | `../output/<day key>-run.md` | Full file | Everything this run did, with numbers |
| Spec | `../../../specs/foreman-rules.md` | "2. Judged on evidence", "5. Weekly scorecard" (Sundays) | How the Foreman grades |
| Skill | `../../../skills/foreman/SKILL.md` | Full file | The Foreman's standing orders and judgment |
| Shared | `../../../shared/logging.md` | "The line", "Helper" | The run-log line |
| Shared | `../../../shared/repo.md` | "Committing", "Write paths" (Night Shift row) | The memory push |
| Database | runs/<runId>, events/<day key>, reports/<day key>, milestones/main, sales | | The report's facts |

## Process
1. Report (room "bridge"). Write reports/<day key> {day, text (under 900 characters, plain,
   honest: what got built, what passed or failed and why, what waits on Grayson, which
   products Bolt publishes next (7:13 AM / 12:13 PM / 4:13 PM, 2 a day), Beacon's one-line ads
   note and Atlas's one-line sales note; then five short lines: IDEAS (15 judged, 3 briefed, N
   held, N dropped, each build's lane), MISSION (active mission title and tasks done/total, or
   "waiting for your approval: <title>"), TEST (experiment due or proposed, else "none"), NEXT
   MOVE (nextmove title), NEEDS YOU (the single most important tap, if any); money only from
   stage 09 D and the verified sales log; whole text under 1200 characters; it ends with the
   standup's first line), summary (under 90 characters), plan (one sentence for the next run),
   createdAt, runId}. If it exists today, rewrite it to cover the whole day.
2. Finish the run doc: status "done", finishedAt, counts, summary, full log. Set every crew doc
   idle. Set requests/nightshift status "done" if it was "requested".
3. Memory. (a) For each agent that worked tonight (atlas, scout, forge, quill, lens, pixel,
   ledger, judge_ideas), append ONE dated line to "What I've learned" at the end of
   skills/<id>/SKILL.md: what scored high, what was rejected and why, what the number says.
   "Same as yesterday" is a fail: write the specific change for tomorrow. (b) Append one line
   to LESSONS.md ONLY when a number proves it ("- <day>: <lesson> — evidence: <number>"), never
   a repeat. (c) Playbooks: when a product or pin scores 92+ AND a later stats snapshot shows
   real engagement, write playbooks/<slug>.md ("# Playbook: <title>", "_Proven by: <number>_",
   "## Steps", "## Beat it"); update an existing one only when a newer version beats its number.
4. The Foreman's standup (room "core"). Write fleet/commander/standups/<day key> {day,
   createdAt, text (under 1500 chars), agents:{<id>:{grade (0-100), verdict ("beat"|"meh"|
   "under"), line, fix}}, source:"Night Shift"} (read first; set). The text opens with "Bar:
   $1,000 per listing. $1,000,000 business. Verified this month: $<real number>." then calls
   every agent that worked by name with tonight's REAL numbers, roasts the ones under the bar
   (funny, merciless about the ROBOTS' work, never Grayson), names ONE concrete fix per agent,
   gives the ones that beat quota one line of "fine, don't get comfortable", and ends with
   "Dismissed. Belts on." The bar is a persona, never a forecast; the standup never invents a
   number or promises income. Grade: under = any number outside target or a product under
   92; beat = every number inside target and something measurably better than the last run;
   meh = the rest. Append one audit line (who "Foreman", mod "fleet").
5. Sundays only (after 4): rank the floors by verified money this month (sales log; YouTube
   only if logged in sales); promote the 3 most-proven LESSONS lines into the matching
   SKILL.md under "## Quality checklist"; delete any LESSONS line a later number disproved;
   rewrite "## Running judgment of each agent" in skills/foreman/SKILL.md (one line per agent,
   numbers only).
5b. WEEKLY SCORECARD (Sundays, after 5; Grayson, Oct 26, 2026). Write
   `factory/notebook/scorecard.md` (keep the newest 8 weeks, newest first) with one block:
   "## Week ending <day key>": shop numbers this week vs last (views, favorites, sales, reviews
   from stats/ and sales), what the crew LEARNED (every notebook line, LESSONS line and
   "What I've learned" line added in the last 7 days: `git log --since="7 days ago" -p --
   factory/notebook factory/LESSONS.md factory/skills` filtered to added lines, summarised in
   at most 6 bullets), what CHANGED because of it (one bullet each), prediction hit rate per
   agent (predictions.md) and the most improved and the weakest agent (from this week's
   standups' grades). Then send Grayson the scorecard with SendUserMessage AND PushNotification
   (status "proactive"), at most 3 plain lines (shared/rules.md): line 1 the week's buyer
   numbers and change, line 2 the most useful thing learned and the change it makes next week,
   line 3 best and weakest agent. Real numbers only; with nothing learned, say so.
6. Schedule sync. If settings.schedule.time differs from settings.schedule.applied: ToolSearch
   `select:mcp__claude-code-remote__update_trigger`, call it with the Night Shift task id
   (accounts.md) and cron "CRON_TZ=America/Chicago M H * * *", then set schedule.applied =
   schedule.time (if_version, nothing else changed). If the tool is unavailable, log and move on.
7. Run log. `python3 factory/shared/runlog.py add --task night-shift --run <runId> --started
   <iso> --finished <now> --stages <list> --skipped <list> --loaded <every instruction file you
   opened> --gateway-jobs 0 --db-writes <count> --outcome done --note "<one line>"
   --needs-you "<line or empty>"`.
8. Commit and push everything in the Night Shift's write paths in one commit
   ("Night Shift <day key>: skills + lessons + runlog"). A 403 goes in the report's NEEDS YOU
   line as "GitHub access needs a look" and in the run log; it does not fail the run.
9. Finish with a two-line summary of the run (the final message; no SendUserMessage unless
   something is red and needs Grayson, or it is Sunday's weekly scorecard, step 5b).

## Audit

| Check | Pass condition |
|-------|---------------|
| Numbers | Every number in the report and standup exists in the database or run notes |
| Memory | One new dated line per agent that worked; no "same as yesterday" |
| Run log | One line appended, loaded files listed honestly |
| Crew idle | Every crew doc idle |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Morning report | reports/<day key> | shape above |
| Standup | fleet/commander/standups/<day key> | shape above |
| Memory | skills/*/SKILL.md, LESSONS.md, playbooks/ | appended lines |
| Run log | `factory/runlog.jsonl` | one line |
| Weekly scorecard (Sundays) | `factory/notebook/scorecard.md` + one 3-line message | step 5b |
