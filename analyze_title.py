from bs4 import BeautifulSoup

def analyze_title():
    with open("github_trending.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    print(f"Title: {soup.title.string if soup.title else 'No title'}")
    
    # Look for "trending" in the body
    if "Trending" in html:
        print("Found 'Trending' in HTML")
    
    # Check if there's a "Next" button or something
    pagination = soup.find("div", class_="pagination")
    if pagination:
        print("Found pagination")

if __name__ == "__main__":
    analyze_title()
