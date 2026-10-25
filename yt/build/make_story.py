#!/usr/bin/env python3
"""
YouTube Starship — illustrated story Short builder ("format": "story").

make_short.py hands any job with "format": "story" to this file, so the Action, the dry run
(--check) and the output paths stay the same.

The look (1080x1920): black background, one 16:9 illustration centered, a small gold label and a
big white headline above it, the narrator's full sentence below it. Each image slowly zooms and
scenes crossfade. Free tools only: Cloudflare FLUX images, edge-tts (andrew or ava), ffmpeg.

Spec:
{
  "id": "st01", "format": "story",
  "title": "The Crocodile Paradox Explained #shorts",
  "voice": "andrew",                       # andrew or ava
  "speed": 1.0,
  "art": "stickfigure",                    # "stickfigure" or "storybook" (one per episode)
  "cast": {"croc": "a big green cartoon crocodile with ..."},   # exact same text in every prompt
  "music": "tense", "music_volume": 0.08,  # optional; "none" for no music
  "lines": [                               # 6-10 scenes: setup, problem, twist, payoff
    {"text": "Why did ...?",               # one sentence, 15 words or fewer; line 1 is the hook question
     "label": "BOARDED UP",                # gold, 2-3 words
     "headline": "THE STORE NOBODY VISITS",# white, 3-6 words
     "image": "{croc} holding ... in the river"}   # must name a cast member with {key}
  ]
}
"""
import json, os, re, shutil, subprocess, sys, tempfile, wave, math, time

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(ROOT, "fonts")
W, H = 1080, 1920
IMG_W, IMG_H = 1080, 608           # 16:9 box in the middle of the screen
IMG_Y = (H - IMG_H) // 2
FPS = 30
SR = 24000
XF = 0.4                           # crossfade between scenes, seconds
ZOOM = 0.07                        # gentle zoom over one scene
MAX_MB = 4.45                      # keeps the file under Make's 5 MB upload limit
GOLD = (245, 197, 66)
VOICES = {"andrew": "en-US-AndrewMultilingualNeural", "ava": "en-US-AvaMultilingualNeural"}
ART = {
    "stickfigure": ("simple hand-drawn stick-figure illustration, characters with round white heads, "
                    "small dot eyes and thin black ink line bodies, on a soft hand-painted watercolor "
                    "background with muted earthy colors, clean minimal ink lines, wide 16:9 landscape scene, "
                    "main action in the center of the frame, no text, no letters, no words, no watermark"),
    "storybook": ("warm storybook cartoon illustration, soft gouache and watercolor textures, gentle warm "
                  "colors, rounded friendly characters, children's picture book style, wide 16:9 landscape "
                  "scene, main action in the center of the frame, no text, no letters, no words, no watermark"),
}

def run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd)[:300], flush=True)
    return subprocess.run(cmd, check=True, **kw)

def ffprobe_dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()
    return float(out)

# ---------------------------------------------------------------- story rules
def words(s):
    return [w for w in s.split() if re.search(r"[A-Za-z0-9]", w)]

