
import asyncio
from scraper.crawler import Crawler
from scraper.extractor import Extractor

async def fetch():
    crawler = Crawler()
    url = "https://www.hindustantimes.com/cricket/players/tim-david-67402"
    
    print(f"Launching browser...")
    async with asyncio.TaskGroup() as tg:
         from playwright.async_api import async_playwright
         async with async_playwright() as p:
            # Use a real user agent to avoid being blocked/served empty pages
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            
            # Go to section page first to find a live link
            await page.goto("https://www.biovoicenews.com/", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            
            # Find first article link
            article_link_el = await page.query_selector("h2 a, h3 a, article a")
            if not article_link_el:
                 print("Could not find article link on listing page")
                 return
            
            url = await article_link_el.get_attribute("href")
            print(f"Found article URL: {url}")
            
            await page.goto(url, wait_until="domcontentloaded")
            
            # Wait for content
            await page.wait_for_timeout(5000)

            content = await page.content()
            
            with open("bio_sample.html", "w", encoding="utf-8") as f:
                f.write(content)
                
            print("Saved ht_sample.html")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch())
