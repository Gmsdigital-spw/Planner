# Shop studio: Etsy commercials (Grayson's standard from Oct 22, 2026)

Every promo video is a short commercial, not a slideshow: a voiceover, punchy captions that pop in
word by word, real product pages cut on the beat, and the REAL listing on a phone (scroll, back up,
tap "Add to cart", "Added to cart" toast), ending on the cover, the live price and "Tap the link".
Reference builds: `awards/` and `savings/` (posted Oct 22). Free tools only.

## Steps (about 15 minutes of work, 5 minutes of rendering)

1. **Pages**: download the product PDF (file.assetId), `pdftoppm -r 150 -png <pdf> social/studio/media/<name>/p`.
   Copy the product's live cover (`listing-photos/atlas/<listingId>.jpg`, else the product's cover asset; the old `listing-photos/styled/` look is retired) to `media/<name>/cover.jpg`.
2. **Live price and title**: read them from the newest `gw/out/price-*-read-*.json` (or an Etsy listing read).
   Never type a price from memory: a starter price may be live.
3. **Script**: 45 to 60 words, 15 to 20 s spoken. Hook in the first 2 s (the buyer's result or a number),
   2 to 4 short facts from the copy, then "Tap the link, and grab it on Etsy." Short sentences: every
   sentence end is a pause the captions snap to. Write it as `phrases` (see `example-spec.json`).
4. **Voice** (free): push `social/studio/tts/<name>.json` =
   `{"id":"<name>","lines":[{"voice":"<voice>","rate":"+6%","path":"social/studio/media/vo/<name>-vo.mp3","text":"<script>"}]}`.
   The "Shop studio voice" Action pushes the MP3 back in about a minute; poll with
   `git fetch origin main && git ls-tree -r --name-only origin/main | grep <name>-vo.mp3`, then pull.
5. **Music**: `python3 yt/build/music.py --mood uplifting --seconds 22 --seed <new each day> --out social/studio/media/vo/<name>-music.wav`
6. **Build**: `python3 social/studio/tools/make_ad.py <spec.json> social/studio/<name>` (times captions,
   scene cuts, phone taps and sound effects from the voice's pauses).
7. **Stills first**: `python3 social/studio/tools/render.py social/studio/<name> /tmp/x.mp4 --only 0.6,2,4,7,10,13,15,17`,
   make a contact sheet, LOOK. Fix cut-off text, a caption hiding the phone, empty frames.
8. **Render**: `python3 social/studio/tools/render.py social/studio/<name> <work>/master.mp4`, then
   `video.mp4` (IG/FB: `-b:v 4000k -maxrate 4500k`) and `video-small.mp4` (YT/TikTok, under 4.5 MB:
   `-b:v 1700k -maxrate 2000k`), both `-c:a aac -ar 48000 -movflags +faststart`. Cover = a frame from the end scene.
   Don't commit the master (too big).

## Keep it fresh (the look must not repeat)

Rotate, and never repeat yesterday's combination:
- **Voice** by weekday: Mon `en-US-AndrewMultilingualNeural`, Tue `en-US-BrianMultilingualNeural`,
  Wed `en-US-ChristopherNeural`, Thu `en-US-AndrewMultilingualNeural`, Fri `en-US-BrianMultilingualNeural`,
  Sat `en-US-GuyNeural`, Sun `en-US-ChristopherNeural`.
- **Opening**: hook (page flies in + badge) / grid (4 pages snap in) / fan (pages deal out). Different from yesterday.
- **Middle order**: the phone scene sits on the phrase right after the hook (blueprint 1.5 to 6 s); pan, fan and grid follow it in a different order each day; 4 to 6 scenes in total.
- **Palette**: from the product's own colours (bg = a bright and a deep shade of its main colour,
  accent = its strongest colour, hl = a warm gold or white that reads on it).
- **Hook style**: alternate a number ("36 awards"), a question ("Want to save $1,000?") and a moment
  ("Your office party needs this").

## Never
Old flat title-card listing images; stock people or AI hands; a fake price, review, sale or scarcity;
Etsy's logo (the words "on Etsy" are fine); captions over the phone screen; silent audio.
