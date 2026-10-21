# 04 Log, run log, and telling Grayson

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Shared | `../../../shared/logging.md` | "The line", "Helper" | The run-log line |
| Shared | `../../../shared/database.md` | "Shared log documents" | events, audit, crew shapes |
| Previous stages | local notes: published, failed, orphans, pins confirmed/queued/failed, snapshot status | | The facts |

## Process
1. events/<day key>: read (may exist), append one item per thing you did {t:now, crew:"Bolt",
   text}, keep the newest 200.
2. crew/bolt: set {state:"idle", task:"last run "+summary, room:"launch", updatedAt:now}
   (keep any rank field).
3. fleet/commander/audit/<day key>: read, append {t:now, who:"Bolt", mod:"etsy", text:<one
   line>}, keep the newest 200.
4. Run log: `python3 factory/shared/runlog.py add --task bolt --started <iso> --finished <now>
   --stages 00,01,02,03,04 --skipped <any> --loaded <every instruction file you opened>
   --gateway-jobs N --db-writes N --outcome done|failed --note "<published N, pins queued N,
   confirmed N>" --needs-you "<line or empty>"`. Commit it with any other repo writes ("Bolt
   <day key> <HHMM>"), pull --rebase, push (a 403: note it, do not fail the run).
5. Message Grayson with SendUserMessage, at most 3 short lines, ONLY when: a new sale (lead
   with it), something went live on Etsy ("Live on Etsy: <short title>" + link), or something
   failed that needs him (lead with what he should do in plain words, e.g. "Delete 1 empty
   draft in the Etsy app: <title>"). Routine pin scheduling goes in the Mechanic's morning
   report, not a message. Never invent numbers.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Events, audit, crew | events/<day key>, fleet/commander/audit/<day key>, crew/bolt | shapes in database.md |
| Run log | `factory/runlog.jsonl` | one line |
