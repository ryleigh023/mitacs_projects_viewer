"""
Central configuration for the Mitacs GRI extractor.

CONFIRMED 2026-08-31 by inspecting the live portal's network traffic: the
Globalink project list is served by a single public JSON API endpoint --
no login and no browser rendering needed. The Angular frontend at
globalink.mitacs.ca calls this same endpoint to render the page; we call
it directly instead, which turns a multi-hour browser-automation job into
one HTTP request that returns in under a second.

Endpoint: POST https://globalink.mitacs.ca/api/sasprojectlistpaging
  body: {..filters (all null = unfiltered).., "offset": int, "limit": int}
  response: {"rows": [...], "count": <total project count>}
The endpoint has no observed page-size cap -- requesting limit=<total
count> returns every project in one call.

The discipline codes in each project's "PreferredBackgroundCollection"
field (e.g. "[88,73,68]") are internal numeric IDs. DISCIPLINE_LOOKUP below
maps them to human-readable names -- extracted directly from the portal's
own bundled frontend JS (it ships this lookup table client-side, in the
clear, unobfuscated).

One data-model note: there is no "Department" field anywhere in the API
response. "Department" will always show as "N/A" in the output.
"""

from __future__ import annotations

API_URL = "https://globalink.mitacs.ca/api/sasprojectlistpaging"

# All-null filter payload -- returns every project, unfiltered.
BASE_PAYLOAD = {
    "HostProvinceName": None,
    "HostUniversityID": None,
    "HostCampusID": None,
    "LanguageUsed": None,
    "keyword": None,
    "FirstName": None,
    "LastName": None,
    "AcademicDiscipline": None,
    "PreferredBackgroundCollection": None,
}

REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2.0

TIER1_UNIVERSITIES = {
    "university of toronto",
    "university of british columbia",
    "mcgill university",
    "university of waterloo",
    "university of alberta",
}

OUTPUT_FILENAME = "mitacs_listings.xlsx"

