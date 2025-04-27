# File: scripts/bookeo_scrape_calendar.py

import os
import time
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import gspread
from google.oauth2 import service_account

from undetected_chromedriver import Chrome, ChromeOptions

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def login_bookeo(driver):
    logging.info("Logging into Bookeo...")
    driver.get("https://signin.bookeo.com/login")
    time.sleep(1)  # slight breathing room

    username = os.getenv('BOOKEO_USERNAME')
    password = os.getenv('BOOKEO_PASSWORD')

    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "login")))
        driver.find_element(By.NAME, "login").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "submit").click()
        logging.info("Login submitted successfully.")
    except Exception as e:
        logging.error(f"Login failed: {e}")
        driver.save_screenshot('login_error.png')
        raise

def go_to_calendar(driver):
    logging.info("Navigating to Calendar page...")
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Calendar']"))).click()

def scrape_calendar_data(driver):
    logging.info("Waiting for classes to load...")
    WebDriverWait(driver, 40).until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'eventSlotBox')]")))
    time.sleep(2)  # Let it fully load

    classes = driver.find_elements(By.XPATH, "//div[contains(@class, 'eventSlotBox')]")
    logging.info(f"Found {len(classes)} classes")

    records = []

    for idx, class_element in enumerate(classes):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", class_element)
            time.sleep(0.5)
            class_element.click()
            logging.info(f"Clicked class {idx + 1}")

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "bookingInfo")))

            # Extract data
            class_name = driver.find_element(By.CLASS_NAME, "ui3boxTitle").text
            instructor = driver.find_element(By.XPATH, "//select[@name='instructor']/option[@selected]").text
            time_text = driver.find_element(By.XPATH, "//input[@name='time']").get_attribute("value")
            date_text = driver.find_element(By.XPATH, "//input[@name='date']").get_attribute("value")

            customers = driver.find_elements(By.CSS_SELECTOR, ".bookingInfo .detailsTitle2")

            for customer in customers:
                customer_name = customer.text.strip()
                records.append([
                    class_name,
                    f"{date_text} {time_text}",
                    instructor,
                    customer_name
                ])

            # Close popup
            close_button = driver.find_element(By.XPATH, "//div[@class='winTop']//img[contains(@onclick, 'closePopup')]")
            close_button.click()

            time.sleep(0.5)

        except Exception as e:
            logging.error(f"Failed to scrape class {idx + 1}: {str(e)}")
            continue

    return records

def upload_to_sheet(records):
    logging.info("Uploading to Google Sheets...")
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_file("service_account.json", scopes=scopes)

    gc = gspread.authorize(creds)

    spreadsheet = gc.open("Glowing Mamma Class Lists")
    worksheet = spreadsheet.worksheet("Clean Class List")

    worksheet.clear()
    worksheet.append_row(["Class Name", "Date", "Instructor", "Customer Name"])

    for row in records:
        worksheet.append_row(row)

    logging.info(f"✅ Uploaded {len(records)} rows successfully!")

def main():
    options = ChromeOptions()
    options.add_argument('--headless=new')  # running in background
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = Chrome(options=options)

    try:
        login_bookeo(driver)
        go_to_calendar(driver)
        records = scrape_calendar_data(driver)

        if records:
            upload_to_sheet(records)
        else:
            logging.warning("No records found to upload.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()


