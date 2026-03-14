import asyncio
from typing import TYPE_CHECKING, Literal

from gwscan2.settings import load_credentials

from gwscan2.locators import LoginLocators as ll

if TYPE_CHECKING:
    import zendriver as zd


async def print_captcha_url(tab: "zd.Tab") -> None:
    captcha_src = (await tab.select(ll.PIN_CAPTCHA)).get("src")
    print(f"Captcha URL: {tab.url + captcha_src}")  # pyright: ignore[reportOperatorIssue]


async def get_auth_state(
    tab: "zd.Tab", timeout: float = 10
) -> Literal["authenticated", "login_required"]:
    """Wait until the page clearly resolves to either auth state."""
    loop = asyncio.get_running_loop()
    start_time = loop.time()

    while loop.time() - start_time < timeout:
        heading = await tab.query_selector(ll.COMMAND_CENTER_HEADING)
        if heading and heading.text == "Command Center":
            return "authenticated"

        login_modal = await tab.query_selector(ll.LOGIN_MODAL)
        if login_modal:
            return "login_required"

        await tab.sleep(0.5)

    raise asyncio.TimeoutError("Timed out determining authentication state")


async def perform_login(
    tab: "zd.Tab"
) -> None:
    print("Attempting login...")
    credentials = load_credentials()
    await (await tab.select(ll.LOGIN_MODAL)).click()

    await print_captcha_url(tab)
    pin = input("PIN: ").strip()

    await (await tab.select(ll.PIN)).send_keys(pin)
    await (await tab.select(ll.USERNAME)).send_keys(credentials[0])
    await (await tab.select(ll.EMAIL)).send_keys(credentials[1])
    await (await tab.select(ll.PASSWORD)).send_keys(credentials[2])

    await (await tab.select(ll.SUBMIT)).click()
