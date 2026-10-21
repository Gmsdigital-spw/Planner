"""Flat holiday/party illustrations as inline SVG (viewBox 0 0 100 100).
Used by tools/fun_covers.py so covers show the THING the product is about:
cookies on a cookie swap, Santa on Secret Santa, a gingerbread house on a gingerbread contest.
Every function returns an <svg> string. Add new art here, never draw people's real faces.
"""

def _svg(body, vb="0 0 100 100"):
    return f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">{body}</svg>'

# ---------- cookies & sweets ----------
def choc_cookie():
    chips = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*0.8}" fill="#4a2512" transform="rotate({a} {x} {y})"/>'
                    for x, y, r, a in [(32,35,6,20),(58,28,5,-10),(70,52,6,30),(45,58,7,0),(28,62,5,40),(60,72,5,-20),(50,42,4,10),(76,35,4,0)])
    return _svg(f'<circle cx="50" cy="52" r="44" fill="#a8652b"/><circle cx="50" cy="50" r="44" fill="#d9964a"/>'
                f'<circle cx="50" cy="50" r="44" fill="none" stroke="#c07a35" stroke-width="3"/>'
                f'<path d="M20 40 Q30 30 40 36" stroke="#efb46a" stroke-width="3" fill="none" stroke-linecap="round"/>{chips}')

def gingerbread_man(icing="#ffffff", button="#e8323c"):
    return _svg(f'''<g>
<path d="M50 6c10 0 17 7 17 16 0 5-2 9-5 12h16c6 0 9 4 9 8s-3 8-9 8H66v10l12 22c3 5 1 10-3 12s-9 1-11-4L50 74 36 90c-2 5-7 6-11 4s-6-7-3-12l12-22V50H22c-6 0-9-4-9-8s3-8 9-8h16c-3-3-5-7-5-12 0-9 7-16 17-16z" fill="#b5652e"/>
<path d="M50 6c10 0 17 7 17 16 0 5-2 9-5 12h16c6 0 9 4 9 8s-3 8-9 8H66v10l12 22c3 5 1 10-3 12s-9 1-11-4L50 74 36 90c-2 5-7 6-11 4s-6-7-3-12l12-22V50H22c-6 0-9-4-9-8s3-8 9-8h16c-3-3-5-7-5-12 0-9 7-16 17-16z" fill="none" stroke="#8e4a1f" stroke-width="1.5"/>
<circle cx="44" cy="19" r="2.6" fill="#3a1d0c"/><circle cx="56" cy="19" r="2.6" fill="#3a1d0c"/>
<path d="M43 26 Q50 32 57 26" stroke="{icing}" stroke-width="2.6" fill="none" stroke-linecap="round"/>
<path d="M18 38 q3 4 0 8 M82 38 q-3 4 0 8 M30 82 q4 2 8-1 M70 82 q-4 2 -8-1" stroke="{icing}" stroke-width="2.4" fill="none" stroke-linecap="round"/>
<circle cx="50" cy="44" r="3.2" fill="{button}"/><circle cx="50" cy="55" r="3.2" fill="#2fa35a"/><circle cx="50" cy="66" r="3.2" fill="{button}"/>
</g>''')

def sugar_star(fill="#ffffff", sprinkles=True):
    sp = ""
    if sprinkles:
        cols = ["#e8323c", "#2fa35a", "#ffcf3f", "#3fa7f5", "#ff8fb1"]
        pts = [(40,40,20),(58,38,-30),(50,55,60),(36,56,10),(62,58,-50),(48,30,80),(54,68,30),(44,66,-20)]
        sp = "".join(f'<rect x="{x-3}" y="{y-1}" width="6" height="2.2" rx="1.1" fill="{cols[i%5]}" transform="rotate({a} {x} {y})"/>' for i,(x,y,a) in enumerate(pts))
    star = "M50 4 L62 36 L96 37 L69 58 L79 92 L50 72 L21 92 L31 58 L4 37 L38 36Z"
    return _svg(f'<path d="{star}" fill="#d9964a" transform="translate(0 3)"/><path d="{star}" fill="#e4a55a"/>'
                f'<path d="{star}" fill="{fill}" transform="translate(50 50) scale(.84) translate(-50 -50)"/>{sp}')

