"""python -m factory.engine <command>

  status                 counts, kill switch, last tick, usage (unknown stays unknown)
  tasks [status]         list tasks (queued|running|needs_approval|succeeded|failed|cancelled)
  show <task_id>         one task with its runs
  approvals              pending approvals
  approve <id> / decline <id>
  retry <task_id>        put a failed task back in the queue
  cancel <task_id>
  kill on|off            the kill switch (stops new actions; deletes nothing)
  pause <agent> / resume <agent>
  tick [n]               one worker pass with the registered demo handlers (n tasks max)
  rebuild                rebuild state.sqlite from journal.jsonl
  agents                 registered agent contracts (versions, skill file state); `agents sync` re-registers
  plan <goal> <input>    build + submit a task graph (goals: launch_product, promote_product, research_lane, health_check)
  projects               open projects;  progress <proj_id>;  verify <proj_id>
  providers              which model providers are really configured (none paid unless a key is set)
  usage [YYYY-MM-DD]     real model usage: calls, known cost, unknown-cost calls, cache hits, budget
  budget [daily_calls N] [daily_usd X] [daily_unknown_calls N]   show or set the daily hard limits
  cache purge            drop expired rows and rows from an older data version
  data-version <v>       bump the data version (every cached answer from before is ignored)
  products               product manifests (latest version, stage, listing + distribution status)
  funnel <plan_id>       the real funnel for one distribution plan (unknown stays unknown)
  publications [plan]    every publish attempt: draft / queued / scheduled / published / failed, verified or not
  refresh                re-check queued publications against gw/out (the gateway's real results)
  integrations           gateway / Make health as last observed (connected · unverified · missing)
  compare [channel|product|plan] [days]   platform-reported sums per group + what is unknown
  recommend [by] [days]  repeat / improve / pause / test / measure, each labelled demonstrated or hypothesis
  report [path]          write the credential-free dashboard report (default factory/engine/public/report.json)
  orders                 apply the order files in factory/engine/orders/ (approve / retry / kill ... from the phone)
  worker                 one worker pass: recover → orders → tick → refresh → integrations → learning ingest → report (what GitHub Actions runs)
  learn <args>           the agent-learning CLI (same as python3 factory/learning/learn.py): recall, score, run, diagnose, propose, ingest, panel ...
  export-ts              regenerate ts/contracts.d.ts and contracts.schema.json
  selftest               run the unit tests

Runs anywhere Python 3.10+ runs: a GitHub Actions step, a Claude scheduled task, your laptop.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import contracts
from .engine import TaskEngine
from .orchestrator import PLANS, Orchestrator
from .providers import availability
from .registry import AGENTS, demo_handlers, sync
from .router import Router, data_version
from .store import Store

HERE = Path(__file__).resolve().parent


def _learning_step(store: Store) -> dict:
    """Phase 9, inside the hourly worker: index the approved sources that changed since the last pass (idempotent by
    content hash; a changed file supersedes its old chunks) so the panel and every crew's recall see today's notebook,
    lessons, run notes and run log. No model call, no network."""
    try:
        from factory.learning.brain import AgentBrain
        from factory.learning.ingest import ingest_all, summarize
        out = summarize(ingest_all(AgentBrain(store), HERE.parents[1]))
        return {"ingested": {k: v.get("new", 0) for k, v in out.items()}, "superseded": sum(v.get("superseded", 0) for v in out.values())}
    except Exception as e:  # never fail the worker over the learning step
        return {"error": f"{type(e).__name__}: {str(e)[:160]}"}


def _engine(store: Store) -> TaskEngine:
    eng = TaskEngine(store, AGENTS, runner="cli", router=Router(store))
    sync(store)
    for kind, fn in demo_handlers().items():
        eng.register(kind, fn)
    return eng


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "status"
    if cmd == "export-ts":
        (HERE / "ts").mkdir(exist_ok=True)
        (HERE / "ts" / "contracts.d.ts").write_text(contracts.to_typescript(), encoding="utf-8")
        (HERE / "contracts.schema.json").write_text(json.dumps(contracts.to_json_schema(), indent=1), encoding="utf-8")
        print("wrote ts/contracts.d.ts and contracts.schema.json")
        return 0
    if cmd == "selftest":
        import unittest
        suite = unittest.defaultTestLoader.discover(str(HERE / "tests"), top_level_dir=str(HERE.parent.parent))
        res = unittest.TextTestRunner(verbosity=1).run(suite)
        return 0 if res.wasSuccessful() else 1
    with Store() as store:
        eng = _engine(store)
        if cmd == "status":
            print(json.dumps(eng.status(), indent=1))
        elif cmd == "tasks":
            st = contracts.TaskStatus(args[1]) if len(args) > 1 else None
            for tk in store.tasks(st):
                print(f"{tk.id}  {tk.status.value:15} {tk.spec.agent_id:12} {tk.spec.kind:24} attempts={tk.attempts}  {tk.last_error or ''}"[:160])
        elif cmd == "show":
            tk = store.get_task(args[1])
            print(json.dumps(tk.to_dict() if tk else None, indent=1))
            for r in store.runs_for(args[1]):
                print(json.dumps(r.to_dict(), indent=1))
        elif cmd == "approvals":
            for a in store.approvals("proposed"):
                print(f"{a.id}  {a.capability.value:18} {a.title}  ({a.requested_at})")
        elif cmd in ("approve", "decline"):
            print(eng.decide(args[1], cmd == "approve").to_json())
        elif cmd == "retry":
            print(eng.retry(args[1]).to_json())
        elif cmd == "cancel":
            print(eng.cancel(args[1]).to_json())
        elif cmd == "kill":
            eng.kill(args[1] == "on")
            print("kill", "ON" if eng.killed() else "off")
        elif cmd in ("pause", "resume"):
            eng.pause_agent(args[1], cmd == "pause")
            print(cmd, args[1])
        elif cmd == "tick":
            runs = eng.tick(int(args[1]) if len(args) > 1 else 10)
            for r in runs:
                print(f"{r.task_id} → {r.status.value}  {r.error or r.output_ref or ''}")
            print(f"{len(runs)} task(s) processed")
        elif cmd == "rebuild":
            print("replayed", store.rebuild(), "journal lines")
        elif cmd == "agents":
            if len(args) > 1 and args[1] == "sync":
                print(json.dumps(sync(store), indent=1))
            for r in store.agents():
                print(f"{r['id']:10} v{r['version']}  {r['role']:16} skill={'ok' if r['skill_sha'] else 'missing'}  {r['registered_at']}")
        elif cmd == "plan":
            print(json.dumps(Orchestrator(eng).plan(args[1], args[2], who="grayson"), indent=1))
        elif cmd == "projects":
            for p in store.projects():
                print(f"{p['id']}  {p['status']:8} {p['goal']:16} {p['input_ref']}")
        elif cmd == "progress":
            print(json.dumps(Orchestrator(eng).progress(args[1]), indent=1))
        elif cmd == "verify":
            print(json.dumps(Orchestrator(eng).verify(args[1], who="grayson"), indent=1))
        elif cmd == "providers":
            print(json.dumps(availability(), indent=1))
        elif cmd == "usage":
            print(json.dumps(eng.router.report(args[1] if len(args) > 1 else None), indent=1))
        elif cmd == "budget":
            if len(args) > 1:
                b = store.control("budget", {}) or {}
                for k, v in zip(args[1::2], args[2::2]):
                    b[k] = float(v) if "usd" in k else int(v)
                store.set_control("budget", b)
            print(json.dumps(store.control("budget", {"note": "defaults: daily_calls 400, daily_unknown_calls 400, daily_usd unlimited (nothing paid is configured)"}), indent=1))
        elif cmd == "cache":
            print("purged", store.cache_purge(data_version(store)), "rows;", json.dumps(store.cache_stats()))
        elif cmd == "products":
            from .quality import Pipeline
            pipe = Pipeline(store)
            seen = set()
            for r in store._rows("SELECT DISTINCT product_id FROM products ORDER BY product_id"):
                m = store.get_product(r["product_id"]); seen.add(m.product_id)
                print(f"{m.product_id:16} v{m.version}  stage={pipe.stage_of(m):12} listing={m.listing_status:9} distribution={m.distribution_status}  {m.title}")
            if not seen:
                print("no product manifests yet")
        elif cmd == "funnel":
            from .distribution import funnel
            pl = store.get_plan(args[1])
            print(json.dumps(funnel(store, pl), indent=1) if pl else "no such plan")
        elif cmd == "publications":
            from .publishing import Publisher
            for r in Publisher(store).publications(args[1] if len(args) > 1 else None):
                print(f"{r.id}  {r.channel.value:12} {r.status:10} via {r.adapter:8} verified={r.verified}  {r.job_id or r.draft_path or ''}  {r.note}")
        elif cmd == "refresh":
            from .publishing import Publisher
            pub = Publisher(store)
            for r in pub.publications():
                if r.status in ("queued", "scheduled"):
                    r = pub.refresh(r)
                    print(f"{r.id}  {r.channel.value:12} {r.status:10} verified={r.verified}  {r.note}")
        elif cmd == "integrations":
            from .publishing import Publisher
            for h in Publisher(store).health():
                print(f"{h.id:10} {h.state.value:11} last_ok={h.last_ok_at or '—'}  {h.note}")
        elif cmd in ("compare", "recommend"):
            from .analytics import compare, recommend
            c = compare(store, args[1] if len(args) > 1 else "channel", int(args[2]) if len(args) > 2 else 14)
            print(json.dumps(c if cmd == "compare" else recommend(c), indent=1))
        elif cmd == "report":
            from .report import build_report, write_report, PUBLIC
            from .orders import recent_outcomes
            p = write_report(build_report(store, eng, orders=recent_outcomes()), args[1] if len(args) > 1 else PUBLIC)
            print("wrote", p)
        elif cmd == "orders":
            from .orders import apply_orders
            res = apply_orders(eng)
            for r in res:
                print(("applied " if r["ok"] else "REFUSED ") + f"{r['action']} {r['id']}: {r.get('result') or r.get('error')}")
            print(f"{len(res)} order(s)")
        elif cmd == "worker":
            from .orders import apply_orders, cleanup_done, recent_outcomes
            from .publishing import Publisher
            from .report import build_report, write_report, PUBLIC
            fixed = eng.recover()
            orders = apply_orders(eng)
            runs = eng.tick(int(args[1]) if len(args) > 1 else 10)
            pub = Publisher(store)
            refreshed = [pub.refresh(r) for r in pub.publications() if r.status in ("queued", "scheduled")]
            pub.health()
            cleanup_done()
            learned = _learning_step(store)
            p = write_report(build_report(store, eng, orders=recent_outcomes()), PUBLIC)
            print(json.dumps({"recovered": fixed, "orders": [(r["action"], r["id"], r["ok"]) for r in orders], "ran": [(r.task_id, r.status.value) for r in runs],
                              "refreshed": [(r.id, r.status) for r in refreshed], "learning": learned, "report": str(p), "kill": eng.killed()}, indent=1))
        elif cmd == "learn":
            from factory.learning.learn import main as learn_main
            return learn_main(args[1:])
        elif cmd == "data-version":
            store.set_control("data_version", args[1])
            print("data version", data_version(store), "— older cached answers are now ignored; run `cache purge` to drop them")
        else:
            print(__doc__)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
