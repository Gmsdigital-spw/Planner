# Known limitations (engine add-on, Phases 3–8) — honest list, Oct 21 2026

What the add-on does NOT do, as built. Each line is a real gap, not a disclaimer.

## Execution
- **No background daemon.** The engine runs only when something calls `worker`/`tick`: the "Engine worker" GitHub
  Action (about hourly 7am–6pm Central; GitHub cron is best-effort and often 10–40 min late), a manual **Run workflow**,
  a push of an order file, or a crew run. The Engine room shows the report's age so a late worker is visible.
- **Phone taps take up to ~4 hours.** Approve / Retry / Kill in the Engine room write an order to the artifact DB. The page
  holds no git credentials (by design); the Mechanic (6:47 AM, 10:47 AM, 2:47 PM, 6:47 PM, 10:47 PM Central) copies queued
  orders into `factory/engine/orders/`, and that push starts the worker at once. Repo half verified end to end on
  Oct 21 (order pushed → worker applied it → report shows the outcome); the Mechanic half runs for the first time at its
  next pass.
- **Nothing submits engine work by itself.** Task graphs start from `plan <goal> <input>` (CLI or a crew run). The
  existing crews (Night Shift, Bolt, Herald, Rocket…) still do their jobs through their own paths; the engine runs beside
  them, not instead of them.

## Handlers
- `research.brief` and `product.build` have **no engine handler**; research and product creation stay with the Night
  Shift. `launch_product` therefore stops at its first step until those exist. `promote_product`, `research_lane`'s
  measure step and `health_check` run end to end (mock gateway in tests; real gateway in the worker).
- Model calls go through the router with **two providers**: the Claude session hand-off (files, no cost reported) and the
  Anthropic API (**off** unless an API key is set AND a spend_money approval is recorded). No paid call has ever been made.

## Publishing
- Pinterest / TikTok / Etsy go out **only** as gateway jobs (`gw/jobs`), exactly as the crews already do; a publication is
  `queued` until `refresh` reads the gateway's real result. Instagram / Facebook / shop YouTube / Gmula become **drafts**
  on disk; the Make lanes are reachable only from the page / crews, so Python never posts there.
- Draft files and engine state live in the repo (public). They never contain credentials (scrubbed), but listing copy and
  captions are visible to anyone reading the repo, as the crews' pins and jobs already are.

## Analytics
- Numbers enter only through `ingest_*` from the Factory's own records or `record()`; nothing is fetched from platforms by
  the engine. **Unknown stays unknown**; the recommendations are labelled *demonstrated* only above fixed thresholds
  (500 reach, 25 clicks, 1 sale) and *hypothesis* otherwise. Correlation is never written as cause.
- Etsy strips UTM parameters, so clicks are what each platform reports, not Etsy-side attribution; sales are never
  attributed to a channel unless the record says so.

## Quality gate
- Offline checks only (file integrity, format, Etsy copy rules, revenue claims, brand names). Links, spreadsheet formulas
  and anything that needs a browser are recorded **unknown** → human review, never pass.

## Dashboard
- The Engine room reads `public/report.json` through raw.githubusercontent, which caches for up to ~5 minutes; the report
  itself is only as fresh as the last worker pass.
- The Foreman's chat answers from the same report; if it has not loaded, the engine is "unknown" to him.

## Learning (Phase 9)
- **No persistent worker.** Memory and evaluation rows are written by the crews' own scheduled runs (through nb.py,
  runlog.py and learn.py) and by the hourly GitHub engine worker's ingest step. Nothing runs continuously.
- **Lexical retrieval only** (term overlap with boosts for tested, Grayson's rules, recent mistakes); no embeddings.
  Budget 6 chunks / 6,000 characters per task; every recall is logged with its size.
- **Tokens are a proxy.** The scheduled sessions expose no token counts; the panel shows loaded-bytes / 4 from the run
  log and says so. Real tokens appear only for engine router calls that report them.
- **The by-eye checks stay by eye.** The slop lines, the side-by-side test, page-fill judgement and market truth need a
  reviewer; code checks file validity, limits, repeats, the centred-square proxy, colour, empty bands, evidence presence.
- **Quality gains are not claimed.** `learn.py compare` shows the frozen rubric reproduces the saved real inspections
  exactly (nothing raised); whether the separate Inspector and the repair list lift pass rates is measured by the
  production rows that accumulate from the next runs, not by this change.
- **Scheduled-task prompts not yet moved** (Mechanic, Pixel, Ledger, Warden, Medic, Trading, Atlas Prime) are connected
  only through the shared helpers they already call (`runlog.py add` for all of them; `nb.py show` where their prompt
  runs it); their prompts can add `--agent/--task` when Grayson edits them.

## Things deliberately NOT done (per the brief)
- Gumroad and the Funnel workflow stay off; parked businesses stay parked; Ridgeline is not in V7.
- No live trading; the trading floor is untouched by the engine (its `trade_live` capability is forbidden in every contract).
- No new accounts, no new paid services, no ads.
