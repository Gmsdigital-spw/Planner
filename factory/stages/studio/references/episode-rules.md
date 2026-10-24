# What a good episode is (Grayson's feedback, Oct 19, 2026; numbers updated to V8, Oct 24, 2026)

A real STORY, not a summary. First person, or a narrator telling what a character did:
specific details (names, numbers, days, what someone said), a clear setup with stakes, a
problem, a twist, a payoff and a final button line that loops. 7 to 12 short lines of 9 words
or fewer each, 20 to 45 seconds (aim 25 to 40; V8). Each line is one picture: one clear scene
the image AI can draw. Example of the storytelling that works (EP 11; written under the older
38 to 52 s bar, so today it would be cut to 12 lines of 9 words or fewer):
"I owe a six-year-old forty dollars, and it's completely my fault. My little brother Max is
six, and he's been begging to play my game for a month. I kept telling him no. It's too hard.
There's a boss I've been stuck on for a week. Forty-seven tries... I counted. Saturday he
caught me rage quitting. And he goes, can I just try one time? So I handed him the
controller. Mostly to watch him lose. [30 SECONDS LATER] He... didn't lose. He didn't even
take damage. He put the controller down, looked at me, and said... that one's easy. Then he
went back to his juice box like nothing happened. [ONE WEEK LATER] Now every time I get
stuck, he charges me five dollars a boss. And this morning he raised his prices. Which is
why..." Not this: "my brother won a game, now he charges me $5" (too thin). No lists of fees,
no price-tag dumps, no AI-slop phrasing, nothing that needs on-screen gameplay to make sense.

## Look (cartoon, not realistic)
- Every line gets an AI-made 3D cartoon scene, Pixar/Illumination movie style. Characters can
  be anthropomorphic fruit or food, animals, objects, or ORIGINAL superheroes/villains. Never
  use or imitate existing characters, brands or celebrities and never copy another channel's
  exact characters or premise; invent your own cast or reuse your own recurring cast from
  intel/trends.cast.
- Stories can be about anything that hooks people: drama, betrayal, revenge, mystery, gaming,
  school, work, family, a heist, a superhero with a stupid power. Funny or dramatic with a
  twist, clean (no sexual content, no gore), understandable with the sound off thanks to
  captions. Emotional or satisfying stories (underdog, kindness payoff, karma, revenge served
  cold, hidden identity, family drama) pull the most views; comedy works when the twist is
  sharp. Reference: yt/jobs/ep13.json (janitor story).
- Pick heads with bold, smooth shapes (orange, apple, banana, strawberry, watermelon, avocado,
  lemon, tomato, pineapple, egg, donut); avoid kiwi, coconut. Every description specific and
  identical every time.
- Keep prompts family-friendly (the image AI wrongly refuses words like bed, bathrobe,
  undress, kiss). Never ask the image for text or signs.

## Hook in the first 1.5 seconds (V8)
- Line 1 moves: `anim: true` on line 1 (the free animation lane) or a real drop-zone clip. No
  slow intro: line 1 is 9 words or fewer.
- The on-screen hook (hook field) is 3 to 8 uppercase words with a question mark, a number or
  a shock word (NEVER, SECRET, CAUGHT, LIED, REVENGE, FIRED, STOLE, BANNED, EXPOSED, WORST,
  LAST, GONE, LOST, FAILED, BROKE, CHEATED, QUIT, REGRET, SORRY and the like). The scorecard
  checks this; a hook that would not stop a scroll in 1.5 seconds fails it.

## Length and beats (V8)
- 7 to 12 lines, each 9 words or fewer; 20 to 45 seconds total, aim 25 to 40. A new beat every
  2 to 3 seconds: no scene longer than 4.0 s on screen (5.5 s with real motion), mean under
  3.5 s. Split a long line into two scenes instead of trimming its meaning. The builder's
  word timings decide the real numbers, not a guess.
- Twist: setup, problem, twist, payoff. The twist line carries motion `punch` and is never the
  first or last line.

## Animation (V8)
- `anim: true` on line 1 and the twist line; an optional third on the one emotional beat when
  the quota allows; never more than 3, never a paid tier, never a second account. Every other
  scene keeps the living-picture motion and a dissolve. A twist with no real motion fails the
  gate.

## Research first, structure not content (V8)
- The Writer reads `## Research` before writing: copy the structure that is working this week
  (hook timing, length, story shape, series or one-off), never a real creator's content,
  characters, premise or title.
- Kill list: a story shape or hook style in intel/trends.kill (it lost twice in a row) is
  never reused without a written reason in `## Drafts`.

## Title (V8)
- Write 2 or 3 title candidates for stage 05 to score: each a question or a shock, under 60
  characters, ends " #shorts". vidIQ scores one only when 5 or more credits are left; with
  fewer, the first candidate is the title and the sidecar says why it was not scored.

## Built to loop
- Cold open: line 1 is the end of the story stated as a confession or a question. The
  on-screen hook (hook field, uppercase, 3 to 8 words with a question mark, a number or a
  shock word) says the same thing shorter.
- The last line ends mid-thought so it cuts straight back into line 1 ("...Which is why...").
  loop true, end_text "", pause 0.05 on the last line. Same image prompt for the first and
  last line.
- Pacing: "..." where a narrator would pause; a yellow label (label field) on every time jump.

## Voice
Engine "edge", voice "andrew" (male) or "ava" (female), speed 1.00 to 1.05, default 1.03
(0.98 when the story is mostly heart; the gate accepts 0.95 to 1.06). Captions 3 words at a
time; the builder keeps them in the safe zone and nothing else goes over the video. Write
lines the way people talk. Never a scene with no character when the line is about a person
(the spec's bar).

## Two drafts (V6), two gates (V8)
Gags writes TWO different scripts (different premise, different emotional engine: one
sharp-twist comedy, one heart). Judge scores both (hook, story, twist, logic, each 1 to 10,
every score at least 7, average at least the last posted episode's score); the higher average
is built, the loser is saved to episodes/<id>-b status "unbuilt". Neither clears 7 on every
score: rewrite the better one once; still short = build nothing today, say why. Save
qc.judge.drafts {a:{logline, scores}, b:{logline, scores}, chosen}. Each new episode uses the
latest lesson and fixes one specific weakness of the last episode (qc.judge.improvedOver).
Never repeat a premise in episodes/. Judge is the first gate; the scorecard after the build
(`python3 studio/quality_gates.py short <id> --write`, 85+ of 100) is the second. A Short
posts only with Judge 7+ AND 85+; the Writer's next episode starts from the fixes a failed
card named.

## Emotion on screen (V6)
Every emotional beat is its own line and its own close-up scene (the tear on the cheek, the
hug, the walk away), motion "orbit", pause 0.4; the one emotional beat may be the optional
third animated shot (V8). Crowd scenes name the background cast. Music
mood per story: emotional for heart, tense for drama/revenge, uplifting for underdog wins,
cozy only for gentle family stories; music_volume 0.13 to 0.16. An episode with no emotional
beat drawn on screen fails Judge's story score.

## Confidence
Every verdict leads with the decision, then the number, then the next action: "BUILD B 8.3 /
drop A 6.8: twist in A needs the setup line." No "maybe", "might", "I think".
