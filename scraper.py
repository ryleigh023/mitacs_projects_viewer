"""
Core scraping logic for the Mitacs GRI project listing.

No login is required -- the listing is public. For each project card we
grab title/description/professor/university/province directly (fast, no
extra click), then open the "View Detail" modal only for the two fields
that aren't on the card itself: Required Skills and Preferred Disciplines.

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

from playwright.sync_api import Locator, Page

from config import CARD_LABEL_MAP, DETAIL_LABEL_MAP, REQUIRED_SKILLS_TAB_INDEX, SELECTORS, SETTINGS

logger = logging.getLogger(__name__)
T = TypeVar("T")


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


def _extract_title_and_description(card: Locator) -> tuple[str, str]:
    """The card's left column (.col-9) holds a bold title <p>, followed by
    one or more plain <p> tags making up the description."""
    paragraphs = card.locator(".col-9 p")
    count = paragraphs.count()
    if count == 0:
        return "N/A", "N/A"

    title = paragraphs.nth(0).inner_text(timeout=2_000).strip() or "N/A"
    description = "\n\n".join(
        paragraphs.nth(i).inner_text(timeout=2_000).strip() for i in range(1, count)
    ).strip() or "N/A"
    return title, description


def _extract_label_value_pairs(card: Locator) -> dict[str, str]:
    """Each '.projectPageDetailsSnapshot' row is a bold label span followed
    by one or more value spans, e.g. 'Faculty supervisor:' -> 'Bora' 'Ung'.
    Returns {lowercased label (no trailing colon): joined value}."""
    pairs: dict[str, str] = {}
    rows = card.locator(".projectPageDetailsSnapshot")
    for i in range(rows.count()):
        spans = rows.nth(i).locator("span")
        span_count = spans.count()
        if span_count == 0:
            continue
        label = spans.nth(0).inner_text(timeout=2_000).strip().rstrip(":").lower()
        value = " ".join(
            spans.nth(j).inner_text(timeout=2_000).strip() for j in range(1, span_count)
        ).strip()
        pairs[label] = value or "N/A"
    return pairs


def _open_and_read_detail(page: Page, card: Locator) -> dict[str, str]:
    """Click 'View Detail', read Required Skills + Preferred Disciplines
    (and anything else useful) from the modal, then close it again."""
    try:
        card.locator(SELECTORS.view_detail_button).first.click()
        page.wait_for_selector(SELECTORS.detail_dialog, timeout=SETTINGS.page_load_timeout_ms)
        _polite_wait()

        detail_pairs: dict[str, str] = {}
        rows = page.locator(SELECTORS.detail_row)
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td")
            if cells.count() < 2:
                continue
            label = cells.nth(0).inner_text(timeout=2_000).strip().lower()
            value = cells.nth(1).inner_text(timeout=2_000).strip()
            detail_pairs[label] = value or "N/A"

        # Each tab's content only renders after it's been clicked at least
        # once (confirmed live -- panels start empty until activated).
        required_skills = "N/A"
        skills_tab = page.locator(SELECTORS.detail_required_skills_tab).first
        if skills_tab.count() > 0:
            skills_tab.click()
            page.wait_for_timeout(400)
            panels = page.locator(SELECTORS.detail_tab_panels)
            if panels.count() > REQUIRED_SKILLS_TAB_INDEX:
                required_skills = panels.nth(REQUIRED_SKILLS_TAB_INDEX).inner_text(timeout=2_000).strip() or "N/A"

        result = {"Required Skills": required_skills}
        for label, value in detail_pairs.items():
            field_name = DETAIL_LABEL_MAP.get(label)
            if field_name:
                result[field_name] = value

        page.locator(SELECTORS.detail_close_button).first.click()
        page.wait_for_selector(SELECTORS.detail_dialog, state="hidden", timeout=SETTINGS.page_load_timeout_ms)
        return result
    except Exception as exc:
        logger.warning("Could not read detail modal for a project: %s", exc)
        try:
            page.locator(SELECTORS.detail_close_button).first.click(timeout=1_000)
        except Exception:
            pass
        return {}


def _scrape_one_project(page: Page, card: Locator) -> dict[str, str]:
    title, description = _extract_title_and_description(card)
    quick_pairs = _extract_label_value_pairs(card)

    record = {
        "Project Title": title,
        "Project Description": description,
        "Host Province": "N/A",
        "Host University": "N/A",
        "Professor Name": "N/A",
        "Department": "N/A",  # not present anywhere in the portal's data model
        "Required Skills": "N/A",
        "Preferred Disciplines": "N/A",
    }
    for label, value in quick_pairs.items():
        field_name = CARD_LABEL_MAP.get(label)
        if field_name:
            record[field_name] = value

    record.update(_open_and_read_detail(page, card))
    return record


def _go_to_next_page(page: Page) -> bool:
    """Click the paginator's 'next' button if present/enabled."""
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


def scrape_all_projects(page: Page) -> list[dict[str, str]]:
    """Navigate to the public project listing and extract every project."""
    _with_retries(
        lambda: page.goto(SELECTORS.projects_url, timeout=SETTINGS.page_load_timeout_ms),
        "Loading project listing page",
    )
    page.wait_for_selector(SELECTORS.project_card, timeout=SETTINGS.page_load_timeout_ms)

    if SELECTORS.uses_infinite_scroll:
        _scroll_to_load_all(page)
        cards = page.locator(SELECTORS.project_card)
        all_projects = [_scrape_one_project(page, cards.nth(i)) for i in range(cards.count())]
    else:
        all_projects = []
        page_number = 1
        while True:
            logger.info("Scraping page %d...", page_number)
            cards = page.locator(SELECTORS.project_card)
            count = cards.count()
            for i in range(count):
                all_projects.append(_scrape_one_project(page, cards.nth(i)))

            if SETTINGS.max_pages and page_number >= SETTINGS.max_pages:
                logger.info("Reached max_pages=%d test limit -- stopping early", SETTINGS.max_pages)
                break
            if not _go_to_next_page(page):
                break
            page_number += 1

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
