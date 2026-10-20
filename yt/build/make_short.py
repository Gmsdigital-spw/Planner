#!/usr/bin/env python3
"""
YouTube Starship — free Short builder.

Turns one job spec (yt/jobs/<id>.json) into a finished 9:16 Short at yt/out/<id>.mp4
plus yt/out/<id>.json (duration, size, credits, word timings, any warnings).

Everything here is free: Kokoro TTS (Apache-2) with edge-tts as a fallback,
faster-whisper for word timings, Pexels footage (direct clip URLs from the spec,
or a Pexels search when PEXELS_API_KEY is set), and ffmpeg for the edit.

Spec (all keys optional except id + lines):
{
  "id": "ep11",
  "hook": "MY DAD SAID GAMES ARE A WASTE OF MONEY",   # top text for the first ~3s
  "end_text": "Part 2?",                                # shown at the very end
  "voice": "andrew", "speed": 1.03,                     # voices: andrew, brian, ava, emma, christopher, jenny
  "engine": "edge",                                     # "edge" (natural story voice, default) or "kokoro"
  "music_url": "https://.../track.wav", "music_volume": 0.16,
  "caption_words": 3,                                   # words per caption chunk
  "loop": true,                                         # default: end cuts hard back to the start (Shorts loop)
  "lines": [
    {"text": "My dad said games are a waste of money.",
     "clip": {"url": "https://videos.pexels.com/....mp4", "credit": "Name", "page": "https://www.pexels.com/video/..."},
     "query": "dad disappointed looking at son",      # used if clip missing and PEXELS_API_KEY set
     "label": "3 WEEKS LATER",                          # yellow top label for this line
     "start": 1.5,                                      # trim-in seconds inside the clip
     "pause": 0.35}                                     # extra silence after this line
  ]
}
"""
import json, os, re, shutil, subprocess, sys, tempfile, urllib.request, urllib.parse, wave, math, html

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(ROOT, "fonts")
W, H = 1080, 1920          # render size
OUT_W, OUT_H = 720, 1280   # delivered size (keeps the file under Make's 5 MB limit)
MAX_MB = 4.45
SR = 24000
# Clearer narration: cut rumble, thin the boxy low-mids, lift presence, even out the level.
VOICE_FX = ("highpass=f=75,equalizer=f=280:t=q:w=1.1:g=-2.5,equalizer=f=3200:t=q:w=1.3:g=3,"
            "equalizer=f=9000:t=q:w=1:g=1.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=2")
MUSIC_MOODS = ("emotional", "tense", "uplifting", "cozy")

def run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, check=True, **kw)

def ffprobe_dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip()
    return float(out)

