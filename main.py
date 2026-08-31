"""
Entry point: fetch every public Mitacs Globalink project via the portal's
own JSON API and export the results to a formatted .xlsx workbook.

No login, no browser -- just one HTTP request.

Usage:
    python main.py
"""

from __future__ import annotations

import logging

from api_client import fetch_all_projects
from config import OUTPUT_FILENAME
from excel_writer import write_projects_to_excel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    projects = fetch_all_projects()
    write_projects_to_excel(projects, OUTPUT_FILENAME)
    logger.info("Done. Open %s to review your projects.", OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
