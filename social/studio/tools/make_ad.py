"""Turn a short spec + a voiceover MP3 into a ready ad folder (stage.html + ad.json) for render.py.

Usage: python3 social/studio/tools/make_ad.py spec.json social/studio/<name>
Then:  python3 social/studio/tools/render.py social/studio/<name> out.mp4 [--only t1,t2,...]

spec.json (see social/studio/README.md for a full example):
{
 "vo": "social/studio/media/vo/<name>-vo.mp3",          voice from the studio voice Action
 "music": "social/studio/media/vo/<name>-music.wav",     from yt/build/music.py, >= video length
 "product": {"dir": "/social/studio/media/<name>", "cover": "cover.jpg", "price": "4.49", "pages": 14,
             "listTitle": "<live Etsy title>", "strip": ["p-04.png", ...4 pages],
             "bg": ["#2f9e6a", "#0b3524"], "accent": "#1f8a55", "hl": "#ffd34d", "dot": "#c9ffe0"},
 "phrases": [   one entry per spoken phrase, in order; the script is these "say" lines joined by spaces
   {"say": "Want to save a thousand dollars in 2027?", "cap": "Save *$1,000* | in *2027?*",
    "scene": "hook", "page": "p-04.png", "badge": "$1,000"},
   {"say": "Color in one box every time you save.", "cap": "Color in | *one* *box*", "scene": "pan", "page": "p-04.png"},
   {"say": "Missed a week?", "cap": "Missed a week?"},                      no "scene" = same scene continues
   {"say": "...", "cap": "...", "scene": "fan", "pages": ["p-04.png", "p-05.png", "p-06.png"]},
   {"say": "...", "cap": "...", "scene": "phone"},
   {"say": "Tap the link,", "cap": "Tap the *link*", "tap": true},          the phone taps Add to cart here
   {"say": "and grab it on Etsy.", "cap": "grab it on *Etsy!*", "scene": "end"}]
}
Scene types: hook (page flies in + badge), pan (close-up glide), fan (pages deal out), grid (2x2 snap-in),
phone (the listing on a phone: scroll, back up, tap), end (cover, price, CTA). Every video must contain
a phone scene with a tap and an end scene.
"""
import json, os, re, subprocess, sys, shutil

spec_path, out_dir = sys.argv[1], sys.argv[2]
S = json.load(open(spec_path))
here = os.path.dirname(os.path.abspath(__file__))
ph = S["phrases"]

