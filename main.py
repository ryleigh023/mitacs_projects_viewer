"""
Entry point: log into the Mitacs GRI portal, scrape every open project,
and export the results to a formatted .xlsx workbook.

Usage:
    python main.py
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from auth import get_authenticated_context
from config import OUTPUT_FILENAME
from excel_writer import write_projects_to_excel
from scraper import scrape_all_projects

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        with sync_playwright() as playwright:
            context = get_authenticated_context(playwright)
            try:
                projects = scrape_all_projects(context)
            finally:
                context.close()
    except Exception:
        logger.exception(
            "Scraping failed. If this is your first run, the CSS selectors "
            "in config.py are almost certainly still placeholders -- inspect "
            "the portal in DevTools and update them (see comments at the top "
            "of config.py)."
        )
        raise

    write_projects_to_excel(projects, OUTPUT_FILENAME)
    logger.info("Done. Open %s to review your projects.", OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
