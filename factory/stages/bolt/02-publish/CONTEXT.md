# 02 Publish (one product at a time; stop when a cap is reached)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/publish-steps.md` | Full file | The exact a to f steps |
| Reference | `../references/listing-fixes.md` | Full file, first run of the day | V8: title and tag fixes on live listings, before new publishes |
| Shared | `../../../shared/gateway.md` | "Etsy" (reads, uploads, fallback) | Op shapes |
| Shared | `../../../shared/database.md` | "Files (assets)" | Downloading covers, previews, the PDF |
| Previous stage | the candidate list; the active list on disk | | What to publish |

## Process
0. LISTING FIXES FIRST (V8, Oct 24, 2026; first run of the day only): apply up to 2 ready
   listing_fixes docs exactly as `../references/listing-fixes.md` says, before any new listing.
   This step runs even when there is no candidate to publish.
1. Skip the rest of this stage if there is no candidate, dryRun is true, or a cap from stage 00 is reached.
2. For each candidate, in order, follow publish-steps.md a to f exactly. Claim first (a), then
   files (b), then create the draft only if needed (c), photos and PDF (d), verify then
   publish (e); any failure goes to f. After each product, re-check publishedToday against
   dailyCap and feesThisMonth against monthlyFeeCap; stop when a cap is reached.
3. Two products failing in one run: stop this stage (stage 03 still runs).
4. Learning: as bolt/CONTEXT.md "Learning" says, for any failed step.

## Audit

| Check | Pass condition |
|-------|---------------|
| Complete listing | images count >= 1 + previews count AND at least one file, verified by GET before the PATCH to active |
| Caps | Listings published today <= dailyCap; fees this month <= monthlyFeeCap |
| Fixes | At most 2 listing fixes applied today, each verified by a GET after the PATCH; title and tags only |
| Resume, never duplicate | A product with etsy.listingId reuses it; no second draft created |
| Temp files gone | dl-temp/<random>/ for each product removed and pushed |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Published products | products/<id> | stage published, etsy {...} |
| Fees | spend/<month key>.entries | one entry per listing |
| Pin links | pins docs of that product | link = listing url |
| Batch status | batches/<id> | published when every product is live |
