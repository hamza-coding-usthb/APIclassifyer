import re
from urllib.parse import unquote
import os

def extract_categories_from_sitemap(sitemap_file="sitemap-category.xml"):
    """
    Extracts API categories from the sitemap.xml file using regex.

    Args:
        sitemap_file (str): The path to the sitemap XML file.

    Returns:
        list: A list of decoded category names.
    """
    print(f"🔎 Extracting categories from {sitemap_file}...")
    try:
        with open(sitemap_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find all category names within the <loc> tags
        # It captures the part of the URL after "/search/"
        pattern = r"<loc>https://rapidapi.com/search/(.*?)</loc>"
        
        # Find all matches and decode URL-encoded characters (e.g., %20 -> space)
        encoded_categories = re.findall(pattern, content)
        decoded_categories = [unquote(cat) for cat in encoded_categories]
        
        return decoded_categories
    except FileNotFoundError:
        print(f"❌ Error: Sitemap file not found at '{sitemap_file}'")
        return []

if __name__ == "__main__":
    sitemap_path = os.path.join(os.path.dirname(__file__), "sitemap-category.xml")
    categories = extract_categories_from_sitemap(sitemap_path)
    
    if categories:
        print(f"\n✅ Successfully extracted {len(categories)} categories:")
        for i, category in enumerate(categories):
            print(f"  {i+1}. {category}")

