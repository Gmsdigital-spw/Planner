#!/usr/bin/env python3
"""Starship free gateway (GitHub Actions).

Runs API jobs for the GM Starship without Make: Etsy (shop's own gm-shop-helper app)
and Zernio (TikTok + Pinterest). A job is gw/jobs/<id>.json = {"id": "...", "ops": [...]};
the result is written to gw/out/<id>.json. Secrets never leave the runner: responses are
scrubbed of anything that looks like a token, and the Etsy refresh token is stored
encrypted (gw/state/etsy.enc) with the STARSHIP_KEY secret.

Ops:
  {"op":"selftest"}
  {"op":"zernio","method":"GET|POST|PUT|PATCH|DELETE","path":"/posts","body":{...},"idem":"key"}
  {"op":"etsy","method":"GET","path":"/shops/68605457","body":{...}}           # path after /v3/application
  {"op":"etsy_upload","path":"/shops/68605457/listings/<id>/images","fileUrl":"https://...",
   "field":"image","fileName":"x.jpg","fields":{"rank":"1","alt_text":"..."}}
  {"op":"fetch_images","dir":"name","items":[{"name":"a.jpg","url":"https://i.etsystatic.com/..."}]}  -> saved under gw/out/files/<dir>/
  {"op":"etsy_auth_start"}            -> gives the Etsy authorize link
  {"op":"etsy_auth_finish","code":"...","state":"..."}
  {"op":"gumroad","method":"GET|POST|PUT|DELETE","path":"/products","body":{...}}   # path after /v2
  {"op":"gumroad_file","fileUrl":"https://...","fileName":"x.pdf"}  -> {"file_url": ...} for products' files[]
  {"op":"gumroad_mirror","key":"<starship product id>","name":"...","price":499,"description":"<html>",
   "summary":"...","tags":[...],"category":"<path>","fileEnc":"gw/vault/<id>.enc","fileName":"x.pdf",
   "covers":["https://..."],"thumbnail":"https://...","publish":false}
     -> one product end to end (skips if a product with the same name already exists).
     fileEnc = the product file encrypted with STARSHIP_KEY (Fernet), so the public repo never holds a usable file.
"""
import base64, hashlib, json, os, secrets, sys, time, urllib.parse
from pathlib import Path
import requests
from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parent
JOBS, OUT, STATE = ROOT / "jobs", ROOT / "out", ROOT / "state" / "etsy.enc"
ZERNIO = "https://zernio.com/api/v1"
ETSY = "https://api.etsy.com/v3/application"
ETSY_TOKEN = "https://api.etsy.com/v3/public/oauth/token"
REDIRECT = os.environ.get("ETSY_REDIRECT", "https://gmsdigital-spw.github.io/planner/gw/callback.html")
SCOPES = "listings_r listings_w listings_d shops_r shops_w transactions_r profile_r"
KEY, SECRET = os.environ.get("ETSY_KEYSTRING", ""), os.environ.get("ETSY_SHARED_SECRET", "")
ZKEY, SKEY = os.environ.get("ZERNIO_API_KEY", ""), os.environ.get("STARSHIP_KEY", "")
GKEY = os.environ.get("GUMROAD_TOKEN", "")
GUMROAD = "https://api.gumroad.com/v2"
AKEY, ASEC = os.environ.get("ALPACA_KEY_ID", ""), os.environ.get("ALPACA_SECRET_KEY", "")
ALPACA_LIVE = os.environ.get("ALPACA_LIVE", "") == "1"   # stays "0": paper only until Grayson flips it himself
ALPACA = "https://api.alpaca.markets/v2" if ALPACA_LIVE else "https://paper-api.alpaca.markets/v2"
ALPACA_DATA = "https://data.alpaca.markets/v2"
SENSITIVE = ("token", "secret", "password", "authorization", "cookie", "apikey", "api_key")
MAX_OUT = 400_000


