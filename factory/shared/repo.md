# The repo: Gmsdigital-spw/Planner

Canonical home for how every crew uses the GitHub repo. The repo is PUBLIC: it hosts files for
Etsy, Pinterest and GitHub Pages, and it carries this workspace. Nothing private goes in it.

## Getting it
- It is ALREADY cloned at `/home/claude/planner` when a scheduled run starts. Check with
  `git -C /home/claude/planner remote -v`, then `cd` there and `git pull --rebase`.
- Only if that folder is missing: `git clone --depth 1 https://github.com/Gmsdigital-spw/Planner /home/claude/planner`
  (generous timeout). Do not use add_repo; it is not available in scheduled runs.

## Committing
- `git config user.email noreply@anthropic.com` and `git config user.name Claude`.
- Commit message: short, starts with the crew or task name and the day key, and ends with the
  trailer line `Co-Authored-By: Claude <noreply@anthropic.com>`.
- `git pull --rebase` then `git push origin HEAD:main`. If rejected as non-fast-forward, pull
  --rebase and push again (up to 3 times).
- If a push fails with 403: do not retry; write "GitHub access needs a look" into your crew
  doc's task and the run log, keep the work you did locally out of the report's claims, and
  tell Grayson in one line only if the stage says the push was required.

## Serving files
- A pushed file is public at `https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/<path>`
  within about 60 seconds. Check with `curl -sI` for a 200 before handing the URL to any API.
- GitHub Pages: `https://gmsdigital-spw.github.io/Planner/<path>` (capital P).
- Pushing a job file under `gw/jobs/` starts the free gateway (see `gateway.md`); pushing
  `yt/jobs/` starts the Shorts builder; pushing `factory/trading/kick/` wakes the autopilot;
  pushing `factory/engine/orders/` starts the Engine worker.

## Write paths (one table; a crew writes ONLY inside its paths)

Until a task's prompt points to this workspace, the list in its own prompt governs; this table
mirrors those lists so they have one home to drift from.

| Crew / task | May write |
|-------------|-----------|
| Night Shift | factory/notebook/, factory/skills/, factory/LESSONS.md, factory/playbooks/, factory/scores.jsonl, factory/runlog.jsonl, factory/stages/night-shift/output/, tools/fun_covers_config.json (add entries only), prints/<hex>/ (wall art) |
| Mechanic | gw/jobs/mech-*.json, factory/trading/kick/<day>-<HHMM>.txt, factory/engine/orders/<doc id>.json |
| Bolt | listing-photos/auto/, dl-temp/, gw/jobs/bolt-*.json, factory/runlog.jsonl |
| Herald | social/, factory/skills/herald/, yt/jobs/spot-*.json, gw/jobs/tt-*.json (TikTok via Postproxy, Oct 24), factory/runlog.jsonl |
| Pixel (video pin) | gw/jobs/vpin-*.json, factory/videopins/ |
| Ledger (pricing) | gw/jobs/price-*.json, factory/pricing/ |
| Warden (check-up) | shopcheck/, listing-photos/warm-covers/, gw/jobs/warden-*.json, tools/warm_covers.py (config only) |
| Medic (Day Watch) | gw/jobs/medic-*.json |
| Trading scans | factory/trading/kick/, factory/trading/watchlist.json, gw/jobs/trade-*.json (read ops), factory/skills/{bull,bear,vault,tape}/ |
| Trading close | gw/jobs/trade-*.json, factory/trading/journal/<day>.md (the nightly trade-journal review; until Grayson adds that folder to the close task's write list, Vault writes factory/skills/vault/journal-<day>.md instead), factory/skills/{bull,bear,vault,tape}/ |
| Trading lab | factory/trading/{backtest.py,params.json,lab/jobs/}, factory/skills/{bull,bear,vault,tape}/, factory/LESSONS.md |
| Studio (Vega) | yt/, factory/skills/{vega,gags,judge,cutter,graph}/ (memory step only), factory/runlog.jsonl, factory/stages/studio/output/ |
| Atlas Prime | factory/notebook/, factory/runlog.jsonl |

Never touch: `.github/`, `gw/run.py`, `gw/tools/`, `gw/vault/`, `factory/trading/autopilot.py`,
`factory/trading/auto/`, `control.json`, `index.html`, `factory/page/`, any secret, any file that
belongs to another crew.
