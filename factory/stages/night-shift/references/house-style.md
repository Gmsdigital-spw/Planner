# House style: PDF pages, photos 2 to 5, the text safe zone

Covers and pins are NOT here: their one home is `specs/cover-styles.md` (newest section wins).
The cream-desk cover style that used to live in the Night Shift prompt ("GM Studio kit v4
cozy, real") was retired by Grayson on Oct 21, 2026 for covers and pins. The kit is still used
for the PDF pages and the inside photos below.

## The kit
- The kit folder is /home/claude/kit (shared by every worker tonight). If gm_style.py or
  mockup.py is missing there: Artifact read with url = the artifact url, out_dir =
  /home/claude/kit, path "917d03e4f21b576da506766f0aa992f8" then path
  "d2fe939ea8bd7975733326b0cc836a6c" (one path per call), and copy the saved .txt files to
  /home/claude/kit/gm_style.py and mockup.py (wall art: path "d0b1821fc580b42db28e2c22b005fb85"
  to wall_art.py). Then sys.path.insert(0, "/home/claude/kit"); import gm_style as gs; import
  mockup as mk. Their
  docstrings list every function. They use the installed Lora and Poppins fonts, fontTools and
  numpy.
- If the kit cannot be fetched or raises an error you cannot fix, follow these same rules by
  hand with reportlab and Pillow (fonts in /usr/share/fonts/truetype/google-fonts), say so in
  the log, and take 2 points off polish.

## PDF pages
- d = gs.Book(path, name, pal, cover_style=..., page_frame=...). Palettes: gs.pick_palette(title
  + " " + niche, avoid=[the palettes of the 3 newest products with a style field]); the gs.COLD
  palettes (midnight, dustyblue, charcoal, plum) are never used for new work. Rotate so no two
  products built back to back share a palette, a page_frame or a PDF cover style (band, frame,
  split).
- page_frame "rule" (thin double rule: planners and journals), "stripe" (diagonal candy stripe:
  holidays and parties), "band" (colour header band: trackers and worksheets) or "none".
- Game sheets and worksheets use d.start(title, subtitle, kicker="Game 3", centered=True).
  Tables that are the page use d.table(..., fill=True) so rows reach the bottom; a page must
  never be half empty. Cards and bingo grids draw on d.c sized to fill the page down to the
  footer (cell height from d.y - MARGIN - 20). Numbered answer lines, checkboxes and tinted
  cells make pages look like real games.
- Palette colours on d.c: d.P primary, d.D deep, d.T tint, d.A accent, d.INK, d.MUT, d.HAIR.
  Fonts: d.S serif bold, d.SB serif semibold, d.F sans, d.FM sans medium. Serif titles (Lora),
  Poppins for small text. At most 2 font families.
- Christmas and holiday products: stripe frames, the warm seasonal palettes (cranberry,
  evergreen, harvest, honey), the kit's own drawn motifs. Holiday figures only as the kit's
  simple original shapes or verified public-domain/CC0 art (record {label, url, licence} in
  product.notes).

## Photos 2 to 5 (all 2000x1600 JPEG under 400 KB via gs.save_jpeg; never PNG)
- Render pages = gs.render_pages(pdf, folder) at 150 dpi.
- (2) gs.preview_inside(pages, pal, up to 8 page indexes, one-line subtitle).
- (3) gs.preview_closeup(the most useful page, pal, title, subtitle, crop box): a real page
  large enough to read.
- (4) gs.preview_included(pages, pal, "13 Pages" style count, up to 8 short items, pages[0]).
- (5) a second shot of real pages in a different layout than photo 1, or gs.preview_how(pal, 3
  steps) if the product needs explaining. Wall art, mug wraps, stickers and invitations: see
  their lane sections (wall-art.md, product-floor-v6.md).
- Grayson's Atlas mockups (Oct 23, 2026): one of photos 2 to 5 MAY be a real-pages scene from
  /home/claude/planner/assets/atlas-pack (README.md there: which scene fits which product;
  place.py puts the real pages on): binder for planners, clipboard for calendars and
  checklists, holiday table for Christmas games, oak frame for wall art. Max one per listing,
  never the same scene on two products in a row, never blank. Covers: specs/cover-styles.md (Oct 24).
- Original design only: no logos, characters, stock photos, claims about sales or reviews,
  confetti, dot patterns, neon, sticker-yellow badges on inside photos, clip art, emoji.

## Text safe zone (photos 2 to 5 only)
- On the kit's inside photos every word sits between x 260 and x 1740 of the 2000-wide image
  (the Etsy app crops to the centred square). The kit raises an error if text falls outside:
  shorten or rewrap, never switch the check off. Props never carry text. The cover (photo 1)
  is NOT under this rule: tools/fun_covers.py runs its banner edge to edge by design; the
  cover passes on the thumbnail test (title and count readable at 300 px centred crop).
- Thumbnail test: gs.thumb_check(image, path) saves the centred square at 400 px; also check
  at 300 px (the Etsy search grid). Title and count must read.
