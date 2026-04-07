from bs4 import BeautifulSoup

def analyze_h2_classes():
    with open("github_trending.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    h2_tags = soup.find_all("h2")
    print(f"Total h2 tags: {len(h2_tags)}")
    
    for h2 in h2_tags:
        classes = h2.get("class", [])
        print(f"h2 class: {classes}")

if __name__ == "__main__":
    analyze_h2_classes()
