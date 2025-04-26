# File: scripts/bookeo_scrape_calendar.py

import os
import time
import json
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
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
SERVICE_ACCOUNT_JSON_FILE = 'service_account.json'

def create_browser():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
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
    calendar_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Calendar']"))
    )
    calendar_button.click()

    WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.ID, "outerBody"))
    )

def scrape_calendar_data(driver):
    time.sleep(5)
    rows = driver.find_elements(By.CSS_SELECTOR, ".classRow")
    all_data = []

    for row in rows:
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", row)
            row.click()

            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "table.details.card.clickable"))
            )

            class_name_element = driver.find_element(By.CSS_SELECTOR, ".bookingInfo > .detailsTitle2")
            class_name = class_name_element.text.strip().split('\n')[0]

            table = driver.find_element(By.CSS_SELECTOR, "table.details.card.clickable")
            rows_in_popup = table.find_elements(By.TAG_NAME, "tr")

            for tr in rows_in_popup:
                try:
                    customer_name = tr.text.split('  ')[0].strip()
                    if customer_name:
                        all_data.append({
                            "Class Name": class_name,
                            "Date": class_name.split('-')[-1].strip(),  # Extract date from title
                            "Instructor": "",  # Optional: you can extend later
                            "Customer Name": customer_name
                        })
                except Exception:
                    continue

            driver.find_element(By.XPATH, "//button[contains(text(),'Cancel')]").click()
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.details.card.clickable"))
            )

        except Exception:
            continue

    return pd.DataFrame(all_data)

def save_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_JSON_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.worksheet('Clean Class List')
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

