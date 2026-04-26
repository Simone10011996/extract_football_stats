######################################################################
########################### SET PARAMETERS ###########################
######################################################################

RESULTS_URL = "https://www.flashscore.com/football/italy/serie-a/results/"
league = "SERIE A"
stats_path = 'data/stats_seriea_25_26.csv'

######################################################################


import time
import pandas as pd
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")

service = Service()
driver = webdriver.Chrome(service=service, options=options)


def stats_object_from_list(data):
    stats = {}
    i = 0
    
    while i < len(data):
        # Scenario 1 — normal format: [home, label, away]
        if (
            i + 2 < len(data)
            and not re.match(r"^\(.*\)$", data[i + 1])  
        ):
            home_val = data[i].replace("%", "").strip()
            label = data[i + 1].strip()
            away_val = data[i + 2].replace("%", "").strip()
    
            # Converts in int or float if numeric
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
    
        # Scenario 2 — format with parenthesis 
        elif (
            i + 4 < len(data)
            and re.match(r"^\(.*\)$", data[i + 1])  
        ):
            home_val = data[i + 1].strip("()")     
            label = data[i + 2].strip()            
            away_val = data[i + 4].strip("()")     
            stats[label] = {"home": home_val, "away": away_val}
            i += 5
        else:
            i += 1  # fallback
    return stats


# Function to obtain links of all matches
def get_match_links():
    driver.get(RESULTS_URL)
    time.sleep(5)

    # Wait loading of matches
    matches = driver.find_elements(By.CSS_SELECTOR, 'a.eventRowLink')
    links = [m.get_attribute('href') for m in matches if m.get_attribute('href')]
    print(f"Found {len(links)} matches.")
    return links

def click_stats_tab(wait, retries=3):
    for attempt in range(retries):
        try:
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@data-testid='wcl-tab' and text()='Stats']")
                )
            )
            button.click()
            return True
        except TimeoutException:
            print(f"Attempt {attempt+1} failed for tab Stats")
    
    return False

# Function to obtain statistics from a single match
def parse_match(url):
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    
    try:
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept_button.click()
    except:
        pass

    if not click_stats_tab(wait):
        print(f"Tab Stats not found for {url}")
        return None
    
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.duelParticipant__startTime')))
    except:
        print(f"Timeout for {url}")
        return None

    try:
        team_home = driver.find_element(By.CSS_SELECTOR, '.duelParticipant__home .participant__participantName').text
        team_away = driver.find_element(By.CSS_SELECTOR, '.duelParticipant__away .participant__participantName').text
        score = driver.find_element(By.CSS_SELECTOR, '.detailScore__wrapper').text.replace('\n', ' ')
    except:
        team_home = team_away = score = None
    
    elements = wait.until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="wcl-scores-simple-text-01"]'))
    )
    
    matchday_items = driver.find_elements(By.CSS_SELECTOR, "span[data-testid='wcl-scores-overline-03']")
    
    # Regex for finding "<LEAGUE> - ROUND #"
    pattern = re.compile(rf"{league}\s*-\s*ROUND\s*(\d+)", re.IGNORECASE)
    
    for el in matchday_items:
        text = el.text.strip()
        match = pattern.search(text)
        if match:
            matchday = match.group(1)
            break
    else:
        raise Exception("No matches found.")

        
    data = []
    for i in elements:
        data.append(i.text)
    
    stats = stats_object_from_list(data)

    return {
        'url': url,
        'home_team': team_home,
        'away_team': team_away,
        'matchday': matchday,
        'score': score,
        'stats': stats
    }

def convert_row(match):
    row = {
        'url': match['url'],
        'home_team': match['home_team'],
        'away_team': match['away_team'],
        'matchday': match['matchday'],
        'score': match['score']
    }
    for stat_name, stat_values in match['stats'].items():
        row[f"{stat_name}_home"] = stat_values['home']
        row[f"{stat_name}_away"] = stat_values['away']
    return row

links = get_match_links()


# If file does not exists, create it empty
if not os.path.exists(stats_path):
    with open(stats_path, "w") as f:
        pass

# Try to read csv, but handle empty case
try:
    existing_data = pd.read_csv(stats_path)
except pd.errors.EmptyDataError:
    existing_data = pd.DataFrame(columns=["url"])

# For on links
for i, link in enumerate(links):
    if link not in existing_data["url"].values:  
        print(f"[{i+1}/{len(links)}] Extracting: {link}")
        
        match = parse_match(link)
        if match:
            data = convert_row(match)  
            data = pd.DataFrame([data])
            # Add and save
            existing_data = pd.concat([existing_data, data], ignore_index=True)
            existing_data.to_csv(stats_path, index=False)
            
        time.sleep(2)
    else:
        print(f"[{i+1}/{len(links)}] Skipped (already present): {link}")


# Order by matchday ascending
df = pd.read_csv(stats_path)
df = df.sort_values(by="matchday")
df.to_csv(stats_path)