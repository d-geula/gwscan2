from zendriver import cdp
import asyncio

from gwscan2.browser import start_browser
from gwscan2.site_actions.battlefield_actions import extract_battlefield_table
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

            for attempt in range(4):
                table_payloads = await extract_battlefield_table(authed_tab)
                player_rows = sum(1 for row in table_payloads if row["href"])
                missing_pop_cells = sum(
                    1 for row in table_payloads if row["href"] and not row["has_pop_cell"]
                )
                if player_rows > 0 and missing_pop_cells == 0:
                    break

                if attempt < 3:
                    await asyncio.sleep(0.25)
            else:
                raise RuntimeError("Battlefield table did not finish loading")

            players = parse_battlefield_table(table_payloads)
            print(players)
            await human_wait()
    finally:
        if browser is not None:
            await browser.stop()
