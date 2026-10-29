# Illustrated story Shorts: the standing format (Grayson, Oct 25, 2026)

Grayson approved this format on Oct 25, 2026 after watching the test episode `story01`
(The Crocodile Paradox). Every new Short uses it. Where this file and the older Studio files
disagree (episode-rules.md, job-format.md, qc.md, studio-floor-v6.md, the gags, judge and
cutter skills: loop, 3D cartoon style, word-pop captions, hook/label fields, anim lane), THIS
FILE WINS. Everything else in the Studio pipeline (stages, two drafts + Judge 7+, posting
windows, logging) stays as it is.

## The look (the builder does this; never change it per episode)
1080x1920 black frame, one 16:9 illustration in the middle, slow zoom, short crossfades.
Big bold white caps caption right above the picture, each word fading in as the narrator says
it (2-5 words at a time). Scene 1 carries the episode title hand-lettered on the picture.
Free tools only: Cloudflare FLUX.2 klein images (FLUX schnell fallback), edge-tts andrew or
ava, ffmpeg. Builder: `yt/build/make_story.py` (make_short.py hands `"format": "story"` jobs
to it). Example job: `yt/jobs/story01.json`.

## The story (Writer + Judge)
- Genres, rotate them: (1) a famous paradox or riddle explained simply (Crocodile Paradox,
  Ship of Theseus, Monty Hall, the Barber, the Unexpected Hanging, Buridan's donkey...);
  (2) a small-town mystery (fictional, clearly a story, no real people); (3) "the real reason
  why..." (true facts only: check them with WebSearch and keep the sources in the run notes).
  Nothing copyrighted, no real private people, no existing characters or brands. Never repeat
  a premise already in yt/jobs/.
- Told in order: setup, then problem, then twist, then payoff. NO loop.
- Line 1 is a clear hook question with real stakes, e.g. "What one sentence could save a boy
  from a hungry crocodile?" or "Why did this whole town stop talking about one store?"
- 8-12 scenes. Each scene = one idea in ONE sentence of 15 words or fewer, plain words a
  10-year-old understands. 3-7 seconds each, 61-75 s total (Grayson, Oct 28, 2026: TikTok's
  Creator Rewards only pay over 1 minute; the builder enforces it). Reach 61 s with more story
  (an extra complication or a bigger twist), never padding, slow narration, dead air or a held
  last frame. Aim for 11-12 scenes and 145-170 words; the dry run (--check) should show 64 s
  or more, since the real voice can run a few seconds shorter than the dry run.
- The ending answers the hook. No cliffhanger, no "part 2", no cut-off sentence, no question.
- Prefer a hero moment in the payoff (someone outsmarts the problem) over "and it was
  confusing". No filler lines that repeat the stakes: a cold reader swipes there.
- Judge scores hook, story, twist, logic (1-10) as before; under 7 = build nothing.

## Clarity check (before ANY build; the coordinator runs it)
1. Launch a separate fresh agent (Agent tool, general-purpose) that gets ONLY the numbered
   lines, no title, no notes, and is told: "You are a first-time viewer. Read this once.
   Reply with exactly two sentences retelling the plot, then 'Confusing:' and 'Boring:' lines
   naming any line, or none."
2. Compare the retelling to the intended plot (who, what happened, how it ended and why).
   If it does not match, the Writer rewrites and the check runs again. At most 2 rewrites.
3. Still failing after 2 rewrites: build nothing, and message Grayson ONE line:
   "Short skipped: script failed the clarity check (<why in a few words>)."
4. Write each retelling and the verdict under `## Clarity` in the run notes.
Fix "Confusing"/"Boring" notes when cheap, but the gate is the plot match.

## The job file (Cutter; replaces job-format.md's fields)
```
{"id": "<epN>", "format": "story", "rev": 1,
 "title": "<under 100 chars, ends \" #shorts\">",
 "title_card": "<2-5 word name hand-lettered on scene 1, e.g. The Crocodile Paradox>",
 "voice": "andrew"|"ava", "speed": 1.0,
 "art": "stickfigure"|"storybook",          # pick one per episode
 "music": "tense"|"emotional"|"uplifting"|"cozy"|"none", "music_volume": 0.05,
 "cast": {"<key>": "<one fixed visual description>", ...},
 "lines": [{"text": "<the sentence>", "label": "<2-3 words, notes only>",
            "headline": "<3-6 words, notes only>",
            "image": "<{key} doing exactly what the sentence says, where, mood>"}]}
```
- Every image prompt names its characters with {key} placeholders, so the EXACT same
  description goes into every prompt. Every scene's image shows exactly what that line says
  (who, doing what, where). Keep each character's description short, visual, and distinct.
- stickfigure = simple ink stick figures on a soft watercolor background (like story01);
  storybook = warm storybook cartoon. The builder adds the style text itself.
- Description: the hook question + "Visuals and voice made with AI." + 5-7 hashtags incl.
  #shorts. 8-12 tags.
- Dry run, push, wait and the one rebuild work exactly as job-format.md says
  (`python3 yt/build/make_short.py yt/jobs/<id>.json --check` first). The dry run rejects any
  script that breaks the rules above and prints why on its last line.

## QC (replaces qc.md's checks)
Duration 61.0-75.0 s (ffprobe on the final mp4; outside it = failed build, back to Writer/Cutter once), size under 4.9 MB, 1080x1920. Extract one frame per scene (the "scenes"
list in yt/out/<id>.json gives the lengths) and LOOK: each picture shows what its line says,
characters look the same throughout, no garbled faces, extra limbs or random text, the
caption is readable. A scene that misses: reword that prompt and use the one rebuild.
Warnings in yt/out/<id>.json (image model fallback, word timings, music) are logged.

## Alerts (Grayson: "never fail silently")
The moment a build, an image, the voice or a post fails, message Grayson ONE line right away
(SendUserMessage AND PushNotification, status "proactive"), e.g. "Short ep18: build failed:
image failed on scene 4 (Cloudflare daily limit)." Do not wait for stage 06. Then log it.