def wav_dur(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()

# ---------------------------------------------------------------- fonts
def ensure_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    wanted = {
        "Poppins-Black.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Black.ttf",
        "Poppins-ExtraBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-ExtraBold.ttf",
    }
    for name, url in wanted.items():
        p = os.path.join(FONT_DIR, name)
        if not os.path.exists(p):
            try:
                urllib.request.urlretrieve(url, p)
            except Exception as e:
                print("font download failed", name, e)
    return os.path.exists(os.path.join(FONT_DIR, "Poppins-Black.ttf"))

# ---------------------------------------------------------------- TTS
def tts_kokoro(lines, voice, speed, workdir):
    from kokoro import KPipeline
    import soundfile as sf, numpy as np
    voice = KOKORO_VOICES.get(voice, voice if voice.startswith(("am_", "af_", "bm_", "bf_")) else "am_michael")
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    paths = []
    for i, ln in enumerate(lines):
        chunks = []
        for _, _, audio in pipe(ln["text"], voice=voice, speed=speed, split_pattern=r"\n+"):
            chunks.append(np.asarray(audio, dtype="float32"))
        audio = np.concatenate(chunks) if chunks else np.zeros(SR // 10, dtype="float32")
        p = os.path.join(workdir, f"line{i:02d}.wav")
        sf.write(p, audio, SR)
        paths.append(p)
    return paths

EDGE_VOICES = {  # storytelling voices people hear in TikTok/Reddit story videos
    "andrew": "en-US-AndrewMultilingualNeural", "brian": "en-US-BrianMultilingualNeural",
    "ava": "en-US-AvaMultilingualNeural", "emma": "en-US-EmmaMultilingualNeural",
    "christopher": "en-US-ChristopherNeural", "jenny": "en-US-JennyNeural",
    "am_michael": "en-US-AndrewMultilingualNeural", "am_puck": "en-US-BrianMultilingualNeural",
    "am_onyx": "en-US-ChristopherNeural", "af_heart": "en-US-AvaMultilingualNeural",
}
KOKORO_VOICES = {"andrew": "am_michael", "brian": "am_puck", "ava": "af_heart", "emma": "af_bella",
                 "christopher": "am_onyx", "jenny": "af_nicole"}

def tts_edge(lines, voice, speed, workdir):
    # Free Microsoft neural voices (edge-tts): natural, story-style delivery.
    import asyncio, edge_tts
    v = EDGE_VOICES.get(voice, voice if "Neural" in voice else "en-US-AndrewMultilingualNeural")
    rate = f"{int(round((speed - 1) * 100)):+d}%"
    paths = []
    async def one(text, out):
        await asyncio.wait_for(edge_tts.Communicate(text, v, rate=rate).save(out), timeout=45)
    for i, ln in enumerate(lines):
        mp3 = os.path.join(workdir, f"line{i:02d}.mp3")
        asyncio.run(one(ln["text"], mp3))
        p = os.path.join(workdir, f"line{i:02d}.wav")
        run(["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", str(SR), "-ac", "1", p])
        paths.append(p)
    return paths

def tts_fake(lines, voice, speed, workdir):
    # Silence sized to the text, for local tests only.
    paths = []
    for i, ln in enumerate(lines):
        secs = max(0.8, 0.33 * len(ln["text"].split()))
        p = os.path.join(workdir, f"line{i:02d}.wav")
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono",
             "-t", f"{secs:.2f}", p])
        paths.append(p)
    return paths

def build_voiceover(lines, voice, speed, workdir, warnings, fake=False, loop=False, engine="edge"):
    order = [("edge", tts_edge), ("kokoro", tts_kokoro)] if engine == "edge" else [("kokoro", tts_kokoro), ("edge", tts_edge)]
    engines = [("fake", tts_fake)] if fake else order
    paths = None; used = None
    for name, fn in engines:
        try:
            paths = fn(lines, voice, speed, workdir); used = name
            print("TTS engine:", name)
            break
        except Exception as e:
            warnings.append(f"TTS {name} failed: {e!r}")
            print("TTS failed", name, e)
    if not paths:
        raise SystemExit("no TTS engine worked")
    # Concatenate with pauses, keep each line's time window.
    t = 0.35  # lead-in before the first word
    windows = []
    parts = ["-f", "lavfi", "-t", "0.35", "-i", f"anullsrc=r={SR}:cl=mono"]
    filt_inputs = ["[0:a]"]
    idx = 1
    for i, (p, ln) in enumerate(zip(paths, lines)):
        d = wav_dur(p)
        windows.append((t, t + d))
        pause = max(0.05, float(ln.get("pause", 0.28)))  # a 0 s silence never ends in ffmpeg
        parts += ["-i", p, "-f", "lavfi", "-t", f"{pause:.2f}", "-i", f"anullsrc=r={SR}:cl=mono"]
        filt_inputs += [f"[{idx}:a]", f"[{idx+1}:a]"]
        idx += 2
        t += d + pause
    tail = 0.12 if loop else 0.6  # a loop cuts straight back to the first word
    t += tail
    parts += ["-f", "lavfi", "-t", f"{tail:.2f}", "-i", f"anullsrc=r={SR}:cl=mono"]
    filt_inputs.append(f"[{idx}:a]")
    vo = os.path.join(workdir, "vo.wav")
    filt = "".join(filt_inputs) + f"concat=n={len(filt_inputs)}:v=0:a=1,{VOICE_FX},loudnorm=I=-15:TP=-1.5:LRA=9[a]"
    run(["ffmpeg", "-v", "error", "-y", *parts, "-filter_complex", filt, "-map", "[a]", "-ar", str(SR), vo])
    return vo, windows, t, used

