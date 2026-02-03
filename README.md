# Web Scraper Setup Guide

To run this web scraper on another computer, you need to set up the Python environment and install the necessary dependencies.

## Prerequisites

1.  **Install Python**: Ensure Python 3.8 or newer is installed. You can download it from [python.org](https://www.python.org/).
2.  **Terminal/Command Prompt**: You will need to run commands in a terminal (Command Prompt, PowerShell, or Terminal on macOS/Linux).

## Installation Steps

1.  **Copy the Project**: Copy the entire project folder to the new computer.
2.  **Navigate to the Folder**: Open your terminal and change directory (`cd`) into the project folder.
    ```bash
    cd "path/to/project_folder"
    ```
3.  **Install Dependencies**: Run the following command to install the required Python libraries.
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install Browsers**: `playwright` requires browser binaries to be installed. Run:
    ```bash
    playwright install
    ```

## Usage

Once installed, you can run the scraper using `python main.py`.

### Example Command
```bash
python main.py "https://www.bbc.com/news/world/asia" --max_pages 12 --format docx --headed --start_date "2026-01-01" --end_date "2026-01-21" --categories news
```

### Arguments
- `URL`: Target website URL.
- `--max_pages`: Limit number of items to scrape.
- `--format`: Output format (`csv`, `docx`, `xml`).
- `--headed`: Show browser window (useful for debugging).
- `--start_date` / `--end_date`: Filter by date.
- `--categories`: Filter by URL category path keywords.
