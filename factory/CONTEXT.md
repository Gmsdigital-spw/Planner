# GM Factory: task routing

One row per scheduled task. Go to the stage folder for your task and follow its CONTEXT.md.
Tasks marked "not yet moved" still carry their full instructions in the scheduled task's prompt;
they only use `shared/` files when their prompt says so.

## Task routing

| Scheduled task | Go to | What it does |
|----------------|-------|--------------|
| GM Factory Night Shift (1:54 AM CT) | `stages/night-shift/CONTEXT.md` | Research, judge, build, copy, photos, inspect, pins, review, report |
| Mechanic · self-fix + morning report (3x daily) | `stages/mechanic/CONTEXT.md` + prompt | Check every lane, fix once, work the Medic's tickets (`medic/queue/`), one morning report |
| Bolt Etsy publisher (7:13 / 12:13 / 4:13 CT) | `stages/bolt/CONTEXT.md` | Publish passed products on Etsy, schedule pins |
| Herald social run (11:16 / 6:16 CT) | `stages/herald/CONTEXT.md` | One post per channel per day |
| Pixel · daily video pin | not yet moved (prompt) | One Pinterest video pin a day |
| Pricing agent (Ledger) | not yet moved (prompt) | Starter prices, raises, lowers within rules |
| Etsy Listing Check-up (Warden) | not yet moved (prompt) | Daily listing health and cover audit |
| GM Starship Day Watch (Medic) | not yet moved (prompt) | Morning system health |
| Trading Floor scans / close / lab | not yet moved (prompt) | Paper trading, live board, nightly backtests |
| Studio Floor daily Short (Vega) | `stages/studio/CONTEXT.md` | One Gmula Short a day |
| Atlas Prime weekly review (Sun) | not yet moved (prompt) | Fleet review, orders, proposals |

## Shared resources (Layer 3, canonical: one home each)

| Resource | Location | Contains |
|----------|----------|----------|
| Rules that never bend | `shared/rules.md` | Honesty, privacy, approvals, caps, how to talk to Grayson |
| The Medic (V8) | `../medic/` (repo root) | Plain-Python self-repair on GitHub Actions every 30 min: `lanes.json`, `public/medic_report.json` (the board), `queue/` (tickets for the Mechanic), `lessons/` |
| Database | `shared/database.md` | Artifact URL, ArtifactData rules, assets, day key, timestamps |
| Repo | `shared/repo.md` | Clone/pull/commit/push rules, write-path allowlist per agent |
| Gateway | `shared/gateway.md` | Free GitHub gateway protocol and every op shape |
| Accounts | `shared/accounts.md` | Shop id, Pinterest boards, TikTok, Make, YouTube, trading numbers |
| Logging | `shared/logging.md` | The run-log line every run writes |
| Floor specs | `specs/` | Grayson's standing orders per floor (load by section) |
| The week's standing order (Oct 23-30, 2026) | `specs/push-week-2026-10-23.md` | Mission numbers, daily targets per crew, the scoreboard, Grayson's taps, cap proposals |
| V8 "The Turning Point" (Oct 24, 2026) | `specs/etsy-v8.md`, `specs/studio-floor-v8.md`, `studio/quality_gates.py` | Grayson's V8 orders for the shop, the promo channels and the Gmula Shorts; the scorecards in code |
| Agent skills | `skills/<agent>/SKILL.md` | Load only the agents acting in the current stage |
| Lessons | `LESSONS.md` | Numbers-only lessons, newest last |
| Playbooks | `playbooks/` | Load only the one a stage names |
