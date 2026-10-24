# 02 Write: Gags (two drafts) and Judge

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/episode-rules.md` | Full file | The bar |
| Spec | `../../../specs/studio-floor-v6.md` | "The bar Grayson set", "Free animation lane" | Grayson's standing order (anim flags, the bar) |
| Skill | `../../../skills/gags/SKILL.md`, `../../../skills/judge/SKILL.md` | Full files | Checklists |
| Lessons | `../../../LESSONS.md` | Full file | Numbers-only lessons |
| Previous stages | `../output/<day key>-run.md` "## Premises", "## Numbers" | | Existing premises; the lesson, weakness, score to beat, trend notes |
| Database | intel/trends (lessons, cast, notes, orders) | | Recurring cast; orders from Atlas Prime |

## Process
1. Set crew/gags working. Write TWO scripts to episode-rules.md (two drafts rule), each using
   the latest lesson and fixing the named weakness; if the brief names a drop-zone clip, use
   it as the hook or twist scene. Any active order in intel/trends.orders shapes the choice.
2. Set crew/judge working. Score both (hook, story, twist, logic, 1 to 10), each with one line
   of evidence, and record each draft with the tool: `python3 factory/learning/learn.py score
   --scope studio --agent judge --rubric studio-judge-x10 --ratings '{"hook":{"points":9,
   "evidence":"..."},"story":{...},"twist":{...},"logic":{...}}' --beat <the last posted episode's
   Judge score from "## Numbers"> --job <day key>:<episode id>:<A|B> --item "<logline>"`. The tool
   keeps the Studio's own bar (every score 7+, the average above the score to beat) as blockers;
   it never mixes these numbers with the Etsy rubric. Choose per the two-drafts rule; rewrite once
   if needed (score again with the same --job); if still short, build nothing: log why and stop
   this worker (the coordinator messages Grayson in one line).
3. Save the winner to episodes/<id> {id, num, title, ytTitle, logline, hook, beats, shots, vo
   (the lines), pinned, tags, description, sound:{voice, speed, music, music_volume, anim:
   [line numbers to animate per the spec's free animation lane]}} and the loser to
   episodes/<id>-b status "unbuilt". Save qc.judge
   {score, hook, story, twist, logic, slop, improvedOver, drafts, at} to pipeline/<id>. Crew idle.
4. Write `## Drafts` in the run notes (both loglines, both score sets, the choice, the
   voice, the music mood).

## Audit

| Check | Pass condition |
|-------|---------------|
| Logic | Every event follows from the one before; the twist surprises and makes sense looking back |
| Originality | No existing character, brand, celebrity or another channel's premise |
| Loop | Line 1 is the cold open; the last line cuts back into it |
| Emotion | At least one emotional beat drawn as its own close-up line |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Episode | episodes/<id>, episodes/<id>-b | shapes in db.md |
| Judge | pipeline/<id>.qc.judge | |
