from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time
import os
import re
from urllib.parse import quote

def create_driver():
    """Create and return a new Chrome driver instance"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scroll_and_load(driver, scroll_pause_time=2):
    """Scrolls to the last element to trigger loading more content."""
    try:
        # Get current number of cards
        card_selector = '[class*="group/card"]'
        num_cards_before = len(driver.find_elements(By.CSS_SELECTOR, card_selector))

        # Find the last card and scroll to it
        all_cards = driver.find_elements(By.CSS_SELECTOR, card_selector)
        if all_cards:
            last_card = all_cards[-1]
            driver.execute_script("arguments[0].scrollIntoView(true);", last_card)
            print("    ⏬ Scrolling to last card to load more APIs...")

            # Wait for new cards to load
            WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, card_selector)) > num_cards_before
            )
            time.sleep(scroll_pause_time) # Extra pause for content to settle
    except Exception:
        print("    ⚠️  Could not scroll or find new cards. Reached end of page or content failed to load.")

def extract_api_cards(driver):
    """Extract all API cards from the current page"""
    print("  🔍 Extracting API cards from page...")
    
    # Wait for cards to be present
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="group/card"]'))
        )
    except:
        print("  ⚠️  No API cards found on page")
        return []
    
    # Find all API cards using the class pattern from the HTML
    cards = driver.find_elements(By.CSS_SELECTOR, '[class*="group/card"]')
    print(f"  📊 Found {len(cards)} API cards on current page")
    
    return cards

def extract_data_from_card(card_element):
    """Extract name, category, and description from a single API card"""
    try:
        data = {
            'name': None,
            'category': None,
            'description': None
        }
        
        # Extract CATEGORY - from the category badge
        try:
            category_element = card_element.find_element(By.CSS_SELECTOR, '[class*="max-w-[100px]"]')
            data['category'] = category_element.text.strip()
        except:
            pass
        
        # Extract NAME - from the title span
        try:
            name_element = card_element.find_element(By.CSS_SELECTOR, '[class*="text-card-primary"][title]')
            data['name'] = name_element.get_attribute('title').strip()
            # Fallback to text content if title attribute is empty
            if not data['name']:
                data['name'] = name_element.text.strip()
        except:
            pass
        
        # Extract DESCRIPTION - from the description span
        try:
            desc_element = card_element.find_element(By.CSS_SELECTOR, '[class*="text-card-secondary"][title]')
            data['description'] = desc_element.get_attribute('title').strip()
            # Fallback to text content if title attribute is empty
            if not data['description']:
                data['description'] = desc_element.text.strip()
        except:
            pass
        
        # Validate that we have at least a name
        if not data['name']:
            return None
            
        return data
        
    except Exception as e:
        print(f"    ❌ Error extracting card data: {e}")
        return None

def append_api_data_to_csv(data, filename="rapidapi_search_dataset.csv"):
    """Append a single API data record to CSV file"""
    # Convert single record to DataFrame
    df_single = pd.DataFrame([data])
    
    # Check if file exists to determine whether to write header
    file_exists = os.path.isfile(filename)
    
    # Append to CSV (write header only if file doesn't exist)
    df_single.to_csv(filename, mode='a', header=not file_exists, index=False)
    print(f"    💾 Saved: {data['name']}")

def scrape_rapidapi_search_page(category=None, max_apis=None, scroll_delay=2, output_csv_prefix="rapidapi_apis"):
    """Scrape API data from RapidAPI search page with infinite scroll"""
    
    print("🚀 Starting RapidAPI Search Page Scraper")
    print("=" * 60)
    
    driver = None
    try:
        # Create driver
        driver = create_driver()
        
        # Build URL and output filename based on category
        if category:
            print(f"\n{'='*20} Scraping Category: {category} {'='*20}")
            encoded_category = quote(category, safe='')
            search_url = f"https://rapidapi.com/search/{encoded_category}?sortBy=ByRelevance"
            sanitized_category = category.replace('/', '_').replace(' ', '')
            output_csv = f"{output_csv_prefix}_{sanitized_category}.csv"
        else:
            search_url = "https://rapidapi.com/search?sortBy=ByRelevance"
            output_csv = f"{output_csv_prefix}_all.csv"

        # Navigate to search page
        print(f"🌐 Loading search page: {search_url}")
        driver.get(search_url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(3)  # Additional wait for initial content

        # Clear existing file for this category
        if os.path.exists(output_csv):
            os.remove(output_csv)
        
        all_extracted_data = []
        unique_apis = set()  # To avoid duplicates
        scroll_count = 0
        consecutive_no_new_apis = 0
        
        if max_apis:
            print(f"🎯 Target: {max_apis} APIs")
        else:
            print("🎯 Target: All available APIs")
        print("🔄 Starting infinite scroll...")
        
        while consecutive_no_new_apis < 5:
            # Break if we've hit the max_apis limit (if one is set)
            if max_apis and len(unique_apis) >= max_apis:
                break

            scroll_count += 1
            print(f"\n📜 Scroll #{scroll_count}")
            
            # Extract cards from current view
            cards = extract_api_cards(driver)
            new_apis_found = 0
            
            for i, card in enumerate(cards):
                if max_apis and len(unique_apis) >= max_apis:
                    break
                    
                data = extract_data_from_card(card)
                
                if data and data['name']:
                    # Create a unique identifier for the API
                    api_id = data['name'].lower().strip()
                    
                    if api_id not in unique_apis:
                        unique_apis.add(api_id)
                        all_extracted_data.append(data)
                        new_apis_found += 1
                        
                        # Save immediately to CSV
                        append_api_data_to_csv(data, output_csv)
                        
                        print(f"    ✅ {len(unique_apis)}. {data['name']}")
            
            print(f"    📈 New APIs this scroll: {new_apis_found}")
            print(f"    📊 Total unique APIs: {len(unique_apis)}")
            
            # Check if we're still finding new APIs
            if new_apis_found == 0:
                consecutive_no_new_apis += 1
                print(f"    ⚠️  No new APIs found ({consecutive_no_new_apis}/5)")
            else:
                consecutive_no_new_apis = 0
            
            # Scroll to trigger loading more content
            scroll_and_load(driver, scroll_pause_time=scroll_delay)
        
        print(f"\n🎉 Scraping completed!")
        print(f"   📊 Total APIs extracted: {len(unique_apis)}")
        print(f"   📜 Total scrolls: {scroll_count}")
        print(f"   💾 Data saved to: {output_csv}")
        
        return all_extracted_data
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def analyze_dataset(csv_file="rapidapi_search_dataset.csv"):
    """Analyze the scraped dataset"""
    if not os.path.exists(csv_file):
        print(f"❌ Dataset file not found: {csv_file}")
        return
    
    df = pd.read_csv(csv_file)
    print(f"\n📊 Dataset Analysis:")
    print(f"   Total APIs: {len(df)}")
    
    if 'category' in df.columns:
        category_counts = df['category'].value_counts()
        print(f"\n   Categories breakdown:")
        for category, count in category_counts.head(10).items():
            print(f"     {category}: {count}")
        
        if len(category_counts) > 10:
            print(f"     ... and {len(category_counts) - 10} more categories")
    
    # Show sample data
    print(f"\n👀 Sample data:")
    for i, row in df.head(3).iterrows():
        print(f"   {i+1}. {row['name']}")
        print(f"      Category: {row.get('category', 'N/A')}")
        print(f"      Description: {row.get('description', 'N/A')[:80]}...")

def quick_search_test(max_apis=200, scroll_delay=1):
    """Quick test of the search page scraper"""
    print("🧪 Quick Search Test")
    print("=" * 50)
    
    output_file = "rapidapi_quick_search_test.csv"
    
    # Clear existing file
    if os.path.exists(output_file):
        os.remove(output_file)
    
    data = scrape_rapidapi_search_page(
        max_apis=max_apis, 
        scroll_delay=scroll_delay, 
        output_csv=output_file
    )
    
    analyze_dataset(output_file)
    return data

def scrape_categories(categories_to_scrape, scroll_delay=2):
    """Loop through a list of categories and scrape each one."""
    print("🚀 Starting Multi-Category Scraping")
    print("=" * 50)
    total_categories = len(categories_to_scrape)

    for i, category in enumerate(categories_to_scrape):
        print(f"\nProcessing category {i+1} of {total_categories}...")
        scrape_rapidapi_search_page(
            category=category,
            max_apis=None, 
            scroll_delay=scroll_delay
        )
        print(f"✅ Finished scraping for category: {category}")
        # Optional: add a pause between categories
        if i < total_categories - 1:
            print("\nPausing for 5 seconds before next category...")
            time.sleep(5)

if __name__ == "__main__":
    
    # Define the list of categories you want to scrape
    categories_to_scrape = [
        "Mapping", "Database", "Search",
        "Food", "Financial", "Music", "Payments", "eCommerce", "Education",
        "Text Analysis", "Translation", "Media", "Commerce", "Medical",
        "Transportation", "Travel", "Visual Recognition", "News, Media",
        "Movies", "Health and Fitness", "Video, Images", "Science", "SMS",
        "Reward", "Monitoring", "Storage", "Devices", "Energy", "Logistics"
    ]

    # Run the scraper for all specified categories
    scrape_categories(categories_to_scrape, scroll_delay=1)
    
    print("\n" + "=" * 60)
    print("\n✅ All tests completed!")

    