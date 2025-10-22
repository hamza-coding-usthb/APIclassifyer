from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

class GitHubAppsScraperFixed:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Start with browser visible for debugging
        chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        self.base_url = "https://github.com"
        
    def scrape_all_apps(self):
        """Main method to scrape all apps"""
        print("🚀 Starting GitHub Apps Scraper - Fixed Version")
        
        all_apps = []
        unique_urls = set()
        
        # Then try category by category
        categories = self.get_categories()
        
        for category in categories:
            try:
                print(f"\n📦 Attempting category: {category}")
                category_apps = self._scrape_all_pages_for_category(category)
                if category_apps: # Add only new apps
                    new_apps = [app for app in category_apps if app['url'] not in unique_urls]
                    all_apps.extend(new_apps)
                    for app in new_apps:
                        unique_urls.add(app['url'])
                    print(f"✅ Category '{category}': {len(category_apps)} apps")
                else:
                    print(f"⚠️  Category '{category}': 0 apps")
            except Exception as e:
                print(f"❌ Category '{category}' failed: {e}")
                continue
        
        # Also scrape the main page for any apps not in categories
        print("\n📦 Attempting main marketplace page")
        main_page_apps = self._scrape_all_pages_for_category(None)
        new_apps = [app for app in main_page_apps if app['url'] not in unique_urls]
        all_apps.extend(new_apps)
        print(f"✅ Main Page: {len(new_apps)} new apps")

        return all_apps

    def _extract_apps_from_page(self, current_category):
        """A single, more reliable strategy to extract app data from a page."""
        apps = []
        # This selector targets the link that acts as a container for the app card.
        app_card_selector = "div[data-testid='marketplace-item']"
        
        try:
            # Wait for the app cards to be present on the page
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, app_card_selector)))
            app_cards = self.driver.find_elements(By.CSS_SELECTOR, app_card_selector)
            print(f"  🔍 Found {len(app_cards)} app cards.")

            for card in app_cards:
                name, description, url = "Unknown", "No description found", " "
                try:
                    # The URL is the href of the card itself
                    url_element = card.find_element(By.CSS_SELECTOR, "a")
                    url = url_element.get_attribute('href')
                    if not url or 'category=' in url or 'type=' in url:
                        continue # Skip category links

                    # The name is in an h3 tag inside the card
                    name_element = card.find_element(By.CSS_SELECTOR, "h3")
                    name = name_element.text.strip()

                    # The description is in a p tag with a specific class, also inside the card
                    description_element = card.find_element(By.CSS_SELECTOR, "p")
                    description = description_element.text.strip()

                    if name and name != "Unknown":
                        apps.append({
                            'name': name,
                            'description': description,
                            'category': current_category or 'Uncategorized',
                            'url': url,
                            'scraped_at': pd.Timestamp.now().isoformat()
                        })
                except Exception as ex:
                    # This can happen if a card doesn't match the structure, so we skip it.
                    # print(f"    - Skipping a card, couldn't parse. Error: {ex}")
                    # This can happen if a card doesn't match the structure, so we skip it.
                    continue
        except Exception as e:
            print(f"  ⚠️  Could not extract apps from this page: Message: {e}")
        return apps

    def get_categories(self):
        """Extracts category slugs from the marketplace sidebar."""
        print("🔍 Discovering categories...")
        self.driver.get(f"{self.base_url}/marketplace?type=apps")
        categories = []
        try:
            # Wait for the sidebar links to be visible
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "nav ul li a[href*='category=']")))
            category_links = self.driver.find_elements(By.CSS_SELECTOR, "nav ul li a[href*='category=']")
            for link in category_links:
                href = link.get_attribute('href')
                if 'type=apps' in href:
                    category = href.split('category=')[1].split('&')[0]
                    if category and category not in categories:
                        categories.append(category)
            print(f"✅ Found {len(categories)} categories.")
        except Exception as e:
            print(f"⚠️ Could not automatically discover categories: {e}. Using a fallback list.")
            # Provide a fallback list in case the dynamic discovery fails
            return ['actions', 'chat', 'code-quality', 'code-review', 'continuous-integration', 'dependency-management', 'deployment', 'ides', 'learning', 'localization', 'mobile', 'monitoring', 'project-management', 'publishing', 'security', 'support', 'testing', 'utilities']
        
        return categories
    
    def _scrape_all_pages_for_category(self, category):
        """Scrapes all pages for a given category, handling pagination."""
        all_category_apps = []
        page_num = 1

        try:
            if category:
                url = f"{self.base_url}/marketplace?type=apps&category={category}"
            else:
                url = f"{self.base_url}/marketplace?type=apps"

            print(f"  ➡️ Navigating to page 1: {url}")
            self.driver.get(url)

            while True:
                print(f"    📄 Scraping page {page_num}...")
                page_apps = self._extract_apps_from_page(category)
                if not page_apps and page_num > 1 and not self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='marketplace-item']"):
                    print("    No more apps found on this page.")
                    break
                all_category_apps.extend(page_apps)

                # Find and click the "Next" button
                try:
                    # Find the pagination container and then the 'Next' button within it.
                    pagination_container = self.driver.find_element(By.CSS_SELECTOR, "nav[aria-label='Pagination']")
                    next_button = pagination_container.find_element(By.CSS_SELECTOR, "a[rel='next']")
                    
                    # Check if the button is disabled (which means it's the last page)
                    if next_button.get_attribute("aria-disabled") == "true":
                        print("    'Next' button is disabled. Reached the last page for this category.")
                        break
                    
                    next_button.click() # Click the enabled "Next" button
                    print(f"    Navigating to page {page_num + 1}...")
                    time.sleep(1) 
                    page_num += 1 
                except Exception:
                    print("    No 'Next' button found. Reached the last page for this category.")
                    break # No "Next" button means we're on the last page
            return all_category_apps
        except Exception as e:
            print(f"  ❌ An error occurred while scraping category '{category}': {e}")
            return all_category_apps # Return what we have so far
    
    def save_to_csv(self, apps, filename="github_apps_fixed.csv"):
        """Save apps to CSV"""
        if not apps:
            print("❌ No apps to save")
            return None
            
        df = pd.DataFrame(apps)
        
        # Remove duplicates based on URL
        df = df.drop_duplicates(subset=['url'], keep='first').reset_index(drop=True)
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"💾 Saved {len(df)} unique apps to {filename}")
        
        # Summary
        if 'category' in df.columns:
            summary = df.groupby('category').size().reset_index(name='count')
            print("\n📊 Summary:")
            for _, row in summary.iterrows():
                print(f"  {row['category']}: {row['count']} apps")
        
        return filename
    
    def close(self):
        """Close browser"""
        self.driver.quit()

# Main execution
if __name__ == "__main__":
    print("🎯 GitHub Marketplace Scraper - Refactored Version")
    
    scraper = GitHubAppsScraperFixed()
    try:
        apps = scraper.scrape_all_apps()
        
        if apps:
            # Create a DataFrame and count unique apps before saving
            df = pd.DataFrame(apps)
            unique_apps_df = df.drop_duplicates(subset=['url'], keep='first')
            num_unique_apps = len(unique_apps_df)

            filename = scraper.save_to_csv(list(unique_apps_df.to_dict('records')))
            print(f"\n✅ Success! Collected {num_unique_apps} unique apps.")
            
            print("\n👀 Sample apps:")
            for i, app in enumerate(apps[:10]):
                print(f"  {i+1}. {app['name']}")
                print(f"     URL: {app['url']}")
                print(f"     Desc: {app['description'][:80]}...")
        else:
            print("\n❌ No apps found. Check the debug files for insights.")
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
    finally:
        scraper.close()