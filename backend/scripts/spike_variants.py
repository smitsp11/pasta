"""Spike 2: mobile, geo proxy, persist_profile. Settles: plan supports proxies; mobile dims.
   .venv/bin/python scripts/spike_variants.py
"""
import asyncio, os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from steel import AsyncSteel

VARIANTS = {
    "mobile": dict(device_config={"device": "mobile"}),
    "geo:CA": dict(use_proxy={"geolocation": {"country": "CA"}}, dimensions={"width": 1280, "height": 800}),
    "geo:DE": dict(use_proxy={"geolocation": {"country": "DE"}}, dimensions={"width": 1280, "height": 800}),
    "persist": dict(persist_profile=True, dimensions={"width": 1280, "height": 800}),
}

async def one(client, key, label, kw):
    try:
        s = await client.sessions.create(api_timeout=120_000, inactivity_timeout=60_000, **kw)
    except Exception as e:
        print(f"[{label}] create FAILED: {type(e).__name__}: {e}"); return
    try:
        print(f"[{label}] id={s.id} dims={s.dimensions} profile_id={s.profile_id} device={s.device_config}")
        pw = await async_playwright().start()
        sep = "&" if "?" in s.websocket_url else "?"
        b = await pw.chromium.connect_over_cdp(f"{s.websocket_url}{sep}apiKey={key}")
        ctx = b.contexts[0]; page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://ipinfo.io/json", wait_until="domcontentloaded", timeout=45_000)
        body = (await page.inner_text("body"))[:300].replace("\n", " ")
        ua = await page.evaluate("navigator.userAgent"); vp = await page.evaluate("[innerWidth, innerHeight, 'ontouchstart' in window]")
        print(f"[{label}] viewport={vp} ua={ua[:70]}")
        print(f"[{label}] ipinfo: {body}")
        await b.close(); await pw.stop()
    finally:
        await client.sessions.release(s.id)

async def main():
    load_dotenv(); key = os.environ["STEEL_API_KEY"]; client = AsyncSteel(steel_api_key=key)
    for label, kw in VARIANTS.items():
        await one(client, key, label, kw)

asyncio.run(main())
