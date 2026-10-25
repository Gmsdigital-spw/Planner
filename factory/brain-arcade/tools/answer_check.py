#!/usr/bin/env python3
"""Brain Arcade answer-key checker. A wrong answer is an automatic FAIL.

It solves every problem in a product spec ITSELF (its own math, not the builder's), then checks:
  1. exactly one printed choice is correct, and it is the choice the builder marked;
  2. the letter on that choice is the lock's code letter (the code words spell what the spec says);
  3. division problems divide evenly (no hidden remainders at grade level);
  4. the built PDF's answer key page prints every correct answer and code word (pdftotext).

Usage:
  python3 answer_check.py <spec.json> <build.json> [<product.pdf>]   -> exit 0 PASS, 1 FAIL
  python3 answer_check.py --selftest
"""
import ast, json, operator, subprocess, sys
from fractions import Fraction

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv}


def ev(expr):
    """Exact arithmetic on + - * / // with Fractions; nothing else is allowed."""
    def go(n):
        if isinstance(n, ast.Expression):
            return go(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, int):
            return Fraction(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            a, b = go(n.left), go(n.right)
            if isinstance(n.op, ast.Div):
                return a / b
            if isinstance(n.op, ast.FloorDiv):
                return Fraction(a.numerator * b.denominator // (a.denominator * b.numerator))
            return OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -go(n.operand)
        raise ValueError("not allowed in expr: " + ast.dump(n))
    return go(ast.parse(expr, mode="eval"))


def frac(s):
    s = s.strip()
    return Fraction(s) if "/" in s or s.lstrip("-").isdigit() else None


def clock(s):
    """'1:15 PM' / '5:05' -> minutes after midnight (12 h clock; AM/PM optional)."""
    s = s.strip().upper()
    ampm = None
    for tag in ("AM", "PM"):
        if s.endswith(tag):
            ampm, s = tag, s[:-2].strip()
    h, m = s.split(":")
    h, m = int(h), int(m)
    if not (1 <= h <= 12 and 0 <= m < 60):
        raise ValueError("bad clock " + s)
    h = h % 12 + (12 if ampm == "PM" else 0)
    return h * 60 + m, ampm


def same_clock(a, b):
    """Compare clock answers; if both carry AM/PM compare exactly, else on the 12-hour dial."""
    (ma, pa), (mb, pb) = clock(a), clock(b)
    if pa and pb:
        return ma == mb
    return ma % 720 == mb % 720


def correct_choices(p):
    """Return the list of choice indexes that are correct, by independent math."""
    k, ch = p["kind"], p["choices"]
    out = []
    for i, c in enumerate(ch):
        num = c.split()[0]
        if k == "arith":
            val = ev(p["expr"])
            if "exact" in p and ev(p["exact"]) != val:
                raise ValueError(f"'{p['text']}' does not divide evenly")
            ok = frac(num) == val
        elif k == "round":
            v, pl = p["value"], p["place"]
            r = ((v + pl // 2) // pl) * pl  # round half up, as taught in grade 3
            ok = frac(num) == r
        elif k == "time_add":
            m, _ = clock(p["start"])
            target = m + p["minutes"]
            cm, cap = clock(c)
            ok = (cm == target % 1440) if cap else (cm % 720 == target % 720)
        elif k == "time_sub":
            m, _ = clock(p["end"])
            ok = clock(c)[0] % 720 == (m - p["minutes"]) % 720
        elif k == "time_diff":
            a, b = clock(p["start"])[0], clock(p["end"])[0]
            ok = frac(num) == (b - a) % 720
        elif k == "frac":
            ok = frac(c) is not None and frac(c) == ev(p["expr"])
        elif k == "frac_equal":
            ok = frac(c) is not None and frac(c) == Fraction(p["target"])
        elif k == "frac_max":
            best = max(p["options"], key=Fraction)
            if len({Fraction(o) for o in p["options"]}) == 1:
                best = "They are equal"
            ok = c.strip() == best
        else:
            raise ValueError("unknown kind " + k)
        if ok:
            out.append(i)
    return out


def pdf_text(pdf):
    return subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout


def check_bingo(spec, build, pdf=None):
    """Bingo: every call's answer is right (own math), answers are all different, every card number is
    a real answer, 24 different numbers + free centre per card, no two cards alike, key page complete."""
    fails = []
    calls = build["calls"]
    if [[c["a"], c["b"]] for c in calls] != [list(f) for f in spec["facts"]]:
        fails.append("calling cards do not match the spec's facts")
    answers = []
    for c in calls:
        right = int(ev(f"{c['a']}*{c['b']}"))
        if c["product"] != right:
            fails.append(f"{c['a']} x {c['b']} printed as {c['product']}, the answer is {right}")
        answers.append(right)
    if len(set(answers)) != len(answers):
        fails.append("two calls have the same answer (a square could match two calls)")
    pool = set(answers)
    if len(build["cards"]) != spec["cards"]:
        fails.append(f"{len(build['cards'])} cards built, spec says {spec['cards']}")
    seen = set()
    for i, cells in enumerate(build["cards"], 1):
        nums = [x for x in cells if x != "FREE"]
        if len(cells) != 25 or cells[12] != "FREE":
            fails.append(f"card {i}: needs 25 squares with FREE in the centre")
        if len(nums) != 24 or len(set(nums)) != 24:
            fails.append(f"card {i}: needs 24 different numbers")
        bad = [x for x in nums if x not in pool]
        if bad:
            fails.append(f"card {i}: numbers {bad} are not answers to any call")
        k = frozenset(nums)
        if k in seen:
            fails.append(f"card {i}: same numbers as another card")
        seen.add(k)
    if pdf:
        txt = pdf_text(pdf)
        # spaces removed: pdftotext drops them unevenly in tight columns ("3×2=6" vs "3 × 7 = 21")
        key = "".join(txt[txt.find("ANSWER KEY"):].split()) if "ANSWER KEY" in txt else ""
        if not key:
            fails.append("PDF has no ANSWER KEY page")
        for c in calls:
            if f"{c['a']}×{c['b']}={c['product']}" not in key:
                fails.append(f"answer key page is missing {c['a']} × {c['b']} = {c['product']}")
        if txt.count(spec["free_label"]) < spec["cards"]:
            fails.append("not every card made it into the PDF")
    return fails


def check(spec, build, pdf=None):
    if spec.get("type") == "bingo":
        return check_bingo(spec, build, pdf)
    fails = []
    locks_b = build["locks"]
    if len(locks_b) != len(spec["locks"]):
        fails.append("build has a different number of locks than the spec")
    firsts = ""
    for li, (L, B) in enumerate(zip(spec["locks"], locks_b)):
        code = L["code"].upper()
        firsts += code[0]
        if len(code) != len(L["problems"]):
            fails.append(f"{L['name']}: code {code} needs {len(code)} problems, has {len(L['problems'])}")
        word = ""
        for pi, (p, pb) in enumerate(zip(L["problems"], B["problems"])):
            tag = f"{L['name']} #{pi + 1}"
            try:
                good = correct_choices(p)
            except Exception as e:  # a problem we cannot solve is a fail, never a skip
                fails.append(f"{tag}: cannot verify ({e})")
                continue
            if len(good) != 1:
                fails.append(f"{tag}: {len(good)} correct choices printed (must be exactly 1): {p['choices']}")
                continue
            letters = pb["letters"]
            if len(set(letters)) != len(letters):
                fails.append(f"{tag}: repeated choice letters {letters}")
            if pb["answer_index"] != good[0]:
                fails.append(f"{tag}: builder marked '{p['choices'][pb['answer_index']]}' but the answer is '{p['choices'][good[0]]}'")
            word += letters[good[0]]
        if word != code:
            fails.append(f"{L['name']}: correct letters spell {word}, code is {code}")
    if firsts != spec["final_word"].upper():
        fails.append(f"first letters spell {firsts}, final word is {spec['final_word']}")
    if pdf:
        try:
            txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
        except Exception as e:
            fails.append(f"PDF unreadable: {e}")
            txt = ""
        key = txt[txt.find("ANSWER KEY"):] if "ANSWER KEY" in txt else ""
        if not key:
            fails.append("PDF has no ANSWER KEY page")
        flat = " ".join(key.split())
        for L, B in zip(spec["locks"], locks_b):
            if L["code"].upper() not in flat:
                fails.append(f"answer key page is missing code {L['code']}")
            for p, pb in zip(L["problems"], B["problems"]):
                ans = p["choices"][pb["answer_index"]]
                if " ".join(ans.split()) not in flat:
                    fails.append(f"answer key page is missing answer '{ans}'")
        if spec["final_word"].upper() not in flat:
            fails.append("answer key page is missing the final word")
    return fails


def selftest():
    spec = {"final_word": "AB", "locks": [
        {"name": "L1", "code": "AX", "problems": [
            {"text": "6x7", "kind": "arith", "expr": "6*7", "choices": ["42", "48"]},
            {"text": "t", "kind": "time_add", "start": "11:50 AM", "minutes": 20, "choices": ["12:10 PM", "12:10 AM"]}]},
        {"name": "L2", "code": "BY", "problems": [
            {"text": "r", "kind": "round", "value": 45, "place": 10, "choices": ["40", "50"]},
            {"text": "f", "kind": "frac_max", "options": ["2/6", "2/3"], "choices": ["2/6", "2/3"]}]}]}
    good = {"locks": [{"problems": [{"answer_index": 0, "letters": ["A", "Q"]}, {"answer_index": 0, "letters": ["X", "Z"]}]},
                      {"problems": [{"answer_index": 1, "letters": ["Q", "B"]}, {"answer_index": 1, "letters": ["K", "Y"]}]}]}
    assert check(spec, good) == [], check(spec, good)
    bad = json.loads(json.dumps(good)); bad["locks"][0]["problems"][0]["answer_index"] = 1
    assert check(spec, bad), "wrong marked answer must fail"
    spec2 = json.loads(json.dumps(spec)); spec2["locks"][0]["problems"][0]["choices"] = ["42", "42"]
    assert check(spec2, good), "two correct choices must fail"
    spec3 = json.loads(json.dumps(spec)); spec3["locks"][0]["problems"][0].update(expr="43//6", exact="43/6", choices=["7", "8"])
    assert check(spec3, good), "uneven division must fail"
    bs = {"type": "bingo", "facts": [[i, 2] for i in range(2, 27)], "cards": 2, "free_label": "FREE"}
    calls = [{"a": i, "b": 2, "product": i * 2} for i in range(2, 27)]
    c1 = [i * 2 for i in range(2, 14)] + ["FREE"] + [i * 2 for i in range(14, 26)]
    c2 = [i * 2 for i in range(3, 15)] + ["FREE"] + [i * 2 for i in range(15, 27)]
    gb = {"calls": calls, "cards": [c1, c2]}
    assert check(bs, gb) == [], check(bs, gb)
    assert check(bs, dict(gb, cards=[c1, c1])), "duplicate cards must fail"
    wrong = [dict(c) for c in calls]; wrong[0]["product"] = 5
    assert check(bs, dict(gb, calls=wrong)), "a wrong product must fail"
    print("selftest PASS")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest(); sys.exit(0)
    spec = json.load(open(sys.argv[1])); build = json.load(open(sys.argv[2]))
    f = check(spec, build, sys.argv[3] if len(sys.argv) > 3 else None)
    n = len(spec["facts"]) * (spec["cards"] + 1) if spec.get("type") == "bingo" else sum(len(L["problems"]) for L in spec["locks"])
    if f:
        print(f"ANSWER KEY FAIL ({len(f)} problem(s)):"); [print(" -", x) for x in f]; sys.exit(1)
    print(f"ANSWER KEY PASS: {n} problems solved independently, every key and code word correct")
