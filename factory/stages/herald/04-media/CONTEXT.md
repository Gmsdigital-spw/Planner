# 04 Make the media

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Studio | `/home/claude/planner/social/studio/README.md` | Full file (read it every run) | The commercial format (Grayson's standard from Oct 22) |
| Reference | `../references/media-rules.md` | Full file | What is allowed and what is not (incl. the V8 commercial blueprint) |
| Tool | `studio/quality_gates.py` | `python3 studio/quality_gates.py blueprint` | The 15 to 22 s commercial blueprint, printed |
| Reference | `../references/spot.md` | Full file, Sundays only (first full-day run) | The Sunday commercial |
| Spec | `../../../specs/studio-floor-v6.md` | "Spot" section, Sundays only | Spot rules |
| Shared | `../../../shared/database.md` | "Files (assets)" | Downloading the PDF |
| Shared | `../../../shared/repo.md` | "Committing" | The push of the videos |
| Previous stage | the pick note | product id, listing url, theme | What to film |

## Process
1. Download the product's PDF (file.assetId), render pages, read the live price and title, write
   the script and phrases, get the free voice, make music, run make_ad.py, check stills, render:
   exactly as the studio README and media-rules.md say. Sundays: spot.md for the skit, studio
   end scene for the tail.
2. Make video.mp4 and video-small.mp4; save under social/<day key>/<listingId>/; commit, push,
   wait for every raw URL to answer 200.

## Audit

| Check | Pass condition |
|-------|---------------|
| Commercial | Voiceover, real pages, phone listing with a tap, end card with the live price |
| Fresh | Voice and opening differ from yesterday's (see yesterday's log line) |
| Captions | 3 to 6 words at a time, never over the phone, facts from the copy |
| Audio | Voice clear over the music; mean about -15 dB, max under -1 dB |
| Sizes | 1080x1920, 15 to 22 s (a Sunday Spot: up to 27 s); video-small.mp4 under 4.5 MB |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Videos | social/<day key>/<listingId>/video.mp4, video-small.mp4 | pushed, 200 |
