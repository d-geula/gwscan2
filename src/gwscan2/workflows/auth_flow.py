from typing import TYPE_CHECKING

from zendriver import cdp

from gwscan2.settings import COMMAND_CENTER_URL, REFERER
from gwscan2.site_actions.auth_actions import (
    get_auth_state,
    perform_login,
)

if TYPE_CHECKING:
    import zendriver as zd


async def get_authed_tab(browser: "zd.Browser") -> "zd.Tab":
    print("Checking if already authenticated")
    tab = await browser.get("about:blank")
    await tab.send(cdp.page.navigate(url=COMMAND_CENTER_URL, referrer=REFERER))

    if await get_auth_state(tab) == "authenticated":
        print("Already authenticated")
        return tab

    await perform_login(tab)

    if await get_auth_state(tab) != "authenticated":
        raise RuntimeError("Login verification failed")

    print("Login successful")
    return tab
