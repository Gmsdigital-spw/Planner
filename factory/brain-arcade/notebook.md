# Brain Arcade notebook (notes on everything; read before every run)

## Grayson's rules
- 2026-10-25: "Build the lane so it can start selling and learning right away." Separate crew, separate shop, zero mixing with GM's Digital Creations.
- 2026-10-25: Starter listings come from his doc (link not pasted yet). Thanksgiving Math Escape Room first, the bundle last.

## What works (only with real buyer or market numbers)

## Testing (not proven yet)
- 2026-10-25: Low-ink version shipped with every game (answers teachers' ink complaint). Check after 14 days live: does "low-ink" in the description/tags move favorites vs a listing without it? (needs 2+ live listings)
- 2026-10-25: Cover layouts: clipboard photo scene (escape room) vs fanned real pages on colour (bingo). Compare views per 100 impressions after 14 days live.
- 2026-10-25: Escape room built as a letter-code game (choices carry letters that spell code words). Check after 14 days live: views, favorites, sales vs the next game type.

## What doesn't work (tried, failed, refused, or Grayson rejected)
- 2026-10-25: Opening Etsy or TpT item pages from the scheduled run: both domains fail (DNS/proxy), so the "2 opened rivals with 100+ item reviews" proof can't be met with WebFetch. Use the Etsy API through the lane's own Make scenario once the shop is connected (GET /v3/application/listings/active?keywords=..., then /listings/<id>/reviews for counts), or the free gateway after the merge. Until then market scores stay at 9-11 and nothing reaches 92.
- 2026-10-25: answer_check read 3 correct bingo key lines as missing because pdftotext drops spaces in tight columns ("3×2=6"). Fixed: compare without spaces (bug rule). Never loosen what is compared, only how text is read.

## Tomorrow (written by ba-night/ba-learn; the next run applies it first)
- 2026-10-25 night: if the shop is connected, Compass runs the Etsy API market search FIRST for "math escape room 3rd grade" and "multiplication bingo" and records rivals' item review counts; Ruler re-scores both games with that evidence. If not connected, Domino builds item 3 (Turkey Trot Fractions Board Game) instead of waiting.
- 2026-10-25 learn (8:41 PM): no numbers yet (0 live listings, shop link not tapped after 2 Publisher runs). No lesson can be proven without buyer numbers, so none written. Plan for tonight's Night Build stands: shop connected -> Etsy API market search first and re-score both games; not connected -> build item 3 (Turkey Trot Fractions Board Game) with photos 03-05 in varied layouts (Crayon's open fix).
