# 06 Lens: the five listing photos (room "studio")

Cover and pin rules have ONE home: `specs/cover-styles.md`. Its newest section (Oct 24, 2026,
Grayson's Atlas covers) wins: real pages on one of Grayson's own scenes (assets/atlas-pack,
place.py) with one cream label card; the real product is the hero (60%+ of the frame); no
badge stickers, pills, emoji or gradients; every cover different by code (the V8 check below)
and by the side-by-side against EVERY live cover. tools/fun_covers.py and tools/varied_covers
are retired for covers.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/preflight.md` | the lines for this stage (File / Copy / Images) | Faults that failed the last 5 builds: check and fix before handing over |
| Spec | `../../../specs/cover-styles.md` | Full file | The cover standard |
| Tool | `assets/atlas-pack/README.md` ("Etsy") + `place.py` docstring; `listing-photos/atlas/README.md` | scene names (planner, clipboard, christmas, frame) and the Oct 24 build pattern | Grayson's scenes and how the 17 live covers were built |
| Database | lessons (status active), sprint/main, pinstats (newest) | | Build more of what gets views, saves and clicks |
| Reference | `../references/house-style.md` | "Photos 2 to 5", "Text safe zone" | The other four photos |
| Tool | `studio/quality_gates.py` docstring ("Cover"); the last 20 covers: this run's other covers (under /tmp), `listing-photos/auto/*/1.jpg`, `listing-photos/atlas`, `listing-photos/fun` | | The V8 cover check and what it compares against |
| Skill | `../../../skills/lens/SKILL.md` | Full file | Checklist and lessons |
| Database | products (newest 5 published): coverLook, cover; every live cover (listing-photos/atlas/, listing-photos/auto/*/1.jpg, listing-photos/fun/, stats/) | | The side-by-side test; the scene of the last product built |
| Reference | `../references/wall-art.md` | "Lens" section | Only for a wallart product |

## Process
1. Set crew/lens working ("Photos: <title>"). Render the PDF pages with
   pages = gs.render_pages(pdf, "/home/claude/kit/pages/<product id>") (150 dpi); leave them
   there for the Pins worker.
2. Photo 1, the cover (cover-styles.md Oct 24). Pick the Atlas scene by product kind (planner =
   binder; clipboard = single-page trackers and game packs; christmas = Christmas only; frame =
   wall art), never the scene of the last product built; place the real rendered pages with
   `place.place(scene, pages, scale=2000/crop_w)`, add ONE cream label card (Lora title, the
   count big in the facts line) and change crop, label position and label colour from the last
   covers. Save product.coverLook = {tool:"atlas", scene, crop, labelPos, labelColour}. The
   fun_covers steps that follow are retired (Oct 24) and stay for history only: add ONE entry to
   tools/fun_covers_config.json: slug = the product id, listing_id "" (not published yet),
   root/out under listing-photos/fun/<product id>.jpg, theme = style.theme, kicker, title (one
   *word* in the accent font), badge [count, word], 3 pills from real facts, pages.src = a
   rendered page image from gs.render_pages (the most useful inside page, crop fractions),
   decor = 4 to 7 art pieces on theme (`img:<code>` from tools/img3d or tools/art.py) placed
   around the card, never over the title, badge or pills. Render with
   `python3 tools/fun_covers.py tools/fun_covers_config.json <slug>` (Playwright preinstalled,
   PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers). LOOK at it (playbook step 4). Save a 2000x1500
   JPEG under 400 KB (gs.save_jpeg). The entry is committed in stage 10 so the cover can be
   re-rendered; the JPEG is uploaded as an asset, not committed. Never a picture from the
   internet.
3. Photos 2 to 5 as house-style.md says: gs.preview_inside (up to 8 pages), gs.preview_closeup
   (the most useful page, readable), gs.preview_included (count + up to 8 items), and a second
   real-pages shot or gs.preview_how (3 steps). All 2000 px wide JPEG under 400 KB.
4. Thumbnail test: save gs.thumb_check(cover, path) (the centred square at 400 px) and also a
   300 px square, and Read them next to the question "would this win a tap next to the top
   sellers?": the product and its count must read clearly at 300 px, the title readable. Fix
   it if not. Then put this cover next to the 3 newest published covers in one image and Read
   it: it must not look like a recolour of any of them. THEN the full side-by-side: this cover
   next to EVERY live cover in the shop (contact sheet). If a stranger would say it came from
   the same template as any of ours, rebuild it (up to 2 rounds) or fail it.
5. Upload each photo as an asset; set product.cover (id) and product.previews (4 ids); confirm
   product.coverLook; stage "inspection". Set crew/lens idle. Write `## Photos: <title>` in the
   run notes (scene, crop, label position and colour, the smallest gate distance, thumbnail check result).

## Audit

| Check | Pass condition |
|-------|---------------|
| Standard | Real pages on an Atlas scene not used by the last product built; real product 60%+ of the frame; one cream label card with the count big; no badge stickers, pills, emoji, 3D art or gradients |
| Rotation | Passes the side-by-side against every live cover; not a recolour or re-layout of any |
| Thumbnail | Title and count readable at 300 px; product fills the frame |
| Rights | No internet images; art from tools/img3d or the kit only |
| Text zone | Photos 2 to 5: every word inside the safe zone; the cover is judged by the thumbnail test only |
| Format | 5 JPEGs, 2000 px wide, each under 400 KB |

## V8 cover check before handing over (Oct 24, 2026; specs/etsy-v8.md section 1)
Photo 1 follows cover-styles.md's Oct 24 section: real pages on one of Grayson's own scenes
(assets/atlas-pack, place.py) with one cream label card whose facts line carries the count big
and readable; no badge stickers, pills, emoji or gradients. Before setting stage "inspection",
run `python3 studio/quality_gates.py cover <cover.jpg> --recent /tmp/<the other covers built this run> listing-photos/auto/*/1.jpg listing-photos/atlas listing-photos/fun`
(pip install imagehash if needed; the gate keeps that order, newest first, and compares the first
20; the FAIL line is expected here: Lens reads only the distances, Inspect scores the five
checks): a distance under 18 to any of the last 20 covers means it is
a copy-paste in a stranger's eyes; change the scene, the crop, the label position and the
label colour and run it again. Write the smallest distance in the run notes under Photos.

## Pre-flight gate (Oct 23, 2026)
Before setting stage "inspection": run EVERY line of `../references/preflight.md` on the whole
product (file, copy, images, market, price) and fix what fails. Write
`Pre-flight: N of M lines pass; fixed: <short list>` under the Photos heading in the run notes.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Cover + 4 previews | assets; products/<id>.cover, .previews, .coverLook | JPEG ids, stage inspection |
