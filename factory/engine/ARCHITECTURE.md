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
  quality.py         ten-stage product pipeline, offline validation, human-review gate, versioned manifests (Phase 6)
  distribution.py    distribution plans, approval, schedule, results, next action, honest funnel (Phase 6)
  publishing.py      gateway + draft adapters, idempotent approval-gated publish, verify from gw/out, adapt() (Phase 7)
  analytics.py       metric rows with sources, ingest from Factory records, compare, recommend, measure_plan (Phase 7)
  report.py          credential-free dashboard report → public/report.json (Phase 8)
  orders.py          phone orders (approve / retry / kill ...) from files, outcomes audited (Phase 8)
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

## Added in Phase 6

- `quality.py` — the ten-stage pipeline (hypothesis → … → publish → measure) enforced in order on versioned
  manifests; `validate()` checks file integrity (exists, non-empty, sha256, real PDF/PNG/JPG/SVG header), lane
  formats, the Etsy copy rules (140 / 13×20 / 300), revenue claims, brand and character names, and lists known
  limitations; anything it cannot check offline is **unknown**, never pass. `gate()` → approved / needs_review /
  rejected. Publishing requires validation not failed, the human review when one was required, an approved
  distribution plan and an approved `publish_public` approval. Every stage writes a new manifest version.
- `distribution.py` — `build_plan()` (channels by lane with a reason each, V7 keep-list only; assets per
  channel from one source; validated Etsy destination + CTA; schedule inside each channel's window and free
  daily cap, America/Chicago; measurable hypothesis + success criteria; campaign id), `approve_plan()`,
  `mark()` (planned → approved → scheduled → published → measured, no skipping), `record_results()` (real
  numbers; an unreported 0 is refused), `next_action()` (repeat / improve listing / improve hook / test /
  measure first), `funnel()` (every stage real or "unknown"; sales never attributed unless recorded).
- Two orchestrator steps are now REAL handlers: `quality.inspect` and `distribution.plan` (deterministic,
  no model, no network). CLI `products`, `funnel <plan_id>`.

## Added in Phase 7

- `publishing.py` — authorized routes only, nothing new: Pinterest/TikTok/Etsy go through the existing free
  GitHub gateway as `gw/jobs/<id>.json` in exactly the shape `gw/run.py` runs today (Zernio POST /posts with an
  Idempotency-Key; Etsy PATCH state=active). The adapter cannot run the job; a publication is `queued` until
  `refresh` reads the gateway's real result in `gw/out` and marks it scheduled / published / failed. Instagram,
  Facebook, shop YouTube and Gmula (Make lanes, reachable only from the page/crews) become **review-ready drafts**
  (`factory/engine/drafts/`), status `draft`, never "published". `Publisher.publish()` requires an approved plan,
  honours the kill switch, never sends the same (plan, channel, asset) twice, and audits every attempt.
  `adapt()` makes one channel asset per plan channel inside each platform's limits, deterministically.
- `analytics.py` — metric rows with source and retrieval time; an unreported zero is refused; `ingest_pins /
  ingest_social / ingest_youtube` read the Factory's own records with the page's availability rules; `compare`
  sums known numbers per channel / product / plan and lists what is unknown; `recommend` labels every line
  demonstrated or hypothesis; `measure_plan` folds rows into the plan through Phase 6's rules.
- Real handlers now: `channel.adapt`, `publish.listing`, `publish.social` (approval-gated), `analytics.measure`.
  `promote_product` runs end to end through the orchestrator with the mock gateway in tests. Only
  `research.brief` and `product.build` remain with the Night Shift.
- `publications` + `metrics` tables (migration v4); CLI `publications`, `refresh`, `integrations`, `compare`, `recommend`.

## Added in Phase 8

- `report.py` — one credential-free JSON (`factory/engine/public/report.json`): health (kill switch, last worker pass, report
  age), agents' live state, workflows with what blocks them, queued / running / needs-approval / failed tasks (each failed
  one with its error and a plain next step), pending approvals with cost + risk, products with gate decision, plans with
  funnel + every publish attempt and whether it was verified, platform-reported channel sums with unknown kinds,
  recommendations labelled demonstrated / hypothesis, real model usage + daily budget, integrations as last observed,
  latest errors, order outcomes, audit tail. The whole document passes through `scrub()`; the scrubber now also catches
  `sk-ant-…`, GitHub PATs, bearer tokens and 40+ hex secrets.
- `orders.py` — Grayson's taps as files in `factory/engine/orders/` (approve / decline / retry / cancel / kill / pause /
  resume). Applied oldest first, unknown ids and actions refused, every outcome audited and moved to `orders/done/`.
- `python -m factory.engine worker` — one pass: recover → orders → tick → refresh queued posts → integration health →
  report. `.github/workflows/engine.yml` runs it about hourly 7am–6pm Central (GitHub cron, best effort), on a tap
  (workflow_dispatch) and when an order file lands. State is the committed journal `factory/engine/state/journal.jsonl`
  (`GM_ENGINE_DB_DIR`); the sqlite index is rebuilt each run and never committed.
- Dashboard: an **Engine room** fold on the factory map (More → Engine room; no new tab, the four Today lights are
  untouched). It reads the public report every 2 minutes the same way the Trading tab reads the heartbeat, shows the
  sections above, and folds logs behind a details toggle. Engine approvals, failed tasks, the kill switch and a stale
  report join the existing "Needs you" list. Approve / Decline / Retry / Cancel / Kill are confirm-sheet taps that write an
  ORDER doc to the artifact DB (`engine/main/orders`); the page cannot reach the repo (no credentials, by design), so an
  order waits there until a crew run copies it into `factory/engine/orders/`. The Foreman's DATA now carries the engine
  summary.

## What is NOT implemented yet (honest list)

- Phase 4 leftover: the task kinds the orchestrator submits still have no real handlers — `tick` runs only the
  placeholder; the crews keep doing the real work through their own scheduled runs until Phase 7 wires them.
- Research and build (`research.brief`, `product.build`) stay with the Night Shift; the engine has no handler for them yet.
- Phone orders reach the engine through the Mechanic's five daily passes (step 4b of its prompt copies `engine/main/orders`
  docs into `factory/engine/orders/`; the push starts the worker). Latency is up to ~4 hours, not minutes.
- Nothing submits engine work on its own yet; the Foreman / a crew calls `plan <goal> <input>`.
- Phase 8: dashboard views for tasks/health (the page shows nothing from the engine yet; Phase 8 will mirror the journal into the artifact DB so the page can read it without a new tab).
- Phase 9: regression pass across page + engine, limitations doc, rollback drill.
