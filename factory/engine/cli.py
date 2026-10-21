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
from .registry import AGENTS, demo_handlers
from .store import Store

HERE = Path(__file__).resolve().parent


def _engine(store: Store) -> TaskEngine:
    eng = TaskEngine(store, AGENTS, runner="cli")
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
        else:
            print(__doc__)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
