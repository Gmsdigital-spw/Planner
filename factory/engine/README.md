# factory/engine — the durable task engine (add-on Phase 3)

Read `ARCHITECTURE.md` first: it maps the add-on onto what the Factory already does and lists every
conflict and how it was resolved (dashboard stays the artifact; SQL = SQLite + a git-committed JSONL
journal; no background workers are claimed — a worker is whatever calls `tick()`).

## Run it (phone-friendly)

- **GitHub app → Actions → "Engine tests"**: runs on every push to this folder. Green = all 70 unit tests,
  the V7 rules self-test and the contracts export check passed. Red = open the log; the Mechanic reads it too.
- From any shell with Python 3.10+ (no packages needed):

```
python -m factory.engine status          # counts, kill switch, last tick, real usage (unknown stays unknown)
python -m factory.engine tasks queued    # or running | needs_approval | failed …
python -m factory.engine approvals       # what is waiting on you
python -m factory.engine approve apr_…   # or decline
python -m factory.engine kill on         # stop every new action; deletes nothing.  kill off to resume
python -m factory.engine retry task_…    # put a failed task back
python -m factory.engine agents          # the registered crews, versions, whether their SKILL.md is on disk
python -m factory.engine plan launch_product briefs/<id>   # build the task graph for one brief
python -m factory.engine progress proj_…  # done / blocked (with the reason) / failed
python -m factory.engine verify proj_…    # complete only when every step succeeded with an output
python -m factory.engine providers       # which model providers are really configured (paid one is off)
python -m factory.engine usage           # real model usage today: calls, known cost, unknown-cost calls, cache hits
python -m factory.engine budget daily_calls 300   # set a daily hard limit (daily_usd, daily_unknown_calls too)
python -m factory.engine products        # every product manifest: version, pipeline stage, listing + distribution status
python -m factory.engine funnel plan_…   # created → approved → planned → published → reached → clicks → sales (unknown stays unknown)
python -m factory.engine publications    # every publish attempt: draft / queued / scheduled / published / failed (verified or not)
python -m factory.engine refresh         # re-check queued posts against the gateway's real results
python -m factory.engine recommend       # repeat / improve / pause / test, each labelled demonstrated or hypothesis
python -m factory.engine selftest        # the tests, locally
```

## Guarantees (each one is a test in `tests/test_engine.py`)

queued → running → needs_approval → succeeded | failed | cancelled · idempotency keys · tool allow-list
per agent · publish/spend/credentials/destructive gated behind an approval id · bounded retries with
exponential backoff · timeouts · kill switch · pause/resume per agent · stalled-task recovery from the last
checkpoint · secrets scrubbed from every error and audit line · product versions never overwritten ·
unknown numbers reported as unknown, never 0 · no agent can hold `trade_live`.

## Rollback

Everything here is additive. `git revert` the commit (or delete `factory/engine/` and
`.github/workflows/engine-tests.yml`) and nothing else in the Factory changes: the page, the crews, the
gateway and the trading autopilot never import it.