def sugar_tree():
    return _svg('<path d="M50 4 L84 50 H66 L90 84 H10 L34 50 H16Z" fill="#e4a55a"/>'
                '<path d="M50 10 L78 48 H62 L82 80 H18 L38 48 H22Z" fill="#3cb46e"/>'
                '<path d="M30 62 Q50 56 70 64 M26 76 Q50 68 76 78" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round"/>'
                '<circle cx="44" cy="40" r="3" fill="#e8323c"/><circle cx="58" cy="52" r="3" fill="#ffcf3f"/><circle cx="40" cy="70" r="3" fill="#ffcf3f"/><circle cx="62" cy="72" r="3" fill="#e8323c"/>'
                '<rect x="44" y="84" width="12" height="10" fill="#8e4a1f"/>')

def candy_cane():
    return _svg('<defs><clipPath id="cc"><path d="M38 96 V36 a22 22 0 0 1 44 0 v6 h-14 v-6 a8 8 0 0 0 -16 0 V96Z"/></clipPath></defs>'
                '<path d="M38 96 V36 a22 22 0 0 1 44 0 v6 h-14 v-6 a8 8 0 0 0 -16 0 V96Z" fill="#fff"/>'
                '<g clip-path="url(#cc)">' + "".join(f'<rect x="20" y="{y}" width="80" height="7" fill="#e8323c" transform="rotate(-35 50 {y})"/>' for y in range(0, 110, 14)) + '</g>'
                '<path d="M38 96 V36 a22 22 0 0 1 44 0 v6 h-14 v-6 a8 8 0 0 0 -16 0 V96Z" fill="none" stroke="#c51d2a" stroke-width="1.5"/>')

def milk_glass():
    return _svg('<path d="M28 14 H72 L66 94 H34Z" fill="#eef6ff" stroke="#bcd3ea" stroke-width="2"/>'
                '<path d="M30 34 H70 L66 92 H34Z" fill="#ffffff"/><path d="M36 40 L38 84" stroke="#dfe9f5" stroke-width="4" stroke-linecap="round"/>')

# ---------- christmas ----------
def santa():
    return _svg('''
<path d="M18 46 Q22 10 58 12 Q86 14 90 40 L84 44 Q78 26 58 26 Q34 26 30 50Z" fill="#e8323c"/>
<path d="M58 12 Q84 8 94 30 Q96 38 90 40 Q86 22 70 20Z" fill="#c51d2a"/>
<circle cx="92" cy="42" r="8" fill="#fff"/>
<ellipse cx="52" cy="58" rx="27" ry="24" fill="#ffd2b3"/>
<path d="M22 60 Q20 96 52 98 Q84 96 82 60 Q76 74 66 70 Q60 78 52 76 Q44 78 38 70 Q28 74 22 60Z" fill="#fff"/>
<path d="M36 70 Q44 62 52 68 Q60 62 68 70 Q60 76 52 72 Q44 76 36 70Z" fill="#fff" stroke="#e7e7e7" stroke-width="1"/>
<circle cx="52" cy="64" r="6" fill="#f59b8b"/>
<circle cx="42" cy="54" r="3.2" fill="#2b2b2b"/><circle cx="62" cy="54" r="3.2" fill="#2b2b2b"/>
<circle cx="43" cy="53" r="1" fill="#fff"/><circle cx="63" cy="53" r="1" fill="#fff"/>
<path d="M36 47 Q42 43 48 47 M56 47 Q62 43 68 47" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round"/>
<circle cx="34" cy="62" r="4" fill="#f7a6a0" opacity=".7"/><circle cx="70" cy="62" r="4" fill="#f7a6a0" opacity=".7"/>
<rect x="14" y="40" width="72" height="14" rx="7" fill="#fff"/>''')

def gift(box="#e8323c", ribbon="#ffcf3f"):
    return _svg(f'<rect x="12" y="40" width="76" height="54" rx="4" fill="{box}"/><rect x="8" y="28" width="84" height="18" rx="4" fill="{box}"/>'
                f'<rect x="8" y="40" width="84" height="6" fill="#000" opacity=".12"/>'
                f'<rect x="44" y="28" width="12" height="66" fill="{ribbon}"/>'
                f'<path d="M50 28 C36 8 20 16 30 26 C34 30 44 30 50 28Z M50 28 C64 8 80 16 70 26 C66 30 56 30 50 28Z" fill="{ribbon}" stroke="#000" stroke-opacity=".12"/>')

