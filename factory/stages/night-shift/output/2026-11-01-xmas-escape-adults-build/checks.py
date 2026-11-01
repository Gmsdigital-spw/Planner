# ------------------------------------------------------------------ fix round 2: EVERY page's lowest element ends 0.25 in+ above the footer rule
def check_clearance(pdf, dpi=100):
    """Render every page and assert no ink sits between the footer rule and 0.25 in above it (x L..R).
    Pages without the kit footer (cover, thank-you) are checked against the same band at the same height."""
    import subprocess, tempfile, glob as _g
    from PIL import Image as _I
    tmp = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, tmp + "/p"], check=True)
    k = dpi / 72.0
    rule = round((PH - FOOT_RULE) * k)
    x0, x1 = round(L * k) + 2, round(R * k) - 2
    res = []
    for n, f in enumerate(sorted(_g.glob(tmp + "/p-*.png")), 1):
        im = _I.open(f).convert("RGB"); px = im.load()
        bg = px[x0 + 5, rule - 3]
        has_rule = n not in (1, len(_g.glob(tmp + "/p-*.png")))
        top = rule - 2
        while top > 0:
            row_ink = any(sum(abs(a - b) for a, b in zip(px[x, top], bg)) > 40 for x in range(x0, x1))
            if row_ink: break
            top -= 1
        gap_in = (rule - top) / dpi
        res.append((n, round(gap_in, 3), has_rule))
    return res


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
        Y0, Y1 = round((PH - (yb + h) + s) * k), round((PH - yb - s) * k)
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
    box_bad = check_boxes(OUT)
    print(f"boxes checked: {len(BOXES)} on {len(set(b[0] for b in BOXES))} pages; violations: {len(box_bad)}")
    for v in box_bad: print("  BOX", v)
    assert not box_bad, ("boxes with ink inside 0.25 in of the border or over the footer gap", len(box_bad))
    bad = []
    for n, gap_in, has_rule in check_clearance(OUT):
        print(f"p{n:02d} clearance above footer rule {gap_in:.2f} in" + ("" if has_rule else " (no kit footer)"))
        if has_rule and gap_in < 0.25: bad.append((n, gap_in))
    assert not bad, ("pages under 0.25 in above the footer rule", bad)
    print("clearance OK: every footer page >= 0.25 in")
