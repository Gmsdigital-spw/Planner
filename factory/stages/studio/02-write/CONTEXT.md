# 02 Write: Gags (two drafts) and Judge

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/episode-rules.md` | Full file | The bar |
| Spec | `../../../specs/studio-floor-v8.md` | Full file (it wins over V6) | Grayson's standing order: the seven rules, the hook, the length, the anim lines, the kill list |
| Spec | `../../../specs/studio-floor-v6.md` | "The bar Grayson set", "Free animation lane" | The older bar where V8 is silent; how the free animation lane works |
| Skill | `../../../skills/gags/SKILL.md`, `../../../skills/judge/SKILL.md` | Full files | Checklists |
| Lessons | `../../../LESSONS.md` | Full file | Numbers-only lessons |
| Previous stages | `../output/<day key>-run.md` "## Premises", "## Research", "## Numbers" | | Existing premises; what works right now; the lesson, weakness, scores to beat, kill list, trend notes |
| Database | intel/trends (lessons, kill, cast, notes, orders), intel/research (today) | | Recurring cast; killed shapes; orders from Atlas Prime |

## Process
1. Set crew/gags working. Read `## Research` and `## Numbers` first: copy the structure that
   is working this week (hook timing, length, story shape), never its content, characters or
   titles. Write TWO scripts to episode-rules.md (two drafts rule), each using the latest
   lesson and fixing the named weakness. Every draft: line 1 is the hook and moves (anim true
   or the drop-zone clip), 9 words or fewer, and the on-screen hook is 3 to 8 uppercase words
   with a question mark, a number or a shock word (V8 rule 2: the first 1.5 seconds); 7 to 12
   lines of 9 words or fewer each, 20 to 45 seconds read aloud (aim 25 to 40); setup, problem,
   twist (motion punch, never the first or last line), payoff, loop. Mark anim on line 1 and
   the twist, an optional third on the one emotional beat (never more than 3). Never a story
   shape or hook style on intel/trends.kill without a written reason in `## Drafts`. If the
   brief names a drop-zone clip, use it as the hook or twist scene. Any active order in
   intel/trends.orders shapes the choice.
2. Set crew/judge working. Score both (hook, story, twist, logic, 1 to 10; every score 7+).
   Also check what the scorecard will check later: the hook text rule, the twist line marked
   punch, the loop (same prompt first and last, pause 0.05), every line 9 words or fewer, 7
   to 12 lines; a draft that misses one gets it fixed before scoring. Choose per the
   two-drafts rule; rewrite once if needed; if still short, build nothing: log why and stop
   this worker (the coordinator messages Grayson in one line).
3. Save the winner to episodes/<id> {id, num, title, ytTitle, titleCandidates, logline, hook,
   beats, shots, vo (the lines), pinned, tags, description, sound:{voice, speed, music,
   music_volume, anim: [line numbers to animate: 1, the twist, optional emotional beat]}} and
   the loser to episodes/<id>-b status "unbuilt". titleCandidates = 2 or 3 titles written
   for scoring in stage 05 (each a question or a shock, under 60 characters, ends " #shorts";
   the first is ytTitle). Save qc.judge
   {score, hook, story, twist, logic, slop, improvedOver, drafts, at} to pipeline/<id>. Crew idle.
4. Write `## Drafts` in the run notes (both loglines, both score sets, the choice, the
   voice, the speed, the music mood, the anim lines, the story shape and hook style in two
   words each (the notebook tags shape= and hook=), the title candidates, and the written
   reason if a killed shape was used).

## Audit

| Check | Pass condition |
|-------|---------------|
| Logic | Every event follows from the one before; the twist surprises and makes sense looking back |
| Originality | No existing character, brand, celebrity or another channel's premise |
| Loop | Line 1 is the cold open; the last line cuts back into it (same image prompt, pause 0.05, loop true) |
| Emotion | At least one emotional beat drawn as its own close-up line |
| Hook | Line 1 is 9 words or fewer and marked anim (or a real clip); the hook field is 3 to 8 uppercase words with a question mark, a number or a shock word |
| Length | 7 to 12 lines, each 9 words or fewer; 20 to 45 seconds read aloud (aim 25 to 40) |
| Twist | One line marked punch, never the first or last, marked anim |
| Kill list | No shape or hook style from intel/trends.kill without a written reason in `## Drafts` |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Episode | episodes/<id>, episodes/<id>-b | shapes in db.md |
| Judge | pipeline/<id>.qc.judge | |
