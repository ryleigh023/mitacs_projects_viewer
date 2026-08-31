mitacs projects viewer

a python tool that scrapes every public project on the mitacs globalink research internship (gri) project listing and exports them into a clean, filterable excel spreadsheet. no login required — browsing the project list is public, only applying to a project needs an account.

what it does

- opens the public gri project listing with playwright (headless chromium) — confirmed live: no login needed to browse
- scrapes every open project: title, host university, host province, professor name, department, description, required skills, and preferred disciplines
  - "department" isn't part of mitacs's data model for this listing (confirmed by inspecting the live site), so it will always show "n/a"
- retries flaky page loads with backoff and waits politely between requests so it doesn't hammer the portal
- adds a "competition tier" column: flags tier-1 schools (university of toronto, ubc, mcgill, waterloo, university of alberta) as "high competition" and everything else as "strategic / less competitive"
- writes everything to mitacs_listings.xlsx with a styled header row, frozen header, auto-fit column widths, and native excel autofilter dropdowns on every column

files

- config.py — urls, css selectors, and timing/retry settings (the only file you'll likely need to edit if mitacs changes their site)
- scraper.py — pagination, per-project extraction, retries, throttling
- excel_writer.py — builds the formatted .xlsx output
- main.py — runs the whole pipeline

setup

1. install dependencies

   pip install -r requirements.txt
   playwright install chromium

2. run it

   python main.py

   this opens a browser, scrapes every project (there are roughly 3,359 projects across ~336 pages as of writing), and saves mitacs_listings.xlsx in the project folder.

testing a small batch first

the full run covers ~336 pages, which takes a while given the polite delays between requests. to try it on just the first couple of pages, temporarily set `max_pages` in config.py's `ScraperSettings` to a small number (e.g. 2) before running, then set it back to `None` for a full run.

notes

- no credentials or .env file needed — the listing is fully public
- the generated mitacs_listings.xlsx is gitignored since it's local output data, not code
- check mitacs's terms of use before running a full scrape — this is meant for personal research/filtering at a slow, human-like pace, not bulk or commercial use
