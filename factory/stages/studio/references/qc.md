# QC of the built file (stage 04): the gate first, then the eyes

## The gate (V8 rule 6)
`python3 studio/quality_gates.py short <id> --write` reads yt/jobs/<id>.json, yt/out/<id>.json
and, when it exists, yt/jobs/<id>.research.json, decides 10 checks from those files and saves
yt/out/<id>.score.json {score, pass, checks, fixes}. Exit 0 = PASS (85+), 1 = FAIL, 2 = cannot
judge (a missing file or a failed build; not a pass). The GitHub build Action runs the same
gate after every build. The checks and points: hook motion in the first 1.5 s 15, hook text a
question or a shock 10, story has a twist (punch, not first or last) 15, ending loops to the
start 10, a new beat every 3 s 10, real animation not zoom (line 1 and the twist got real
motion, no zoom fallback) 15, natural voice (edge, 0.95 to 1.06) 10, captions in the safe
zone 5, length 20 to 45 s 5, vidIQ title score 70+ 5. A check the files cannot prove is FALSE.
85 or more posts. Under 85: fix exactly the checks in `fixes` in the job, bump rev, use the
day's one rebuild (job-format.md), run the gate again. Still under 85: not posted; `## QC`
says the score and the fixes; the Writer's next episode starts from them. Save
pipeline/<id>.scorecard {score, pass, fixes, at}. Never lower a check or skip the command to pass;
never call a Short "passed" without the score file.

## The eyes
ffprobe duration 20 to 45 s (aim 25 to 40), size under 4.9 MB. Extract 6 frames spread across
the video and Read them: captions readable and inside the safe zone, hook visible on the
first frame, characters consistent from scene to scene, no garbled faces, extra limbs, or
random text; the animated scenes (line 1 and the twist) show real motion between two frames
a second apart. If one scene is bad, reword that line's prompt and rebuild (only if today's
one rebuild is unused; the rebuild steps are in job-format.md). If it still fails, do not post;
log it and message Grayson in one line. Warnings in yt/out/<id>.json about TTS, whisper,
clips or the animation lane are logged.