def ornament(c="#3fa7f5"):
    return _svg(f'<rect x="42" y="6" width="16" height="12" rx="2" fill="#d4af37"/><circle cx="50" cy="6" r="4" fill="none" stroke="#d4af37" stroke-width="2"/>'
                f'<circle cx="50" cy="58" r="38" fill="{c}"/><path d="M14 52 Q50 66 86 52 L86 62 Q50 76 14 62Z" fill="#fff" opacity=".85"/>'
                f'<circle cx="36" cy="40" r="7" fill="#fff" opacity=".45"/>')

def holly():
    return _svg('<path d="M50 50 C40 30 18 34 8 22 C14 40 6 46 14 56 C24 50 40 58 50 50Z" fill="#2f8f4e"/>'
                '<path d="M50 50 C60 30 82 34 92 22 C86 40 94 46 86 56 C76 50 60 58 50 50Z" fill="#26794a"/>'
                '<circle cx="44" cy="58" r="8" fill="#e8323c"/><circle cx="58" cy="60" r="8" fill="#c51d2a"/><circle cx="51" cy="70" r="8" fill="#e8323c"/>'
                '<circle cx="41" cy="55" r="2" fill="#fff" opacity=".6"/>')

def snowflake(c="#ffffff"):
    arm = '<path d="M50 50 V8 M50 22 L40 14 M50 22 L60 14 M50 34 L42 28 M50 34 L58 28" stroke="%s" stroke-width="4" stroke-linecap="round" fill="none"/>' % c
    return _svg("".join(f'<g transform="rotate({a} 50 50)">{arm}</g>' for a in range(0, 360, 60)))

def xmas_tree():
    return _svg('<path d="M50 4 L74 34 H62 L84 62 H68 L92 90 H8 L32 62 H16 L38 34 H26Z" fill="#2f8f4e"/>'
                '<path d="M50 4 L74 34 H62 L84 62 H68 L92 90 H50Z" fill="#26794a"/>'
                '<circle cx="42" cy="40" r="4" fill="#e8323c"/><circle cx="60" cy="52" r="4" fill="#ffcf3f"/><circle cx="34" cy="72" r="4" fill="#3fa7f5"/><circle cx="58" cy="78" r="4" fill="#e8323c"/><circle cx="70" cy="74" r="4" fill="#ffcf3f"/>'
                '<path d="M50 0 l3 7 7 0 -6 4 2 7 -6 -4 -6 4 2 -7 -6 -4 7 0z" fill="#ffcf3f"/><rect x="43" y="90" width="14" height="9" fill="#8e4a1f"/>')

def stocking():
    return _svg('<path d="M34 8 H66 V58 L82 70 Q92 82 80 92 Q70 98 58 90 L36 74 Q30 70 32 62Z" fill="#e8323c"/>'
                '<rect x="30" y="6" width="40" height="16" rx="4" fill="#fff"/>'
                '<path d="M58 90 Q70 98 80 92 Q90 84 84 74 Q74 82 62 78Z" fill="#fff"/><circle cx="48" cy="42" r="3" fill="#fff"/><circle cx="56" cy="52" r="3" fill="#fff"/>')

def gingerbread_house():
    return _svg('''
<rect x="18" y="46" width="64" height="48" fill="#b5652e"/>
<path d="M10 50 L50 14 L90 50 L82 54 L50 26 L18 54Z" fill="#fff"/>
<path d="M14 48 L50 16 L86 48" fill="none" stroke="#fff" stroke-width="2"/>
<path d="M22 50 L50 26 L78 50Z" fill="#9c5326"/>
<path d="M18 46 q4 6 8 0 q4 6 8 0 q4 6 8 0 q4 6 8 0 q4 6 8 0 q4 6 8 0 q4 6 8 0 q4 6 8 0" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
<rect x="42" y="66" width="16" height="28" rx="8" fill="#e8323c"/><circle cx="54" cy="81" r="1.6" fill="#ffcf3f"/>
<rect x="24" y="58" width="12" height="12" fill="#ffcf3f" stroke="#fff" stroke-width="2"/><rect x="64" y="58" width="12" height="12" fill="#ffcf3f" stroke="#fff" stroke-width="2"/>
<circle cx="30" cy="80" r="4" fill="#2fa35a"/><circle cx="70" cy="80" r="4" fill="#e8323c"/><circle cx="50" cy="38" r="5" fill="#e8323c" stroke="#fff" stroke-width="1.5"/>
<rect x="64" y="22" width="9" height="16" fill="#8e4a1f"/><rect x="62" y="20" width="13" height="5" fill="#fff"/>
<path d="M30 94 l3-6 3 6 3-6 3 6" stroke="#fff" stroke-width="0" />''')

