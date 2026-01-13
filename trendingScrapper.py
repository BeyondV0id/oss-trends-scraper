from bs4 import BeautifulSoup
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

def get_trending_repos(language="", since="daily"):
    URL = "https://github.com/trending"
    print(f"Scraping {language if language else 'all languages'} and from {since}")
    if language:
        URL += f"/{language}"
    params = {"since": since}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(URL, params=params, headers=headers)
        response.raise_for_status()

    except Exception as e:
        print(f"Failed to fetch Github page :{e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    repos = []

    for row in soup.find_all("article", class_="Box-row"):
        try:
            title_tag = row.find("h2", class_="h3")
            a_tag = title_tag.find("a")
            title = a_tag.get_text(strip=True)
            title = title.replace(" ", "")
            parts = title.split("/")
            
            if len(parts) < 2:
                continue

            owner = parts[0]
            repo_name = parts[1]

            stats_div = row.find("div", class_="f6 color-fg-muted mt-2")
            if not stats_div:
                continue
                
            spans = stats_div.find_all("span")
            if not spans:
                stars_earned = 0
            else:
                raw_stars_earned = spans[-1].get_text(strip=True)
                clean_num = re.sub(r'[^\d]', '', raw_stars_earned)
                stars_earned = int(clean_num) if clean_num else 0

            repos.append({
                "owner": owner,
                "repo": repo_name,
                "stars_earned": stars_earned
            })
        except Exception as e:
            print(f"Skipping row error: {e}")
            continue

    return repos

def push_trending_repos(repos, category):
    BACKEND_URL = os.getenv("BACKEND_URL")
    SECRET_KEY = os.getenv("ADMIN_SECRET")
    
    if not SECRET_KEY:
        print("Error: ADMIN_SECRET environment variable not set.")
        return

    if not repos:
        print(f"No repos to send for {category}.")
        return
    
    print(f"Sending {len(repos)} repos of category: {category}")

    jsonData = {
        "repoList": repos,
        "category": category,
    }

    headers = {
        "Content-Type": "application/json",
        "x-admin-secret": SECRET_KEY
    }

    try:
        data = requests.post(BACKEND_URL, json=jsonData, headers=headers)
        if data.status_code == 200:
            print(f"Success: {category} processed.")
            print("Response:", data.json())
        else:
            print(f"Failed: {data.status_code} - {data.text}")

    except Exception as e:
        print(f" Connection Error: {e}")


if __name__ == "__main__":
    mode = os.getenv("SCRAPE_MODE","daily")

    if mode == "daily":
        data = get_trending_repos(since='daily')
        push_trending_repos(data, category='daily')

    elif mode == "weekly":
        data = get_trending_repos(since='weekly')
        push_trending_repos(data, category='weekly')

    elif mode == "monthly":
        data = get_trending_repos(since='monthly')
        push_trending_repos(data, category='monthly')
    
    elif:
        print("Invalid mode")
    
