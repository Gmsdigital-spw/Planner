# Inspection rubric (rubric 2, pass 92)

## Rules (rulesPass is true only if every line holds)
- Title 140 max; exactly 13 tags of 20 max, no duplicates; description 300+ with the exact AI
  line last; price > 0.
- File with 3+ pages (not for mugwrap, sticker, invitation: their lane spec's counts), plus
  the thank-you page last; the PDF opens; every answer key verified.
- Cover plus 4 previews, 2000 px wide JPEG. The COVER (photo 1) is judged
  by the thumbnail test only: title and count readable in the centred 300 px square; its
  banner may run edge to edge, that is the approved design. The text safe zone (x 260 to
  1740) applies to photos 2 to 5 (the kit's inside photos) only.
- Cover follows specs/cover-styles.md (newest section, Oct 24, wins): real pages on one of
  Grayson's Atlas scenes with one cream label card; real product 60%+ of the frame; passes the
  side-by-side test against EVERY live cover and the V8 cover gate (score.coverGate.pass true:
  unique by code and 92+ on the five checks); either fail = rulesPass false, whatever else the
  product scores. No badge stickers, pills, emoji, 3D art or gradients; pins (if already
  made) in 2+ styles.
- Pages full and framed; no cramped or half-empty page.
- No real name or hometown; no brand or character names; nothing copied from another shop; no
  internet images.

## Slop check (an honest look for anything that looks AI-made or cheap next to top sellers)
Before scoring, put gs.thumb_check of this cover next to the 3 newest published covers in one
image and Read it. Fail if ANY of these is true:
(a) the product's real pages are not the biggest thing in the picture, or fill less than about
    40% of the Etsy square;
(b) the title shows twice as big text (badge or card plus the PDF cover);
(c) any background or prop looks fake (rippled, stretched, blurry), or art covers words on a
    page, or more than 7 art pieces;
(d) any garbled, misspelled, cut-off or nonsense text anywhere on a page or photo;
(e) badges or claims like bestseller, top rated, reviews, #1, sale stickers, emoji (a count
    big on the label card is fine; a round badge sticker is not, cover-styles.md Oct 24);
(f) the copy uses AI-sounding phrases (elevate, unlock, seamless, game-changer, dive into,
    whether you're, look no further, in today's busy world), em-dash runs, or keyword soup;
(g) the cover looks like a recolour of one of the last 3 covers (same layout + same theme +
    same hero page type);
(h) any page has placeholder, generic or repeated filler content instead of specific real
    prompts, rows and answers;
(i) new lanes: any fake 3D mug, hand, kitchen or room; emoji-style icons; filler sayings;
    a sticker sheet padded with identical stickers; wall art: a misquoted or non-KJV verse, a
    drawn room or hand, a print not sitting exactly in a real frame opening.
Record score.slopCheck {pass, fails:[short strings]}. A fail caps images at 12 and polish at 6.

## Scores
- file /25: content complete and real, layout clean, prints right, answer keys correct (wall
  art and new lanes: their lane's file rules).
- copy /20: search-first title, real tags, specific description (page list, count, holiday,
  buyer), price backed by research.
- images /20: how professional next to top sellers. Thumbnail-readable at 300 px, product
  filling the frame, style rotation, real pages. A cover whose title or count is not readable
  at 300 px: at most 14. Overlap, clipped text, cramped spacing or a cheap cover: at most 14.
- market /15: evidence of a real gap vs the top 3 competitors (links in the brief).
- price /10: within the lane's range and justified.
- polish /10: no cramped page, no half-empty page, consistent fonts and colours. Cheap-looking
  cover or any layout fault: at most 7.
- total /100, rubric 2, verdict (one sentence, leads with PASS or FAIL and the number).

## V8 cover checks (Oct 24, 2026; studio/quality_gates.py COVER_RUBRIC, pass 92)
real_product_pages_fill_frame 20 (real pages 60%+ of the frame), big_count_badge 10 (the count
big and readable on the label card; never a sticker, pill or emoji: cover-styles.md Oct 24),
realistic_mockup 20 (Grayson's Atlas scenes with the real pages placed on them; never drawn or
fake), unique_vs_last_20_covers 20 (perceptual-hash distance 18 or more to every one of the
last 20 covers, decided by the code, never by eye), readable_at_thumbnail_size 15 (title and
count at 300 px), matches_season_and_buyer 15. Record the result in score.coverGate. A cover
under 92 here, or not unique, caps images at 12, fails rulesPass ("Rules" above) and goes back
to Lens in a fix round.

## Where 85 to 91 usually lose points (check first)
Images (hero pages too small in the square, same layout as last time), copy (generic lines
instead of the specific page list, count, holiday and buyer), market (weak evidence vs the top
3), polish (any cramped or half-empty page).