def bow(c="#ff6fa0"):
    return _svg(f'<path d="M50 44 C30 20 6 26 10 44 C14 60 36 56 50 50Z" fill="{c}"/><path d="M50 44 C70 20 94 26 90 44 C86 60 64 56 50 50Z" fill="{c}"/>'
                f'<path d="M46 50 L30 92 L40 86 L46 96 L52 54Z M54 50 L70 92 L60 86 L54 96 L48 54Z" fill="{c}"/>'
                f'<circle cx="50" cy="48" r="9" fill="{c}" stroke="#000" stroke-opacity=".15" stroke-width="2"/>'
                f'<path d="M20 38 C28 34 38 38 44 44" stroke="#fff" stroke-opacity=".5" stroke-width="3" fill="none" stroke-linecap="round"/>')

# ---------- party / NYE / awards ----------
def balloon(c="#ff5a5f"):
    return _svg(f'<path d="M50 74 Q46 86 54 98" stroke="#555" stroke-width="1.5" fill="none"/>'
                f'<ellipse cx="50" cy="38" rx="28" ry="34" fill="{c}"/><path d="M46 72 L54 72 L50 78Z" fill="{c}"/>'
                f'<ellipse cx="40" cy="26" rx="6" ry="10" fill="#fff" opacity=".4"/>')

def champagne():
    return _svg('<path d="M38 6 H62 Q66 40 50 52 Q34 40 38 6Z" fill="#fff3c4" stroke="#d4af37" stroke-width="2"/>'
                '<path d="M39 18 H61 Q62 40 50 48 Q38 40 39 18Z" fill="#ffd45e"/>'
                '<circle cx="46" cy="30" r="1.6" fill="#fff"/><circle cx="54" cy="24" r="1.3" fill="#fff"/><circle cx="50" cy="38" r="1.4" fill="#fff"/>'
                '<rect x="48.5" y="52" width="3" height="32" fill="#d4af37"/><ellipse cx="50" cy="88" rx="16" ry="5" fill="#d4af37"/>')

def star(c="#ffcf3f"):
    return _svg(f'<path d="M50 4 L62 36 L96 37 L69 58 L79 92 L50 72 L21 92 L31 58 L4 37 L38 36Z" fill="{c}"/>'
                '<path d="M50 14 L58 38 L50 34Z" fill="#fff" opacity=".45"/>')

def sparkle(c="#ffcf3f"):
    return _svg(f'<path d="M50 0 C54 36 64 46 100 50 C64 54 54 64 50 100 C46 64 36 54 0 50 C36 46 46 36 50 0Z" fill="{c}"/>')

def clock():
    return _svg('<circle cx="50" cy="54" r="42" fill="#d4af37"/><circle cx="50" cy="54" r="35" fill="#fffaf0"/>'
                + "".join(f'<rect x="49" y="22" width="2" height="7" fill="#14213d" transform="rotate({a} 50 54)"/>' for a in range(0, 360, 30)) +
                '<path d="M50 54 V28 M50 54 L46 30" stroke="#14213d" stroke-width="4" stroke-linecap="round"/><circle cx="50" cy="54" r="4" fill="#e8323c"/>'
                '<rect x="44" y="4" width="12" height="9" rx="2" fill="#d4af37"/>')

def trophy():
    return _svg('<path d="M28 10 H72 V34 Q72 60 50 64 Q28 60 28 34Z" fill="#ffcf3f"/><path d="M50 10 H72 V34 Q72 60 50 64Z" fill="#f2b705"/>'
                '<path d="M28 18 H14 Q12 40 30 44 M72 18 H86 Q88 40 70 44" stroke="#ffcf3f" stroke-width="6" fill="none"/>'
                '<rect x="44" y="62" width="12" height="14" fill="#f2b705"/><rect x="30" y="76" width="40" height="16" rx="3" fill="#8e4a1f"/>'
                '<rect x="38" y="80" width="24" height="6" rx="2" fill="#ffcf3f"/><path d="M50 22 l3 7 7 1 -5 5 1 7 -6 -3 -6 3 1 -7 -5 -5 7 -1z" fill="#fff"/>')

