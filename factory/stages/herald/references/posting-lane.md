# Posting lane (all four channels through Make scenario 6676353)

mcp__Make__scenarios_run {scenarioId:6676353, responsive:true, data:{...}}. The platform's
answer is in outputs.tool_output; an error object on the result means it failed. If the call
returns "Bad Gateway" or times out, do NOT retry blindly: mcp__Make__executions_list
(scenarioId 6676353) and read the newest with executions_get-detail; if it succeeded, use its
id. Use ONLY these actions:
- ig_reel: data {action:"ig_reel", videoUrl, caption} -> tool_output.id. Video: MP4 H.264, AAC
  48 kHz, -movflags +faststart, 9:16, 3 to 90 s, bitrate under 5 Mbps.
- ig_photo: data {action:"ig_photo", imageUrl (public JPG, 4:5 to 1.91:1), caption} -> tool_output.id.
- fb_reel: data {action:"fb_reel", videoUrl, caption, title} -> tool_output.video_id.
- fb_photo: data {action:"fb_photo", imageUrl, caption} -> tool_output.id.
- yt_short: data {action:"yt_short", videoUrl, title (ends " #shorts", under 100 chars),
  caption (= description), tags (comma list), privacy:"public"} -> tool_output.id = videoId.
  The video file MUST be under 4.5 MB (Make refuses bigger downloads).
- TikTok: data {action:"zernio_api", method:"POST", url:"/posts", body:<JSON string>} with the
  body in shared/gateway.md "Zernio" (TikTok). Success = tool_output.post.status "published"
  (or "publishing"); postId = tool_output.post._id, postUrl = platforms[0].platformPostUrl if
  present. NEVER use the tt_post action (draft only) and NEVER push TikTok jobs through the
  GitHub gateway (that push gets blocked in scheduled runs).
- yt_shop_api: data {action:"yt_shop_api", url:"/v3/videos?part=statistics&id=<id1>,<id2>"}
  -> read-only stats for the SHOP channel.

## TikTok check (next run)
data {action:"zernio_api", method:"GET", url:"/posts/<id>"}; if the TikTok platform status is
"failed", mark the doc "failed" with the reason.

## Posting what is due (stage 01)
Only if signal/main.live is true and firstApprovedAt is set. For each social doc with status
"approved" (or "queued") and due <= now, no postId, whose channel is connected and not
paused, and whose qc.slopGate is "pass": call the matching action (reel/short when
media.video exists, otherwise photo with media.images[0]). Before calling, set status
"queued" with if_version. Record postId and postUrl; status "posted" (postedAt now) only when
an id comes back. On error: check executions as above, retry once after 60 seconds; then
status "failed" with error (under 300 chars). One failed channel never stops the others. Max
one post per channel per day.

## Real numbers (stage 02)
YouTube: for SHOP Shorts posted in the last 14 days, one yt_shop_api call -> metrics
{availability:"available", views, likes, comments, retrievedAt, source:"YouTube API"}.
TikTok: zernio_api GET /posts/<id> returns analytics when available; use only what comes
back. Instagram and Facebook stats are not wired yet: metrics {availability:"unavailable",
reason:"stats lane not built yet"} (never 0). A one-line lesson at most once a week, only from real numbers. Herald's lesson shape (use
this one, not the generic one in database.md): {at, crew:"Herald", text, evidence (the
numbers), status:"active", area:"socials"}.
