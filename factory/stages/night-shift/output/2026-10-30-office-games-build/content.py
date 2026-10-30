"""Content for Office Christmas Party Games (24 original games). All text original; no brands, songs or movies."""

# (name, players, minutes, type, how to play, win/tip, sheet page or None)
GAMES = [
    ("Coworker Holiday Bingo", "6 to 60", "10 min", "Mingle",
     "Give everyone a bingo card and a pen. Players walk around and find a different coworker for each square, "
     "then write that person's first name in it. One name per square, and nobody signs their own card.",
     "Win: first to fill a full row, column or diagonal shouts \"Bingo!\" and reads the names out loud.", 10),
    ("Holiday Word Scramble", "Teams of 3 to 6", "8 min", "Team",
     "Hand each team one scramble sheet. Teams unscramble the 20 holiday words using the small hint beside "
     "each one. Call time after 6 minutes, then swap sheets with the next table to mark them from the key.",
     "Win: 1 point per correct word. Ties go to the team that handed in first.", 11),
    ("Holiday Trivia Showdown", "Teams of 3 to 6", "12 min", "Team",
     "Each team gets one trivia sheet. The host reads each question out loud once, and teams talk quietly and "
     "write one answer. Every question is general holiday and winter knowledge: no movies, no songs.",
     "Win: 1 point per correct answer from the key. Read the last 5 answers slowly for drama.", 12),
    ("Letter Lists", "Teams of 2 to 6", "10 min", "Team",
     "The host calls a letter. Teams have 2 minutes to write one answer for each category that starts with "
     "that letter. Play 3 rounds with 3 different letters. Read answers aloud at the end of each round.",
     "Win: 1 point for every answer no other team wrote. Duplicates score 0.", 13),
    ("Guess the Coworker", "6 to 40", "15 min", "Icebreaker",
     "Before the games, everyone fills in a fact card without writing their name and drops it in a pile. "
     "The host reads one card at a time, and the room shouts guesses. The writer stands up after 3 guesses.",
     "Tip: hand out cards as people arrive, so they are filled in before the first game.", 14),
    ("Silent Line-Up", "8 to 40", "5 min", "Mingle",
     "Without talking, the whole group lines up in order of birthday, January 1 at one end and December 31 "
     "at the other. Pointing and hand signs are fine. When everyone is still, check the line out loud.",
     "Tip: count off along the finished line to make even teams for the next game.", None),
    ("This or That Walk", "6 to 60", "5 min", "Active",
     "Point to one side of the room for \"this\" and the other for \"that\". Read pairs and players walk to a side: "
     "cookies or pie, snow or sunshine, wrap gifts or open them, early bird or night owl, cocoa or cider.",
     "Tip: ask one person on the smaller side to explain their pick in one sentence.", None),
    ("Two Truths and a Tale", "6 to 20", "10 min", "Icebreaker",
     "One at a time, players share three short statements about their holiday seasons: two true and one "
     "made up. The group votes on which one is the tale, then the speaker reveals the answer.",
     "Win: everyone who fooled at least half the room gets 1 point.", None),
    ("Snowball Questions", "8 to 60", "8 min", "Active",
     "Everyone writes a fun question on scrap paper (\"best gift you ever got?\"), crumples it into a snowball "
     "and throws it on the count of three. Pick up any snowball and answer it to a nearby coworker.",
     "Tip: throw two more rounds so people talk to someone new each time.", None),
    ("Pass the Story", "6 to 20", "8 min", "Seated",
     "Sit in a circle. The host starts: \"The night before the office party, the copier started to glow...\" "
     "Going around, each person adds exactly one sentence. The last player must give the story an ending.",
     "Tip: the host repeats the funniest line at the end for a round of applause.", None),
    ("Draw It on Your Head", "6 to 60", "5 min", "Seated",
     "Everyone holds a sheet of paper flat on top of their head and draws a snowman while the host "
     "calls the parts: body, head, hat, scarf, three buttons, carrot nose, arms. No peeking until the end.",
     "Win: the room votes for the snowman whose nose is closest to its face.", None),
    ("Holiday Alphabet Chain", "6 to 30", "5 min", "Seated",
     "Go around the circle naming winter or holiday words in order of the alphabet: apple cider, bow, candle "
     "and on. A player who takes more than 5 seconds sits out. Skip Q, X and Z, or allow any word.",
     "Win: the last player still in the chain.", None),
    ("Pocket Scavenger Hunt", "Teams of 4 to 8", "8 min", "Team",
     "Teams search only their own pockets, bags and desks. The host calls one thing at a time: something red, "
     "a receipt, a pen that clicks, a coin, something with a snowflake, a sticky note, a key, a mint.",
     "Win: the first team to hold up the called item scores 1 point.", None),
    ("Sixty-Second Sprints", "Teams of 3 to 6", "10 min", "Team",
     "Run quick one-minute rounds: name 12 holiday cookies, list 15 things that are green, write 10 gifts "
     "under five dollars, name 8 winter sports, list 10 words that rhyme with snow. Teams write as they go.",
     "Win: 1 point for each round a team finishes before the minute is up.", None),
    ("Big Word Builder", "Solo or pairs", "5 min", "Seated",
     "Write HAPPY HOLIDAYS EVERYONE at the top of any paper. In 3 minutes, players make as many words of 3 "
     "or more letters as they can, using each letter only as many times as it appears in the phrase.",
     "Win: the longest list. Bonus point for the longest single word.", None),
    ("Freeze Frame", "Teams of 4 to 8", "10 min", "Active",
     "Whisper a scene to one team: the office at 4:59 on the last day before the break, the gift exchange, "
     "a snowball fight. The team has 30 seconds to build a frozen picture, and the room guesses the scene.",
     "Win: a correct guess gives 1 point to the guessers and 1 to the team.", None),
    ("Holiday Act-It-Out", "6 to 40", "10 min", "Active",
     "One player acts out a holiday task with no words or sounds while their team guesses: wrapping a "
     "huge gift, untangling lights, shoveling snow, ice skating, baking cookies, hanging a wreath.",
     "Win: each correct guess inside 45 seconds earns the team 1 point.", None),
    ("Team Holiday Haiku", "Teams of 3 to 6", "8 min", "Team",
     "Each team writes a haiku about holiday season at work: 5 syllables, then 7, then 5. Topics can be the "
     "break room, the year-end rush or the office party itself. One person per team reads it out loud.",
     "Win: the room claps for each one and the host picks the loudest cheer.", None),
    ("Kind Words Circle", "6 to 30", "8 min", "Seated",
     "Everyone writes their name at the top of a sheet of paper and passes it left. Each person adds one "
     "short, kind line about that coworker, folds the paper over and passes it on until it comes home.",
     "Tip: play near the end; people keep these sheets long after the party.", None),
    ("Last One Standing", "8 to 60", "3 min", "Active",
     "Everyone stands. The host reads statements and people sit when one is true for them: I have shopped "
     "online this week, I own a holiday sweater, I have burned cookies, I have wrapped a gift in newspaper.",
     "Win: the last person standing. Keep adding statements until one remains.", None),
    ("Snowflake Showdown", "10 to 60", "5 min", "Active",
     "Pairs play rock, paper, scissors. The loser becomes the winner's cheering fan and follows them to the "
     "next match, so the cheering crowds grow each round until two big crowds face off in the final.",
     "Win: the last player standing takes the title of Snowflake Champion.", None),
    ("Guess My Gift", "6 to 30", "8 min", "Seated",
     "One player secretly picks a holiday gift. The group asks up to 20 yes-or-no questions (\"Can you eat "
     "it?\" \"Does it plug in?\") to guess it. Whoever guesses right picks the next gift.",
     "Win: guessers score 1 point if they solve it in 20 questions or fewer.", None),
    ("Office Superlatives", "6 to 60", "10 min", "Seated",
     "Read fun award names and everyone writes one coworker's name for each: best desk snacks, calmest on a "
     "deadline, best email sign-off, most likely to bring cookies, best laugh. Collect and read the winners.",
     "Tip: keep every award kind. Announce them as the last thing before goodbyes.", None),
    ("Holiday Name Game", "6 to 20", "5 min", "Icebreaker",
     "Each person says their first name and a holiday food with the same first letter (\"Pat, pumpkin pie\"), "
     "then repeats everyone who went before them. The last player has to remember the whole circle.",
     "Tip: great for teams where not everyone knows each other yet.", None),
]
assert len(GAMES) == 24

