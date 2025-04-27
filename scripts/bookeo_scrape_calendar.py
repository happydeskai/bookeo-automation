def scrape_calendar_data(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    logging.info("Looking for class rows...")
    class_rows = driver.find_elements(By.XPATH, "//div[contains(@class,'eventSlotBox')]")
    logging.info(f"Found {len(class_rows)} classes.")

    if not class_rows:
        logging.warning("No classes found. Skipping scraping.")
        return pd.DataFrame()

    for idx, class_row in enumerate(class_rows):
        try:
            logging.info(f"Opening class {idx + 1} of {len(class_rows)}...")
            driver.execute_script("arguments[0].scrollIntoView(true);", class_row)
            class_row.click()
            time.sleep(2)

            driver.save_screenshot(f"debug_screenshots/class_{idx + 1}.png")

            logging.info("Waiting for booking tab to appear...")
            wait.until(EC.presence_of_element_located((By.ID, "tab_esd_bookings")))

            customer_cards = driver.find_elements(By.CSS_SELECTOR, ".bookingInfo .detailsTitle2")
            logging.info(f"Found {len(customer_cards)} customer cards.")

            class_info = driver.find_element(By.CLASS_NAME, "ui3boxTitle").text
            date_time = driver.find_element(By.XPATH, "//div[contains(@class,'bookingInfo')]/table//td").text
            instructor = driver.find_element(By.XPATH, "//select[@id='instructor']/option[@selected]").text.strip()

            for card in customer_cards:
                customer_name = card.text.strip()
                results.append({
                    'Class Name': class_info.split(' - ')[0],
                    'Date': date_time,
                    'Instructor': instructor,
                    'Customer Name': customer_name
                })

            logging.info(f"Scraped {len(customer_cards)} customers for this class.")

            close_button = driver.find_element(By.XPATH, "//div[@class='winTop']//img[contains(@onclick, 'closePopup')]")
            close_button.click()
            time.sleep(2)

        except Exception as e:
            logging.error(f"Failed scraping class {idx + 1}: {e}")
            driver.save_screenshot(f"debug_screenshots/error_class_{idx + 1}.png")
            continue

    logging.info(f"Scraping complete. Total records scraped: {len(results)}")
    return pd.DataFrame(results)


