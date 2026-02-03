from scraper.extractor import Extractor
import json

def test():
    with open("it_article.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    extractor = Extractor()
    data = extractor.parse(html, "http://test.com")
    
    print("Extracted Data:")
    out_json = json.dumps(data, indent=2, default=str)
    print(out_json)
    with open("debug_output.json", "w", encoding="utf-8") as f:
        f.write(out_json)

if __name__ == "__main__":
    test()
