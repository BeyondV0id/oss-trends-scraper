from bs4 import BeautifulSoup

def analyze_articles():
    with open("github_trending.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article")
    print(f"Total articles: {len(articles)}")
    
    for i, article in enumerate(articles):
        classes = article.get("class", [])
        h2 = article.find("h2")
        h2_class = h2.get("class", []) if h2 else "No h2"
        print(f"Article {i+1}: class={classes}, h2_class={h2_class}")

if __name__ == "__main__":
    analyze_articles()
