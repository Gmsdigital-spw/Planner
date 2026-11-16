"""Box sweep for the Left Right build (adapted from the Nov 9 trivia checks.py: per-page heights, since pages 11-16 are 16:9).
python3 checks.py <pdf>"""
import sys, json
J = json.load(open(__file__.rsplit("/",1)[0] + "/boxes.json"))
BOXES = [tuple(b) for b in J["boxes"]]; PAGE_H = J["page_h"]
FOOT_RULE = 0.7 * 72 - 1; CLEAR = 18; PAD = 18
def check_boxes(pdf, dpi=150):
    """Fix round 3 (root fix): for EVERY registered box on EVERY page, no ink (text, badge, line, icon)
    may sit within 0.25 in of the box border on any side, and every box on a footer page ends 0.25 in+
    above the footer rule. Ink = a pixel that matches neither the box's own fill nor its row's fill (so a
    tinted header band or a writing line counts as fill, text on it does not). Returns the violations."""
    import subprocess, tempfile, numpy as np
    from PIL import Image as _I
    tmp = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, tmp + "/p"], check=True)
    k = dpi / 72.0
    n_pages = len(__import__("glob").glob(tmp + "/p-*.png"))
    imgs = {}
    bad = []
    for (pg, name, x, yb, w, h, r) in BOXES:
        if pg not in imgs:
            imgs[pg] = np.asarray(_I.open(f"{tmp}/p-{pg:02d}.png").convert("RGB")).astype(int)
        a = imgs[pg]
        if pg not in (1, n_pages) and yb < FOOT_RULE + CLEAR - 0.01:
            bad.append((pg, name, "bottom over footer gap", round((yb - FOOT_RULE) / 72, 3)))
        s = 3.0                                     # border stroke + anti-alias, excluded
        X0, X1 = round((x + s) * k), round((x + w - s) * k)
        PHp = PAGE_H[str(pg)] if str(pg) in PAGE_H else PAGE_H[pg]
        Y0, Y1 = round((PHp - (yb + h) + s) * k), round((PHp - yb - s) * k)
        sub = a[Y0:Y1, X0:X1]
        q = (sub[..., 0] << 16) | (sub[..., 1] << 8) | sub[..., 2]
        def near(col_int, ref):
            return (abs(((col_int >> 16) & 255) - ((ref >> 16) & 255)) + abs(((col_int >> 8) & 255) - ((ref >> 8) & 255)) + abs((col_int & 255) - (ref & 255))) <= 60
        H_, W_ = q.shape
        yy_, xx_ = np.mgrid[0:H_, 0:W_]
        dl, dr = (xx_ + s * k) / k, (W_ - 1 - xx_ + s * k) / k      # distance to border, pt
        dt, db = (yy_ + s * k) / k, (H_ - 1 - yy_ + s * k) / k
        corner = ((np.minimum(dl, dr) < r + 1.5) & (np.minimum(dt, db) < r + 1.5))
        # the box's own fills = the colours along its inner edge (white body, tinted header band)
        edge = (np.minimum(np.minimum(dl, dr), np.minimum(dt, db)) < s + 2.5) & ~corner
        vals, cnt = np.unique(q[edge], return_counts=True)
        fills = [v for v, n_ in zip(vals, cnt) if n_ >= 0.08 * cnt.sum()]
        ink = np.ones_like(q, dtype=bool)
        for f_ in fills: ink &= ~near(q, f_)
        for i in range(q.shape[0]):
            if ink[i].any():
                rv, rc = np.unique(q[i], return_counts=True); ink[i] &= ~near(q[i], rv[rc.argmax()])
        ring = (np.minimum(np.minimum(dl, dr), np.minimum(dt, db)) < PAD) & ~corner
        hit = ink & ring
        if hit.sum() > 2:
            side = {"left": dl[hit].min(), "right": dr[hit].min(), "top": dt[hit].min(), "bottom": db[hit].min()}
            worst = {kk: round(v / 72, 3) for kk, v in side.items() if v < PAD}
            bad.append((pg, name, "ink inside 0.25 in", worst))
    return bad



if __name__ == "__main__":
    bad = check_boxes(sys.argv[1])
    print(f"check_boxes: {len(BOXES)} boxes, {len(bad)} faults"); [print(x) for x in bad]
    sys.exit(1 if bad else 0)
