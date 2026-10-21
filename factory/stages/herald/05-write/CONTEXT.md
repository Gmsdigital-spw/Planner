# 05 Write one post per channel (native to each)

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/docs.md` | "Per-channel post rules", "Plan day and due times", "social/<id>", "idem" | The doc shape and rules |
| Database | products/<id> (copy.title, copy.description, copy.tags, kind) and the rendered pages from stage 04 | | Facts only |

## Process
1. Write the four posts to docs.md rules, facts only from the product's copy and PDF pages.
2. Prepare the four docs LOCALLY (a JSON file each, shape in docs.md) with media URLs,
   planDate, planDay, due (Instagram and Facebook 11:00 AM Central, YouTube and TikTok 6:00
   PM Central; next window if past). Do NOT write them to the database yet: stage 06 grades
   them and creates each social/<idem> with its final status, so a run that dies here leaves
   no half-made docs that would make the next run skip the day.

## Audit

| Check | Pass condition |
|-------|---------------|
| Hooks | First line names the buyer's result in under 8 words |
| Links | Instagram "link in bio"; Facebook and YouTube carry the listing link; all point to Etsy |
| Banned words | No elevate / unlock / game-changer; no emoji walls |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Four docs | local JSON files for stage 06 | docs.md shape, no status yet |
