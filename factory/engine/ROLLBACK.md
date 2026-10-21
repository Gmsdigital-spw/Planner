# Rollback (from a phone)

Every phase was committed on its own, so you can step back one layer at a time. Nothing below deletes data.

## 1. Hide the Engine room (page only, 1 minute)
Ask Claude: "republish the Factory page without the Engine room". It re-publishes the artifact from
`factory/page/gm-factory-v7.html` at commit **19db710** (Phase 7, V7 page without the engine fold). Everything else on
the page is identical. The repo side keeps working either way.

## 2. Stop the engine worker (GitHub app, 30 seconds)
GitHub app → Planner → Actions → **Engine worker** → ⋯ → **Disable workflow**. Nothing runs, nothing is committed.
Turn it back on the same way. The kill switch is the softer option: Engine room → **Kill switch ON** (needs the order hop)
or `python -m factory.engine kill on` from any shell.

## 3. Remove a whole phase (ask Claude, or any shell)
The commits, newest first — `git revert <sha>` undoes one without touching the others:

| phase | what | commit |
|---|---|---|
| 8 dashboard | Engine room fold, sweep, docs | `git log --oneline -- factory/page/gm-factory-v7.html` (newest) |
| 8 repo | report.py, orders.py, worker, engine.yml | `4116c27` |
| 7 | publishing.py, analytics.py, migration v4 | `19db710` |
| 6 | quality.py, distribution.py | see `git log --oneline -- factory/engine/quality.py` |
| 5 | providers.py, router.py, llm_cache | `git log --oneline -- factory/engine/router.py` |
| 4 | registry.py, orchestrator.py, skills | `git log --oneline -- factory/engine/orchestrator.py` |
| 3 | contracts.py, store.py, engine.py, tests | `git log --oneline -- factory/engine/engine.py` |

Reverting everything: `git revert` each in that order, or delete `factory/engine/` and `.github/workflows/engine*.yml`
in one commit. The Factory page, crews, gateway and trading autopilot do not import anything from `factory/engine/`.

## 4. Wipe engine state only (keep the code)
Delete `factory/engine/state/journal.jsonl` (and commit). The next worker pass starts from an empty engine; agents
re-register themselves. Order files already applied are in `factory/engine/orders/done/` and can be deleted too.

## What rollback never touches
Your artifact database, the crews' scheduled tasks, `gw/`, `factory/trading/`, Etsy, Pinterest, Make, the trading
workflow. The engine only ever *added* files.
