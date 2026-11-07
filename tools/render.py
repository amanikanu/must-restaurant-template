"""Dev helper: screenshots the built page (desktop + mobile) using Playwright.

Usage:  python3 tools/render.py [--mobile]
Note: on this sandbox the browser needs the locally extracted libs:
  export LD_LIBRARY_PATH=/tmp/debs/root/usr/lib/x86_64-linux-gnu
"""
import asyncio, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "screenshots"


async def main(mobile=False):
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        vp = {"width": 390, "height": 844} if mobile else {"width": 1440, "height": 950}
        pg = await b.new_page(viewport=vp, device_scale_factor=2 if mobile else 1,
                              is_mobile=mobile, has_touch=mobile)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto((ROOT / "index.html").as_uri())
        await pg.wait_for_timeout(2400)
        await pg.screenshot(path=str(OUT / ("v2-m390.png" if mobile else "v2-hero.png")))
        for sel, name in [("#about", "about"), ("#menu", "menu"), (".why", "why"),
                          ("#say", "say"), ("#contact", "footer")]:
            el = await pg.query_selector(sel)
            await el.scroll_into_view_if_needed()
            await pg.wait_for_timeout(1400)
            await el.screenshot(path=str(OUT / f"{'m-' if mobile else ''}{name}.png"))
        print("page errors:", errs)
        await b.close()


if __name__ == "__main__":
    asyncio.run(main("--mobile" in sys.argv))
