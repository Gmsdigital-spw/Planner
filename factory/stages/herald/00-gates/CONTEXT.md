# 00 Gates and channel check

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/channels.md` | Full file | signal/main shape, connection ids, URLs, repo paths |
| Spec | `../../../specs/marketing-wing-v6.md` | Full file | Plan-from-numbers, holiday share, hooks, channel separation |
| Spec | `../../../specs/foreman-rules.md` | "1. Focus", "2. Judged on evidence", "3. Quality gates", "6. Self-repair" | Etsy first; never invent a number; 92 + slop gate; exact blocker lines |
| Skill | `../../../skills/herald/SKILL.md` | Full file | Checklist and lessons |
| Database | settings/main, signal/main, lessons (newest 10 with crew Herald) | | Gates and lessons |

## Process
1. Repo: cd /home/claude/planner && git pull --rebase. Note the start time, day key, now (Central).
2. Read settings/main; stop silently if paused is true.
3. Read signal/main (create it if missing, as channels.md says). Verify every channel with
   mcp__Make__connections_list {teamId:3216895} exactly as channels.md says; write connected,
   verifiedAt, connectionId and a note per channel; a missing or expired connection sets
   connected false, note "Reconnect <name> in Make", and goes in the message to Grayson.
4. Read the newest 10 Herald lessons and apply them.
5. Decide the run shape: stages 01 and 02 always; stages 03 to 06 only if no social docs
   exist with planDate = today (query social where planDate == day key). Record the decision.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Channel state | signal/main.channels | per channels.md |
| Run shape | local note | "post+numbers only" or "full day" |
