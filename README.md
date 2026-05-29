# Invoice Web Scraper

A Python-based scraper designed to extract invoice and 
tracking information for workflow automation.

## Features
- Extracts invoice data automatically
- Tracks order/shipment information
- Designed for workflow automation pipelines

## Skills Used
- Python
- Web Scraping
- Data Processing
- Workflow Automation

## How to Run
1. Clone this repo
2. Install dependencies: `pip install requests beautifulsoup4`
3. Run: `python scraper.py`
## Setup
1. Copy `config.example.py` to `config.py`
2. Fill in your portal credentials and CSS selectors
3. Generate a Gmail App Password at: myaccount.google.com/apppasswords
4. Install dependencies:
pip install requests beautifulsoup4 selenium webdriver-manager pyperclip
5. Run: `python scraper.py`

## Security Note
`config.py` is listed in `.gitignore` and will never be 
uploaded to GitHub. Only `config.example.py` is shared 
as a safe template.
