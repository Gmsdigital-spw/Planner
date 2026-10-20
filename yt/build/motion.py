"""
Living-picture motion for cartoon scenes (free, CPU only).

Turns one still into a moving shot:
  - 3D parallax: a depth map splits the scene into layers, so the character slides
    against the background as the camera moves (like a real camera move).
  - Breathing / idle sway: the character (near layers) gently rises and falls.
  - Camera moves: push (dolly in), pull, panl, panr, punch (zoom hit + shake), orbit.

Depth comes from Depth-Anything-V2-Small (free model, runs on CPU in a few seconds).
If the model is not available, a soft "subject in the middle" depth guess is used.
"""
import os, subprocess, math
import numpy as np
import cv2

_DEPTH = None


def _depth_model():
    global _DEPTH
    if _DEPTH is None:
        try:
            from transformers import pipeline
            _DEPTH = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")
        except Exception as e:  # noqa
            print("depth model unavailable:", e)
            _DEPTH = False
    return _DEPTH


def depth_map(img_bgr):
    """0 = far, 1 = near, same size as img."""
    h, w = img_bgr.shape[:2]
    m = _depth_model()
    if m:
        try:
            from PIL import Image
            pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
            d = np.array(m(pil)["depth"], dtype=np.float32)
            d = cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)
            d = (d - d.min()) / max(1e-6, d.max() - d.min())
            return cv2.GaussianBlur(d, (0, 0), 3)
        except Exception as e:
            print("depth failed:", e)
    # fallback: subject in the middle and lower half is nearer
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h * 0.55
    r = np.sqrt(((xx - cx) / (w * 0.45)) ** 2 + ((yy - cy) / (h * 0.45)) ** 2)
    d = np.clip(1.0 - r, 0, 1) * 0.8 + (yy / h) * 0.2
    return cv2.GaussianBlur(d.astype(np.float32), (0, 0), 25)


def render(img_path, out_path, dur, motion="push", W=1080, H=1920, fps=30, seed=0):
    img = cv2.imread(img_path)
    if img is None:
        raise RuntimeError("cannot read " + img_path)
    # cover W x H with a margin so moves never show an edge
    margin = 1.18
    sh, sw = img.shape[:2]
    s = max(W * margin / sw, H * margin / sh)
    big = cv2.resize(img, (int(sw * s + 0.5), int(sh * s + 0.5)), interpolation=cv2.INTER_LANCZOS4)
    bh, bw = big.shape[:2]
    depth = depth_map(big)
    near = np.clip((depth - 0.45) / 0.55, 0, 1).astype(np.float32)  # where the character is
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ox, oy = (bw - W) / 2.0, (bh - H) / 2.0
    n = max(2, int(round(dur * fps)))
    rng = np.random.default_rng(seed)
    phase = rng.uniform(0, math.tau)
    # sample depth in output space once (for parallax strength)
    d_out = cv2.resize(depth[int(oy):int(oy) + H, int(ox):int(ox) + W], (W, H))
    n_out = cv2.resize(near[int(oy):int(oy) + H, int(ox):int(ox) + W], (W, H))
    cxo, cyo = W / 2.0, H * 0.5

    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
                             "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out_path],
                            stdin=subprocess.PIPE)
    for i in range(n):
        t = i / (n - 1)
        e = t * t * (3 - 2 * t)  # ease in-out
        # camera: zoom (z), pan (px, py) in output pixels
        z, px, py, shake = 1.0, 0.0, 0.0, 0.0
        if motion == "push":
            z = 1.0 + 0.10 * e
        elif motion == "pull":
            z = 1.10 - 0.10 * e
        elif motion == "panl":
            px = 70 * (e - 0.5); z = 1.04
        elif motion == "panr":
            px = -70 * (e - 0.5); z = 1.04
        elif motion == "orbit":
            px = 55 * math.sin(e * math.pi - math.pi / 2); z = 1.03 + 0.03 * e
        elif motion == "punch":
            k = min(1.0, i / 7.0)
            z = 1.22 - 0.16 * (k * k * (3 - 2 * k)) + 0.03 * e
            shake = max(0.0, 1 - i / 14.0)
        # parallax: near pixels move more with the camera than far ones
        par = (d_out - 0.5)
        sx = px * (0.6 + 1.4 * par)
        sy = py * (0.6 + 1.4 * par)
        zz = 1.0 + (z - 1.0) * (0.7 + 0.8 * d_out)   # near layers zoom more = depth
        # breathing / idle sway on the character only
        br = math.sin(2 * math.pi * 0.55 * i / fps + phase)
        sway = math.sin(2 * math.pi * 0.27 * i / fps + phase * 0.7)
        by = -5.0 * br * n_out
        bx = 3.0 * sway * n_out
        bscale = 1.0 + 0.006 * br * n_out
        if shake:
            sx = sx + shake * 14 * math.sin(i * 2.3)
            sy = sy + shake * 10 * math.cos(i * 2.9)
        mx = (xx - cxo) / (zz * bscale) + cxo - sx - bx + ox
        my = (yy - cyo) / (zz * bscale) + cyo - sy - by + oy
        frame = cv2.remap(big, mx.astype(np.float32), my.astype(np.float32),
                          interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed in motion render")
    return out_path


if __name__ == "__main__":
    import sys
    render(sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "push")