BINGO = [
    "Has been skiing or snowboarding", "Bakes cookies every December", "Has a holiday birthday",
    "Wrapped a gift this week", "Can name all their cousins", "Prefers pie over cake",
    "Has worked here 5+ years", "Started here this year", "Owns a holiday sweater",
    "Has built a snowman", "Drinks cocoa, not coffee", "Has a pet with a holiday name",
    "Shops for gifts in July", "Has been ice skating", "Can say hello in 3 languages",
    "Has never seen real snow", "Sends paper holiday cards", "Is the oldest sibling",
    "Has a gift-wrapping trick", "Was born in December", "Makes a family recipe",
    "Has stayed up past midnight on New Year's", "Has sledded down a hill", "Plays an instrument",
]
assert len(BINGO) == 24 and len(set(BINGO)) == 24

# (answer, hint)
SCRAMBLE = [
    ("SNOWFLAKE", "falls from winter clouds"), ("MITTENS", "warm hands"), ("GINGERBREAD", "a cookie house"),
    ("ORNAMENT", "hangs on a tree"), ("WREATH", "round, on the door"), ("SLEIGH", "rides over snow"),
    ("REINDEER", "antlers"), ("TINSEL", "shiny strands"), ("CANDLE", "has a wick"),
    ("COCOA", "hot drink"), ("SWEATER", "knit and cozy"), ("PEPPERMINT", "cool candy flavor"),
    ("GARLAND", "draped decoration"), ("ICICLE", "hangs from the roof"), ("CHIMNEY", "smoke goes up it"),
    ("STOCKING", "hung up for gifts"), ("SNOWMAN", "carrot nose"), ("HOLLY", "red berries, spiky leaves"),
    ("MISTLETOE", "hung over a doorway"), ("CALENDAR", "counts down the days"),
]
assert len(SCRAMBLE) == 20


