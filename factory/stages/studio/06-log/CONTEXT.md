# 06 Log, memory, run log, telling Grayson

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/logging.md` | "The line", "Helper" | The run-log line |
| Shared | `../../../shared/repo.md` | "Committing", Studio row of "Write paths" | The push |
| Skill | `../../../skills/vega/SKILL.md` | Full file | Vega's standing orders |
| Previous stages | `../output/<day key>-run.md` | Full file | The facts |

## Process
1. log/main: copy Vega's verdict lines from the run notes `## Vega` plus the day's result;
   keep the newest 40. On any failure, factory/main.lastError holds exactly what broke.
   Every crew doc under modules/youtube/crew idle (vega last).
2. Memory: append ONE dated line to "What I've learned" at the end of skills/<id>/SKILL.md for
   vega, gags, judge, cutter and graph (what the numbers said, what scored high or failed, the
   one change for tomorrow; "same as yesterday" is a fail). Write nothing else in factory/
   except the run log.
3. fleet/commander/audit/<day key>: one line (who "Vega", mod "youtube") with what was built
   and posted or why nothing was, the two drafts' averages and which was built.
4. Run log: `python3 factory/shared/runlog.py add --task studio --started <iso> --finished
   <now> --stages <list> --skipped <list> --loaded <every instruction file the workers and
   you opened> --gateway-jobs 0 --db-writes N --outcome done|failed --note "<ep id, judge
   avg, posted or not, publishAt>"`. Commit skills + runlog ("Studio <day key>: skills +
   runlog"), pull --rebase, push.
5. Message Grayson (SendUserMessage; you are the only one who does), at most 3 lines: title +
   https://youtube.com/shorts/<videoId> + when it goes live; what is better than last time;
   anything that needs him (usually nothing). A skipped or failed day: one line saying why
   (a push 403: "GitHub access needs a look").

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Logs | modules/youtube/log/main, fleet audit, skills/* | shapes above |
| Run log | `factory/runlog.jsonl` | one line |
