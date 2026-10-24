#!/usr/bin/env python3
"""memory.py: the crew's long-term memory (Grayson, Oct 24, 2026). Python stdlib only; no network.

The memory folder (this file's folder) holds:
  MEMORY.md         the shared memory every run reads first (curated, under 60 lines, newest first)
  facts.md          dated facts with a source, append-only (the long tail behind MEMORY.md)
  decisions.md      Grayson's decisions, dated, with where the full text lives
  agents/<id>.md    one agent's durable memory: what lasts beyond one run (tool quirks, numbers that
                    matter, what Grayson rejected, what worked twice). Read yours at the start,
                    append at the end. The nightly "What I've learned" line stays in the skill file.
  handoffs/         what a Claude session that built something leaves for the next one and for the crews

Commands (run from anywhere; paths are relative to this file):
  python3 memory.py show [--agent <id>]                 print MEMORY.md, then the agent's memory
  python3 memory.py remember --agent <id> --kind fact|lesson|gotcha|decision --text "..." [--source "..."]
  python3 memory.py fact --text "..." --source "..."    append to facts.md
  python3 memory.py promote --text "..." [--source "..."]   add a line every crew needs to MEMORY.md
  python3 memory.py agents                               list every agent memory with its line count
  python3 memory.py prune [--max 60]                     say what to move out of MEMORY.md (never deletes)
  python3 memory.py --selftest

Rules: one line per memory, dated automatically, with a source when there is one. No personal detail,
no secret, no token, no invented number: the repo is public. Memory beats habit; it never beats the
task prompt, CLAUDE.md, the specs or shared/rules.md.
"""
import os, sys, re, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ("fact", "lesson", "gotcha", "decision")
BAD = re.compile(r"(@[a-z0-9.-]+\.[a-z]{2,}|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b|sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{12,})", re.I)

def day():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")
    except Exception:
        return dt.date.today().isoformat()

def path(name):
    return os.path.join(HERE, name)

def agent_path(aid):
    aid = re.sub(r"[^a-z0-9_-]", "", str(aid).lower())
    if not aid:
        raise SystemExit("agent id missing")
    return os.path.join(HERE, "agents", aid + ".md"), aid

def clean(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text:
        raise SystemExit("text missing")
    if BAD.search(text):
        raise SystemExit("refused: that line looks like an email, phone number or secret; memory is public")
    return text[:400]

def append(p, line):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(line.rstrip("\n") + "\n")

def ensure_agent(p, aid):
    if not os.path.exists(p):
        append(p, f"# {aid}: durable memory\n_What lasts beyond one run. Read at the start, append at the end (memory.py remember). Dated, sourced, no personal details._\n")

def show(aid=None):
    m = path("MEMORY.md")
    print(open(m).read().rstrip() if os.path.exists(m) else "(no MEMORY.md yet)")
    if aid:
        p, aid = agent_path(aid)
        print("\n" + ("=" * 60))
        print(open(p).read().rstrip() if os.path.exists(p) else f"(no memory for {aid} yet: start one with memory.py remember)")

def remember(aid, kind, text, source=""):
    if kind not in KINDS:
        raise SystemExit("kind must be one of " + ", ".join(KINDS))
    p, aid = agent_path(aid)
    ensure_agent(p, aid)
    line = f"- {day()} ({kind}): {clean(text)}" + (f" [{clean(source)}]" if source else "")
    append(p, line)
    print("remembered for", aid + ":", line)

def fact(text, source=""):
    line = f"- {day()}: {clean(text)}" + (f" [{clean(source)}]" if source else "")
    append(path("facts.md"), line)
    print("fact:", line)

def promote(text, source=""):
    m = path("MEMORY.md")
    line = f"- {day()}: {clean(text)}" + (f" [{clean(source)}]" if source else "")
    s = open(m).read() if os.path.exists(m) else "# Crew memory\n"
    marker = "## Promoted by the crew"
    if marker not in s:
        s = s.rstrip("\n") + "\n\n" + marker + "\n_Lines added by runs with memory.py promote; the commander prunes these weekly._\n"
    s = s.rstrip("\n") + "\n" + line + "\n"
    open(m, "w").write(s)
    print("promoted:", line)
    prune(60, quiet=True)

def agents():
    d = os.path.join(HERE, "agents")
    if not os.path.isdir(d):
        print("(no agent memories yet)"); return
    for n in sorted(os.listdir(d)):
        if n.endswith(".md"):
            lines = [l for l in open(os.path.join(d, n)) if l.startswith("- ")]
            print(f"{n[:-3]:<14} {len(lines):>3} memories")

def prune(mx=60, quiet=False):
    m = path("MEMORY.md")
    if not os.path.exists(m):
        return
    lines = open(m).read().splitlines()
    n = len([l for l in lines if l.strip()])
    if n > mx:
        print(f"MEMORY.md has {n} non-empty lines (max {mx}): the commander moves the oldest promoted lines to facts.md")
        promoted = [l for l in lines if l.startswith("- 20")]
        for l in promoted[:max(1, n - mx)]:
            print("  oldest:", l[:120])
    elif not quiet:
        print(f"MEMORY.md ok: {n} lines of {mx}")

def selftest():
    import tempfile, shutil
    global HERE
    keep = HERE
    HERE = tempfile.mkdtemp()
    try:
        open(path("MEMORY.md"), "w").write("# Crew memory\n- 2026-10-24: a seed line\n")
        remember("vega", "gotcha", "a   gotcha   line", "run notes 10-24")
        p, _ = agent_path("vega")
        s = open(p).read()
        assert s.count("(gotcha): a gotcha line [run notes 10-24]") == 1, s
        try:
            remember("vega", "fact", "mail me at someone@example.com"); raise AssertionError("email not refused")
        except SystemExit as e:
            assert "refused" in str(e)
        promote("every crew needs this")
        assert "## Promoted by the crew" in open(path("MEMORY.md")).read()
        fact("a fact", "source")
        assert open(path("facts.md")).read().count("a fact [source]") == 1
        print("memory selftest ok")
    finally:
        shutil.rmtree(HERE, ignore_errors=True)
        HERE = keep

def arg(args, key, default=None):
    if key in args:
        i = args.index(key)
        if i + 1 < len(args):
            return args[i + 1]
    return default

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    c = argv[0]
    if c == "--selftest": selftest(); return 0
    if c == "show": show(arg(argv, "--agent")); return 0
    if c == "remember": remember(arg(argv, "--agent"), arg(argv, "--kind", "fact"), arg(argv, "--text"), arg(argv, "--source", "")); return 0
    if c == "fact": fact(arg(argv, "--text"), arg(argv, "--source", "")); return 0
    if c == "promote": promote(arg(argv, "--text"), arg(argv, "--source", "")); return 0
    if c == "agents": agents(); return 0
    if c == "prune": prune(int(arg(argv, "--max", 60))); return 0
    print("unknown command", c); return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
