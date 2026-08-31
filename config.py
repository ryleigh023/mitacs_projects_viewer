"""
Central configuration for the Mitacs GRI extractor.

IMPORTANT: The Globalink Research Internship project list lives behind a
student login (the Globalink Student Portal) and is rendered by a
JavaScript single-page app. That means nobody outside your logged-in
session can see its real HTML from the outside -- the selectors below
are PLACEHOLDERS. You must confirm/replace them before the scraper will
find anything.

How to fill these in (~5 minutes):
  1. Log into the portal in a normal browser (Chrome/Firefox/Edge).
  2. Open DevTools (F12) -> "Elements" tab.
  3. Right-click a project title on the listing page -> "Inspect".
  4. Note the tag/class (e.g. <h3 class="project-title">) and put a CSS
     selector for it below (e.g. ".project-title" or "h3.project-title").
  5. Repeat for host university, province, professor, department,
     description, skills, disciplines, and the "next page" control.

Tip: also check DevTools -> "Network" -> filter "Fetch/XHR" while the
project list loads. Many modern portals fetch the list as JSON from an
internal API. If you spot one, hitting that endpoint directly with
`requests` (reusing your session cookie) is far more robust than scraping
rendered HTML -- worth 10 minutes of looking before you rely on selectors.

Respect the Mitacs Terms of Use while running this. It's built to be slow
and polite (see ScraperSettings below) for reviewing your own accessible
project list -- not for high-volume or commercial use.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Selectors:
    # --- Login page ---
    login_url: str = "https://gri.mitacs.ca/login"           # PLACEHOLDER -- confirm real URL
    username_input: str = "input#username"                   # PLACEHOLDER
    password_input: str = "input#password"                   # PLACEHOLDER
    login_button: str = "button[type='submit']"               # PLACEHOLDER
    post_login_marker: str = "text=Dashboard"                  # element that only exists once logged in

    # --- Project listing page ---
    projects_url: str = "https://gri.mitacs.ca/projects"      # PLACEHOLDER -- confirm real URL
    project_card: str = "div.project-card"                    # PLACEHOLDER -- one match per project
    title: str = ".project-title"
    university: str = ".host-university"
    province: str = ".host-province"
    professor: str = ".professor-name"
    department: str = ".department"
    description: str = ".project-description"
    skills: str = ".required-skills"
    disciplines: str = ".preferred-disciplines"

    # --- Pagination ---
    next_page_button: str = "button.pagination-next"          # PLACEHOLDER
    uses_infinite_scroll: bool = False                         # set True if there's no "next" button


@dataclass(frozen=True)
class ScraperSettings:
    min_delay_seconds: float = 1.5
    max_delay_seconds: float = 3.5
    max_retries: int = 3
    backoff_base_seconds: float = 2.0
    page_load_timeout_ms: int = 30_000
    headless: bool = True
    storage_state_path: str = "mitacs_session.json"
    user_agents: tuple = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36",
    )


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
