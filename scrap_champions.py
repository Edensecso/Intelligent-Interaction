import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def create_driver():
    """Configures and returns a Selenium WebDriver instance with anti-detection options."""
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    return driver

def scrape_players():
    driver = create_driver()
    all_players = []
    
    try:
        url = "https://gaming.uefa.com/es/uclfantasy/create-team"
        print(f"Navigating to {url}...")
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)

        # 1. Handle Cookie Consent
        try:
            print("Checking for cookie consent...")
            cookie_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#cmpwelcomebtnaccept")))
            cookie_btn.click()
            print("Cookie consent accepted.")
            time.sleep(2)
        except Exception as e:
            print(f"Cookie handling skipped: {e}")

        # 2. Handle 'Guest' Modals
        try:
            wait_short = WebDriverWait(driver, 5)
            print("Looking for first guest button...")
            guest_btn1 = wait_short.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".si-btn.si-btn--outline")))
            print(f"Clicking guest button 1: {guest_btn1.text}")
            guest_btn1.click()
            time.sleep(2)
            
            print("Looking for second guest button...")
            guest_btn2 = wait_short.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".si-btn.si-btn--outline")))
            print(f"Clicking guest button 2: {guest_btn2.text}")
            guest_btn2.click()
            time.sleep(3)
        except Exception as e:
            print(f"Guest modal handling finished (or skipped): {e}")

        # 3. Wait for Player List
        print("Waiting for player list...")
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".si-plist__row")))
            print("Player list loaded.")
        except Exception as e:
            print(f"Timeout waiting for player list: {e}")
            raise

        # 4. Scroll to load all players
        print("Scrolling to load all players...")
        last_count = 0
        scroll_attempts = 0
        max_attempts = 200 
        
        while scroll_attempts < max_attempts:
            # Scroll the specific container
            try:
                # Script to scroll the .si-plist element
                scroll_script = """
                    var plist = document.querySelector('.si-plist');
                    plist.scrollTop = plist.scrollHeight;
                """
                driver.execute_script(scroll_script)
            except Exception as e:
                print(f"Error scrolling container: {e}")
                # Fallback to window scroll just in case
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(1.5) 
            
            items = driver.find_elements(By.CSS_SELECTOR, ".si-plist__row")
            current_count = len(items)
            print(f"Found {current_count} rows...", end='\r')
            
            if current_count == last_count and current_count > 0:
                time.sleep(3)
                items_check = driver.find_elements(By.CSS_SELECTOR, ".si-plist__row")
                if len(items_check) == last_count:
                    print(f"\nNo new rows loaded. Stopping scroll at {last_count}.")
                    break
            
            last_count = current_count
            scroll_attempts += 1

        # 5. Extract Data
        print(f"\nExtracting details for {last_count} rows...")
        player_elements = driver.find_elements(By.CSS_SELECTOR, ".si-plist__row")
        
        for el in player_elements:
            try:
                # Use innerText
                raw_text = el.get_attribute("innerText")
                if not raw_text: continue
                
                class_attr = el.get_attribute("class")
                if "si-plist__row--title" in class_attr:
                    continue
                
                text_content = raw_text.split('\n')
                text_content = [t.strip() for t in text_content if t.strip()]
                
                if not text_content: continue
                    
                # Basic Fields
                name = text_content[0]
                team_match = text_content[1] if len(text_content) > 1 else ""
                
                price = "0.0"
                position = "UNK"
                pos_index: int = -1
                
                known_positions = ["POR", "DEF", "MED", "DEL", "GK", "MID", "FWD", "CEN"]
                
                # Dynamic Logic: Find Position Index
                for i, t in enumerate(text_content):
                    if t in known_positions:
                        position = t
                        pos_index = i
                        break
                
                # Find Price (usually before position)
                if pos_index > -1:
                    # Look backwards from position for price
                    for i in range(int(pos_index) - 1, -1, -1):
                        t = text_content[i]
                        if re.search(r'\d', t) and (('€' in t) or ('m' in t) or re.match(r'^\d+(\.\d+)?$', t)):
                            price = t
                            break
                            
                # Parse Stats relative to Position Index
                # Structure seen: Pos (idx) | Total Pts | Sel % | Pts Day | Pts/Euro | Pts/MD | POTM | Goals | Assists | Balls | Clean | Red | Yellow | Mins | Transfers | Next Match
                stats = {
                    "ptos_total": "", "seleccionado": "", "ptos_jornada": "", "ptos_por_euro": "",
                    "ptos_per_md": "", "ptos_potm": "", "goles": "", "asistencias": "",
                    "balones_recuperados": "", "porteria_a_0": "", "tarjetas_rojas": "",
                    "tarjetas_amarillas": "", "mins_jugados": "", "fichados": "", "prox_partido": "",
                    "estado_forma": ""
                }
                
                if pos_index > -1:
                    try:
                        # Map based on offset from Position
                        stats["ptos_total"] = text_content[pos_index + 1]
                        stats["seleccionado"] = text_content[pos_index + 2]
                        stats["ptos_jornada"] = text_content[pos_index + 3]
                        stats["ptos_por_euro"] = text_content[pos_index + 4]
                        stats["ptos_per_md"] = text_content[pos_index + 5]
                        stats["ptos_potm"] = text_content[pos_index + 6]
                        stats["goles"] = text_content[pos_index + 7]
                        stats["asistencias"] = text_content[pos_index + 8]
                        stats["balones_recuperados"] = text_content[pos_index + 9]
                        stats["porteria_a_0"] = text_content[pos_index + 10]
                        stats["tarjetas_rojas"] = text_content[pos_index + 11]
                        stats["tarjetas_amarillas"] = text_content[pos_index + 12]
                        stats["mins_jugados"] = text_content[pos_index + 13]
                        stats["fichados"] = text_content[pos_index + 14]
                        stats["prox_partido"] = text_content[pos_index + 15]
                    except IndexError:
                        pass # Handle partial data gracefully

                # Extract Form (Stars)
                try:
                    stars_container = el.find_element(By.CSS_SELECTOR, ".si-plyr__ratingStar")
                    stars = stars_container.find_elements(By.CSS_SELECTOR, "span")
                    score = 0.0
                    for s in stars:
                        c = s.get_attribute("class")
                        if "si-1" in c: score += 1.0
                        elif "si-05" in c: score += 0.5
                    stats["estado_forma"] = f"{score} stars"
                except:
                    stats["estado_forma"] = "N/A"

                # Final Object
                p_data = {
                    "name": name,
                    "team_match": team_match,
                    "position": position,
                    "price": price,
                    **stats
                }
                all_players.append(p_data)
                    
            except Exception as e:
                # print(f"Error parsing specific player: {e}")
                continue

    except Exception as e:
        print(f"Global error: {e}")
    finally:
        driver.quit()
        
    # Save Data
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(all_players)} players to players.json")

if __name__ == "__main__":
    scrape_players()
