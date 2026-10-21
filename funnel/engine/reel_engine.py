"""Funnel Floor reel engine: renders a faceless, motion-graphics "build in public" Reel (about 20 s).

Usage: python3 reel_engine.py config.json out.mp4
Config keys: day, slam (big opening line), hook (typed line under it), workers, products (image paths),
stats (list of [label, value]), stats_line, foreman (quote), cta_word, cta_sub, handle.
Everything (visuals, beat, click/pop/whoosh/stamp sounds) is generated here: free and original.
"""
import json, math, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 44100
BPM = 116
BEAT = 60 / BPM
BG = (8, 9, 13)
AMB = (255, 179, 71)
GRN = (60, 255, 138)
BLU = (95, 182, 255)
PUR = (169, 112, 255)
RED = (255, 93, 108)
INK = (240, 244, 252)
DIM = (125, 135, 155)
FD = "/usr/share/fonts/truetype/dejavu/"
MB, SB, SR_ = FD + "DejaVuSansMono-Bold.ttf", FD + "DejaVuSans-Bold.ttf", FD + "DejaVuSans.ttf"
TYPE = 0.045  # seconds per typed character
_fc = {}


def F(p, s):
    k = (p, int(s))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(p, max(8, int(s)))
    return _fc[k]


def ease_out(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


def back_out(x):
    x = min(max(x, 0), 1)
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def wrap(d, t, f, maxw):
    out, cur = [], ""
    for w in t.split():
        tt = (cur + " " + w).strip()
        if d.textlength(tt, font=f) <= maxw:
            cur = tt
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return out


def ctext(d, t, f, y, col, maxw=960, gap=16):
    for ln in wrap(d, t, f, maxw):
        d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=col)
        y += f.size + gap
    return y


def bot(d, x, y, s, col, blink=False, walk=None, carry=None):
    """Pixel robot. walk = phase (radians) animates legs and bob; carry = box colour held overhead."""
    u = s / 8
    bob = 0
    if walk is not None:
        bob = -abs(math.sin(walk)) * u * 0.6
    y = y + bob
    d.rectangle((x + 3 * u, y, x + 5 * u, y + u), fill=col)
    d.rectangle((x + u, y + u, x + 7 * u, y + 5 * u), fill=col)
    eh = 0.25 * u if blink else 1.1 * u
    ey = y + 2.85 * u - eh / 2
    d.rectangle((x + 2.2 * u, ey, x + 3.4 * u, ey + eh), fill=BG)
    d.rectangle((x + 4.6 * u, ey, x + 5.8 * u, ey + eh), fill=BG)
    d.rectangle((x + 2 * u, y + 5.5 * u, x + 6 * u, y + 7.4 * u), fill=col)
    if walk is not None:
        a = math.sin(walk) * u * 0.9
        d.rectangle((x + 2.4 * u + a, y + 7.4 * u, x + 3.4 * u + a, y + 8.4 * u - bob), fill=col)
        d.rectangle((x + 4.6 * u - a, y + 7.4 * u, x + 5.6 * u - a, y + 8.4 * u - bob), fill=col)
    else:
        d.rectangle((x + 2.4 * u, y + 7.4 * u, x + 3.4 * u, y + 8 * u), fill=col)
        d.rectangle((x + 4.6 * u, y + 7.4 * u, x + 5.6 * u, y + 8 * u), fill=col)
    if carry:
        d.rectangle((x + 1.5 * u, y - 2.6 * u, x + 6.5 * u, y - 0.3 * u), fill=carry, outline=BG, width=max(1, int(u * 0.3)))
        d.line((x + 4 * u, y - 2.6 * u, x + 4 * u, y - 0.3 * u), fill=BG, width=max(1, int(u * 0.3)))


