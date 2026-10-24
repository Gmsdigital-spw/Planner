# 03 Cutter: the job file, dry run, build, then the gate

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/job-format.md` | Full file | The job schema and the build loop |
| Example | `yt/jobs/ep12.json` | "style" and "cast" | Copy style exactly; cast shape |
| Builder | `yt/build/make_short.py` | docstring only | The format |
| Reference | `../references/tools.md` | "GitHub build", "Scorecard" | Push rules, Cloudflare, the gate command |
| Skill | `../../../skills/cutter/SKILL.md` | Full file | Checklist |
| Database | episodes/<id> (vo, hook, title, description, tags, sound incl. anim) | | The script, voice, speed, music mood, the lines to animate |
| Previous stage | `../output/<day key>-run.md` "## Drafts" | | The choices in one place |

## Process
1. Set crew/cutter working. Write yt/jobs/<id>.json per job-format.md from episodes/<id>:
   "anim": true on line 1 and the twist line (the optional third on the emotional beat only
   if sound.anim names it; never more than 3), motion "punch" on the twist, the hook field
   as written (3 to 8 uppercase words), loop true with the last line's prompt identical to
   line 1's and pause 0.05, every line 9 words or fewer (split a long line into two scenes
   rather than trim its meaning).
2. Dry-run, push only a passing job (commit "Studio <day key>: <id>", pull --rebase, push),
   wait for the build, one rebuild at most, exactly as job-format.md says. You may git pull
   to receive the build output; that is the one exception to "do not pull again".
3. The gate after the build: pull, then run `python3 studio/quality_gates.py short <id>
   --write` (the Action runs it too and saves yt/out/<id>.score.json; run it yourself anyway
   so the card is in your hands). Read the scene lengths it reports: they come from the built
   file's word timings in yt/out/<id>.json (no still scene over 4.0 s, 5.5 s with real
   motion, mean under 3.5 s), never from a guess. Check the warnings for "line N: real motion
   from the free animation lane": line 1 and the twist must be there. Do not rebuild for the
   score here; stage 04 owns that decision and the day's one rebuild (a rebuild already used
   for a build error counts).
4. Update modules/youtube/factory/main {lastBuildAt, lastBuildId, lastDuration, lastMb,
   lastScore, lastError (or ""), builtThisWeek, totalBuilt, usedClips, nextRun:"tomorrow
   8:12 PM CT", tts}. Crew idle. Write `## Build` in the run notes (duration, MB, rebuilds,
   warnings, which lines got real motion, longest and mean scene length, the gate score and
   its fixes list).

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Built Short | yt/out/<id>.mp4, yt/out/<id>.json | from the Action |
| Scorecard | yt/out/<id>.score.json | {score, pass, checks, fixes} from the gate |
| Factory state | modules/youtube/factory/main | |
