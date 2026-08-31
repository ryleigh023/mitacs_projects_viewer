mitacs projects viewer

a python tool that logs into the mitacs globalink research internship (gri) student portal, scrapes the open project listings, and exports them into a clean, filterable excel spreadsheet.

what it does

- logs into the gri student portal with playwright (headless chromium) and reuses the session on later runs
- scrapes every open project: title, host university, host province, professor name, department, description, required skills, and preferred disciplines
- retries flaky page loads with backoff and waits politely between requests so it doesn't hammer the portal
- adds a "competition tier" column: flags tier-1 schools (university of toronto, ubc, mcgill, waterloo, university of alberta) as "high competition" and everything else as "strategic / less competitive"
- writes everything to mitacs_listings.xlsx with a styled header row, frozen header, auto-fit column widths, and native excel autofilter dropdowns on every column

files

- config.py — urls, css selectors, and timing/retry settings (the only file you'll likely need to edit)
- auth.py — login + session persistence
- scraper.py — pagination, extraction, retries, throttling
- excel_writer.py — builds the formatted .xlsx output
- main.py — runs the whole pipeline

setup

1. install dependencies

   pip install -r requirements.txt
   playwright install chromium

2. copy the env template and fill in your mitacs credentials (or leave it blank and you'll be prompted securely at runtime)

   cp .env.example .env

3. confirm the selectors in config.py

   the gri portal only renders project data after you log in, so the selectors in config.py are placeholders. open the portal in your browser, log in, open devtools (f12) on the project listing page, and update the selectors in config.py to match the real page structure. the comments at the top of config.py walk through this step by step.

4. run it

   python main.py

   this opens a browser, logs in, scrapes every project, and saves mitacs_listings.xlsx in the project folder.

notes

- credentials are read from environment variables or prompted for at runtime — never hardcoded, never committed (.env is gitignored)
- the saved session file (mitacs_session.json) and the generated .xlsx output are also gitignored since they're local/personal data
- check mitacs's terms of use before running this at any real volume — it's meant for reviewing your own accessible project list at a slow, human-like pace, not bulk or commercial scraping
