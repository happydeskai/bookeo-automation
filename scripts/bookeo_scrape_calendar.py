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
SERVICE_ACCOUNT_JSON_FILE = 'service_account.json'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

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
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'username')))
        driver.find_element(By.NAME, 'username').send_keys(username)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
    except Exception as e:
        with open("page_error.html", "w") as f:
            f.write(driver.page_source)
        raise Exception(f"Login failed: {e}")

def go_to_calendar(driver):
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.LINK_TEXT, 'Calendar')))
    driver.find_element(By.LINK_TEXT, 'Calendar').click()
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'groupClasses')]"))
    )

def scrape_calendar_data(driver):
    time.sleep(5)  # wait calendar fully loaded
    classes = driver.find_elements(By.CSS_SELECTOR, "div.groupClasses > div > div")
    data = []

    for cls in classes:
        try:
            # Click on the class (not the plus button)
            cls.click()
            time.sleep(2)

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".bookingInfo"))
            )

            class_name_elem = driver.find_element(By.CSS_SELECTOR, "div.ui-dialog-title")
            class_name = class_name_elem.text.split('(')[0].strip()

            date_elem = driver.find_element(By.CSS_SELECTOR, "div.bookingInfo td")
            date_text = date_elem.text

            instructor_elem = driver.find_element(By.NAME, "instructor")
            instructor = instructor_elem.get_attribute('value')

            customers = driver.find_elements(By.CSS_SELECTOR, "div.detailsTitle2")

            for customer in customers:
                data.append({
                    "Class Name": class_name,
                    "Date": date_text,
                    "Instructor": instructor,
                    "Customer Name": customer.text.strip()
                })

            # Close the popup
            driver.find_element(By.CSS_SELECTOR, "button.ui-dialog-titlebar-close").click()
            time.sleep(1)

        except Exception as e:
            print(f"Error scraping a class: {e}")
            driver.find_element(By.CSS_SELECTOR, "button.ui-dialog-titlebar-close").click()
            time.sleep(1)
            continue

    return pd.DataFrame(data)

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

