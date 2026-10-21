#!/usr/bin/env python3
"""
Free animation lane: turn one still (the factory's own scene) into a short real-motion clip
using a Hugging Face ZeroGPU Space (image-to-video), through the public Gradio API.

Why free: a free Hugging Face account gets 5 minutes of ZeroGPU time a day (unauthenticated
callers share a 2-minute pool), which is 1 to 3 short hero shots a night at no cost. PRO gets 40.
Set HF_TOKEN (a free account's READ token) as a GitHub secret so the quota is the account's own.

Usage:  python3 hf_anim.py <still.jpg> "<prompt>" <out.mp4> [--space owner/name] [--seconds 5]
Exit 0 = out.mp4 written. Exit 2 = lane unavailable (quota, no token, space asleep): the caller
falls back to the parallax still. Never raises into the build.

The Space list is tried in order; each one's API is introspected (view_api) so a renamed
endpoint or parameter does not break the lane. A Space counts only if it exposes an endpoint
taking an image and a text prompt and returning a video.
"""
import os, sys, json, time, shutil, subprocess

SPACES = [s for s in os.environ.get("HF_ANIM_SPACES", "").split(",") if s.strip()] or [
    # image-to-video Spaces on ZeroGPU; edit this list (or HF_ANIM_SPACES) as Spaces come and go.
    "Lightricks/ltx-video-distilled",
    "Wan-AI/Wan2.2-TI2V-5B",
    "zerogpu-aoti/wan2-2-fp8da-aoti-faster",
    "multimodalart/wan2-1-fast",
]

def log(*a):
    print("[hf_anim]", *a, flush=True)

def pick_endpoint(client):
    """Find an endpoint with an image input and a text input; return (api_name, params)."""
    try:
        info = client.view_api(return_format="dict", print_info=False)
    except Exception as e:
        log("view_api failed:", repr(e)); return None, None
    for api_name, ep in (info.get("named_endpoints") or {}).items():
        params = ep.get("parameters") or []
        kinds = [(p.get("parameter_name") or p.get("label") or "").lower() + "|" + json.dumps(p.get("python_type") or p.get("type") or {}).lower() for p in params]
        has_img = any(("image" in k or "filepath" in k or "file" in k) for k in kinds)
        has_txt = any(("prompt" in k) for k in kinds)
        if has_img and has_txt:
            return api_name, params
    return None, None

def build_args(params, image_path, prompt, seconds):
    from gradio_client import handle_file
    args = []
    for p in params:
        name = (p.get("parameter_name") or p.get("label") or "").lower()
        ptype = json.dumps(p.get("python_type") or p.get("type") or {}).lower()
        default = p.get("parameter_default", None) if p.get("parameter_has_default") else None
        if "image" in name or ("filepath" in ptype and "video" not in name):
            args.append(handle_file(image_path))
        elif "negative" in name:
            args.append(default if default is not None else "blurry, text, watermark, extra limbs, distorted face")
        elif "prompt" in name:
            args.append(prompt)
        elif "duration" in name or "seconds" in name or "num_frames" in name or "frames" in name:
            if "frame" in name:
                args.append(default if default is not None else int(seconds * 24))
            else:
                args.append(default if default is not None else float(seconds))
        elif "seed" in name:
            args.append(default if default is not None else 42)
        elif "random" in name and "bool" in ptype:
            args.append(False)
        else:
            args.append(default)
    return args

def first_video(result):
    stack = [result]
    while stack:
        r = stack.pop()
        if isinstance(r, dict):
            if r.get("video"):
                v = r["video"]; return v if isinstance(v, str) else (v.get("path") or v.get("url"))
            if r.get("path") and str(r["path"]).lower().endswith((".mp4", ".webm")):
                return r["path"]
            stack.extend(r.values())
        elif isinstance(r, (list, tuple)):
            stack.extend(r)
        elif isinstance(r, str) and r.lower().endswith((".mp4", ".webm")):
            return r
    return None

def main():
    if len(sys.argv) < 4:
        log("usage: hf_anim.py still.jpg prompt out.mp4"); return 2
    still, prompt, out = sys.argv[1], sys.argv[2], sys.argv[3]
    seconds = 5.0
    spaces = list(SPACES)
    a = sys.argv[4:]
    while a:
        k = a.pop(0)
        if k == "--seconds" and a: seconds = float(a.pop(0))
        elif k == "--space" and a: spaces = [a.pop(0)] + spaces
    token = os.environ.get("HF_TOKEN", "").strip() or None
    if not token:
        log("no HF_TOKEN: unauthenticated pool is tiny; trying anyway")
    try:
        from gradio_client import Client
    except Exception as e:
        log("gradio_client missing:", repr(e)); return 2
    for sp in spaces:
        t0 = time.time()
        try:
            client = Client(sp, token=token, verbose=False)
        except Exception as e:
            log(sp, "not reachable:", repr(e)[:200]); continue
        api_name, params = pick_endpoint(client)
        if not api_name:
            log(sp, "has no image+prompt endpoint"); continue
        try:
            args = build_args(params, still, prompt, seconds)
            log(sp, api_name, "generating", f"{seconds}s")
            result = client.predict(*args, api_name=api_name)
        except Exception as e:
            msg = repr(e)[:300]
            log(sp, "failed:", msg)
            if "quota" in msg.lower() or "gpu" in msg.lower():
                log("ZeroGPU quota reached for today on this account")
            continue
        vid = first_video(result)
        if not vid or not os.path.exists(vid):
            log(sp, "returned no video file"); continue
        tmp = out + ".src.mp4"
        shutil.copy(vid, tmp)
        # normalise to the factory's render size, 30 fps, no audio; keep aspect by crop-to-fill
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-an",
                            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)
        except Exception as e:
            log("ffmpeg normalise failed:", repr(e)); continue
        finally:
            try: os.remove(tmp)
            except Exception: pass
        log("done in", int(time.time() - t0), "s via", sp)
        return 0
    log("every Space failed or quota is used up; falling back to the still")
    return 2

if __name__ == "__main__":
    sys.exit(main())
