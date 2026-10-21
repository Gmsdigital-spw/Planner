# Studio database (everything under modules/youtube/; never write YouTube data anywhere else)

Docs: modules/youtube/settings/main, modules/youtube/stats/channel, modules/youtube/intel/
trends, modules/youtube/factory/main, modules/youtube/episodes/<id>, modules/youtube/pipeline/
<id>, modules/youtube/log/main ({items:[{t,text}]}, newest first, max 40), modules/youtube/
crew/<id> ({state:"working"|"idle", task, room, updatedAt}; ids vega, radar, gags, cutter,
judge, rocket, graph; rooms control, radar, writers, edit, qc, launch, analytics). Set a crew
member working while they work and idle after; leave everyone idle at the end. Read before
every write; if_version.

## episodes/<id>
{id, num, title, ytTitle, logline, hook, beats, shots, vo (the lines), pinned, tags,
description, sound:{voice, speed, music, music_volume, anim}}. The loser of
the two drafts is saved as episodes/<id>-b with status "unbuilt" so its premise is never
repeated. Next id = one more than the highest ep number in episodes/ and yt/jobs/. Ignore job
ids that do not start with "ep".

## pipeline/<id>
{made:{clips, voice, edit}, videoId, videoTitle, privacy:"scheduled", duration:"PT<n>S",
launch:{mode:"schedule", privacy:"private", publishAt, at}, qc:{judge:{score, hook, story,
twist, logic, slop, improvedOver, drafts:{a:{logline, scores}, b:{logline, scores}, chosen},
at}, file:{pass, duration, mb, frames, rebuilt, at}}, stats:{views, likes, comments, at},
autoVideo:{url, note:"Built free in the factory", credits:0}}. Status
"built-awaiting-launch" when autopilot is false.

## factory/main
{lastBuildAt, lastBuildId, lastDuration, lastMb, lastError (or ""), builtThisWeek,
totalBuilt, postedThisWeek, usedClips, nextRun:"tomorrow 8:12 PM CT", tts}.

## intel/trends
{lessons (newest 10), windowNote, notes (Radar), cast (recurring cast), orders (from Atlas
Prime: [{t, text, status}])}.

## Fleet
fleet/commander/audit/<day key>: append one line {t, who:"Vega", mod:"youtube", text} saying
what was built and posted or why nothing was, plus the two drafts' averages and which was
built (read first; newest 200).
