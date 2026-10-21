# QC of the built file (stage 04)

ffprobe duration 25 to 58 s, size under 4.9 MB. Extract 6 frames spread across the video and
Read them: captions readable, hook visible on the first frame, characters consistent from
scene to scene, no garbled faces, extra limbs, or random text. If one scene is bad, reword
that line's prompt and rebuild (only if today's one rebuild is unused; the rebuild steps are
in job-format.md). If it still fails, do not post; log it and message Grayson in one line.
Warnings in yt/out/<id>.json about TTS, whisper or clips are logged.
