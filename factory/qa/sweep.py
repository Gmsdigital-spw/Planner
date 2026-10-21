import asyncio, sys, json
from playwright.async_api import async_playwright
import sys
PAGE="file://"+sys.argv[1]
OUT=(sys.argv[2] if len(sys.argv)>2 else "/tmp/qa")+"/"
async def main():
    errs=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await b.new_page(viewport={"width":390,"height":844},device_scale_factor=2)
        pg.on("pageerror",lambda e: errs.append("PAGEERROR "+str(e)))
        pg.on("console",lambda m: errs.append("CONSOLE "+m.type+" "+m.text) if m.type in("error","warning") else None)
        await pg.goto(PAGE); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=OUT+"01_home.png")
        steps=[]
        async def click(sel,name,back=True):
            try:
                el=pg.locator(sel).first
                if await el.count()==0: steps.append(name+": MISSING "+sel); return
                await el.click(timeout=3000); await pg.wait_for_timeout(900)
                await pg.screenshot(path=OUT+name+".png"); steps.append(name+": ok")
            except Exception as e: steps.append(name+": FAIL "+str(e)[:150])
            if back:
                try:
                    if await pg.locator("#sheet.on").count(): await pg.locator("#shClose").click(); await pg.wait_for_timeout(300)
                except Exception: pass
        await click("#coreBtn","02_foreman")
        for f in ["funnel","trading"]: await click(f'[data-floorinfo="{f}"]',"03_floor_"+f)
        for fold in ["inbox","launch","treasury","mission","settings"]:
            await click(f"#fold-{fold} > summary","04_fold_"+fold,back=False)
        await click('[data-bay="third"]',"05_marketing",back=False)
        await pg.screenshot(path=OUT+"05b_marketing_full.png",full_page=True)
        await click('[data-agent="hawk"]',"05c_agent_hawk")
        await click('#v-bay-third [data-go="command"]',"05d_back",back=False)
        await click('[data-bay="etsy"]',"06_product",back=False)
        await pg.screenshot(path=OUT+"06b_product_full.png",full_page=True)
        await click('[data-pf="ideas"]',"06c_ideas")
        await click('[data-pf="lane:mugwrap"]',"06d_lane")
        await click('[data-pf="holiday"]',"06e_holiday")
        await click('#etsyHead [data-go="command"]',"06f_back",back=False)
        await click('[data-bay="youtube"]',"07_studio",back=False)
        await pg.screenshot(path=OUT+"07b_studio_full.png",full_page=True)
        await click('#ytHead [data-go="command"]',"07c_back",back=False)
        await b.close()
    print("\n".join(steps)); print("---ERRORS---"); print("\n".join(sorted(set(errs)))[:4000])
asyncio.run(main())
