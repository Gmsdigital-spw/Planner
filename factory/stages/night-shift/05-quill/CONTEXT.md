# 05 Quill: listing copy (room "factory")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Previous stage | products in stage "copy" (this run's builds) | title, summary, file, brief | What to write for |
| Spec | `../../../specs/product-floor-v6.md` | SALES PUSH ("SEARCH-FIRST COPY", "PRICES"), the lane's spec (Quill lines) | Search-first titles, prices, lane categories |
| Skill | `../../../skills/quill/SKILL.md` | Full file | Checklist and lessons |
| Database | lessons (active), the brief's evidence | | What sells, what Grayson rejected |
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
