"""Thanksgiving escape room puzzles (The Pie Safe): content + checks. Run directly to verify every answer."""
import itertools, random
from collections import deque

CODE = [5, 2, 8, 3]          # pie safe code 5283

# ---- Clue 1 -------------------------------------------------------------
A1Z26_MSG = "FIVE"
def a1z26(word): return [ord(ch) - 64 for ch in word]
A1_WARMUP = "PIE"
SHIFT = 4
def caesar(s, k):
    return "".join(chr((ord(ch) - 65 + k) % 26 + 65) if ch.isalpha() else ch for ch in s)
C1_PLAIN = "THE FIRST DIGIT IS FIVE"
C1_SIGN_PLAIN = "HAZEL"
C1_CIPHER = caesar(C1_PLAIN, SHIFT)
C1_SIGN = caesar(C1_SIGN_PLAIN, SHIFT)

# ---- Clue 2 -------------------------------------------------------------
L1_COUNTS = {"pumpkin": 6, "apple": 4, "acorn": 8}   # pumpkins + apples - acorns
SCENE_COLS, SCENE_ROWS = 6, 4
def l1_scene(seed=23):
    """Place pictures on a 6x4 pantry shelf grid, one per cell, so none overlap."""
    rnd = random.Random(seed)
    cells = [(c, r) for r in range(SCENE_ROWS) for c in range(SCENE_COLS)]
    rnd.shuffle(cells)
    items = []
    for kind, n in L1_COUNTS.items():
        for _ in range(n): items.append((kind, cells.pop()))
    return items
# Level 2 picture sums: pumpkin=3, apple=5, acorn=4
L2_VALUES = {"pumpkin": 3, "apple": 5, "acorn": 4}
L2_EQS = [(["pumpkin", "pumpkin", "pumpkin"], "+", 9), (["pumpkin", "apple", "apple"], "+", 13), (["apple", "acorn"], "x", 20)]
L2_ASK = (["pumpkin", "acorn", "apple"], ["+", "-"])   # pumpkin + acorn - apple

# ---- Clue 3 -------------------------------------------------------------
PLUGS = ["pumpkin", "apple", "acorn", "leaf"]          # vine starts, left to right
PIES = [4, 8, 1, 6]                                    # pie numbers left to right
VINES = {"pumpkin": 1, "apple": 3, "acorn": 0, "leaf": 2}   # start -> pie index
# waypoint columns per row: each row is a permutation of 0..3, so vines never share a point
VINE_ROWS = {"pumpkin": [2, 3, 0], "apple": [0, 1, 2], "acorn": [3, 0, 1], "leaf": [1, 2, 3]}
L1_START = "pumpkin"
MAZE_W, MAZE_H = 11, 13
def maze(seed=17):
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
def acorns(seed=17, on=8, off=9):
    walls, D = maze(seed); path = solve(walls, D)
    rnd = random.Random(seed + 1)
    inner = path[2:-2]
    on_cells = sorted(rnd.sample(inner, on), key=path.index)
    offs = [c for c in walls if c not in path]
    off_cells = rnd.sample(offs, off)
    return walls, D, path, on_cells, off_cells

# ---- Clue 4 -------------------------------------------------------------
SUDOKU_SOL = [[2, 4, 1, 3], [1, 3, 2, 4], [4, 1, 3, 2], [3, 2, 4, 1]]
SUDOKU_GIVEN = [[2, 4, 0, 0], [1, 0, 2, 0], [4, 0, 0, 0], [0, 2, 0, 1]]
SUDOKU_MARK = (2, 2)     # row, col (0-based): the leaf square -> 3
def sudoku_solutions(g):
    sols = []
    for P in itertools.product(itertools.permutations([1, 2, 3, 4]), repeat=4):
        if any(g[r][c] not in (0, P[r][c]) for r in range(4) for c in range(4)): continue
        if any(len({P[r][c] for r in range(4)}) < 4 for c in range(4)): continue
        if all(len({P[r][c] for r in (br, br + 1) for c in (bc, bc + 1)}) == 4 for br in (0, 2) for bc in (0, 2)):
            sols.append([list(r) for r in P])
    return sols
