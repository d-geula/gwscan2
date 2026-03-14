import asyncio

from gwscan2.browser import start_browser
from gwscan2.site_actions.auth import ensure_auth


async def test_auth_flow() -> None:
    browser = None
    try:
        browser = await start_browser()
        await ensure_auth(browser)
        await asyncio.sleep(10)
    finally:
        if browser is not None:
            await browser.stop()
