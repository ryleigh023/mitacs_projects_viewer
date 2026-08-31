"""
Core scraping logic for the Mitacs GRI project listing.

Design notes:
  - Every field extraction is wrapped so a missing/renamed element degrades
    to "N/A" instead of crashing the whole run.
  - `_polite_wait` inserts a randomized delay between page interactions so
    the scraper behaves like a human, not a burst client.
  - `_with_retries` wraps flaky network/render operations (timeouts, slow
    renders) with exponential backoff.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, TypeVar

from playwright.sync_api import BrowserContext, Locator, Page

from config import SELECTORS, SETTINGS

logger = logging.getLogger(__name__)
T = TypeVar("T")

FIELDS = {
    "Project Title": SELECTORS.title,
    "Host University": SELECTORS.university,
    "Host Province": SELECTORS.province,
    "Professor Name": SELECTORS.professor,
    "Department": SELECTORS.department,
    "Project Description": SELECTORS.description,
    "Required Skills": SELECTORS.skills,
    "Preferred Disciplines": SELECTORS.disciplines,
}


def _polite_wait() -> None:
    time.sleep(random.uniform(SETTINGS.min_delay_seconds, SETTINGS.max_delay_seconds))


def _with_retries(operation: Callable[[], T], description: str) -> T:
    last_error: Exception | None = None
    for attempt in range(1, SETTINGS.max_retries + 1):
        try:
            return operation()
        except Exception as exc:  # deliberately broad -- any transient failure is worth a retry
            last_error = exc
            wait = SETTINGS.backoff_base_seconds ** attempt
            logger.warning(
                "%s failed (attempt %d/%d): %s -- retrying in %.1fs",
                description, attempt, SETTINGS.max_retries, exc, wait,
            )
            time.sleep(wait)
    raise RuntimeError(f"{description} failed after {SETTINGS.max_retries} attempts") from last_error


def _extract_field(card: Locator, selector: str) -> str:
    try:
        text = card.locator(selector).first.inner_text(timeout=2_000).strip()
        return text if text else "N/A"
    except Exception:
        return "N/A"


def _extract_projects_from_page(page: Page) -> list[dict[str, str]]:
    cards = page.locator(SELECTORS.project_card)
    count = cards.count()
    logger.info("Found %d project cards on current page", count)

    projects = []
    for i in range(count):
        card = cards.nth(i)
        record = {name: _extract_field(card, selector) for name, selector in FIELDS.items()}
        projects.append(record)
    return projects


def _go_to_next_page(page: Page) -> bool:
    """Click the 'next' control if present/enabled. Returns True if it advanced."""
    next_button = page.locator(SELECTORS.next_page_button)
    if next_button.count() == 0 or next_button.first.is_disabled():
        return False

    next_button.first.click()
    _polite_wait()
    page.wait_for_load_state("networkidle", timeout=SETTINGS.page_load_timeout_ms)
    return True


def _scroll_to_load_all(page: Page) -> None:
    """For infinite-scroll listings: scroll until the card count stops growing."""
    previous_count = -1
    while True:
        current_count = page.locator(SELECTORS.project_card).count()
        if current_count == previous_count:
            break
        previous_count = current_count
        page.mouse.wheel(0, 4000)
        _polite_wait()


def scrape_all_projects(context: BrowserContext) -> list[dict[str, str]]:
    """Navigate to the project listing and extract every project record."""
    page = context.new_page()
    _with_retries(
        lambda: page.goto(SELECTORS.projects_url, timeout=SETTINGS.page_load_timeout_ms),
        "Loading project listing page",
    )
    page.wait_for_selector(SELECTORS.project_card, timeout=SETTINGS.page_load_timeout_ms)

    if SELECTORS.uses_infinite_scroll:
        _scroll_to_load_all(page)
        all_projects = _extract_projects_from_page(page)
    else:
        all_projects = []
        page_number = 1
        while True:
            logger.info("Scraping page %d...", page_number)
            all_projects.extend(_extract_projects_from_page(page))
            if not _go_to_next_page(page):
                break
            page_number += 1

    page.close()
    logger.info("Scraped %d projects in total", len(all_projects))
    return _deduplicate(all_projects)


def _deduplicate(projects: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    unique = []
    for project in projects:
        key = (project["Project Title"], project["Host University"], project["Professor Name"])
        if key not in seen:
            seen.add(key)
            unique.append(project)
    return unique
