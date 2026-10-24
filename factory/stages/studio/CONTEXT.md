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
that would not stop a scroll in 1.5 seconds, no junk posted to hit a quota, no day skipped out of
laziness. Vega logs a one-line verdict per crew member every run.

## V8 (Oct 24, 2026)
Grayson's new standing order is `specs/studio-floor-v8.md` ("stop the flatline"). It wins over
`specs/studio-floor-v6.md` wherever they differ; V6's Spot lane and "paid hero-shot lane stays
OFF" still stand. The seven rules, one line each:
1. Research before making: the Analyst pulls 5+ Shorts from the last 7 days (free ytapi path
   first; vidIQ only with 5+ credits) and writes `## Research` before a word is written.
2. Hook in the first 1.5 seconds: line 1 moves (anim true or a real clip), 9 words or fewer;
   the on-screen hook is 3 to 8 uppercase words with a question mark, a number or a shock word.
3. A real story that loops: setup, problem, twist (motion punch, never first or last), payoff,
   last line cuts back into line 1; Judge still scores hook, story, twist, logic 7+ each.
4. Real animation, not a slideshow: anim true on line 1 and the twist, an optional third on
   the one emotional beat, never more than 3, never a paid tier or a second account.
5. Natural voice, safe captions, a beat every 2 to 3 seconds: edge andrew or ava at 0.95 to
   1.06, 7 to 12 lines of 9 words or fewer, 20 to 45 seconds total (aim 25 to 40), no scene
   over 4.0 s (5.5 s with real motion), measured from the built file's word timings.
6. The quality gate: `python3 studio/quality_gates.py short <id> --write` after every build;
   85+ of 100 posts, under 85 = fix the named checks with the day's one rebuild, still under
   85 = not posted. Judge 7+ AND scorecard 85+ are the two gates.
7. Learn every day: Graph reads the last 7 posted Shorts, writes the lesson and the weakness,
   keeps the kill list (shapes that lost twice in a row), adds one notebook line per Short;
   Sundays compare posting windows.

## How the coordinator runs it (fresh workers, like the Night Shift)
1. Do stage 00 yourself. Then launch one fresh general-purpose agent per worker below, in the
   foreground, one at a time, with this brief filled in:
   "You are the Studio's <WORKER> for <day key>. The repo is at /home/claude/planner (already
   pulled; do not pull again; push only where your stage says). FIRST read factory/CLAUDE.md,
   factory/shared/database.md, factory/shared/rules.md and
   factory/stages/studio/CONTEXT.md. Then read factory/stages/studio/<stage>/CONTEXT.md for
   each of your stages in order and load ONLY what each Inputs table names. Tonight: episode
   id <epN>, autopilot <true/false>, vidIQ credits <n> (research path: free ytapi or vidIQ),
   drop-zone clip <file or none>. The run notes at
   factory/stages/studio/output/<day key>-run.md hold the premises list and earlier
   sections: read them. Write your outputs where each stage says and append your section to
   the run notes. Report back in at most 12 plain lines, the last of which lists the
   instruction files you loaded."
2. Read each report and write Vega's one-line verdict per crew member under `## Vega` in the
   run notes (the Launch worker copies them into log/main). Decide the next worker. A worker
   that crashed or reported an error is retried once with the failure in its brief; a second
   failure ends the day with nothing posted (06 still runs). A Writer that reports "build
   nothing: Judge under 7 after the rewrite" did its job: no retry, skip Cutter. A Cutter that
   reports "not posted: gate <score> after the rebuild" did its job too: no retry; Launch still
   runs (05 skips itself, 06 logs the score and the fixes). You never
   message Grayson yourself; 06 does. At the very end set modules/youtube/crew/vega idle.
3. If the Agent tool is unavailable, run the stages yourself in order, loading each when you
   reach it, and say so in the run log.

| Worker | Stages | Skip when |
|--------|--------|-----------|
| Analyst | 01-graph (the Research step first, then the numbers) | never |
| Writer | 02-write | never |
| Cutter | 03-cut, 04-qc (the build, then the gate) | Writer built nothing (Judge under 7) |
| Launch | 05-launch, 06-log | never (05 skips itself when there is nothing to post or the gate failed) |

## Load map (every worker also has CLAUDE.md, database.md, rules.md, this file)