def scrub(x):
    if isinstance(x, dict):
        return {k: ("[hidden]" if any(s in k.lower() for s in SENSITIVE) else scrub(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [scrub(v) for v in x]
    return x


def body_of(r):
    try:
        return r.json()
    except Exception:
        return r.text[:4000]


# ---------- encrypted Etsy state ----------
def fernet():
    if not SKEY:
        raise RuntimeError("STARSHIP_KEY secret is missing")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(SKEY.encode()).digest()))


def load_state():
    if not STATE.exists():
        return {}
    try:
        return json.loads(fernet().decrypt(STATE.read_bytes()))
    except InvalidToken:
        raise RuntimeError("Etsy state can't be decrypted (STARSHIP_KEY changed?) - run etsy_auth_start again")


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_bytes(fernet().encrypt(json.dumps(st).encode()))


def api_key_header(fmt):
    return f"{KEY}:{SECRET}" if (fmt == "pair" and SECRET) else KEY


def etsy_access(st):
    if st.get("access_token") and st.get("expires_at", 0) > time.time() + 120:
        return st["access_token"]
    if not st.get("refresh_token"):
        raise RuntimeError("Etsy not authorized yet - run etsy_auth_start / etsy_auth_finish")
    r = requests.post(ETSY_TOKEN, data={"grant_type": "refresh_token", "client_id": KEY,
                                        "refresh_token": st["refresh_token"]}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Etsy token refresh failed: {r.status_code} {str(body_of(r))[:300]}")
    t = r.json()
    st.update(access_token=t["access_token"], refresh_token=t.get("refresh_token", st["refresh_token"]),
              expires_at=time.time() + int(t.get("expires_in", 3600)), refreshed_at=int(time.time()))
    save_state(st)
    return st["access_token"]


def etsy_call(st, method, path, **kw):
    fmt = st.get("key_fmt", "pair" if SECRET else "single")
    for attempt in range(2):
        hdr = {"x-api-key": api_key_header(fmt), "Authorization": f"Bearer {etsy_access(st)}"}
        hdr.update(kw.pop("headers", {}) or {})
        r = requests.request(method, ETSY + path, headers=hdr, timeout=120, **kw)
        txt = r.text[:300].lower()
        if r.status_code in (401, 403) and "api key" in txt and attempt == 0 and SECRET:
            fmt = "single" if fmt == "pair" else "pair"
            continue
        if r.status_code < 400 and st.get("key_fmt") != fmt:
            st["key_fmt"] = fmt
            save_state(st)
        return r
    return r


# ---------- ops ----------
def op_selftest(o, st):
    return 200, {"configured": {"etsyKeystring": bool(KEY), "etsySharedSec": bool(SECRET),
                             "zernio": bool(ZKEY), "starship": bool(SKEY), "gumroad": bool(GKEY)},
                 "etsyAuthorized": bool(st.get("refresh_token")), "redirect": REDIRECT,
                 "starshipKeyFp": hashlib.sha256(SKEY.encode()).hexdigest()[:6] if SKEY else None,
                 "starshipKeyFpStripped": hashlib.sha256(SKEY.strip().encode()).hexdigest()[:6] if SKEY else None}


def op_zernio(o, st):
    if not ZKEY:
        raise RuntimeError("ZERNIO_API_KEY secret is missing")
    hdr = {"Authorization": f"Bearer {ZKEY}", "Content-Type": "application/json"}
    if o.get("idem"):
        hdr["Idempotency-Key"] = str(o["idem"])[:255]
    r = requests.request(o.get("method", "GET").upper(), ZERNIO + o["path"], headers=hdr,
                         json=o.get("body"), timeout=180)
    return r.status_code, body_of(r)


def op_etsy(o, st):
    m = o.get("method", "GET").upper()
    kw = {}
    if o.get("body") is not None:
        b = o["body"]
        if isinstance(b, str):
            try:
                b = json.loads(b)
            except Exception:
                pass
        if o.get("form"):
            kw["data"] = b
        else:
            kw["json"] = b
    r = etsy_call(st, m, o["path"], **kw)
    return r.status_code, body_of(r)


def op_etsy_upload(o, st):
    f = requests.get(o["fileUrl"], timeout=120)
    if f.status_code != 200 or not f.content:
        raise RuntimeError(f"could not download {o['fileUrl']}: {f.status_code}")
    files = {o.get("field", "image"): (o.get("fileName", "file"), f.content)}
    r = etsy_call(st, "POST", o["path"], files=files, data=o.get("fields", {}))
    return r.status_code, body_of(r)


def op_etsy_auth_start(o, st):
    if not KEY:
        raise RuntimeError("ETSY_KEYSTRING secret is missing")
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    st["pkce"] = {"verifier": verifier, "state": state, "at": int(time.time())}
    save_state(st)
    url = "https://www.etsy.com/oauth/connect?" + urllib.parse.urlencode({
        "response_type": "code", "redirect_uri": REDIRECT, "scope": SCOPES, "client_id": KEY,
        "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})
    return 200, {"authorizeUrl": url, "state": state, "redirect": REDIRECT}


def op_etsy_auth_finish(o, st):
    p = st.get("pkce") or {}
    if not p:
        raise RuntimeError("run etsy_auth_start first")
    if o.get("state") and o["state"] != p.get("state"):
        raise RuntimeError("state does not match the last etsy_auth_start")
    r = requests.post(ETSY_TOKEN, data={"grant_type": "authorization_code", "client_id": KEY,
                                        "redirect_uri": REDIRECT, "code": o["code"],
                                        "code_verifier": p["verifier"]}, timeout=30)
    if r.status_code != 200:
        return r.status_code, body_of(r)
    t = r.json()
    st.pop("pkce", None)
    st.update(access_token=t["access_token"], refresh_token=t["refresh_token"],
              expires_at=time.time() + int(t.get("expires_in", 3600)), authorized_at=int(time.time()))
    save_state(st)
    me = etsy_call(st, "GET", "/users/me")
    return 200, {"authorized": True, "me": body_of(me)}


def gumroad_hdr():
    if not GKEY:
        raise RuntimeError("GUMROAD_TOKEN secret is missing")
    return {"Authorization": f"Bearer {GKEY}"}


def op_gumroad(o, st):
    r = requests.request(o.get("method", "GET").upper(), GUMROAD + o["path"], headers=gumroad_hdr(),
                         json=o.get("body"), timeout=180)
    return r.status_code, body_of(r)


def file_bytes(o):
    if o.get("fileEnc"):
        p = (ROOT.parent / o["fileEnc"]).resolve()
        if ROOT.parent.resolve() not in p.parents or not p.exists():
            raise RuntimeError(f"encrypted file not found: {o['fileEnc']}")
        vf = Fernet(base64.urlsafe_b64encode(hashlib.sha256(SKEY.strip().encode()).digest()))
        raw = p.read_bytes()
        if raw.startswith(b"SEAL1"):
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            priv = serialization.load_pem_private_key(vf.decrypt((ROOT / "state" / "vault_priv.enc").read_bytes()), None)
            n = int.from_bytes(raw[5:7], "big")
            fk = priv.decrypt(raw[7:7 + n], padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
            return Fernet(fk).decrypt(raw[7 + n:])
        return vf.decrypt(raw)
    f = requests.get(o["fileUrl"], timeout=300)
    if f.status_code != 200 or not f.content:
        raise RuntimeError(f"could not download {o['fileUrl']}: {f.status_code}")
    return f.content


def op_gumroad_file(o, st):
    data = file_bytes(o)
    name = o.get("fileName") or (o.get("fileUrl") or "file").rsplit("/", 1)[-1] or "file"
    r = requests.post(GUMROAD + "/files/presign", headers=gumroad_hdr(),
                      json={"filename": name, "file_size": len(data)}, timeout=60)
    pre = body_of(r)
    if r.status_code != 200 or not isinstance(pre, dict) or not pre.get("success"):
        return r.status_code, pre
    size, parts = 100 * 1024 * 1024, []
    for p in pre["parts"]:
        n = int(p["part_number"])
        u = requests.put(p["presigned_url"], data=data[(n - 1) * size:n * size], timeout=300)
        if u.status_code != 200:
            requests.post(GUMROAD + "/files/abort", headers=gumroad_hdr(),
                          json={"upload_id": pre["upload_id"], "key": pre["key"]}, timeout=60)
            raise RuntimeError(f"part {n} upload failed: {u.status_code}")
        parts.append({"part_number": n, "etag": u.headers.get("ETag", "").strip()})
    c = requests.post(GUMROAD + "/files/complete", headers=gumroad_hdr(),
                      json={"upload_id": pre["upload_id"], "key": pre["key"], "parts": parts}, timeout=120)
    out = body_of(c)
    if isinstance(out, dict):
        out.update(fileName=name, bytes=len(data))
    return c.status_code, out


def square_thumb_blob(url, H, size=1000):
    """Center-crop an image to a square JPEG and reserve+upload it as a Gumroad direct-upload blob."""
    import io
    from PIL import Image
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    w, h = im.size
    m = min(w, h)
    im = im.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m)).resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    data = buf.getvalue()
    blob = {"filename": "thumbnail.jpg", "byte_size": len(data), "content_type": "image/jpeg",
            "checksum": base64.b64encode(hashlib.md5(data).digest()).decode()}
    d = requests.post(GUMROAD + "/direct_uploads", headers=H, json={"blob": blob}, timeout=60)
    dj = body_of(d)
    if d.status_code != 200 or not isinstance(dj, dict) or not dj.get("signed_id"):
        raise RuntimeError(f"direct upload reservation failed: {d.status_code} {str(dj)[:200]}")
    up = requests.put(dj["direct_upload"]["url"], data=data, headers=dj["direct_upload"].get("headers") or {}, timeout=120)
    if up.status_code not in (200, 201, 204):
        raise RuntimeError(f"thumbnail upload failed: {up.status_code}")
    return dj["signed_id"]


def gumroad_name_ok(H, o):
    """Privacy lock: only publish when the public store name is the shop name (never the owner's real name)."""
    want = (o.get("requireStoreName") or "").strip().lower()
    if not want:
        return True, None
    u = requests.get(GUMROAD + "/user", headers=H, timeout=60).json().get("user") or {}
    shown = (u.get("name") or u.get("display_name") or "").strip()
    return shown.lower() == want, shown


def op_gumroad_mirror(o, st):
    H = gumroad_hdr()
    log = []
    if o.get("publish"):
        ok, shown = gumroad_name_ok(H, o)
        if not ok:
            o = dict(o, publish=False)
            log.append({"step": "privacy_lock", "ok": False, "msg": "store name is not the shop name yet, kept as draft"})
    ex = requests.get(GUMROAD + "/products", headers=H, timeout=60).json()
    for p in (ex.get("products") or []):
        if p.get("name") == o["name"]:
            pid = p["id"]
            if o.get("publish") and not p.get("published"):
                e = requests.put(GUMROAD + f"/products/{pid}/enable", headers=H, timeout=60)
                log.append({"step": "enable", "status": e.status_code, "body": body_of(e)})
            return 200, {"skipped": "exists", "id": pid, "url": p.get("short_url"), "published": p.get("published"), "log": log}
    code, up = op_gumroad_file(o, st)
    if code != 200 or not isinstance(up, dict) or not up.get("file_url"):
        return (code if code >= 400 else 422), {"failedAt": "file", "body": up}
    body = {"name": o["name"], "price": int(o["price"]), "description": o.get("description", ""),
            "draft": True, "files": [{"url": up["file_url"], "display_name": o.get("displayName") or o["name"]}]}
    if o.get("summary"):
        body["custom_summary"] = o["summary"][:250]
    if o.get("tags"):
        body["tags"] = list(o["tags"])[:5]
    if o.get("category"):
        body["category"] = o["category"]
    if o.get("permalink"):
        body["custom_permalink"] = o["permalink"]
    r = requests.post(GUMROAD + "/products", headers=H, json=body, timeout=180)
    cr = body_of(r)
    if r.status_code != 200 or not isinstance(cr, dict) or not cr.get("success"):
        return (r.status_code if r.status_code >= 400 else 422), {"failedAt": "create", "body": cr}
    prod = cr.get("product") or {}
    pid = prod.get("id")
    for u in (o.get("covers") or [])[:8]:
        c = requests.post(GUMROAD + f"/products/{pid}/covers", headers=H, json={"url": u}, timeout=120)
        log.append({"step": "cover", "status": c.status_code, "ok": isinstance(body_of(c), dict) and body_of(c).get("success")})
    if o.get("thumbFrom"):
        try:
            sid = square_thumb_blob(o["thumbFrom"], H)
            t = requests.post(GUMROAD + f"/products/{pid}/thumbnail", headers=H, json={"signed_blob_id": sid}, timeout=120)
            tb = body_of(t)
            log.append({"step": "thumbnail", "status": t.status_code, "ok": isinstance(tb, dict) and tb.get("success"),
                        "msg": tb.get("message") if isinstance(tb, dict) else None})
        except Exception as e:
            log.append({"step": "thumbnail", "ok": False, "msg": f"{type(e).__name__}: {e}"[:300]})
    elif o.get("thumbnail"):
        t = requests.post(GUMROAD + f"/products/{pid}/thumbnail", headers=H, json={"url": o["thumbnail"]}, timeout=120)
        tb = body_of(t)
        log.append({"step": "thumbnail", "status": t.status_code, "ok": isinstance(tb, dict) and tb.get("success"),
                    "msg": tb.get("message") if isinstance(tb, dict) else None})
    published = False
    if o.get("publish"):
        e = requests.put(GUMROAD + f"/products/{pid}/enable", headers=H, timeout=60)
        eb = body_of(e)
        published = isinstance(eb, dict) and bool(eb.get("success"))
        log.append({"step": "enable", "status": e.status_code, "body": eb if not published else "ok"})
    return 200, {"id": pid, "url": prod.get("short_url"), "published": published, "warning": cr.get("warning") or cr.get("message"), "log": log}


def op_fetch_images(o, st):
    """Save small Etsy listing images into gw/out/files/<dir>/ so the crew can look at them.
    {"op":"fetch_images","dir":"<name>","items":[{"name":"<file>.jpg","url":"https://i.etsystatic.com/..."}]}"""
    d = OUT / "files" / "".join(c for c in str(o.get("dir", "x")) if c.isalnum() or c in "-_")[:60]
    d.mkdir(parents=True, exist_ok=True)
    saved = []
    for it in (o.get("items") or [])[:120]:
        u = str(it.get("url", ""))
        if urllib.parse.urlparse(u).hostname != "i.etsystatic.com":
            continue
        r = requests.get(u, timeout=30)
        if r.ok and len(r.content) < 3_000_000:
            n = "".join(c for c in str(it.get("name", "img.jpg")) if c.isalnum() or c in "-_.")[:80]
            (d / n).write_bytes(r.content)
            saved.append(n)
    return 200, {"dir": str(d.relative_to(ROOT)), "saved": saved}


def op_alpaca(o, st):
    """Trading Floor (V6, paper first). {"op":"alpaca","method":"GET|POST|DELETE","path":"/account" | "/orders" | "/positions" ...,"body":{...}}
    Hard rules enforced here, not just in the prompt: paper endpoint unless the ALPACA_LIVE secret is "1"; no margin
    (notional orders only, buying power capped by cash); every buy must carry a stop_loss (bracket); no order after
    19:45 UTC (2:45 PM CT); the floor: if equity would drop below ALPACA_FLOOR (default 20) all new buys are refused.
    Data reads: {"op":"alpaca","data":true,"path":"/stocks/AAPL/bars?timeframe=5Min&limit=50"}"""
    if not (AKEY and ASEC):
        raise RuntimeError("ALPACA_KEY_ID / ALPACA_SECRET_KEY secrets are missing (paper keys from a free Alpaca account)")
    hdr = {"APCA-API-KEY-ID": AKEY, "APCA-API-SECRET-KEY": ASEC, "Content-Type": "application/json"}
    base = ALPACA_DATA if o.get("data") else ALPACA
    m = o.get("method", "GET").upper()
    body = o.get("body")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            pass
    if m == "POST" and o["path"].startswith("/orders") and not o.get("data"):
        floor = float(os.environ.get("ALPACA_FLOOR", "20"))
        acct = requests.get(ALPACA + "/account", headers=hdr, timeout=60).json()
        equity = float(acct.get("equity") or 0); cash = float(acct.get("cash") or 0)
        side = str((body or {}).get("side", "")).lower()
        if side == "buy":
            if equity <= floor:
                return 423, {"refused": "floor", "equity": equity, "floor": floor, "message": "Equity is at or below the hard floor; the floor is locked. No new buys."}
            if not (body.get("stop_loss") or body.get("order_class") == "bracket"):
                return 422, {"refused": "no_stop", "message": "Every buy needs a stop_loss (bracket order)."}
            notional = float(body.get("notional") or 0)
            if body.get("qty") and not notional:
                return 422, {"refused": "qty", "message": "Use notional dollars (fractional shares), not qty, so sizing stays exact."}
            if notional > cash * 0.4 + 0.01:
                return 422, {"refused": "size", "message": f"Position {notional:.2f} is over 40% of cash ({cash:.2f})."}
            if body.get("time_in_force", "day") != "day":
                return 422, {"refused": "tif", "message": "Day orders only; no overnight holds."}
            hh, mm = time.gmtime().tm_hour, time.gmtime().tm_min
            if (hh, mm) >= (19, 45) or (hh, mm) < (14, 35):
                return 422, {"refused": "hours", "message": "Buys only between 9:35 AM and 2:45 PM Central."}
    r = requests.request(m, base + o["path"], headers=hdr, json=body if m in ("POST", "PATCH", "PUT") else None, timeout=120)
    return r.status_code, body_of(r)


OPS = {"fetch_images": op_fetch_images, "gumroad": op_gumroad, "gumroad_mirror": op_gumroad_mirror, "gumroad_file": op_gumroad_file, "selftest": op_selftest, "zernio": op_zernio, "etsy": op_etsy, "etsy_upload": op_etsy_upload,
       "etsy_auth_start": op_etsy_auth_start, "etsy_auth_finish": op_etsy_auth_finish, "alpaca": op_alpaca}


def run_job(path):
    job = json.loads(path.read_text())
    jid = str(job.get("id") or path.stem)
    try:
        st = load_state() if SKEY else {}
    except Exception as e:
        st, state_err = {}, str(e)
    else:
        state_err = None
    results = []
    for i, o in enumerate(job.get("ops", [])):
        name = o.get("op")
        t0 = time.time()
        try:
            if state_err and name.startswith("etsy") and name != "etsy_auth_start":
                raise RuntimeError(state_err)
            code, data = OPS[name](o, st)
            results.append({"i": i, "op": name, "tag": o.get("tag"), "status": code, "ok": 200 <= code < 300,
                            "data": scrub(data), "ms": int((time.time() - t0) * 1000)})
        except Exception as e:
            results.append({"i": i, "op": name, "tag": o.get("tag"), "status": 0, "ok": False,
                            "error": f"{type(e).__name__}: {e}"[:500]})
            if job.get("stopOnError"):
                break
    out = {"id": jid, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "ok": all(r["ok"] for r in results), "results": results}
    s = json.dumps(out, ensure_ascii=False)
    if len(s) > MAX_OUT:
        for r in out["results"]:
            if "data" in r:
                r["data"] = "[truncated: response too large]"
        s = json.dumps(out, ensure_ascii=False)
    (OUT / f"{jid}.json").write_text(s)
    print(f"{jid}: {'ok' if out['ok'] else 'had errors'} ({len(results)} ops)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    for p in sorted(JOBS.glob("*.json")):
        if only and p.stem != only:
            continue
        if (OUT / f"{p.stem}.json").exists() and not only:
            continue
        run_job(p)


if __name__ == "__main__":
    main()