def medal(c="#e8323c"):
    return _svg(f'<path d="M30 4 H46 L56 44 H40Z" fill="{c}"/><path d="M70 4 H54 L44 44 H60Z" fill="#3fa7f5"/>'
                '<circle cx="50" cy="66" r="28" fill="#ffcf3f"/><circle cx="50" cy="66" r="21" fill="#f2b705"/>'
                '<path d="M50 52 l4 9 10 1 -7 7 2 10 -9 -5 -9 5 2 -10 -7 -7 10 -1z" fill="#fff"/>')

def magnifier():
    return _svg('<circle cx="42" cy="42" r="28" fill="#dff3ff" stroke="#e8323c" stroke-width="9"/>'
                '<path d="M62 62 L90 90" stroke="#8e4a1f" stroke-width="14" stroke-linecap="round"/>'
                '<path d="M28 32 Q34 22 44 22" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/>')

def footprints():
    return _svg('<ellipse cx="30" cy="70" rx="9" ry="14" fill="#fff"/><circle cx="24" cy="50" r="3" fill="#fff"/><circle cx="31" cy="48" r="3" fill="#fff"/><circle cx="38" cy="51" r="3" fill="#fff"/>'
                '<ellipse cx="66" cy="38" rx="9" ry="14" fill="#fff"/><circle cx="60" cy="18" r="3" fill="#fff"/><circle cx="67" cy="16" r="3" fill="#fff"/><circle cx="74" cy="19" r="3" fill="#fff"/>')

# ---------- fall / thanksgiving ----------
def pumpkin(c="#f28b2a"):
    return _svg(f'<path d="M48 24 Q46 10 56 6" stroke="#5a7a2a" stroke-width="6" fill="none" stroke-linecap="round"/>'
                f'<ellipse cx="30" cy="60" rx="20" ry="30" fill="{c}"/><ellipse cx="70" cy="60" rx="20" ry="30" fill="{c}"/>'
                f'<ellipse cx="50" cy="60" rx="22" ry="34" fill="{c}" stroke="#000" stroke-opacity=".12" stroke-width="2"/>'
                f'<path d="M58 14 Q74 12 76 24 Q64 26 58 14Z" fill="#6c9a34"/>'
                f'<ellipse cx="42" cy="46" rx="4" ry="10" fill="#fff" opacity=".25"/>')

def maple_leaf(c="#e0482a"):
    return _svg(f'<path d="M50 6 L58 26 L72 18 L68 38 L88 34 L76 50 L92 58 L70 62 L74 78 L54 68 L52 94 H48 L46 68 L26 78 L30 62 L8 58 L24 50 L12 34 L32 38 L28 18 L42 26Z" fill="{c}"/>'
                f'<path d="M50 30 V92" stroke="#000" stroke-opacity=".18" stroke-width="2"/>')

def pie():
    return _svg('<ellipse cx="50" cy="66" rx="44" ry="20" fill="#c9823e"/><ellipse cx="50" cy="60" rx="44" ry="20" fill="#e6a24f"/>'
                '<ellipse cx="50" cy="58" rx="36" ry="15" fill="#d9772f"/>'
                '<path d="M50 58 L86 56 Q84 66 72 70Z" fill="#fff6e6"/>'
                + "".join(f'<circle cx="{50+40*__import__("math").cos(a/57.3)}" cy="{60+18*__import__("math").sin(a/57.3)}" r="4" fill="#f0b766"/>' for a in range(0, 360, 24)) +
                '<path d="M40 50 q4 -8 10 -4 q6 -8 10 0" fill="#fff"/>')

