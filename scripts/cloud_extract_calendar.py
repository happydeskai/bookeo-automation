# File: scripts/cloud_extract_calendar.py

import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe

BOOKEO_URL = 'https://login.bookeo.com/'
GOOGLE_SHEET_NAME = 'Glowing Mamma Class Lists'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service_account.json'

def create_browser():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def login(driver):
    username = os.environ.get("BOOKEO_USERNAME")
    password = os.environ.get("BOOKEO_PASSWORD")

    driver.get(BOOKEO_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
    print("✅ Logged in")

def go_to_calendar(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Calendar']")))
    driver.find_element(By.XPATH, "//span[text()='Calendar']").click()
    print("✅ Reached calendar")

def scrape_calendar_data(driver):
    time.sleep(5)
    data = []
    rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'bookings') or contains(@class, 'fullWB')]")
    for row in rows:
        try:
            provider = row.find_element(By.CLASS_NAME, "ber_td_eprovider").text
            class_name = row.find_element(By.CLASS_NAME, "ber_title").text
            data.append({"Provider": provider, "Class Name": class_name})
        except Exception:
            continue
    df = pd.DataFrame(data)
    print(f"✅ Scraped {len(df)} entries")
    return df

def upload_to_google_sheets(df):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    sheet.clear()
    set_with_dataframe(sheet, df)
    print("✅ Uploaded to Google Sheets")

def main():
    driver = create_browser()
    try:
        login(driver)
        go_to_calendar(driver)
        df = scrape_calendar_data(driver)
        upload_to_google_sheets(df)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
