# The build job (yt/jobs/<id>.json; the builder is yt/build/make_short.py)

Fields: id, title (under 100 chars, ends " #shorts"), hook (uppercase, 4 to 7 words),
end_text "", loop true, engine "edge", voice "andrew"|"ava", speed 1.00 to 1.05 (default
1.03; 0.98 for heart), caption_words 3, music (emotional|tense|uplifting|cozy: the builder
makes an original track for that mood), music_volume 0.13 to 0.16, style (copy it exactly
from yt/jobs/ep12.json), cast, lines, rev (bump on a rebuild). The builder's docstring lists
the older Pexels-era keys too; the ones above are what the cartoon episodes use.

- cast = {key: full visual description}, like ep12's: "Avo, a cartoon character whose whole
  head is a giant shiny green avocado (bumpy dark green avocado skin, big round cartoon eyes
  and a mouth on the avocado, no hair, no human face), human body wearing a grey hoodie".
- Each line: {"text", "image": {"prompt": "<who> doing <what>, <where>, <mood/lighting>" using
  {castkey} placeholders, "motion": push|pull|panl|panr|punch|orbit}, "label", "pause",
  optional "clip": {"url": "<the drop-zone clip's raw https URL>"} (a bare string is
  dropped by the builder), optional "anim": true on the twist line and one more beat (the
  spec's free animation lane, max 2)}. "punch" on reveals and twists, push for
  tension, pan for wide scenes, orbit for emotional close-ups. Twist line pause 0.5, last line
  pause 0.05, emotional beats pause 0.4.
- Description: hook line + pinned question + "Visuals and voice made with AI." + 5 to 7
  hashtags incl. #shorts and #ai. 8 to 12 tags.

## Dry run, push, wait, rebuild
BEFORE pushing: python3 yt/build/make_short.py yt/jobs/<id>.json --check (8-minute timeout).
Fix and dry-run again if it errors. Only push a job that passed. Then git fetch + git
ls-tree origin/main until yt/out/<id>.mp4 and yt/out/<id>.json exist (every 60 s, give up
after 45 minutes). Pull. If yt/out/<id>.json has "error": fix the job (simplify or reword the
failing prompt, cut to 10 or 11 lines), set a new "rev", delete yt/out/<id>.mp4 and .json,
commit together and push, wait again. Only ONE rebuild per day. Then update factory/main.
