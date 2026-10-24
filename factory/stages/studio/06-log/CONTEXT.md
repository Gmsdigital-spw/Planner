# 06 Log, memory, run log, telling Grayson

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/logging.md` | "The line", "Helper" | The run-log line |
| Shared | `../../../shared/repo.md` | "Committing", Studio row of "Write paths" | The push |
| Skill | `../../../skills/vega/SKILL.md` | Full file | Vega's standing orders |
| Previous stages | `../output/<day key>-run.md` | Full file | The facts (the gate score, the fixes, the kill list, the tags) |

## Process
1. log/main: copy Vega's verdict lines from the run notes `## Vega` plus the day's result
   (episode, Judge average, gate score, posted or not, publishAt; a shape added to
   intel/trends.kill today is named in a few words); keep the newest 40. On any failure,
   factory/main.lastError holds exactly what broke. Every crew doc under modules/youtube/crew
   idle (vega last).
2. Memory: append ONE dated line to "What I've learned" at the end of skills/<id>/SKILL.md for
   vega, gags, judge, cutter and graph (what the numbers said, what scored high or failed, the
   one change for tomorrow; "same as yesterday" is a fail). Write nothing else in factory/
   except the run log.
3. Notebook (V8 rule 7): one line per Short built today, posted or not: `python3
   factory/notebook/nb.py add --lane shorts --kind short --id <ep id> --what "<title>; <posted
   or not posted and why>" --tags hook=<hook style>,shape=<story shape>,seconds=<duration>,
   window=<weekday-7pm|weekend-1130am|test-midday|none>,anim=<animated line numbers, e.g.
   1+6>,score=<gate score>,judge=<Judge average>` (the tags come from `## Drafts`, `## Build`,
   `## QC` and `## Launch`; the keeper fills the views at 7 days). A Short not posted (gate
   under 85 or Judge under 7) also gets one "What doesn't work" line in
   factory/notebook/shorts.md with the failed checks, the same day. Nothing in the notebook
   claims a result from our own score: views are the result.
4. fleet/commander/audit/<day key>: one line (who "Vega", mod "youtube") with what was built
   and posted or why nothing was, the two drafts' averages, which was built and its gate score.
5. Run log: `python3 factory/shared/runlog.py add --task studio --started <iso> --finished
   <now> --stages <list> --skipped <list> --loaded <every instruction file the workers and
   you opened> --gateway-jobs 0 --db-writes N --outcome done|failed --note "<ep id, judge
   avg, gate score, posted or not, publishAt>"`. Commit skills + runlog + notebook +
   yt/jobs/<id>.research.json + yt/out/<id>.score.json when the Action did not already commit
   it ("Studio <day key>: skills + runlog"), pull --rebase, push.
6. Message Grayson (SendUserMessage; you are the only one who does), at most 3 lines: title +
   https://youtube.com/shorts/<videoId> + when it goes live + the score ("gate 90/100, Judge
   8.25"); what is better than last time; anything that needs him (usually nothing). A skipped
   or failed day: one line saying why, with the score ("not posted: gate 75, fixes: twist had
   no real motion, hook text"; a push 403: "GitHub access needs a look").

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Logs | modules/youtube/log/main, fleet audit, skills/* | shapes above |
| Notebook | `factory/notebook/results.jsonl` (nb.py add), `factory/notebook/shorts.md` ("What doesn't work" on a fail) | one line per Short, tags hook=, shape=, seconds=, window=, anim=, score= |
| Run log | `factory/runlog.jsonl` | one line |
