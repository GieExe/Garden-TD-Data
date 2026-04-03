Project: GTD unit scraper + frontend

Files created:
- scraper.py — simple Python scraper for a Fandom unit page
- unit_data.json — sample scraped data for `Stretch Plant`
- index.html — frontend to display the JSON data
- requirements.txt — Python dependencies

Quick start

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Run the scraper (writes `unit_data.json`):

```bash
python scraper.py
```

Or scrape a different page:

```bash
python scraper.py https://gtd.fandom.com/wiki/Another_Unit
```

3. Start a local web server (to allow `fetch()` to load the JSON):

```bash
python -m http.server 8000
```

Open your browser at `http://localhost:8000` and the card will load.

Notes
- If the Fandom theme differs, `scraper.py` may need tweaks for alternate infobox class names.
- For bulk scraping, modify `scraper.py` to loop URLs and produce a master JSON array.
