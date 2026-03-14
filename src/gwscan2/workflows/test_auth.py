import asyncio

from gwscan2.browser import start_browser
from gwscan2.workflows.authed import get_authed_tab


async def test_auth_flow() -> None:
    browser = None
    try:
        browser = await start_browser()
        await get_authed_tab(browser)
        await asyncio.sleep(10)
    finally:
        if browser is not None:
            await browser.stop()
