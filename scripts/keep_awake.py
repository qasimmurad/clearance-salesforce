"""Keep the Clearance app on Streamlit Community Cloud from hibernating.

Community Cloud puts an app to sleep after 12 hours without traffic, and a
plain HTTP GET does not reliably count as traffic. A sleeping app shows a page
with a "Yes, get this app back up!" button that has to be clicked, so this
loads the app in headless Chromium and clicks that button if it is there.

Exit codes
  0  the app was already awake, or it was asleep and has been woken
  1  the page failed to load, or the app did not wake after the click

A screenshot of the final state is always written to /tmp/state.png, and the
GitHub Actions workflow uploads it as an artifact.
"""

from __future__ import annotations

import re
import sys
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, sync_playwright

APP_URL = "https://clearance-salesforce-hmafug6z9asdx5l2swspbu.streamlit.app/"
SCREENSHOT_PATH = "/tmp/state.png"

LOAD_TIMEOUT_MS = 60_000
SETTLE_MS = 5_000
# How long to keep looking for the wake button, or the running app, once the
# page has settled. The app boots inside an iframe and took about 8 seconds to
# render when this was written, so a single check at the 5 second mark can see
# neither and would miss a wake button that renders late.
DETECT_TIMEOUT_S = 30
WAKE_TIMEOUT_S = 90
POLL_MS = 2_000

WAKE_BUTTON_TEXT = re.compile(r"get this app back up", re.IGNORECASE)
# On Community Cloud the app renders inside an iframe at /~/+/, so the
# container has to be looked for in every frame, not only the top-level page.
APP_CONTAINER = '[data-testid="stAppViewContainer"]'


def find_wake_button(page: Page) -> Locator | None:
    """Return the visible wake button from any frame on the page, or None."""
    for frame in page.frames:
        try:
            candidates = frame.locator("button, [role='button']").filter(
                has_text=WAKE_BUTTON_TEXT
            )
            for i in range(candidates.count()):
                if candidates.nth(i).is_visible():
                    return candidates.nth(i)
        except PlaywrightError:
            # A frame can detach while the page navigates. Check the others.
            continue
    return None


def app_is_rendered(page: Page) -> bool:
    """True if Streamlit's main app container is visible in any frame."""
    for frame in page.frames:
        try:
            container = frame.locator(APP_CONTAINER)
            if container.count() and container.first.is_visible():
                return True
        except PlaywrightError:
            continue
    return False


def run(page: Page) -> int:
    try:
        response = page.goto(
            APP_URL, timeout=LOAD_TIMEOUT_MS, wait_until="domcontentloaded"
        )
    except PlaywrightError as exc:
        print(f"Page failed to load: {exc}")
        return 1

    page.wait_for_timeout(SETTLE_MS)

    button = None
    deadline = time.monotonic() + DETECT_TIMEOUT_S
    while True:
        button = find_wake_button(page)
        if button is not None or app_is_rendered(page):
            break
        if time.monotonic() >= deadline:
            break
        page.wait_for_timeout(POLL_MS)

    if button is None:
        # A deleted or renamed app is served as a 404 page with no wake button.
        if response is not None and response.status >= 400:
            print(f"Page failed to load: HTTP {response.status} from {APP_URL}")
            return 1
        print("App already awake")
        return 0

    try:
        button.click(timeout=15_000)
    except PlaywrightError as exc:
        # If the click starts a navigation, the button's frame can detach
        # mid-click. That only counts as a failure if the button is still there.
        if find_wake_button(page) is not None:
            print(f"Could not click the wake button: {exc}")
            return 1
    print("App was asleep, clicked the wake button")

    deadline = time.monotonic() + WAKE_TIMEOUT_S
    clear_checks = 0
    while time.monotonic() < deadline:
        page.wait_for_timeout(POLL_MS)
        if app_is_rendered(page):
            print("Woke app")
            return 0
        if find_wake_button(page) is None:
            # Require two clean checks in a row, so a blank moment while the
            # page reloads is not mistaken for the button going away.
            clear_checks += 1
            if clear_checks >= 2:
                print("Woke app")
                return 0
        else:
            clear_checks = 0

    print(f"Wake button still showing {WAKE_TIMEOUT_S} seconds after clicking it")
    return 1


def main() -> int:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            return run(page)
        finally:
            try:
                page.screenshot(path=SCREENSHOT_PATH, full_page=True)
                print(f"Screenshot saved to {SCREENSHOT_PATH}")
            except PlaywrightError as exc:
                print(f"Could not save screenshot: {exc}")
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
