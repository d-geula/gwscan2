import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import random
import traceback
from typing import Literal

from dotenv import load_dotenv
from zendriver import cdp
import zendriver as zd

from gemini_pin_solver import solve_pin_image


BASE_URL = "https://main.gatewa.rs"
COMMAND_CENTER_URL = BASE_URL + "/base.php"
BANK_URL = BASE_URL + "/bank.php"
REFERER = COMMAND_CENTER_URL + "?game=gatewars"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = Path(__file__).resolve().parent / "profile"

LOGIN_MODAL = "#loginModal"
PIN_CAPTCHA = '#loginModal img[alt="PIN"]'
PIN_INPUT = "input#PIN"
USERNAME_INPUT = "input#usname"
EMAIL_INPUT = "input#usemail"
PASSWORD_INPUT = "input#uspass"
SUBMIT_BUTTON = "button[type=submit]"
COMMAND_CENTER_HEADING = 'main[class="mine"] > h3'
BANK_DEPOSIT_INPUT = "input#deposit_amount"


def log(message: str) -> None:
    print(f"[auto-login] {message}", flush=True)


async def pause_between_site_actions(
    reason: str, minimum: float = 0.8, maximum: float = 1.8
) -> None:
    delay = random.uniform(minimum, maximum)
    log(f"Pausing {delay:.2f}s before {reason}")
    await asyncio.sleep(delay)