dur_vo = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", S["vo"]]).decode())
log = subprocess.run(["ffmpeg", "-i", S["vo"], "-af", "silencedetect=noise=-38dB:d=0.18", "-f", "null", "-"], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
gaps = [(a, b) for a, b in zip(starts, ends) if b - a < 1.5 and a > 0.2]

# first guess: phrases share the speech time by length; then snap each boundary to the nearest pause
speech_end = starts[-1] if starts and ends and ends[-1] >= dur_vo - 0.05 else dur_vo
L = [max(4, len(p["say"])) for p in ph]
tot = sum(L); acc = 0; guesses = []
for l in L[:-1]:
    acc += l; guesses.append(speech_end * acc / tot)
nb = len(guesses)
if len(gaps) >= nb:
    # pick nb pauses in order, closest overall to the guesses (small DP, keeps phrases in order)
    INF = 1e9; G = len(gaps); mid = [(a + b) / 2 for a, b in gaps]
    cost = [[INF] * (G + 1) for _ in range(nb + 1)]; back = [[0] * (G + 1) for _ in range(nb + 1)]
    for j in range(G + 1): cost[0][j] = 0
    for i in range(1, nb + 1):
        for j in range(i, G + 1):
            skip = cost[i][j - 1]; take = cost[i - 1][j - 1] + (mid[j - 1] - guesses[i - 1]) ** 2
            if take <= skip: cost[i][j] = take; back[i][j] = 1
            else: cost[i][j] = skip; back[i][j] = 0
    picked = []; i, j = nb, G
    while i > 0:
        if back[i][j]: picked.append(gaps[j - 1]); i -= 1
        j -= 1
    bounds = picked[::-1]
else:
    print("note: fewer pauses than phrases; timing by length (check the stills)")
    bounds = [(g, g) for g in guesses]
times = []
t = 0.0
for i, p in enumerate(ph):
    t1 = bounds[i][0] if i < len(bounds) else speech_end
    times.append([round(t, 2), round(max(t1, t + 0.4), 2)])
    t = bounds[i][1] if i < len(bounds) else speech_end
dur = round(dur_vo + 1.7, 2)

scenes, cur = [], None
for i, p in enumerate(ph):
    if p.get("scene") or cur is None:
        if cur: cur["t1"] = times[i][0]; scenes.append(cur)
        cur = {k: v for k, v in p.items() if k in ("page", "pages", "badge", "path", "cut")}
        cur["type"] = p.get("scene", "hook"); cur["t0"] = times[i][0]; cur["_ph"] = []
    cur["_ph"].append(i)
cur["t1"] = dur + 0.3; scenes.append(cur)
scenes[0]["t0"] = 0

sfx = [[0.05, "whoosh"], [0.75, "thud"], [0.95, "pop"]]
for k, s in enumerate(scenes):
    d = s["t1"] - s["t0"]
    if k: sfx.append([round(s["t0"] - 0.05, 2), "whoosh"])
    if s["type"] == "pan":
        s.setdefault("path", [-60, 430, -150, -300]); s.setdefault("cut", "whip")
    if s["type"] in ("fan", "grid"):
        n = len(s["pages"]); st = [times[i][0] for i in s["_ph"]]
        if len(st) < n:  # spread the pages over the scene
            st = [s["t0"] + 0.1 + j * (d - 0.6) / max(1, n - 1) * 0.8 for j in range(n)]
        s["beats"] = [round(x, 2) for x in st[:n]]
        sfx += [[b, "pop"] for b in s["beats"]]
    if s["type"] == "phone":
        tap_i = next((i for i in s["_ph"] if ph[i].get("tap")), s["_ph"][-1])
        tap = times[tap_i][0] - s["t0"] + 0.05
        tap = min(tap, d - 0.4)
        down0 = min(0.5, tap * 0.15); down1 = down0 + min(0.9, tap * 0.3)
        up0 = max(down1 + 0.2, tap - 1.2); up1 = max(up0 + 0.3, tap - 0.4)
        s["beats"] = [round(x, 2) for x in (down0, down1, up0, up1, tap)]
        sfx += [[round(s["t0"] + down0, 2), "whoosh"], [round(s["t0"] + tap, 2), "tap"], [round(s["t0"] + tap + 0.25, 2), "pop"]]
    if s["type"] == "end":
        sfx += [[round(s["t0"] + 0.35, 2), "impact"], [round(s["t0"] + 0.8, 2), "pop"]]
    del s["_ph"]
types = [s["type"] for s in scenes]
assert "phone" in types and types[-1] == "end", "every ad needs a phone scene and ends on the end scene"

ad = {"dur": dur, "vo": S["vo"], "music": S["music"], "musicVol": S.get("musicVol", 0.7),
      "grade": "eq=contrast=1.04:saturation=1.08,noise=alls=2:allf=t",
      "tl": {"product": S["product"], "scenes": scenes},
      "captions": [[times[i][0], times[i][1], p["cap"]] for i, p in enumerate(ph)], "sfx": sorted(sfx)}
os.makedirs(out_dir, exist_ok=True)
shutil.copy(os.path.join(here, "..", "etsy", "stage.html"), os.path.join(out_dir, "stage.html"))
json.dump(ad, open(os.path.join(out_dir, "ad.json"), "w"), indent=1)
print("dur", dur, "| scenes", [(s["type"], s["t0"], round(s["t1"], 2)) for s in scenes])
print("captions", [(c[0], c[1]) for c in ad["captions"]])
