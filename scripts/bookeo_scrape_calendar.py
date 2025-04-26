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
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(options=options)
    return driver

def login(driver):
    driver.get(BOOKEO_URL)
    username = os.environ.get("BOOKEO_USERNAME")
    password = os.environ.get("BOOKEO_PASSWORD")
    
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'username')))
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)

def go_to_calendar(driver):
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@onclick, 'book_viewSchedules.html')]"))).click()
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'outerBody')))

def scrape_calendar_data(driver):
    class_rows = driver.find_elements(By.XPATH, "//div[@class='calendarBoxContentRow']")
    data = []
    
    for row in class_rows:
        try:
            driver.execute_script("arguments[0].scrollIntoView();", row)
            row.click()
            
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'contentPopup')))
            
            time.sleep(1)
            popup = driver.find_element(By.ID, 'contentPopup')

            class_name = popup.find_element(By.CLASS_NAME, 'detailsTitle2').text
            datetime = popup.find_element(By.XPATH, "//input[@name='date']").get_attribute('value')
            instructor = popup.find_element(By.XPATH, "//select[@name='instr']").get_attribute('value')

            try:
                customer_elements = popup.find_elements(By.XPATH, "//div[contains(@class, 'bookingInfo')]/div[@class='detailsTitle2']")
            except:
                customer_elements = []

            if customer_elements:
                for customer in customer_elements:
                    customer_name = customer.text.split()[0] + ' ' + customer.text.split()[1]
                    data.append({
                        "Class Name": class_name,
                        "Date": datetime,
                        "Instructor": instructor,
                        "Customer Name": customer_name
                    })
            driver.find_element(By.XPATH, "//div[@id='contentPopup']//button[contains(@class,'close')]").click()
            time.sleep(0.5)

        except Exception:
            driver.refresh()
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'outerBody')))
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
    if not df.empty:
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