# id -> human-readable discipline name, extracted from the portal's own
# frontend bundle (main.*.js) on 2026-08-31.
DISCIPLINE_LOOKUP: dict[str, str] = {
    "0": "Accounting", "1": "Actuarial Science", "2": "Agriculture", "3": "American Studies",
    "4": "Anatomy", "5": "Anthropology", "6": "Arabic Language", "7": "Archaeology",
    "8": "Architecture", "9": "Art", "10": "Art History", "11": "Asian Studies",
    "12": "Astronomy", "13": "Astrophysics", "14": "Atmospheric Science", "15": "Australian Studies",
    "16": "Aviation", "17": "Banking", "18": "Biochemistry", "19": "Biological Sceinces",
    "20": "Biological Sciences", "21": "Biologie", "22": "Biology", "23": "Botany",
    "24": "Business", "25": "Canadian Studies", "26": "Ceramics", "27": "Chemistry",
    "28": "Chimie", "29": "Chinese Language", "30": "Chiropractic", "31": "City/Regional Planning",
    "32": "Classics", "33": "Communication", "34": "Comparative Development",
    "35": "Comparative Literature", "37": "Cultural Studies", "38": "Dentistry", "39": "Design",
    "40": "Development Studies", "41": "Drama", "42": "Earth Science", "43": "East Asian Studies",
    "44": "Ecology", "45": "Econometrics", "46": "Economics", "47": "Educ-Admin",
    "48": "Educ-Art", "49": "Educ-Curriculum Studies", "50": "Educ-Elementary",
    "51": "Educ-Foundations", "52": "Educ-Languages", "53": "Educ-Music", "54": "Educ-Phys Ed",
    "55": "Educ-Psychology", "56": "Educ-Religion", "57": "Educ-Science", "58": "Educ-Secondary",
    "59": "Educ-Social Studies", "60": "Educ-Special Ed", "61": "Educ-Vocational",
    "62": "Education", "63": "Electronic Systems", "64": "Engg-Aeronautical",
    "65": "Engg-Biological", "66": "Engg-Biomedical", "67": "Engg-Ceramic", "68": "Engg-Chemical",
    "69": "Engg-Civil", "70": "Engg-Computer", "71": "Engg-Electrical", "73": "Engg-Enviromental",
    "75": "Engg-Fuel", "76": "Engg-Geological", "77": "Engg-Industrial",
    "78": "Engg-Manufacturing", "80": "Engg-Materials", "81": "Engg-Mechanical",
    "82": "Engg-Metallurgical", "83": "Engg-Mineral", "84": "Engg-Mining", "85": "Engg-Petroleum",
    "86": "Engg-Software", "87": "Engg-Systems and Technology", "88": "Engineering",
    "89": "English Literature", "90": "Secondary Education", "91": "Primary Education",
    "92": "Entomology", "93": "Environmental Studies", "94": "Ergonomics",
    "95": "European Studies", "96": "Film Studies", "97": "Finance", "98": "Fine Arts",
    "99": "Food Science", "100": "Forestry", "101": "French Language", "102": "French Studies",
    "103": "Genetics", "104": "Geography", "105": "Geology", "106": "Geomatics",
    "107": "German Language", "108": "German Studies", "109": "Greek Language",
    "110": "Health Studies", "111": "Hebrew Language", "112": "Hindi Language",
    "113": "Hispanic Studies", "114": "Histoire", "115": "History", "116": "History-Ancient",
    "117": "Hospitality", "118": "Human Ecology", "119": "Humanities", "120": "Immunology",
    "121": "Indonesian Language", "122": "Indonesian Studies",
    "123": "Industrial Design and Technology", "124": "Industrial Relations",
    "125": "Information Studies", "128": "Interior Design", "129": "International Business",
    "130": "International Business and Trade", "131": "International Studies",
    "132": "Islamic Studies", "133": "Italian Language", "134": "Italian Studies",
    "135": "Japanese Language", "136": "Japanese Studies", "137": "Jewish Studies",
    "138": "Journalism", "139": "Korean Language", "140": "Korean Studies",
    "141": "Land Information", "142": "Landscaping", "143": "Language Studies",
    "144": "Langues Modernes", "145": "Latin American Studies", "146": "Latin Language",
    "147": "Law", "148": "Law-Business", "149": "Law-International", "150": "Library Studies",
    "151": "Linguistics", "153": "Management", "154": "Management Information Systems",
    "155": "Manufacturing", "156": "Maritime Studies", "157": "Marketing", "158": "Mathematics",
    "159": "Media Studies", "160": "Medical Sciences", "161": "Medicine", "162": "Meterology",
    "163": "Microbiology", "164": "Modern Languages", "165": "Molecular Biology", "166": "Music",
    "167": "Musique", "168": "Native Studies", "169": "Neuroscience", "170": "Nursing",
    "171": "Nutrition", "172": "Occupational Health", "173": "Optometry", "174": "Parasitology",
    "175": "Pathology", "176": "Pharmacology", "177": "Pharmacy", "178": "Philosophy",
    "180": "Photomedia", "181": "Physics", "182": "Physiology", "184": "Planning",
    "185": "Political Science", "186": "Psychologie", "187": "Psychology",
    "188": "Public Health", "189": "Public Policy and Administration", "190": "Public Relations",
    "191": "Quantitative Surveying", "193": "Radiation Science", "194": "Recreation",
    "195": "Rehabilitation Medicine", "196": "Religious Studies", "197": "Russian Language",
    "198": "Russian Studies", "199": "Scandinavian Languages", "200": "Science Politique",
    "201": "Science and Technology", "202": "Science des Ordinateurs",
    "203": "Sciences Politiques", "204": "Sciences de la Terre", "205": "Social Work",
    "206": "Sociologie", "207": "Sociology", "208": "Soil Science", "209": "Spanish Language",
    "210": "Sports Science", "211": "Statistics", "212": "Studies Science and Technology",
    "213": "Surveying", "214": "Tourism", "215": "Tourism", "216": "Translation",
    "217": "Urdu Language", "218": "Veterinary Science and Medicine", "219": "Womens Studies",
    "221": "Zoology", "222": "Sanskrit Language", "223": "Scandinavian Studies",
}
