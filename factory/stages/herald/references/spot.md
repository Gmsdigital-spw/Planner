# Spot: the Sunday commercial (Sundays only, in the first run of the day that does stage 03)

Follow the Spot section of specs/studio-floor-v6.md. Instead of the plain pages video, today's
video is a 15 to 20 second cartoon commercial for today's product: write
yt/jobs/spot-<day key>.json in the make_short format (read yt/build/make_short.py's docstring
and copy "style" from yt/jobs/ep12.json): id "spot-<day key>", 3 or 4 skit lines with
ORIGINAL cartoon characters (a tired party host, a mom with a budget binder, a teacher with a
stack of games; never a brand, character or celebrity) that set up the problem with a laugh,
engine "edge", voice ava or andrew, speed 1.03, caption_words 3, music "uplifting" or "cozy",
loop false, end_text "", the last line's text leading into the fix ("...so she printed
this."). Dry-run with python3 yt/build/make_short.py <job> --check, push only a job that
passed, then wait for yt/out/spot-<day key>.mp4 (git fetch + ls-tree every 60 s, give up
after 35 minutes). Append your own 5 to 7 second pages tail (the kit: the real pages on the
warm desk, caption "Instant download · link in bio") with ffmpeg at the same resolution and
audio format, music continued or crossfaded, loudnorm, then make video.mp4 and
video-small.mp4 as media-rules.md says and continue with stages 05 and 06 (same slop gate,
same 92). If the build fails, errors or times out, or yt/out/spot-<day key>.json reports the
Cloudflare key is missing or rejected, post the normal pages video instead and say so in the
log ("Spot skipped: <reason>"). Never write any other file under yt/.
