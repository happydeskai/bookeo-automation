import time
import os
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

# Constants
SERVICE_ACCOUNT_JSON_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# We connect directly by your Google Sheet ID
GOOGLE_SHEET_ID = '1CKfwa1o9AGf-7mQibkVELa9JBDy-a3c1XHC7hXr-d7Q'
GOOGLE_SHEET_TAB = 'Clean Class List'

BOOKEO_LOGIN_URL = 'https://signin.bookeo.com/login'
BOOKEO_USERNAME = os.getenv('BOOKEO_USERNAME')
BOOKEO_PASSWORD = os.getenv('BOOKEO_PASSWORD')

def create_driver():
    options = uc.ChromeOptions()
    options.headless = True  # run in background
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    return driver

def login_to_bookeo(driver):
    driver.get(BOOKEO_LOGIN_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "login_user_username")))
    
    driver.find_element(By.ID, "login_user_username").send_keys(BOOKEO_USERNAME)
    driver.find_element(By.ID, "login_user_password").send_keys(BOOKEO_PASSWORD)
    driver.find_element(By.NAME, "login_user_login").click()
    
    # Wait for dashboard to load
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "dashboard")))

def scrape_calendar_data(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    # Navigate to bookings calendar
    driver.get('https://signin.bookeo.com/bookings')

    class_rows = driver.find_elements(By.XPATH, "//div[contains(@class,'eventSlotBox')]")
    print(f"✅ Found {len(class_rows)} class rows.")

    if not class_rows:
        print("⚠️ No classes found, exiting.")
        return pd.DataFrame()

    for idx, class_row in enumerate(class_rows):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", class_row)
            class_row.click()
            print(f"➡️  Opened class {idx+1}")
            time.sleep(2)

            wait.until(EC.presence_of_element_located((By.ID, "tab_esd_bookings")))
            customer_cards = driver.find_elements(By.CSS_SELECTOR, ".bookingInfo .detailsTitle2")
            print(f"👥 Found {len(customer_cards)} customers in class {idx+1}")

            class_info = driver.find_element(By.CLASS_NAME, "ui3boxTitle").text
            date_time = driver.find_element(By.XPATH, "//div[contains(@class,'bookingInfo')]/table//td").text
            instructor = driver.find_element(By.XPATH, "//select[@id='instructor']/option[@selected]").text.strip()

            for card in customer_cards:
                customer_name = card.text.strip().split(' ')[0] + " " + card.text.strip().split(' ')[1]
                results.append({
                    'Class Name': class_info.split(' - ')[0],
                    'Date': date_time,
                    'Instructor': instructor,
                    'Customer Name': customer_name
                })

            close_button = driver.find_element(By.XPATH, "//div[@class='winTop']//img[contains(@onclick, 'closePopup')]")
            close_button.click()
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error in class {idx+1}: {e}")
            continue

    print(f"✅ Total records scraped: {len(results)}")
    return pd.DataFrame(results)

def save_to_google_sheet(df):
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_JSON_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    worksheet = sh.worksheet(GOOGLE_SHEET_TAB)
    worksheet.clear()

    if not df.empty:
        set_with_dataframe(worksheet, df)
        print("✅ Uploaded data to Google Sheet.")
    else:
        print("⚠️ No data to upload, sheet cleared only.")

if __name__ == "__main__":
    driver = create_driver()
    try:
        login_to_bookeo(driver)
        df = scrape_calendar_data(driver)
        save_to_google_sheet(df)
    except Exception as e:
        print(f"❌ Script error: {e}")
        driver.save_screenshot('error_screenshot.png')
        raise
    finally:
        driver.quit()

