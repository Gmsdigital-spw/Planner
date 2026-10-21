# Media rules (stage 04; free tools only: the video kit, ffmpeg, Pillow, Playwright, the music tool)

- Build from the REAL PRODUCT PAGES: download the PDF (file.assetId), render pages with
  pdftoppm -r 220, and follow social/tools/README.md: pages printed on a warm wood desk with a
  mug, pen or autumn/holiday props, slow zooms, a close-up pan on the product's hero page,
  short crossfades. Pick the 4 to 6 pages that sell this product best. Mug wraps and sticker
  sheets (product.kind "mugwrap" / "sticker") are shown flat on the desk the same way; never
  draw a mug, a hand or a kitchen.
- NEVER use the product's preview images or the Etsy listing slideshow photos in videos: many
  are the old flat title-card style Grayson rejected. Never use flat solid-colour backgrounds,
  "What's Inside" / "How It Works" boxes, stock-template text slides, fake AI hands or people,
  dark navy designs, or emoji walls.
- Captions: cream rounded boxes like the kit, max 7 words per line, max 3 lines, facts from
  the real copy. First caption is the hook (matches the plan theme). Last scene: fanned page
  stack with the cover on top and "Instant download · link in bio".
- Video 1080x1920, 12 to 20 s (a Sunday Spot may run to 27 s with its pages tail), 30 fps,
  H.264 + AAC 48 kHz. Make two files: video.mp4 (IG/FB,
  under 5 Mbps) and video-small.mp4 under 4.5 MB (-b:v 2100k -maxrate 2400k) for YouTube and
  TikTok.
- MUSIC IS REQUIRED on every video: an original track from the music tool at the video's
  length, mood matched to the product (cozy default; uplifting for New Year, goals, savings
  wins; emotional for heartfelt family/holiday), loudnorm I=-16, fade in/out. Never
  copyrighted or downloaded music. A different seed each day.
- Save to /home/claude/planner/social/<day key>/<listingId>/. Push and wait for 200. New file
  names if a file of that name was already posted (never overwrite a posted video).
- No paid tools, no vidIQ generation.