def check_story(spec):
    """Raise with a one-line reason when the script breaks a story rule. Returns warnings."""
    warn = []
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", str(spec.get("id", ""))):
        raise SystemExit("story: spec id missing or invalid")
    lines = spec.get("lines") or []
    if not 6 <= len(lines) <= 10:
        raise SystemExit(f"story: need 6-10 scenes, got {len(lines)}")
    if spec.get("voice", "andrew") not in VOICES:
        raise SystemExit("story: voice must be andrew or ava")
    if spec.get("art") not in ART:
        raise SystemExit("story: art must be stickfigure or storybook")
    if spec.get("loop"):
        raise SystemExit("story: loop format is retired; tell the story start to finish")
    cast = spec.get("cast") or {}
    if not cast:
        raise SystemExit("story: cast is empty; every character needs one fixed description")
    for i, ln in enumerate(lines, 1):
        t = re.sub(r"\s+", " ", str(ln.get("text", ""))).strip(); ln["text"] = t
        n = len(words(t))
        if not t or n > 15:
            raise SystemExit(f"story: scene {i} has {n} words (max 15): {t[:60]}")
        if "..." in t or "…" in t or t.endswith(("-", ",")):
            raise SystemExit(f"story: scene {i} trails off; use one complete sentence")
        body = re.sub(r"[\"'”’]+$", "", t)
        if re.search(r"[.!?][\"'”’]?\s+[\"'“‘]?[A-Z]", body[:-1]):
            raise SystemExit(f"story: scene {i} has more than one sentence")
        lab = str(ln.get("label", "")).strip(); hl = str(ln.get("headline", "")).strip()
        if not 2 <= len(lab.split()) <= 3:
            raise SystemExit(f"story: scene {i} label must be 2-3 words")
        if not 3 <= len(hl.split()) <= 6:
            raise SystemExit(f"story: scene {i} headline must be 3-6 words")
        ln["label"] = lab.upper(); ln["headline"] = hl.upper()
        img = ln.get("image")
        prompt = img.get("prompt") if isinstance(img, dict) else img
        if not prompt or not re.search(r"\{(" + "|".join(map(re.escape, cast)) + r")\}", prompt):
            raise SystemExit(f"story: scene {i} image prompt must name a cast member like {{{next(iter(cast))}}}")
        unknown = set(re.findall(r"\{(\w+)\}", prompt)) - set(cast)
        if unknown:
            raise SystemExit(f"story: scene {i} uses unknown cast {sorted(unknown)}")
        ln["prompt"] = prompt
    if not lines[0]["text"].endswith("?"):
        raise SystemExit("story: line 1 must be the hook question (end with ?)")
    if not lines[-1]["text"].endswith((".", "!", '."', '!"')):
        raise SystemExit("story: the last line must end the story, not tease it")
    if lines[-1]["text"].endswith("?"):
        raise SystemExit("story: the ending must answer the hook, not ask a new question")
    return warn

def expand(prompt, spec):
    for k, v in spec["cast"].items():
        prompt = prompt.replace("{" + k + "}", v)
    return f"{prompt}. {ART[spec['art']]}"

# ---------------------------------------------------------------- voice
def tts(lines, voice, speed, work, fake):
    paths = []
    if fake:
        for i, ln in enumerate(lines):
            p = os.path.join(work, f"v{i:02d}.wav")
            secs = 0.36 * len(words(ln["text"])) + 0.3
            run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=f=220:r={SR}", "-t", f"{secs:.2f}",
                 "-af", "volume=0.05", "-ac", "1", p])
            paths.append(p)
        return paths
    import asyncio, edge_tts
    rate = f"{int(round((speed - 1) * 100)):+d}%"
    async def one(text, out):
        await asyncio.wait_for(edge_tts.Communicate(text, VOICES[voice], rate=rate).save(out), timeout=45)
    for i, ln in enumerate(lines):
        mp3 = os.path.join(work, f"v{i:02d}.mp3"); p = mp3[:-4] + ".wav"
        err = None
        for attempt in range(4):
            try:
                asyncio.run(one(ln["text"], mp3))
                if os.path.getsize(mp3) > 2000:
                    break
                err = "empty audio"
            except Exception as e:
                err = repr(e)
            time.sleep(3 + attempt * 5)
        else:
            raise SystemExit(f"voice failed on scene {i+1} after 4 tries: {err[:150]}")
        # trim the silence edge-tts leaves at both ends so scenes stay tight
        run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-af",
             "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
             "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
             "-ar", str(SR), "-ac", "1", p])
        paths.append(p)
    return paths

def wav_frames(p):
    with wave.open(p) as w:
        return w.readframes(w.getnframes()), w.getnframes() / w.getframerate()

def plan_timing(durs, warn):
    """Scene length = voice + breathing room, 3-6 s each, 40-60 s total."""
    lead, tail = 0.25, 0.45
    scenes = [max(3.0, lead + d + tail) for d in durs]
    for i, s in enumerate(scenes):
        if s > 6.5:
            raise SystemExit(f"story: scene {i+1} needs {s:.1f}s of voice (max 6); shorten the line")
        if s > 6.0:
            warn.append(f"scene {i+1} runs {s:.1f}s")
    total = sum(scenes)
    if total < 40:  # stretch the pauses evenly, never past 6 s a scene
        room = [6.0 - s for s in scenes]
        need = 40 - total
        if sum(room) >= need:
            scenes = [s + r * need / sum(room) for s, r in zip(scenes, room)]
        total = sum(scenes)
    if not 39.5 <= total <= 60.5:
        raise SystemExit(f"story: runs {total:.1f}s; it must be 40-60s (add or trim scenes)")
    return scenes, lead