# ---------------------------------------------------------------- word timing
def word_times(vo_path, lines, windows, warnings, fake=False):
    """Return a list of {w, s, e, line} for every spoken word."""
    words = []
    if not fake:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base.en", device="cpu", compute_type="int8")
            segs, _ = model.transcribe(vo_path, word_timestamps=True, beam_size=3, vad_filter=False)
            heard = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
            # Map heard words onto the script line by line (script text wins, timings from whisper).
            hi = 0
            for li, (ln, (ws, we)) in enumerate(zip(lines, windows)):
                toks = ln["text"].split()
                for tk in toks:
                    if hi < len(heard):
                        _, s, e = heard[hi]; hi += 1
                        s = min(max(s, ws), we); e = min(max(e, s + 0.05), we + 0.3)
                    else:
                        s, e = ws, we
                    words.append({"w": tk, "s": round(s, 3), "e": round(e, 3), "line": li})
            if abs(len(heard) - sum(len(l["text"].split()) for l in lines)) > max(3, 0.25 * len(words)):
                warnings.append("whisper word count differs a lot from the script; captions timed evenly")
                words = []
        except Exception as e:
            warnings.append(f"whisper failed: {e!r}; captions timed evenly")
            words = []
    if not words:
        for li, (ln, (ws, we)) in enumerate(zip(lines, windows)):
            toks = ln["text"].split()
            weights = [max(1, len(re.sub(r"[^A-Za-z0-9']", "", t))) + 1 for t in toks]
            tot = sum(weights); cur = ws
            for tk, wt in zip(toks, weights):
                d = (we - ws) * wt / tot
                words.append({"w": tk, "s": round(cur, 3), "e": round(cur + d, 3), "line": li})
                cur += d
    return words

