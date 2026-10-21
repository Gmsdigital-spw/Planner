# Herald's channels and documents

## signal/main
{live, autoApprove, firstApprovedAt, postsPerDay (1), passScore (92), plan:[{d,t}],
channels:{instagram|facebook|youtube|tiktok:{connected, paused, verifiedAt, note,
connectionId}}, updatedAt}. Create it if missing with live:false, autoApprove:false,
firstApprovedAt:null and every channel connected:false.

## Verifying channels (every run, stage 00)
mcp__Make__connections_list {teamId:3216895}: instagram = connection 11830197 "Instagram GM"
(@gmsdigitalcreations, 17841469346530680); facebook = 11830277 "Facebook GM Page"
(Gmsdigitalcreations, 1358210974045889); youtube = 11830335 "YouTube SHOP"
(GMsDigitalCreations, UCBEMIih_sKOxjZvQ9oeqYWw); tiktok = 11830987 "Zernio TikTok GM" (Zernio
account 6ad7a7ecea18e081fb3894d2, @gmsdigitalcreatio). Connection 11806532 (@gmulaishere) is
the Studio floor's channel and must NEVER be used here. Write connected (true only if the
connection is listed), verifiedAt, connectionId and a short note per channel. Missing or
expired: connected false, note "Reconnect <name> in Make", and tell Grayson.

## Post URLs
Instagram: leave postUrl empty, link https://www.instagram.com/gmsdigitalcreations/.
Facebook reel: https://www.facebook.com/reel/<video_id>. YouTube Short:
https://youtube.com/shorts/<id>. TikTok: platformPostUrl when present, else
https://www.tiktok.com/@gmsdigitalcreatio.

## Repo paths
Public hosting at https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/<path>. Video
kit: /home/claude/planner/social/tools/ (README.md, promo_scenes.py, promo_video.py). Music:
python3 /home/claude/planner/yt/build/music.py --mood cozy|uplifting|emotional --seconds <len>
--seed <n> --out <work>/music.wav (an original royalty-free track; a different seed each day).
