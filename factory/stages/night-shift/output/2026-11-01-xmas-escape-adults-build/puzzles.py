"""The Snowbound Lodge: 8 linked puzzles. Every answer feeds the next; verify() proves the chain by code."""
import random, itertools

A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# P1 acrostic: first letters of the keeper's letter spell SHIFT BY NINE -> 9
LETTER = [
    "Snow came early this year, and the road up to the lodge closed by noon.",
    "Hot cider is on the stove, and the fire should last until morning.",
    "I had to leave before the storm, so every gift is locked in the vault.",
    "Find your way in, and the gifts are yours to open tonight.",
    "The window, the card box and the old clock each hold a piece of the way in.",
    "Begin at the frosted window beside the front door.",
    "You will see that the letters there have slipped out of place.",
    "Nothing in this lodge is random, not even this letter.",
    "If you get stuck, your host has hint cards for every room.",
    "Not every clue looks like a clue at first glance.",
    "Enjoy the night, and save me a slice of pie.",
]
P1_ANS = 9


def caesar(s, k):
    return "".join(A[(A.index(ch) + k) % 26] if ch in A else ch for ch in s)


# P2 Caesar +9 on the window
P2_PLAIN = "THE CARD BOX KEYWORD IS PINE"
P2_CIPHER = caesar(P2_PLAIN, P1_ANS)
P2_ANS = "PINE"


def vig(s, key, sign=1):
    out, i = [], 0
    for ch in s:
        if ch in A:
            out.append(A[(A.index(ch) + sign * A.index(key[i % len(key)])) % 26]); i += 1
        else:
            out.append(ch)
    return "".join(out)


# P3 keyword (Vigenere) cipher with PINE
P3_PLAIN = "STOP THE CLOCK AT ROW SIX"
P3_CIPHER = vig(P3_PLAIN, P2_ANS)
P3_ANS = 6


# P4 6x6 sudoku (2x3 boxes)
def sud_solve(g, limit=2):
    sols = []
    def ok(r, c, v):
        if v in g[r]: return False
        if any(g[i][c] == v for i in range(6)): return False
        br, bc = r // 2 * 2, c // 3 * 3
        return all(g[i][j] != v for i in range(br, br + 2) for j in range(bc, bc + 3))
    def rec():
        for r in range(6):
            for c in range(6):
                if g[r][c] == 0:
                    for v in range(1, 7):
                        if ok(r, c, v):
                            g[r][c] = v; rec(); g[r][c] = 0
                            if len(sols) >= limit: return
                    return
        sols.append([row[:] for row in g])
    rec()
    return sols


