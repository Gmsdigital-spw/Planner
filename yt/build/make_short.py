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
  "voice": "am_michael", "speed": 1.08,
  "music_url": "https://.../track.wav", "music_volume": 0.16,
  "caption_words": 3,                                   # words per caption chunk
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
MAX_MB = 4.6
SR = 24000

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

def tts_edge(lines, voice, speed, workdir):
    # Free Microsoft neural voices. Used only if Kokoro is unavailable.
    import asyncio, edge_tts
    v = {"am_michael": "en-US-GuyNeural", "am_puck": "en-US-ChristopherNeural",
         "am_onyx": "en-US-DavisNeural", "af_heart": "en-US-AriaNeural"}.get(voice, "en-US-GuyNeural")
    rate = f"{int(round((speed - 1) * 100)):+d}%"
    paths = []
    async def one(text, out):
        await edge_tts.Communicate(text, v, rate=rate).save(out)
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

def build_voiceover(lines, voice, speed, workdir, warnings, fake=False):
    engines = [("fake", tts_fake)] if fake else [("kokoro", tts_kokoro), ("edge", tts_edge)]
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
        pause = float(ln.get("pause", 0.28))
        parts += ["-i", p, "-f", "lavfi", "-t", f"{pause:.2f}", "-i", f"anullsrc=r={SR}:cl=mono"]
        filt_inputs += [f"[{idx}:a]", f"[{idx+1}:a]"]
        idx += 2
        t += d + pause
    t += 0.6  # tail so the last word is not cut
    parts += ["-f", "lavfi", "-t", "0.6", "-i", f"anullsrc=r={SR}:cl=mono"]
    filt_inputs.append(f"[{idx}:a]")
    vo = os.path.join(workdir, "vo.wav")
    filt = "".join(filt_inputs) + f"concat=n={len(filt_inputs)}:v=0:a=1,loudnorm=I=-15:TP=-1.5:LRA=9[a]"
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

# ---------------------------------------------------------------- main
def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: make_short.py yt/jobs/<id>.json [--fake-tts]")
    spec_path = sys.argv[1]; fake = "--fake-tts" in sys.argv
    spec = json.load(open(spec_path))
    jid = spec["id"]; lines = spec["lines"]
    out_dir = os.path.join(os.path.dirname(os.path.dirname(spec_path)), "out")
    os.makedirs(out_dir, exist_ok=True)
    warnings = []; credits = []
    ensure_fonts()
    work = tempfile.mkdtemp(prefix=f"short-{jid}-")
    try:
        # 1. voice
        vo, windows, total, tts_used = build_voiceover(lines, spec.get("voice", "am_michael"),
                                             float(spec.get("speed", 1.08)), work, warnings, fake)
        # 2. word timings
        words = word_times(vo, lines, windows, warnings, fake)
        # 3. scenes: one per line; a line without a clip shares the previous clip
        scene_files = []; prev_clip = None
        for i, ln in enumerate(lines):
            s, e = windows[i]
            nxt = windows[i + 1][0] if i + 1 < len(lines) else total
            dur = nxt - s if i > 0 else nxt  # first scene starts at 0
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
                    if clip.get("credit"):
                        credits.append({"credit": clip["credit"], "page": clip.get("page", "")})
                except Exception as ex:
                    warnings.append(f"clip download failed for line {i}: {ex!r}")
            if not prev_clip:
                raise SystemExit(f"line {i} has no usable clip and nothing to reuse")
            scene_files.append(make_scene(prev_clip, dur, float(ln.get("start", 0)), i, work, 1 if i % 2 == 0 else -1))
        # 4. captions
        ass = os.path.join(work, "caps.ass"); build_ass(words, lines, windows, spec, total, ass)
        # 5. concat video, lay captions, mix audio
        lst = os.path.join(work, "list.txt")
        with open(lst, "w") as f:
            for sf in scene_files:
                f.write(f"file '{sf}'\n")
        joined = os.path.join(work, "joined.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
        music = spec.get("music_url"); mpath = None
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
                  f"[1:a][md]amix=inputs=2:duration=first:dropout_transition=0,afade=t=out:st={max(0,total-0.6):.2f}:d=0.6[a]")
        else:
            af = f"[1:a]afade=t=out:st={max(0,total-0.4):.2f}:d=0.4[a]"
        # bitrate to land under MAX_MB
        kbps = int(max(700, min(3200, MAX_MB * 8192 / total - 96 - 40)))
        final = os.path.join(out_dir, f"{jid}.mp4")
        base = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"[0:v]{vf}[v];{af}",
                "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-r", "30",
                "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-b:v", f"{kbps}k",
                "-maxrate", f"{int(kbps*1.3)}k", "-bufsize", f"{kbps*2}k", "-pix_fmt", "yuv420p"]
        plog = os.path.join(work, "pass")
        run([*base, "-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", "/dev/null"])
        run([*base, "-pass", "2", "-passlogfile", plog, "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
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
