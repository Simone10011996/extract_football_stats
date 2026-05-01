# SERIE A MATCH STATS SCRAPER (Flashscore)

## 1. DESCRIPTION
This script is an automated Selenium-based web scraper designed to extract detailed football match statistics (Italian Serie A in the example, but any league can be set) from Flashscore.com.

The system navigates through historical results, accesses each match individually, extracts performance data (shots, possession, xG, etc.), and saves them into a structured CSV file, ready for statistical analysis or machine learning models.

## 2. KEY FEATURES
- Headless Execution: Runs in the background without opening a visible browser window.
- Duplicate Handling: Automatically skips already processed matches by checking the existing CSV file.
- Incremental Saving: Saves data after every single match to prevent data loss in case of interruptions or errors.
- Intelligent Parsing: Handles various statistic formats, including advanced metrics like Expected Goals (xG).
- Auto-Sorting: Once the process is complete, it automatically sorts the final CSV by Matchday.

## 3. TECHNICAL REQUIREMENTS
- Python 3.7 or higher
- Google Chrome installed
- Chrome Driver (handled automatically via Selenium Service)

Required Python Libraries:
- pandas
- selenium

You can install them using:
pip install pandas selenium

## 4. CONFIGURATION
The main parameters are located in the "CONFIGURATION" section:

- RESULTS_URL: The URL of the Flashscore results page.
- STATS_PATH: The output file path (default: data/stats_seriea_25_26.csv).
- LEAGUE: League name used for regex filtering.

## 5. USAGE
1. Ensure all dependencies are installed.
2. Run the script:
   python ExtractFootballStats.py

3. The script will start scanning for match links. If the 'data' directory does not exist, it will be created automatically.

## 6. OUTPUT STRUCTURE (CSV)
The generated file contains one row per match with the following columns:
- url: Unique link to the match page.
- home_team / away_team: Names of the competing teams.
- matchday: The league round number.
- score: Final score.
- [StatName]_home: Value for the home team.
- [StatName]_away: Value for the away team.

## 7. IMPORTANT NOTES
- Politeness: The script includes delays (time.sleep) to respect the website's loading times and avoid being blocked.
- Selectors: CSS selectors (e.g., [data-testid="..."]) are specific to the current Flashscore layout. If the website updates its UI, these selectors might require updates.

---
### Developed for Football Data Analysis.
