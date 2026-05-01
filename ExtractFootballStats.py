import time
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# =====================================================================
# CONFIGURATION & PARAMETERS
# =====================================================================
RESULTS_URL = "https://www.flashscore.com/football/italy/serie-a/results/"
LEAGUE = "SERIE A"
STATS_PATH = Path('data/stats_seriea_25_26.csv')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# =====================================================================
# CORE FUNCTIONS
# =====================================================================

def init_driver() -> webdriver.Chrome:
    """Initializes and returns a Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service()
    return webdriver.Chrome(service=service, options=options)


def stats_object_from_list(data: List[str]) -> Dict[str, Dict[str, Any]]:
    """Parses a list of text elements into a structured statistics dictionary."""
    stats = {}
    i = 0
    
    while i < len(data):
        # Scenario 1 — standard format: [home_value, label, away_value]
        if i + 2 < len(data) and not re.match(r"^\(.*\)$", data[i + 1]):
            home_val = data[i].replace("%", "").strip()
            label = data[i + 1].strip()
            away_val = data[i + 2].replace("%", "").strip()
    
            # Convert to numeric types where possible
            try:
                home_val = float(home_val) if "." in home_val else int(home_val)
            except ValueError:
                pass
            try:
                away_val = float(away_val) if "." in away_val else int(away_val)
            except ValueError:
                pass
    
            stats[label] = {"home": home_val, "away": away_val}
            i += 3
    
        # Scenario 2 — format with parentheses (e.g., expected goals)
        elif i + 4 < len(data) and re.match(r"^\(.*\)$", data[i + 1]):
            home_val = data[i + 1].strip("()")     
            label = data[i + 2].strip()            
            away_val = data[i + 4].strip("()")     
            stats[label] = {"home": home_val, "away": away_val}
            i += 5
        else:
            i += 1  # Fallback to avoid infinite loops
    return stats


def get_match_links(driver: webdriver.Chrome, url: str) -> List[str]:
    """Scrapes all match URLs from the results page."""
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # Handle cookie consent banner
    try:
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept_button.click()
    except TimeoutException:
        pass 

    # Expand the list to load more matches
    for _ in range(3):
        try:
            load_more_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Show more matches')]"))
            )
            load_more_button.click()
            time.sleep(1.5) 
        except TimeoutException:
            break 

    time.sleep(3) 
    matches = driver.find_elements(By.CSS_SELECTOR, 'a.eventRowLink')
    links = [m.get_attribute('href') for m in matches if m.get_attribute('href')]
    
    logging.info(f"Found {len(links)} match links.")
    return links


def click_stats_tab(wait: WebDriverWait, retries: int = 3) -> bool:
    """Attempts to click the 'Stats' tab on a match detail page."""
    for attempt in range(retries):
        try:
            button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='wcl-tab' and text()='Stats']"))
            )
            button.click()
            return True
        except TimeoutException:
            logging.debug(f"Attempt {attempt+1} failed to find 'Stats' tab.")
    return False


def parse_match(driver: webdriver.Chrome, url: str) -> Optional[Dict[str, Any]]:
    """Extracts team info, score, and stats from a specific match page."""
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    
    try:
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept_button.click()
    except TimeoutException:
        pass

    if not click_stats_tab(wait):
        logging.warning(f"Could not find 'Stats' tab for {url}")
        return None
    
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.duelParticipant__startTime')))
        team_home = driver.find_element(By.CSS_SELECTOR, '.duelParticipant__home .participant__participantName').text
        team_away = driver.find_element(By.CSS_SELECTOR, '.duelParticipant__away .participant__participantName').text
        score = driver.find_element(By.CSS_SELECTOR, '.detailScore__wrapper').text.replace('\n', ' ')
    except (TimeoutException, NoSuchElementException):
        logging.warning(f"Header data missing or timeout for {url}")
        return None
    
    try:
        elements = wait.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="wcl-scores-simple-text-01"]'))
        )
    except TimeoutException:
        logging.warning(f"Stat elements not visible for {url}")
        return None

    # Determine the Matchday (Round)
    matchday_items = driver.find_elements(By.CSS_SELECTOR, "span[data-testid='wcl-scores-overline-03']")
    pattern = re.compile(rf"{LEAGUE}\s*-\s*ROUND\s*(\d+)", re.IGNORECASE)
    
    matchday = None
    for el in matchday_items:
        match = pattern.search(el.text.strip())
        if match:
            matchday = match.group(1)
            break
            
    if not matchday:
        logging.error(f"Could not identify the Matchday for {url}.")
        return None

    raw_data = [el.text for el in elements]
    stats = stats_object_from_list(raw_data)

    return {
        'url': url,
        'home_team': team_home,
        'away_team': team_away,
        'matchday': matchday,
        'score': score,
        'stats': stats
    }


def convert_to_row(match: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens the match dictionary into a single-level row for CSV export."""
    row = {
        'url': match['url'],
        'home_team': match['home_team'],
        'away_team': match['away_team'],
        'matchday': int(match['matchday']),
        'score': match['score']
    }
    for stat_name, stat_values in match['stats'].items():
        row[f"{stat_name}_home"] = stat_values['home']
        row[f"{stat_name}_away"] = stat_values['away']
    return row

# =====================================================================
# MAIN EXECUTION
# =====================================================================

def main():
    # Ensure data directory exists
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data to avoid duplicates and ensure column alignment
    if STATS_PATH.exists():
        try:
            df_main = pd.read_csv(STATS_PATH)
            processed_urls = set(df_main['url'].dropna())
        except pd.errors.EmptyDataError:
            df_main = pd.DataFrame(columns=["url"])
            processed_urls = set()
    else:
        df_main = pd.DataFrame(columns=["url"])
        processed_urls = set()

    driver = init_driver()
    
    try:
        logging.info("Fetching match links from results page...")
        links = get_match_links(driver, RESULTS_URL)

        for i, link in enumerate(links, start=1):
            if link in processed_urls:
                logging.info(f"[{i}/{len(links)}] Skipped (already exists): {link}")
                continue

            logging.info(f"[{i}/{len(links)}] Processing: {link}")
            match_data = parse_match(driver, link)
            
            if match_data:
                new_row_df = pd.DataFrame([convert_to_row(match_data)])
                
                # Using concat ensures column alignment via header names (prevents shifting)
                df_main = pd.concat([df_main, new_row_df], ignore_index=True)
                
                # Save after every successful scrape to prevent data loss
                df_main.to_csv(STATS_PATH, index=False)
                
            time.sleep(2) # Politeness delay
            
    finally:
        logging.info("Closing WebDriver.")
        driver.quit()

    # Final sort by matchday
    if STATS_PATH.exists():
        try:
            logging.info("Sorting final CSV by matchday...")
            df_final = pd.read_csv(STATS_PATH)
            df_final = df_final.sort_values(by="matchday")
            df_final.to_csv(STATS_PATH, index=False)
            logging.info("Process finished successfully.")
        except Exception as e:
            logging.error(f"Error during final CSV sorting: {e}")

if __name__ == "__main__":
    main()
