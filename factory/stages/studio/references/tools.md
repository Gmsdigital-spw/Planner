# Studio tools

## Make: stats (free)
Scenario 6676353 via mcp__Make__scenarios_run (responsive true). Results in
outputs.tool_output.body. data {action:"ytapi", method:"GET", url:"/v3/videos?part=
statistics,snippet&id=<id1>,<id2>"} -> items[].statistics (viewCount, likeCount,
commentCount). The last 7 posted episodes' ids go in ONE call. Retention and watch time are
not returned: write "unknown".

## Research (free)
The same ytapi lane (scenario 6676353), 0 vidIQ credits, about 100 YouTube quota units of a
free 10,000 a day; verified working Oct 24, 2026. One or two calls per run:
1. data {action:"ytapi", method:"GET", url:"/v3/search?part=snippet&type=video&videoDuration=
   short&order=viewCount&publishedAfter=<7 days ago, ISO>&q=<query>&maxResults=10&regionCode=
   US&relevanceLanguage=en"} -> items[].id.videoId, items[].snippet (title, channelTitle,
   publishedAt). Queries like "3D cartoon story short", "animated story shorts"; one query a
   run, a different one tomorrow if fewer than 5 usable results came back.
2. data {action:"ytapi", method:"GET", url:"/v3/videos?part=statistics,contentDetails&id=<ids,
   comma-joined>"} -> items[].statistics.viewCount, items[].contentDetails.duration (ISO, turn
   it into seconds).
Filter: keep English titles only (the API also returns Hindi/Urdu cartoon channels). Save to
modules/youtube/intel/research (db.md) and write `## Research` in the run notes. vidIQ's
research tools (vidiq_outliers, vidiq_trending_videos, vidiq_similar_channels; 5 credits
each) are allowed only when 5 or more credits would be left after the call; with 2 credits
(today) they are skipped until Nov 19, 2026. Copy structure, never content, characters or
titles.
Verified Oct 24, 2026 (Make executions d0e6d3839491482d8526052b81dc693f and 52cd09f2b470471aa1d9c358fcbff3e9, 0 credits):
the search returned 5 videos and the videos call returned their statistics and contentDetails. Two
filters are required: YouTube's videoDuration=short means under 4 minutes, so keep only items whose
contentDetails.duration is 60 seconds or less (parse PT<m>M<s>S); and keep English titles only (the
search returns Hindi and Urdu cartoon channels too). Record every kept item's seconds, views and
what its first 1.5 seconds do (from the title and thumbnail; never invent a watch of the video).


## Scorecard
`python3 studio/quality_gates.py short <id> --write` (from the repo root): reads yt/jobs/<id>
.json, yt/out/<id>.json and yt/jobs/<id>.research.json when it exists; prints PASS/FAIL,
score/100 and one evidence line per check; saves yt/out/<id>.score.json {score, pass, checks,
fixes}. Exit 0 = PASS (85+), 1 = FAIL, 2 = cannot judge. The ten checks (points): hook motion
in the first 1.5 s (15), hook text a question or a shock (10), story has a twist (15), ending
loops to the start (10), a new beat every 3 s (10), real animation not zoom (15), natural
voice (10), captions in the safe zone (5), length 20 to 45 s (5), vidIQ title 70+ (5). A
check the files cannot prove is FALSE. The GitHub build Action runs the same gate after every
build. `python3 studio/quality_gates.py --selftest` checks the tool itself (the bug rule).
Stage 03 runs it after the build, stage 04 acts on it (85 posts; under 85 = fix the named
checks with the day's one rebuild; still under 85 = not posted), stage 05 re-runs it once
after writing the title sidecar.

## Make: post
data {action:"youtube", fileData:<public mp4 url>, fileName:<title ending " #shorts">,
body:<description>, nameKey:<comma tags>, nameValue:"private", rank:<publishAt UTC ISO>} ->
YouTube publishes it publicly at that time; output id = videoId. Confirm with ytapi GET
/v3/videos?part=status&id=<videoId> that privacyStatus is "private" and publishAt is set; if
missing, ytapi PUT /v3/videos?part=status body {"id":<videoId>,"status":{"privacyStatus":
"private","publishAt":<window>,"selfDeclaredMadeForKids":false,"containsSyntheticMedia":true}}.
Posting windows: weekdays 7:00 PM Central, weekends 11:30 AM Central, unless Graph's Sunday
window comparison (intel/trends.windowNote) moved them with numbers; one midday test (12:30
PM Central) is allowed per week, logged as a test (launch.window "test-midday"). Skip windows
taken in pipeline launch.publishAt; if today's is past or taken, use tomorrow's. Never touch
the Etsy or Pinterest lanes of the scenario.

## GitHub build
Write only inside yt/ (jobs, the title sidecar yt/jobs/<id>.research.json, yt/out/<id>.score
.json), factory/skills/ (stage 06), factory/notebook/ (stage 06, the nb.py lines; V8 rule 7),
factory/runlog.jsonl and factory/stages/studio/output/. Pushing yt/jobs/<id>.json
starts the free "YouTube Starship build" Action, which writes yt/out/<id>.mp4 (under 4.6 MB)
and yt/out/<id>.json in about 15 to 25 minutes, then runs the scorecard and saves
yt/out/<id>.score.json. Files are public at
https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/<path>. If a push fails with
403: as shared/repo.md says, plus write the exact error into factory/main.lastError; stage
06 tells Grayson "GitHub access needs a look" in one line. Images come from Cloudflare Workers AI (GitHub secrets CF_ACCOUNT_ID /
CF_API_TOKEN); if yt/out/<id>.json says the keys are missing or rejected, do not post and
message Grayson one line: "Cloudflare key needs a refresh".

## vidIQ budget
The truth on Oct 24, 2026: the balance is 2 credits (renewable 0 of 150; the 150 renew Nov 19,
2026), so every 5-credit vidIQ call is skipped until then and the free paths above are the
paths. vidiq_balance (free) every run; stage 00 writes it to stats/channel.vidiqCredits and
notes the research path in the brief. When credits are back: vidiq_outliers (5 credits) on
Sundays only (contentType short, threeMonths, maxSubscribers 500000, keyword "AI 3D cartoon
story drama twist"), only if 5 or more would be left after the call; vidiq_score_title (type
short, 5 credits) in stage 05 only with 5 or more credits, 10 credits a day at most. Nothing
else. Never buy credits: they are Grayson's call. HERO-SHOT LANE stays OFF: never call
vidiq_generate_video; Grayson decides in chat.

## Drop zone
List yt/clips/. Any video file not in factory/main.usedClips is a clip Grayson made; grab a
frame with ffmpeg, Read it, and have Gags use it as the hook or twist scene (its raw URL as
that line's clip). Add it to usedClips when used.
