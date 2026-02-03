import asyncio
from playwright.async_api import async_playwright

async def fetch_article():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to India Today...")
        await page.goto("https://www.indiatoday.in/india", timeout=60000)
        
        # Find first story link
        print("Finding article...")
        # Select a link that looks like a story (usually under h2, h3 or specific classes)
        # Bypassing the listing page, let's try to find a link that matches /story/
        link = await page.evaluate("""
            () => {
                const anchors = Array.from(document.querySelectorAll('a'));
                const storyLink = anchors.find(a => a.href.includes('/story/') || a.href.includes('/video/'));
                return storyLink ? storyLink.href : null;
            }
        """)
        
        if link:
            print(f"Navigating to article: {link}")
            await page.goto(link, timeout=60000)
            content = await page.content()
            
            with open("it_article.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Saved to it_article.html")
        else:
            print("No article link found.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_article())
