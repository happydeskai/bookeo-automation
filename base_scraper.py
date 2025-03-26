#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Date: 02/21/2024
    Author: Joshua David Golafshan
"""

import logging
from typing import Optional, Any
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

from src.application_constants import MAX_WAIT_TIME


class WebAutomation(uc.Chrome):
    def __init__(self, config):
        self.config = config
        chrome_profile_name = self.config.get('chrome_profile', 'profile_name')
        chrome_profile_directory = self.config.get('chrome_profile', 'profile_directory')
        self.service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        if chrome_profile_name and chrome_profile_directory:
            chrome_options.add_argument(f"--user-data-dir={chrome_profile_name}")
            chrome_options.add_argument(f"--profile-directory={chrome_profile_directory}")

        super(WebAutomation, self).__init__(service=self.service, options=chrome_options)
        self.wait = WebDriverWait(self, MAX_WAIT_TIME)
        self.maximize_window()

    def close_browser(self):
        """Closes the browser session safely."""
        if self:
            try:
                self.quit()
                print("🚪 Browser session closed.")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")

    def wait_for_page_load(self):
        """Waits until the page is fully loaded."""
        try:
            WebDriverWait(self, MAX_WAIT_TIME).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            print(f"⚠️ Page load timeout: {e}")

    def open_page(self, url: str):
        try:
            self.get(url)
            logging.info(f"successfully open url {url}")
        except Exception as e:
            logging.error(f"Failed to load {url}: {e}")
            raise

    def select_option_by_text(self, by_type, element: str, option_text: str):
        try:
            # Wait for the select element to be clickable
            select_element = self.wait.until(EC.element_to_be_clickable((by_type, element)))
            logging.info(f"Found select element: {element}")

            # Create a Select object to interact with the dropdown
            select = Select(select_element)

            # Select the option by visible text
            select.select_by_visible_text(option_text)
            logging.info(f"Selected option: {option_text}")

        except Exception as e:
            logging.error(f"Failed to select option '{option_text}' in element '{element}': {e}")
            raise

    def select_option_by_index(self, by_type, element: str, option_index: int):
        try:
            # Wait for the select element to be clickable
            select_element = self.wait.until(EC.element_to_be_clickable((by_type, element)))
            logging.info(f"Found select element: {element}")

            # Create a Select object to interact with the dropdown
            select = Select(select_element)
            for index, option in enumerate(select.options):
                print(index, option.text)

            # Select the option by visible text
            select.select_by_index(option_index)
            logging.info(f"Selected option: {option_index}")

        except Exception as e:
            logging.error(f"Failed to select option '{option_index}' in element '{element}': {e}")
            raise

    def click_button(self, by_type, element):
        try:
            actions = ActionChains(self)
            button = self.wait.until(EC.element_to_be_clickable((by_type, element)))
            actions.move_to_element(button).click().perform()
            logging.info(f"Clicked button {element}")
        except Exception as e:
            logging.error(f"Failed to clicked '{element}': {e}")
            raise

    def send_key(self, by_type, element: str, key_text: str):
        try:
            label = self.wait.until(EC.element_to_be_clickable((by_type, element)))
            label.send_keys(key_text)
            logging.info(f"Entered text '{key_text}' in field: {element}")
        except Exception as e:
            logging.error(f"Failed to send key to '{element}': {e}")
            raise

    def click_element_with_text(self, text) -> Optional[Any]:
        try:
            button = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{text}')]")))
            logging.info(f"Clicked element containing text: {text}")
            return button
        except Exception as e:
            logging.error(f"Failed to click element containing text '{text}': {e}")
            return None
