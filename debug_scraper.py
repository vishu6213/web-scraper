
import asyncio
from playwright.async_api import async_playwright

async def debug(url):
    print("Launching browser...")
    async with async_playwright() as p:
        # Launch headed to see if it helps with Cloudflare
        # Using args to disable automation flags
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        # Inject stealth scripts to mask webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        print(f"Navigating to {url}")
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("Initial navigation done. Waiting for potential cloudflare redirect...")
            
            # Wait 15s for Cloudflare challenge to clear
            await page.wait_for_timeout(15000)
            
            title = await page.title()
            print(f"Page Title: {title}")
            print(f"Current URL: {page.url}")
            
            # Check for links
            links_count = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).length")
            print(f"Total links found: {links_count}")
            
            # Check content
            content = await page.content()
            if "biovoice" in content.lower():
                print("Content verification: 'biovoice' found in HTML.")
            else:
                print("Content verification: 'biovoice' NOT found.")
                
            # Screenshot for debugging (saved to current folder)
            await page.screenshot(path="debug_bl_screenshot.png")
            print("Screenshot saved to debug_bl_screenshot.png")

        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug("https://biovoicenews.com/"))
