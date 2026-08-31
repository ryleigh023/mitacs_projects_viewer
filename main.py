"""
Entry point: scrape every public project on the Mitacs Globalink project
listing and export the results to a formatted .xlsx workbook.

No login is required -- browsing the project list is public (only
applying to a project requires an account).

Usage:
    python main.py
"""

from __future__ import annotations

import logging
import random

from playwright.sync_api import sync_playwright

from config import OUTPUT_FILENAME, SETTINGS
from excel_writer import write_projects_to_excel
from scraper import scrape_all_projects

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=SETTINGS.headless)
            context = browser.new_context(user_agent=random.choice(SETTINGS.user_agents))
            page = context.new_page()
            try:
                projects = scrape_all_projects(page)
            finally:
                context.close()
                browser.close()
    except Exception:
        logger.exception(
            "Scraping failed. If the portal's markup changed, the selectors "
            "in config.py will need updating -- see the comments there."
        )
        raise

    write_projects_to_excel(projects, OUTPUT_FILENAME)
    logger.info("Done. Open %s to review your projects.", OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
