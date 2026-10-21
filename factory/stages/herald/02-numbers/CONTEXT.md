# 02 Refresh real numbers

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/posting-lane.md` | "Real numbers", "TikTok check" | What to call (the GET shape is there) |
| Database | social (posted in the last 14 days) | postId, platform, metrics | Whose numbers |

## Process
1. YouTube: one yt_shop_api call for the SHOP Shorts posted in the last 14 days; write metrics
   as posting-lane.md says. TikTok: zernio_api GET /posts/<id> per posted doc; use only what
   comes back; a TikTok platform status "failed" marks the doc failed with the reason.
   Instagram and Facebook: metrics {availability:"unavailable", reason:"stats lane not built
   yet"} (never 0).
2. A one-line lesson at most once a week, only from real numbers (shape in posting-lane.md).

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Metrics | social/<id>.metrics | per channel |
