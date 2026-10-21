# 04 Forge: build the product file (room "factory")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Previous stage | `../output/<day key>-run.md` | "## Build list" | What to build |
| Reference | `../references/house-style.md` | "PDF pages" and "The kit" | How pages are built |
| Spec | `../../../specs/product-floor-v6.md` | the lane's build spec (mug wrap, sticker, invitation) | Only for those lanes |
| Reference | `../references/wall-art.md` | "Forge" section | Only for a wallart product |
| Skill | `../../../skills/forge/SKILL.md` | Full file | Checklist and lessons |
| Playbook | `../../../playbooks/<slug>.md` | Only if one matches this product type | Proven way |
| Spec | `../../../specs/product-floor-v6.md` | "THANK-YOU PAGE" | The last page of every PDF |

## Process
1. Set crew/forge working ("Building: <title>"). Fetch the kit as house-style.md says.
2. For each product in the build list: write the real content first (every page in full: real
   prompts, questions, rows, answer keys; no placeholders, no lorem ipsum).
3. Build the PDF with the kit: d = gs.Book(path, name, pal, cover_style=style.coverStyle,
   page_frame=style.pageFrame). US Letter with 0.7 inch margins so it also prints on A4, 6 to
   16 pages (the 3+ pages rule does not apply to mug wraps, stickers, invitations). Page 1:
   d.cover(2 or 3 short title lines, one-line subtitle, pages=count, kicker such as
   "PRINTABLE PLANNER"). Then a short how-to-use page, then the content pages with d.start,
   d.heading, d.text, d.bullets (check=True for checklists, numbered=True for steps, cols=2 for
   short items), d.table, d.lines, d.box and d.end() (adds the name and page number footer).
   Custom layouts draw on d.c with the palette colours and kit fonts; keep text inside the
   margins. Tables that are the page use fill=True so rows reach the bottom; a page is never
   half empty. End with the thank-you page from the spec, word for word (it is not counted in
   the 6 to 16 content pages or in the copy's page count; file.pages is the pypdf total). Wall
   art: append it to the link PDF with pypdf after wa.link_pdf, keeping the file under 550 KB.
4. Render every page at 50 dpi into one contact sheet and Read it yourself: fix any overlap,
   clipped text, crowded page or empty half page before moving on. Verify every answer key
   against its questions with Python.
5. Count the pages with pypdf, upload the PDF as an asset (database.md "Files"), update the
   product: file {assetId, url, pages, sizeBytes, builtAt}, stage "copy".
6. Set crew/forge idle. Write `## Build: <title>` in the run notes: pages, size, asset id.

## Audit

| Check | Pass condition |
|-------|---------------|
| Real content | No placeholder, generic or repeated filler on any page |
| Layout | Contact sheet shows no overlap, clipping, cramped or half-empty page |
| Answer keys | Every key verified against its questions by code |
| Thank-you page | Present as the last page, spec text verbatim |
| Margins | Text inside 0.7 inch margins; prints on Letter and A4 |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Product file | asset + products/<id>.file | PDF, stage copy |
