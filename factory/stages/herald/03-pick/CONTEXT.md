# 03 Pick today's product (only when no social docs exist for today)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Spec | `../../../specs/marketing-wing-v6.md` | product pick and Holiday Mode share | The rule |
| Reference | `../references/docs.md` | "Product pick", "Plan day and due times" | Candidates, order, plan day |
| Database | products (via out_dir + script: id, title, kind, etsy.state, etsy.url, etsy.listingId, file.assetId, copy.title), sprint/main, stats (newest 2), social (last 7 days: productId) | | Candidates and recency |

## Process
1. Products through out_dir; a script prints one line per candidate (etsy.state active, a
   listing url, a file.assetId). Order by the docs.md rule; skip anything featured in the last
   7 days; while Holiday Mode is ON, 2 or 3 of the 4 channels feature a holiday product (pick
   a second product if the first is not seasonal).
2. Compute today's plan day and theme (docs.md). Record product(s), listing url(s), plan day,
   theme for stages 04 and 05.

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Today's pick | local note | product id(s), listing url(s), plan day, theme |
