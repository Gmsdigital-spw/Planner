# Playbook: Fun listing cover (Oct 21, 2026)
_Proven by: Grayson approved this look on Oct 21, 2026 after rejecting the beige covers. Beat it with real tap-rate numbers._

## Steps
1. Add an entry to tools/fun_covers_config.json: slug, listing_id, theme, kicker, title (*one word* in the accent font),
   badge [count, word], 3 pills, pages {src: a real product image, crop: fractions}, decor (4-7 art pieces placed around
   the card corners, never covering the title, badge or pills).
2. Art = the thing the product is about: `img:<code>` from tools/img3d (1f36a cookie, 1f385 Santa, 1f381 gift, 1f384 tree,
   1f983 turkey, 1f967 pie, 1f4b0 money bag, 1fa99 coin, 1f3c6 trophy, 1f942 champagne, 1f380 bow...) or SVG from tools/art.py
   (gingerbread_man, gingerbread_house, candy_cane, stocking, sugar_star).
3. Render: `python3 tools/fun_covers.py tools/fun_covers_config.json <slug>` -> listing-photos/fun/<slug>.jpg (2000x1500).
4. LOOK at it: title fully visible, nothing hidden behind the badge (drop `sub` if the title is 4 lines), badge word fits,
   product pages readable, art on theme.
5. Push, upload at rank 1 with alt text (title + count + pills), DELETE the old cover, re-pull, run factory/qa/listing_audit.py.