COUSINS = ["Ada", "Milo", "Rosa", "Theo"]
DISHES = ["corn", "cranberry sauce", "pie", "rolls"]
LOGIC_CLUES = [
    "Theo sits in chair 1, and Theo did not bring the rolls.",
    "Rosa brought the cranberry sauce.",
    "Ada sits right between Theo and Milo.",
    "The corn sits right next to the rolls.",
    "Whoever brought the pie sits right next to Rosa.",
]
def logic_solutions():
    sols = []
    for e in itertools.permutations(COUSINS):          # e[i] = cousin in chair i+1
        for t in itertools.permutations(DISHES):
            ch = {e[i]: i + 1 for i in range(4)}; tc = {t[i]: i + 1 for i in range(4)}
            dish = {e[i]: t[i] for i in range(4)}
            if ch["Theo"] != 1 or dish["Theo"] == "rolls": continue
            if dish["Rosa"] != "cranberry sauce": continue
            if not (min(ch["Theo"], ch["Milo"]) < ch["Ada"] < max(ch["Theo"], ch["Milo"]) and abs(ch["Ada"] - ch["Theo"]) == 1 and abs(ch["Ada"] - ch["Milo"]) == 1): continue
            if abs(tc["corn"] - tc["rolls"]) != 1: continue
            if abs(tc["pie"] - ch["Rosa"]) != 1: continue
            sols.append((e, t))
    return sols

def verify():
    out = []
    assert "".join(chr(n + 64) for n in a1z26(A1Z26_MSG)) == "FIVE" and CODE[0] == 5
    out.append(f"C1 L1 warm-up {a1z26(A1_WARMUP)} = PIE; {a1z26(A1Z26_MSG)} = FIVE -> 5")
    assert caesar(C1_SIGN, -SHIFT) == C1_SIGN_PLAIN and caesar(C1_CIPHER, -SHIFT) == C1_PLAIN
    out.append(f"C1 L2 '{C1_CIPHER}' signed '{C1_SIGN}' back {SHIFT} = '{C1_PLAIN}' -> 5")
    items = l1_scene(); cnt = {k: sum(1 for i in items if i[0] == k) for k in L1_COUNTS}
    assert len({c for _, c in items}) == len(items)
    v1 = cnt["pumpkin"] + cnt["apple"] - cnt["acorn"]; assert v1 == CODE[1]
    out.append(f"C2 L1 pumpkins {cnt['pumpkin']} + apples {cnt['apple']} - acorns {cnt['acorn']} = {v1}")
    V = L2_VALUES
    for syms, op, tot in L2_EQS:
        val = sum(V[s] for s in syms) if op == "+" else V[syms[0]] * V[syms[1]]
        assert val == tot, (syms, val, tot)
    sols = [(p, a, c) for p in range(21) for a in range(21) for c in range(21) if 3 * p == 9 and p + 2 * a == 13 and a * c == 20]
    assert sols == [(3, 5, 4)], sols
    v2 = V["pumpkin"] + V["acorn"] - V["apple"]; assert v2 == CODE[1]
    out.append(f"C2 L2 pumpkin 3, apple 5, acorn 4 unique; 3 + 4 - 5 = {v2}")
    for k in range(3): assert sorted(v[k] for v in VINE_ROWS.values()) == [0, 1, 2, 3]
    assert PIES[VINES[L1_START]] == CODE[2] and sorted(VINES.values()) == [0, 1, 2, 3]
    out.append(f"C3 L1 pumpkin vine -> pie {PIES[VINES[L1_START]]}")
    walls, D, path, on, off = acorns()
    assert len(on) == CODE[2] and all(c in path for c in on) and not any(c in path for c in off)
    edges = sum(1 for c in walls for d in ("E", "S") if d not in walls[c])
    assert edges == MAZE_W * MAZE_H - 1
    out.append(f"C3 L2 maze {MAZE_W}x{MAZE_H} perfect (edges {edges}), path {len(path)} cells, acorns on path {len(on)}, off path {len(off)} -> {CODE[2]}")
    s = sudoku_solutions(SUDOKU_GIVEN); assert s == [SUDOKU_SOL], len(s)
    assert SUDOKU_SOL[SUDOKU_MARK[0]][SUDOKU_MARK[1]] == CODE[3] and SUDOKU_GIVEN[SUDOKU_MARK[0]][SUDOKU_MARK[1]] == 0
    givens = sum(1 for r in SUDOKU_GIVEN for v in r if v)
    out.append(f"C4 L1 4x4 sudoku unique ({givens} givens), leaf square = {CODE[3]}")
    ls = logic_solutions(); assert len(ls) == 1, ls
    e, t = ls[0]; pie_chair = t.index("pie") + 1; assert pie_chair == CODE[3]
    out.append("C4 L2 logic grid unique: " + ", ".join(f"chair {i+1} {e[i]} {t[i]}" for i in range(4)) + f"; pie at chair {pie_chair}")
    out.append("Pie Safe code " + "".join(map(str, CODE)))
    return out, ls[0]

if __name__ == "__main__":
    lines, _ = verify(); print("\n".join(lines))
