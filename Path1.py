import pandas as pd
from bs4 import BeautifulSoup
import concurrent.futures
import time
import json
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# URLs and configuration
URLS = {
    'stats_standard': 'https://fbref.com/en/comps/9/stats/Premier-League-Stats',
    'stats_keeper': 'https://fbref.com/en/comps/9/keepers/Premier-League-Stats',
    'stats_keeper_adv': 'https://fbref.com/en/comps/9/keepersadv/Premier-League-Stats',
    'stats_shooting': 'https://fbref.com/en/comps/9/shooting/Premier-League-Stats',
    'stats_passing': 'https://fbref.com/en/comps/9/passing/Premier-League-Stats',
    'stats_passing_types': 'https://fbref.com/en/comps/9/passing_types/Premier-League-Stats',  # Fixed URL
    'stats_gca': 'https://fbref.com/en/comps/9/gca/Premier-League-Stats',
    'stats_defense': 'https://fbref.com/en/comps/9/defense/Premier-League-Stats',
    'stats_possession': 'https://fbref.com/en/comps/9/possession/Premier-League-Stats',
    'stats_misc': 'https://fbref.com/en/comps/9/misc/Premier-League-Stats'
}

COLUMNS_ORDER = [
    'player', 'nationality', 'team', 'position', 'age', 'games', 'games_starts', 'minutes', 'goals',
    'assists', 'cards_yellow', 'cards_red', 'xg', 'xg_assist', 'progressive_carries', 'progressive_passes',
    'progressive_passes_received', 'goals_per90', 'assists_per90', 'xg_per90', 'xg_assist_per90',
    'gk_goals_against_per90', 'gk_save_pct', 'gk_clean_sheets_pct', 'gk_pens_save_pct',
    'shots_on_target_pct', 'shots_on_target_per90', 'goals_per_shot', 'average_shot_distance',
    'passes_completed', 'passes_pct', 'passes_total_distance', 'passes_pct_short', 'passes_pct_medium',
    'passes_pct_long', 'assisted_shots', 'passes_into_final_third', 'passes_into_penalty_area',
    'crosses_into_penalty_area', 'progressive_passes', 'sca', 'sca_per90', 'gca', 'gca_per90',
    'tackles', 'tackles_won', 'tackles_def_3rd', 'tackles_lost', 'blocks', 'blocked_shots',
    'blocked_passes', 'interceptions',
    'touches', 'touches_def_pen_area', 'touches_def_3rd', 'touches_mid_3rd', 'touches_att_3rd', 'touches_att_pen_area',
    'take_ons', 'take_ons_won_pct', 'take_ons_tackled_pct',
    'carries', 'carry_progressive_distance', 'progressive_carries', 'carries_into_final_third', 'carries_into_penalty_area', 'miscontrols', 'dispossessed',
    'passes_received', 'progressive_passes_received',
    'fouls', 'fouled', 'offsides', 'crosses', 'ball_recoveries', 'aerials_won', 'aerials_lost',
    'aerials_won_pct'
]

COLUMNS_NAME = [
    'Player', 'Nation', 'Team', 'Position', 'Age', 'Match played', 'Starts', 'Minutes',
    'Goals', 'Assists', 'Yellow cards', 'Red cards', 'xG', 'xAG', 'PrgC', 'PrgP',
    'PrgR', 'Goals per 90', 'Assists per 90', 'xG per 90', 'xAG per 90',
    'GA90', 'Save%', 'CS%', 'Pen Save%',
    'SoT%', 'SoT/90', 'G/Sh', 'Average dist',
    'Cmp', 'Cmp%', 'TotDist', 'Cmp%_S', 'Cmp%_M', 'Cmp%_L', 'KP', '1/3', 'PPA', 'CrsPA', 'PrgPasses',
    'SCA', 'SCA90', 'GCA', 'GCA90',
    'Tkl', 'TklW', 'Att', 'Lost', 'Blocks', 'Block shot', 'Pass', 'Int',
    'Touches', 'Def Pen', 'Def 3rd', 'Mid 3rd', 'Att 3rd', 'Att Pen',
    'Possession_Att', 'Possession_Succ%', 'Possession_Tkld%',
    'Carries', 'Possession_ProDist', 'Possession_ProgC', 'Possession_1/3', 'Possession_CPA', 'Possession_Mis',
    'Possession_Dis', 'Rec', 'PrgR',
    'Fls', 'Fld', 'Off', 'Crs', 'Recov', 'Won', 'Lost', 'Won%'
]