| Stage | Loads |
|-------|-------|
| 00 | `references/db.md`, `references/tools.md` ("vidIQ budget", "Drop zone"), `specs/studio-floor-v8.md` ("The seven rules" 1, "Title, description and tags"), `specs/push-week-2026-10-23.md` (the Studio row) |
| 01 | `references/tools.md` ("Research (free)", "Make: stats", "vidIQ budget"), `specs/studio-floor-v8.md` ("The seven rules" 1 and 7), `references/db.md` ("intel/research", "intel/trends"), `skills/graph/SKILL.md`, `skills/radar/SKILL.md` (Sundays) |
| 02 | `references/episode-rules.md` (full), `specs/studio-floor-v8.md` (full; it wins over V6), `specs/studio-floor-v6.md` ("The bar Grayson set", "Free animation lane"), `skills/gags/SKILL.md`, `skills/judge/SKILL.md`, `LESSONS.md` |
| 03 | `references/job-format.md` (full), `yt/jobs/ep12.json` (style and cast example), `yt/build/make_short.py` docstring, `skills/cutter/SKILL.md`, `references/tools.md` ("GitHub build", "Scorecard") |
| 04 | `references/qc.md`, `specs/studio-floor-v8.md` ("The seven rules" 4 and 6), `references/tools.md` ("Scorecard") |
| 05 | `references/tools.md` ("Make: post", "vidIQ budget"), `specs/studio-floor-v8.md` ("Title, description and tags", "One great Short a day"), `skills/rocket/SKILL.md`, `references/db.md` ("pipeline", "Sidecars in the repo") |
| 06 | `shared/logging.md`, `shared/repo.md` (Studio row), `skills/vega/SKILL.md` |

Do NOT load: the Etsy floor's stages or specs, marketing-wing, trading, any other skill
(reel included). `specs/studio-floor-v8.md` is Grayson's standing instruction: below the task
prompt, above every older rule, above `studio-floor-v6.md` where they differ; if it cannot be
read, run without it and say so in the log.
The skill files are generic templates: their "read LESSONS.md and playbooks" and "under 92"
lines do not apply here; this load map and the Studio bar (Judge 7+ of 10 AND scorecard 85+
of 100) do.

Grayson's story-short backgrounds (Oct 23, 2026): assets/atlas-pack/story_shorts (forest sunrise,
cabin in the rain; README there). Photo-real: never mixed into a cartoon episode.

## Run notes (`output/<day key>-run.md`)
`# Studio <day key>` (00: settings line, next episode id, credits and research path, clip),
`## Premises` (00: one line per existing episode: id, logline), `## Research` (01: at least 5
Shorts from the last 7 days with views, seconds and what the first 1.5 s do; the patterns to
copy), `## Numbers` (01: views, likes and comments for the last 7 posted episodes, the
lesson, the weakness to fix, the last posted episode's Judge score and gate score, the kill
list, Radar's notes, Sunday's window note), `## Drafts` (02: both loglines, both score sets,
chosen, voice, speed, music mood, anim lines, title candidates), `## Build` (03: duration,
MB, animated lines, scene lengths, the gate score), `## QC` (04: PASS/FAIL, score, fixes,
frames), `## Launch` (05), `## Vega` (coordinator: verdict lines).

## Never
Spend money, buy credits, use paid vidIQ generation tools (generate_video, voiceover,
compose, video_stats, get_videos_by_ids), post twice in one day, delete anything in the repo
outside yt/out for a rebuild, touch Etsy, Pinterest, social files or lanes (including the
SHOP YouTube channel), use or imitate existing characters, brands or celebrities. No real
name, hometown or personal details of Grayson anywhere. Never post under 85 on the scorecard
or under Judge 7; never claim a Short "passed" without yt/out/<id>.score.json to show for it;
never copy a real creator's characters, premise or title. Never wait on any single step
longer than 45 minutes; never loop retries; one rebuild and one upload retry at most. If the
database or GitHub cannot be reached, stop and say so in one line.

## Notebook (Grayson, Oct 23, 2026)
Before stage 01, run `python3 factory/notebook/nb.py show --lane shorts` and follow its "Grayson's rules", "What works" and "What doesn't work" lines. After the day's Short is built, stage 06 adds one notebook line for it (`nb.py add --lane shorts`, tags hook=, shape=, seconds=, window=, anim=, score=; V8 rule 7). The Night Shift's keeper fills in each Short's results at 7 days.
