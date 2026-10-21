# 04 Make the media

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Kit | `/home/claude/planner/social/tools/README.md` | Full file (read it every run) | The approved look |
| Reference | `../references/media-rules.md` | Full file | What is allowed and what is not |
| Reference | `../references/spot.md` | Full file, Sundays only (first full-day run) | The Sunday commercial |
| Spec | `../../../specs/studio-floor-v6.md` | "Spot" section, Sundays only | Spot rules |
| Shared | `../../../shared/database.md` | "Files (assets)" | Downloading the PDF |
| Previous stage | the pick note | product id, listing url, theme | What to film |

## Process
1. Download the product's PDF (file.assetId), render pages (pdftoppm -r 220), pick the 4 to 6
   pages that sell it best, build the video with the kit exactly as media-rules.md says, with
   music from the music tool. Sundays: spot.md instead, with the pages tail.
2. Make video.mp4 and video-small.mp4; save under social/<day key>/<listingId>/; commit, push,
   wait for every raw URL to answer 200.

## Audit

| Check | Pass condition |
|-------|---------------|
| Real pages | Every scene shows real rendered pages on the desk; no preview or listing images |
| Captions | <= 3 lines, <= 7 words per line, facts from the copy |
| Music | Present, original, loudnorm I=-16, fades |
| Sizes | 1080x1920, 12 to 20 s; video-small.mp4 under 4.5 MB |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Videos | social/<day key>/<listingId>/video.mp4, video-small.mp4 | pushed, 200 |
