import asyncio
import os
from typing import TYPE_CHECKING, Literal

from dotenv import load_dotenv
from zendriver import cdp

from gwscan2.locators import LoginLocators as ll
from gwscan2.settings import COMMAND_CENTER_URL, REFERER

if TYPE_CHECKING:
    import zendriver as zd


def load_credentials() -> tuple[str, str, str]:
    """Load credentials from .env file."""
    load_dotenv()
    username = os.getenv("GW_USERNAME", "").strip()
    email = os.getenv("GW_EMAIL", "").strip()
    password = os.getenv("GW_PASSWORD", "").strip()

    missing = [
        name
        for name, value in (
            ("GW_USERNAME", username),
            ("GW_EMAIL", email),
            ("GW_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required credentials in .env: {joined}")

    return username, email, password


async def print_captcha_url(tab: "zd.Tab") -> None:
    captcha_src = (await tab.select(ll.PIN_CAPTCHA)).get("src")
    print(f"Captcha URL: {tab.url + captcha_src}")


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


async def ensure_auth(browser: "zd.Browser") -> "zd.Tab":
    username, email, password = load_credentials()

    print("Checking if already authenticated")
    tab = await browser.get("about:blank")
    await tab.send(cdp.page.navigate(url=COMMAND_CENTER_URL, referrer=REFERER))

    if await get_auth_state(tab) == "authenticated":
        print("Already authenticated")
        return tab

    print("Attempting login...")
    await (await tab.select(ll.LOGIN_MODAL)).click()

    await print_captcha_url(tab)
    pin = input("PIN: ").strip()

    await (await tab.select(ll.PIN)).send_keys(pin)
    await (await tab.select(ll.USERNAME)).send_keys(username)
    await (await tab.select(ll.EMAIL)).send_keys(email)
    await (await tab.select(ll.PASSWORD)).send_keys(password)

    await (await tab.select(ll.SUBMIT)).click()

    if await get_auth_state(tab) != "authenticated":
        raise RuntimeError("Login verification failed")

    print("Login successful")
    return tab
