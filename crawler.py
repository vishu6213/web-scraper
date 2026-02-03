import asyncio
from playwright.async_api import async_playwright

class Crawler:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        
    async def run(self, url: str, max_pages: int, output_base: str, output_format: str, headless: bool = True, start_date: str = None, end_date: str = None, categories: list = None):
        from scraper.extractor import Extractor
        from exporter.writer import write_data
        from datetime import datetime
        import dateparser
        
        # Parse filter dates
        filter_start = dateparser.parse(start_date) if start_date else None
        filter_end = dateparser.parse(end_date) if end_date else None
        
        if filter_start:
            print(f"Filtering items from {filter_start.strftime('%Y-%m-%d')}")
        if filter_end:
            print(f"Filtering items up to {filter_end.strftime('%Y-%m-%d')}")
        if categories:
            print(f"Filtering items by categories: {categories}")
        
        extractor = Extractor()
        collected_data = []
        visited_urls = set()
        
        print(f"Launching browser (Headless: {headless})...")
        async with async_playwright() as p:
            self.playwright = p
            # Disable automation flags to be less detectable
            self.browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                device_scale_factor=1,
                locale="en-US",
            )
            
            # Inject stealth script to hide webdriver property
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await self.context.new_page()
            results = []
            
            current_url = url
            is_pagination_active = True
            
            print(f"Starting crawl at {url}")
            
            try:
                # Increased timeout for initial load and potential challenges
                await page.goto(current_url, timeout=60000, wait_until="domcontentloaded")
                
                # Cloudflare bypass check
                for _ in range(5):
                    title = await page.title()
                    if "One moment" in title or "Just a moment" in title:
                        print(f"Cloudflare challenge detected (Title: {title}). Waiting...")
                        await page.wait_for_timeout(5000)
                    else:
                        break
                
                # Wait a bit extra for dynamic content or challenges
                await page.wait_for_timeout(5000) 
            except Exception as e:
                print(f"Failed to load initial page: {e}")
                return

            max_items = max_pages 

            while len(results) < max_items and is_pagination_active:
                # 1. Extract Links from current listing page
                try:
                    links = await self._extract_links(page, categories)
                    print(f"Found {len(links)} potential article links on current page.")
                except Exception as e:
                    print(f"Error extracting links: {e}")
                    links = []
                
                # 2. Visit each link in PARALLEL
                # Create a semaphore to limit concurrency
                sem = asyncio.Semaphore(5)  # Adjust concurrency level as needed

                async def scrape_wrapper(link):
                    if link in visited_urls:
                        return None
                    visited_urls.add(link)
                    
                    async with sem:
                        try:
                            print(f"Scraping: {link}")
                            # Create a fresh page for each task
                            detail_page = await self.context.new_page()
                            try:
                                await detail_page.goto(link, timeout=45000, wait_until="domcontentloaded")
                                
                                # Wait for content (lighter wait)
                                try:
                                    await detail_page.wait_for_load_state("domcontentloaded", timeout=15000)
                                except:
                                    pass
                                    
                                content = await detail_page.content()
                                data = extractor.parse(content, link)
                                
                                if data.get("title"):
                                    # Post-processing filters
                                    item_category = data.get("category", "").lower()
                                    item_tags = [t.lower() for t in data.get("tags", [])]
                                    
                                    keep_item = True
                                    if categories:
                                        # RELAXED: If category is empty but we have content, keep it? 
                                        # Or better: Check if categories matches EITHER category OR tags OR generic search
                                        # For now, let's keep the logic but maybe relax the "empty" check if user complains?
                                        # The users complaint was "0 items".
                                        # Let's search the DESCRIPTION or TITLE for the category keywords as a fallback
                                        
                                        title_lower = data.get("title", "").lower()
                                        desc_lower = data.get("description", "").lower()
                                        
                                        cat_match = any(cat.lower() in item_category for cat in categories)
                                        tag_match = any(any(cat.lower() in t for t in item_tags) for cat in categories)
                                        content_match = any(cat.lower() in title_lower or cat.lower() in desc_lower for cat in categories)
                                        
                                        if not (cat_match or tag_match or content_match):
                                            print(f"Skipping article: '{data['title'][:20]}' - No match for {categories}")
                                            keep_item = False
                                    
                                    # Date Logic
                                    item_date_str = data.get("date")
                                    if item_date_str and (filter_start or filter_end):
                                        item_date = dateparser.parse(item_date_str)
                                        if item_date:
                                            if item_date.tzinfo and not filter_start.tzinfo:
                                                 item_date = item_date.replace(tzinfo=None)
                                            if filter_start and item_date < filter_start:
                                                print(f"Skipping: Too old ({item_date})")
                                                keep_item = False
                                            if filter_end and item_date > filter_end:
                                                print(f"Skipping: Too new ({item_date})")
                                                keep_item = False
                                    
                                    if keep_item:
                                        print(f"Extracted: {data['title'][:30]}...")
                                        return data
                                    else:
                                        return None  # Filtered out
                                else:
                                    print(f"Skipped {link}: No title")
                                    return None
                            except Exception as e:
                                print(f"Error scraping {link}: {e}")
                                return None
                            finally:
                                await detail_page.close()
                        except Exception as e:
                            print(f"Task error {link}: {e}")
                            return None

                # Create tasks
                tasks = [scrape_wrapper(link) for link in links if link not in visited_urls]
                
                # Run batch
                if tasks:
                    batch_results = await asyncio.gather(*tasks)
                    # Filter None results
                    valid_results = [r for r in batch_results if r]
                    results.extend(valid_results)
                    print(f"Batch finished. Total items: {len(results)}")
                
                # Check limits
                if len(results) >= max_items:
                    break

                        
                # 3. Handle Pagination
                if len(results) < max_items:
                    try:
                        has_next = await self._handle_pagination(page)
                    except Exception as e:
                        print(f"Pagination error: {e}")
                        has_next = False
                        
                    if not has_next:
                        print("No more pages found or pagination ended.")
                        is_pagination_active = False
                    else:
                        print("Navigating to next page...")
                        await asyncio.sleep(2)

            print(f"Crawl finished. Collected {len(results)} items.")
            write_data(results, output_base, output_format, source_url=url)
            await self.browser.close()

    async def _extract_links(self, page, categories=None):
        links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links
                    .map(link => link.href)
                    .filter(href => href.startsWith(window.location.origin)) 
                    .filter(href => href.length > window.location.href.length + 10) 
            }
        """)
        
        unique_links = list(set(links))
        
        # Blacklist for common non-article pages
        blacklist = [
            'privacy', 'terms', 'policy', 'about-us', 'contact', 'login', 'signup', 
            'subscribe', 'rss', 'archive', 'newsletter', 'preference', 'advertisement',
            'correction', 'syndication', 'careers', 'sitemap'
        ]
        
        from urllib.parse import urlparse
        
        filtered_links = []
        for link in unique_links:
            # 1. Check blacklist
            if any(b in link.lower() for b in blacklist):
                continue
                
            # 2. Check categories (strict path matching) - RELAXED
            # We no longer strictly filter by URL path for categories because many sites 
            # (like Tribune India) don't put the category in the URL consistently.
            # We will filter AFTER extraction.
            # if categories:
            #     parsed = urlparse(link)
            #     path = parsed.path.lower()
            #     # Check if any category is in the PATH, not just the whole url (avoid domain matches)
            #     if not any(cat.lower() in path for cat in categories):
            #         continue
            
            filtered_links.append(link)
            
        return filtered_links

    async def _handle_pagination(self, page):
        next_selectors = [
            "text=Next", "text=next", "text=More", "text=Load more",
            "[aria-label='Next']", ".next", ".pagination-next", "a[rel='next']"
        ]
        
        for selector in next_selectors:
            if await page.is_visible(selector):
                try:
                    # Scroll to element to ensure visibility
                    await page.eval_on_selector(selector, "el => el.scrollIntoView()")
                    await page.click(selector, timeout=5000)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    return True
                except:
                    continue
                    
        # Scroll check
        previous_height = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        new_height = await page.evaluate("document.body.scrollHeight")
        
        if new_height > previous_height:
            return True
            
        return False
