def scrape_calendar_data(driver):
    results = []
    wait = WebDriverWait(driver, 30)

    class_rows = driver.find_elements(By.XPATH, "//div[contains(@class,'eventSlotBox')]")
    print(f"✅ Found {len(class_rows)} class rows.")  # <-- print classes found

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
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.worksheet("Clean Class List")
    worksheet.clear()
    if not df.empty:
        set_with_dataframe(worksheet, df)
        print("✅ Uploaded data to Google Sheet.")
    else:
        print("⚠️ No data to upload, sheet cleared only.")

