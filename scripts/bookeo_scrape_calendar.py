# File: scripts/bookeo_scrape_calendar.py

import os
import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe

BOOKEO_URL = 'https://signin.bookeo.com/'
GOOGLE_SHEET_NAME = 'Glowing Mamma Class Lists'
SHEET_TAB_NAME = 'RawData'  # <-- saving into RawData tab
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
SERVICE_ACCOUNT_JSON_FILE = 'service_account.json'

def create_browser():
    options = uc.ChromeOptions()
    options.add_argument('--headless')  # headless to run quietly
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(options=options)
    return driver

def login(driver):
    username = os.environ.get("BOOKEO_USERNAME")
    password = os.environ.get("BOOKEO_PASSWORD")
    
    driver.get(BOOKEO_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'username')))
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)

def go_to_calendar(driver):
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@onclick, 'book_viewSchedules.html')]"))).click()
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'calendarBoxes')))
    time.sleep(2)

def scrape_classes(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    classes = driver.find_elements(By.XPATH, "//div[contains(@class, 'eventSlotBox')]")
    print(f"Found {len(classes)} classes.")

    for event in classes:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", event)
            event.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tab_esd_bookings")))
            time.sleep(1)

            title = driver.find_element(By.CLASS_NAME, "ui3boxTitle").text
            date_time = driver.find_element(By.XPATH, "//div[contains(@class,'bookingInfo')]/table//td").text
            instructor = driver.find_element(By.XPATH, "//select[@id='instructor']/option[@selected]").text.strip()

            customers = driver.find_elements(By.CSS_SELECTOR, ".bookingInfo .detailsTitle2")
            for cust in customers:
                name = cust.text.strip()
                results.append({
                    'Class Name': title.split(' - ')[0],
                    'Date': date_time,
                    'Instructor': instructor,
                    'Customer Name': name
                })

            close_btn = driver.find_element(By.XPATH, "//div[@class='winTop']//img[contains(@onclick, 'closePopup')]")
            close_btn.click()
            time.sleep(1)
        except Exception as e:
            print(f"Failed extracting class: {e}")
            continue

    return pd.DataFrame(results)

def save_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_JSON_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.worksheet(SHEET_TAB_NAME)
    worksheet.clear()
    if not df.empty:
        set_with_dataframe(worksheet, df)

def main():
    driver = create_browser()
    try:
        print("[+] Opening Bookeo login page...")
        login(driver)
        print("[+] Logged in successfully.")

        print("[+] Navigating to Calendar page...")
        go_to_calendar(driver)
        print("[+] Calendar page loaded.")

        df = scrape_classes(driver)

        print("[+] Saving results to Google Sheets...")
        save_to_google_sheet(df)

        print(f"[+] Done. Scraped {len(df)} records.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()


