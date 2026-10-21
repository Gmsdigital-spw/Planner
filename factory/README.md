# GM Factory — skills, lessons, playbooks

This folder is the factory's memory. No agent starts from zero again.

- `skills/<agent>/SKILL.md` — one per agent: job, exact steps, quality checklist, and an append-only
  "What I've learned" section. Every scheduled run reads its agents' files at the start and appends one
  dated line at the end. "Same as yesterday" counts as a fail.
- `skills/foreman/SKILL.md` — the Foreman's standing orders and his running judgment of every agent
  (rewritten at the Sunday all-hands).
- `LESSONS.md` — dated, one line each, only things proven by numbers. Promoted into SKILL.md rules at
  the Sunday all-hands; deleted when later disproven.
- `playbooks/<thing>.md` — repeatable wins. Created the first time something scores 92+ AND gets real
  engagement; updated only when a later version beats its number. Use the playbook before inventing.
- `scores.jsonl` — one JSON line per scored item (agent, kind, item, score, metric, day) so the Foreman
  grades on trend, not vibes.
- `specs/` — standing instructions the scheduled runs read in STEP 0 (`product-floor-v6.md`: Idea Engine,
  lanes, Holiday Mode, mug wrap / sticker / invitation build specs; `marketing-wing-v6.md`: plan-from-numbers,
  holiday share, hooks, channel separation; `studio-floor-v6.md`: the Shorts bar, two drafts, hero-shot lane, Spot commercials; `funnel-floor-v6.md`: comment-the-word business + Frontier Nav; `trading-floor-v6.md`: Alpaca paper trading rules, crew, run prompt).
- `../apps/frontier-nav/` — Frontier Nav v0.1, the original old-west map app (GitHub Pages). Same authority as the run prompt, below it on conflict.
- `gm_factory_v6.py` — the Python brain (registry, Foreman grading, Idea Engine, holiday calendar,
  marketing plan-from-stats, DM keyword map, trading risk manager). Runs with no dependencies.

Rules that never change: real numbers only; nothing ships under 92; no paid service without Grayson's go;
no real name, hometown or personal details of Grayson in any file.
