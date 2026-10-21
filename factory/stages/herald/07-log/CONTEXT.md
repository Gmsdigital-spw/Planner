# 07 Log, memory, run log, telling Grayson

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/logging.md` | "The line", "Helper" | The run-log line |
| Shared | `../../../shared/repo.md` | "Committing", Herald row of "Write paths" | The push |
| Shared | `../../../shared/database.md` | "Shared log documents" | events, audit, crew |

## Process
1. crew/herald {state:"idle", task:"last run: "+summary, room:"signal", updatedAt}.
   events/<day key>: append {t, crew:"Herald", text}. fleet/commander/audit/<day key>: append
   {t, who:"Herald", mod:"etsy", text}. Keep both at the newest 200.
2. A lesson ({at, crew:"Herald", text, evidence, status:"active", area:"socials"}) when
   something failed in a way that is not a one-off.
3. Memory, once per day (the evening run): append ONE dated line to "What I've learned" at the
   end of skills/herald/SKILL.md (what the numbers said, what scored high or failed, the one
   change for tomorrow; "same as yesterday" is a fail). Write nothing else in factory/.
4. Run log: `python3 factory/shared/runlog.py add --task herald --started <iso> --finished
   <now> --stages <list> --skipped <list> --loaded <every instruction file you opened>
   --gateway-jobs 0 --db-writes N --outcome done|failed --note "<posted N, made N, qc>"
   --needs-you "<line or empty>"`. Commit skills/herald + runlog.jsonl ("Herald <day key>:
   skills + runlog"), pull --rebase, push. A 403 goes in the message to Grayson.
5. SendUserMessage only when it matters, at most 3 short lines: something posted with its
   link, a channel that needs reconnecting, a slop-gate fail, or a failure he needs to know
   about. Otherwise send nothing.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Logs | events, audit, crew/herald, skills/herald | shapes above |
| Run log | `factory/runlog.jsonl` | one line |
