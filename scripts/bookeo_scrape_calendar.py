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
    # options.add_argument('--headless')  # Comment out to see the browser window
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(options=options)
    return driver

def login(driver):
    username = os.environ.get("BOOKEO_USERNAME")
    password = os.environ.get("BOOKEO_PASSWORD")

    print("[+] Logging into Bookeo...")
    driver.get(BOOKEO_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'username')))
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
    print("[✓] Logged in.")

def go_to_calendar(driver):
    print("[+] Navigating to Calendar...")
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@onclick, 'book_viewSchedules.html')]"))).click()
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'calendarBoxes')))
    time.sleep(2)
    print("[✓] Calendar page ready.")

def scrape_calendar_data(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    print("[+] Finding classes...")
    class_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'bookings')]")
    if not class_rows:
        print("[!] No classes found.")
        return pd.DataFrame()

    print(f"[+] Found {len(class_rows)} classes.")

    for index, class_row in enumerate(class_rows, start=1):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", class_row)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", class_row)

            wait.until(EC.presence_of_element_located((By.ID, "tab_esd_bookings")))

            # Extract data from popup
            class_info = driver.find_element(By.CLASS_NAME, "ui3boxTitle").text
            date_time_elem = driver.find_element(By.XPATH, "//div[@class='bookingInfo']//tr[td[contains(text(),'Date')]]/td[2]")
            date_time = date_time_elem.text if date_time_elem else "Unknown Date"
            instructor_elem = driver.find_element(By.XPATH, "//select[@id='instructor']/option[@selected]")
            instructor = instructor_elem.text.strip() if instructor_elem else "Unknown Instructor"
            customer_cards = driver.find_elements(By.CSS_SELECTOR, ".bookingInfo .detailsTitle2")

            if not customer_cards:
                print(f"[!] No customers for Class {index}.")
            else:
                print(f"[✓] Scraping {len(customer_cards)} customers for Class {index}.")

            for card in customer_cards:
                customer_text = card.text.strip()
                name_parts = customer_text.split(' ')[:2]
                customer_name = ' '.join(name_parts)
                results.append({
                    'Class Name': class_info.split(' - ')[0],
                    'Date': date_time,
                    'Instructor': instructor,
                    'Customer Name': customer_name
                })

        except Exception as e:
            print(f"[!] Error scraping Class {index}: {e}")
            driver.save_screenshot(f"error_class_{index}.png")

        finally:
            # Always close the popup
            try:
                close_button = driver.find_element(By.XPATH, "//div[@class='winTop']//img[contains(@onclick, 'closePopup')]")
                driver.execute_script("arguments[0].click();", close_button)
                time.sleep(1)
                print(f"[✓] Closed popup for Class {index}.")
            except Exception as close_err:
                print(f"[!] Failed to close popup for Class {index}: {close_err}")
                driver.save_screenshot(f"error_close_class_{index}.png")
                continue

    return pd.DataFrame(results)

def save_to_google_sheet(df):
    print("[+] Uploading data to Google Sheet...")
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
        print(f"[✓] Uploaded {len(df)} rows to sheet.")
    else:
        print("[!] No data to upload.")

def main():
    driver = create_browser()
    try:
        login(driver)
        go_to_calendar(driver)
        df = scrape_calendar_data(driver)
        save_to_google_sheet(df)
        print("[✓] Done.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

