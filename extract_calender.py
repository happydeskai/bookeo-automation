import time
import pandas as pd
import pyperclip

import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def extract_calender():
    web_scraper = BookeoScraper(config=config)
    web_scraper.login()
    web_scraper.go_to_calender_page()
    web_scraper.extract_data()
    web_scraper.close_browser()

    google_sheets = BookeoScraper(config=config)
    google_sheets.import_data_to_google_sheets()

    print("✅ Added extracted data to Google Sheets")

    google_sheets.close_browser()
    time.sleep(1)


if __name__ == "__main__":
    extract_calender()
