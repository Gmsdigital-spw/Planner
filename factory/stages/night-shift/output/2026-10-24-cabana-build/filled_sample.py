"""Photo 3 sample: the same invite typed with a different party, refonted, to show typing works."""
import sys, pikepdf, subprocess
src, out = sys.argv[1], sys.argv[2]
vals = {"pink1_name": "Mia Turns Seven", "pink1_date": "SUNDAY, JUNE 7, 2026", "pink1_time": "11:00 AM TO 1:30 PM",
        "pink1_place": "MIA'S BACKYARD", "pink1_addr": "48 MAGNOLIA LANE", "pink1_rsvp": "TO MOM AT 555-0188 BY MAY 30"}
p = pikepdf.open(src)
for pg in p.pages:
    for a in pg.get("/Annots", []):
        t = str(a.get("/T", ""))
        if t in vals: a.V = pikepdf.String(vals[t])
p.save("/tmp/filled_raw.pdf")
subprocess.run(["python3", "/home/claude/planner/tools/acro_font.py", "/tmp/filled_raw.pdf", out], check=True)
