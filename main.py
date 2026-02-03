import argparse
import asyncio
from scraper.crawler import Crawler

def main():
    parser = argparse.ArgumentParser(description="Generic Web Scraper")
    parser.add_argument("url", nargs="?", help="Target Website URL")
    parser.add_argument("--max_pages", type=int, default=10, help="Maximum number of pages/items to scrape")
    parser.add_argument("--output", default="output", help="Output filename base (without extension)")
    parser.add_argument("--format", default="csv", choices=["csv", "xml", "docx"], help="Output format")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode (useful for debugging or bypassing anti-bot)")
    parser.add_argument("--start_date", help="Filter articles from this date (YYYY-MM-DD)")
    parser.add_argument("--end_date", help="Filter articles up to this date (YYYY-MM-DD)")
    parser.add_argument("--categories", nargs="+", help="Filter URLs by specific categories (e.g. sports business)")
    
    args = parser.parse_args()

    # Interactive Mode if no URL provided
    if not args.url:
        print("\n--- Interactive Web Scraper Mode ---")
        args.url = input("Enter Target Website URL: ").strip()
        while not args.url:
            print("URL is required.")
            args.url = input("Enter Target Website URL: ").strip()
            
        sd = input("Enter Start Date (YYYY-MM-DD) [Optional, press Enter to skip]: ").strip()
        if sd: args.start_date = sd
        
        ed = input("Enter End Date (YYYY-MM-DD) [Optional, press Enter to skip]: ").strip()
        if ed: args.end_date = ed
        
        mp = input("Enter Max Pages/Items [Default: 10]: ").strip()
        if mp.isdigit(): args.max_pages = int(mp)
        
        fmt = input("Enter Output Format (csv/xml/docx) [Default: csv]: ").strip().lower()
        if fmt in ["csv", "xml", "docx"]: args.format = fmt
        
        headed = input("Run in Headed Mode (visible browser)? (y/n) [Default: n]: ").strip().lower()
        if headed == 'y': args.headed = True

    print(f"\nStarting scrape of {args.url}")
    if args.start_date: print(f"Filter Start: {args.start_date}")
    if args.end_date: print(f"Filter End: {args.end_date}")
    
    crawler = Crawler()
    asyncio.run(crawler.run(
        args.url, 
        args.max_pages, 
        args.output, 
        args.format, 
        headless=not args.headed,
        start_date=args.start_date,
        end_date=args.end_date,
        categories=args.categories
    ))

if __name__ == "__main__":
    main()
