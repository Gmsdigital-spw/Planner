#!/usr/bin/env python3
"""
YouTube Starship — illustrated story Short builder ("format": "story").

make_short.py hands any job with "format": "story" to this file, so the Action, the dry run
(--check) and the output paths stay the same.

The look (1080x1920): black background, one 16:9 illustration centered, and right above it a big
bold caps caption of the narrator's words, each word fading in as it is spoken (timed from the
voice itself). Scene 1 carries the episode title hand-lettered on the picture. Each image slowly
zooms and scenes crossfade. Free tools only: Cloudflare FLUX images, edge-tts (andrew or ava), ffmpeg.

Spec:
{
  "id": "st01", "format": "story",
  "title": "The Crocodile Paradox Explained #shorts",
  "voice": "andrew",                       # andrew or ava
  "speed": 1.0,
  "art": "stickfigure",                    # "stickfigure" or "storybook" (one per episode)
  "cast": {"croc": "a big green cartoon crocodile with ..."},   # exact same text in every prompt
  "title_card": "The Crocodile Paradox",   # hand-lettered on the first picture (optional)
  "music": "tense", "music_volume": 0.05,  # optional; "none" for no music
  "lines": [                               # 6-10 scenes: setup, problem, twist, payoff
    {"text": "Why did ...?",               # one sentence, 15 words or fewer; line 1 is the hook question
     "label": "BOARDED UP",                # optional notes for the writer (2-3 words), not drawn
     "headline": "THE STORE NOBODY VISITS",# optional notes (3-6 words), not drawn
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
VOICES = {"andrew": "en-US-AndrewMultilingualNeural", "ava": "en-US-AvaMultilingualNeural"}
ART = {
    "stickfigure": ("simple hand-drawn stick-figure illustration, every person is a simple stick figure with a round white head, "
                    "small dot eyes and thin black ink line bodies, on a soft hand-painted watercolor "
                    "background with muted earthy colors, clean minimal ink lines, wide 16:9 landscape scene, "
                    "main action in the center of the frame, every character's whole body and head fully in frame, no text, no letters, no words, no watermark"),
    "storybook": ("warm storybook cartoon illustration, soft gouache and watercolor textures, gentle warm "
                  "colors, rounded friendly characters, children's picture book style, wide 16:9 landscape "
                  "scene, main action in the center of the frame, every character's whole body and head fully in frame, no text, no letters, no words, no watermark"),
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
def even_times(text, dur):
    """Fallback word timings: spread the words over the line by length."""
    ws = text.split(); wt = [len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2 for w in ws]
    tot = sum(wt); t = 0.0; out = []
    for w, k in zip(ws, wt):
        out.append(round(t, 3)); t += dur * k / tot
    return out

def match_times(text, marks, cut):
    """Script words get the start times edge-tts reported (WordBoundary), shifted by the trim."""
    ws = [w for w in text.split()]
    spoken = [i for i, w in enumerate(ws) if re.search(r"[A-Za-z0-9]", w)]
    if len(marks) != len(spoken):
        return None
    out = [0.0] * len(ws)
    for i, (_, st) in zip(spoken, marks):
        out[i] = round(max(0.0, st - cut), 3)
    for i in range(len(ws)):  # a token with no letters (a dash) rides with the next word
        if i not in spoken:
            out[i] = out[i + 1] if i + 1 < len(ws) else out[i - 1]
    return out

def tts(lines, voice, speed, work, fake, warn):
    paths, times = [], []
    if fake:
        for i, ln in enumerate(lines):
            p = os.path.join(work, f"v{i:02d}.wav")
            secs = 0.36 * len(words(ln["text"])) + 0.3
            run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=f=220:r={SR}", "-t", f"{secs:.2f}",
                 "-af", "volume=0.05", "-ac", "1", p])
            paths.append(p); times.append(even_times(ln["text"], secs))
        return paths, times
    import asyncio, edge_tts
    rate = f"{int(round((speed - 1) * 100)):+d}%"
    async def one(text, out):
        marks = []
        async def go():
            com = edge_tts.Communicate(text, VOICES[voice], rate=rate, boundary="WordBoundary")
            with open(out, "wb") as f:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        marks.append((ch["text"], ch["offset"] / 1e7))
        await asyncio.wait_for(go(), timeout=45)
        return marks
    for i, ln in enumerate(lines):
        mp3 = os.path.join(work, f"v{i:02d}.mp3"); p = mp3[:-4] + ".wav"
        err = None; marks = []
        for attempt in range(4):
            try:
                marks = asyncio.run(one(ln["text"], mp3))
                if os.path.getsize(mp3) > 2000:
                    break
                err = "empty audio"
            except Exception as e:
                err = repr(e)
            time.sleep(3 + attempt * 5)
        else:
            raise SystemExit(f"voice failed on scene {i+1} after 4 tries: {err[:150]}")
        # trim the silence edge-tts leaves at both ends so scenes stay tight
        cut = max(0.0, marks[0][1] - 0.04) if marks else 0.0
        head = "" if marks else "silenceremove=start_periods=1:start_threshold=-45dB,"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{cut:.3f}", "-i", mp3, "-af",
             head + "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
             "-ar", str(SR), "-ac", "1", p])
        tm = match_times(ln["text"], marks, cut)
        if tm is None:
            warn.append(f"scene {i+1}: word timings from length (voice gave {len(marks)} marks)")
            tm = even_times(ln["text"], wav_frames(p)[1])
        paths.append(p); times.append(tm)
    return paths, times

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
    fx = ("highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=2500:t=q:w=1.2:g=2,"
          "deesser=i=0.35,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,"
          "loudnorm=I=-14:TP=-1.5:LRA=7")
    run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", fx, "-ar", str(SR), vo])
    return vo

# ---------------------------------------------------------------- images
KLEIN = "@cf/black-forest-labs/flux-2-klein-4b"
REF_NOTE = ("Keep the exact same characters, character designs, colors and art style as the reference "
            "image, in a new scene. ")

def gen_klein(prompt, seed, dest, ref, msgs):
    """Free FLUX.2 klein on Cloudflare Workers AI: native 16:9 and a reference picture for
    consistent characters. Returns True on success."""
    import base64, urllib.request, uuid
    acct = os.environ.get("CF_ACCOUNT_ID", "").strip(); tok = os.environ.get("CF_API_TOKEN", "").strip()
    if not (acct and tok):
        msgs.append("no Cloudflare keys"); return False
    fields = {"prompt": (REF_NOTE if ref else "") + prompt[:1900], "width": "1280", "height": "720",
              "seed": str(seed), "steps": "4"}
    bnd = uuid.uuid4().hex; body = b""
    for k, v in fields.items():
        body += f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    if ref:
        body += (f"--{bnd}\r\nContent-Disposition: form-data; name=\"input_image_0\"; filename=\"ref.jpg\"\r\n"
                 "Content-Type: image/jpeg\r\n\r\n").encode() + open(ref, "rb").read() + b"\r\n"
    body += f"--{bnd}--\r\n".encode()
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{KLEIN}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, method="POST", headers={
                "Authorization": f"Bearer {tok}", "Content-Type": f"multipart/form-data; boundary={bnd}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read(); ctype = r.headers.get("Content-Type", "")
            if "json" in ctype:
                d = json.loads(raw); img = (d.get("result") or {}).get("image")
                raw = base64.b64decode(img) if img else b""
                if not raw:
                    msgs.append(f"klein try {attempt+1}: no image ({str(d.get('errors'))[:120]})")
            if len(raw) > 20000:
                open(dest, "wb").write(raw); return True
        except Exception as e:
            m = ""
            try:
                m = e.read().decode()[:160]
            except Exception:
                pass
            msgs.append(f"klein try {attempt+1} failed: {e!r} {m}"[:220])
            if "daily free allocation" in m or "neurons" in m or "No route" in m or "not found" in m.lower():
                return False
        time.sleep(3 + attempt * 6)
    return False

def get_image(spec, ln, i, work, fake, warn, ref=None):
    from PIL import Image
    p = os.path.join(work, f"img{i:02d}.jpg")
    if fake:
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1024x1024", "-frames:v", "1", p])
    else:
        prompt = expand(ln["prompt"], spec); msgs = []
        ok = spec.get("image_model", "klein") == "klein" and gen_klein(prompt, 1000 + i, p, ref, msgs)
        if not ok:
            sys.path.insert(0, ROOT)
            from make_short import gen_image
            if msgs:
                warn.append(f"scene {i+1}: klein failed, used FLUX schnell ({msgs[-1][:120]})")
            if not gen_image(prompt, 1000 + i, p, msgs):
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

def title_card(im, title):
    """Hand-letter the episode title across the top of the first picture, in dark ink."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(im); w, h = im.size
    f, ls, size = fit(d, title, "PatrickHand-Regular.ttf", int(h * 0.13), int(h * 0.07), w * 0.86, 1)
    d.text((w / 2, h * 0.05), ls[0], font=f, fill=(28, 26, 24), anchor="mt")
    return im

