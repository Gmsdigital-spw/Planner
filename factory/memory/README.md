# Crew memory (Grayson, Oct 24, 2026): the agents remember everything that lasts

Why: every run used to start from the skill file and the stage files alone, so a fact learned on
Tuesday was gone by Thursday unless someone wrote it into a spec. This folder is the crew's
long-term memory. It is read at the start of every run and written at the end, by every agent,
with the helper `memory.py` (stdlib, no network).

| File | What it holds | Who writes it |
|---|---|---|
| `MEMORY.md` | The shared memory every run reads first: standing truths, gotchas, where things live. Under 60 lines, newest first. | Claude sessions and the commander (`memory.py promote` adds a line; the commander prunes weekly) |
| `facts.md` | Dated facts with a source, append-only: the long tail behind MEMORY.md. | Any agent (`memory.py fact`) |
| `decisions.md` | Grayson's decisions, dated, in his words, with where the full text lives. | Claude sessions after a chat with Grayson; the Night Shift's Report for in-app decisions |
| `agents/<id>.md` | One agent's durable memory: tool quirks, numbers that matter, what Grayson rejected, what worked twice. | That agent, at the end of every run (`memory.py remember --agent <id>`) |
| `handoffs/<date>-<topic>.md` | What a Claude session that built something leaves behind: what it built, verified, learned, left open. | The session, before it ends |

The nightly "What I've learned" line stays in `skills/<id>/SKILL.md`; `LESSONS.md` and `notebook/`
keep the numbers-backed lessons. Memory is for what lasts: a fact, a quirk, a decision, a gotcha.

## The rule (also in CLAUDE.md)
1. Before working: `python3 factory/memory/memory.py show --agent <id>`.
2. After working: `python3 factory/memory/memory.py remember --agent <id> --kind fact|lesson|gotcha|decision --text "..." --source "..."` for anything that would help the next run. One line each.
3. A fact every crew needs: `memory.py promote --text "..."`. The commander keeps MEMORY.md under 60 lines (`memory.py prune`), moving stale lines to facts.md.
4. Never a personal detail, a secret, a token or an invented number (the helper refuses emails, phone numbers and key-shaped strings). The repo is public.
5. Memory beats habit. It never beats the task prompt, CLAUDE.md, the specs or shared/rules.md.
