import time
import json
import cloudscraper
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BASE_URL = "https://gtd.fandom.com"
TOWERS_URL = f"{BASE_URL}/wiki/Towers"
OUTPUT_FILE = "database.json"
DEBUG_FILE = "debug_infobox.html"

def get_scraper():
    """Initializes Cloudscraper with a forced Desktop User-Agent."""
    print("Initializing Cloudscraper...")
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True 
        }
    )

def get_tower_links(scraper):
    """Fetches and parses the main Towers page for links."""
    print("Fetching main towers list...")
    response = scraper.get(TOWERS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = []
    # Locate the main body of the wiki page
    content = soup.find(id="mw-content-text")
    if not content:
        print("Could not find main content on Towers page.")
        return []

    # Extract all links that point to specific wiki pages
    for a in content.find_all('a', href=True):
        href = a['href']
        # Filter: Must be a wiki link, exclude special pages, exclude the Towers page itself
        if href.startswith('/wiki/') and ':' not in href and href != '/wiki/Towers':
            full_url = BASE_URL + href
            # Grab the title attribute, or fall back to formatting the URL string
            name = a.get('title', href.split('/')[-1].replace('_', ' '))
            
            # Prevent duplicate links
            if full_url not in [link['url'] for link in links]:
                links.append({'name': name, 'url': full_url})
                
    print(f"Found {len(links)} potential links! Starting extraction...")
    return links

def parse_tower(scraper, tower):
    """Navigates to a specific tower's URL and extracts its infobox stats."""
    print(f"Checking: {tower['name']}...")
    try:
        response = scraper.get(tower['url'])
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Target the Fandom Infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if not infobox:
            print(" ---> SKIPPED: Page loaded, but no 'portable-infobox' was found.")
            return None
            
        # 2. Target the Stat Rows
        stat_rows = infobox.find_all(class_='pi-data')
        
        if not stat_rows:
            print(f" ---> SKIPPED: Infobox found, but it has no stat rows. (Saving raw HTML to {DEBUG_FILE})")
            # DUMP THE HTML FOR DEBUGGING
            with open(DEBUG_FILE, 'w', encoding='utf-8') as f:
                f.write(infobox.prettify())
            return None
            
        tower_data = {
            "name": tower['name'],
            "url": tower['url'],
            "stats": {}
        }
        
        # 3. Extract Labels and Values
        for row in stat_rows:
            label_element = row.find(class_='pi-data-label')
            value_element = row.find(class_='pi-data-value')
            
            if label_element and value_element:
                label = label_element.get_text(strip=True)
                
                # --- ICON DETECTION LOGIC ---
                # Look for images inside the value element to modify the label appropriately
                images = value_element.find_all('img')
                for img in images:
                    # Fandom uses 'alt' or 'data-image-name' for the filename
                    img_identifier = img.get('data-image-name', '') + img.get('alt', '')
                    
                    if 'RangeIcon' in img_identifier:
                        label = "Range (Single Target)"
                    elif 'RadiusIcon' in img_identifier:
                        label = "Range (AOE Size)"
                # ----------------------------

                value = value_element.get_text(separator=' ', strip=True)
                tower_data["stats"][label] = value
                
        if not tower_data["stats"]:
             print(" ---> SKIPPED: Rows found, but label/value extraction failed.")
             return None
             
        print(f" ---> SUCCESS: Extracted {len(tower_data['stats'])} stats.")
        return tower_data
        
    except Exception as e:
        print(f" ---> ERROR processing {tower['name']}: {e}")
        return None

def main():
    scraper = get_scraper()
    tower_links = get_tower_links(scraper)
    
    database = []
    
    try:
        for tower in tower_links:
            data = parse_tower(scraper, tower)
            if data:
                database.append(data)
                
            # 1.5 second delay to avoid getting rate-limited or IP-banned by Cloudflare
            time.sleep(1.5) 
            
    except KeyboardInterrupt:
        # This catches your Ctrl+C and allows the script to finish gracefully
        print("\n\nScraping interrupted by user. Initiating safe shutdown...")
    
    finally:
        # This block ALWAYS runs, saving whatever data you managed to grab.
        if database:
            print("Saving data...")
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=4, ensure_ascii=False)
            print(f"Saved {len(database)} towers to {OUTPUT_FILE}.")
        else:
            print("No data extracted. Nothing to save.")

if __name__ == "__main__":
    main()