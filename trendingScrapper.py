from bs4 import BeautifulSoup
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

def get_trending_repos(language="", since="daily"):
    url = "https://github.com/trending"
    if language:
        url += f"/{language}"

    print(f"Scraping {language or 'all languages'} | {since}")

    try:
        response = requests.get(
            url,
            params={"since": since},
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
    except Exception as e:
        print("Failed to fetch GitHub page:", e)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    repos = []

    for row in soup.find_all("article", class_="Box-row"):
        try:
            # Find the h2 with class "h3 lh-condensed"
            h2_tag = row.find("h2", class_="h3")
            if not h2_tag:
                continue
            
            # Find the link inside h2
            a_tag = h2_tag.find("a")
            if not a_tag:
                continue

            # Get href which contains /owner/repo
            href = a_tag.get("href", "")
            if not href or href.count("/") < 2:
                continue
            
            # Parse owner and repo from href (format: /owner/repo)
            parts = href.strip("/").split("/")
            if len(parts) < 2:
                continue
            
            owner = parts[0]
            repo_name = parts[1]

            # Find stars earned - look for span with "stars today" or similar text
            stars_earned = 0
            
            # Try to find the stats section - usually in a div after h2
            stats_section = row.find("div", class_="f6")
            if stats_section:
                spans = stats_section.find_all("span")
                for span in spans:
                    text = span.get_text(strip=True).lower()
                    # Look for pattern like "123 stars today" or "1,234 stars this week"
                    if "star" in text:
                        # Extract numbers from text like "123 stars today"
                        match = re.search(r'([\d,]+)\s*star', text)
                        if match:
                            num_str = match.group(1).replace(",", "")
                            stars_earned = int(num_str) if num_str.isdigit() else 0
                            break

            repos.append({
                "owner": owner,
                "repo": repo_name,
                "stars_earned": stars_earned
            })
            
            print(f"Found: {owner}/{repo_name} ({stars_earned} stars)")

        except Exception as e:
            print("Skipping row:", e)

    return repos


def push_trending_repos(repos, category):
    BACKEND_URL = os.getenv("BACKEND_URL")
    SECRET_KEY = os.getenv("ADMIN_SECRET")

    if not BACKEND_URL:
        print("Error: BACKEND_URL not set")
        return

    if not SECRET_KEY:
        print("Error: ADMIN_SECRET not set")
        return

    if not repos:
        print(f"No repos to send for {category}")
        return

    payload = {
        "repoList": repos,
        "category": category
    }

    headers = {
        "Content-Type": "application/json",
        "x-admin-secret": SECRET_KEY
    }

    try:
        res = requests.post(
            BACKEND_URL,
            json=payload,
            headers=headers,
            timeout=15
        )

        if res.status_code == 200:
            print(f"{category} pushed successfully")
            print("Response:", res.json())
        else:
            print(f"Failed ({res.status_code}):", res.text)

    except Exception as e:
        print("Connection error:", e)


if __name__ == "__main__":
    mode = os.getenv("SCRAPE_MODE", "daily").lower()

    if mode in {"daily", "weekly", "monthly"}:
        data = get_trending_repos(since=mode)
        push_trending_repos(data, category=mode)
    else:
        print("Invalid SCRAPE_MODE:", mode)
