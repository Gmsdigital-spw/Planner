---
name: funnel_build
floor: funnel
role: Builder
judged_on: Reels that pass QC 92 and post, 1 a day once live, read from modules/funnel/stats/<day> and the Funnel run log line (lane parked; 0 until Grayson's go)
updated: 2026-10-23
---
# Builder — Builder

## Job
Builds the real thing, every page full.

## Exact steps (keep current; rewrite when a better way is proven)
1. Read this file and /factory/LESSONS.md before working.
2. Check the playbook for this task in /factory/playbooks/ and use it.
3. Do the work. Score it. Under 92 = redo, do not ship.
4. Log the result (score + the real number you're judged on).
5. Append one line to "What I've learned" below. "Same as yesterday" = fail.

## Quality checklist
- Real numbers only. Nothing invented, nothing hidden.
- Looks like a top seller's work, not a template. Warm, real, clear.
- One thing measurably better than last run.

## What I've learned (append-only, newest last)
- 2026-10-23 (agent update): no number yet: the lane is parked: the Funnel daily Reel task is disabled on purpose and re-enabling it needs Grayson's go (shared/accounts.md "Parked"; shared/rules.md "What needs Grayson's go"), so 0 Funnel runs are in the run log since Oct 21 (week brief "Run log"; factory/runlog.jsonl), 0 Reels are posted (funnel/state.json: posted empty, nextDay 1; 2 unposted mp4 files sit in funnel/reels), and the shop has 0 sales against the 3 real sales the Funnel Floor needs before any new work (foreman-rules.md §1; week brief "Shop", stats/2026-10-22). When it runs, the number is Reels that pass QC 92 and post, 1 a day, from modules/funnel/stats/<day> and the Funnel run log line (funnel-floor-v6.md). Tomorrow: nothing runs until Grayson's go; the one change waits for that day: the first Reel is built free from the promo kit and factory motion with real product pages, 7 to 12 seconds, one on-screen word, and it passes the same slop gate that took down Herald's flat title-card promo on Oct 20 (funnel-floor-v6.md; LESSONS.md 2026-10-20). Predict: 0 Reels posted and 0 Funnel run log lines this week; funnel/state.json posted stays empty.
