import asyncio

from site_actions.auth import ensure_auth
from browser import start_browser

async def test_auth_flow():
    try:
        browser = await start_browser()
        await ensure_auth(browser)
        await asyncio.sleep(10)
    finally:
        await browser.stop()