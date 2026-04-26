# Football Match Stats Scraper

Python script for scraping football match statistics from FlashScore using Selenium.

The script automatically collects:

* Home and away teams
* Final score
* Matchday
* Detailed match statistics (e.g., possession, shots, etc.)

All data is incrementally saved into a CSV file.

---

## Configuration

At the top of the script, you can configure the main parameters:

RESULTS_URL = "https://www.flashscore.com/football/italy/serie-a/results/"
league = "SERIE A"
stats_path = "data/stats_seriea_25_26.csv"

* RESULTS_URL: results page of the league. It can be chosen the running league but also an archived one.
* league: league name (used to extract matchday)
* stats_path: output CSV file path

---

## Main Features

### 1. Match Links Extraction

The function `get_match_links()`:

* Opens the results page
* Extracts all available match links

---

### 2. Single Match Parsing

The function `parse_match(url)`:

* Opens the match page
* Accepts cookies (if required)
* Navigates to the "Stats" tab
* Extracts:

  * Teams
  * Score
  * Matchday
  * Statistics

---

### 3. Statistics Processing

The function `stats_object_from_list(data)`:

* Converts raw scraped data into a structured dictionary:

{
"Possession": {"home": 55, "away": 45},
"Shots on Target": {"home": 6, "away": 3}
}

It also handles special formats (e.g., values inside parentheses).

---

### 4. Data Storage

* Data is saved into a CSV file
* The script:

  * Avoids duplicates (checks existing URLs)
  * Updates the dataset incrementally
  * Sorts data by matchday at the end

---

## Output

The generated CSV file contains columns such as:

url
home_team
away_team
matchday
score
Possession_home
Possession_away
Shots on Target_home
Shots on Target_away
...

---

## Requirements

Install dependencies:

pip install pandas selenium

Make sure you have:

* Google Chrome installed
* A compatible ChromeDriver available in your system

---

## Usage

Run the script with:

python ExtractFootballStats.py

The script will:

1. Collect all match links
2. Extract only new matches (not already in CSV)
3. Save results progressively

---

##  Notes

* The script runs in headless mode (no GUI)
* Uses delays to ensure proper page loading
* Website structure changes may require selector updates

---

## Limitations

* Depends on the HTML structure of the website
* May encounter timeouts or loading issues
* No proxy or IP rotation support

---

## Possible Improvements

* Parallel scraping
* Advanced logging
* Better error handling
* Multi-league support
* Database integration (e.g., SQL)

---