CAP_SIZE = 72
CAP_TOP_GAP = 34   # space between the caption and the picture

def caption_chunks(lines, times, starts, lead):
    """Group each line into short caption chunks (fit 2 lines, break at punctuation) with word times."""
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f = font("Poppins-Black.ttf", CAP_SIZE); maxw = W - 2 * 80
    space = d.textlength(" ", font=f); lh = int(CAP_SIZE * 1.12)
    chunks = []
    for li, ln in enumerate(lines):
        ws = ln["text"].upper().split(); tms = [starts[li] + lead + t for t in times[li]]
        # one short line at a time: split at punctuation, then into even pieces of 2-5 words
        fits = lambda g: len(g) <= 5 and d.textlength(" ".join(g), font=f) <= maxw
        phrases, cur = [], []
        for w in ws:
            cur.append(w)
            if re.search(r"[,.!?;:]['\"”’]?$", w):
                phrases.append(cur); cur = []
        if cur:
            phrases.append(cur)
        merged = []
        for ph in phrases:  # a one-word phrase leans on its neighbor ("IT HISSED,")
            if merged and (len(ph) == 1 or len(merged[-1]) == 1) and fits(merged[-1] + ph):
                merged[-1] = merged[-1] + ph
            else:
                merged.append(ph)
        groups = []
        for ph in merged:
            n = 1
            while True:
                size = math.ceil(len(ph) / n)
                parts = [ph[j:j + size] for j in range(0, len(ph), size)]
                if all(fits(x) for x in parts) or n >= len(ph):
                    break
                n += 1
            groups += parts
        k = 0
        for g in groups:
            rows = wrap(d, " ".join(g), f, maxw)
            y0 = IMG_Y - CAP_TOP_GAP - lh * len(rows)
            placed = []; gi = 0
            for r, row in enumerate(rows):
                x = (W - d.textlength(row, font=f)) / 2
                for w in row.split():
                    placed.append((w, x, y0 + r * lh, tms[k + gi])); gi += 1
                    x += d.textlength(w, font=f) + space
            chunks.append({"words": placed, "start": tms[k]}); k += len(g)
    for i, c in enumerate(chunks):
        c["end"] = chunks[i + 1]["start"] if i + 1 < len(chunks) else 1e9
    return chunks, f

