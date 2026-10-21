# 01 Candidates and the duplicate guard

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/product-rules.md` | Full file | What counts as a candidate; what must never be touched |
| Previous stage | the active and draft lists on disk | listing ids, titles, states | Duplicate guard |
| Database | products (limit 200, via out_dir + script) | stage, score, copy, file, cover, previews, etsy, createdAt | Candidates |

## Process
1. Query products (limit 200) with out_dir; a Python script prints one line per product: id,
   stage, score.total, score.rulesPass, score.scoredAt, has file.assetId, has cover, previews
   count, copy.title, copy.price, tags count, etsy.state, etsy.listingId, etsy.claimedAt,
   createdAt. Read that table, not the docs.
2. A candidate has ALL of: stage "batched"; file.assetId; cover; at least 1 preview;
   copy.title, copy.description, copy.price > 0 and copy.tags; score.rulesPass true;
   score.total >= 92 (products whose score.scoredAt is before 2026-10-21 need only 90); and
   NOT etsy.state "active". Also a candidate (resume, do not recreate): any product with stage
   "publishing" whose etsy.claimedAt is older than 2 hours. Oldest createdAt first.
3. Problems to note for the summary: products in stage "batched" that fail only the score rule
   stay put (never publish them); count them.
4. DUPLICATE GUARD (before creating anything on Etsy). Normalize titles (lowercase, letters and
   digits only). For each candidate:
   - normalized copy.title (or its first 40 normalized characters) matches an ACTIVE listing:
     do not publish. Update the product {stage:"published", publishedAt:now, etsy:{listingId,
     state:"active", url, legacy:true, matchedBy:"Bolt duplicate guard"}} and log it.
   - matches a DRAFT whose listing_id equals the product's etsy.listingId: resume that draft
     (stage 02 skips creation).
   - matches some other draft (an orphan from an earlier failed send): never publish or reuse
     the orphan; continue normally and list the orphan's title and id for Grayson (he deletes
     drafts in the Etsy app).
5. Write the candidate list (ids, titles, resume-or-create) to a local note for stage 02.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Candidate list | local note | id, title, listingId or "create" |
| Duplicate matches | products/<id> | stage published, legacy true |