def build_audio(paths, scenes, lead, work):
    pcm = b""
    for p, s in zip(paths, scenes):
        data, d = wav_frames(p)
        n_total = int(round(s * SR)); n_lead = int(lead * SR)
        seg = b"\x00\x00" * n_lead + data
        seg = seg[: n_total * 2] + b"\x00\x00" * max(0, n_total - len(seg) // 2)
        pcm += seg
    raw = os.path.join(work, "vo_raw.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
    vo = os.path.join(work, "vo.wav")
    fx = ("highpass=f=75,equalizer=f=280:t=q:w=1.1:g=-2.5,equalizer=f=3200:t=q:w=1.3:g=3,"
          "acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2,loudnorm=I=-15:TP=-1.5:LRA=9")
    run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", fx, "-ar", str(SR), vo])
    return vo

# ---------------------------------------------------------------- images
def get_image(spec, ln, i, work, fake, warn):
    from PIL import Image
    p = os.path.join(work, f"img{i:02d}.jpg")
    if fake:
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1024x1024", "-frames:v", "1", p])
    else:
        sys.path.insert(0, ROOT)
        from make_short import gen_image
        msgs = []
        if not gen_image(expand(ln["prompt"], spec), 1000 + i, p, msgs):
            raise SystemExit(f"image failed on scene {i+1}: {'; '.join(msgs[-2:])[:200]}")
    im = Image.open(p).convert("RGB")
    # FLUX schnell returns a square: keep the middle 16:9 band
    w, h = im.size
    ch = int(round(w * 9 / 16))
    if ch < h:
        top = (h - ch) // 2
        im = im.crop((0, top, w, top + ch))
    return im

# ---------------------------------------------------------------- text
def font(name, size):
    from PIL import ImageFont
    p = os.path.join(FONT_DIR, name)
    if not os.path.exists(p):
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(p, size)

def wrap(draw, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    if cur:
        out.append(cur)
    return out

def fit(draw, text, fname, size, minsize, maxw, maxlines):
    while True:
        f = font(fname, size)
        ls = wrap(draw, text, f, maxw)
        if (len(ls) <= maxlines and all(draw.textlength(l, font=f) <= maxw for l in ls)) or size <= minsize:
            return f, ls, size
        size -= 4

def scene_layer(ln):
    """Black frame with the label, headline and caption for one scene (image box left empty)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    margin = 70; maxw = W - 2 * margin
    hf, hls, hs = fit(d, ln["headline"], "Poppins-Black.ttf", 92, 60, maxw, 2)
    lf = font("Poppins-ExtraBold.ttf", 50)
    gap = int(hs * 1.12)
    y = IMG_Y - 44 - gap * len(hls)  # headline sits right above the picture
    ly = y - 70
    d.text((W / 2, ly), ln["label"], font=lf, fill=GOLD, anchor="mt")
    for k, l in enumerate(hls):
        d.text((W / 2, y + k * gap), l, font=hf, fill=(255, 255, 255), anchor="mt")
    cf, cls, cs = fit(d, ln["text"], "Poppins-ExtraBold.ttf", 66, 46, maxw, 3)
    cy = IMG_Y + IMG_H + 56
    for k, l in enumerate(cls):
        d.text((W / 2, cy + k * int(cs * 1.22)), l, font=cf, fill=(255, 255, 255), anchor="mt")
    return im

# ---------------------------------------------------------------- frames
def render_video(images, layers, scenes, out, work):
    from PIL import Image
    starts = [sum(scenes[:k]) for k in range(len(scenes))]
    total = sum(scenes); n = int(round(total * FPS))
    srcs = [im.resize((int(IMG_W * 1.25), int(IMG_H * 1.25)), Image.LANCZOS) for im in images]

    def frame(k, t):
        s0 = starts[k] - XF / 2; span = scenes[k] + XF
        u = min(1.0, max(0.0, (t - s0) / span))
        u = u * u * (3 - 2 * u) * 0.35 + u * 0.65            # soft start and stop
        zin = k % 2 == 0
        z = 1.0 + ZOOM * (u if zin else 1 - u)
        src = srcs[k]; sw, sh = src.size
        cw, chh = sw / z, sh / z
        dx = (sw - cw) / 2 + (sw - cw) * 0.15 * (u - 0.5) * (1 if k % 4 < 2 else -1)
        dy = (sh - chh) / 2
        a = cw / IMG_W
        pic = src.transform((IMG_W, IMG_H), Image.AFFINE, (a, 0, dx, 0, a, dy), resample=Image.BICUBIC)
        f = layers[k].copy(); f.paste(pic, (0, IMG_Y))
        return f

    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                             "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out],
                            stdin=subprocess.PIPE)
    k = 0
    for fi in range(n):
        t = fi / FPS
        while k + 1 < len(scenes) and t >= starts[k + 1]:
            k += 1
        f = frame(k, t)
        # crossfade: XF/2 before and after each cut
        if k + 1 < len(scenes) and t > starts[k + 1] - XF / 2:
            a = (t - (starts[k + 1] - XF / 2)) / XF
            f = Image.blend(f, frame(k + 1, t), a)
        elif k > 0 and t < starts[k] + XF / 2:
            a = (t - (starts[k] - XF / 2)) / XF
            f = Image.blend(frame(k - 1, t), f, a)
        proc.stdin.write(f.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed while drawing the frames")
    return total

# ---------------------------------------------------------------- main
def build(spec_path, check=False):
    spec = json.load(open(spec_path))
    warn = check_story(spec)
    jid = spec["id"] + ("-check" if check else "")
    lines = spec["lines"]
    out_dir = tempfile.mkdtemp(prefix="check-") if check else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(spec_path))), "out")
    os.makedirs(out_dir, exist_ok=True)
    work = tempfile.mkdtemp(prefix=f"story-{jid}-")
    try:
        speed = min(1.15, max(0.9, float(spec.get("speed", 1.0))))
        vpaths = tts(lines, spec.get("voice", "andrew"), speed, work, check)
        durs = [wav_frames(p)[1] for p in vpaths]
        scenes, lead = plan_timing(durs, warn)
        vo = build_audio(vpaths, scenes, lead, work)
        images = [get_image(spec, ln, i, work, check, warn) for i, ln in enumerate(lines)]
        layers = [scene_layer(ln) for ln in lines]
        silent = os.path.join(work, "silent.mp4")
        total = render_video(images, layers, scenes, silent, work)
        # music: quiet generated bed (free), ducked under the voice
        mpath = None; mood = str(spec.get("music", "tense")).lower()
        if mood != "none" and not check:
            try:
                sys.path.insert(0, ROOT)
                import music as _music
                mpath = os.path.join(work, "music.wav")
                _music.write_wav(mpath, _music.make(mood, total + 1.5, sum(map(ord, jid)) % 1000))
            except Exception as ex:
                warn.append(f"music failed, built without it: {ex!r}"[:160]); mpath = None
        inputs = ["-i", silent, "-i", vo]
        if mpath:
            mv = float(spec.get("music_volume", 0.08))
            inputs += ["-i", mpath]
            af = (f"[2:a]volume={mv},aformat=sample_rates={SR}:channel_layouts=mono[m];"
                  f"[m][1:a]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[md];"
                  f"[1:a][md]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={total-0.8:.2f}:d=0.8[a]")
        else:
            af = f"[1:a]afade=t=out:st={total-0.6:.2f}:d=0.6[a]"
        kbps = int(max(400, min(4000, MAX_MB * 8192 / total - 96 - 30)))
        final = os.path.join(out_dir, f"{jid}.mp4")
        base = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"[0:v]fade=t=out:st={total-0.5:.2f}:d=0.5[v];{af}",
                "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-r", str(FPS),
                "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-tune", "animation",
                "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps*1.5)}k", "-bufsize", f"{kbps*3}k", "-pix_fmt", "yuv420p"]
        plog = os.path.join(work, "pass")
        run([*base, "-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", "/dev/null"])
        run([*base, "-pass", "2", "-passlogfile", plog, "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
             "-movflags", "+faststart", final])
        size = os.path.getsize(final)
        if size > MAX_MB * 1048576 * 1.03:
            warn.append(f"file is {size/1048576:.2f} MB, over the 4.6 MB upload target")
        t = 0.0; win = []
        for s, d in zip(scenes, durs):
            win.append([round(t + lead, 2), round(t + lead + d, 2)]); t += s
        meta = {"id": jid, "format": "story", "duration": round(ffprobe_dur(final), 2), "bytes": size,
                "mb": round(size / 1048576, 2), "width": W, "height": H, "scenes": [round(s, 2) for s in scenes],
                "lines": win, "credits": [], "warnings": warn, "fakeTts": check, "tts": "fake" if check else "edge",
                "voice": spec.get("voice", "andrew"), "art": spec["art"]}
        json.dump(meta, open(os.path.join(out_dir, f"{jid}.json"), "w"), indent=1)
        print(json.dumps(meta, indent=1))
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: make_story.py yt/jobs/<id>.json [--check]")
    build(sys.argv[1], "--check" in sys.argv or "--fake-tts" in sys.argv)
