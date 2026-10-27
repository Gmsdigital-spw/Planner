"""Christmas Party Bundle (prod-xmas-party-mega-bundle), Night Shift 2026-10-27.
16 content pages + cover + thank-you page. Run: python3 build.py Christmas-Party-Bundle-GMs-Digital-Creations.pdf"""
import sys, random
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from gm_style import PW, PH, MARGIN, wrap
from reportlab.lib.colors import white, HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "bundle.pdf"
registerFont(TTFont("dejavu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

# ------------------------------------------------------------------ content (all real)
SCRAMBLE = ["REINDEER", "SNOWMAN", "MISTLETOE", "ORNAMENT", "STOCKING", "GINGERBREAD",
            "SLEIGH", "TINSEL", "WREATH", "CHIMNEY", "POINSETTIA", "NUTCRACKER",
            "SNOWFLAKE", "CAROLERS"]

def scramble(word, seed):
    r = random.Random(seed)
    s = list(word)
    while True:
        r.shuffle(s)
        t = "".join(s)
        # never the word itself, and never starting with its own first two letters
        if t != word and t[:2] != word[:2]:
            return t
SCRAMBLED = [scramble(w, 100 + i) for i, w in enumerate(SCRAMBLE)]

# (question, options, correct option text)
TRIVIA = [
    ("Which country is usually credited with starting the Christmas tree tradition?",
     ["France", "Germany", "Norway", "England"], "Germany"),
    ("In the 1823 poem 'A Visit from St. Nicholas', how many reindeer pull the sleigh?",
     ["6", "8", "9", "12"], "8"),
    ("What is given on the first day in 'The Twelve Days of Christmas'?",
     ["Two turtle doves", "Five gold rings", "A partridge in a pear tree", "Three French hens"],
     "A partridge in a pear tree"),
    ("Which red-leaved Christmas plant is native to Mexico?",
     ["Holly", "Poinsettia", "Mistletoe", "Amaryllis"], "Poinsettia"),
    ("How many points or arms does a snowflake usually have?",
     ["4", "5", "6", "8"], "6"),
    ("What is the day after Christmas called in the UK and Canada?",
     ["Boxing Day", "Twelfth Night", "St. Stephen's Eve", "Plum Day"], "Boxing Day"),
    ("In the 1823 poem, the children dream of visions of what?",
     ["Gingerbread men", "Sugar-plums", "Candy canes", "Snowflakes"], "Sugar-plums"),
    ("Counting every gift on every day, how many gifts are given in 'The Twelve Days of Christmas'?",
     ["78", "144", "300", "364"], "364"),
    ("The word 'Noel' comes from a Latin word meaning what?",
     ["Snow", "Birth", "Star", "Peace"], "Birth"),
    ("What is the shortest day of the year in the Northern Hemisphere called?",
     ["Winter solstice", "Equinox", "Midwinter Eve", "Polar night"], "Winter solstice"),
    ("Which German glass-making town is famous for the first glass Christmas ornaments?",
     ["Lauscha", "Munich", "Dresden", "Bremen"], "Lauscha"),
    ("Christmas Eve falls on which date?",
     ["December 23", "December 24", "December 25", "December 31"], "December 24"),
]
LET = "ABCD"
SHORT = ["Germany", "8", "Partridge", "Poinsettia", "6", "Boxing Day", "Sugar-plums", "364", "Birth", "Solstice", "Lauscha", "December 24"]
TRIVIA_KEY = [LET[o.index(a)] for _, o, a in TRIVIA]

WYR = [
    ("Wear an ugly sweater to work all December", "Wear a reindeer antler headband all December"),
    ("Only eat Christmas cookies for a week", "Only drink hot cocoa for a week"),
    ("Wrap 50 presents in one night", "Untangle every string of lights in the house"),
    ("Build a snowman in shorts", "Go caroling in your pajamas"),
    ("Get socks every Christmas forever", "Never get a surprise gift again"),
    ("Have a white Christmas every year", "Spend every Christmas on a warm beach"),
    ("Be Santa's best elf for a day", "Ride in the sleigh for one night"),
    ("Open all your gifts on Christmas Eve", "Wait until Christmas night to open them"),
    ("Sing a solo carol in front of everyone", "Do a holiday dance in the living room"),
    ("Lose the TV remote all December", "Lose your phone charger all December"),
    ("Have a 12-foot Christmas tree", "Have a tiny tree in every room"),
    ("Eat the last cookie and get caught", "Never get to eat the last cookie"),
]

THIS_THAT = [("Hot cocoa", "Eggnog"), ("Real tree", "Fake tree"), ("Gift giving", "Gift getting"),
             ("Snow day", "Sunny day"), ("Candy cane", "Gingerbread"), ("Wrapping paper", "Gift bags"),
             ("Colored lights", "White lights"), ("Ugly sweater", "Fancy outfit"), ("Sledding", "Ice skating"),
             ("Cookies", "Pie"), ("Stockings", "Presents"), ("Christmas Eve", "Christmas Day"),
             ("Carols", "Pop songs"), ("Board games", "Movie night"), ("Snowman", "Snow angel"),
             ("Ham", "Turkey"), ("Mittens", "Gloves"), ("Fireplace", "Hot tub"),
             ("Early riser", "Sleep in"), ("Peppermint", "Cinnamon")]

FIND_WHO = ["Has been ice skating this year", "Has a December birthday", "Can name 5 reindeer",
            "Owns an ugly sweater", "Has built a gingerbread house", "Has seen real snow this year",
            "Opens gifts on Christmas Eve", "Has a tree up already", "Has worn a Santa hat today",
            "Can sing a carol from memory", "Has been to a holiday market", "Prefers a fake tree",
            "Loves peppermint", "Has wrapped a gift tonight", "Has a pet in a holiday outfit",
            "Has baked cookies this month", "Has made a snow angel", "Has been sledding",
            "Shops for gifts last minute", "Has a holiday tradition at home", "Has kissed under mistletoe",
            "Has travelled for Christmas", "Can do a reindeer impression", "Hates fruitcake"]

CHARADES = ["Wrapping a gift", "Building a snowman", "Decorating a tree", "Sledding downhill",
            "Ice skating", "Untangling lights", "Baking cookies", "Hanging a stocking",
            "Reindeer flying", "Opening a present", "Snowball fight", "Making a snow angel",
            "Drinking hot cocoa", "Kissing under mistletoe", "Writing to Santa", "Shoveling snow",
            "Elf making toys", "Caroling door to door", "Santa down the chimney", "Lighting a candle",
            "Cutting the turkey", "Wearing mittens", "Shaking a gift box", "Catching snowflakes"]

AWARDS = [
    ("Best Ugly Sweater", "for the loudest, proudest knit in the room"),
    ("Life of the Party", "for keeping the fun going all night"),
    ("Top Cookie Taster", "for sampling every tray, for science"),
    ("Most Festive Outfit", "for head-to-toe Christmas spirit"),
    ("Best Gift Giver", "for the most thoughtful present of the night"),
    ("Jolliest Laugh", "for the laugh we could hear from the North Pole"),
    ("Most Likely to Re-Gift", "for a true talent in recycling joy"),
    ("Best Dance Moves", "for owning the living room dance floor"),
    ("Hot Cocoa Champion", "for never letting a mug run empty"),
    ("Early Bird", "for arriving first and helping set up"),
    ("Gift Wrap Master", "for the neatest corners and the biggest bows"),
    ("Christmas Spirit Award", "for bringing the warmest holiday cheer"),
]

DICE = [
    ("1", "Pick a wrapped gift from the pile, or steal any opened gift."),
    ("2", "Swap your gift with the player on your left."),
    ("3", "Swap your gift with the player on your right."),
    ("4", "Trade gifts with anyone you choose."),
    ("5", "Lucky you: keep your gift and roll again."),
    ("6", "Everyone passes their gift one seat to the left."),
]

STORY = ("It was the night of the office Christmas party, and Holly RIGHT away noticed the gift pile "
         "LEFT under the tree. \"I hope nobody LEFT the good ones at home,\" she said. Her friend Nick "
         "walked RIGHT in with a box so big he had to turn LEFT, then RIGHT, then LEFT again just to get "
         "through the door. \"Is that RIGHT?\" Holly laughed. \"You brought a gift bigger than you?\" "
         "Nick set it down to the RIGHT of the cookies and said, \"You'll see.\" The host clapped and said, "
         "\"Only one rule tonight: nobody opens anything until the story is over!\" Grandma Ivy, who had "
         "LEFT her reading glasses in the car, squinted at the tags. \"This one is for... oh, you're RIGHT, "
         "it says 'anyone'.\" Somebody turned the music up RIGHT as the lights flickered, and the snow outside "
         "LEFT a white blanket on every car. The dog ran LEFT, then RIGHT, chasing a ribbon nobody could catch. "
         "\"Hold on tight,\" said Holly, \"whatever you've got RIGHT now might not be yours for long.\" "
         "Nick checked his watch. There was only one gift LEFT to explain. \"Fine,\" he said, \"it's a sweater. "
         "An ugly one. You're going to love it.\" Everyone laughed RIGHT out loud. Now, before the night is over, "
         "everyone pass one last time to the LEFT, open your gift, and Merry Christmas!")

TIMELINE = [
    ("1 week before", "Print this kit. Cut the charades cards, award strips and contest ribbons."),
    ("2 days before", "Write names on the awards you already know. Ask guests to bring a wrapped gift."),
    ("Party day", "Set out pens, a die, gingerbread kits and candy. Stack game sheets by the door."),
    ("Guests arrive", "Hand out Find the Guest Who (Game 5) as an icebreaker while people mingle."),
    ("First hour", "Word Scramble and Trivia in teams, then This or That and Would You Rather."),
    ("Snack break", "Gingerbread contest: 30 to 45 minutes to build, then judges score."),
    ("Main event", "White elephant dice game, then the left-right story to finish the swap."),
    ("Last 15 min", "Charades, then the awards ceremony and ribbons. Photos!"),
]

GB_RULES = ["Teams of 2 to 4 get the same kit, frosting and candy.",
            "Build time is 45 minutes. Hands off when the host calls time.",
            "Anything edible counts. No glue, tape or toothpicks that show.",
            "Each team names its house and writes it on a score card.",
            "Judges score every entry on the 5 categories, 1 to 10 each.",
            "Highest total wins 1st place. Ties are broken by Christmas Spirit."]
GB_CATS = ["Creativity", "Use of Candy", "Neatness", "Stands Up", "Christmas Spirit"]
RIBBONS = [("1st", "PLACE"), ("2nd", "PLACE"), ("3rd", "PLACE"),
           ("MOST", "CREATIVE"), ("BEST", "CANDY USE"), ("JUDGES'", "PICK")]

# ------------------------------------------------------------------ checks by code
assert len(SCRAMBLE) == len(set(SCRAMBLE)) == 14
for w, s in zip(SCRAMBLE, SCRAMBLED):
    assert sorted(w) == sorted(s) and w != s
for q, o, a in TRIVIA:
    assert a in o and len(o) == 4 and len(set(o)) == 4
assert sum(k * (13 - k) for k in range(1, 13)) == 364   # twelve days total
assert len(FIND_WHO) == 24 and len(CHARADES) == 24 and len(set(CHARADES)) == 24
assert len(SHORT) == 12 and all(sh.split()[0].lower() in a.lower() for sh, (_, _, a) in zip(SHORT, TRIVIA))
assert len(AWARDS) == 12 and len(DICE) == 6 and len(WYR) == 12 and len(THIS_THAT) == 20
N_LEFT, N_RIGHT = STORY.count("LEFT"), STORY.count("RIGHT")
assert STORY.split("LEFT")[-1].count("RIGHT") == 0   # last move is a LEFT pass

# ------------------------------------------------------------------ build
pal = gs.palette("evergreen")
d = gs.Book(OUT, "Christmas Party Bundle", pal, cover_style="band", page_frame="stripe")
c = d.c
CW = PW - 2 * MARGIN
BOTTOM = MARGIN + 16          # top of the footer zone


def ctext(x, y, w, text, font, size, color, lead=1.3, align="c"):
    """Wrapped text in a column; returns y below."""
    c.setFillColor(color); c.setFont(font, size)
    for ln in wrap(text, font, size, w):
        if align == "c": c.drawCentredString(x + w / 2, y - size, ln)
        else: c.drawString(x, y - size, ln)
        y -= size * lead
    return y


def tag(x, y, text, size=8):
    w = stringWidth(text, d.FM, size) + 14
    c.setFillColor(d.T); c.roundRect(x, y - 13, w, 15, 7, fill=1, stroke=0)
    c.setFillColor(d.D); c.setFont(d.FM, size); c.drawString(x + 7, y - 9, text)


def holly(x, y, s=1.0):
    """Kit-style drawn holly sprig (two leaves, three berries)."""
    c.saveState(); c.translate(x, y); c.scale(s, s)
    c.setFillColor(d.P)
    for ang in (-28, 28):
        c.saveState(); c.rotate(ang); c.ellipse(-22 if ang < 0 else 2, -5, 2 if ang < 0 else 22, 5, fill=1, stroke=0); c.restoreState()
    c.setFillColor(HexColor("#B23A3A"))
    for bx, by in ((-3, 2), (3, 2), (0, -3)):
        c.circle(bx, by, 3.2, fill=1, stroke=0)
    c.restoreState()


d.cover(["Christmas Party", "Bundle"], "6 games, 12 awards, a white elephant dice game and a gingerbread contest",
        pages=16, kicker="PRINTABLE PARTY NIGHT KIT")

# ---- page 1: host timeline + how to use + keys
d.start("Host Timeline & How to Use", "Everything for one party night, in the order you will use it.",
        kicker="Start here", centered=True)
d.table(["When", "What to do"], [1.1, 4], TIMELINE, rowh=22, size=9.2)
d.heading("How to use this kit", 12)
d.bullets(["Print on US Letter or A4 at 100% or 'fit to page'. Cardstock is best for awards and ribbons.",
           "Print one game sheet per guest or per team. Keep this page for yourself: the answer keys are below.",
           "You need pens, one six-sided die, gingerbread kits with frosting and candy, scissors."], size=9.4, gap=2)
ky = d.y - 4; bh = ky - BOTTOM - 4
d.box(MARGIN, ky, CW / 2 - 6, bh, "Answer key: Game 1 Word Scramble")
d.box(MARGIN + CW / 2 + 6, ky, CW / 2 - 6, bh, "Answer key: Game 4 Trivia")
c.setFont(d.F, 8.6); c.setFillColor(d.INK)
for i, w in enumerate(SCRAMBLE):
    col, row = divmod(i, 7)
    c.drawString(MARGIN + 14 + col * (CW / 4 - 4), ky - 42 - row * ((bh - 52) / 7), f"{i + 1}. {w.title()}")
for i, (k, (_, o, a)) in enumerate(zip(TRIVIA_KEY, TRIVIA)):
    col, row = divmod(i, 6)
    c.drawString(MARGIN + CW / 2 + 20 + col * (CW / 4 - 4), ky - 42 - row * ((bh - 52) / 6), f"{i + 1}. {k}  {SHORT[i]}")
d.end()

# ---- Game 1: word scramble
d.start("Christmas Word Scramble", "Unscramble each Christmas word. Fastest correct sheet wins.",
        kicker="Game 1 · Ages 6 to adult", centered=True)
rows = [[str(i + 1), " ".join(s), ""] for i, s in enumerate(SCRAMBLED)]
d.table(["#", "Scrambled", "Your answer"], [0.4, 2.4, 3], rows, size=11, fill=True)
d.end()

# ---- Game 2: this or that
d.start("Christmas This or That", "Circle one in every pair, then compare with the person next to you.",
        kicker="Game 2 · Icebreaker", centered=True)
rh = (d.y - BOTTOM) / 10; y0 = d.y
for i, (a, b) in enumerate(THIS_THAT):
    col, row = i % 2, i // 2
    x = MARGIN + col * (CW / 2 + 4); y = y0 - row * rh; w = CW / 2 - 4
    c.setFillColor(d.T if row % 2 == 0 else white); c.roundRect(x, y - rh + 4, w, rh - 6, 6, fill=1, stroke=0)
    c.setFillColor(d.INK); c.setFont(d.FM, 11)
    c.drawCentredString(x + w * 0.27, y - rh / 2 - 2, a); c.drawCentredString(x + w * 0.73, y - rh / 2 - 2, b)
    c.setFillColor(d.A); c.setFont(d.S, 10); c.drawCentredString(x + w / 2, y - rh / 2 - 2, "or")
d.y = y0 - 10 * rh
d.end()

# ---- Game 3: would you rather
d.start("Christmas Would You Rather", "Tick your choice for each one. Read them aloud and see who matches.",
        kicker="Game 3 · Any age", centered=True)
rh = (d.y - BOTTOM) / 12; y0 = d.y
for i, (a, b) in enumerate(WYR):
    y = y0 - i * rh
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(MARGIN, y - rh + 2, PW - MARGIN, y - rh + 2)
    c.setFillColor(d.T); c.circle(MARGIN + 11, y - rh / 2, 10, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawCentredString(MARGIN + 11, y - rh / 2 - 3, str(i + 1))
    for j, opt in enumerate((a, b)):
        x = MARGIN + 30 + j * (CW - 30) / 2
        c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(x, y - rh / 2 - 5, 10, 10, 2, fill=0, stroke=1)
        ctext(x + 16, y - rh / 2 + 10, (CW - 30) / 2 - 44, opt, d.F, 9.6, d.INK, align="l")
    c.setFillColor(d.A); c.setFont(d.S, 9); c.drawCentredString(MARGIN + 30 + (CW - 30) / 2 - 16, y - rh / 2 - 3, "or")
d.end()

# ---- Game 4: trivia
d.start("Christmas Trivia Quiz", "Circle A, B, C or D. One point each. Play in teams of 2 to 4.",
        kicker="Game 4 · Teams", centered=True)
rh = (d.y - BOTTOM) / 12; y0 = d.y
for i, (q, o, a) in enumerate(TRIVIA):
    y = y0 - i * rh
    c.setFillColor(d.T if i % 2 == 0 else white); c.rect(MARGIN, y - rh + 2, CW, rh - 2, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.FM, 10); c.drawString(MARGIN + 8, y - 15, f"{i + 1}.")
    yy = ctext(MARGIN + 28, y - 3, CW - 40, q, d.FM, 9.6, d.INK, align="l")
    fs = 9.2; avail = CW - 40
    labs = [f"{LET[j]})  {opt}" for j, opt in enumerate(o)]
    while sum(stringWidth(t, d.F, fs) for t in labs) + 3 * 14 > avail: fs -= 0.2
    gap = (avail - sum(stringWidth(t, d.F, fs) for t in labs)) / 3
    gap = min(gap, 40); x = MARGIN + 28
    c.setFont(d.F, fs); c.setFillColor(d.INK)
    for t in labs:
        c.drawString(x, yy - 12, t); x += stringWidth(t, d.F, fs) + gap
d.end()

# ---- Game 5: find the guest who
d.start("Find the Guest Who", "Find a guest for each square and have them sign it. First full row wins.",
        kicker="Game 5 · Mingle", centered=True)
n = 5; gw = CW / n; gh = (d.y - BOTTOM) / n; y0 = d.y; k = 0
for r in range(n):
    for cc in range(n):
        x, y = MARGIN + cc * gw, y0 - r * gh
        free = (r == 2 and cc == 2)
        c.setFillColor(d.P if free else (d.T if (r + cc) % 2 == 0 else white))
        c.setStrokeColor(d.P); c.setLineWidth(0.8); c.rect(x, y - gh, gw, gh, fill=1, stroke=1)
        if free:
            c.setFillColor(white); c.setFont(d.S, 15); c.drawCentredString(x + gw / 2, y - gh / 2 + 2, "MERRY")
            c.setFont(d.FM, 8); c.drawCentredString(x + gw / 2, y - gh / 2 - 12, "FREE SPACE")
            continue
        ctext(x + 6, y - 8, gw - 12, FIND_WHO[k], d.FM, 8.8, d.INK)
        c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(x + 10, y - gh + 16, x + gw - 10, y - gh + 16)
        c.setFillColor(d.MUT); c.setFont(d.F, 6.5); c.drawCentredString(x + gw / 2, y - gh + 7, "signature")
        k += 1
d.end()

# ---- Game 6: charades cards
d.start("Christmas Charades Cards", "Cut out the cards. Act it out, no talking. Your team has 60 seconds to guess.",
        kicker="Game 6 · Cut and play", centered=True)
cols, rws = 4, 6; gw = CW / cols; gh = (d.y - BOTTOM) / rws; y0 = d.y
c.setDash(4, 3)
for i, word in enumerate(CHARADES):
    cc, r = i % cols, i // cols; x, y = MARGIN + cc * gw, y0 - r * gh
    c.setStrokeColor(d.MUT); c.setLineWidth(0.5); c.rect(x, y - gh, gw, gh, fill=0, stroke=1)
c.setDash()
for i, word in enumerate(CHARADES):
    cc, r = i % cols, i // cols; x, y = MARGIN + cc * gw, y0 - r * gh
    c.setFillColor(d.A); c.setFont(d.FM, 6.8); c.drawCentredString(x + gw / 2, y - 16, f"CHARADES  ·  {i + 1:02d}")
    lines = wrap(word, d.S, 13, gw - 20); ty = y - gh / 2 + (len(lines) - 1) * 8 - 2
    c.setFillColor(d.D); c.setFont(d.S, 13)
    for ln in lines: c.drawCentredString(x + gw / 2, ty, ln); ty -= 16
d.end()

# ---- Awards: 4 pages x 3
for p in range(4):
    d.start("Christmas Party Awards", "Cut along the dashed lines. Write a name and present at the end of the night.",
            kicker=f"Awards {p * 3 + 1} to {p * 3 + 3} of 12", centered=True)
    ah = (d.y - BOTTOM) / 3; y0 = d.y
    for j in range(3):
        title, why = AWARDS[p * 3 + j]
        y = y0 - j * ah; bx, by, bw, bh = MARGIN, y - ah + 6, CW, ah - 12
        c.setStrokeColor(d.MUT); c.setLineWidth(0.5); c.setDash(4, 3); c.rect(bx - 3, by - 3, bw + 6, bh + 6, fill=0, stroke=1); c.setDash()
        c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1.6); c.roundRect(bx, by, bw, bh, 8, fill=1, stroke=1)
        c.setStrokeColor(d.A); c.setLineWidth(0.7); c.roundRect(bx + 7, by + 7, bw - 14, bh - 14, 5, fill=0, stroke=1)
        holly(bx + 40, by + bh - 34, 1.0); holly(bx + bw - 40, by + bh - 34, 1.0)
        gs_y = by + bh - 30
        d._spaced(PW / 2, gs_y, "THIS AWARD IS PRESENTED TO", 7.5, d.P, d.FM)
        c.setStrokeColor(d.INK); c.setLineWidth(0.7); c.line(PW / 2 - 150, gs_y - 30, PW / 2 + 150, gs_y - 30)
        c.setFillColor(d.D); c.setFont(d.S, 25); c.drawCentredString(PW / 2, gs_y - 62, title)
        c.setFillColor(d.INK); c.setFont(d.SS, 11); c.drawCentredString(PW / 2, gs_y - 80, why)
        ly = by + 26
        c.setStrokeColor(d.HAIR); c.setLineWidth(0.6)
        c.line(bx + 40, ly, bx + 200, ly); c.line(bx + bw - 200, ly, bx + bw - 40, ly)
        c.setFillColor(d.MUT); c.setFont(d.F, 7.5)
        c.drawCentredString(bx + 120, ly - 11, "DATE"); c.drawCentredString(bx + bw - 120, ly - 11, "PRESENTED BY")
        c.setFillColor(d.P); c.setFont(d.FM, 8); c.drawCentredString(PW / 2, ly - 4, "Christmas Party " + "  ·  " + "Award")
    d.end()

# ---- Gingerbread 1: rules
d.start("Gingerbread House Contest", "Rules, judging and the entry list for a 45-minute decorating contest.",
        kicker="Contest · Page 1 of 3", centered=True)
d.heading("The rules", 12)
d.bullets(GB_RULES, size=9.8, numbered=True, gap=3)
d.heading("How judges score", 12)
d.bullets([f"{cat}: 1 to 10 points" for cat in GB_CATS] + ["Best total: 50 points"], size=9.6, cols=2, gap=2)
d.table(["Entry #", "Team / house name", "Builders", "Total / 50"], [0.7, 2.4, 2.4, 1], empty=8, fill=True)
d.end()

# ---- Gingerbread 2: score cards (4)
d.start("Judge's Score Cards", "One card per entry. Circle a score from 1 to 10 in each row, then add the total.",
        kicker="Contest · Page 2 of 3", centered=True)
gw = CW / 2; gh = (d.y - BOTTOM) / 2; y0 = d.y
for i in range(4):
    cc, r = i % 2, i // 2; x, y = MARGIN + cc * gw + 4, y0 - r * gh - 4; w, h = gw - 8, gh - 8
    c.setStrokeColor(d.P); c.setLineWidth(1.1); c.setFillColor(white); c.roundRect(x, y - h, w, h, 8, fill=1, stroke=1)
    c.setFillColor(d.P); c.roundRect(x, y - 26, w, 26, 8, fill=1, stroke=0); c.rect(x, y - 26, w, 10, fill=1, stroke=0)
    c.setFillColor(white); c.setFont(d.FM, 9.5); c.drawString(x + 12, y - 17, "SCORE CARD")
    c.setFont(d.F, 8.5); c.drawRightString(x + w - 12, y - 17, "Entry # ______")
    c.setFillColor(d.INK); c.setFont(d.F, 8.5); c.drawString(x + 12, y - 44, "House name")
    c.setStrokeColor(d.HAIR); c.line(x + 70, y - 45, x + w - 12, y - 45)
    rowy = y - 62; rstep = (h - 62 - 52) / len(GB_CATS)
    for cat in GB_CATS:
        c.setFillColor(d.D); c.setFont(d.FM, 8.6); c.drawString(x + 12, rowy - 9, cat)
        for s in range(10):
            sx = x + 12 + s * (w - 24) / 10 + (w - 24) / 20
            c.setStrokeColor(d.P); c.setLineWidth(0.6); c.setFillColor(d.T); c.circle(sx, rowy - 22, 6.8, fill=1, stroke=1)
            c.setFillColor(d.INK); c.setFont(d.F, 7); c.drawCentredString(sx, rowy - 24.4, str(s + 1))
        rowy -= rstep
    c.setFillColor(d.D); c.setFont(d.SB, 11); c.drawString(x + 12, y - h + 18, "Total")
    c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(x + 52, y - h + 12, 60, 22, 4, fill=0, stroke=1)
    c.setFillColor(d.MUT); c.setFont(d.F, 8.5); c.drawString(x + 118, y - h + 18, "/ 50")
    c.drawRightString(x + w - 12, y - h + 18, "Judge ________")
d.end()

# ---- Gingerbread 3: ribbons
d.start("Contest Ribbons", "Cut out each ribbon and give it to the winning team. Print on cardstock.",
        kicker="Contest · Page 3 of 3", centered=True)
gw = CW / 3; gh = (d.y - BOTTOM) / 2; y0 = d.y
import math
for i, (a, b) in enumerate(RIBBONS):
    cc, r = i % 3, i // 3; cx = MARGIN + cc * gw + gw / 2; top = y0 - r * gh
    R = min(gw, gh * 0.62) / 2 - 8; cy = top - R - 10
    # tails
    c.setFillColor(d.D if i < 3 else d.P)
    for sgn in (-1, 1):
        p_ = c.beginPath(); p_.moveTo(cx + sgn * 6, cy - R * 0.5); p_.lineTo(cx + sgn * (R * 0.55), cy - R * 0.5)
        p_.lineTo(cx + sgn * (R * 0.62), top - gh + 14); p_.lineTo(cx + sgn * (R * 0.33), top - gh + 30)
        p_.lineTo(cx + sgn * 2, top - gh + 14); p_.close(); c.drawPath(p_, fill=1, stroke=0)
    # rosette
    c.setFillColor(d.A)
    pts = 24; p_ = c.beginPath()
    for t in range(pts * 2 + 1):
        ang = math.pi * t / pts; rr = R if t % 2 == 0 else R * 0.88
        X, Y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
        (p_.moveTo if t == 0 else p_.lineTo)(X, Y)
    p_.close(); c.drawPath(p_, fill=1, stroke=0)
    c.setFillColor(white); c.circle(cx, cy, R * 0.76, fill=1, stroke=0)
    c.setStrokeColor(d.P); c.setLineWidth(1.2); c.circle(cx, cy, R * 0.7, fill=0, stroke=1)
    s1 = 30 if len(a) <= 4 else 20
    c.setFillColor(d.D); c.setFont(d.S, s1); c.drawCentredString(cx, cy + 2, a)
    c.setFillColor(d.P); c.setFont(d.FM, 9 if len(b) < 9 else 8); c.drawCentredString(cx, cy - 16, b)
    c.setFillColor(d.MUT); c.setFont(d.F, 6.5); c.drawCentredString(cx, cy - R * 0.45, "GINGERBREAD CONTEST")
d.end()

# ---- White elephant 1: dice game
d.start("White Elephant Dice Game", "Everyone brings one wrapped gift. Sit in a circle with the gifts in the middle.",
        kicker="Gift swap · Page 1 of 2", centered=True)
d.heading("How to play", 12)
d.bullets(["Youngest player rolls first. Go around the circle to the left.",
           "Roll the die and do what the chart says. Unwrap a gift as soon as you pick it.",
           "A gift can be stolen 3 times. After the third steal it is frozen and stays put.",
           "When every gift is opened, play the left-right story on the next page to finish."],
          size=9.8, numbered=True, gap=2)
rh = (d.y - BOTTOM - 14) / 6; y0 = d.y - 6
for i, (num, act) in enumerate(DICE):
    y = y0 - i * rh
    c.setFillColor(d.T if i % 2 == 0 else white); c.roundRect(MARGIN, y - rh + 4, CW, rh - 6, 8, fill=1, stroke=0)
    s = min(rh - 18, 58); dx, dy = MARGIN + 16, y - rh / 2 - s / 2 + 1
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.4); c.roundRect(dx, dy, s, s, 8, fill=1, stroke=1)
    pip = {1: [(0.5, 0.5)], 2: [(0.27, 0.73), (0.73, 0.27)], 3: [(0.25, 0.75), (0.5, 0.5), (0.75, 0.25)],
           4: [(0.27, 0.27), (0.27, 0.73), (0.73, 0.27), (0.73, 0.73)],
           5: [(0.25, 0.25), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25), (0.75, 0.75)],
           6: [(0.27, 0.22), (0.27, 0.5), (0.27, 0.78), (0.73, 0.22), (0.73, 0.5), (0.73, 0.78)]}[int(num)]
    c.setFillColor(d.D)
    for px, py in pip: c.circle(dx + px * s, dy + py * s, s * 0.085, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.S, 18); c.drawString(dx + s + 22, y - rh / 2 + 3, f"Roll {num}")
    ctext(dx + s + 110, y - rh / 2 + 13, CW - s - 140, act, d.F, 11, d.INK, align="l")
