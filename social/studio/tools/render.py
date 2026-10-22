"""Render a Ridgeline commercial: stage.html + captions -> frames -> MP4 with voice, music and sound effects.
Usage: python3 render.py <ad folder> <out.mp4> [--fps 30] [--only t1,t2,...  (just save stills)]
The ad folder holds stage.html and ad.json:
  {"dur": seconds, "vo": "path to voice mp3", "music": "path to wav", "captions": [[t0, t1, "text with *highlight*"], ...],
   "sfx": [[t, "whoosh|tap|thud|pop"], ...], "capTop": 1430}
"""
import json, os, sys, subprocess, threading, shutil, functools, http.server, socketserver, wave
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=os.path.dirname(os.path.abspath(__file__))).decode().strip()
ad_dir, out = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
fps = int(args[args.index("--fps") + 1]) if "--fps" in args else 30
only = [float(x) for x in args[args.index("--only") + 1].split(",")] if "--only" in args else None
cfg = json.load(open(os.path.join(ad_dir, "ad.json")))
work = out + ".work"; shutil.rmtree(work, ignore_errors=True); os.makedirs(work)

def chunks(captions):
    res = []
    for t0, t1, text in captions:
        parts = [p.strip() for p in text.split("|")]
        total = sum(len(p) for p in parts) or 1
        t = t0
        for p in parts:
            d = (t1 - t0) * len(p) / total
            words = [{"w": w.strip("*"), "hl": w.startswith("*")} for w in p.split()]
            res.append({"t0": round(t, 3), "t1": round(t + d, 3), "words": words, "top": cfg.get("capTop", 1430)})
            t += d
        res[-1]["t1"] = round(t1 + 0.25, 3)  # hold the last chunk through the breath
    return res

data = {"dur": cfg["dur"], "captions": chunks(cfg["captions"]), "tl": cfg.get("tl", {}), "bgs": cfg.get("bgs", [])}

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=ROOT))
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
stage_url = f"http://127.0.0.1:{port}/" + os.path.relpath(os.path.join(ad_dir, "stage.html"), ROOT)

times = only if only else [i / fps for i in range(int(cfg["dur"] * fps))]
with sync_playwright() as p:
    b = p.chromium.launch(args=["--disable-gpu-vsync", "--force-color-profile=srgb"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
    pg.add_init_script("window.AD_DATA=" + json.dumps(data))
    pg.goto(stage_url); pg.evaluate("window.ready"); pg.wait_for_timeout(800)
    for i, t in enumerate(times):
        pg.evaluate(f"window.render({t})")
        name = f"still-{t:05.2f}.png" if only else f"f{i:05d}.jpg"
        if only: pg.screenshot(path=os.path.join(work, name))
        else: pg.screenshot(path=os.path.join(work, name), type="jpeg", quality=93)
        if not only and i % 150 == 0: print("frame", i, "/", len(times), flush=True)
    b.close()
srv.shutdown()
if only:
    print("stills in", work); sys.exit(0)

# ---- sound effects (generated, royalty free)
SR = 44100
n = int(cfg["dur"] * SR) + SR
fx = np.zeros(n); rng = np.random.default_rng(3)
def put(sig, t, g):
    i = int(t * SR); j = min(n, i + len(sig)); fx[i:j] += sig[: j - i] * g
def whoosh():
    L = int(0.45 * SR); x = rng.standard_normal(L)
    # band-pass sweep by cumulative smoothing
    out = np.zeros(L); a = 0.0
    for k in range(L):
        c = 0.02 + 0.25 * (k / L); a += c * (x[k] - a); out[k] = a
    e = np.sin(np.pi * np.arange(L) / L) ** 2
    return out * e * 2.2
def tap():
    t = np.arange(int(0.05 * SR)) / SR
    return (np.sin(2 * np.pi * 1800 * t) * 0.5 + rng.standard_normal(len(t)) * 0.3) * np.exp(-t * 120)
def thud():
    t = np.arange(int(0.5 * SR)) / SR
    f = 45 + 120 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 1.2
def pop():
    t = np.arange(int(0.08 * SR)) / SR
    f = 900 + 900 * np.exp(-t * 60)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 50) * 0.35
def riser(L=1.3):
    N = int(L * SR); x = rng.standard_normal(N); out = np.zeros(N); a = 0.0
    for k in range(N):
        c = 0.004 + 0.12 * (k / N) ** 2; a += c * (x[k] - a); out[k] = a
    t = np.arange(N) / SR
    tone = np.sin(2 * np.pi * np.cumsum(200 + 1400 * (t / L) ** 2) / SR) * 0.25
    env = (t / L) ** 1.6
    return (out * 3 + tone) * env
def impact():
    t = np.arange(int(1.2 * SR)) / SR
    f = 38 + 160 * np.exp(-t * 18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4) * 1.4
    burst = rng.standard_normal(len(t)) * np.exp(-t * 28) * 0.5
    return sub + burst
FX = {"whoosh": whoosh, "tap": tap, "thud": thud, "pop": pop, "riser": riser, "impact": impact}
gains = {"whoosh": 0.35, "tap": 0.5, "thud": 0.7, "pop": 0.4, "riser": 0.45, "impact": 0.9}
for t, kind in cfg.get("sfx", []):
    put(FX[kind](), t, gains[kind])
fx = np.clip(fx, -1, 1)
with wave.open(os.path.join(work, "fx.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((fx * 32767).astype("<i2").tobytes())

# ---- mux: frames + voice (front) + music (ducked under the voice) + fx
vo, music = cfg["vo"], cfg["music"]
filt = ("[1:a]aresample=44100,highpass=f=70,equalizer=f=140:t=q:w=1:g=2.5,equalizer=f=3200:t=q:w=1.2:g=3,equalizer=f=9000:t=q:w=1:g=1.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,volume=1.6,asplit=2[vo][sc];"
        "[2:a]aresample=44100,volume=" + str(cfg.get("musicVol", 0.55)) + "[mu];"
        "[mu][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck];"
        "[3:a]aresample=44100,volume=0.9[fx];"
        "[vo][duck][fx]amix=inputs=3:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st=" + str(cfg["dur"] - 1.3) + ":d=1.3[a]")
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
       "-framerate", str(fps), "-i", os.path.join(work, "f%05d.jpg"),
       "-i", vo, "-i", music, "-i", os.path.join(work, "fx.wav"),
       "-filter_complex", filt, "-map", "0:v", "-map", "[a]", "-vf", cfg.get("grade", "eq=contrast=1.05:saturation=1.08,noise=alls=3:allf=t"),
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", str(cfg["dur"]), "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
shutil.rmtree(work)
print("wrote", out)
