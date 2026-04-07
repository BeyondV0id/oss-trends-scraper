from bs4 import BeautifulSoup

def analyze_html_v2():
    with open("github_trending.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    
    h2_tags = soup.find_all("h2", class_="h3")
    print(f"Total h2 tags with class 'h3': {len(h2_tags)}")
    
    for i, h2 in enumerate(h2_tags):
        a = h2.find("a")
        if a:
            print(f"{i+1}: {a.get('href')}")

if __name__ == "__main__":
    analyze_html_v2()