d.end()

# ---- White elephant 2: left-right story
d.start("The Left-Right Gift Story", f"Read aloud. Pass your gift LEFT or RIGHT each time you hear the word ({N_LEFT} lefts, {N_RIGHT} rights).",
        kicker="Gift swap · Page 2 of 2", centered=True)
bh = d.y - BOTTOM - 2; box_top = d.y
def _lines(size):
    out, cur = [], []
    for w in STORY.split():
        t = " ".join(cur + [w])
        if stringWidth(t, d.F, size) > CW - 50 and cur: out.append(cur); cur = [w]
        else: cur.append(w)
    return out + [cur]
size = 12.4
while len(_lines(size + 0.2)) * (size + 0.2) * 1.7 < bh - 70: size += 0.2
lines = _lines(size); lead = size * 1.7
c.setFillColor(d.T); c.roundRect(MARGIN, box_top - bh, CW, bh, 10, fill=1, stroke=0)
holly(PW - MARGIN - 34, box_top - bh + 26, 1.1)
used = len(lines) * lead; y = box_top - (bh - used) / 2 - 4
for ln in lines:
    x = MARGIN + 20
    for w in ln:
        bold = "LEFT" in w or "RIGHT" in w
        f = d.FB if bold else d.F; col = HexColor("#B23A3A") if "RIGHT" in w else (d.P if bold else d.INK)
        c.setFillColor(col); c.setFont(f, size); c.drawString(x, y - size, w)
        x += stringWidth(w + " ", f, size)
    y -= lead
