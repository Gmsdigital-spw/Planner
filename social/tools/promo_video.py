import os, subprocess
from PIL import Image, ImageDraw, ImageFont

import sys
S = os.environ.get("WORK") or sys.exit("set WORK=<work folder>")
MUSIC = os.environ.get("MUSIC") or sys.exit("set MUSIC=<wav from yt/build/music.py>")
F = f"{S}/frames"
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FONT_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
if not os.path.exists(FONT_B): FONT_B = FONT

def caption(name, lines, y, size=64, small=None):
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_B, size)
    fs = ImageFont.truetype(FONT, int(size * 0.72))
    rows = [(l, f) for l in lines] + ([(small, fs)] if small else [])
    pad_x, pad_y, gap = 44, 30, 14
    widths = [d.textbbox((0, 0), t, font=ft)[2] for t, ft in rows]
    heights = [ft.getbbox("Ag")[3] for t, ft in rows]
    bw = max(widths) + pad_x * 2
    bh = sum(heights) + gap * (len(rows) - 1) + pad_y * 2
    x0 = (1080 - bw) // 2
    d.rounded_rectangle([x0 + 6, y + 10, x0 + bw + 6, y + bh + 10], 34, fill=(40, 20, 5, 70))
    d.rounded_rectangle([x0, y, x0 + bw, y + bh], 34, fill=(250, 244, 233, 245))
    cy = y + pad_y
    for (t, ft), w, h in zip(rows, widths, heights):
        col = (43, 33, 27, 255) if ft is f else (176, 82, 44, 255)
        d.text(((1080 - w) // 2, cy - 4), t, font=ft, fill=col)
        cy += h + gap
    img.save(f"{F}/cap_{name}.png")

caption("s1", ["First time hosting", "Thanksgiving?"], 150, 76)
caption("s2", ["Pick your dinner time.", "It tells you when", "the turkey goes in."], 1420, 64)
caption("s3a", ["3-week countdown"], 150)
caption("s3b", ["Turkey size + thaw guide"], 150)
caption("s3c", ["Grocery list by store aisle"], 150)
caption("s4", ["13 printable pages"], 170, 72, "Instant download · link in bio")

# (still, caption, seconds, motion)
SEG = [("s1", 3.0, "zin"), ("s2", 4.0, "pan"), ("s3a", 1.5, "zin"), ("s3b", 1.5, "zin"),
       ("s3c", 1.5, "zin"), ("s4", 4.3, "zout")]
FPS = 30
parts = []
for i, (n, sec, mo) in enumerate(SEG):
    fr = int(sec * FPS)
    if mo == "zin":
        z = f"zoom='1+0.07*on/{fr}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
    elif mo == "zout":
        z = f"zoom='1.08-0.07*on/{fr}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
    else:
        z = f"zoom='1.06':x='iw*0.01':y='(ih-ih/zoom)*(0.05+0.9*on/{fr})'"
    out = f"{F}/seg{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f"{F}/{n}.png", "-loop", "1", "-i", f"{F}/cap_{n}.png",
        "-filter_complex",
        f"[0]scale=2430:4320,zoompan={z}:d={fr}:s=1080x1920:fps={FPS}[v];"
        f"[1]format=rgba,fade=in:st=0:d=0.25:alpha=1[c];[v][c]overlay=0:0,format=yuv420p",
        "-t", str(sec), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "19", out], check=True)
    parts.append((out, sec))

# join with short crossfades
X = 0.2
inputs, fc, prev, off = [], "", "0:v", 0.0
for i, (p, sec) in enumerate(parts):
    inputs += ["-i", p]
for i in range(1, len(parts)):
    off += parts[i - 1][1] - X
    lab = f"v{i}"
    fc += f"[{prev}][{i}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[{lab}];"
    prev = lab
total = sum(s for _, s in parts) - X * (len(parts) - 1)
ai = len(parts)
fc += (f"[{ai}:a]atrim=0:{total:.3f},afade=t=in:d=0.4,afade=t=out:st={total-1.2:.3f}:d=1.2,"
       f"aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-i", MUSIC,
    "-filter_complex", fc, "-map", f"[{prev}]", "-map", "[a]",
    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "4500k", "-bufsize", "9000k",
    "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-ar", "48000", "-b:a", "160k",
    "-movflags", "+faststart", f"{S}/video.mp4"], check=True)
# cover = s1 frame with caption
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.2", "-i", f"{S}/video.mp4", "-frames:v", "1", "-q:v", "3", f"{S}/cover.jpg"], check=True)
print("total", total)
