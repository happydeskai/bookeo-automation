# File: scripts/bookeo_scrape_calendar.py

import os
import time
import pandas as pd
import pyperclip
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from pynput.keyboard import Controller, Key

BOOKEO_URL = 'https://signin.bookeo.com/'
GOOGLE_SHEET_NAME = 'Glowing Mamma Class Lists'
SERVICE_ACCOUNT_JSON_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def create_browser():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Do NOT headless - we want browser window open for clipboard
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
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@onclick, 'book_viewSchedules.html')]"))).click()
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'calendarBoxes')))
    time.sleep(2)

def copy_calendar_data(driver):
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Print']"))).click()
    time.sleep(3)
    
    keyboard = Controller()

    # Cancel Print popup
    keyboard.press(Key.esc)
    keyboard.release(Key.esc)
    time.sleep(2)

    # Select all text
    keyboard.press(Key.ctrl)
    keyboard.press('a')
    keyboard.release('a')
    keyboard.release(Key.ctrl)
    time.sleep(1)

    # Copy to clipboard
    keyboard.press(Key.ctrl)
    keyboard.press('c')
    keyboard.release('c')
    keyboard.release(Key.ctrl)
    time.sleep(2)

def parse_calendar_data():
    content = pyperclip.paste()
    if not content:
        raise Exception("Clipboard is empty. Nothing copied from calendar page!")

    lines = content.split("\n")
    data = []

    current_class = ""
    current_instructor = ""
    current_datetime = ""

    for line in lines:
        if "Instructor:" in line:
            current_instructor = line.replace("Instructor:", "").strip()
        elif "-" in line and ":" in line:
            current_datetime = line.strip()
        elif line.strip() and "Instructor:" not in line and ":" not in line:
            customer_name = line.strip()
            if customer_name and current_class:
                data.append({
                    "Class Name": current_class,
                    "Date": current_datetime,
                    "Instructor": current_instructor,
                    "Customer Name": customer_name
                })
        elif line.strip():
            current_class = line.strip()

    return pd.DataFrame(data)

def save_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON_FILE, scopes=SCOPES)
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
        copy_calendar_data(driver)
        df = parse_calendar_data()
        save_to_google_sheet(df)
        print(f"✅ Done. Scraped {len(df)} rows.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
