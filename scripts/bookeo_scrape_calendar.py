# file: /scripts/bookeo_scrape_calendar.py

import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from google.oauth2 import service_account
import gspread
import os

BOOKEO_USERNAME = os.getenv("BOOKEO_USERNAME")
BOOKEO_PASSWORD = os.getenv("BOOKEO_PASSWORD")
SERVICE_ACCOUNT_FILE = 'service_account.json'

SPREADSHEET_NAME = "Glowing Mamma Class Lists"
WORKSHEET_NAME = "Clean Class List"

def login_to_bookeo(driver):
    driver.get("https://signin.bookeo.com/login")

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(BOOKEO_USERNAME)
    driver.find_element(By.ID, "password").send_keys(BOOKEO_PASSWORD)
    driver.find_element(By.ID, "loginButton").click()

def go_to_calendar(driver):
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@onclick, 'open\\(\\'book_viewSchedules.html\\'\\)')]"))).click()

def scrape_class_list(driver):
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "calendarContent")))

    time.sleep(2)

    classes = driver.find_elements(By.CSS_SELECTOR, ".fc-event-container .fc-event")

    class_data = []
    actions = ActionChains(driver)

    for cls in classes:
        try:
            cls.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "contentLeftPopup")))

            class_name = driver.find_element(By.CSS_SELECTOR, "div.detailsTitle").text
            date = driver.find_element(By.CSS_SELECTOR, "div.bookingInfo span[style*='font-weight:bold']").text
            instructor = driver.find_element(By.CSS_SELECTOR, "div.bookingInfo select[name='instructor']").get_attribute("value")
            customer_elements = driver.find_elements(By.CSS_SELECTOR, "div.bookingDetailsList .detailsCardName")

            for customer in customer_elements:
                customer_name = customer.text.strip()
                class_data.append([class_name, date, instructor, customer_name])

            driver.find_element(By.XPATH, "//button[contains(text(), 'Cancel')]").click()

            time.sleep(1)

        except Exception as e:
            print(f"Failed to scrape class: {e}")
            driver.find_element(By.XPATH, "//button[contains(text(), 'Cancel')]").click()
            time.sleep(1)

    return class_data

def upload_to_google_sheets(data):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(SPREADSHEET_NAME)
    worksheet = sh.worksheet(WORKSHEET_NAME)

    worksheet.clear()
    worksheet.append_row(["Class Name", "Date", "Instructor", "Customer Name"])

    if data:
        worksheet.append_rows(data, value_input_option="RAW")

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    try:
        login_to_bookeo(driver)
        go_to_calendar(driver)
        class_data = scrape_class_list(driver)
        upload_to_google_sheets(class_data)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()


