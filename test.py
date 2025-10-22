import requests
import xml.etree.ElementTree as ET

def extract_from_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    root = ET.fromstring(response.content)
    
    urls = []
    for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        urls.append(url.text)
    
    return urls

# Get all API-related URLs
api_urls = extract_from_sitemap("https://rapidapi.com/sitemap-category.xml")
print(api_urls)