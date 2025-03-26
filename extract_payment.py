import time
import pandas as pd
import pyperclip

from bookeo_scraper import BookeoScraper
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def extract_client_payments():
    web_scraper = BookeoScraper(config=config)
    web_scraper.login()
    web_scraper.go_to_calender_page()
    data = web_scraper.extract_payments()
    web_scraper.close_browser()

    print("✅ Extracted Payment Data")

    # Save Data
    df = pd.DataFrame(data)
    tsv_data = df.to_csv(index=False, sep='\t')
    pyperclip.copy(tsv_data)

    print("✅ Payment Data Copied into clipbroad")

    google_sheets = BookeoScraper(config=config)
    google_sheets.import_payment_data_to_google_sheets()

    print("✅ Payment Data Copied into PaymentSheet")

    google_sheets.close_browser()
    time.sleep(1)


if __name__ == "__main__":
    extract_client_payments()
