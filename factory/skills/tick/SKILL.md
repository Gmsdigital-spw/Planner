---
name: tick
floor: marketing
role: TikTok
judged_on: TikTok posts out with a Zernio post id (social docs status posted; run log note), then views from zernio_api GET /posts/<id> when Zernio returns them (social/<id>.metrics); profile taps are not read by any record yet
updated: 2026-10-23
---
# Tick — TikTok

## Job
Tick is the TikTok lane inside Herald's run: one post a day through zernio_api POST /posts (caption under 150 chars, 3 to 6 hashtags, "link in bio"), counted only when Zernio returns a post id with status published or publishing (posting-lane.md; docs.md). TikTok has been disconnected in Zernio since the night of Oct 22; until Grayson reconnects it (his tap, push-week-2026-10-23.md), the lane's whole output is one NEEDS YOU line per run while the other channels still post (marketing-wing-v6.md 8a). The run does not load this file. Judged every run on TikTok posts out with a Zernio post id (social docs, run log) and their views when zernio GET /posts/<id> returns analytics (social/<id>.metrics).

## Exact steps (keep current; rewrite when a better way is proven)
1. Grade yesterday's prediction from your last learned line (hit or miss, and why) before doing anything else.
2. Read this file; the rules the run applies live in stages/herald/references/posting-lane.md, channels.md and docs.md (the Herald load map does not load this skill, LESSONS.md or playbooks for it).
3. Do the work: verify the Zernio TikTok connection in stage 00; connected = post what is due with zernio_api POST /posts and record post._id; not connected = one NEEDS YOU line and nothing held. Write the caption to docs.md rules. Score it (06). Under 92 = one rewrite, then qc_failed; do not ship.
4. Log the result (score + the real number you're judged on: TikTok posts out with ids, views Zernio returned, or "disconnected" with the NEEDS YOU line).
5. End with one dated "What I've learned" line: the number, the one change for tomorrow, and "predict: <number>" for the next run. "Same as yesterday" = fail.

## Quality checklist
- Real numbers only. Nothing invented, nothing hidden.
- Looks like a top seller's work, not a template. Warm, real, clear.
- One thing measurably better than last run.
- TikTok's connection is read from mcp__Make__connections_list every run (connection 11830987 "Zernio TikTok GM"); not listed or a 403 = connected false, one NEEDS YOU line "Reconnect TikTok in Zernio", and IG, FB and YT still post (channels.md; marketing-wing-v6.md 8a; push-week-2026-10-23.md tap 2; Oct 22: 403 on the Zernio account id, posts red: skills/herald learned line 10-22 evening, Mechanic run log 10-22).
- A TikTok doc is "posted" only on tool_output.post.status "published" or "publishing" with post._id; never the tt_post action (draft only), never a TikTok job through the GitHub gateway (posting-lane.md).
- TikTok metrics come only from zernio_api GET /posts/<id>; nothing returned = "unavailable", never 0 (Oct 20 and 21 posts published with no analytics: skills/herald learned lines 10-21 and 10-22; 02-numbers CONTEXT; posting-lane.md "TikTok check").
- video-small.mp4 is under 4.5 MB, 1080x1920, 15 to 22 s (media-rules.md; 04-media CONTEXT Audit "Sizes").

## What I've learned (append-only, newest last)
- 2026-10-23 (agent update): TikTok posted 0 on Oct 22 and is disconnected in Zernio (403 on its account id); the Oct 20 and 21 TikTok posts published but Zernio returned no analytics, so TikTok has 0 readable views and 0 profile taps in any record (herald run log 10-22; skills/herald learned lines 10-21 and 10-22 evening; Mechanic run log 10-22 "posts red"). The lane waits on Grayson's tap 2 (push-week-2026-10-23.md "Grayson's taps"); the number will come from social docs with a Zernio post id and zernio GET /posts/<id> views once it is back. Tomorrow: one NEEDS YOU line per run naming the reconnect, nothing else held for it. Predict: 0 TikTok posts and 1 NEEDS YOU line in each Oct 23 Herald run log until the reconnect; the first run after it posts 1.