CACHE_FILE = 'fbref_cache.json'

def scrape_table(url, table_id, max_retries=3):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36")
    for attempt in range(max_retries):
        driver = None
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, table_id)))

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table', {'id': table_id})
            
            if not table:
                print(f"Table {table_id} not found on {url}")
                return {}

            # Get all available stats from table headers
            headers = []
            data_list = {}
            
            header_row = table.find('thead').find_all('tr')[-1]
            for th in header_row.find_all(['th', 'td']):
                data_stat = th.get('data-stat')
                if data_stat in COLUMNS_ORDER:
                    headers.append(data_stat)
                    data_list[data_stat] = []


            rows = table.find('tbody').find_all('tr')
            for row in rows:
                # Skip non-player rows
                if 'class' in row.attrs and ('thead' in row['class'] or 'spacer' in row['class']):
                    continue
                
                # Process each cell
                for data_stat in headers:
                    cell = row.find(['th', 'td'], {'data-stat': data_stat})
                    if cell:
                        value = cell.get_text(strip=True)
                        if data_stat == 'minutes':
                            value = value.replace(',', '')
                            data_list[data_stat].append(int(value) if value.isdigit() else 0)
                        else:
                            data_list[data_stat].append(value if value else 'N/a')
                    else:
                        data_list[data_stat].append('N/a')

            return data_list

        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {table_id}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
        finally:
            if driver:
                driver.quit()

    return {}

def load_cached_data():
    """Load cached data from file"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {str(e)}")
    return None

def save_to_cache(data):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving cache: {str(e)}")

def merge_statistics(all_stats):
    merged_data = {}
    

    if 'stats_standard' in all_stats:
        for i, player in enumerate(all_stats['stats_standard']['player']):
            merged_data[player] = {}
            for stat in all_stats['stats_standard']:
                merged_data[player][stat] = all_stats['stats_standard'][stat][i]
    
    
    for stat_type in all_stats:
        if stat_type == 'stats_standard':
            continue
            
        for i, player in enumerate(all_stats[stat_type]['player']):
            if player not in merged_data:
                continue 
                
            for stat in all_stats[stat_type]:
                if stat not in merged_data[player]:  
                    merged_data[player][stat] = all_stats[stat_type][stat][i]
    
    return merged_data

def scrape_all_stats(force_scrape=False):
    """Main function to scrape all statistics"""
    if not force_scrape:
        cached_data = load_cached_data()
        if cached_data:
            print("Using cached data")
            return pd.DataFrame.from_dict(cached_data, orient="index")

    print("Starting data scraping...")
    all_stats = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_table = {
            executor.submit(scrape_table, URLS[table_id], table_id): table_id 
            for table_id in URLS
        }
        
        for future in concurrent.futures.as_completed(future_to_table):
            table_id = future_to_table[future]
            try:
                table_data = future.result()
                if table_data:
                    all_stats[table_id] = table_data
                    print(f"Successfully scraped {table_id}")
                else:
                    print(f"Failed to scrape {table_id}")
            except Exception as e:
                print(f"Error processing {table_id}: {str(e)}")


    merged_data = merge_statistics(all_stats)
    
    if not merged_data:
        print("No data was collected")
        return pd.DataFrame()

    
    df = pd.DataFrame.from_dict(merged_data, orient="index")
    
    if 'minutes' in df.columns:
        df = df[df['minutes'] > 90]
    
    
    available_columns = [col for col in COLUMNS_ORDER if col in df.columns]
    df = df[available_columns]
    

    column_mapping = dict(zip(COLUMNS_ORDER, COLUMNS_NAME))
    df = df.rename(columns=column_mapping)
    
    
    df = df.fillna('N/a')
    
    df = df.sort_values('Player')
    
    save_to_cache(merged_data)
    
    return df

if __name__ == "__main__":
    start_time = time.time()
    print("Starting Premier League data collection...")
    
    try:
        df = scrape_all_stats(force_scrape=True)
        
        if not df.empty:
            df.to_csv("results.csv", index=False)
            print(f"Successfully saved data for {len(df)} players to results.csv")
        else:
            print("No data was collected. Please check the scraping process.")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    print(f"Execution completed in {time.time() - start_time:.2f} seconds")