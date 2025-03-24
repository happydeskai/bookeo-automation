#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Date: 02/21/2024
    Author: Joshua David Golafshan
"""
import re

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.application_constants import GOOGLESHEETS_URL, SCRAPE_URL
from src.base_scraper import WebAutomation
from src.utils import *


class BookeoScraper(WebAutomation):
    def __init__(self, config):
        super().__init__(config)

    def login(self):
        """Logs into Bookeo."""
        self.get(SCRAPE_URL)
        self.wait_for_page_load()

        try:
            username_input = WebDriverWait(self, 10).until(
                EC.element_to_be_clickable((By.NAME, "username"))
            )
            username_input.clear()
            username_input.send_keys("s")
            username_input.clear()
            username_input.send_keys(self.config.get("bookeo", "username"))
            print("✅ Entered username.")

            password_input = WebDriverWait(self, 10).until(
                EC.element_to_be_clickable((By.ID, "password"))
            )
            password_input.clear()
            password_input.send_keys("s")
            password_input.clear()
            password_input.send_keys(self.config.get("bookeo", "password"))
            print("✅ Entered password and logged in.")

            self.send_key(By.ID, "password", Keys.RETURN)
            print("✅ Logged in.")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            quit()

    def go_to_calender_page(self):
        self.wait_for_page_load()
        try:
            self.click_button(By.XPATH, "//span[text()='Calendar']")
            print("✅ Clicked Calendar button.")
        except Exception as e:
            print(f"❌ Error: Unable to find Calendar button: {e}")
            quit()

    def extract_payments(self):
        self.click_button(By.XPATH, "//*[@title='Go back 14 days']")
        time.sleep(INTERMEDIATE_WAIT_TIME)
        data = []
        pattern = r"([A-Za-z]+(?:, [A-Za-z]+)?)\s+(\d{1,2} [A-Za-z]+ \d{4}, \d{1,2}:\d{2})"

        rows = self.find_elements(By.XPATH, "//tr[contains(@class, 'bookings') or contains(@class, 'fullWB')]")
        for booking in rows:
            provider_name = booking.find_element(By.CLASS_NAME, "ber_td_eprovider").text
            class_name = str(booking.find_element(By.CLASS_NAME, "ber_title").text).split(" - ")[0]
            booking.click()
            time.sleep(2)
            booking_info_divs = self.find_elements(By.CLASS_NAME, "bookingInfo")
            for booking_info in booking_info_divs:
                name_date = booking_info.find_element(By.CLASS_NAME, "title").text
                match = re.search(pattern, name_date)
                if match:
                    client_name = match.group(1)
                    class_time = match.group(2)
                    print(f"Name: {client_name}, Date: {class_time}")
                else:
                    continue

                when = booking_info.find_element(By.XPATH, ".//th[text()='When:']/following-sibling::td").text.strip()

                total_price_paid_due = booking_info.find_element(By.XPATH, ".//th[text()='Total price:']/following-sibling::td").text.strip()
                price_components = total_price_paid_due.split()
                total_price = str(price_components[0]).replace("£", "")
                total_paid = str(price_components[3]).replace("£", "")
                total_due = str(price_components[6]).replace("£", "")

                # Extract the "Booking number"
                booking_number = booking_info.find_element(By.XPATH, ".//th[text()='Booking number:']/following-sibling::td").text.strip()

                # Check if there is a "Promotion" field
                promotion = None
                try:
                    promotion = booking_info.find_element(By.XPATH,".//th[text()='Promotion:']/following-sibling::td").text.strip()
                except:
                    pass  # Promotion field does not exist for this booking

                data.append({
                    "Provider": provider_name,
                    "Class Name": class_name,
                    "Client Name": client_name,
                    "Class Time": class_time,
                    "Client Time": when,
                    "Total Price": total_price,
                    "Total Paid": total_paid,
                    "Total Due": total_due,
                    "Booking Number": booking_number,
                    "Promotion": promotion
                })

            self.find_element(By.CLASS_NAME, "icon-win_close").click()
        return data

    def extract_data(self):
        """Extracts data from the calendar page."""
        try:
            self.click_button(By.XPATH, "//span[text()='Print']")
            print("✅ Clicked Print button.")
        except Exception as e:
            print(f"❌ Error clicking 'Print' button: {e}")
            quit()

        time.sleep(INTERMEDIATE_WAIT_TIME)
        pyautogui.press('esc')  # Close print dialog
        print("✅ Print dialog closed successfully.")
        time.sleep(INTERMEDIATE_WAIT_TIME)
        # Copy data using system clipboard
        copy_to_clipboard()
        time.sleep(INTERMEDIATE_WAIT_TIME)

    def import_data_to_google_sheets(self):
        """Navigates to Google Sheets, creates a new sheet, and pastes clipboard data."""
        self.get(GOOGLESHEETS_URL)
        self.wait_for_page_load()

        try:
            pyautogui.press('esc')
            time.sleep(INTERMEDIATE_WAIT_TIME)
            clean_sheet()
            time.sleep(INTERMEDIATE_WAIT_TIME)
            paste_from_clipboard()

            time.sleep(INTERMEDIATE_WAIT_TIME)
            self.click_button(By.XPATH, "//*[contains(text(), 'Clean Class List')]")
            time.sleep(1)
            self.click_button(By.XPATH, "//*[contains(text(), 'Run Cleaning Script')]")

            # Sleep for 3 minutes lets the program run the script.
            time.sleep(180)

        except Exception as e:
            print(f"❌ Error pasting data into Google Sheets: {e}")
            quit()

    def import_payment_data_to_google_sheets(self):
        """Navigates to Google Sheets, creates a new sheet, and pastes clipboard data."""
        self.get(GOOGLESHEETS_URL)
        self.wait_for_page_load()

        try:
            pyautogui.press('esc')
            time.sleep(INTERMEDIATE_WAIT_TIME)
            self.click_button(By.XPATH, "//*[contains(text(), 'Payments Extracted')]")
            time.sleep(INTERMEDIATE_WAIT_TIME)
            clean_sheet()
            time.sleep(INTERMEDIATE_WAIT_TIME)
            paste_from_clipboard()
            time.sleep(10)
        except Exception as e:
            print(f"❌ Error pasting data into Google Sheets: {e}")
            quit()
