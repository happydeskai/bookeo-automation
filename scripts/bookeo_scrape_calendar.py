# File: scripts/bookeo_scrape_calendar.py

import os
import time
import pandas as pd
import gspread
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
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
    driver.find_element(By.ID, 'password').submit()

def go_to_calendar(driver):
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Calendar')))
    driver.find_element(By.LINK_TEXT, 'Calendar').click()
    WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID, 'outerBody')))

def scrape_calendar_data(driver):
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.fc-event')))
    class_elements = driver.find_elements(By.CSS_SELECTOR, 'div.fc-event')

    rows = []

    for class_element in class_elements:
        try:
            class_element.click()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.bookingInfo')))

            class_name = driver.find_element(By.CSS_SELECTOR, 'div.popupTitle').text.strip()
            date_time = driver.find_element(By.CSS_SELECTOR, 'div.popupSubTitle').text.strip()
            instructor = driver.find_element(By.CSS_SELECTOR, 'select[name="instrid"] option:checked').text.strip()

            booking_elements = driver.find_elements(By.CSS_SELECTOR, 'div.bookingInfo > table.details.card.clickable tbody tr td:nth-child(1)')

            for booking in booking_elements:
                customer_name = booking.text.strip()
                if customer_name:
                    rows.append({
                        "Class Name": class_name,
                        "Date": date_time,
                        "Instructor": instructor,
                        "Customer Name": customer_name
                    })

            driver.find_element(By.CSS_SELECTOR, 'button[title="Close"]').click()
            time.sleep(2)
        except Exception as e:
            driver.find_element(By.CSS_SELECTOR, 'button[title="Close"]').click()
            continue

    return pd.DataFrame(rows)

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

