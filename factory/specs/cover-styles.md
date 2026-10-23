# Cover & Pin Styles (Grayson, Oct 21, 2026)

## GRAYSON LOVES THIS LOOK (Oct 21, 2026, 4 PM)
Grayson: the new bold, fun covers (bright theme color, real pages big on a white card, big count badge, benefit pills, 3D themed art) are "exactly how they're supposed to look." Keep this look as the standard for every new listing, pin and banner, and make each new one a little better than the last: sharper readability at thumbnail size, more varied layouts, better-matched art. Never drift back to beige/cream desk covers.

## UPDATE Oct 21, 2026 afternoon (wins over everything below)
Grayson: the covers were too bland, "like they're for old people or college professors". Make them fun, colorful,
something people want to buy. If the listing says cookie, put real cookies on it; if it says Santa, put Santa on it.
- Every cover: a bold theme color (red/green for Christmas, orange for Thanksgiving, navy + gold for New Year's,
  pink for coquette, bright green/teal/yellow for money and planners), the real product pages big on a white card,
  a big count badge, 3 short benefit pills, and 4-7 realistic 3D pieces of themed art from tools/img3d.
- Built with tools/fun_covers.py from tools/fun_covers_config.json. Beige/cream desk covers are retired.
- Never use pictures pulled off the internet: other people's photos are copyrighted and can get listings removed.
  The 3D art in tools/img3d is Apache-2.0 (Google Noto), safe for business use.
- Exactly ONE cover per listing. Replacing = upload new at rank 1 + delete the old one in the same run.
- Warden checks every cover daily with factory/qa/listing_audit.py (bold color, one cover, no duplicates).
- Pins (added Oct 21, 2026, evening, with Grayson's OK): built with tools/fun_pins.py, the 1000x1500
  portrait twin of fun_covers.py (same themes, art and config keys; the hook sits in the top third).
  cover_styles.py is no longer used for new pins; its cream and linen looks are retired with the covers.
- Wall art is the one exception: its covers and pins are real-frame photos per factory/stages/night-shift/references/wall-art.md
  (2000x1600 cover, 1000x1500 pins), never a fun_covers card. The listing audit knows a wall art listing by that cover size.


Grayson's standing instructions for listing photo 1 (the cover) and Pinterest pins. Same authority as the other files in factory/specs/.

## Why this exists
Too many covers look the same: one cream desk, one coffee cup, one tablet. Grayson likes the covers that show the whole product at a glance (like the "36 games" cover with a big count). He sent screenshots of top Etsy sellers to show the range he wants. Do not copy any seller's design, words or artwork. Use the patterns below with our own layouts, fonts and motifs.

## The rule
- Every cover uses one of the 6 styles below, picked to fit the product.
- No two listings published back to back may use the same style. Record the style on the product (`product.coverStyle`) and check the last 3 published products before choosing.
- The cream desk + coffee cup look (style 6) is at most 1 in 4 covers. Coffee cups are no longer a default prop.
- Colours follow the product's theme (Christmas red and green, blush pink, sage, neutral linen, bright multicolour for kids and calendars), not always cream.
- The cover must still read on a phone thumbnail: title readable at small size, product clearly visible, filling the frame edge to edge. No empty margins.

## The 6 styles
1. **Contents collage + count badge** (bundles, game packs, planners with many pages). Real page previews tiled edge to edge across the whole cover, slightly overlapping. A bold title banner across the top with one small format line under it (e.g. "Printable | US Letter + A4 | Instant Download"). A big round badge with the count ("36 GAMES", "85+ PAGES"). This is Grayson's favourite. Use it for every bundle.
2. **Headline + device dashboard** (web apps, spreadsheets, digital trackers). Large two-font headline at the top (one script word + one heavy serif word). A line of 3 short benefits separated by dots. The real app or sheet shown on a laptop, tablet and phone. A strip of 3 feature pills along the bottom (e.g. "Works offline · Instant download · One-time purchase").
3. **Clean tablet on linen** (digital planners for GoodNotes and Notability). A tablet and stylus on soft linen or stone, showing 2 real pages. Very little text, calm and premium.
4. **Hero page close-up** (single printables, trivia, one-page games, checklists). One real page shown big and readable, slightly tilted, on a themed background with a few motifs around it. The title is the page's own title.
5. **Bright month grid** (calendars, monthly planners, kids' products). Several months or pages in a bright grid with colourful headers, a bold title across the top, the year big.
6. **Warm desk flat-lay** (the old house style; wall art, mug wraps, stickers, invitations). Cream paper on wood with a pencil and a sprig. Wall art can use a real framed-print photo instead.

## Pins
Pins follow the same 6 styles in 2:3 format. Each product's 2 to 3 pins use at least 2 different styles. A pin's top third carries the hook text in big type.

## Scoring
A cover scores under 92 if it repeats the previous listing's style, if the product isn't clearly visible, or if the title can't be read at thumbnail size.

## Oct 23, 2026 — Grayson: the covers ALL look like one copy-pasted template (this section overrides everything above)
Third time this has happened (Oct 20 cream desk, Oct 21 cream desk again, Oct 23 fun_covers). Each "fix" swapped one look every listing shares for another look every listing shares. The fix is a variety GATE, not a new favourite style.
- The fun_covers card (title left, round count badge, 3 pills, tilted page on the right, emoji stickers, colour swapped) is retired as the default. At most 1 in 6 live listings may use it.
- Use the 6 layout families in "The 6 styles" above (collage, device dashboard, tablet, hero page, month grid, flat-lay/frame). A new cover must not share a layout family with ANY of the last 5 covers published, and no family may be on more than 1 in 4 live listings.
- The product is the hero: real pages fill at least 60% of the frame and are readable at 300 px. 3D emoji stickers on at most 1 in 4 covers, max 2 per cover.
- SIDE-BY-SIDE TEST (required, no exceptions): before a cover can pass, render it in a contact sheet next to every live cover in the shop and next to 3 top-seller covers for the same search. If a stranger would say it came from the same template as one of ours, it FAILS (cap the score at 80), whatever else it scores.
- Our own score is not proof. Report what the side-by-side showed in one line.
- Order of redo: listings with the fewest views first (0-3 views), max 6 per run, then the rest.
- Worked examples of 5 families (live Oct 23): tools/varied_covers/ (README there). Examples, not a template.
- Covers redone so far (Oct 23): 4601798994, 4599447958, 4597998190, 4597977363, 4600177516. The other 19 still carry the retired template: Warden redoes them, fewest views first.
- Pins (Oct 23 check of all 61 queued pins): most already vary (headline block + real pages, tablets, framed prints, different colours) and stay scheduled. The tools/fun_pins.py card (the pin twin of the retired cover card: big round count badge, emoji stickers, saturated theme colour) is retired as the default the same way: at most 1 in 6 new pins. No two pins posting on back-to-back slots may share a layout.
