#!/usr/bin/env python3
"""Brain Arcade game builder: spec.json -> printable PDF + build.json (choice letters, answers).

Usage: python3 games.py <spec.json> <out_dir>
Writes <out_dir>/<id>.pdf and <out_dir>/build.json, then runs answer_check.py on them.
Exit 1 if the answer key fails: a wrong answer is never shipped.

Types built today: escape_room. Add a new type as a new build_<type>() and keep the rule:
answers come from the spec's math, and answer_check.py must PASS before anything else happens.
"""
import json, os, random, subprocess, sys
from fractions import Fraction
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, "../../../tools/fonts"))
for name, f in [("Head", "BricolageGrotesque-Bold.ttf"), ("Body", "Outfit-Regular.ttf"),
                ("BodyB", "Outfit-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, f)))

W, H = letter
M = 42
SHOP = "Brain Arcade Games"
LICENSE = "Personal and single-classroom use only. Please do not share, resell or post these files online."


def solve_index(p):
    """Builder's own solver (answer_check.py re-solves independently)."""
    k, ch = p["kind"], p["choices"]
    def mins(s):
        s = s.upper().replace("AM", "").replace("PM", "").strip(); h, m = s.split(":")
        return (int(h) % 12) * 60 + int(m)
    for i, c in enumerate(ch):
        n = c.split()[0]
        if k == "arith" and n.lstrip("-").isdigit() and int(n) == eval(p["expr"], {"__builtins__": {}}):
            return i
        if k == "round" and n.isdigit() and int(n) == int(round(p["value"] / p["place"] + 1e-9) * p["place"]):
            return i
        if k == "time_add" and mins(c) % 720 == (mins(p["start"]) + p["minutes"]) % 720:
            return i
        if k == "time_sub" and mins(c) % 720 == (mins(p["end"]) - p["minutes"]) % 720:
            return i
        if k == "time_diff" and n.isdigit() and int(n) == (mins(p["end"]) - mins(p["start"])) % 720:
            return i
        if k == "frac" and "/" in c and Fraction(c) == Fraction(1) - Fraction(p["expr"].split("-")[1]):
            return i
        if k == "frac_equal" and ("/" in c or c.isdigit()) and Fraction(c) == Fraction(p["target"]):
            return i
        if k == "frac_max" and c == max(p["options"], key=Fraction):
            return i
    raise ValueError("no correct choice for: " + p["text"])


def assign_letters(spec):
    pool = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    out = {"id": spec["id"], "locks": []}
    for li, L in enumerate(spec["locks"]):
        lb = {"problems": []}
        for pi, p in enumerate(L["problems"]):
            rng = random.Random(f"{spec['id']}-{li}-{pi}")
            right = L["code"][pi].upper()
            others = [c for c in pool if c != right and c not in L["code"].upper()]
            rng.shuffle(others)
            ai = solve_index(p)
            letters = [right if i == ai else others.pop() for i in range(len(p["choices"]))]
            lb["problems"].append({"answer_index": ai, "letters": letters})
        out["locks"].append(lb)
    return out


class Book:
    def __init__(self, path, spec):
        self.c = canvas.Canvas(path, pagesize=letter)
        self.c.setTitle(f"{spec['title']} - {spec['subtitle']}")
        self.c.setAuthor(SHOP)
        self.s = spec
        self.P = {k: HexColor(v) for k, v in spec["palette"].items()}
        self.n = 0

    def page(self, band=None):
        c, P = self.c, self.P
        if self.n:
            c.showPage()
        self.n += 1
        c.setFillColor(P["bg"]); c.rect(0, 0, W, H, 0, 1)
        # harvest border: two rules in the theme colours
        c.setStrokeColor(P["primary"]); c.setLineWidth(5); c.roundRect(18, 18, W - 36, H - 36, 14)
        c.setStrokeColor(P["accent"]); c.setLineWidth(1.5); c.roundRect(26, 26, W - 52, H - 52, 10)
        c.setFont("Body", 8); c.setFillColor(P["deep"])
        c.drawCentredString(W / 2, 32, f"{SHOP}  ·  {self.s['subtitle']}  ·  {self.s['grade']}  ·  page {self.n}")
        if band:
            c.setFillColor(P["primary"]); c.roundRect(M, H - 110, W - 2 * M, 66, 12, 0, 1)
            c.setFillColor(white); c.setFont("Head", 25); c.drawString(M + 18, H - 78, band[0])
            if len(band) > 1:
                c.setFont("Body", 11.5); c.drawString(M + 18, H - 98, band[1])
        return H - 130

    def wrap(self, text, font, size, width):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if pdfmetrics.stringWidth(t, font, size) <= width:
                cur = t
            else:
                lines.append(cur); cur = w
        return lines + ([cur] if cur else [])

    def para(self, x, y, text, font="Body", size=12, width=None, lead=None, color=None):
        c = self.c; width = width or W - 2 * M - (x - M); lead = lead or size * 1.35
        c.setFont(font, size); c.setFillColor(color or self.P["ink"])
        for line in self.wrap(text, font, size, width):
            c.drawString(x, y, line); y -= lead
        return y

    def padlock(self, x, y, s, col, letter_=None):
        c = self.c
        c.setStrokeColor(col); c.setLineWidth(s * 0.12); c.setFillColor(col)
        c.arc(x + s * 0.18, y + s * 0.55, x + s * 0.82, y + s * 1.2, 0, 180)
        c.line(x + s * 0.18, y + s * 0.87, x + s * 0.18, y + s * 0.6)
        c.line(x + s * 0.82, y + s * 0.87, x + s * 0.82, y + s * 0.6)
        c.roundRect(x, y, s, s * 0.66, s * 0.1, 0, 1)
        if letter_:
            c.setFillColor(white); c.setFont("Head", s * 0.42); c.drawCentredString(x + s / 2, y + s * 0.18, letter_)

    def boxes(self, x, y, n, size=34, fill=None, text=None):
        c = self.c
        for i in range(n):
            c.setStrokeColor(self.P["deep"]); c.setLineWidth(2); c.setFillColor(white)
            c.roundRect(x + i * (size + 8), y, size, size, 6, 1, 1)
            if text:
                c.setFillColor(self.P["berry"]); c.setFont("Head", size * 0.6)
                c.drawCentredString(x + i * (size + 8) + size / 2, y + size * 0.27, text[i])
        return x + n * (size + 8)


def build_escape_room(spec, out_dir):
    b = assign_letters(spec)
    pdf = os.path.join(out_dir, spec["id"] + ".pdf")
    d = Book(pdf, spec); c, P = d.c, d.P
    locks = spec["locks"]
    nprob = sum(len(L["problems"]) for L in locks)

    # 1 cover
    d.page()
    c.setFillColor(P["primary"]); c.roundRect(M, H - 330, W - 2 * M, 270, 18, 0, 1)
    c.setFillColor(P["accent"]); c.setFont("BodyB", 14)
    c.drawCentredString(W / 2, H - 100, spec["subtitle"].upper())
    c.setFillColor(white); c.setFont("Head", 50); c.drawCentredString(W / 2, H - 170, spec["title"])
    c.setFont("Body", 16)
    c.drawCentredString(W / 2, H - 205, f"{spec['grade']} Math  ·  {len(locks)} locks  ·  {nprob} problems  ·  answer key")
    for i, L in enumerate(locks):
        d.padlock(W / 2 - 2.5 * 74 + i * 74 + 12, H - 300, 50, [P["berry"], P["green"], P["accent"], P["deep"], P["berry"]][i], str(i + 1))
    y = H - 380
    c.setFillColor(P["deep"]); c.setFont("Head", 20); c.drawString(M + 10, y, "Inside this game")
    y -= 28
    for L in locks:
        c.setFillColor(P["primary"]); c.circle(M + 18, y + 4, 4, 0, 1)
        c.setFillColor(P["ink"]); c.setFont("BodyB", 14); c.drawString(M + 30, y, L["name"])
        c.setFont("Body", 12); c.setFillColor(P["deep"]); c.drawString(M + 30, y - 16, f"{L['skill']}  ·  {L['standard']}")
        y -= 42
    for extra in ["Teacher guide, story page and student recording sheet", "Final vault page and Escape Expert certificate",
                  "Full answer key with every code word"]:
        c.setFillColor(P["green"]); c.circle(M + 18, y + 4, 4, 0, 1)
        c.setFillColor(P["ink"]); c.setFont("BodyB", 13.5); c.drawString(M + 30, y, extra); y -= 26
    c.setFillColor(P["deep"]); c.setFont("Body", 10.5); c.drawCentredString(W / 2, 58, LICENSE)

    # 2 teacher guide
    y = d.page(("Teacher Guide", "No cutting, no prep: about 45 to 60 minutes"))
    steps = [
        ("Print", f"One copy per student or pair: the story page, the {len(locks)} lock pages and the recording sheet. Keep the answer key for yourself."),
        ("Launch", "Read the story page out loud. Students work alone, in pairs or in teams of 3 to 4."),
        ("Solve", "On each lock page, students solve every problem, circle the answer, and write the letter next to it in the code boxes."),
        ("Check", "When a team shows you a code word, check it against the key. Right code = the next lock. Wrong code = check each problem again."),
        ("Escape", "After lock 5, the first letter of each code word spells the word that opens the vault."),
        ("Celebrate", "Hand out the Escape Expert certificate to every team that opens the vault."),
    ]
    for i, (h, t) in enumerate(steps):
        c.setFillColor(P["primary"]); c.circle(M + 26, y - 4, 15, 0, 1)
        c.setFillColor(white); c.setFont("Head", 15); c.drawCentredString(M + 26, y - 9, str(i + 1))
        c.setFillColor(P["deep"]); c.setFont("Head", 15); c.drawString(M + 52, y - 2, h)
        y = d.para(M + 52, y - 20, t, size=12, width=W - 2 * M - 70) - 14
    c.setFillColor(P["deep"]); c.setFont("Head", 16); c.drawString(M + 10, y - 6, "Skills and standards")
    y -= 32
    for L in locks:
        c.setFillColor(white); c.setStrokeColor(P["accent"]); c.setLineWidth(1)
        c.roundRect(M + 10, y - 8, W - 2 * M - 20, 24, 6, 1, 1)
        c.setFillColor(P["ink"]); c.setFont("BodyB", 11); c.drawString(M + 20, y, L["name"])
        c.setFont("Body", 10); c.drawString(M + 190, y, L["skill"]); c.drawRightString(W - M - 20, y, L["standard"])
        y -= 30
    y = d.para(M + 10, y - 6, "Make it easier: let pairs use a multiplication chart for lock 1 and a clock for lock 4. "
               "Make it harder: set a 40-minute timer and ask teams to show their work for every problem.", size=11.5, color=P["deep"])

    # 3 story
    d.page(("The Great Pie Vault", "Read this first"))
    c.setFillColor(white); c.setStrokeColor(P["primary"]); c.setLineWidth(3)
    c.roundRect(M + 20, 230, W - 2 * M - 40, H - 400, 18, 1, 1)
    y = H - 210
    for line in spec["story"]:
        y = d.para(M + 50, y, line, size=17, width=W - 2 * M - 100, lead=25) - 16
    for i, L in enumerate(locks):
        d.padlock(M + 70 + i * 92, 255, 56, [P["berry"], P["green"], P["accent"], P["deep"], P["primary"]][i])
    c.setFillColor(P["deep"]); c.setFont("Head", 22); c.drawCentredString(W / 2, 170, "Can your team open the vault before dinner?")
    c.setFont("Body", 13); c.drawCentredString(W / 2, 140, "Team name: ______________________________")

    # 4.. lock pages
    for li, (L, B) in enumerate(zip(locks, b["locks"])):
        y = d.page((L["name"], f"{L['skill']}  ·  {L['standard']}"))
        n = len(L["problems"])
        avail = y - 175
        bh = min(118, avail / n - 10)
        for pi, (p, pb) in enumerate(zip(L["problems"], B["problems"])):
            top = y - pi * (bh + 10)
            c.setFillColor(white); c.setStrokeColor(P["accent"]); c.setLineWidth(1.5)
            c.roundRect(M + 6, top - bh, W - 2 * M - 12, bh, 12, 1, 1)
            c.setFillColor(P["berry"]); c.circle(M + 30, top - 24, 14, 0, 1)
            c.setFillColor(white); c.setFont("Head", 15); c.drawCentredString(M + 30, top - 29, str(pi + 1))
            ty = d.para(M + 54, top - 22, p["text"], font="BodyB", size=13.5, width=W - 2 * M - 80, lead=17)
            cw = (W - 2 * M - 70) / len(p["choices"])
            cy = min(ty - 12, top - bh + 16)
            cy = max(cy, top - bh + 12)
            for ci, (ch, lt) in enumerate(zip(p["choices"], pb["letters"])):
                x = M + 50 + ci * cw
                c.setFillColor(P["bg"]); c.setStrokeColor(P["primary"]); c.setLineWidth(1.2)
                c.roundRect(x, cy - 6, cw - 12, 28, 8, 1, 1)
                c.setFillColor(P["primary"]); c.roundRect(x, cy - 6, 26, 28, 8, 0, 1)
                c.setFillColor(white); c.setFont("Head", 14); c.drawCentredString(x + 13, cy + 2, lt)
                c.setFillColor(P["ink"]); fs = 12.5 if len(ch) < 14 else 10.5
                while pdfmetrics.stringWidth(ch, "BodyB", fs) > cw - 12 - 32 and fs > 8:
                    fs -= 0.5
                c.setFont("BodyB", fs); c.drawCentredString(x + 26 + (cw - 12 - 26) / 2, cy + 3, ch)
        # code boxes
        c.setFillColor(P["deep"]); c.setFont("Head", 16)
        c.drawString(M + 10, 112, "Write the letter of each answer, in order:")
        d.padlock(M + 12, 52, 44, P["berry"])
        d.boxes(M + 80, 58, n, size=38)
        c.setFont("Body", 11); c.setFillColor(P["deep"])
        c.drawRightString(W - M - 14, 72, "Show your code to your teacher.")

    # recording sheet
    y = d.page(("Student Recording Sheet", "Write each code word as you open each lock"))
    c.setFont("Body", 13); c.setFillColor(P["ink"]); c.drawString(M + 10, y, "Name or team: ____________________________________")
    y -= 40
    for li, L in enumerate(locks):
        c.setFillColor(white); c.setStrokeColor(P["primary"]); c.setLineWidth(1.5)
        c.roundRect(M + 6, y - 74, W - 2 * M - 12, 84, 12, 1, 1)
        d.padlock(M + 22, y - 58, 44, [P["berry"], P["green"], P["accent"], P["deep"], P["primary"]][li])
        c.setFillColor(P["deep"]); c.setFont("Head", 15); c.drawString(M + 80, y - 18, L["name"])
        d.boxes(M + 80, y - 64, len(L["code"]), size=34)
        c.setFont("Body", 11); c.setFillColor(P["ink"]); c.drawString(M + 330, y - 50, "Teacher check:  ______")
        y -= 98
    c.setFillColor(P["deep"]); c.setFont("Head", 15); c.drawString(M + 10, y - 10, "Scratch space")
    c.setStrokeColor(P["accent"]); c.setLineWidth(1); c.setDash(3, 4)
    c.roundRect(M + 6, 60, W - 2 * M - 12, y - 80, 10, 1, 0); c.setDash()

    # final vault
    d.page(("The Vault Door", "The last lock"))
    c.setFillColor(P["deep"]); c.circle(W / 2, H / 2 + 60, 170, 0, 1)
    c.setFillColor(P["primary"]); c.circle(W / 2, H / 2 + 60, 150, 0, 1)
    c.setFillColor(P["bg"]); c.circle(W / 2, H / 2 + 60, 120, 0, 1)
    c.setFillColor(P["deep"]); c.setFont("Head", 15); c.drawCentredString(W / 2, H / 2 + 120, "Write the FIRST letter")
    c.drawCentredString(W / 2, H / 2 + 100, "of each code word:")
    n = len(spec["final_word"])
    d.boxes(W / 2 - (n * 46 - 8) / 2, H / 2 + 20, n, size=38)
    c.setFont("Body", 13); c.drawCentredString(W / 2, H / 2 - 20, "Say the word to your teacher")
    c.drawCentredString(W / 2, H / 2 - 38, "to open the vault!")
    y = d.para(M + 30, 210, "When the vault opens, every pie is saved and the Harvest Feast can begin. "
               "Great math, team!", font="BodyB", size=16, width=W - 2 * M - 60, lead=22)

    # answer key
    y = d.page(("ANSWER KEY", "For the teacher. Every answer checked by the Brain Arcade answer checker."))
    for L, B in zip(locks, b["locks"]):
        c.setFillColor(P["deep"]); c.setFont("Head", 14); c.drawString(M + 10, y, L["name"])
        c.setFillColor(P["berry"]); c.drawRightString(W - M - 10, y, "Code: " + L["code"])
        y -= 18
        for pi, (p, pb) in enumerate(zip(L["problems"], B["problems"])):
            a = p["choices"][pb["answer_index"]]
            c.setFillColor(P["ink"]); c.setFont("Body", 11)
            short = p["text"] if len(p["text"]) < 70 else p["text"][:67].rsplit(" ", 1)[0] + "..."
            c.drawString(M + 20, y, f"{pi + 1}.  {short}")
            c.setFont("BodyB", 11); c.drawRightString(W - M - 40, y, a)
            c.setFillColor(P["primary"]); c.drawRightString(W - M - 12, y, pb["letters"][pb["answer_index"]])
            y -= 15
        y -= 10
    c.setFillColor(P["primary"]); c.roundRect(M + 6, y - 32, W - 2 * M - 12, 40, 10, 0, 1)
    c.setFillColor(white); c.setFont("Head", 17)
    c.drawCentredString(W / 2, y - 19, "Vault word: " + spec["final_word"])

    # certificate
    d.page()
    c.setFillColor(P["primary"]); c.roundRect(M + 10, H - 300, W - 2 * M - 20, 220, 18, 0, 1)
    c.setFillColor(P["accent"]); c.setFont("BodyB", 15); c.drawCentredString(W / 2, H - 130, "CERTIFICATE OF ESCAPE")
    c.setFillColor(white); c.setFont("Head", 40); c.drawCentredString(W / 2, H - 190, "Pie Vault")
    c.drawCentredString(W / 2, H - 236, "Escape Expert")
    c.setFillColor(P["ink"]); c.setFont("Body", 16); c.drawCentredString(W / 2, H - 370, "This certifies that")
    c.setStrokeColor(P["deep"]); c.setLineWidth(1.5); c.line(M + 90, H - 420, W - M - 90, H - 420)
    for i, t in enumerate(["opened all five locks, cracked the vault", "and saved the Harvest Feast with great math."]):
        c.drawCentredString(W / 2, H - 470 - i * 24, t)
    for i in range(5):
        d.padlock(W / 2 - 2.5 * 70 + i * 70 + 10, 210, 50, [P["berry"], P["green"], P["accent"], P["deep"], P["primary"]][i])
    c.setFont("Body", 13); c.setFillColor(P["ink"])
    c.drawString(M + 40, 140, "Teacher: ____________________"); c.drawRightString(W - M - 40, 140, "Date: ______________")

    # terms + thanks
    d.page(("Thank You!", "Terms of use"))
    y = H - 170
    for t in ["Thank you for choosing Brain Arcade Games. We make printable math games that are ready to play, so your class gets more practice with less prep.",
              "You may: print and copy this game for your own students, in one classroom or one homeschool family, every year you teach.",
              "Please do not: share the files with other teachers, post them online (including school websites, shared drives open to others, or resale sites), or sell them.",
              "Teaching more than one class? Buy one copy per teacher.",
              "Found something to fix? Message us on Etsy and we will help right away.",
              "A review on Etsy helps other teachers find games that work. Thank you!"]:
        y = d.para(M + 20, y, t, size=15, width=W - 2 * M - 40, lead=21) - 18
    c.setFillColor(white); c.setStrokeColor(P["primary"]); c.setLineWidth(2.5)
    c.roundRect(M + 20, 70, W - 2 * M - 40, y - 90, 16, 1, 1)
    for i in range(5):
        d.padlock(W / 2 - 2.5 * 80 + i * 80 + 14, (y + 70) / 2 - 40, 52, [P["berry"], P["green"], P["accent"], P["deep"], P["primary"]][i])
    c.setFillColor(P["deep"]); c.setFont("Head", 18)
    c.drawCentredString(W / 2, (y + 70) / 2 + 60, "Happy Thanksgiving from Brain Arcade Games!")
    c.setFont("Body", 9); c.drawCentredString(W / 2, 84, "Fonts: Bricolage Grotesque and Outfit (SIL Open Font License).")
    c.save()

    bj = os.path.join(out_dir, "build.json")
    json.dump(b, open(bj, "w"), indent=1)
    return pdf, bj, d.n


def main():
    spec_path, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    spec = json.load(open(spec_path))
    pdf, bj, pages = {"escape_room": build_escape_room}[spec["type"]](spec, out_dir)
    print(f"built {pdf} ({pages} pages)")
    r = subprocess.run([sys.executable, os.path.join(HERE, "answer_check.py"), spec_path, bj, pdf])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
