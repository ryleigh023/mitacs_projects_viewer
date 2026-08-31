mitacs projects viewer

a python tool that pulls every public project on the mitacs globalink research internship (gri) listing straight from the portal's own json api and exports them into a clean, filterable excel spreadsheet. no login, no browser — just one http request, done in a few seconds.

what it does

- calls the same public api the mitacs website itself uses (`/api/sasprojectlistpaging`) to fetch every project in one request — confirmed live: no login needed, no page-size cap
- decodes the numeric "preferred academic background" codes into readable discipline names using a lookup table pulled from the portal's own frontend code
- retries failed requests with backoff
- adds a "competition tier" column: flags tier-1 schools (university of toronto, ubc, mcgill, waterloo, university of alberta) as "high competition" and everything else as "strategic / less competitive"
- writes everything to mitacs_listings.xlsx with a styled header row, frozen header, auto-fit column widths, and native excel autofilter dropdowns on every column

files

- config.py — the api endpoint, request payload, and the discipline-code lookup table
- api_client.py — fetches and decodes the project data
- excel_writer.py — builds the formatted .xlsx output
- main.py — runs the whole pipeline

setup

1. install dependencies

   pip install -r requirements.txt

2. run it

   python main.py

   this fetches all ~3,359 projects (as of writing) and saves mitacs_listings.xlsx in the project folder — typically done in under 10 seconds.

notes

- no credentials, no .env file, no headless browser — the listing api is fully public
- "department" isn't part of mitacs's data for this listing (confirmed against the live api), so that column will always read "n/a"
- the generated mitacs_listings.xlsx is gitignored since it's local output data, not code
- this hits mitacs's api directly rather than the rendered page — be a good citizen and don't hammer it with repeated automated runs
