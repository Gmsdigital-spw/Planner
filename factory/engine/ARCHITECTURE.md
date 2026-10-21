# GM Factory engine — architecture map (add-on Phase 2)

Written Oct 21 2026, after V7 "Simple Ship" shipped. This maps what already exists in this repo and the
Factory page to the "extreme power-up" add-on, and records every conflict and how it was resolved.
Rule used for every conflict: **keep the existing safeguard, keep the existing surface, add underneath.**

## What exists today (preserved, untouched by the add-on)

| Add-on role | Already exists as | Where |
|---|---|---|
| Orchestrator | The Foreman (page) + the scheduled crews (Night Shift, Bolt, Herald, Mechanic, Trading scans/close/lab, Studio Short, Etsy Check-up, Day Watch) | page `AGENTS`/`foremanStandup`; Claude scheduled tasks |
| Research & Opportunity | Scout (15 ideas → 3 briefs, 2+ evidence links, scored /30) | `factory/skills/scout`, Night Shift STEP 2 |
| Product Factory | Forge + Quill + Lens (file, copy, photos), lanes + Holiday Mode | `factory/gm_factory_v6.py`, `factory/specs/product-floor-v6.md` |
| Quality & Compliance | Atlas inspection (rubric v2, 90+, rules pass/fail), Judge (YouTube 7+), Flame (posts 92+), Mirror | page `RUBRIC`, `pubGates`; skills |
| Distribution Intelligence | Hawk (plan from the numbers), Santa (holiday share), Beacon (ads locked) | page `hawkPlan`, `holidayState` |
| Channel adapters | Pixel (pins), Herald (IG/FB/TikTok/shop YT), Rocket (Gmula) | page `SIG_CH`, `MK_CHANNELS`; Make lanes, Zernio via `gw/run.py` |
| Publishing | Bolt (Etsy, keyed by listing id, 2/day cap, fee cap), Rocket (Make YouTube lane), Zernio queue | `gw/run.py`, Bolt task |
| Analytics & Learning | Graph (YouTube API via Make), Medic/Day Watch (pin stats), Sales Sprint snapshots, `LESSONS.md` | page `pullStats`, `listingHealth` |
| Model & cost optimisation | Claude scheduled tasks on the plan (no per-call pricing exposed); vidIQ credit gauge | page `yCreditsLine`, `monthlyCosts` |
| Engineering & Reliability | Mechanic (self-fix + morning report), `factory/qa/sweep.py` (Playwright sweep), `medic/qa` doc | `factory/qa/sweep.py`, Mechanic task |
| Durable records | Artifact DB (`claude.use("db")`: products, pins, social, events, audit, modules/*) + git (`gw/state`, `factory/trading/auto`, `factory/scores.jsonl`) | page `connect()`, repo |
| Kill switch / pause | `settings/main.paused`, `fleet/commander.pausedAll`, `factory/trading/auto/control.json.paused` | page, `autopilot.py` |
| Secrets | GitHub Actions secrets only (`STARSHIP_KEY`, `ALPACA_*`, `ZERNIO_API_KEY`, Etsy keys); Fernet-encrypted state in `gw/state`, `gw/vault` | `.github/workflows/*.yml`, `gw/run.py` |

## Conflicts and how they were resolved

1. **"TypeScript dashboard" vs the one-page HTML artifact.** The Factory is a single published Claude
   artifact (HTML/CSS/JS, 5 tabs, 4 Today lights) that talks to the artifact DB and connectors. Rebuilding
   it as a TypeScript app would break every connector permission, the DB subscriptions and the phone
   workflow. **Resolved:** the dashboard stays the artifact. TypeScript's job here is *typed contracts*:
   `factory/engine/ts/contracts.d.ts` is generated from the Python contracts so any future TS code (or
   the page's JS, by reading it) shares one schema. No TS runtime is introduced.
2. **"SQL persistent memory" vs no database server.** There is no Postgres/MySQL host and the add-on
   forbids new paid services. **Resolved:** SQLite (`factory/engine/db/state.sqlite`, rebuilt on demand) is
   the SQL store, and an append-only JSONL journal (`factory/engine/db/journal.jsonl`) is the git-durable
   source of truth. The journal merges cleanly across runners (append-only, `pull --rebase`); the SQLite
   file is derived from it and ignored by git. Every record the add-on asks for (tasks, runs, approvals,
   audit, model usage, product manifests, distribution plans, integration health) has a table and a
   journal event type.
3. **"Background workers / durable execution" vs no always-on server.** The only runtimes are GitHub
   Actions (free, public repo) and Claude scheduled tasks. **Resolved:** the engine runs as *steps inside*
   those runs (same pattern as `factory/trading/autopilot.py --loop`). It never claims to be running when
   no runner is up: `status` reports the last heartbeat and the runner window, and anything older than its
   `stalled_after_s` is reported as stalled, not running.
4. **Agents calling tools freely.** The add-on requires explicit permitted tools per agent. **Resolved:**
   `AgentContract.tools` is an allow-list checked in `TaskEngine.submit`; a task that names a tool outside
   its agent's list is rejected before it is queued. Publishing, money and credentials are
   `Capability` flags that must be present on the contract *and* carry an approval.
5. **Gumroad / Funnel / parked businesses.** V7 parked them. **Resolved:** the engine has no Gumroad
   channel, no Funnel agent and no Ridgeline anything. `Channel` lists exactly the six Marketing-tab
   channels plus `etsy` for listings.
6. **Trading.** The add-on must not touch paper mode or the money rules. **Resolved:** the engine does not
   wrap `gw/run.py op_alpaca` or `autopilot.py`. `Capability.TRADE_LIVE` exists only so the contract test
   can prove no agent is granted it; `ALPACA_LIVE` stays a GitHub variable the engine never reads.
7. **Model routing without known prices.** Claude scheduled tasks run on the plan and expose no per-call
   cost. **Resolved (Phase 5 design, Phase 3 schema):** `ModelUsage` stores `tokens_in/out` and `cost_usd`
   as *optional*; unknown stays `null` and is reported as "unknown", never 0 and never estimated into a
   budget. Budgets in Phase 5 will count calls and tokens where a provider reports them.
8. **Existing self-tests.** `factory/gm_factory_v7.py --selftest` and `factory/gm_factory_v6.py` keep
   running unchanged; the engine's tests are additive (`python -m unittest factory.engine.tests`).

## Layout added in Phase 3

```
factory/engine/
  __init__.py        package + version
  contracts.py       typed contracts (dataclasses + enums + JSON schema export)
  store.py           SQLite store with versioned migrations + JSONL journal
  engine.py          TaskEngine: queued→running→needs_approval→succeeded|failed|cancelled,
                     idempotency keys, bounded retries with backoff, timeouts, kill switch,
                     stalled detection, checkpoints, secret-safe logging
  cli.py             python -m factory.engine  status | tasks | agents | plan | progress | verify | providers | kill on|off | selftest | export-ts
  registry.py        the ten agent contracts + versioned sync into the store (Phase 4)
  orchestrator.py    goal → dependency graph, progress, blocked reasons, verify-before-complete (Phase 4)
  providers.py       provider-neutral model interface: mock, Claude-session hand-off, paid API (off) (Phase 4)
  router.py          routing, escalation, cache, dedup, usage tracking, hard budgets, loop guard (Phase 5)
  ts/contracts.d.ts  generated TypeScript types (do not edit; `export-ts` regenerates)
  db/journal.jsonl   append-only durable records (committed)
  db/state.sqlite    derived index (ignored by git)
  tests/             unittest suite (no third-party deps)
.github/workflows/engine-tests.yml   runs the suite on every push (green check in the GitHub app)
```

## Added in Phase 4

- `registry.py` — the ten agent contracts (one per add-on role, each mapped to the crew that already does the
  job and to its `factory/skills/<agent>/SKILL.md`), **versioned in the store**: `sync()` writes a new row only
  when the contract or its SKILL.md hash changed; old versions are kept (`agents` table, migration v2).
- `orchestrator.py` — goal → task graph with dependencies (`launch_product`, `promote_product`,
  `research_lane`, `health_check`), submitted through the engine so every safeguard applies; `progress()`
  names what is blocked and why; `verify()` marks a project complete only when every task succeeded *with an
  output*. Projects live in the `projects` table and the journal.
- `providers.py` — provider-neutral `Provider` interface and three adapters: `MockProvider` (tests),
  `ClaudeSessionProvider` (hand-off to the crew's own Claude session; usage unknown; available only inside a
  crew run), `AnthropicApiProvider` (paid; unavailable until a key is configured and, in Phase 5, a budget is
  approved). No prices anywhere; no model names hard-coded.

## Added in Phase 5

- `router.py` — tier by task kind or `model_hint`, escalation to "strong" after a failed validation or when the
  caller is unsure; providers tried in order (free session hand-off first, paid API last) and only when
  configured; the paid API is used only with an APPROVED `spend_money` approval named in control
  `paid_provider_approval`. Cache keyed by provider+model+prompt version+**data version**+prompt, TTL per
  call, `cacheable` only for safe repeatable work, bump `data-version` to invalidate everything older; in-process
  dedup. Cost tracking records exactly what the provider reported — unknown is counted as unknown, no price
  table exists. Hard budgets: per task (calls / tokens / usd from the contract), per day (`budget` control:
  calls, known usd, and a cap on unknown-cost calls so a silent provider cannot run away), plus a runaway-loop
  guard. A hard stop is a PermanentError: the task fails safely, nothing is deleted.
- `RunContext.llm()` — the one way a handler reaches a model; records usage and model on the run.
- `llm_cache` table (migration v3); CLI `usage`, `budget`, `cache purge`, `data-version`.

## What is NOT implemented yet (honest list)

- Phase 4 leftover: the task kinds the orchestrator submits still have no real handlers — `tick` runs only the
  placeholder; the crews keep doing the real work through their own scheduled runs until Phase 7 wires them.
- Phase 6–7: quality gate + distribution plans driving real runs; publishing adapters (today Bolt/Herald/Rocket publish through their own paths, not the engine).
- Phase 8: dashboard views for tasks/health (the page shows nothing from the engine yet; Phase 8 will mirror the journal into the artifact DB so the page can read it without a new tab).
- Phase 9: regression pass across page + engine, limitations doc, rollback drill.
