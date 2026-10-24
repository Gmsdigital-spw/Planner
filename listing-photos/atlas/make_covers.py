import sys, os
sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import place
from PIL import Image, ImageDraw, ImageFont
S = sys.argv[1]; P = S + "/pages"
FD = "/usr/share/fonts/truetype/google-fonts/"
def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f
def pg(lid, n): return f"{P}/{lid}/p-{n:02d}.png"
# lid, scene, pages, title, sub, color, crop (x0,y0,w) in scene px (5:4), label pos
L = [
 ("4597749137","christmas",[pg("749137",1),pg("749137",2)],"Christmas Party Games","8 GAMES  ·  PRINTABLE PDF","#9B2A2E",(46,0,1357),"top"),
 ("4597755725","christmas",[pg("755725",1),pg("755725",3)],"Secret Santa Kit","OFFICE GIFT EXCHANGE  ·  PRINTABLE","#1F5A41",(150,180,1100),"bottom"),
 ("4600177510","christmas",[pg("177510",1),pg("177510",3)],"Cookie Swap Party Kit","13 PRINTABLE PAGES","#8E2433",(0,60,1240),"top"),
 ("4598379368","christmas",[pg("379368",1),pg("379368",9)],"36 Christmas Party Awards","PRINTABLE PDF  ·  INSTANT DOWNLOAD","#8E2433",(91,0,1357),"bottom"),
 ("4597998190","christmas",[pg("998190",1),pg("998190",3)],"24 Days of Christmas","FAMILY ACTIVITY CARDS  ·  PRINTABLE","#1F5A41",(220,130,1150),"top"),
 ("4597743627","clipboard",[pg("743627",1)],"Thanksgiving Family Games","TRIVIA  ·  BINGO  ·  PRINTABLE","#B8582A",(46,0,1357),"bottom"),
 ("4598501430","clipboard",[pg("501430",9)],"Friendsgiving Party Kit","7 GAMES  ·  POTLUCK  ·  PRINTABLE","#B9603F",(170,60,1200),"top"),
 ("4597755593","clipboard",[pg("755593",1)],"New Year's Eve Party Games","FAMILY FRIENDLY  ·  PRINTABLE","#1E2F4F",(0,0,1357),"bottom"),
 ("4598535050","clipboard",[pg("535050",13)],"2027 Debt Payoff Tracker","SNOWBALL & AVALANCHE  ·  16 PAGES","#5E6F4E",(230,80,1150),"top"),
 ("4598358161","clipboard",[pg("358161",4)],"2027 Savings Challenge","COLOR-IN TRACKERS  ·  14 PAGES","#7A5236",(91,0,1357),"top"),
 ("4598358317","planner",[pg("358317",1),pg("358317",9)],"2027 Goal Setting Workbook","12-WEEK PLAN  ·  14 PAGES","#8A6A44",(46,0,1357),"top"),
 ("4599444986","planner",[pg("444986",1),pg("444986",5)],"2027 No-Buy Year Planner","NO-SPEND TRACKERS  ·  13 PAGES","#5F6B40",(130,120,1200),"bottom"),
 ("4596203264","planner",[S+"/src/dec.png",S+"/src/dinner.png"],"2026 Christmas Planner","BUDGET  ·  GIFTS  ·  MENU  ·  16 PAGES","#1F5A41",(91,0,1357),"bottom"),
 ("4598721247","frame",[f"{P}/pink-christmas-verse-art/p-02.png"],"Pink Christmas Bible Verse Prints","SET OF 6  ·  INSTANT DOWNLOAD","#B5566A",(46,0,1357),"bottom"),
 ("4598659189","frame",[f"{P}/pink-coquette-verse-art/p-02.png"],"Pink Bible Verse Wall Art","SET OF 6  ·  INSTANT DOWNLOAD","#B04A62",(200,40,1100),"bottom"),
 ("4596406689","phone",[S+"/src/app.png"],"ADHD Budget Planner App","SAFE-TO-SPEND DAILY  ·  NO SPREADSHEETS","#1F6F63",(0,520,941),"top"),
 ("4596095937","phone",[S+"/src/sheet.png"],"Monthly Budget Spreadsheet","GOOGLE SHEETS & EXCEL","#1F6F4F",(0,560,941),"top"),
]
def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines
def label(img, title, sub, color, pos):
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    ft = font("Lora-Variable.ttf", 118, 650); fs = font("Poppins-Medium.ttf", 38)
    maxw = int(W * 0.78)
    lines = wrap(d, title, ft, maxw)
    lh = 128; th = lh * len(lines); sh = 50; pad = 46
    bw = max(max(d.textlength(l, font=ft) for l in lines), d.textlength(sub, font=fs) + 40) + pad * 2
    bh = th + sh + pad * 2 + 6
    x0 = (W - bw) / 2; y0 = 70 if pos == "top" else H - bh - 70
    d.rounded_rectangle((x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10), 26, fill=(0, 0, 0, 40))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 26, fill=(251, 247, 240, 245))
    d.rounded_rectangle((x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14), 18, outline=color, width=3)
    y = y0 + pad - 10
    for l in lines:
        d.text((W / 2, y), l, font=ft, fill=color, anchor="ma"); y += lh
    d.text((W / 2, y + 14), sub, font=fs, fill=(90, 82, 74), anchor="ma")
for lid, scene, pages, title, sub, color, (cx, cy, cw), pos in L:
    ch = round(cw * 0.8)
    if scene == "phone": ch = round(cw * 0.8)
    sc = 2000 / cw
    big = place.place(scene, pages, scale=sc)
    img = big.crop((round(cx * sc), round(cy * sc), round(cx * sc) + 2000, round(cy * sc) + 1600)).convert("RGB")
    label(img, title, sub, color, pos)
    img.save(f"{S}/covers/{lid}.jpg", "JPEG", quality=88, optimize=True)
    print(lid, img.size, os.path.getsize(f"{S}/covers/{lid}.jpg") // 1024, "KB")
