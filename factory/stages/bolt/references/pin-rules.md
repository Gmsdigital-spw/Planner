# Pin scheduling rules (Grayson, Oct 21, 2026: 6 pins a day, varied looks)

## Which pins
Pins with status not "posted" and not "retired", no auto.zernioPostId and no auto.queuedAt,
with an image (image assetId OR auto.imageUrl) and a link containing listing/<digits> whose
listing is ACTIVE (from the active list plus anything published this run). At most 18 per
run. Order: pins that have a "style" field (the styled pins) first, then the rest by their
due date. Spread products: never two pins of the same product on the same date, and never
two pins of the same style back to back on a date.

## Quality gate (Grayson, Oct 27, 2026)
Schedule only pins with qc.slopGate "pass" (pins made before Oct 27 without qc are allowed only if
their style.layout is not "fun"). Never schedule two pins with the same style.layout in back-to-back
slots, never more than 1 "fun" pin a day, and never more than 2 pins of one layout family a day. A
pin that fails this stays "ready" with note "held: quality gate" for Pixel to re-image.

## Image hosting
If auto.imageUrl is missing: Artifact read the image asset, convert to JPG (long side at most
2000 px), push to listing-photos/auto/pins/<pin id>.jpg, wait for a 200, use that raw URL. If
auto.imageUrl is present, use it as is after checking it answers 200 (skip the pin if not).

## Due dates
If the pin's "day" field looks like "Wed Oct 28": that date (this year, or next year if it is
more than 60 days in the past). If missing or in the past: the earliest date from today on
that still has a free slot. Slots per date (6): 13:30Z, 15:30Z, 17:30Z, 19:30Z, 21:30Z,
23:30Z; skip slots already in the past. Check the other queued pins' auto.due so a date
never gets more than 6.

## Boards
Map the pin's board name with the table in shared/accounts.md "Pinterest", else by the
keywords there; default Christmas Planning and Organization.

## Never
Post through Make; touch pins with status retired; change a pin's image, title, description
or style; schedule a pin for a listing that is not active.
