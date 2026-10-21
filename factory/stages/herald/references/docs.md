# social docs (Herald's documents; write only these plus the log lines)

## social/<id>
{id, idem, platform, format ("reel"|"carousel"|"photo"|"short"|"video"), productId,
listingId, link, productTitle, title (YouTube only), caption, hashtags[], media:{video
(public URL), images:[public URLs], cover}, planDate (day key), planDay (1-7), due (UTC
ISO), score, qc:{scores, notes, slopGate}, status ("awaiting_approval"|"approved"|"queued"|
"posted"|"failed"|"manual"|"rejected"|"qc_failed"), postId, postUrl, postedAt, error,
metrics:{availability, views, reach, likes, saves, shares, clicks, retrievedAt, source},
lesson, createdAt, updatedAt}.

## idem
idem = <platform>-<listingId>-<planDate>. Never create a second doc with the same idem (query
first). That is what stops duplicate posts across retries and restarts. Before posting, also
check the doc has no postId: a doc with a postId was already posted and must never be posted
again.

## Plan day and due times
Today's plan day = ((days since 2026-10-20) mod 7) + 1, theme from signal/main.plan.
due = Instagram and Facebook 11:00 AM Central (late-morning run), YouTube and TikTok 6:00 PM
Central (evening run). If that time is already past, use the next window.

## Per-channel post rules (Flame's rules: first line names the buyer's result in under 8
words, second line says exactly what is inside, one plain call to action, no "elevate" /
"unlock" / "game-changer", no emoji walls)
- Instagram: hook line first, 2 to 4 short lines of real benefits, "Link in bio to grab it",
  8 to 15 relevant hashtags.
- Facebook: friendlier and slightly longer, the clickable listing link in the text, 3 to 5
  hashtags.
- YouTube (shop channel): Short with title under 90 chars ending " #shorts", description with
  the listing link first, 5 to 8 tags.
- TikTok (Tick's lane): caption under 150 chars + 3 to 6 hashtags; "link in bio".
Name the product by its lane (planner, wall art set, mug wrap, sticker sheet, editable
invitation, party game pack). Facts only from the product's copy and its PDF pages: never
invent included pages, discounts, reviews, scarcity or income claims.

## Product pick (stage 03; marketing-wing-v6.md rules in short)
Candidates: products with etsy.state "active", a listing url (etsy.url or
https://www.etsy.com/listing/<listingId>) and a file.assetId (the real PDF). Order: sprint/main
flags "working" first, then "looks, no sale", then most views in 7 days (newest two stats
docs), then not featured in 7 days (check social). While Holiday Mode is ON (Christmas
window: 70 days before Dec 25 until Dec 15), 2 or 3 of the 4 channels feature a holiday
product (pick a second product for them if the first is not seasonal).
