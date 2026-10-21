# Herald promo video kit (Oct 20, 2026)

Reference build that Grayson approved after the first promo looked AI-made.
Real product pages printed on a warm wood desk, slow zooms, short captions in cream boxes, original music.

1. Download the product PDF (product.file.assetId) with Artifact read. Render pages:
   `pdftoppm -r 220 -png <pdf> $WORK/pdf/hi`
2. Copy promo_scenes.py, change SCENES to the best 4-6 pages for THIS product
   (hook page, the hero page close-up, 3 quick cuts, fanned stack with the cover on top). Run with WORK=...
3. Make music: `python3 yt/build/music.py --mood cozy --seconds 16 --seed <n> --out $WORK/music.wav`
4. Copy promo_video.py, change the caption() lines to this product's real facts (max 7 words a line). Run with WORK=... MUSIC=...
5. Output: $WORK/video.mp4 (IG/FB). For YouTube and TikTok also make a copy under 4.5 MB
   (`-b:v 2100k -maxrate 2400k`), because Make can't fetch files over ~5 MB.

## Listing photos (Oct 20, 2026)
`python3 social/tools/listing_photos.py spec.json` builds 2000x1600 Etsy photos from real PDF pages on the wood desk.
See listing_photos_example.json. Layouts: hero, inside, trio, duo, howto, howto2, cover, land, screen.
