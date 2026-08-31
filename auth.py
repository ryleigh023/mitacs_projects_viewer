"""
Authentication helper for the Mitacs GRI Student Portal.

Logs in once with Playwright, then persists the browser's storage state
(cookies + local storage) to disk so subsequent runs can skip the login
step entirely -- fewer requests against the portal, and faster reruns.
"""

from __future__ import annotations

import getpass
import logging
import os
import random
from pathlib import Path

from playwright.sync_api import BrowserContext, Page

from config import SELECTORS, SETTINGS

logger = logging.getLogger(__name__)


def _load_credentials() -> tuple[str, str]:
    """Read credentials from environment variables, prompting if missing.

    Never hardcode credentials in source files -- set MITACS_USERNAME /
    MITACS_PASSWORD in a local .env file (see .env.example) or answer the
    interactive prompt instead.
    """
    username = os.getenv("MITACS_USERNAME") or input("Mitacs portal username/email: ").strip()
    password = os.getenv("MITACS_PASSWORD") or getpass.getpass("Mitacs portal password: ")

    if not username or not password:
        raise RuntimeError("Mitacs credentials are required to continue.")

    return username, password


def get_authenticated_context(playwright) -> BrowserContext:
    """Return a Playwright BrowserContext that is logged into the GRI portal,
    reusing a saved session when one exists and is still valid."""
    browser = playwright.chromium.launch(headless=SETTINGS.headless)
    saved_session = SETTINGS.storage_state_path if Path(SETTINGS.storage_state_path).exists() else None

    context = browser.new_context(
        storage_state=saved_session,
        user_agent=random.choice(SETTINGS.user_agents),
    )

    if saved_session:
        logger.info("Reusing saved session from %s", SETTINGS.storage_state_path)
        page = context.new_page()
        page.goto(SELECTORS.projects_url, timeout=SETTINGS.page_load_timeout_ms)
        still_valid = _looks_logged_in(page)
        page.close()
        if still_valid:
            return context
        logger.warning("Saved session expired -- logging in again.")

    _login(context)
    context.storage_state(path=SETTINGS.storage_state_path)
    logger.info("Session saved to %s for future runs", SETTINGS.storage_state_path)
    return context


def _looks_logged_in(page: Page) -> bool:
    try:
        page.wait_for_selector(SELECTORS.post_login_marker, timeout=5_000)
        return True
    except Exception:
        return False


def _login(context: BrowserContext) -> None:
    username, password = _load_credentials()
    page = context.new_page()

    logger.info("Navigating to login page...")
    page.goto(SELECTORS.login_url, timeout=SETTINGS.page_load_timeout_ms)

    page.fill(SELECTORS.username_input, username)
    page.fill(SELECTORS.password_input, password)
    page.click(SELECTORS.login_button)

    page.wait_for_selector(SELECTORS.post_login_marker, timeout=SETTINGS.page_load_timeout_ms)
    logger.info("Login successful.")
    page.close()
