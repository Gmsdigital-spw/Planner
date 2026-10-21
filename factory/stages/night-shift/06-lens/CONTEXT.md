# 06 Lens: the five listing photos (room "studio")

Cover and pin rules have ONE home: `specs/cover-styles.md`. Its newest section (Oct 21, 2026,
4 PM) wins: bold theme colour, the real pages big, a big count badge, 3 benefit pills, themed
3D art from tools/img3d, built with tools/fun_covers.py. Beige/cream desk covers are retired.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Spec | `../../../specs/cover-styles.md` | Full file | The cover standard |
| Playbook | `../../../playbooks/fun-listing-cover.md` | Steps 1 to 4 ONLY (step 5 uploads to Etsy: that is Warden's job, never the Night Shift's) | The proven way to build one |
| Database | lessons (status active), sprint/main, pinstats (newest) | | Build more of what gets views, saves and clicks |
| Reference | `../references/house-style.md` | "Photos 2 to 5", "Text safe zone" | The other four photos |
| Tool | `tools/fun_covers.py` docstring, `tools/fun_covers_config.json` | config shape | How to render |
| Skill | `../../../skills/lens/SKILL.md` | Full file | Checklist and lessons |
| Database | products (newest 3 published): coverLook, cover | | Rotate theme and art |
| Reference | `../references/wall-art.md` | "Lens" section | Only for a wallart product |

## Process
1. Set crew/lens working ("Photos: <title>"). Render the PDF pages with
   pages = gs.render_pages(pdf, folder) (150 dpi).
2. Photo 1, the cover: the coverLook picked in stage 03. Add ONE entry to
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
   it: it must not look like a recolour of any of them.
5. Upload each photo as an asset; set product.cover (id) and product.previews (4 ids); confirm
   product.coverLook; stage "inspection". Set crew/lens idle. Write `## Photos: <title>` in the
   run notes (theme, art used, thumbnail check result).

## Audit

| Check | Pass condition |
|-------|---------------|
| Standard | Bold theme colour, real pages big, count badge, 3 pills, themed art; no cream desk |
| Rotation | Theme + art differ from the last 3 published covers; not a recolour of any |
| Thumbnail | Title and count readable at 300 px; product fills the frame |
| Rights | No internet images; art from tools/img3d or the kit only |
| Text zone | Every word inside the safe zone house-style.md names; kit check not switched off |
| Format | 5 JPEGs, 2000 px wide, each under 400 KB |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Cover + 4 previews | assets; products/<id>.cover, .previews, .coverStyle | JPEG ids, stage inspection |
