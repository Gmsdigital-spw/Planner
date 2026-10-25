# YouTube Starship

Free video factory for the YouTube Starship. Nothing here touches the Etsy files.

- `jobs/<id>.json` — a Short to make (script lines, clips, hook, labels). Pushing one starts the free **YouTube Starship build** Action.
- `out/<id>.mp4` + `out/<id>.json` — the finished Short (under 4.6 MB so Make can upload it) and its facts (duration, credits, word timings, warnings).
- `clips/` — drop zone. Any clip you upload here (for example a free Google Flow / Veo clip from your phone) can be used by a job as `https://raw.githubusercontent.com/Gmsdigital-spw/Planner/main/yt/clips/<file>.mp4`. The crew checks this folder first.
- `build/make_short.py` — the builder (Kokoro voice, whisper word timings, ffmpeg edit, word-by-word captions).
- **Illustrated story format** (`"format": "story"` in a job): black 1080x1920 frame, one 16:9 FLUX illustration in the middle, gold label + white headline above, the narrator's full sentence below, slow zoom and crossfades. 6-10 scenes, 15 words max each, line 1 a hook question, told start to finish (no loop). Built by `build/make_story.py` (edge-tts andrew/ava only); it refuses scripts that break the story rules. Example: `jobs/story01.json`. Standing rules for every new Short: `STORY_FORMAT.md`.
- `queue/` + `out/` from the old shrink step still work (`yt-shrink.yml`).

Optional free upgrade: add a Pexels API key (free at pexels.com/api) as the repo secret `PEXELS_API_KEY` and jobs can search footage themselves with zero vidIQ credits. Without it, the crew finds clips through vidIQ b-roll search (1 credit per search).
