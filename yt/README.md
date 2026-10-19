# YouTube Starship

Free video factory for the YouTube Starship. Nothing here touches the Etsy files.

- `jobs/<id>.json` — a Short to make (script lines, clips, hook, labels). Pushing one starts the free **YouTube Starship build** Action.
- `out/<id>.mp4` + `out/<id>.json` — the finished Short (under 4.6 MB so Make can upload it) and its facts (duration, credits, word timings, warnings).
- `clips/` — drop zone. Any clip you upload here (for example a free Google Flow / Veo clip from your phone) can be used by a job as `https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/yt/clips/<file>.mp4`. The crew checks this folder first.
- `build/make_short.py` — the builder (Kokoro voice, whisper word timings, ffmpeg edit, word-by-word captions).
- `queue/` + `out/` from the old shrink step still work (`yt-shrink.yml`).

Optional free upgrade: add a Pexels API key (free at pexels.com/api) as the repo secret `PEXELS_API_KEY` and jobs can search footage themselves with zero vidIQ credits. Without it, the crew finds clips through vidIQ b-roll search (1 credit per search).
