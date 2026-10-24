"""Christmas escape room puzzles: content + checks. Run directly to verify every answer."""
import itertools, random
from collections import deque

CODE = [7, 3, 9, 4]          # vault code 7394

# ---- Clue 1 -------------------------------------------------------------
A1Z26_MSG = "SEVEN"
def a1z26(word): return [ord(ch) - 64 for ch in word]
A1_WARMUP = "ELF"
SHIFT = 3
def caesar(s, k):
    return "".join(chr((ord(ch) - 65 + k) % 26 + 65) if ch.isalpha() else ch for ch in s)
C1_PLAIN = "THE FIRST DIGIT IS SEVEN"
C1_SIGN_PLAIN = "JUNIPER"
C1_CIPHER = caesar(C1_PLAIN, SHIFT)
C1_SIGN = caesar(C1_SIGN_PLAIN, SHIFT)

# ---- Clue 2 -------------------------------------------------------------
L1_COUNTS = {"tree": 4, "gift": 5, "star": 6}   # trees + gifts - stars
SCENE_COLS, SCENE_ROWS = 6, 4
def l1_scene(seed=11):
    """Place shapes on a 6x4 shelf grid so none overlap (one shape per cell)."""
    rnd = random.Random(seed)
    cells = [(c, r) for r in range(SCENE_ROWS) for c in range(SCENE_COLS)]
    rnd.shuffle(cells)
    items = []
    for kind, n in L1_COUNTS.items():
        for _ in range(n): items.append((kind, cells.pop()))
    return items
# Level 2 symbol sums: tree=5, gift=4, star=2
L2_VALUES = {"tree": 5, "gift": 4, "star": 2}
L2_EQS = [(["tree", "tree", "tree"], "+", 15), (["tree", "gift", "gift"], "+", 13), (["gift", "star"], "x", 8)]
L2_ASK = ("tree", "+", "star", "-", "gift")

# ---- Clue 3 -------------------------------------------------------------
PLUGS = ["star", "tree", "gift", "bell"]
BULBS = [2, 9, 5, 6]                     # bulb digits left to right
STRANDS = {"star": 1, "tree": 3, "gift": 0, "bell": 2}   # plug -> bulb index
L1_START = "star"
MAZE_W, MAZE_H = 11, 13
def maze(seed=5):
    rnd = random.Random(seed)
    walls = {(x, y): {"N", "S", "E", "W"} for x in range(MAZE_W) for y in range(MAZE_H)}
    D = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
    OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}
    stack, seen = [(0, 0)], {(0, 0)}
    while stack:
        x, y = stack[-1]
        nb = [(d, (x + dx, y + dy)) for d, (dx, dy) in D.items() if (x + dx, y + dy) in walls and (x + dx, y + dy) not in seen]
        if not nb: stack.pop(); continue
        d, n = rnd.choice(nb)
        walls[(x, y)].discard(d); walls[n].discard(OPP[d]); seen.add(n); stack.append(n)
    return walls, D
def solve(walls, D, a=(0, 0), b=(MAZE_W - 1, MAZE_H - 1)):
    prev, q = {a: None}, deque([a])
    while q:
        cur = q.popleft()
        for d, (dx, dy) in D.items():
            n = (cur[0] + dx, cur[1] + dy)
            if d not in walls[cur] and n not in prev: prev[n] = cur; q.append(n)
    path, cur = [], b
    while cur: path.append(cur); cur = prev[cur]
    return path[::-1]
def bells(seed=5, on=9, off=9):
    walls, D = maze(seed); path = solve(walls, D)
    rnd = random.Random(seed + 1)
    inner = path[2:-2]
    on_cells = sorted(rnd.sample(inner, on), key=path.index)
    offs = [c for c in walls if c not in path]
    off_cells = rnd.sample(offs, off)
    return walls, D, path, on_cells, off_cells

# ---- Clue 4 -------------------------------------------------------------
SUDOKU_SOL = [[1, 2, 3, 4], [3, 4, 1, 2], [2, 1, 4, 3], [4, 3, 2, 1]]
SUDOKU_GIVEN = [[1, 0, 0, 0], [0, 0, 1, 2], [2, 0, 0, 3], [0, 3, 0, 1]]
SUDOKU_STAR = (2, 2)     # row, col (0-based): the snowflake square -> 4
def sudoku_solutions(g):
    sols = []
    for perm_rows in itertools.product(itertools.permutations([1, 2, 3, 4]), repeat=4):
        ok = all(g[r][c] in (0, perm_rows[r][c]) for r in range(4) for c in range(4))
        if not ok: continue
        if any(len({perm_rows[r][c] for r in range(4)}) < 4 for c in range(4)): continue
        boxes_ok = all(len({perm_rows[r][c] for r in (br, br + 1) for c in (bc, bc + 1)}) == 4 for br in (0, 2) for bc in (0, 2))
        if boxes_ok: sols.append([list(r) for r in perm_rows])
    return sols
