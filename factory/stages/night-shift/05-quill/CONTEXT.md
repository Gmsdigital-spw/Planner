# 05 Quill: listing copy (room "factory")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/preflight.md` | the lines for this stage (File / Copy / Images) | Faults that failed the last 5 builds: check and fix before handing over |
| Previous stage | products in stage "copy" (this run's builds) | title, summary, file, brief | What to write for |
| Spec | `../../../specs/product-floor-v6.md` | SALES PUSH ("SEARCH-FIRST COPY", "PRICES"), the lane's spec (Quill lines) | Search-first titles, prices, lane categories |
| Skill | `../../../skills/quill/SKILL.md` | Full file | Checklist and lessons |
| Database | lessons (active), the brief's evidence | | What sells, what Grayson rejected |
| Database | stats (newest 1), listing_fixes (all) | | Step 6: the 5 most-viewed live listings, the 14-day rule, the 5-ready cap |
| Reference | `../references/wall-art.md` | "Quill" section | Only for a wallart product |

## Process
1. Set crew/quill working ("Writing copy: <title>").
2. Set product.copy: title 140 characters max, the exact phrase a buyer types first (check Etsy
   autocomplete via WebSearch when possible), readable, no keyword soup; exactly 13 tags, each
   20 characters max, no duplicates, real search phrases (no one-page tags, no "digital
   download"); description 300 characters or more that sells the result in the first two
   lines, lists what is included, says it is a digital PDF download (nothing ships) and how to
   download, and ends with this exact line:
   This design was created with AI assistance under the creative direction of the seller.
3. Price as a number backed by the brief's research: single kits and planners $3.99 to $7.99,
   bundles $8 to $14, wall art sets $6.99 to $11.99, the lane spec's ranges for mug wraps,
   stickers and invitations. Bundle titles lead with the count and the main search phrase.
4. Category: an Etsy category path (party games are "Paper & Party Supplies > Party Supplies >
   Party Games"; wall art "Art & Collectibles > Prints > Digital Prints"; lane specs for the
   rest); materials "Digital download, PDF" (mug wraps add PNG).
5. Verify every limit with Python (counts, lengths, tag uniqueness, the exact AI line). Then
   stage "images". Set crew/quill idle. Write `## Copy: <title>` in the run notes: the
   title, price, tag count.
6. LISTING FIXES (V8, Oct 24, 2026; specs/etsy-v8.md section 5; the Builder's last product
   only, once per run): read the newest stats doc and take the 5 most-viewed live listings.
   For each whose title does not start with the phrase buyers type (Etsy autocomplete via
   WebSearch) or whose tags are not 13 real search phrases, and that has no listing_fixes doc
   from the last 14 days (a doc with status applied is never overwritten before its 14-day judgement), write listing_fixes/<listingId> {listingId, title_before,
   title_after, tags_before, tags_after, why (one line with the views number), status
   "ready", at}. Title and tags only; never price, photos, description or category. At most 5
   docs with status "ready" exist at once. Bolt applies 2 a day (its steps: bolt/references/listing-fixes.md, Bolt's file, not loaded here).
   Write `## Listing fixes` in the run notes: which listings, and the before/after titles.

## Audit

| Check | Pass condition |
|-------|---------------|
| Limits | Title <= 140, 13 unique tags <= 20 chars, description >= 300, verified by code |
| AI line | Present, exact, last |
| Search-first | Title starts with a real buyer phrase; every tag is a search phrase |
| Privacy | No real name, hometown or personal detail (rules.md) |
| Voice | No AI-sounding phrases, no emoji walls, no invented claims |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Listing copy | products/<id>.copy | title, tags[13], description, price, category, materials |
| Listing fixes | listing_fixes/<listingId> | title and tags before/after, status ready |
