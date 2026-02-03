
import json
from bs4 import BeautifulSoup

def find_in_obj(obj, target, path="", results=[]):
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_in_obj(v, target, f"{path}.{k}", results)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_in_obj(v, target, f"{path}[{i}]", results)
    elif isinstance(obj, str):
        if target.lower() in obj.lower():
            results.append(f"Found '{target}' at path: {path}")

def inspect_next_data():
    with open("ht_sample_news.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")
    next_data_script = soup.find("script", id="__NEXT_DATA__")
    
    results = []
    
    if not next_data_script:
        results.append("No __NEXT_DATA__ script found.")
    else:
        try:
            data = json.loads(next_data_script.string)
            # Search for headline word
            find_in_obj(data, "strictures", "root", results)
            find_in_obj(data, "datePublished", "root", results)

        except Exception as e:
            results.append(f"Error parsing JSON: {e}")
            
    with open("path_dump.txt", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    inspect_next_data()