ELVES = ["Juniper", "Pip", "Holly", "Sprout"]
TOYS = ["drum", "kite", "train", "yo-yo"]
LOGIC_CLUES = [
    "Pip works at bench 1, and Pip does not make yo-yos.",
    "Holly makes the drums.",
    "Holly works at the bench between Pip and Juniper.",
    "The kites and the yo-yos are both made at odd-numbered benches.",
    "Juniper works right next to the elf who builds the trains.",
]
def logic_solutions():
    sols = []
    for e in itertools.permutations(ELVES):          # e[i] = elf at bench i+1
        for t in itertools.permutations(TOYS):
            b = {e[i]: i + 1 for i in range(4)}; tb = {t[i]: i + 1 for i in range(4)}
            toy_of = {e[i]: t[i] for i in range(4)}
            if b["Pip"] != 1 or toy_of["Pip"] == "yo-yo": continue
            if toy_of["Holly"] != "drum": continue
            if not (min(b["Pip"], b["Juniper"]) < b["Holly"] < max(b["Pip"], b["Juniper"]) and abs(b["Holly"] - b["Pip"]) == 1 and abs(b["Holly"] - b["Juniper"]) == 1): continue
            if tb["kite"] % 2 == 0 or tb["yo-yo"] % 2 == 0: continue
            if abs(b["Juniper"] - tb["train"]) != 1: continue
            sols.append((e, t))
    return sols

def verify():
    out = []
    # 1
    assert "".join(chr(n + 64) for n in a1z26(A1Z26_MSG)) == "SEVEN"; out.append(f"C1 L1 {a1z26(A1Z26_MSG)} = SEVEN -> 7")
    assert caesar(C1_SIGN, -SHIFT) == "JUNIPER" and caesar(C1_CIPHER, -SHIFT) == C1_PLAIN
    out.append(f"C1 L2 '{C1_CIPHER}' signed '{C1_SIGN}' back 3 = '{C1_PLAIN}' -> 7")
    # 2
    items = l1_scene(); cnt = {k: sum(1 for i in items if i[0] == k) for k in L1_COUNTS}
    assert len({c for _, c in items}) == len(items)
    v1 = cnt["tree"] + cnt["gift"] - cnt["star"]; assert v1 == CODE[1]
    out.append(f"C2 L1 trees {cnt['tree']} + gifts {cnt['gift']} - stars {cnt['star']} = {v1}")
    V = L2_VALUES
    for syms, op, tot in L2_EQS:
        val = sum(V[s] for s in syms) if op == "+" else V[syms[0]] * V[syms[1]]
        assert val == tot, (syms, val, tot)
    # uniqueness of symbol values over 0..15
    sols = [(t, g, s) for t in range(16) for g in range(16) for s in range(16) if 3 * t == 15 and t + 2 * g == 13 and g * s == 8]
    assert sols == [(5, 4, 2)], sols
    v2 = V["tree"] + V["star"] - V["gift"]; assert v2 == CODE[1]
    out.append(f"C2 L2 tree 5, gift 4, star 2 unique; 5 + 2 - 4 = {v2}")
    # 3
    assert BULBS[STRANDS[L1_START]] == CODE[2] and sorted(STRANDS.values()) == [0, 1, 2, 3]
    out.append(f"C3 L1 star plug -> bulb {BULBS[STRANDS[L1_START]]}")
    walls, D, path, on, off = bells()
    assert len(on) == CODE[2] and all(c in path for c in on) and not any(c in path for c in off)
    # perfect maze: every cell reachable, unique path (edges = cells - 1)
    edges = sum(1 for c in walls for d in ("E", "S") if d not in walls[c])
    assert edges == MAZE_W * MAZE_H - 1
    out.append(f"C3 L2 maze {MAZE_W}x{MAZE_H} perfect (edges {edges}), path {len(path)} cells, bells on path {len(on)}, off path {len(off)} -> 9")
    # 4
    s = sudoku_solutions(SUDOKU_GIVEN); assert s == [SUDOKU_SOL], len(s)
    assert SUDOKU_SOL[SUDOKU_STAR[0]][SUDOKU_STAR[1]] == CODE[3]
    givens = sum(1 for r in SUDOKU_GIVEN for v in r if v)
    out.append(f"C4 L1 4x4 sudoku unique ({givens} givens), snowflake square = {CODE[3]}")
    ls = logic_solutions(); assert len(ls) == 1, ls
    e, t = ls[0]; train_bench = t.index("train") + 1; assert train_bench == CODE[3]
    out.append(f"C4 L2 logic grid unique: " + ", ".join(f"bench {i+1} {e[i]} {t[i]}" for i in range(4)) + f"; trains at bench {train_bench}")
    out.append("Vault code " + "".join(map(str, CODE)))
    return out, ls[0]

if __name__ == "__main__":
    lines, _ = verify(); print("\n".join(lines))
