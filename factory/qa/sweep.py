import asyncio, sys, json
from playwright.async_api import async_playwright
# Atlas Hub page sweep (V8 "The Turning Point", Oct 24 2026). Same call as before:
#   python3 factory/qa/sweep.py <page.html> [out dir] [width] [engine report fixture]
# Opens the page in a phone-size Chromium, walks Today -> Work -> Agents -> More and every screen behind More,
# and prints one line per step plus every PAGEERROR / console error. A FAIL or PAGEERROR is a page bug.
# The old Starship sweep is kept as sweep_v7.py for the pre-V8 page.
PAGE="file://"+sys.argv[1]
OUT=(sys.argv[2] if len(sys.argv)>2 else "/tmp/qa")+"/"
async def main():
    errs=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        W=int(sys.argv[3]) if len(sys.argv)>3 else 390
        pg=await b.new_page(viewport={"width":W,"height":844},device_scale_factor=2)
        pg.on("pageerror",lambda e: errs.append("PAGEERROR "+str(e)))
        pg.on("console",lambda m: errs.append("CONSOLE "+m.type+" "+m.text) if m.type in("error","warning") and "Failed to load resource" not in m.text else None)
        REPORT=sys.argv[4] if len(sys.argv)>4 else None
        if REPORT:
            body=open(REPORT,"rb").read()
            await pg.route("**/factory/engine/public/report.json*",lambda r: r.fulfill(status=200,content_type="application/json",body=body))
        await pg.goto(PAGE); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=OUT+"01_today.png")
        steps=[]
        async def noscroll(name):
            sw=await pg.evaluate("Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)"); cw=await pg.evaluate("document.documentElement.clientWidth")
            steps.append(f"noscroll_{name}: "+("ok" if sw<=cw else f"FAIL scrollWidth {sw} > {cw}"))
        async def tab(id,name):
            try:
                el=pg.locator(f'#tabs [data-go="{id}"]').first
                if await el.count()==0: steps.append(name+": MISSING tab "+id); return
                await el.click(timeout=3000); await pg.wait_for_timeout(700)
                on=await pg.locator(f"#p-{id}.on").count()
                txt=await pg.locator(f"#p-{id}").inner_text()
                steps.append(name+": "+("ok" if on and len(txt)>40 and "hit an error" not in txt else f"FAIL (on={on}, chars={len(txt)})"))
                await pg.screenshot(path=OUT+name+".png")
            except Exception as e: steps.append(name+": FAIL "+str(e)[:150])
        n=await pg.locator("#p-today .wrow").count(); steps.append("01_today_rows: "+("ok "+str(n) if n>=4 else f"FAIL {n} rows"))
        n=await pg.locator("#p-today .next").count(); steps.append("01b_next_card: "+("ok" if n else "FAIL missing"))
        await noscroll("today")
        await tab("work","02_work"); await noscroll("work")
        await tab("agents","03_agents"); await noscroll("agents")
        n=await pg.locator("#p-agents [data-agent]").count(); steps.append("03b_agent_rows: "+("ok "+str(n) if n>=20 else f"FAIL {n}"))
        try:
            await pg.locator('#p-agents [data-agent]').first.click(timeout=3000); await pg.wait_for_timeout(400)
            on=await pg.locator("#drawer.on").count(); steps.append("03c_agent_drawer: "+("ok" if on else "FAIL"))
            await pg.locator("#dClose").click(); await pg.wait_for_timeout(200)
        except Exception as e: steps.append("03c_agent_drawer: FAIL "+str(e)[:120])
        await pg.locator('#tabs [data-go="more"]').click(); await pg.wait_for_timeout(300)
        on=await pg.locator("#sheetNav.on").count(); steps.append("04_more_sheet: "+("ok" if on else "FAIL"))
        await pg.evaluate("document.querySelector('#sheetNav').classList.remove('on')")
        for v in ["etsy","marketing","shorts","trading","money","approvals","missions","engine","settings","parked"]:
            await pg.evaluate(f"location.hash='#{v}'"); await pg.wait_for_timeout(600)
            on=await pg.locator(f"#p-{v}.on").count(); txt=await pg.locator(f"#p-{v}").inner_text()
            steps.append(f"05_{v}: "+("ok" if on and len(txt)>40 and "hit an error" not in txt else f"FAIL (on={on}, chars={len(txt)})"))
            await noscroll(v)
            if v in("etsy","trading","settings"): await pg.screenshot(path=OUT+f"05_{v}.png",full_page=True)
        n=await pg.locator('#p-settings [data-sw="paused"]').count(); steps.append("06_pause_switch: "+("ok" if n else "FAIL missing"))
        await pg.evaluate("location.hash='#today'"); await pg.wait_for_timeout(500)
        await b.close()
    print("\n".join(steps)); print("---ERRORS---"); print("\n".join(sorted(set(errs)))[:4000])
asyncio.run(main())
