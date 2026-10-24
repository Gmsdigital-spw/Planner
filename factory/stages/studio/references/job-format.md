# The build job (yt/jobs/<id>.json; the builder is yt/build/make_short.py)

Fields: id, title (a question or a shock, under 60 chars, ends " #shorts"), hook (uppercase,
3 to 8 words with a question mark, a number or a shock word), end_text "", loop true, engine
"edge", voice "andrew"|"ava", speed 1.00 to 1.05 (default 1.03; 0.98 for heart; the gate
accepts 0.95 to 1.06), caption_words 3, music (emotional|tense|uplifting|cozy: the builder
makes an original track for that mood), music_volume 0.13 to 0.16, style (copy it exactly
from yt/jobs/ep12.json), cast, lines (7 to 12, each 9 words or fewer), rev (bump on a
rebuild). The builder's docstring lists the older Pexels-era keys too; the ones above are
what the cartoon episodes use.

- cast = {key: full visual description}, like ep12's: "Avo, a cartoon character whose whole
  head is a giant shiny green avocado (bumpy dark green avocado skin, big round cartoon eyes
  and a mouth on the avocado, no hair, no human face), human body wearing a grey hoodie".
- Each line: {"text", "image": {"prompt": "<who> doing <what>, <where>, <mood/lighting>" using
  {castkey} placeholders, "motion": push|pull|panl|panr|punch|orbit}, "label", "pause",
  optional "clip": {"url": "<the drop-zone clip's raw https URL>"} (a bare string is
  dropped by the builder), "anim": true on line 1 and the twist line, optional on the one
  emotional beat (the free animation lane; max 3, V8)}. "punch" on the twist (never the first
  or last line), push for tension, pan for wide scenes, orbit for emotional close-ups. Twist
  line pause 0.5, last line pause 0.05, emotional beats pause 0.4. The last line's image
  prompt is identical to line 1's (the loop check compares them word for word).
- Description: hook line + pinned question + "Visuals and voice made with AI." + 5 to 7
  hashtags incl. #shorts and #ai. 8 to 12 tags.

## Dry run, push, wait, rebuild, gate
BEFORE pushing: python3 yt/build/make_short.py yt/jobs/<id>.json --check (8-minute timeout).
Fix and dry-run again if it errors. Only push a job that passed. Then git fetch + git
ls-tree origin/main until yt/out/<id>.mp4 and yt/out/<id>.json exist (every 60 s, give up
after 45 minutes). Pull. If yt/out/<id>.json has "error": fix the job (simplify or reword the
failing prompt, keep 7 to 12 lines of 9 words or fewer), set a new "rev", delete
yt/out/<id>.mp4 and .json, commit together and push, wait again. Only ONE rebuild per day,
shared between a build error and a gate fail. After the build lands: `python3
studio/quality_gates.py short <id> --write` (the Action runs it too and saves
yt/out/<id>.score.json). Under 85, the gate-fix rebuild is the same loop: fix exactly the
checks in `fixes`, bump rev, delete the two output files, commit, push, wait, gate again.
Then update factory/main.

## The title sidecar (yt/jobs/<id>.research.json)
Written by stage 05 and read by the gate's title check: {title, title_score (number, or null
when not scored), scored_at, credits_before, credits_after, why ("credits N of 5" when vidIQ
was not called)}. The title check is 5 points, so an empty credit balance never blocks a 95.