def load_credentials() -> tuple[str, str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
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
        raise RuntimeError(
            f"Missing required credentials in .env: {', '.join(missing)}"
        )

    return username, email, password


async def start_browser(headless: bool) -> zd.Browser:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return await zd.start(headless=headless, user_data_dir=PROFILE_DIR)


async def get_auth_state(
    tab: zd.Tab, timeout: float = 10
) -> Literal["authenticated", "login_required"]:
    loop = asyncio.get_running_loop()
    start_time = loop.time()

    while loop.time() - start_time < timeout:
        heading = await tab.query_selector(COMMAND_CENTER_HEADING)
        if heading and heading.text == "Command Center":
            return "authenticated"

        login_modal = await tab.query_selector(LOGIN_MODAL)
        pin_input = await tab.query_selector(PIN_INPUT)
        if login_modal or pin_input:
            return "login_required"

        await tab.sleep(0.5)

    raise asyncio.TimeoutError("Timed out determining authentication state")


async def capture_page_debug(tab: zd.Tab) -> dict[str, object]:
    payload = await tab.evaluate(
        f"""
        (() => {{
            const heading = document.querySelector({json.dumps(COMMAND_CENTER_HEADING)});
            const loginModal = document.querySelector({json.dumps(LOGIN_MODAL)});
            const pinInput = document.querySelector({json.dumps(PIN_INPUT)});
            const alert = document.querySelector(".alert, .alert-danger, .alert-warning, .alert-success");
            const bodyText = (document.body?.innerText || "").replace(/\\s+/g, " ").trim();

            return {{
                url: window.location.href,
                title: document.title,
                heading_text: heading ? (heading.textContent || "").trim() : null,
                login_modal_present: Boolean(loginModal),
                pin_input_present: Boolean(pinInput),
                alert_text: alert ? (alert.textContent || "").trim() : null,
                body_excerpt: bodyText.slice(0, 800),
            }};
        }})()
        """
    )
    if not isinstance(payload, dict):
        return {"raw": payload}
    return payload


async def get_captcha_bytes(tab: zd.Tab) -> bytes:
    log("Extracting captcha image from the page")
    image_b64 = await tab.evaluate(
        f"""
        (() => {{
            const image = document.querySelector({json.dumps(PIN_CAPTCHA)});
            if (!image) {{
                throw new Error("Captcha image not found");
            }}

            const canvas = document.createElement("canvas");
            canvas.width = image.naturalWidth || image.width;
            canvas.height = image.naturalHeight || image.height;
            const context = canvas.getContext("2d");
            if (!context) {{
                throw new Error("Canvas context unavailable");
            }}

            context.drawImage(image, 0, 0);
            return canvas.toDataURL("image/png").split(",")[1];
        }})()
        """
    )
    if not isinstance(image_b64, str) or not image_b64:
        raise RuntimeError("Failed to extract captcha image data")
    log(f"Captcha image extracted: {len(image_b64)} base64 chars")
    return base64.b64decode(image_b64)


async def ensure_login_modal_open(tab: zd.Tab) -> None:
    log("Ensuring login modal is open")
    await tab.evaluate(
        f"""
        (() => {{
            const modal = document.querySelector({json.dumps(LOGIN_MODAL)});
            if (!modal) {{
                throw new Error("Login modal not found");
            }}

            if (window.jQuery && typeof window.jQuery(modal).modal === "function") {{
                window.jQuery(modal).modal("show");
                return "jquery";
            }}

            modal.style.display = "block";
            modal.classList.add("show", "in");
            modal.setAttribute("aria-hidden", "false");
            document.body.classList.add("modal-open");
            return "dom";
        }})()
        """
    )
    await tab.sleep(0.5)


async def perform_login(tab: zd.Tab, model: str) -> None:
    log("Loading credentials from .env")
    username, email, password = load_credentials()
    await ensure_login_modal_open(tab)

    pin = solve_pin_image(await get_captcha_bytes(tab), model=model, logger=log)
    log(f"Predicted PIN: {pin}")

    log("Filling login form")
    await (await tab.select(PIN_INPUT)).send_keys(pin)
    await (await tab.select(USERNAME_INPUT)).send_keys(username)
    await (await tab.select(EMAIL_INPUT)).send_keys(email)
    await (await tab.select(PASSWORD_INPUT)).send_keys(password)
    log("Submitting login form")
    await (await tab.select(SUBMIT_BUTTON)).click()
    await tab.sleep(1.0)
    page_debug = await capture_page_debug(tab)
    log(f"Post-submit page debug: {json.dumps(page_debug, ensure_ascii=True)}")


async def navigate_to_bank_and_deposit(tab: zd.Tab) -> None:
    await pause_between_site_actions("navigating to the bank page")
    log(f"Navigating to {BANK_URL}")
    await tab.send(cdp.page.navigate(url=BANK_URL, referrer=COMMAND_CENTER_URL))
    await tab.sleep(1.0)

    log("Waiting for bank deposit input")
    deposit_input = await tab.select(BANK_DEPOSIT_INPUT)
    deposit_value = deposit_input.get("value")
    log(f"Deposit input current value: {deposit_value!r}")

    await pause_between_site_actions("clicking the deposit button")
    log("Clicking deposit button")
    await tab.evaluate(
        f"""
        (() => {{
            const input = document.querySelector({json.dumps(BANK_DEPOSIT_INPUT)});
            if (!input) {{
                throw new Error("Deposit input not found");
            }}

            const form = input.closest("form");
            const button = form?.querySelector('button[type="submit"]');
            if (!button) {{
                throw new Error("Deposit submit button not found");
            }}

            button.click();
        }})()
        """
    )
    await tab.sleep(1.0)
    page_debug = await capture_page_debug(tab)
    log(f"Post-deposit page debug: {json.dumps(page_debug, ensure_ascii=True)}")


async def run(headless: bool, model: str) -> None:
    log(f"Starting browser (headless={headless})")
    browser = await start_browser(headless=headless)
    tab: zd.Tab | None = None
    try:
        log(f"Navigating to {COMMAND_CENTER_URL}")
        tab = await browser.get("about:blank")
        await tab.send(cdp.page.navigate(url=COMMAND_CENTER_URL, referrer=REFERER))

        initial_state = await get_auth_state(tab)
        log(f"Initial auth state: {initial_state}")
        if initial_state == "authenticated":
            log("Already authenticated")
        else:
            await perform_login(tab, model=model)

            log("Waiting for authenticated state after login submit")
            final_state = await get_auth_state(tab, timeout=15)
            log(f"Final auth state: {final_state}")
            if final_state != "authenticated":
                raise RuntimeError("Login verification failed")

            log("Login successful")

        await navigate_to_bank_and_deposit(tab)
        log("Waiting 1 second at the end for visual confirmation")
        await tab.sleep(1.0)
    except Exception as exc:
        log(f"Run failed: {exc!r}")
        if tab is not None:
            try:
                page_debug = await capture_page_debug(tab)
                log(f"Failure page debug: {json.dumps(page_debug, ensure_ascii=True)}")
            except Exception as debug_exc:
                log(f"Failed to capture page debug: {debug_exc!r}")
        log(traceback.format_exc())
        raise
    finally:
        log("Stopping browser")
        await browser.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Experimental automated GateWa.rs login"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the browser headlessly instead of opening a visible window.",
    )
    parser.add_argument(
        "--model",
        default="gemini-3.1-pro-preview",
        help="Gemini model to use for captcha solving.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(headless=args.headless, model=args.model))
