# 01 Analyst: Research first, then Graph (and Radar on Sundays): every video better than the last

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/tools.md` | "Research (free)", "Make: stats", "vidIQ budget" | The calls |
| Spec | `../../../specs/studio-floor-v8.md` | "The seven rules" 1 and 7 | Research before making; learn every day |
| Reference | `../references/db.md` | "intel/research", "intel/trends" | Shapes to save |
| Skill | `../../../skills/graph/SKILL.md` | Full file | Checklist |
| Skill | `../../../skills/radar/SKILL.md` | Full file, Sundays only | Trend notes |
| Previous stage | `../output/<day key>-run.md` header | | Credits and the research path (free or vidIQ) |
| Database | pipeline (the last 7 posted: videoId, launch.publishAt, stats, qc), intel/trends (lessons, kill, windowNote, notes), intel/research (yesterday's: do not repeat its items) | | The numbers |

## Process
1. RESEARCH FIRST (V8 rule 1; before the Writer writes a word). Set crew/graph working. Free
   path, one or two ytapi calls through Make (tools.md "Research (free)"): GET /v3/search
   (type video, videoDuration short, order viewCount, publishedAfter = 7 days ago, q = a 3D
   cartoon story Shorts query, maxResults 10, regionCode US, relevanceLanguage en), then GET
   /v3/videos?part=statistics,contentDetails for the ids it returned (views and seconds).
   Keep only English titles (the API also returns Hindi/Urdu cartoon channels). vidIQ research
   tools (vidiq_outliers, vidiq_trending_videos, vidiq_similar_channels; 5 credits each) only
   when stats/channel.vidiqCredits would still be 5 or more AFTER the call; today it is 2
   (renews Nov 19, 2026), so the free path is the path. Write `## Research` in the run notes:
   at least 5 Shorts from the last 7 days, one line each (views, seconds, what the first 1.5
   seconds do as far as the title, description and thumbnail show; "unknown" when they do not
   say), then the patterns to copy: hook timing, length, story shape, series or one-off.
   Structure only, never the content, characters or titles. Fewer than 5 English titles came
   back: say so, use what came back, change the query tomorrow. Save modules/youtube/intel/
   research {day, source, items, patterns, at} (shape in db.md).
2. Numbers: pull the LAST 7 posted episodes' stats in ONE ytapi call (tools.md "Make:
   stats"). Save views/likes/comments into pipeline/<id>.stats {views, likes, comments, at}
   (retention and watch time are not returned by the free API: write "unknown", never a
   guess). Compare at the same age where you can. Write a one-line lesson (what the best one
   did right: hook, story shape, length, posting time, animated lines) and the one weakness
   into intel/trends.lessons (keep the newest 10). Kill list: a story shape or hook style
   whose last two episodes in a row both landed in the bottom half of the 7 by views at the
   same age goes into intel/trends.kill [{shape, why, at}] (keep what is there; add, never
   silently remove; the Writer never reuses a killed shape without a written reason). Sundays:
   compare posting windows over the last 7 posted episodes; write intel/trends.windowNote and
   move the window only when the numbers say so (ep10's 12:49 PM CT is the one data point for
   a midday window: test it before trusting it).
3. Radar (Sundays only): one vidiq_outliers search (tools.md) only when 5 or more credits
   would be left after it; otherwise Radar reads today's `## Research` instead and spends
   nothing. Save 3 observations to intel/trends.notes. Set crew idle.
4. Write `## Numbers` in the run notes: the 7 episodes' views, likes and comments (one line
   each, with seconds and posting window), the lesson, the weakness of the last episode to
   fix tonight, the last posted episode's Judge score and gate score (pipeline qc.judge.score
   and scorecard.score; the Writer must match or beat the Judge score and the build must clear
   85), the kill list (every entry, one line each, newest first, or "kill list: empty"),
   Radar's newest trend notes (intel/trends.notes) in one line each, and on Sundays the
   window note. Notebook outcome lines: for each of the 7 with numbers, if `python3
   factory/notebook/nb.py pending --days 7` lists it, fill it with `nb.py outcome --id <ep id>
   --set views=N,likes=N,comments=N` (real numbers only; "unknown" stays unknown).

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Research | intel/research; run notes `## Research` | shape in db.md |
| Stats, lesson, kill list | pipeline/<id>.stats, intel/trends.lessons, intel/trends.kill, intel/trends.windowNote (Sundays) | shapes in db.md |
| Notebook outcomes | `factory/notebook/results.jsonl` via nb.py outcome | real numbers only |
