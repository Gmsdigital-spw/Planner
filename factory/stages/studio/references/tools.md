# Studio tools

## Make: stats (free)
Scenario 6676353 via mcp__Make__scenarios_run (responsive true). Results in
outputs.tool_output.body. data {action:"ytapi", method:"GET", url:"/v3/videos?part=
statistics,snippet&id=<id1>,<id2>"} -> items[].statistics (viewCount, likeCount,
commentCount).

## Make: post
data {action:"youtube", fileData:<public mp4 url>, fileName:<title ending " #shorts">,
body:<description>, nameKey:<comma tags>, nameValue:"private", rank:<publishAt UTC ISO>} ->
YouTube publishes it publicly at that time; output id = videoId. Confirm with ytapi GET
/v3/videos?part=status&id=<videoId> that privacyStatus is "private" and publishAt is set; if
missing, ytapi PUT /v3/videos?part=status body {"id":<videoId>,"status":{"privacyStatus":
"private","publishAt":<window>,"selfDeclaredMadeForKids":false,"containsSyntheticMedia":true}}.
Posting windows: weekdays 7:00 PM Central, weekends 11:30 AM Central; skip windows taken in
pipeline launch.publishAt; if today's is past or taken, use tomorrow's. Never touch the Etsy
or Pinterest lanes of the scenario.

## GitHub build
Only ever write inside yt/ (and factory/skills/ in stage 06). Pushing yt/jobs/<id>.json
starts the free "YouTube Starship build" Action, which writes yt/out/<id>.mp4 (under 4.6 MB)
and yt/out/<id>.json in about 15 to 25 minutes. Files are public at
https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/<path>. If a push fails with
403, write the exact error into factory/main.lastError and tell Grayson "GitHub access needs
a look" in one line. Images come from Cloudflare Workers AI (GitHub secrets CF_ACCOUNT_ID /
CF_API_TOKEN); if yt/out/<id>.json says the keys are missing or rejected, do not post and
message Grayson one line: "Cloudflare key needs a refresh".

## vidIQ budget
vidiq_balance (free) every run; report it in stats/channel.vidiqCredits. vidiq_outliers (5
credits) on Sundays only (contentType short, threeMonths, maxSubscribers 500000, keyword
"AI 3D cartoon story drama twist"). Nothing else. HERO-SHOT LANE stays OFF: never call
vidiq_generate_video; Grayson decides in chat.

## Drop zone
List yt/clips/. Any video file not in factory/main.usedClips is a clip Grayson made; grab a
frame with ffmpeg, Read it, and have Gags use it as the hook or twist scene (its raw URL as
that line's clip). Add it to usedClips when used.
