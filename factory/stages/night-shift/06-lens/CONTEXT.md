# 06 Lens: the five listing photos (room "studio")

Cover and pin rules have ONE home: `specs/cover-styles.md`. Its newest section (Oct 21, 2026,
4 PM) wins: bold theme colour, the real pages big, a big count badge, 3 benefit pills, themed
3D art from tools/img3d, built with tools/fun_covers.py. Beige/cream desk covers are retired.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Spec | `../../../specs/cover-styles.md` | Full file | The cover standard |
| Playbook | `../../../playbooks/fun-listing-cover.md` | Full file | The proven way to build one |
| Reference | `../references/house-style.md` | "Photos 2 to 5", "Text safe zone" | The other four photos |
| Tool | `tools/fun_covers.py` docstring, `tools/fun_covers_config.json` | config shape | How to render |
| Skill | `../../../skills/lens/SKILL.md` | Full file | Checklist and lessons |
| Database | products (newest 3 published): coverStyle, style | | Rotate styles |
| Reference | `../references/wall-art.md` | "Lens" section | Only for a wallart product |

## Process
1. Set crew/lens working ("Photos: <title>"). Render the PDF pages with
   pages = gs.render_pages(pdf, folder) (150 dpi).
2. Photo 1, the cover: the style picked in stage 03 (never the same as the last 3 published).
   Add a config entry to tools/fun_covers_config.json using only facts from the title and
   description (count, what is included), theme colour matching the product, 4 to 7 pieces of
   themed 3D art, real pages big on the white card, the count badge, 3 benefit pills. Render
   with tools/fun_covers.py (Playwright, PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers). Save as
   2000x1500 JPEG (gs.save_jpeg, under 400 KB). Never a picture pulled off the internet.
3. Photos 2 to 5 as house-style.md says: gs.preview_inside (up to 8 pages), gs.preview_closeup
   (the most useful page, readable), gs.preview_included (count + up to 8 items), and a second
   real-pages shot or gs.preview_how (3 steps). All 2000 px wide JPEG under 400 KB.
4. Thumbnail test: save gs.thumb_check(cover, path) (the centred square at 400 px) and also a
   300 px square, and Read them next to the question "would this win a tap next to the top
   sellers?": the product and its count must read clearly at 300 px, the title readable. Fix
   it if not. Then put this cover next to the 3 newest published covers in one image and Read
   it: it must not look like a recolour of any of them.
5. Upload each photo as an asset; set product.cover (id) and product.previews (4 ids); save
   product.coverStyle and style; stage "inspection". Set crew/lens idle.

## Audit

| Check | Pass condition |
|-------|---------------|
| Standard | Bold theme colour, real pages big, count badge, 3 pills, themed art; no cream desk |
| Rotation | Style differs from the last 3 published covers |
| Thumbnail | Title and count readable at 300 px; product fills the frame |
| Rights | No internet images; art from tools/img3d or the kit only |
| Text zone | Every word inside the safe zone house-style.md names; kit check not switched off |
| Format | 5 JPEGs, 2000 px wide, each under 400 KB |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Cover + 4 previews | assets; products/<id>.cover, .previews, .coverStyle | JPEG ids, stage inspection |
