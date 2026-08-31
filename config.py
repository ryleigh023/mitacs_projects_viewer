"""
Central configuration for the Mitacs GRI extractor.

CONFIRMED 2026-08-31 by directly inspecting the live portal: the Globalink
project list at globalink.mitacs.ca is fully PUBLIC -- no login is required
to browse or scrape it, only to actually apply to a project. It's an
Angular + PrimeNG single-page app. All selectors below were verified
against the real, live DOM (not guessed).

One data-model note: there is no "Department" field anywhere in the
portal's data (checked the full page text for it). The closest available
field is "Preferred student academic background", which is mapped to the
"Preferred Disciplines" output column. "Department" will show as "N/A".
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Selectors:
    # --- Project listing page (public, no auth) ---
    projects_url: str = "https://globalink.mitacs.ca/#/student/application/projects"
    project_card: str = "div.row:has(div.projectPageDetailsSnapshot)"   # 10 cards per page
    view_detail_button: str = "button:has-text('View Detail')"           # one per card

    # --- Project detail modal (opens in-place on "View Detail", no navigation) ---
    detail_dialog: str = ".p-dialog"
    detail_row: str = "table tr.detailRow"          # label/value <td> pairs
    detail_tab_panels: str = "p-tabpanel"            # all 5 tabs pre-rendered, fixed order (see DETAIL_TAB_ORDER)
    detail_close_button: str = ".p-dialog-header-close"

    # --- Pagination ---
    # Standard PrimeNG paginator. ~3359 projects / 10 per page =~ 336 pages.
    next_page_button: str = "button.p-paginator-next"
    uses_infinite_scroll: bool = False


@dataclass(frozen=True)
class ScraperSettings:
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 2.5
    max_retries: int = 3
    backoff_base_seconds: float = 2.0
    page_load_timeout_ms: int = 30_000
    headless: bool = True
    user_agents: tuple = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36",
    )
    # Cap how many listing pages to scrape -- handy for a quick test run.
    # None means scrape everything (~336 pages / ~3359 projects).
    max_pages: int | None = None


# Fixed order of the 5 tabs inside the detail modal -- CONFIRMED all 5 are
# pre-rendered in the DOM at once (no need to click between them).
DETAIL_TAB_ORDER = [
    "Project Description",
    "Student Roles",
    "Required Skills",
    "Project Activities",
    "Additional Information",
]
REQUIRED_SKILLS_TAB_INDEX = DETAIL_TAB_ORDER.index("Required Skills")

# Maps label text from the card's ".projectPageDetailsSnapshot" rows
# (lowercased, trailing colon stripped) to our output field names.
CARD_LABEL_MAP = {
    "faculty supervisor": "Professor Name",
    "faculty province": "Host Province",
    "faculty university": "Host University",
}

# Maps label text from the detail modal's "table tr.detailRow" rows
# (lowercased) to our output field names.
DETAIL_LABEL_MAP = {
    "faculty supervisor": "Professor Name",
    "faculty province": "Host Province",
    "faculty university": "Host University",
    "preferred student academic background": "Preferred Disciplines",
}

TIER1_UNIVERSITIES = {
    "university of toronto",
    "university of british columbia",
    "mcgill university",
    "university of waterloo",
    "university of alberta",
}

OUTPUT_FILENAME = "mitacs_listings.xlsx"

SELECTORS = Selectors()
SETTINGS = ScraperSettings()