# ---------------------------------------------------------------- footage
def pexels_search(query, min_dur):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    q = urllib.parse.quote(query)
    req = urllib.request.Request(
        f"https://api.pexels.com/videos/search?query={q}&orientation=portrait&per_page=8",
        headers={"Authorization": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    best = None
    for v in data.get("videos", []):
        if v.get("duration", 0) < max(2, min_dur - 0.5):
            continue
        files = [f for f in v.get("video_files", []) if f.get("height") and f.get("width")
                 and f["height"] >= f["width"] and f["height"] >= 1280]
        if not files:
            continue
        files.sort(key=lambda f: abs(f["height"] - 1920))
        best = {"url": files[0]["link"], "credit": v.get("user", {}).get("name", ""),
                "page": v.get("url", ""), "duration": v.get("duration")}
        break
    return best

def fetch_clip(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (YouTube Starship builder)"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)

def make_scene(clip_path, dur, start, idx, workdir, drift_dir):
    """Normalize a clip to WxH for exactly `dur` seconds, muted, with a slow drift."""
    out = os.path.join(workdir, f"scene{idx:02d}.mp4")
    src_dur = ffprobe_dur(clip_path)
    loop = ["-stream_loop", "-1"] if src_dur - start < dur + 0.2 else []
    # scale up 6% so the slow drift never shows an edge; drift ~40px over the scene
    drift = 40 if drift_dir > 0 else -40
    vf = (f"scale={W*1.06:.0f}:{H*1.06:.0f}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H}:x='(iw-{W})/2 + {drift}*(t/{max(dur,0.1):.3f}) - {drift/2}':y='(ih-{H})/2',"
          f"setsar=1,fps=30,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", *loop, "-ss", f"{start:.2f}", "-i", clip_path, "-t", f"{dur:.3f}",
         "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])
    return out

# ---------------------------------------------------------------- AI cartoon images (free)
def expand_prompt(prompt, spec):
    for k, v in (spec.get("cast") or {}).items():
        prompt = prompt.replace("{" + k + "}", v)
    style = spec.get("style", "")
    return f"{prompt}. {style}".strip()

def gen_image(prompt, seed, dest, warnings):
    """Free text-to-image: Cloudflare Workers AI FLUX.1 schnell (free daily allowance).
    Needs CF_ACCOUNT_ID + CF_API_TOKEN. Returns True on success."""
    import time, base64
    acct = os.environ.get("CF_ACCOUNT_ID", "").strip(); tok = os.environ.get("CF_API_TOKEN", "").strip()
    if not (acct and tok):
        warnings.append("no Cloudflare keys (CF_ACCOUNT_ID / CF_API_TOKEN), cannot make cartoon images")
        return False
    import hashlib
    cache_dir = os.environ.get("IMG_CACHE", "/tmp/yt-img-cache"); os.makedirs(cache_dir, exist_ok=True)
    cached = os.path.join(cache_dir, hashlib.sha1(prompt.encode()).hexdigest() + ".jpg")
    if os.path.exists(cached) and os.path.getsize(cached) > 20000:
        shutil.copy(cached, dest)  # a retry reuses images it already paid for
        return True
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    body = json.dumps({"prompt": prompt[:2000], "steps": 8}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=body, method="POST",
                                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            b64 = (d.get("result") or {}).get("image")
            if b64:
                open(dest, "wb").write(base64.b64decode(b64))
                if os.path.getsize(dest) > 20000:
                    shutil.copy(dest, cached)
                    return True
            warnings.append(f"image try {attempt+1}: no image ({str(d.get('errors'))[:120]})")
        except Exception as e:
            msg = ""
            try:
                msg = e.read().decode()[:160]
            except Exception:
                pass
            warnings.append(f"image try {attempt+1} failed: {e!r} {msg}"[:220])
            if "daily free allocation" in msg or "neurons" in msg:
                warnings.append("Cloudflare free image allowance used up for today (resets 00:00 UTC)")
                return False
            if "NSFW" in msg and not prompt.startswith("wholesome"):
                prompt = "wholesome family-friendly kids animated movie scene, " + prompt.replace("bathrobe", "cozy pajamas").replace("bed", "couch")
                body = json.dumps({"prompt": prompt[:2000], "steps": 8}).encode()
        time.sleep(3 + attempt * 6)
    return False

def make_image_scene(img, dur, idx, workdir, motion):
    """Turn a still into a moving shot: push, pull, pan, punch (zoom hit + shake)."""
    out = os.path.join(workdir, f"scene{idx:02d}.mp4")
    n = max(2, int(round(dur * 30)))
    if motion == "pull":
        z = f"1.14-0.12*on/{n}"
    elif motion in ("panl", "panr"):
        z = "1.16"
    elif motion == "punch":
        z = f"if(lt(on,8),1.30-0.03*on,1.06+0.06*on/{n})"
    else:  # push
        z = f"1.0+0.13*on/{n}"
    cx = "iw/2-(iw/zoom/2)"; cy = "ih/2-(ih/zoom/2)"
    if motion == "panl":
        cx = f"(iw-iw/zoom)*(1-on/{n})"
    elif motion == "panr":
        cx = f"(iw-iw/zoom)*on/{n}"
    if motion == "punch":
        cx += "+if(lt(on,14),14*sin(on*2.3),0)"; cy += "+if(lt(on,14),10*cos(on*2.9),0)"
    vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='{z}':x='{cx}':y='{cy}':d={n}:s={W}x{H}:fps=30,setsar=1,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-i", img, "-vf", vf, "-frames:v", str(n),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])
    return out

# ---------------------------------------------------------------- captions (ASS)
def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def esc(s):
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

def build_ass(words, lines, windows, spec, total, path):
    per = int(spec.get("caption_words", 3))
    hook = spec.get("hook"); end_text = spec.get("end_text")
    cap_font = "Poppins Black" if os.path.exists(os.path.join(FONT_DIR, "Poppins-Black.ttf")) else "DejaVu Sans"
    ev = []
    # Word-by-word captions: chunk of `per` words, active word yellow + slightly bigger.
    # Chunks never cross a line boundary.
    for li in range(len(lines)):
        lw = [w for w in words if w["line"] == li]
        for c in range(0, len(lw), per):
            chunk = lw[c:c + per]
            for k, w in enumerate(chunk):
                parts = []
                for j, x in enumerate(chunk):
                    txt = esc(x["w"].upper())
                    if j == k:
                        parts.append("{\\c&H00E5FF&\\fscx108\\fscy108}" + txt + "{\\c&HFFFFFF&\\fscx100\\fscy100}")
                    else:
                        parts.append(txt)
                s = w["s"]; e = chunk[k + 1]["s"] if k + 1 < len(chunk) else max(w["e"], w["s"] + 0.12)
                if k == len(chunk) - 1:
                    e = max(e, w["e"] + 0.05)
                    nxt = lw[c + per]["s"] if c + per < len(lw) else None
                    if nxt is not None:
                        e = min(e, nxt - 0.01)
                ev.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{' '.join(parts)}")
    # Hook on top for the first line's window + a little.
    if hook:
        e = min(total, max(windows[0][1] + 0.4, 2.8))
        ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(e)},Hook,,0,0,0,,{{\\fad(120,200)}}{esc(hook.upper())}")
    # Time-jump / section labels per line.
    for li, ln in enumerate(lines):
        lab = ln.get("label")
        if lab:
            s, e = windows[li]
            s0 = max(0, s - 0.25)
            ev.append(f"Dialogue: 2,{ass_time(s0)},{ass_time(min(total, e + 0.3))},Label,,0,0,0,,{{\\fad(100,150)}}{esc(lab.upper())}")
    if end_text:
        s = max(0, total - 1.6)
        ev.append(f"Dialogue: 3,{ass_time(s)},{ass_time(total)},End,,0,0,0,,{{\\fad(150,0)}}{esc(end_text)}")
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{cap_font},88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,8,3,2,70,70,600,1
Style: Hook,{cap_font},76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,8,90,90,230,1
Style: Label,{cap_font},68,&H0000E5FF,&H0000E5FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,8,90,90,230,1
Style: End,{cap_font},104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,8,4,8,90,90,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w") as f:
        f.write(header + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- spec check
def clean_spec(spec, warnings):
    """Repair everything that can be repaired; raise only on things that cannot."""
    if not spec.get("id") or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", str(spec["id"])):
        raise SystemExit("spec id missing or invalid")
    lines = [l for l in spec.get("lines", []) if isinstance(l, dict) and str(l.get("text", "")).strip()]
    if not 3 <= len(lines) <= 22:
        raise SystemExit(f"need 3-22 lines with text, got {len(lines)}")
    for i, l in enumerate(lines):
        l["text"] = re.sub(r"\s+", " ", str(l["text"])).strip()
        try:
            l["pause"] = min(1.5, max(0.05, float(l.get("pause", 0.28))))
        except Exception:
            l["pause"] = 0.28
        try:
            l["start"] = max(0.0, float(l.get("start", 0)))
        except Exception:
            l["start"] = 0.0
        c = l.get("clip")
        if c is not None and (not isinstance(c, dict) or not str(c.get("url", "")).startswith(("https://", "lavfi:"))):
            warnings.append(f"line {i} clip dropped (bad url)"); l.pop("clip", None)
        elif c and "_360_640" in c["url"]:
            warnings.append(f"line {i} clip is 360p; consider a sharper one")
    if not any(l.get("clip") or l.get("image") for l in lines) and not any(l.get("query") for l in lines):
        raise SystemExit("no clips at all")
    if lines[0].get("image"):
        pass
    elif any(l.get("image") for l in lines):
        lines[0]["image"] = next(l["image"] for l in lines if l.get("image"))
    # the first line must have footage; borrow the first available clip
    elif not lines[0].get("clip"):
        lines[0]["clip"] = next(l["clip"] for l in lines if l.get("clip"))
    spec["lines"] = lines
    try:
        spec["speed"] = min(1.25, max(0.85, float(spec.get("speed", 1.03))))
    except Exception:
        spec["speed"] = 1.03
    return spec

# ---------------------------------------------------------------- main
def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: make_short.py yt/jobs/<id>.json [--fake-tts]")
    spec_path = sys.argv[1]; fake = "--fake-tts" in sys.argv or "--check" in sys.argv
    spec = json.load(open(spec_path))
    pre_warn = []
    spec = clean_spec(spec, pre_warn)
    if "--check" in sys.argv:
        # Dry run: same spec, synthetic footage + silent voice, to catch hangs/crashes before the real build.
        fake = True
        for i, l in enumerate(spec["lines"]):
            if not l.get("image"):
                l["clip"] = {"url": "lavfi:testsrc2=size=720x1280:rate=30" if i % 2 else "lavfi:smptebars=size=1080x1920:rate=30"}
        spec["id"] = spec["id"] + "-check"
    jid = spec["id"]; lines = spec["lines"]
    out_dir = os.path.join(os.path.dirname(os.path.dirname(spec_path)), "out")
    if "--check" in sys.argv:
        out_dir = tempfile.mkdtemp(prefix="check-")
    os.makedirs(out_dir, exist_ok=True)
    warnings = list(pre_warn); credits = []
    ensure_fonts()
    work = tempfile.mkdtemp(prefix=f"short-{jid}-")
    try:
        # 1. voice
        loop = bool(spec.get("loop", True))
        vo, windows, total, tts_used = build_voiceover(lines, spec.get("voice", "andrew"),
                                             float(spec.get("speed", 1.03)), work, warnings, fake, loop,
                                             spec.get("engine", "edge"))
        # 2. word timings
        words = word_times(vo, lines, windows, warnings, fake)
        # 3. scenes: one per line; a line without a clip shares the previous clip
        scene_files = []; scene_durs = []; prev_clip = None; prev_img = None; credits_ai = False
        XF = 0.3 if (any(l.get("image") for l in lines) and spec.get("transition", "dissolve") == "dissolve") else 0.0
        for i, ln in enumerate(lines):
            s, e = windows[i]
            nxt = windows[i + 1][0] if i + 1 < len(lines) else total
            dur = nxt - s if i > 0 else nxt  # first scene starts at 0
            if ln.get("image"):
                im = ln["image"]; ip = os.path.join(work, f"img{i:02d}.jpg")
                ok = False
                if fake:
                    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1080x1920", "-frames:v", "1", ip]); ok = True
                else:
                    ok = gen_image(expand_prompt(im.get("prompt", ln["text"]), spec), im.get("seed", 1000 + i), ip, warnings)
                if ok:
                    prev_img = ip
                else:
                    img_fail = globals().get("_img_fail", 0) + 1; globals()["_img_fail"] = img_fail
                    if img_fail > 2 or not prev_img:
                        raise SystemExit("cartoon images failed (" + "; ".join(warnings[-2:]) + "); not shipping a half-made video")
                    warnings.append(f"line {i}: image failed, reused previous image")
                motions = ["push", "panr", "pull", "panl"]
                mo = im.get("motion") or motions[i % 4]
                sdur = dur + (XF if i < len(lines) - 1 else 0.0)
                outp = os.path.join(work, f"scene{i:02d}.mp4")
                try:
                    if fake:
                        raise RuntimeError("dry run uses the quick zoom")
                    sys.path.insert(0, ROOT)
                    import motion as _motion
                    _motion.render(prev_img, outp, sdur, mo, W=W, H=H, seed=i)
                    scene_files.append(outp)
                except Exception as ex:
                    if not fake:
                        warnings.append(f"line {i}: 3D motion failed ({ex!r}); used simple zoom")
                    scene_files.append(make_image_scene(prev_img, sdur, i, work, mo if mo != "orbit" else "push"))
                scene_durs.append(sdur)
                credits_ai = True
                continue
            clip = ln.get("clip")
            if not clip and ln.get("query") and not fake:
                try:
                    clip = pexels_search(ln["query"], dur)
                except Exception as ex:
                    warnings.append(f"pexels search failed for line {i}: {ex!r}")
            if clip and clip.get("url"):
                cp = os.path.join(work, f"clip{i:02d}.mp4")
                try:
                    if fake and clip["url"].startswith("lavfi:"):
                        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", clip["url"][6:], "-t", "6",
                             "-pix_fmt", "yuv420p", cp])
                    else:
                        fetch_clip(clip["url"], cp)
                    prev_clip = cp
                    try:
                        hh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height",
                                             "-of", "csv=p=0", cp], capture_output=True, text=True).stdout.strip()
                        if hh and int(hh.split(",")[0]) < 960:
                            warnings.append(f"line {i} clip is low resolution ({hh}p); looks soft")
                    except Exception:
                        pass
                    if clip.get("credit"):
                        credits.append({"credit": clip["credit"], "page": clip.get("page", "")})
                except Exception as ex:
                    warnings.append(f"clip download failed for line {i}: {ex!r}")
            if not prev_clip:
                raise SystemExit(f"line {i} has no usable clip and nothing to reuse")
            sdur = dur + (XF if i < len(lines) - 1 else 0.0)
            scene_files.append(make_scene(prev_clip, sdur, float(ln.get("start", 0)), i, work, 1 if i % 2 == 0 else -1))
            scene_durs.append(sdur)
        # 4. captions
        ass = os.path.join(work, "caps.ass"); build_ass(words, lines, windows, spec, total, ass)
        # 5. concat video, lay captions, mix audio
        lst = os.path.join(work, "list.txt")
        with open(lst, "w") as f:
            for sf in scene_files:
                f.write(f"file '{sf}'\n")
        joined = os.path.join(work, "joined.mp4")
        if XF > 0 and len(scene_files) > 1:
            ins = []
            for sf in scene_files:
                ins += ["-i", sf]
            chain = []; prev = "[0:v]"; off = 0.0
            for k in range(1, len(scene_files)):
                off += scene_durs[k - 1] - XF
                lab = f"[x{k}]"
                chain.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}{lab}")
                prev = lab
            run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(chain), "-map", prev,
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", joined])
        else:
            run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
        music = spec.get("music_url"); mpath = None
        mood = str(spec.get("music", "emotional")).lower()
        if not music and not fake and mood in MUSIC_MOODS:
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                import music as _music
                mpath = os.path.join(work, "music.wav")
                seed = sum(ord(c) for c in jid) % 1000
                _music.write_wav(mpath, _music.make(mood, total + 1.5, seed))
                spec.setdefault("music_volume", 0.13)
            except Exception as ex:
                warnings.append(f"music generation failed: {ex!r}"); mpath = None
        if music and not fake:
            try:
                mpath = os.path.join(work, "music"); fetch_clip(music, mpath)
            except Exception as ex:
                warnings.append(f"music download failed: {ex!r}"); mpath = None
        inputs = ["-i", joined, "-i", vo]
        vf = f"subtitles='{ass}':fontsdir='{FONT_DIR}',scale={OUT_W}:{OUT_H}:flags=lanczos"
        if mpath:
            mv = float(spec.get("music_volume", 0.16))
            inputs += ["-stream_loop", "-1", "-i", mpath]
            af = (f"[2:a]volume={mv},aformat=sample_rates={SR}:channel_layouts=mono[m];"
                  f"[m][1:a]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[md];"
                  f"[1:a][md]amix=inputs=2:duration=first:dropout_transition=0:normalize=0" + ("" if loop else f",afade=t=out:st={max(0,total-0.6):.2f}:d=0.6") + "[a]")
        else:
            af = f"[1:a]anull[a]" if loop else f"[1:a]afade=t=out:st={max(0,total-0.4):.2f}:d=0.4[a]"
        # bitrate to land under MAX_MB
        kbps = int(max(420, min(3200, MAX_MB * 8192 / total - 80 - 48)))
        final = os.path.join(out_dir, f"{jid}.mp4")
        base = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"[0:v]{vf}[v];{af}",
                "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-r", "30",
                "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-b:v", f"{kbps}k",
                "-maxrate", f"{int(kbps*1.3)}k", "-bufsize", f"{kbps*2}k", "-pix_fmt", "yuv420p"]
        plog = os.path.join(work, "pass")
        run([*base, "-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", "/dev/null"])
        run([*base, "-pass", "2", "-passlogfile", plog, "-c:a", "aac", "-b:a", "80k", "-ar", "44100",
             "-movflags", "+faststart", final])
        size = os.path.getsize(final)
        meta = {"id": jid, "duration": round(ffprobe_dur(final), 2), "bytes": size, "mb": round(size / 1048576, 2),
                "width": OUT_W, "height": OUT_H, "words": words, "lines": windows, "credits": credits,
                "warnings": warnings, "fakeTts": fake, "tts": tts_used}
        json.dump(meta, open(os.path.join(out_dir, f"{jid}.json"), "w"), indent=1)
        print(json.dumps({k: v for k, v in meta.items() if k not in ("words", "lines")}, indent=1))
        if size > MAX_MB * 1048576 * 1.02:
            warnings.append("file is over the 4.6 MB target")
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    main()
