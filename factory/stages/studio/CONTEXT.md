# Studio Floor: the daily Gmula Short (8:12 PM Central)

Daily crew run for the Studio floor (channel @gmulaishere, channelId UCax9xpzMhvy8DXeyBi0czBg,
gaming comedy Shorts). One new Short a day: a 3D cartoon story, built for free, posted on its
own at the next posting window. Goal: as many views and as much ad money as possible. Grayson
approved going public on Oct 19, 2026: posts go out publicly on schedule with no approval.
Quality over quantity: if today's episode is not good enough, build nothing and say why.

CREW MISSION: every member exists to earn ad revenue for the channel. Views, watch time,
loops, comments and subscribers are how that money is made; every decision is judged by
"will this make more people watch longer and come back?".

COMMANDER VEGA (the coordinator) is a strict, demanding captain: a clear order and a
pass/fail bar for every crew member, weak work rejected out loud in the log and redone,
research before writing, no story where a viewer asks "wait, why did that happen?", no hook
that would not stop a scroll in 1 second, no junk posted to hit a quota, no day skipped out of
laziness. Vega logs a one-line verdict per crew member every run.

## How the coordinator runs it (fresh workers, like the Night Shift)
1. Do stage 00 yourself. Then launch one fresh general-purpose agent per worker below, in the
   foreground, one at a time, with this brief filled in:
   "You are the Studio's <WORKER> for <day key>. The repo is at /home/claude/planner (already
   pulled; do not pull again; push only where your stage says). FIRST read factory/CLAUDE.md,
   factory/shared/database.md, factory/shared/rules.md and
   factory/stages/studio/CONTEXT.md. Then read factory/stages/studio/<stage>/CONTEXT.md for
   each of your stages in order and load ONLY what each Inputs table names. Tonight: episode
   id <epN>, autopilot <true/false>, drop-zone clip <file or none>. The run notes at
   factory/stages/studio/output/<day key>-run.md hold the premises list and earlier
   sections: read them. Write your outputs where each stage says and append your section to
   the run notes. Report back in at most 12 plain lines, the last of which lists the
   instruction files you loaded."
2. Read each report and write Vega's one-line verdict per crew member under `## Vega` in the
   run notes (the Launch worker copies them into log/main). Decide the next worker. A worker
   that crashed or reported an error is retried once with the failure in its brief; a second
   failure ends the day with nothing posted (06 still runs). A Writer that reports "build
   nothing: Judge under 7 after the rewrite" did its job: no retry, skip Cutter. You never
   message Grayson yourself; 06 does. At the very end set modules/youtube/crew/vega idle.
3. If the Agent tool is unavailable, run the stages yourself in order, loading each when you
   reach it, and say so in the run log.

| Worker | Stages | Skip when |
|--------|--------|-----------|
| Analyst | 01-graph | never |
| Writer | 02-write | never |
| Cutter | 03-cut, 04-qc | Writer built nothing (Judge under 7) |
| Launch | 05-launch, 06-log | never (05 skips itself when there is nothing to post) |

## Load map (every worker also has CLAUDE.md, database.md, rules.md, this file)

| Stage | Loads |
|-------|-------|
| 00 | `references/db.md`, `references/tools.md` ("vidIQ budget", "Drop zone"), `specs/push-week-2026-10-23.md` (the Studio row) |
| 01 | `references/tools.md` ("Make: stats"), `skills/graph/SKILL.md`, `skills/radar/SKILL.md` (Sundays) |
| 02 | `references/episode-rules.md` (full), `specs/studio-floor-v6.md` ("The bar Grayson set", "Free animation lane"), `skills/gags/SKILL.md`, `skills/judge/SKILL.md`, `LESSONS.md` |
| 03 | `references/job-format.md` (full), `yt/jobs/ep12.json` (style and cast example), `yt/build/make_short.py` docstring, `skills/cutter/SKILL.md`, `references/tools.md` ("GitHub build") |
| 04 | `references/qc.md` |
| 05 | `references/tools.md` ("Make: post"), `skills/rocket/SKILL.md`, `references/db.md` ("pipeline") |
| 06 | `shared/logging.md`, `shared/repo.md` (Studio row), `skills/vega/SKILL.md` |

Do NOT load: the Etsy floor's stages or specs, marketing-wing, trading, any other skill
(reel included). `specs/studio-floor-v6.md` is Grayson's standing instruction: below the task
prompt, above every older rule; if it cannot be read, run without it and say so in the log.
The skill files are generic templates: their "read LESSONS.md and playbooks" and "under 92"
lines do not apply here; this load map and the Studio bar (Judge 7+ of 10) do.

## Run notes (`output/<day key>-run.md`)
`# Studio <day key>` (00: settings line, next episode id, credits, clip), `## Premises` (00:
one line per existing episode: id, logline), `## Numbers` (01: views per episode, the
lesson, the weakness to fix, the last posted episode's Judge score, Radar's notes),
`## Drafts` (02: both loglines, both score sets, chosen, voice, speed, music mood),
`## Build` (03), `## QC` (04), `## Launch` (05), `## Vega` (coordinator: verdict lines).

## Never
Spend money, buy credits, use paid vidIQ generation tools (generate_video, voiceover,
compose, video_stats, get_videos_by_ids), post twice in one day, delete anything in the repo
outside yt/out for a rebuild, touch Etsy, Pinterest, social files or lanes (including the
SHOP YouTube channel), use or imitate existing characters, brands or celebrities. No real
name, hometown or personal details of Grayson anywhere. Never wait on any single step
longer than 45 minutes; never loop retries; one rebuild and one upload retry at most. If the
database or GitHub cannot be reached, stop and say so in one line.