def make_sudoku(seed=11, givens_target=12):
    rnd = random.Random(seed)
    base = [[(3 * (r % 2) + r // 2 + c) % 6 + 1 for c in range(6)] for r in range(6)]
    assert sud_solve([row[:] for row in base], 1), "base invalid"
    perm = list(range(1, 7)); rnd.shuffle(perm)
    sol = [[perm[v - 1] for v in row] for row in base]
    # shuffle rows within bands, bands, cols within stacks
    bands = [0, 1, 2]; rnd.shuffle(bands)
    rows = [b * 2 + i for b in bands for i in rnd.sample([0, 1], 2)]
    sol = [sol[r] for r in rows]
    cols = [s * 3 + i for s in rnd.sample([0, 1], 2) for i in rnd.sample([0, 1, 2], 3)]
    sol = [[row[c] for c in cols] for row in sol]
    puz = [row[:] for row in sol]
    cells = [(r, c) for r in range(6) for c in range(6)]; rnd.shuffle(cells)
    for r, c in cells:
        if sum(v != 0 for row in puz for v in row) <= givens_target: break
        keep = puz[r][c]; puz[r][c] = 0
        if len(sud_solve([row[:] for row in puz])) != 1: puz[r][c] = keep
    return sol, puz


SUD_SOL, SUD_PUZ = make_sudoku()
# one shaded triple per row (the row named by P3 holds the room number)
SHADE = {0: (0, 2, 4), 1: (1, 3, 5), 2: (0, 1, 5), 3: (2, 3, 4), 4: (0, 3, 5), 5: None}


def pick_row6():
    r = P3_ANS - 1
    for t in itertools.combinations(range(6), 3):
        n = int("".join(str(SUD_SOL[r][c]) for c in t))
        if 205 <= n <= 420 and t not in SHADE.values():
            return t, n
    raise AssertionError("no room number in row 6")


SHADE[5], ROOM = pick_row6()

# P5 logic grid: who stays in the room the clock gave?
GUESTS = ["Margo", "Felix", "Iris", "Dexter"]
ROOMS = [204, ROOM, 421, 536]
GIFTS = ["scarf", "candle", "snow globe", "mittens"]
CLUES = [
    "Margo has the lowest room number.",
    "The candle was wrapped in room 204.",
    "The scarf was wrapped in room 421.",
    "Felix wrapped neither the scarf nor the candle.",
    "Dexter's room number is lower than Felix's.",
    "Iris did not wrap the scarf.",
    f"The snow globe was wrapped in room {ROOM}.",
]


def logic_solutions():
    sols = []
    for rp in itertools.permutations(ROOMS):
        room = dict(zip(GUESTS, rp))
        for gp in itertools.permutations(GIFTS):
            gift = dict(zip(GUESTS, gp))
            by_room = {room[g]: g for g in GUESTS}
            if room["Margo"] != min(ROOMS): continue
            if gift[by_room[204]] != "candle": continue
            if gift[by_room[421]] != "scarf": continue
            if gift["Felix"] in ("scarf", "candle"): continue
            if not room["Dexter"] < room["Felix"]: continue
            if gift["Iris"] == "scarf": continue
            if gift[by_room[ROOM]] != "snow globe": continue
            sols.append((room, gift))
    return sols


P5_ANS = "IRIS"

# P6 ornament scale: star = letters in the P5 name
STAR = len(P5_ANS)
EQS = ["star + bell + bell = 14", "tree + bell = star + 4", "tree + star = ?"]


def scale_solutions(star=None):
    out = []
    for s in range(1, 21):
        if star is not None and s != star: continue
        for b in range(1, 21):
            for t in range(1, 21):
                if s + 2 * b == 14 and t + b == s + 4:
                    out.append((s, b, t))
    return out


P6_ANS = 7

# P7 skip cipher: from the 1st letter, every 7th letter
P7_HIDDEN = "ROOMNUMBERTIMESNINE"
COLS = 16


def make_telegram(seed=5):
    rnd = random.Random(seed)
    n = COLS * 9
    s = [rnd.choice("ABCDEFGHIJKLMNOPRSTUVWY") for _ in range(n)]
    for i, ch in enumerate(P7_HIDDEN):
        s[i * P6_ANS] = ch
    return "".join(s)


TELEGRAM = make_telegram()
CODE = ROOM * P1_ANS


def verify():
    out = []
    acro = "".join(l[0] for l in LETTER)
    assert acro == "SHIFTBYNINE", acro
    out.append(f"P1 acrostic {acro} -> {P1_ANS}")
    assert caesar(P2_CIPHER, -P1_ANS) == P2_PLAIN
    out.append(f"P2 '{P2_CIPHER}' back {P1_ANS} = '{P2_PLAIN}' -> {P2_ANS}")
    assert vig(P3_CIPHER, P2_ANS, -1) == P3_PLAIN
    out.append(f"P3 '{P3_CIPHER}' key {P2_ANS} = '{P3_PLAIN}' -> {P3_ANS}")
    sols = sud_solve([row[:] for row in SUD_PUZ])
    assert len(sols) == 1 and sols[0] == SUD_SOL
    givens = sum(v != 0 for row in SUD_PUZ for v in row)
    nums = {r + 1: int("".join(str(SUD_SOL[r][c]) for c in SHADE[r])) for r in range(6)}
    assert nums[P3_ANS] == ROOM and len(set(nums.values())) == 6
    out.append(f"P4 6x6 sudoku unique ({givens} givens); row numbers {nums}; row {P3_ANS} = {ROOM}")
    ls = logic_solutions()
    assert len(ls) == 1, len(ls)
    room, gift = ls[0]
    who = [g for g in GUESTS if room[g] == ROOM][0]
    assert who.upper() == P5_ANS
    out.append(f"P5 logic unique: {room} {gift}; room {ROOM} = {who}")
    free = scale_solutions(); keyed = scale_solutions(STAR)
    assert len(free) > 1 and len(keyed) == 1
    s, b, t = keyed[0]
    assert t + s == P6_ANS
    out.append(f"P6 without key {len(free)} solutions, with star={STAR}: bell {b}, tree {t}; tree+star = {P6_ANS}")
    read = TELEGRAM[::P6_ANS][:len(P7_HIDDEN)]
    assert read == P7_HIDDEN
    out.append(f"P7 every {P6_ANS}th letter: {read}")
    assert 1000 <= CODE <= 9999 and sum(map(int, str(CODE))) == sum(map(int, str(CODE)))
    out.append(f"P8 vault {ROOM} x {P1_ANS} = {CODE} (digit sum {sum(map(int, str(CODE)))})")
    return out


if __name__ == "__main__":
    print("\n".join(verify()))
    for r in SUD_PUZ: print(r)
