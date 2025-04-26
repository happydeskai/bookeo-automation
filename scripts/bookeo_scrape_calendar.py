# File: scripts/bookeo_scrape_calendar.py

import os
import time
import pandas as pd
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

# Constants
BOOKEO_URL = "https://signin.bookeo.com/"
GOOGLE_SHEET_NAME = "Glowing Mamma Class Lists"
SERVICE_ACCOUNT_JSON_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def create_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def login(driver):
    driver.get(BOOKEO_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(os.environ.get("BOOKEO_USERNAME"))
    driver.find_element(By.ID, "password").send_keys(os.environ.get("BOOKEO_PASSWORD"))
    driver.find_element(By.ID, "password").send_keys(Keys.RETURN)

def go_to_calendar(driver):
    calendar_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@onclick=\"open('book_viewSchedules.html')\"]"))
    )
    calendar_button.click()

    WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.ID, "outerBody"))
    )

def scrape_calendar_data(driver):
    time.sleep(5)  # optional, safer if slower loading
    class_rows = driver.find_elements(By.CSS_SELECTOR, "div.calendarRow")
    all_data = []

    for row in class_rows:
        try:
            row.click()

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#tab_esd_bookings .bookingInfo"))
            )

            booking_elements = driver.find_elements(By.CSS_SELECTOR, "div#tab_esd_bookings .bookingInfo")

            class_name = driver.find_element(By.CSS_SELECTOR, "div.ui3boxContent h2").text.split("-")[0].strip()
            date_time = driver.find_element(By.CSS_SELECTOR, "div.ui3boxContent h2").text.split("-")[-1].strip()
            instructor_element = driver.find_element(By.CSS_SELECTOR, "div.ui3boxContent select#teacherId option[selected]")
            instructor_name = instructor_element.text if instructor_element else ""

            for booking in booking_elements:
                customer_name = booking.find_element(By.CSS_SELECTOR, "div.detailsTitle2").text.strip()

                all_data.append({
                    "Class Name": class_name,
                    "Date": date_time,
                    "Instructor": instructor_name,
                    "Customer Name": customer_name
                })

            driver.find_element(By.XPATH, "//button[contains(@class, 'ui-dialog-titlebar-close')]").click()
        except Exception:
            driver.execute_script("window.history.go(-1)")
            time.sleep(3)

    return pd.DataFrame(all_data)

def save_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_JSON_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.worksheet("Clean Class List")
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
