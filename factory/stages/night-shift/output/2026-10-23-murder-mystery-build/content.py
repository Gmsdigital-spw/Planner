TITLE = "The Stolen Star of Hollyridge Lodge"

STORY = ("Christmas Eve, Hollyridge Lodge, high in the snowy hills. A storm has shut the road, so eight people "
         "are stuck together for dinner. At 7:00 the owner, Ivy Hollister, raised a toast to the Hollyridge Star: "
         "a hand-made gold and crystal tree topper that has crowned the lodge tree since 1952. At 7:08 every light "
         "in the lodge went out. At 7:20 they came back on, and the top of the tree was bare. Nobody has left. "
         "The Star is still somewhere in this lodge, and one of you took it.")

CHARS = [
 dict(key="Ivy", name="Ivy Hollister", role="Owner of Hollyridge Lodge", costume="Velvet dress or blazer, pearls, velvet heels, a big ring of keys.",
      who="You inherited the lodge from your grandfather and you love every creaky board of it. Guests call you warm; staff call you strict. The Star is the lodge's pride and you built tonight's whole dinner around showing it off.",
      secret="The lodge is behind on its bills. Last month you raised the Star's insurance to $60,000. It looks bad, and you know it.",
      alibi="At 7:05 you went to the office to take a call from the bank on the landline. You stayed on the phone in the dark until about 7:25.",
      r1="Welcome everyone. Tell the room the Star's story: made by hand in 1952, bought by your grandfather from a glassmaker in the valley. Say you want it back tonight, no questions asked.",
      r2="When asked, give your alibi: the bank call in the office. Admit the lodge has money trouble, but say you would never sell the Star.",
      r3="If the insurance comes up, admit it, then point out that a claim takes months and would not save the lodge by spring. You care more about the Star than the money.",
      ask=["Jasper, how much do you still owe me?", "Rupert, what did you offer me for the Star yesterday?", "Clem, where did you learn to bake like your grandmother?"]),
 dict(key="Jasper", name="Jasper Pike", role="Ski Instructor", costume="Ski sweater, wool hat, goggles on the head, chunky ski boots.",
      who="You teach the guests to ski and you are the loudest laugh in any room. You are charming, a little reckless and always short of cash. You were standing right by the tree at the 7:00 toast.",
      secret="You owe Ivy $2,000 from a loan last winter. You and Dash were secretly fixing your snowmobile so you could slip into town tomorrow and buy Ivy a thank-you gift.",
      alibi="From 7:06 to 7:30 you were in the garage with Dash working on the snowmobile by headlamp. The garage camera runs on a battery.",
      r1="Introduce yourself with a joke. Say you saw the Star sparkle at 7:00 and nothing after that because the lights went out.",
      r2="Give your alibi: the garage with Dash. Do not say why you were fixing the snowmobile yet.",
      r3="Confess the loan and the gift plan. Say the garage camera will clear you and Dash both.",
      ask=["Marigold, why do you have a drawing of the Star in your notebook?", "Felix, what is in the box in your bag?", "Clem, did you hear anything from the kitchen?"]),
 dict(key="Clem", name="Clem Baxter", role="Head Cook", costume="Apron, rolled sleeves, a dusting of flour, a wooden spoon, kitchen clogs.",
      who="You run the lodge kitchen and your cinnamon buns are famous. You are cheerful, busy and good at keeping people fed and talking. YOU ARE THE THIEF. Your late grandmother made the Star by hand in 1952 and sold it to the lodge for almost nothing to pay a doctor's bill. You promised her you would bring it home.",
      secret="At 7:08 you flipped the main switch on the panel in the back hall, slipped into the dark drawing room, stood on the piano bench, untwisted the wire and lifted the Star. You bumped the mantel clock on the way out. The Star is hidden in the flour bin. You flipped the power back on at 7:20.",
      alibi="Your story (a lie): you were in the kitchen pulling the cinnamon buns out of the oven at 7:15. Stick to it. Never admit the oven is electric unless someone proves it.",
      r1="Be friendly and helpful. Offer everyone a bun. Say the Star was the prettiest thing in the lodge and you hope it turns up.",
      r2="Give your oven alibi: buns out at 7:15. Point gently at Rupert: he wanted the Star badly. Do not mention your grandmother.",
      r3="If someone proves the power was off, say the buns were just resting in a warm oven. Keep pointing at Rupert and the insurance. You may lie; you may not destroy a clue card.",
      ask=["Rupert, you offered a fortune for the Star. Did Ivy say no?", "Ivy, how much is the Star insured for?", "Jasper, you were closest to the tree at 7:00, weren't you?"]),
 dict(key="Rupert", name="Rupert Vane", role="Antique Dealer and Guest", costume="Tweed jacket, bow tie, reading glasses, leather loafers, one arm in a sling.",
      who="You buy and sell rare antiques and you can price a teacup from across a room. You came to the lodge to ski and slipped on the slope on Tuesday. Your right hand is in a splint and you cannot grip a thing with it.",
      secret="Yesterday you offered Ivy $40,000 for the Star and she said no. You were angry about it at breakfast and half the lodge heard.",
      alibi="When the lights went out you felt your way to an armchair in the hall and waited. Nobody saw you, and you cannot prove it.",
      r1="Introduce yourself. Say the Star is the finest piece of 1950s glass you have ever seen and that you are a collector, not a thief.",
      r2="Admit you were alone in the dark hall. Admit the $40,000 offer only if someone asks about it.",
      r3="Hold up your splint. Ask how a man with one working hand could untwist wire on top of a tree in the dark.",
      ask=["Clem, the kitchen is next to the back hall. Did you hear the panel click?", "Ivy, why raise the insurance last month?", "Noelle, what were you recording?"]),
 dict(key="Noelle", name="Noelle Winters", role="Lodge Singer", costume="Sparkly sweater or dress, a scarf, snow boots, a songbook.",
      who="You sing by the fire every night of the season. You are dreamy, kind and always humming. You and Felix slipped into the library before dinner to work on a new Christmas song.",
      secret="This is your last season at the lodge. A record label in the city offered you a contract and you have not told Ivy yet.",
      alibi="From 7:09 to 7:19 you and Felix recorded a voice memo of your song in the library, by candlelight. Both your voices are on it, with the time stamp.",
      r1="Introduce yourself and hum a few notes. Say you love this lodge and the Star means Christmas to you.",
      r2="Give your alibi: the library with Felix, recording. Say you will play the memo if anyone doubts you.",
      r3="Tell Ivy about the record contract. Say leaving is hard, and you would never steal from her on the way out.",
      ask=["Marigold, which room were you in during the blackout?", "Dash, who flipped the lights back on?", "Clem, did the buns burn when the power went off?"]),
 dict(key="Dash", name="Dash Moreno", role="Lodge Handyman", costume="Flannel shirt, tool belt, work gloves, heavy work boots.",
      who="You fix everything at Hollyridge: pipes, lifts, lights, snowmobiles. You are quiet, steady and you notice details. You know the lodge has no gas: every light and every oven runs on electricity.",
      secret="You sneak a slice of pie from the kitchen every night and Clem has never noticed. Tonight you also helped Jasper with his snowmobile without asking Ivy.",
      alibi="From 7:06 to 7:30 you were in the garage with Jasper. The battery camera on the garage wall shows you both.",
      r1="Introduce yourself. Say the blackout was strange: no storm damage, and the lights came back all at once at 7:20.",
      r2="Give your alibi: the garage with Jasper. Say you will check the smart panel log if the host lets you.",
      r3="Point out that the panel log says the main switch was flipped BY HAND. Ask who was close to the back hall panel.",
      ask=["Clem, how do you bake buns with no electricity?", "Rupert, can you even hold a screwdriver with that hand?", "Ivy, who else knew where the panel was?"]),
 dict(key="Marigold", name="Marigold Finch", role="Travel Writer", costume="Smart coat, beret, notebook and pen, heeled boots.",
      who="You write for a big travel magazine and every hotel is nervous around you. You are sharp, curious and you take notes on everyone. You booked Room 4, upstairs.",
      secret="Your notebook has a careful drawing of the Star. You planned a magazine story called 'The Star of the Hills' and wanted it to be a surprise for Ivy.",
      alibi="At 7:02 you went up to Room 4 to change shoes. The door lock runs on a battery and logs every key card. You stayed in your room until 7:31.",
      r1="Introduce yourself. Say you are here to write about the lodge and you take notes on everyone, so behave.",
      r2="Give your alibi: Room 4, from 7:02. If someone finds the drawing, say it is for an article.",
      r3="Explain the magazine story and show the drawing. Ask the host to check the Room 4 lock log.",
      ask=["Jasper, why are you so short of money?", "Clem, what did you bake tonight and when?", "Felix, what were you hiding in that box?"]),
 dict(key="Felix", name="Felix Hart", role="Ivy's Nephew", costume="Bright holiday sweater, sneakers, a guitar or a gift box.",
      who="You are Ivy's favorite nephew and the lodge's best (and only) guitar player. You are funny, nervous and you hate secrets, which is a problem tonight.",
      secret="In your bag is a box with a copy of the Star you had made in town as a surprise for Ivy, so the real one could be kept safe. It looks very suspicious tonight.",
      alibi="From 7:09 to 7:19 you were in the library with Noelle, playing guitar on her voice memo. Both your voices are on it, with the time stamp.",
      r1="Introduce yourself. Say you grew up with the Star on this tree and you cannot imagine Christmas without it.",
      r2="Give your alibi: the library with Noelle. Get jumpy if anyone mentions your bag.",
      r3="Open the box and show the copy. Tell Ivy it was meant to be her present. The real Star is still missing.",
      ask=["Rupert, where exactly were you sitting in the dark?", "Clem, can I see the oven?", "Dash, who knew how to switch the power off?"]),
]

