from bs4 import BeautifulSoup
from .utils import clean_text, normalize_date

class Extractor:
    def parse(self, html_content: str, url: str):
        soup = BeautifulSoup(html_content, "lxml")
        data = {
            "url": url,
            "title": self._extract_title(soup),
            "date": self._extract_date(soup),
            "author": self._extract_author(soup),
            "content": self._extract_content(soup),
            "description": self._extract_description(soup),
            "category": self._extract_category(soup),
            "tags": self._extract_tags(soup),
            "scraped_at": self._get_current_time()
        }
        return data

    def _extract_category(self, soup):
        import json
        
        # 1. Try JSON-LD (BreadcrumbList)
        ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in ld_scripts:
            try:
                if not script.string: continue
                data = json.loads(script.string)
                if isinstance(data, dict):
                    data_list = [data]
                elif isinstance(data, list):
                    data_list = data
                else:
                    continue
                
                for item in data_list:
                    # BreadcrumbList
                    if item.get('@type') == 'BreadcrumbList' and 'itemListElement' in item:
                        items = item['itemListElement']
                        if items:
                            # Sort by position if available, or assume order
                            sorted_items = sorted(items, key=lambda x: int(x.get('position', 0)))
                            # Usually the 2nd or 3rd item is the category (Home > Category > Subcat)
                            # Let's take the last one before the article itself, or just the second one
                            if len(sorted_items) >= 2:
                                return self.clean_text(sorted_items[1]['item']['name'])
                            if len(sorted_items) > 0:
                                return self.clean_text(sorted_items[-1]['item']['name'])
                                
                    # NewsArticle / Article articleSection
                    if item.get('@type') in ['NewsArticle', 'Article', 'ReportageNewsArticle']:
                        if 'articleSection' in item:
                             section = item['articleSection']
                             if isinstance(section, list):
                                 return self.clean_text(section[0])
                             return self.clean_text(section)
            except:
                continue

        # 2. Meta Tags
        cat_meta = soup.find("meta", property="article:section") or \
                   soup.find("meta", attrs={"name": "category"}) or \
                   soup.find("meta", attrs={"name": "section"})
        if cat_meta:
            return clean_text(cat_meta.get("content"))

        if cat_meta:
            return clean_text(cat_meta.get("content"))

        # 3. Common WordPress / standard generic Classes
        cat_link = soup.find("a", attrs={"rel": "category tag"})
        if cat_link:
             return clean_text(cat_link.get_text())
             
        cat_elem = soup.select_one(".category, .post-category, .article-category, .cat-links")
        if cat_elem:
             return clean_text(cat_elem.get_text())

        # 4. URL path segments (heuristic)
        # e.g., domain.com/sports/article-name -> processed in Crawler usually, but good fallback here
        # We can't easily see the URL here unless we pass it, which we do
        if "url" in locals():
            from urllib.parse import urlparse
            path = urlparse(url).path 
            parts = [p for p in path.split('/') if p]
            if len(parts) > 0:
                # heuristic: first non-empty part that isn't date-like or 'news'
                # Check specific positions often used for categories
                candidate = parts[0]
                if candidate.lower() not in ['news', 'article', 'video', '2024', '2025', '2026'] and not candidate.isdigit() and len(candidate) > 3:
                     return candidate.capitalize()
                if len(parts) > 1:
                     candidate = parts[1]
                     if candidate.lower() not in ['news', 'article', 'video'] and not candidate.isdigit():
                          return candidate.capitalize()

        # 4. Common Breadcrumb HTML
        breadcrumb = soup.select_one(".breadcrumb, .breadcrumbs, .crt-breadcrumb")
        if breadcrumb:
            text = breadcrumb.get_text()
            # Try to split by common separators
            parts = [p.strip() for p in text.replace('>', '|').replace('/', '|').split('|') if p.strip()]
            if len(parts) > 1:
                 return parts[1] # Usually Home > Category

        return ""

    def _extract_title(self, soup):
        if soup.h1:
            return clean_text(soup.h1.get_text())
        if soup.title:
            return clean_text(soup.title.get_text())
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return clean_text(og_title.get("content"))
        return ""

    def _extract_date(self, soup):
        import dateparser
        
        # Try meta tags first
        date_meta = soup.find("meta", property="article:published_time") or \
                    soup.find("meta", attrs={"name": "date"}) or \
                    soup.find("time")
                    
        date_str = ""
        if date_meta:
            if date_meta.name == "time":
                date_str = date_meta.get("datetime") or date_meta.get_text()
            else:
                date_str = date_meta.get("content")
        
        # Try generic text patterns for date
        if not date_str:
            for text_pattern in ["Updated:", "Created:", "Published:", "Date:"]:
                element = soup.find(lambda tag: tag.name in ['span', 'div', 'p'] and text_pattern in tag.get_text())
                if element:
                    text = element.get_text().strip()
                    if text_pattern in text:
                         try:
                             potential_date = text.split(text_pattern, 1)[1].strip()
                             potential_date = " ".join(potential_date.split()[:5]) 
                             dt = dateparser.parse(potential_date)
                             if dt: return dt.isoformat()
                         except:
                             pass
        
        # Specific meta tags for India Today and others
        if not date_str:
            meta_date = soup.find("meta", attrs={"name": "publish-date"}) or \
                        soup.find("meta", property="og:updated_time")
            if meta_date:
                date_str = meta_date.get("content")

        # Try JSON-LD (common in modern news sites)
        if not date_str:
            import json
            ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in ld_scripts:
                try:
                    if not script.string: continue
                    data = json.loads(script.string)
                    
                    # Normalize to list to handle both dict and list of dicts
                    if isinstance(data, dict):
                        data_list = [data]
                    elif isinstance(data, list):
                        data_list = data
                    else:
                        continue
                        
                    for item in data_list:
                        if not isinstance(item, dict): continue
                        
                        # NewsArticle / Article
                        if 'datePublished' in item:
                            dt = dateparser.parse(item['datePublished'])
                            if dt: return dt.isoformat()
                        if 'dateCreated' in item:
                            dt = dateparser.parse(item['dateCreated'])
                            if dt: return dt.isoformat()
                            
                        # VideoObject (India Today videos)
                        if item.get('@type') == 'VideoObject' and 'uploadDate' in item:
                            dt = dateparser.parse(item['uploadDate'])
                            if dt: return dt.isoformat()
                except:
                    continue

        if date_str:
            dt = dateparser.parse(date_str)
            if dt:
                return dt.isoformat()
        return ""

    def _extract_author(self, soup):
        author_meta = soup.find("meta", property="author") or \
                      soup.find("meta", attrs={"name": "author"})
        if author_meta:
            return clean_text(author_meta.get("content"))
            
        # Try JSON-LD first (reliable)
        import json
        ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in ld_scripts:
            try:
                if not script.string: continue
                data = json.loads(script.string)
                
                if isinstance(data, dict):
                    data_list = [data]
                elif isinstance(data, list):
                    data_list = data
                else:
                    continue

                for item in data_list:
                    if not isinstance(item, dict): continue
                    
                    if 'author' in item:
                        author_data = item['author']
                        if isinstance(author_data, list): 
                            # Join multiple authors if present
                            names = []
                            for a in author_data:
                                if isinstance(a, dict) and 'name' in a: names.append(clean_text(a['name']))
                                elif isinstance(a, str): names.append(clean_text(a))
                            if names: return ", ".join(names)
                            
                        if isinstance(author_data, dict) and 'name' in author_data:
                            return clean_text(author_data['name'])
                        if isinstance(author_data, str):
                            return clean_text(author_data)
            except:
                continue

        author_tag = soup.find(class_=lambda x: x and "author" in x.lower())
        if author_tag:
            return clean_text(author_tag.get_text())
            
        # Common byline classes/attributes
        for selector in [".byline", ".auth-nm", "[itemprop='author']", ".writer", ".journalist", ".profile-details", ".story__author"]:
            elem = soup.select_one(selector)
            if elem:
                return clean_text(elem.get_text())
                
        # "By [Name]" pattern
        by_text = soup.find(lambda tag: tag.name in ['span', 'div', 'p'] and "By" in tag.get_text() and len(tag.get_text()) < 50)
        if by_text:
            text = by_text.get_text().strip()
            if text.lower().startswith("by") and len(text) < 50:
                 # Check if it looks like a name (no numbers, etc)
                 candidate = text[2:].strip()
                 if candidate and len(candidate.split()) < 5:
                     return clean_text(candidate)

        return ""

    def _extract_content(self, soup):
        # Heuristics for content
        article = soup.find("article")
        if article:
            return clean_text(article.get_text())
            
        main = soup.find("main")
        if main:
            return clean_text(main.get_text())
            
        # Fallback to largest text block ? (too expensive maybe, stick to generic classes)
        content_div = soup.find("div", class_=lambda x: x and ("content" in x.lower() or "body" in x.lower() or "article" in x.lower()))
        if content_div:
            return clean_text(content_div.get_text())
            
        return ""

    def _extract_description(self, soup):
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            return clean_text(og_desc.get("content"))
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            return clean_text(desc.get("content"))
        return ""
        
    def _extract_tags(self, soup):
        tags = []
        # Look for keywords meta
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords and keywords.get("content"):
            tags.extend([t.strip() for t in keywords.get("content").split(",")])
        return tags

    def _get_current_time(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
