import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from zendriver import cdp

from selectors import LoginSelectors as ls
from settings import COMMAND_CENTER_URL, REFERER

if TYPE_CHECKING:
    import zendriver as zd


def load_credentials() -> tuple[str, str, str]:
    """Load credentials from .env file"""
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
    captcha_src = (await tab.select(ls.PIN_CAPTCHA)).get("src")
    print(f"Captcha URL: {tab.url + captcha_src}")


async def ensure_auth(browser: "zd.Browser") -> "zd.Tab":
    username, email, password = load_credentials()

    print("Checking if already authenticated")
    tab = await browser.get("about:blank")
    tab.send(cdp.page.navigate(url=COMMAND_CENTER_URL, referrer=REFERER))

    if (await tab.select(ls.COMMAND_CENTER_HEADING)).text == "Command Center":
        print("Already authenticated")
        return tab

    print("Attempting login...")
    # Open the login modal
    await (await tab.select(ls.LOGIN_MODAL)).click()

    # Get PIN challenge image; user enters PIN
    await print_captcha_url(tab)
    pin = input("PIN: ").strip()

    # Fill in: PIN, username, email, and password
    await (await tab.select(ls.PIN)).send_keys(pin)
    await (await tab.select(ls.USERNAME)).send_keys(username)
    await (await tab.select(ls.EMAIL)).send_keys(email)
    await (await tab.select(ls.PASSWORD)).send_keys(password)

    # Submit creds
    await (await tab.select(ls.SUBMIT)).click()

    # Verify login based on availability of specific text
    if (await tab.select(ls.COMMAND_CENTER_HEADING)).text != "Command Center":
        raise RuntimeError("Login verification failed")

    print("Login successful")
    return tab