# Clue cards: (id, round, title, text). Logic in logic_check.py uses these exact facts.
CLUES = [
 ("C1", 1, "The Stopped Clock", "The mantel clock in the drawing room was knocked to the floor and stopped at 7:14. The piano bench was dragged under the tree. Whoever took the Star was in the drawing room at 7:14."),
 ("C3", 1, "The Panel Log", "The smart panel in the back hall says the main switch was flipped OFF by hand at 7:08 and back ON at 7:20. No storm fault. The lodge has no gas: the lights, the heat and the kitchen oven are all electric."),
 ("C9", 1, "The 6:45 Group Photo", "Shoes in the photo: Ivy, velvet heels. Jasper, ski boots. Clem, kitchen clogs (smooth and flat). Rupert, heeled loafers. Noelle, snow boots. Dash, work boots. Marigold, heeled boots. Felix, zigzag sneakers."),
 ("C4", 2, "The Phone Bill", "The lodge phone company's call record: the office landline was on a call from 7:05 to 7:25, to the bank. Landlines work in a blackout. Ivy was in the office the whole time."),
 ("C5", 2, "The Garage Camera", "The battery camera on the garage wall shows Jasper and Dash working on a snowmobile by headlamp at 7:14, and the whole time from 7:06 to 7:30. Neither leaves the frame."),
 ("C6", 2, "The Voice Memo", "A phone recording from the library, time stamped 7:09 to 7:19: Noelle singing a new Christmas song and Felix on guitar. Both voices, start to finish, no gaps."),
 ("C7", 3, "The Room 4 Lock Log", "The battery door lock on Room 4 logs Marigold's key card IN at 7:02 and OUT at 7:31. Room 4 has no other door, and the window is frozen shut."),
 ("C8", 3, "The Star's Mount", "The Star sits on a brass spike, held by a wire twisted tight. The wire was untwisted, not cut: that takes two hands. A doctor's note says Rupert's right hand has been in a splint since Tuesday."),
 ("C2", 3, "The Print on the Bench", "The velvet piano bench under the tree holds one shoe print: a smooth, flat sole with no heel and no tread, and a light dusting of white powder in it."),
]