d.end()

# ---- thank-you page (spec text verbatim, not counted)
d.page += 1; d._frame()
c.setFillColor(d.T); c.roundRect(MARGIN + 20, 150, CW - 40, PH - 300, 16, fill=1, stroke=0)
holly(PW / 2, PH - 210, 1.6)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, PH - 270, "You just made my day!")
d._ornament(PW / 2, PH - 292)
y = PH - 330
for t in ["Thank you for choosing a small, one-person shop over the big guys.",
          "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one."]:
    y = ctext(MARGIN + 70, y, CW - 140, t, d.SS, 14, d.INK, lead=1.45) - 16
# how line with arrows in DejaVu (Lora/Poppins lack the arrow glyph)
parts = ["How: Etsy app ", "→", " You ", "→", " Purchases ", "→", " Leave a review"]
fs = 12.5; tw = sum(stringWidth(p, "dejavu" if p == "→" else d.FM, fs) for p in parts)
x = PW / 2 - tw / 2; y -= 6
c.setFillColor(white); c.roundRect(x - 16, y - fs - 10, tw + 32, fs + 22, 10, fill=1, stroke=0)
c.setFillColor(d.P)
for p in parts:
    f = "dejavu" if p == "→" else d.FM; c.setFont(f, fs); c.drawString(x, y - fs, p); x += stringWidth(p, f, fs)
y -= fs + 44
y = ctext(MARGIN + 70, y, CW - 140, "Something not right? Message me first and I'll fix it fast.", d.SS, 13.5, d.INK)
c.setFillColor(d.D); c.setFont(d.S, 15); c.drawCentredString(PW / 2, 200, "With thanks,")
c.setFillColor(d.P); c.setFont(d.SB, 17); c.drawCentredString(PW / 2, 176, "GM's Digital Creations")
c.showPage()
d.save()
print("ok", OUT, "lefts", N_LEFT, "rights", N_RIGHT, "trivia key", "".join(TRIVIA_KEY))
print("scrambled", list(zip(SCRAMBLE, SCRAMBLED)))
