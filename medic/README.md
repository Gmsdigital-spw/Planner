# The Medic (V8 "The Turning Point", Oct 24, 2026)

Self-repair for the GM Agency, in plain Python on GitHub's free minutes. Every 30 minutes
(`.github/workflows/medic.yml`) it reads this repo's own signals, fixes what it can for free,
checks the fix is live, learns, and writes `public/medic_report.json` for the Today screen.

| File | What it is |
|---|---|
| `medic.py` | the engine (`--dry-run`, `--selftest`, `--board`) |
| `lanes.json` | every lane: its signal, daily goal, fix playbook; the crews' cadences; the words for "needs you" |
| `schema.sql` + `db/history.sqlite` | runs, incidents, lessons, fix attempts (fix-once), lane days |
| `lessons/<lane>.md`, `lessons/RULES.md` | what broke and what fixed it; a fix that worked 3 times becomes a rule |
| `queue/*.json` | tickets for the Mechanic: fixes that need a Claude crew (rebuild, re-send, fire a task) |
| `public/medic_report.json` | the board, what was fixed, what needs Grayson, yesterday's numbers |

Signals it reads: `factory/runlog.jsonl` (every crew's run line), `gw/jobs` vs `gw/out` (gateway),
`factory/trading/*/heartbeat.json`, `factory/videopins/state.json`, `yt/jobs` vs `yt/out`,
`factory/engine/public/report.json`, and the GitHub Actions API (failed runs).

What it fixes itself: a gateway job the Action never picked up (re-dispatch, verify the answer
lands), a Short that never built (re-dispatch), a bot or the engine that stopped checking in
(re-dispatch, verify a fresh heartbeat), a failed Action (re-run once). Everything else becomes a
ticket for the Mechanic, who reads `queue/` on each run. Grayson is told only when neither can fix it.

Rules: fix each thing at most once a day; never spend; parked lanes (Gumroad, Funnel Floor, Frontier
Nav, TikTok) are never checked; unknown stays unknown; this repo is public, so ids only in tickets.
The Ridgeline Office has its own copy under `office/medic/` in its own repo; the two never link.
