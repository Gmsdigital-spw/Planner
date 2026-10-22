#!/usr/bin/env python3
"""GM Agency safety guard (Claude Code PreToolUse hook).

Runs before every Bash, Edit and Write call in a session on this repo, including the
scheduled crew runs. It blocks the few actions that can wreck the shop or the repo and
tells the crew why. A block is final: the crew writes a NEEDS YOU line instead of trying
another way. Everything else passes through untouched, so normal work is not slowed down.

Exit code 2 = deny (the reason on stderr goes back to the model). Exit 0 = allow.
"""
import json
import re
import sys

BASH_RULES = [
    (r"\brm\s+(-[a-zA-Z]*[rR][a-zA-Z]*\s+|--recursive\s+)(-\S+\s+)*(/|~|\$HOME|\.\.?|\*|\./?\*|/home/claude/planner|factory|\.git|\.claude)(/?\s|/?$|/\*)",
     "Deleting a whole folder (rm -r on the repo, home, factory, .git or .claude) is blocked."),
    (r"\bgit\s+push\b[^\n;&|]*(\s--force\b|\s-f\b|\s--force-with-lease\b|\s\+\S)",
     "Force-pushing can erase the crew's history. Pull, rebase and push normally."),
    (r"\bgit\s+reset\s+[^\n;&|]*--hard\b", "git reset --hard can throw away work. Blocked."),
    (r"\bgit\s+clean\s+[^\n;&|]*-[a-zA-Z]*f", "git clean -f deletes untracked files. Blocked."),
    (r"\bgit\s+(branch\s+-D|push\s+\S+\s+--delete|push\s+\S+\s+:)\s*\S*", "Deleting branches is blocked."),
    (r"\bgit\s+filter-(branch|repo)\b", "Rewriting repo history is blocked."),
    (r"\b(DROP\s+(TABLE|DATABASE)|TRUNCATE\s+TABLE)\b", "Dropping database tables is blocked."),
    (r"ALPACA_LIVE\s*=\s*['\"]?(1|true|yes)", "Live-money trading needs Grayson's go. Blocked."),
    (r"\b(cat|less|more|head|tail|printenv|env)\b[^\n;&|]*(\.env\b|credentials|secrets?\.json|id_rsa)", "Printing secrets is blocked."),
    (r"^\s*(printenv|env)\s*$", "Printing every secret in the environment is blocked."),
    (r"(curl|wget)[^\n|]*\|\s*(ba)?sh\b", "Running a script straight off the internet is blocked."),
]

PROTECTED_PATHS = [
    (r"(^|/)\.claude/(hooks/|settings(\.local)?\.json$)", "The safety guard cannot be edited by the crew. Ask Grayson."),
    (r"(^|/)\.env(\.|$)", "Secret files are off limits."),
]


def deny(reason: str) -> None:
    sys.stderr.write(
        "BLOCKED by the GM Agency safety guard: " + reason +
        " Do not try another way around it. Write a NEEDS YOU line in the run doc and move on.\n"
    )
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # never break a run because of a malformed payload
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {}) or {}

    if tool == "Bash":
        cmd = str(inp.get("command", ""))
        for pattern, reason in BASH_RULES:
            if re.search(pattern, cmd, re.IGNORECASE | re.MULTILINE):
                deny(reason)
        # editing the guard through the shell counts too
        if re.search(r"\.claude/(hooks|settings)", cmd) and re.search(r"(>|\bsed\s+-i|\brm\b|\bmv\b|\bcp\b|\btee\b|chmod)", cmd):
            deny("The safety guard cannot be changed by the crew. Ask Grayson.")
    elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = str(inp.get("file_path", "") or inp.get("notebook_path", ""))
        for pattern, reason in PROTECTED_PATHS:
            if re.search(pattern, path):
                deny(reason)
    sys.exit(0)


if __name__ == "__main__":
    main()
