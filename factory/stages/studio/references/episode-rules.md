# What a good episode is (Grayson's feedback, Oct 19, 2026)

A real STORY, not a summary. First person, or a narrator telling what a character did:
specific details (names, numbers, days, what someone said), a clear setup with stakes, two or
three escalations, a twist, and a final button line. 11 to 14 short lines, 38 to 52 seconds.
Each line is one picture: one clear scene the image AI can draw. Example that works (EP 11):
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

## Built to loop
- Cold open: line 1 is the end of the story stated as a confession or a question. The
  on-screen hook (hook field, uppercase, 4 to 7 words) says the same thing shorter.
- The last line ends mid-thought so it cuts straight back into line 1 ("...Which is why...").
  loop true, end_text "", pause 0.05 on the last line. Same image prompt for the first and
  last line.
- Pacing: "..." where a narrator would pause; a yellow label (label field) on every time jump.

## Voice
Engine "edge", voice "andrew" (male) or "ava" (female), speed 1.00 to 1.05 (0.98 when the
story is mostly heart). Write lines the way people talk.

## Two drafts (V6)
Gags writes TWO different scripts (different premise, different emotional engine: one
sharp-twist comedy, one heart). Judge scores both (hook, story, twist, logic, each 1 to 10,
every score at least 7, average at least the last posted episode's score); the higher average
is built, the loser is saved to episodes/<id>-b status "unbuilt". Neither clears 7 on every
score: rewrite the better one once; still short = build nothing today, say why. Save
qc.judge.drafts {a:{logline, scores}, b:{logline, scores}, chosen}. Each new episode uses the
latest lesson and fixes one specific weakness of the last episode (qc.judge.improvedOver).
Never repeat a premise in episodes/.

## Emotion on screen (V6)
Every emotional beat is its own line and its own close-up scene (the tear on the cheek, the
hug, the walk away), motion "orbit", pause 0.4. Crowd scenes name the background cast. Music
mood per story: emotional for heart, tense for drama/revenge, uplifting for underdog wins,
cozy only for gentle family stories; music_volume 0.13 to 0.16. An episode with no emotional
beat drawn on screen fails Judge's story score.

## Confidence
Every verdict leads with the decision, then the number, then the next action: "BUILD B 8.3 /
drop A 6.8: twist in A needs the setup line." No "maybe", "might", "I think".
