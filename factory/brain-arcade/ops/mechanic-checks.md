# Mechanic checks for the Brain Arcade lane (every Mechanic run)

The Mechanic reads this lane through its ROOM DATABASE (no repo needed, so it works while the lane
lives on its own branch): ArtifactData url https://claude.ai/artifact/RuApFd8YnEgouX4ogv6D2i,
doc status/main {at, lights, shopVerified, listedTotal, views, favs, sales, topLesson, nextMove,
needsYou[], blocked, lastRun{task,outcome,note,at}}.

1. Scheduled tasks "Brain Arcade · Night Build" (3:22 AM), "Brain Arcade · Publisher" (9:17 AM,
   3:17 PM), "Brain Arcade · Learn" (8:41 PM): last_run not SUCCEEDED or a window missed by 2+ hours
   -> fire_trigger ONCE per day (same refired rule as the other tasks).
2. status/main: blocked true, lastRun.outcome "failed"/"blocked", or "at" older than 30 hours ->
   red light "arcade" + one needsYou line with the exact tap. needsYou lines go to the report as-is
   (dedupe: once a day each).
3. A guard BLOCK is never retried by re-firing the Publisher; it is reported.
4. The Mechanic never edits Brain Arcade files, its Make scenario, its listings or its room docs.

Morning report (6:47 AM): add line 5 from status/main:
"🕹️ Brain Arcade: <listedTotal> listed · <views> views · <favs> favs · <sales> sales · <topLesson or 'no lesson proven yet'> · Next: <nextMove>"
(null numbers print as "unknown"; keep it to one line, two only when needsYou has something).
