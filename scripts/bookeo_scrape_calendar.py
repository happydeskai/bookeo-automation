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
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
SERVICE_ACCOUNT_JSON_FILE = 'service_account.json'

def create_browser():
    options = uc.ChromeOptions()
    # options.add_argument('--headless')  # DEBUG: leave visual
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
    print("✅ Logged in.")

def go_to_calendar(driver):
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='Calendar']"))
    ).click()
    print("✅ Clicked Calendar.")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'calendarBoxes')))
    time.sleep(2)

def scrape_calendar_data(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'bookings') or contains(@class, 'fullWB')]")
    print(f"✅ Found {len(rows)} classes.")

    for idx, row in enumerate(rows):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", row)
            clickable_td = row.find_element(By.TAG_NAME, "td")
            clickable_td.click()
            print(f"✅ Opened class {idx+1} popup.")
            time.sleep(2)

            wait.until(EC.presence_of_element_located((By.ID, "tab_esd_bookings")))
            booking_popup = driver.find_element(By.ID, "tab_esd_bookings")

            class_name = driver.find_element(By.CLASS_NAME, "ui3boxTitle").text.split(' - ')[0]
            date_time = booking_popup.find_element(By.XPATH, ".//th[text()='When:']/following-sibling::td").text.strip()
            instructor = booking_popup.find_element(By.XPATH, ".//th[text()='Instructor:']/following-sibling::td").text.strip()

            customers = booking_popup.find_elements(By.CLASS_NAME, "_title")
            for customer in customers:
                customer_name = customer.text.strip()
                if customer_name:
                    results.append({
                        'Class Name': class_name,
                        'Date': date_time,
                        'Instructor': instructor,
                        'Customer Name': customer_name
                    })

            close_button = driver.find_element(By.XPATH, "//div[@class='winTop']//img[contains(@onclick, 'closePopup')]")
            close_button.click()
            print(f"✅ Closed class {idx+1} popup.")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Failed at class {idx+1}: {e}")
            continue

    print(f"✅ Scraped {len(results)} customer entries.")
    return pd.DataFrame(results)

def save_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_JSON_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.worksheet("Clean Class List")
    worksheet.clear()
    print("✅ Cleared Clean Class List sheet.")
    if not df.empty:
        set_with_dataframe(worksheet, df)
        print("✅ Uploaded data.")
    else:
        print("⚠️ No data to upload.")

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