class Reel:
    def __init__(self, cfg):
        self.c = cfg
        self.events = []
        random.seed(7)
        self.pal = [AMB, GRN, BLU, PUR, RED]
        self.cols = [random.choice(self.pal) for _ in range(60)]
        self.prod = []
        for p in cfg["products"][:3]:
            im = Image.open(p).convert("RGB")
            im.thumbnail((800, 800))
            self.prod.append(im.convert("RGBA"))
        lens = [4.6, 4.4, 4.2, 4.0, 4.3]
        self.S, t = [], 0.0
        for L in lens:
            self.S.append((t, t + L))
            t += L
        self.dur = t
        self._plan_events()

    # ---------- sound events, matched to the visuals ----------
    def _plan_events(self):
        c, ev = self.c, self.events
        ev.append((0.0, "impact"))
        hook = c["hook"]
        for i, ch in enumerate(hook):
            if ch != " ":
                ev.append((1.0 + i * TYPE, "click"))
        t0 = self.S[1][0]
        ev.append((t0, "whoosh"))
        for i in range(len(self.prod)):
            ev.append((t0 + 0.4 + i * 0.7, "whoosh"))
            ev.append((t0 + 0.95 + i * 0.7, "stamp"))
        t0 = self.S[2][0]
        ev.append((t0, "whoosh"))
        for i in range(len(c["stats"])):
            for k in range(12):
                ev.append((t0 + 0.55 + i * 0.75 + k * 0.05, "tick"))
        t0 = self.S[3][0]
        ev.append((t0 + 0.45, "impact"))
        for i, ch in enumerate(c["foreman"]):
            if ch != " ":
                ev.append((t0 + 1.1 + i * TYPE, "click"))
        t0 = self.S[4][0]
        ev.append((t0 + 0.1, "impact"))
        ev.append((t0 + 0.6, "impact"))

    # ---------- shared layers ----------
    def bg(self, t):
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        off = int((t * 40) % 60)
        for x in range(-60, W + 60, 60):
            d.line([(x + off, 0), (x + off, H)], fill=(17, 19, 26))
        for y in range(-60, H + 60, 60):
            d.line([(0, y + off), (W, y + off)], fill=(17, 19, 26))
        return im, d

    def conveyor(self, d, t, y=1600, n=7):
        """Factory floor strip: moving belt, boxes riding it, robots running along it carrying boxes."""
        d.rectangle((0, y + 120, W, y + 150), fill=(28, 32, 42))
        off = (t * 220) % 80
        for x in range(-80, W + 80, 80):
            d.line((x + off, y + 120, x + off - 20, y + 150), fill=(45, 52, 66), width=4)
        for i in range(5):
            bx = (i * 260 + t * 220) % (W + 260) - 130
            d.rectangle((bx, y + 70, bx + 70, y + 120), fill=self.pal[i % 5], outline=BG, width=3)
        for i in range(n):
            sp = 160 + (i % 3) * 60
            x = (i * (W + 200) / n + t * sp) % (W + 200) - 120
            bot(d, x, y - 10 - (i % 2) * 30, 90, self.cols[i + 30], walk=t * 14 + i, carry=self.pal[(i + 2) % 5] if i % 2 == 0 else None)

    def chrome(self, d, t):
        d.rectangle((40, 60, 280, 130), fill=AMB)
        d.text((60, 72), "DAY %s" % self.c["day"], font=F(MB, 46), fill=BG)
        d.text((W - 190, 76), "LIVE", font=F(MB, 36), fill=INK)
        if int(t * 2) % 2 == 0:
            d.ellipse((W - 76, 84, W - 52, 108), fill=RED)
        h = self.c["handle"]
        d.text((W - 40 - d.textlength(h, font=F(SR_, 30)), 1830), h, font=F(SR_, 30), fill=DIM)

    # ---------- scenes ----------
    def s_hook(self, d, t):
        # robots already sprinting across the floor from frame 1
        nb = int(self.c.get("workers", 26))
        rows = [(760, 0), (950, 1), (1140, 2)]
        for i in range(min(nb, 21)):
            ry, r = rows[i % 3]
            sp = 260 + r * 70 + (i % 4) * 25
            x = (i * 151 + t * sp) % (W + 240) - 140
            bot(d, x, ry + (i % 2) * 20, 105, self.cols[i], walk=t * 15 + i, blink=(int(t * 3 + i) % 13 == 0))
        e = back_out(t / 0.35)
        slam = self.c.get("slam", "I DON'T RUN MY BUSINESS.")
        f = F(SB, 104 * e)
        if e > 0.05:
            ctext(d, slam, f, 250 + (1 - e) * 40, AMB, 1000, 10)
        hook = self.c["hook"]
        n = int(max(0, t - 1.0) / TYPE)
        shown = hook[: min(n, len(hook))]
        if t > 1.0:
            cur = "|" if (int(t * 6) % 2 == 0 and n <= len(hook) + 6) else ""
            ctext(d, shown + cur, F(SB, 68), 520, INK, 980, 12)
        # counter chip
        if t > 2.6:
            k = back_out((t - 2.6) / 0.3)
            d.rounded_rectangle((W / 2 - 230 * k, 1380, W / 2 + 230 * k, 1480), radius=50, fill=(20, 32, 24), outline=GRN, width=4)
            if k > 0.9:
                tx = "%d WORKERS ONLINE" % nb
                d.text(((W - d.textlength(tx, font=F(MB, 40))) / 2, 1408), tx, font=F(MB, 40), fill=GRN)
        self.conveyor(d, t)

    def s_products(self, im, d, t):
        k = ease_out(t / 0.4)
        f = F(MB, 60)
        title = "MY AI CREW BUILT THESE"
        d.text(((W - d.textlength(title, font=f)) / 2 - (1 - k) * 300, 230), title, font=f, fill=AMB)
        for i, p in enumerate(self.prod):
            st = 0.4 + i * 0.7
            if t < st:
                continue
            e = back_out((t - st) / 0.5)
            rot = p.rotate([-6, 5, -2][i] * e, expand=True, resample=Image.BICUBIC)
            x = int(W + 100 - (W + 100 - [80, 200, 140][i]) * e)
            y = 360 + i * 330
            a = rot.split()[3]
            im.paste(Image.new("RGB", rot.size, (0, 0, 0)), (x + 18, y + 22), a.point(lambda v: v * 0.55))
            im.paste(rot.convert("RGB"), (x, y), a)
        d = ImageDraw.Draw(im)
        for i in range(len(self.prod)):
            st = 0.95 + i * 0.7
            if t < st:
                continue
            e = back_out((t - st) / 0.2)
            sc = 2.2 - 1.2 * e
            fw = F(MB, 44 * sc)
            tx = "✓ QUALITY CHECK"
            w = d.textlength(tx, font=fw)
            cx, cy = [700, 820, 760][i], 420 + i * 330
            d.rounded_rectangle((cx - w / 2 - 20, cy - 10, cx + w / 2 + 20, cy + fw.size + 20), radius=14, outline=GRN, width=6, fill=(10, 30, 18))
            d.text((cx - w / 2, cy + 4), tx, font=fw, fill=GRN)
        return d

    def s_stats(self, d, t):
        tl = "THE SCOREBOARD"
        d.text(((W - d.textlength(tl, font=F(MB, 60))) / 2, 280), tl, font=F(MB, 60), fill=AMB)
        y = 470
        for i, (lab, val) in enumerate(self.c["stats"]):
            st = 0.3 + i * 0.75
            if t < st:
                continue
            e = ease_out((t - st) / 0.35)
            x = 90 - (1 - e) * 1000
            d.rounded_rectangle((x, y, x + 900, y + 230), radius=26, outline=(51, 58, 71), width=4, fill=(16, 19, 25))
            d.text((x + 50, y + 40), lab.upper(), font=F(MB, 40), fill=DIM)
            num = "".join(ch for ch in val if ch.isdigit())
            pre = val.split(num)[0] if num else ""
            pr = min(1, max(0, (t - st - 0.25) / 0.6))
            shown = pre + str(int(round(int(num) * pr))) if num else val
            zero = val.strip("$") == "0"
            shake = math.sin(t * 60) * 9 if (zero and pr >= 1 and t - st < 1.6) else 0
            d.text((x + 50 + shake, y + 100), shown, font=F(SB, 96), fill=RED if zero else GRN)
            y += 280
        if t > 2.7:
            ctext(d, self.c.get("stats_line", "Let's see how long that $0 lasts."), F(SR_, 50), y + 30, INK)
        self.conveyor(d, t, n=5)

    def s_foreman(self, d, t):
        ctext(d, "EVERY MORNING THE BOSS ROBOT GRADES THE CREW", F(MB, 56), 240, AMB, 960)
        drop = ease_out(min(1, t / 0.45))
        land = (math.sin(t * 40) * 14 * max(0, 1 - (t - 0.45) * 4)) if t > 0.45 else 0
        yb = -500 + (640 + 500) * drop + land
        bot(d, 330, yb, 420, AMB, blink=(int(t * 2.5) % 5 == 0))
        # little workers scrambling around the boss
        for i in range(6):
            x = (i * 190 + t * (200 + i * 30) * (1 if i % 2 else -1)) % (W + 160) - 80
            bot(d, x, 1130 + (i % 2) * 40, 80, self.cols[i + 10], walk=t * 16 + i)
        if t > 0.9:
            e = back_out((t - 0.9) / 0.3)
            bw = 860 * e
            d.rounded_rectangle((W / 2 - bw / 2, 1300, W / 2 + bw / 2, 1300 + 270 * e), radius=30, fill=(32, 25, 14), outline=AMB, width=4)
            q = self.c["foreman"]
            n = int(max(0, t - 1.1) / TYPE)
            if e > 0.9:
                ctext(d, '"' + q[: min(n, len(q))] + ('"' if n >= len(q) else ""), F(MB, 50), 1350, AMB, 780)
                ctext(d, "- The Foreman", F(SR_, 38), 1490, DIM)

    def s_cta(self, d, t):
        pulse = 1 + 0.06 * max(0, math.cos((t % BEAT) / BEAT * math.pi * 2)) if t > 0.7 else 1
        e1 = back_out(t / 0.3)
        e2 = back_out(max(0, t - 0.5) / 0.35)
        d.rounded_rectangle((80, 380, 1000, 1300), radius=40, outline=AMB, width=int(8 * pulse))
        if e1 > 0:
            ctext(d, "COMMENT", F(SB, 100 * e1), 490, INK)
        if e2 > 0:
            f = F(SB, 300 * e2 * pulse)
            w = d.textlength(self.c["cta_word"], font=f)
            d.text(((W - w) / 2, 650 + (300 - f.size) / 2), self.c["cta_word"], font=f, fill=AMB)
        if t > 1.1:
            ctext(d, self.c["cta_sub"], F(SR_, 52), 1020, INK, 800)
        self.conveyor(d, t)

    def frame(self, t):
        im, d = self.bg(t)
        si = max(i for i, (a, b) in enumerate(self.S) if t >= a)
        lt = t - self.S[si][0]
        if si == 0:
            self.s_hook(d, lt)
        elif si == 1:
            d = self.s_products(im, d, lt)
        elif si == 2:
            self.s_stats(d, lt)
        elif si == 3:
            self.s_foreman(d, lt)
        else:
            self.s_cta(d, lt)
        self.chrome(d, t)
        bp = (t % BEAT) / BEAT
        z = 1 + 0.01 * max(0, 1 - bp * 4)
        if z > 1.0005:
            nw, nh = int(W * z), int(H * z)
            im = im.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        if lt < 0.12 and (si > 0 or t < 0.12):
            im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 0.5 * (1 - lt / 0.12))
        return im

    # ---------- audio ----------
    def audio(self, path):
        N = int(SR * self.dur)
        out = np.zeros(N)
        rng = np.random.default_rng(3)

        def add(sig, t, vol=1.0):
            s = int(t * SR)
            if s >= N:
                return
            e = min(N, s + len(sig))
            out[s:e] += sig[: e - s] * vol

        def tt(sec):
            return np.arange(int(sec * SR)) / SR

        x = tt(0.35)
        kick = np.sin(2 * np.pi * (48 + 110 * np.exp(-x * 25)) * x) * np.exp(-x * 9)
        x = tt(0.25)
        snare = (rng.standard_normal(len(x)) * 0.6 + np.sin(2 * np.pi * 190 * x) * 0.5) * np.exp(-x * 18)
        x = tt(0.05)
        hat = np.diff(rng.standard_normal(len(x)) * np.exp(-x * 120), prepend=0)
        prog = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
        for b in range(int(self.dur / BEAT) + 1):
            t = b * BEAT
            if t > self.dur - 0.6:
                break
            add(kick, t, 0.9)
            if b % 2 == 1:
                add(snare, t, 0.45)
            add(hat, t + BEAT / 2, 0.18)
            add(hat, t, 0.08)
            root, ch = prog[(b // 4) % 4]
            if b % 2 == 0:
                x = tt(BEAT * 1.9)
                f = 440 * 2 ** ((root - 12 - 69) / 12)
                add((np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2 * f * x)) * np.exp(-x * 1.4), t, 0.45)
            for st in (0, BEAT * 0.75):
                x = tt(0.22)
                stab = sum(np.sign(np.sin(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * x)) * 0.5 + np.sin(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * x) for m in ch)
                add(stab * np.exp(-x * 14) / len(ch), t + st, 0.12)
        x = tt(0.03)
        click = (rng.standard_normal(len(x)) * 0.5 + np.sin(2 * np.pi * 3200 * x)) * np.exp(-x * 260)
        x = tt(0.04)
        tick = np.sin(2 * np.pi * 2400 * x) * np.exp(-x * 150)
        x = tt(0.45)
        whoosh = np.convolve(rng.standard_normal(len(x)), np.ones(18) / 18, mode="same") * np.sin(np.pi * x / 0.45) ** 2
        x = tt(0.6)
        impact = (np.sin(2 * np.pi * (40 + 80 * np.exp(-x * 18)) * x) * 1.2 + rng.standard_normal(len(x)) * 0.3 * np.exp(-x * 30)) * np.exp(-x * 6)
        x = tt(0.18)
        stamp = (np.sin(2 * np.pi * (90 + 200 * np.exp(-x * 40)) * x) + rng.standard_normal(len(x)) * 0.5 * np.exp(-x * 60)) * np.exp(-x * 22)
        fx = {"click": (click, 0.2), "tick": (tick, 0.2), "whoosh": (whoosh, 0.35), "impact": (impact, 0.8), "stamp": (stamp, 0.6)}
        for t, k in self.events:
            s, v = fx[k]
            add(s, t, v)
        fo = int(0.8 * SR)
        out[-fo:] *= np.linspace(1, 0, fo)
        out = np.tanh(out * 1.3)
        out /= np.max(np.abs(out)) * 1.05
        st = np.stack([out, np.roll(out, 40) * 0.97], axis=1)
        with wave.open(path, "w") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((st * 32767).astype(np.int16).tobytes())

    def render(self, out):
        wav = out + ".wav"
        self.audio(wav)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", wav,
                              "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for i in range(int(self.dur * FPS)):
            p.stdin.write(self.frame(i / FPS).tobytes())
        p.stdin.close()
        p.wait()
        return p.returncode


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    sys.exit(Reel(cfg).render(sys.argv[2]))