def scramble(word, seed):
    import random
    r = random.Random(seed * 7919 + len(word))
    while True:
        l = list(word); r.shuffle(l); s = "".join(l)
        # not the word, not the word reversed, first letter moved, no 3-letter run of the answer kept
        if s != word and s != word[::-1] and s[0] != word[0] and not any(word[i:i + 3] in s for i in range(len(word) - 2)):
            return s


# (question, answer) all general knowledge, checked against common references
TRIVIA = [
    ("How many points or arms does a typical snowflake have?", "6"),
    ("Poinsettia plants are native to which country?", "Mexico"),
    ("In the Northern Hemisphere, the shortest day of the year falls in which month?", "December"),
    ("What is the name for the shortest day of the year?", "Winter solstice"),
    ("Which spice gives gingerbread its name?", "Ginger"),
    ("At how many degrees Fahrenheit does water freeze?", "32"),
    ("In North America, wild reindeer are usually called what?", "Caribou"),
    ("Which country is known for starting the decorated indoor Christmas tree tradition?", "Germany"),
    ("What flavor is a classic red-and-white candy cane?", "Peppermint"),
    ("Hanukkah is celebrated for how many nights?", "8"),
    ("Kwanzaa begins on which date in December?", "December 26"),
    ("Do polar bears live in the Arctic or the Antarctic?", "The Arctic"),
    ("Most wild penguins live in which half of the world: Northern or Southern?", "Southern Hemisphere"),
    ("\"Noel\" comes from which language's word for Christmas?", "French"),
    ("What color are the berries of mistletoe usually?", "White"),
    ("What do you call ice crystals that form on a cold window overnight?", "Frost"),
    ("The holiday drink eggnog is made mainly with milk or cream, sugar and what?", "Eggs"),
    ("In which month does the Northern Hemisphere's winter officially begin?", "December"),
    ("Holly bushes are known for spiky green leaves and berries of what color?", "Red"),
    ("A New Year's ball drops in which famous New York City square?", "Times Square"),
]
assert len(TRIVIA) == 20 and len(set(q for q, a in TRIVIA)) == 20

LETTER_CATS = ["A holiday food", "Something cold", "Something in an office", "A gift under $10",
               "Something that sparkles", "A winter activity", "Something red or green", "A word for a great coworker"]

FACT_PROMPTS = ["My favorite holiday food is", "My first ever job was", "A hidden talent of mine is",
                "My dream winter trip is", "The best gift I ever got was"]

RUN_SHEET = [
    ("0:00", "5 min", "Silent Line-Up", "Mixes the room and makes even teams (count off along the line)."),
    ("0:05", "10 min", "Coworker Holiday Bingo", "Everyone talks to someone new. Hand out cards at the door."),
    ("0:15", "12 min", "Holiday Trivia Showdown", "Teams sit together. Host reads; teams write answers."),
    ("0:27", "8 min", "Holiday Word Scramble", "Same teams. Swap sheets and mark from the key."),
    ("0:35", "5 min", "This or That Walk", "Everyone up and moving after the paper games."),
    ("0:40", "3 min", "Last One Standing", "A quick, loud finish the whole room can play."),
    ("0:43", "2 min", "Scores and winners", "Add up the score sheet and cheer the winning team."),
]
assert sum(int(r[1].split()[0]) for r in RUN_SHEET) == 45
