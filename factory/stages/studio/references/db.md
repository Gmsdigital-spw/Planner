# Studio database (everything under modules/youtube/; never write YouTube data anywhere else)

Docs: modules/youtube/settings/main, modules/youtube/stats/channel ({vidiqCredits, ...}),
modules/youtube/intel/trends, modules/youtube/intel/research, modules/youtube/factory/main,
modules/youtube/episodes/<id>, modules/youtube/pipeline/<id>, modules/youtube/log/main ({items:[{t,text}]}, newest first, max 40), modules/youtube/
crew/<id> ({state:"working"|"idle", task, room, updatedAt}; ids vega, radar, gags, cutter,
judge, rocket, graph; rooms control, radar, writers, edit, qc, launch, analytics). Set a crew
member working while they work and idle after; leave everyone idle at the end. Read before
every write; if_version.

## episodes/<id>
{id, num, title, ytTitle, titleCandidates (2 or 3 titles for stage 05 to score), logline,
hook, beats, shots, vo (the lines), pinned, tags, description, sound:{voice, speed, music,
music_volume, anim (line numbers: 1, the twist, optional emotional beat; max 3)}}. The loser of
the two drafts is saved as episodes/<id>-b with status "unbuilt" so its premise is never
repeated. Next id = one more than the highest ep number in episodes/ and yt/jobs/. Ignore job
ids that do not start with "ep".

## pipeline/<id>
{made:{clips, voice, edit}, videoId, videoTitle, privacy:"scheduled", duration:"PT<n>S",
launch:{mode:"schedule", privacy:"private", publishAt, window ("weekday-7pm"|"weekend-1130am"
|"test-midday"), at}, qc:{judge:{score, hook, story, twist, logic, slop, improvedOver,
drafts:{a:{logline, scores}, b:{logline, scores}, chosen}, at}, file:{pass, duration, mb, frames, rebuilt, at}}, scorecard:{score, pass, fixes, at} (the V8 scorecard, stage 04; the Atlas Hub reads this field), titleScore (the
sidecar's title_score or null), stats:{views, likes, comments, at}, autoVideo:{url,
note:"Built free in the factory", credits:0}}. Status "built-awaiting-launch" when autopilot
is false; "not-posted-gate" when the gate stayed under 85.

## factory/main
{lastBuildAt, lastBuildId, lastDuration, lastMb, lastScore (the gate score), lastError (or
""), builtThisWeek, totalBuilt, postedThisWeek, usedClips, nextRun:"tomorrow 8:12 PM CT",
tts}.

## intel/trends
{lessons (newest 10), windowNote, notes (Radar), cast (recurring cast), kill ([{shape, why,
at}]: story shapes and hook styles that lost twice in a row; the Writer never reuses one
without a written reason; add, never silently remove), orders (from Atlas Prime: [{t, text,
status}])}.

## intel/research
One doc, rewritten every run by the Analyst (V8 rule 1): {day, source ("ytapi" or the vidIQ
tool used), items:[{videoId, title, channel, views, seconds, published, first_1_5s}] (at
least 5 Shorts from the last 7 days, English titles only), patterns:[...] (the structure to
copy: hook timing, length, story shape, series or one-off), at}. Never a real creator's
content, characters or title copied into an episode.

## Sidecars in the repo (not the database)
- yt/jobs/<id>.research.json (stage 05, read by the gate): {title, title_score (number or
  null), scored_at, credits_before, credits_after, why ("credits N of 5" when not scored)}.
- yt/out/<id>.score.json (the gate, `--write`; the Action writes it too): {schema, version,
  id, score, pass, passmark 85, at, checks:{<check>:{ok, pts, evidence}}, fixes}. No score
  file = not passed.

## Fleet
fleet/commander/audit/<day key>: append one line {t, who:"Vega", mod:"youtube", text} saying
what was built and posted or why nothing was, plus the two drafts' averages and which was
built (read first; newest 200).
