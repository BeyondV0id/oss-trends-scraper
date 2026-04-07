import sys
import os
import json
import logging

# Set logging level to see warnings from the scraper
logging.basicConfig(level=logging.INFO)

# Add the current directory to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.scraper import scrape_trending_page

def test():
    print("Testing scrape_trending_page(since='weekly')...")
    repos = scrape_trending_page(since="weekly")
    print(f"\nScraped {len(repos)} repos.")
    if repos:
        print("First repo data:")
        print(json.dumps(repos[0], indent=2))
    else:
        print("No repos found. The scraper might be broken.")

if __name__ == "__main__":
    test()
