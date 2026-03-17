from zendriver import cdp

from gwscan2.browser import start_browser
from gwscan2.site_actions.battlefield_actions import get_battlefield_table
from gwscan2.parsing import parse_battlefield_table
from gwscan2.workflows.auth_flow import get_authed_tab
from gwscan2.settings import BATTLEFIELD_URL, REFERER
from gwscan2.utils import human_wait


async def run_test_battlefield_scan(page_range: range) -> None:
    browser = None
    try:
        browser = await start_browser()
        authed_tab = await get_authed_tab(browser)
        await human_wait()

        for page in page_range:
            URL = f"{BATTLEFIELD_URL}{page}"
            await authed_tab.send(cdp.page.navigate(url=URL, referrer=REFERER))
            table_payloads = await get_battlefield_table(authed_tab)
            players = parse_battlefield_table(table_payloads)
            print(players)
            await human_wait()
    finally:
        if browser is not None:
            await browser.stop()
