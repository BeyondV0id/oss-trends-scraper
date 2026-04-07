from bs4 import BeautifulSoup

def analyze_html():
    with open("github_trending.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("article", class_="Box-row")
    print(f"Total rows found with class 'Box-row': {len(rows)}")
    
    if len(rows) < 25:
        print("GitHub might have changed the structure.")
        # Check for other possible structures
        all_articles = soup.find_all("article")
        print(f"Total article tags: {len(all_articles)}")
        
        # Check for div with class Box-row
        div_rows = soup.find_all("div", class_="Box-row")
        print(f"Total div tags with class 'Box-row': {len(div_rows)}")

if __name__ == "__main__":
    analyze_html()
