# File: scripts/bookeo_scrape_calendar.py

import os
import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2.service_account import Credentials
import gspread
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
    return uc.Chrome(options=options)

def login(driver):
    username = os.environ.get("BOOKEO_USERNAME")
    password = os.environ.get("BOOKEO_PASSWORD")
    driver.get(BOOKEO_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'username')))
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@onclick, 'book_viewSchedules.html')]")))

def go_to_calendar(driver):
    driver.find_element(By.XPATH, "//div[contains(@onclick, 'book_viewSchedules.html')]").click()
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'calendarBoxes')))
    time.sleep(2)

def scrape_classes(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    classes = driver.find_elements(By.CSS_SELECTOR, ".bookeoScheduleEventBox")
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

def upload_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_JSON_FILE, scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.worksheet("RawData")  # You can change to Clean Class List if preferred
    worksheet.clear()
    if not df.empty:
        set_with_dataframe(worksheet, df)

def main():
    driver = create_browser()
    try:
        login(driver)
        go_to_calendar(driver)
        data = scrape_classes(driver)
        upload_to_google_sheet(data)
        print(f"✅ Scraped {len(data)} records and updated Google Sheet.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

