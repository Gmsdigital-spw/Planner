"""Single-solution check for The Stolen Star of Hollyridge Lodge.
Each clue card is written as a predicate on the culprit, from facts printed on the cards.
Pass = exactly one suspect fits every clue, every other suspect is ruled out by at least
one clue, the culprit fits all clues (no clue contradicts another), and the solution is
still unique if any single clue card is lost (two independent routes)."""
import itertools, json, sys

SUSPECTS = ["Ivy", "Jasper", "Clem", "Rupert", "Noelle", "Dash", "Marigold", "Felix"]
# Facts as printed on the clue cards and character sheets.
VERIFIED_AT_714 = {          # card id -> who that card places away from the drawing room at 7:14
    "C4": {"Ivy"},            # phone bill: office landline 7:05-7:25
    "C5": {"Jasper", "Dash"}, # garage camera still 7:14
    "C6": {"Noelle", "Felix"},# voice memo 7:09-7:19 in the library
    "C7": {"Marigold"},       # Room 4 lock log in 7:02, out 7:31
}
TWO_HANDS_OK = {s: s != "Rupert" for s in SUSPECTS}          # C8: Rupert's right hand in a splint
FOOTWEAR = {"Ivy": "velvet heels", "Jasper": "ski boots", "Clem": "kitchen clogs", "Rupert": "loafers",
            "Noelle": "snow boots", "Dash": "work boots", "Marigold": "heeled boots", "Felix": "sneakers"}  # C9
CLAIMS = {"Clem": ("oven", "7:15")}   # Clem's spoken alibi: pulling buns from the oven at 7:15
POWER_OUT = (7 * 60 + 8, 7 * 60 + 20)  # C3: generator log, whole lodge dark 7:08-7:20

def t(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)

CLUES = {
    "C1 clock stopped 7:14 (thief in drawing room then)": lambda s: True,  # sets the time used by C4-C7
    "C2 bench print: flat clog sole": lambda s: FOOTWEAR[s] == "kitchen clogs",
    "C3 power out 7:08-7:20: no oven ran": lambda s: True,                 # breaks Clem's claim, see below
    "C4 phone bill": lambda s: s not in VERIFIED_AT_714["C4"],
    "C5 garage camera": lambda s: s not in VERIFIED_AT_714["C5"],
    "C6 voice memo": lambda s: s not in VERIFIED_AT_714["C6"],
    "C7 room lock log": lambda s: s not in VERIFIED_AT_714["C7"],
    "C8 two hands to twist star off": lambda s: TWO_HANDS_OK[s],
    "C9 group photo footwear": lambda s: True,                               # data for C2
}

def solve(clues):
    return [s for s in SUSPECTS if all(f(s) for f in clues.values())]

problems = []
sol = solve(CLUES)
if sol != ["Clem"]: problems.append(f"expected only Clem, got {sol}")
# every other suspect ruled out by at least one clue
for s in SUSPECTS:
    if s == "Clem": continue
    out = [k for k, f in CLUES.items() if not f(s)]
    if not out: problems.append(f"{s} not ruled out")
# no contradictions: verified alibi sets do not overlap, and the culprit is not verified elsewhere
seen = set()
for k, v in VERIFIED_AT_714.items():
    if seen & v: problems.append(f"{k} places someone in two places")
    seen |= v
if "Clem" in seen: problems.append("culprit has a verified alibi")
# the culprit's spoken alibi must be broken by a card fact (the lie the players can catch)
place, when = CLAIMS["Clem"]
lie_caught = place == "oven" and POWER_OUT[0] <= t(when) <= POWER_OUT[1]
if not lie_caught: problems.append("Clem's oven alibi is not contradicted")
# the clock time sits inside the outage (lights out is when the star could be taken unseen)
if not (POWER_OUT[0] <= t("7:14") <= POWER_OUT[1]): problems.append("clock time outside outage")
# robustness: still unique with any one card missing, via a second route
robust = {}
for k in CLUES:
    rest = {kk: f for kk, f in CLUES.items() if kk != k}
    r = solve(rest)
    if k.startswith("C2") or k.startswith("C9"):
        # without the footwear route the alibi + splint route must still leave only Clem
        pass
    robust[k] = r
route_a = [s for s in SUSPECTS if all(CLUES[k](s) for k in CLUES if k[:2] in ("C4", "C5", "C6", "C7", "C8")) ]
route_b = [s for s in SUSPECTS if CLUES["C2 bench print: flat clog sole"](s)]
if route_a != ["Clem"]: problems.append(f"alibi+splint route gives {route_a}")
if route_b != ["Clem"]: problems.append(f"footwear route gives {route_b}")
res = {"solution": sol, "ruled_out_by": {s: [k.split()[0] for k, f in CLUES.items() if not f(s)] for s in SUSPECTS if s != "Clem"},
       "route_alibis_splint": route_a, "route_footwear": route_b, "lie_caught": lie_caught,
       "drop_one_card": {k.split()[0]: v for k, v in robust.items()}, "problems": problems}
print(json.dumps(res, indent=1))
sys.exit(1 if problems else 0)