TIMELINE = [
 ("0:00", "Guests arrive", "Hand out name tags and character sheets (if not sent ahead). Serve drinks."),
 ("0:10", "Read the opening", "Host reads the opening on this page out loud. Everyone reads their Round 1 part."),
 ("0:15", "Round 1: Meet the suspects", "Read Round 1 clue cards (C1, C3, C9). Guests mingle, introduce themselves, ask questions."),
 ("0:45", "Dinner and Round 2", "Read Round 2 clue cards (C4, C5, C6) between courses. Everyone gives their alibi."),
 ("1:15", "Round 3: Secrets out", "Read Round 3 clue cards (C7, C8, C2). Secrets come out. Last questions."),
 ("1:35", "Accusations", "Each player fills in a Detective Notes sheet and names the thief."),
 ("1:45", "The reveal", "Host reads the solution page. The thief takes a bow. Hand out awards."),
]

SOLUTION_READ = ("Lights on, everyone. The clock on the floor tells us when: 7:14, in the dark drawing room. "
  "The bank's phone record puts Ivy in the office. The garage camera clears Jasper and Dash. Noelle and Felix "
  "sang together on a time-stamped memo. Marigold's lock log keeps her in Room 4. Rupert could not untwist that "
  "wire with one good hand. That leaves one person with no proof at all: Clem Baxter. Clem says the buns came out "
  "of the oven at 7:15, but the panel log shows the power was off from 7:08 to 7:20, and every oven here is "
  "electric. And the print on the bench? Smooth, flat, no heel, no tread, dusted with flour. Kitchen clogs.")

MOTIVE = ("Clem's grandmother made the Hollyridge Star with her own hands in 1952 and sold it to the lodge for almost "
  "nothing to pay a doctor's bill. Clem promised her the Star would come home one day. Tonight, in the dark, "
  "Clem tried to keep that promise.")

ENDING = ("Check the flour bin. The Star is wrapped in a tea towel, not a scratch on it. Ivy, moved by the story, "
  "makes Clem an offer: from now on the Star spends every other Christmas on the Baxter family tree. "
  "Clem says yes, and the buns are on the house.")
