import httpx
import os

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def fetch_html():
    url = "https://github.com/trending"
    try:
        resp = httpx.get(url, params={"since": "daily"}, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        with open("github_trending.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print("Fetched and saved to github_trending.html")
    except Exception as exc:
        print("Failed to fetch GitHub trending page:", exc)

if __name__ == "__main__":
    fetch_html()