def turkey():
    feathers = "".join(f'<ellipse cx="50" cy="20" rx="9" ry="26" fill="{c}" transform="rotate({a} 50 58)"/>'
                       for a, c in [(-70,"#e0482a"),(-45,"#f28b2a"),(-20,"#ffcf3f"),(0,"#e0482a"),(20,"#ffcf3f"),(45,"#f28b2a"),(70,"#e0482a")])
    return _svg(f'{feathers}<ellipse cx="50" cy="64" rx="24" ry="26" fill="#8e4a1f"/><circle cx="50" cy="40" r="14" fill="#9c5326"/>'
                '<circle cx="45" cy="37" r="2.6" fill="#222"/><circle cx="55" cy="37" r="2.6" fill="#222"/>'
                '<path d="M46 43 L54 43 L50 50Z" fill="#ffcf3f"/><path d="M52 46 Q56 54 51 56" stroke="#e8323c" stroke-width="4" fill="none" stroke-linecap="round"/>'
                '<path d="M40 92 v6 M60 92 v6" stroke="#f28b2a" stroke-width="3"/>')

def acorn():
    return _svg('<ellipse cx="50" cy="62" rx="22" ry="28" fill="#c9823e"/><path d="M24 44 Q50 20 76 44 Q76 52 50 52 Q24 52 24 44Z" fill="#7a4a24"/>'
                '<path d="M50 30 Q50 20 58 14" stroke="#5a3a1a" stroke-width="4" fill="none" stroke-linecap="round"/>')

# ---------- money / planning ----------
def coin():
    return _svg('<circle cx="50" cy="54" r="42" fill="#e3a600"/><circle cx="50" cy="50" r="42" fill="#ffcf3f"/><circle cx="50" cy="50" r="32" fill="none" stroke="#f2b705" stroke-width="4"/>'
                '<text x="50" y="66" text-anchor="middle" font-family="Outfit" font-weight="700" font-size="44" fill="#b07d00">$</text>')

def piggy():
    return _svg('<ellipse cx="50" cy="58" rx="38" ry="28" fill="#ff8fb1"/><circle cx="84" cy="56" r="10" fill="#ff7aa2"/>'
                '<circle cx="81" cy="54" r="2" fill="#b0405f"/><circle cx="87" cy="54" r="2" fill="#b0405f"/>'
                '<path d="M30 34 L36 20 L44 32Z" fill="#ff7aa2"/><circle cx="66" cy="46" r="3" fill="#333"/>'
                '<rect x="40" y="30" width="20" height="5" rx="2.5" fill="#b0405f"/>'
                '<rect x="26" y="78" width="10" height="14" rx="3" fill="#ff7aa2"/><rect x="60" y="78" width="10" height="14" rx="3" fill="#ff7aa2"/>'
                '<path d="M12 56 q-8 -4 -4 -12" stroke="#ff7aa2" stroke-width="4" fill="none" stroke-linecap="round"/>')

def bill():
    return _svg('<rect x="6" y="24" width="88" height="52" rx="6" fill="#3cb46e"/><rect x="12" y="30" width="76" height="40" rx="4" fill="none" stroke="#c9f2d8" stroke-width="2"/>'
                '<circle cx="50" cy="50" r="13" fill="#c9f2d8"/><text x="50" y="57" text-anchor="middle" font-family="Outfit" font-weight="700" font-size="20" fill="#1e7a45">$</text>')

def target():
    return _svg('<circle cx="46" cy="54" r="40" fill="#e8323c"/><circle cx="46" cy="54" r="30" fill="#fff"/><circle cx="46" cy="54" r="20" fill="#e8323c"/><circle cx="46" cy="54" r="10" fill="#fff"/>'
                '<path d="M46 54 L88 12" stroke="#2b2b2b" stroke-width="4"/><path d="M80 8 L94 6 L92 20 L84 16Z" fill="#3fa7f5"/>')

def calendar(c="#e8323c", day="1"):
    return _svg(f'<rect x="10" y="16" width="80" height="76" rx="8" fill="#fff"/><rect x="10" y="16" width="80" height="22" rx="8" fill="{c}"/><rect x="10" y="30" width="80" height="8" fill="{c}"/>'
                f'<rect x="28" y="8" width="6" height="16" rx="3" fill="#555"/><rect x="66" y="8" width="6" height="16" rx="3" fill="#555"/>'
                f'<text x="50" y="80" text-anchor="middle" font-family="Outfit" font-weight="700" font-size="38" fill="#2b2b2b">{day}</text>')

