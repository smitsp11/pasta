"""Spike 3: persist a profile in session A, poll until READY, reuse in session B, read the cookie.
Settles: profile status call + time-to-READY.   .venv/bin/python scripts/spike_profile.py
"""
import asyncio, os, time
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from steel import AsyncSteel

async def connect(pw, s, key):
    sep = "&" if "?" in s.websocket_url else "?"
    b = await pw.chromium.connect_over_cdp(f"{s.websocket_url}{sep}apiKey={key}")
    ctx = b.contexts[0]; page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    return b, ctx, page

async def main():
    load_dotenv(); key = os.environ["STEEL_API_KEY"]; client = AsyncSteel(steel_api_key=key)
    pw = await async_playwright().start()
    a = await client.sessions.create(api_timeout=120_000, persist_profile=True, dimensions={"width": 1280, "height": 800})
    print("A:", a.id, "profile_id:", a.profile_id)
    b, ctx, page = await connect(pw, a, key)
    await page.goto("https://example.com", wait_until="domcontentloaded")
    await ctx.add_cookies([{"name": "crucible_seen", "value": "1", "domain": "example.com", "path": "/"}])
    await page.evaluate("localStorage.setItem('crucible', 'yes')")
    await b.close()
    await client.sessions.release(a.id); t0 = time.time()
    while True:
        p = await client.profiles.get(a.profile_id)
        print(f"  profile status after {time.time()-t0:.0f}s: {p.status}")
        if str(p.status).upper() in ("READY", "FAILED") or time.time() - t0 > 180: break
        await asyncio.sleep(3)
    s2 = await client.sessions.create(api_timeout=120_000, profile_id=a.profile_id, dimensions={"width": 1280, "height": 800})
    print("B:", s2.id, "profile_id:", s2.profile_id)
    b2, ctx2, page2 = await connect(pw, s2, key)
    await page2.goto("https://example.com", wait_until="domcontentloaded")
    cookies = [c["name"] for c in await ctx2.cookies("https://example.com")]
    ls = await page2.evaluate("localStorage.getItem('crucible')")
    print("  cookies in B:", cookies, "| localStorage:", ls)
    await b2.close(); await pw.stop(); await client.sessions.release(s2.id)

asyncio.run(main())
