# File: scripts/cloud_extract_calendar.py

import os
import time
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

def go_to_calendar(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Calendar']")))
    driver.find_element(By.XPATH, "//span[text()='Calendar']").click()

def scrape_calendar_data(driver):
    time.sleep(5)
    data = [
        {"Date": "2025-05-01", "Event": "Sample Class 1"},
        {"Date": "2025-05-02", "Event": "Sample Class 2"},
    ]
    return pd.DataFrame(data)

def save_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    worksheet.clear()
    set_with_dataframe(worksheet, df)

def main():
    driver = create_browser()
    try:
        login(driver)
        go_to_calendar(driver)
        df = scrape_calendar_data(driver)
        save_to_google_sheet(df)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

