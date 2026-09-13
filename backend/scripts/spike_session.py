"""Spike 1: create a Steel session, connect Playwright over CDP, load a page, release.
Settles: session kwargs, URL fields, release semantics.   .venv/bin/python scripts/spike_session.py
"""
import asyncio, os, time
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from steel import AsyncSteel

async def main():
    load_dotenv(); key = os.environ["STEEL_API_KEY"]
    client = AsyncSteel(steel_api_key=key)
    t0 = time.time()
    s = await client.sessions.create(api_timeout=120_000, inactivity_timeout=60_000,
                                     dimensions={"width": 1280, "height": 800})
    print(f"created in {time.time()-t0:.1f}s")
    for f in ("id", "status", "websocket_url", "debug_url", "session_viewer_url", "dimensions", "created_at", "timeout"):
        print(f"  {f}: {getattr(s, f, None)}")
    pw = await async_playwright().start()
    sep = "&" if "?" in s.websocket_url else "?"
    browser = await pw.chromium.connect_over_cdp(f"{s.websocket_url}{sep}apiKey={key}")
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    await page.goto("https://example.com", wait_until="domcontentloaded")
    print("  page title:", await page.title(), "| viewport:", await page.evaluate("[innerWidth, innerHeight]"))
    await browser.close(); await pw.stop()
    r = await client.sessions.release(s.id)
    print("  release:", r)
    s2 = await client.sessions.retrieve(s.id)
    print("  status after release:", s2.status, "| credits_used:", s2.credits_used)
    try:
        print("  second release:", await client.sessions.release(s.id))
    except Exception as e:
        print("  second release raised:", type(e).__name__, e)

asyncio.run(main())
