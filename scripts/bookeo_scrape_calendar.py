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
    # Comment headless if you want to see browser
    # options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(options=options)
    return driver

def login(driver):
    username = os.environ.get("BOOKEO_USERNAME")
    password = os.environ.get("BOOKEO_PASSWORD")
    
    print("[+] Opening Bookeo login page...")
    driver.get(BOOKEO_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'username')))
    
    driver.find_element(By.NAME, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
    print("[✓] Logged in successfully.")

def go_to_calendar(driver):
    print("[+] Navigating to Calendar page...")
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@onclick, 'book_viewSchedules.html')]"))).click()
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'calendarBoxes')))
    time.sleep(2)
    print("[✓] Calendar page loaded.")

def click_class(driver, class_row, class_num):
    try:
        WebDriverWait(driver, 20).until(EC.invisibility_of_element_located((By.ID, "overlay_modal")))
        driver.execute_script("arguments[0].scrollIntoView(true);", class_row)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", class_row)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tab_esd_bookings")))
        print(f"[✓] Opened Class {class_num} popup.")
        return True
    except Exception as e:
        print(f"[!] Failed to open Class {class_num} popup on first try: {e}")
        driver.save_screenshot(f"fail_class_{class_num}.png")
        return False

def scrape_calendar_data(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    class_rows = driver.find_elements(By.XPATH, "//div[contains(@class,'eventSlotBox')]")
    if not class_rows:
        print("[!] No classes found.")
        return pd.DataFrame()

    print(f"[+] Found {len(class_rows)} classes to scrape.")

    for index, class_row in enumerate(class_rows, start=1):
        success = click_class(driver, class_row, index)
        if not success:
            print(f"[X] Skipping Class {index} due to popup issue.")
            continue

        try:
            class_info = driver.find_element(By.CLASS_NAME, "ui3boxTitle").text

            date_time_elem = driver.find_element(By.XPATH, "//div[@class='bookingInfo']//tr[td[contains(text(),'Date')]]/td[2]")
            date_time = date_time_elem.text if date_time_elem else "Unknown Date"

            instructor_elem = driver.find_element(By.XPATH, "//select[@id='instructor']/option[@selected]")
            instructor = instructor_elem.text.strip() if instructor_elem else "Unknown Instructor"

            customer_cards = driver.find_elements(By.CSS_SELECTOR, ".bookingInfo .detailsTitle2")

            if customer_cards:
                print(f"[✓] Found {len(customer_cards)} customers for Class {index}.")
            else:
                print(f"[!] No customers found for Class {index}.")

            for card in customer_cards:
                full_text = card.text.strip()
                name_parts = full_text.split(' ')[:2]
                customer_name = ' '.join(name_parts)
                results.append({
                    'Class Name': class_info.split(' - ')[0],
                    'Date': date_time,
                    'Instructor': instructor,
                    'Customer Name': customer_name
                })

        except Exception as e:
            print(f"[!] Error scraping Class {index}: {e}")
            driver.save_screenshot(f"fail_class_{index}_details.png")

        finally:
            try:
                close_button = driver.find_element(By.XPATH, "//div[@class='winTop']//img[contains(@onclick, 'closePopup')]")
                driver.execute_script("arguments[0].click();", close_button)
                time.sleep(1)
                print(f"[✓] Closed popup for Class {index}.")
            except Exception as close_error:
                print(f"[!] Failed to close popup for Class {index}: {close_error}")
                driver.save_screenshot(f"fail_close_class_{index}.png")
                continue

    return pd.DataFrame(results)

def save_to_google_sheet(df):
    print("[+] Saving results to Google Sheets...")
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
        print(f"[✓] Successfully saved {len(df)} rows to Google Sheet.")
    else:
        print("[!] No data scraped, skipping sheet update.")

def main():
    driver = create_browser()
    try:
        login(driver)
        go_to_calendar(driver)
        df = scrape_calendar_data(driver)
        save_to_google_sheet(df)
        print("[✓] DONE.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