def draw_caption(frame, chunks, f, t, cache):
    from PIL import Image, ImageDraw
    c = next((c for c in chunks if c["start"] - 0.02 <= t < c["end"]), None)
    if not c:
        return frame
    for w, x, y, ws in c["words"]:
        a = (t - ws) / 0.16
        if a <= 0:
            continue
        spr = cache.get(w)
        if spr is None:
            bb = f.getbbox(w)
            spr = Image.new("L", (bb[2] + 8, int(CAP_SIZE * 1.4)), 0)
            ImageDraw.Draw(spr).text((0, 0), w, font=f, fill=255)
            cache[w] = spr
        mask = spr if a >= 1 else spr.point(lambda v, a=a: int(v * a))
        frame.paste((255, 255, 255), (int(x), int(y)), mask)
    return frame

# ---------------------------------------------------------------- frames
def render_video(images, scenes, chunks, cfont, out, work):
    from PIL import Image
    black = Image.new("RGB", (W, H), (0, 0, 0)); cache = {}
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
        f = black.copy(); f.paste(pic, (0, IMG_Y))
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
        draw_caption(f, chunks, cfont, t, cache)
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
        vpaths, wtimes = tts(lines, spec.get("voice", "andrew"), speed, work, check, warn)
        durs = [wav_frames(p)[1] for p in vpaths]
        scenes, lead = plan_timing(durs, warn)
        vo = build_audio(vpaths, scenes, lead, work)
        # scene 1 sets the characters; every later scene gets it as a reference picture
        images = [get_image(spec, lines[0], 0, work, check, warn)]
        ref = os.path.join(work, "img00.jpg")
        images += [get_image(spec, ln, i, work, check, warn, ref) for i, ln in enumerate(lines) if i > 0]
        if spec.get("title_card"):
            images[0] = title_card(images[0], str(spec["title_card"]))
        starts = [sum(scenes[:k]) for k in range(len(scenes))]
        chunks, cfont = caption_chunks(lines, wtimes, starts, lead)
        silent = os.path.join(work, "silent.mp4")
        total = render_video(images, scenes, chunks, cfont, silent, work)
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
            mv = float(spec.get("music_volume", 0.05))
            inputs += ["-i", mpath]
            af = (f"[2:a]volume={mv},aformat=sample_rates={SR}:channel_layouts=mono[m];"
                  f"[m][1:a]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[md];"
                  f"[1:a][md]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={total-0.8:.2f}:d=0.8[a]")
        else:
            af = f"[1:a]afade=t=out:st={total-0.6:.2f}:d=0.6[a]"
        kbps = int(max(400, min(4000, MAX_MB * 8192 / total - 128 - 30)))
        final = os.path.join(out_dir, f"{jid}.mp4")
        base = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"[0:v]fade=t=out:st={total-0.5:.2f}:d=0.5[v];{af}",
                "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-r", str(FPS),
                "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-tune", "animation",
                "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps*1.5)}k", "-bufsize", f"{kbps*3}k", "-pix_fmt", "yuv420p"]
        plog = os.path.join(work, "pass")
        run([*base, "-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", "/dev/null"])
        run([*base, "-pass", "2", "-passlogfile", plog, "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
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
