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
            # repo name
            a_tag = row.select_one("h2 a")
            if not a_tag:
                continue

            full_name = a_tag.get_text(strip=True).replace(" ", "")
            if "/" not in full_name:
                continue

            owner, repo_name = full_name.split("/", 1)

            # stars earned
            stars_earned = 0
            stats = row.select("div.f6 span")

            for span in stats:
                text = span.get_text(strip=True).lower()
                if "star" in text:
                    num = re.sub(r"[^\d]", "", text)
                    stars_earned = int(num) if num else 0
                    break

            repos.append({
                "owner": owner,
                "repo": repo_name,
                "stars_earned": stars_earned
            })

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