def checkmark(c="#3cb46e"):
    return _svg(f'<circle cx="50" cy="50" r="44" fill="{c}"/><path d="M28 52 L44 68 L74 34" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

def heart(c="#ff5a8a"):
    return _svg(f'<path d="M50 90 C10 62 4 36 18 22 C30 10 44 16 50 28 C56 16 70 10 82 22 C96 36 90 62 50 90Z" fill="{c}"/>'
                '<ellipse cx="30" cy="34" rx="6" ry="9" fill="#fff" opacity=".4" transform="rotate(-30 30 34)"/>')

def tulip(c="#ff6fa0"):
    return _svg(f'<path d="M50 50 V96" stroke="#3a8a4e" stroke-width="5"/><path d="M50 80 Q30 66 26 52 Q44 58 50 74" fill="#3a8a4e"/>'
                f'<path d="M30 20 L40 32 L50 14 L60 32 L70 20 Q74 48 50 54 Q26 48 30 20Z" fill="{c}"/>')

def flower(c="#ffb3c7", center="#ffcf3f"):
    return _svg("".join(f'<ellipse cx="50" cy="26" rx="14" ry="22" fill="{c}" transform="rotate({a} 50 50)"/>' for a in range(0, 360, 72)) + f'<circle cx="50" cy="50" r="12" fill="{center}"/>')

def leaf(c="#5f9b5a"):
    return _svg(f'<path d="M10 90 Q14 20 90 10 Q86 80 10 90Z" fill="{c}"/><path d="M14 86 Q46 50 84 14" stroke="#fff" stroke-opacity=".5" stroke-width="2" fill="none"/>')

def sticky(c="#ffe066", text=""):
    return _svg(f'<rect x="8" y="8" width="84" height="84" rx="3" fill="{c}"/><path d="M8 78 L22 92 H8Z" fill="#000" opacity=".08"/>'
                f'<rect x="38" y="2" width="24" height="10" rx="2" fill="#fff" opacity=".7"/>'
                f'<path d="M20 34 H78 M20 50 H70 M20 66 H60" stroke="#000" stroke-opacity=".25" stroke-width="4" stroke-linecap="round"/>')

def lightbulb():
    return _svg('<circle cx="50" cy="40" r="30" fill="#ffe066"/><rect x="38" y="66" width="24" height="18" rx="4" fill="#9aa5b1"/><rect x="42" y="84" width="16" height="8" rx="3" fill="#6b7682"/>'
                '<path d="M40 44 Q50 30 60 44 L54 66 M46 66 L40 44" stroke="#f2b705" stroke-width="3" fill="none"/>'
                '<path d="M10 40 H2 M98 40 H90 M22 12 L16 6 M78 12 L84 6" stroke="#ffcf3f" stroke-width="5" stroke-linecap="round"/>')

def phone(screen="#ffffff"):
    return _svg('<rect x="22" y="4" width="56" height="92" rx="10" fill="#1d1d1f"/><rect x="26" y="10" width="48" height="80" rx="6" fill="%s"/>'
                '<rect x="42" y="6" width="16" height="3" rx="1.5" fill="#444"/>' % screen)

def pencil():
    return _svg('<g transform="rotate(45 50 50)"><rect x="42" y="6" width="16" height="70" fill="#ffcf3f"/><rect x="42" y="6" width="16" height="10" fill="#ff8fb1"/>'
                '<rect x="42" y="16" width="16" height="5" fill="#bbb"/><path d="M42 76 L58 76 L50 94Z" fill="#f5d7a8"/><path d="M47 88 L53 88 L50 94Z" fill="#333"/></g>')

def confetti_layer(w, h, n=70, colors=None, seed=7):
    import random
    rnd = random.Random(seed)
    colors = colors or ["#ff5a5f", "#ffb627", "#1fb58f", "#3fa7f5", "#b06ee8", "#ff8fb1", "#ffffff"]
    out = []
    for i in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        c = rnd.choice(colors); a = rnd.uniform(0, 180); s = rnd.uniform(14, 30)
        if i % 3 == 0:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{s/3:.0f}" fill="{c}"/>')
        else:
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{s:.0f}" height="{s/2.6:.0f}" rx="3" fill="{c}" transform="rotate({a:.0f} {x:.0f} {y:.0f})"/>')
    return f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">{"".join(out)}</svg>'

ART = {k: v for k, v in globals().items() if callable(v) and not k.startswith("_") and k != "confetti_layer"}
