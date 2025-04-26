# File: scripts/bookeo_scrape_calendar.py

import os
import time
from datetime import datetime, timedelta
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

def create_browser():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')  # Updated headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return uc.Chrome(options=options)

def login(driver):
    username = os.environ.get("BOOKEO_USERNAME")
    password = os.environ.get("BOOKEO_PASSWORD")

    driver.get(BOOKEO_URL)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'username')))
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)

def go_to_calendar(driver):
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//span[text()='Calendar']"))
    )
    driver.find_element(By.XPATH, "//span[text()='Calendar']").click()

def scrape_calendar_data(driver):
    data = []
    today = datetime.now()
    two_weeks_later = today + timedelta(days=14)

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'calendarView')]"))
    )
    time.sleep(2)

    class_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'bookings')]")
    
    for row in class_rows:
        try:
            row.click()
            time.sleep(1)

            class_name = row.find_element(By.CLASS_NAME, "ber_title").text
            instructor = row.find_element(By.CLASS_NAME, "ber_td_eprovider").text
            date_time = row.find_element(By.CLASS_NAME, "ber_td_start").text

            customers = driver.find_elements(By.XPATH, "//tr[contains(@class, 'ber_booking')]//td[@class='booking_customer']")

            for customer in customers:
                customer_name = customer.text.strip()
                if customer_name:
                    data.append({
                        "Class Name": class_name,
                        "Date": date_time,
                        "Instructor": instructor,
                        "Customer Name": customer_name
                    })
            # Collapse after scraping (optional)
            row.click()
            time.sleep(0.5)

        except Exception:
            continue

    df = pd.DataFrame(data)
    return df

def save_to_google_sheet(df):
    service_account_info = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    import json
    credentials = Credentials.from_service_account_info(
        json.loads(service_account_info),
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.sheet1
    worksheet.clear()

    headers = ["Class Name", "Date", "Instructor", "Customer Name"]
    worksheet.append_row(headers)

    set_with_dataframe(worksheet, df, row=2, include_column_header=False)

    worksheet.format('1:1', {'textFormat': {'bold': True}})
    worksheet.freeze(rows=1)

def main():
    driver = create_browser()
    try:
        login(driver)
        go_to_calendar(driver)
        df = scrape_calendar_data(driver)
        if not df.empty:
            save_to_google_sheet(df)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()


