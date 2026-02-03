
from bs4 import BeautifulSoup

def inspect_content():
    with open("ht_sample_news.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")
    h1 = soup.find("h1")
    if h1:
        print(f"H1 Text: {h1.get_text().strip()}")
    else:
        print("H1 not found")

    # Check for common article body containers in HT
    article_body = soup.select_one(".storyDetail, .story-details, .detail")
    if article_body:
         print(f"Article Body found (.storyDetail/etc): {article_body.get_text().strip()[:100]}...")
    else:
         print("Common article body selectors not found")
         
    # Check for meta updated time again (using BS4)
    meta_date = soup.find("meta", property="article:published_time")
    if meta_date:
        print(f"Meta Date: {meta_date.get('content')}")
    else:
        print("Meta Date not found")
        
    # Check for ANY text that looks like the article
    # "strictures passed against him" 
    # (Removed specific text check as the article changed)
    
    # Check Author
    meta_author = soup.find("meta", property="author") or soup.find("meta", attrs={"name": "author"})
    if meta_author:
        print(f"Meta Author: {meta_author.get('content')}")
    else:
        print("Meta Author not found")
        
    # Check JSON-LD for Author and Category
    import json
    ld_scripts = soup.find_all('script', type='application/ld+json')
    print(f"Found {len(ld_scripts)} JSON-LD scripts")
    for i, script in enumerate(ld_scripts):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                print(f"JSON-LD {i} Type: {data.get('@type')}")
                if 'author' in data:
                    print(f"  Author found in JSON-LD: {data['author']}")
                if 'articleSection' in data:
                    print(f"  Category (articleSection) found: {data['articleSection']}")
        except:
            pass
            
    # Check Breadcrumbs for Category
    breadcrumb = soup.select_one(".breadcrumb, .breadcrumbs, .crt-breadcrumb")
    if breadcrumb:
        print(f"Breadcrumb found: {breadcrumb.get_text().strip()}")
    
    # Check URL for Category
    # We don't have the URL easily available here in the static file check unless we infer it


if __name__ == "__main__":
    inspect_content()
