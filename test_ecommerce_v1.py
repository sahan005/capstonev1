"""
Capstone Milestone 1 (V1) - E-Commerce Test Automation Script
Automated tests for OpenCart demo storefront using Selenium WebDriver.
"""

import os
import sys
import time
import re
import logging
from datetime import datetime
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager

# Paths (resilient to root or capstone_v1 execution)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(BASE_DIR) == "capstone_v1":
    SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
    REPORTS_DIR = os.path.join(BASE_DIR, "reports")
    DATA_DIR = os.path.join(BASE_DIR, "test_data")
    UTILS_DIR = os.path.join(BASE_DIR, "utils")
else:
    SCREENSHOTS_DIR = os.path.join(BASE_DIR, "capstone_v1", "screenshots")
    REPORTS_DIR = os.path.join(BASE_DIR, "capstone_v1", "reports")
    DATA_DIR = os.path.join(BASE_DIR, "capstone_v1", "test_data")
    UTILS_DIR = os.path.join(BASE_DIR, "capstone_v1", "utils")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Add utils directory to sys.path
if UTILS_DIR not in sys.path:
    sys.path.insert(0, os.path.dirname(UTILS_DIR))
    sys.path.insert(0, UTILS_DIR)

from utils.data_reader import get_test_data, persist_user_credentials

# Setup logging
LOG_FILE = os.path.join(REPORTS_DIR, "test_execution.log")
logger = logging.getLogger("EcommerceV1")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)


# STEP 7: Capture screenshots
def take_screenshot(driver, step_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{step_name}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    driver.save_screenshot(filepath)
    logger.info(f"Screenshot captured: {filename}")
    return filepath


# STEP 9: Handle popups / alerts defensively
def handle_popups_and_alerts(driver):
    # Handle JS alert
    try:
        alert = driver.switch_to.alert
        logger.info(f"Dismissing JS alert: {alert.text}")
        alert.accept()
    except NoAlertPresentException:
        pass

    # Handle cookie banners or modal close buttons
    close_selectors = [
        "//button[contains(text(), 'Accept') or contains(text(), 'Agree')]",
        "//button[@class='close' and @data-dismiss='modal']",
        "//div[contains(@class,'cookie')]//button"
    ]
    for xpath in close_selectors:
        try:
            btn = driver.find_element(By.XPATH, xpath)
            if btn.is_displayed():
                btn.click()
                logger.info(f"Dismissed popup/banner: {xpath}")
                break
        except Exception:
            continue


def parse_price(price_str):
    cleaned = re.sub(r"[^\d.]", "", price_str)
    return float(cleaned) if cleaned else 0.0


# STEP 1: Launch browser — Chrome via webdriver-manager
@pytest.fixture(scope="function")
def driver():
    logger.info("STEP 1: Launching Chrome browser...")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=options)
    browser.implicitly_wait(5)
    
    yield browser

    logger.info("Closing browser...")
    browser.quit()


def test_ecommerce_flow(driver):
    wait = WebDriverWait(driver, 10)

    # STEP 8: Read test data from Excel / JSON
    logger.info("STEP 8: Reading test data from file...")
    data = get_test_data(source_type="json", base_dir=DATA_DIR)
    base_url = data.get("base_url", "https://tutorialsninja.com/demo/")
    user = data["user"]
    product = data["product"]
    target_qty = int(product["target_quantity"])
    logger.info(f"Test Data: Product='{product['product_name']}', Qty={target_qty}, Email='{user['email']}'")

    # Navigate to site
    driver.get(base_url)
    handle_popups_and_alerts(driver)
    time.sleep(1.5)  # Visual pause: storefront loaded

    # STEP 2: Login (Register first if no test account exists yet)
    logger.info("STEP 2: My Account -> Login / Register...")
    account_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='My Account']")))
    account_menu.click()
    time.sleep(1.0)

    if not user.get("is_registered", False):
        logger.info("No existing account found. Registering new account...")
        register_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Register']")))
        register_link.click()

        reg_email = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        wait.until(EC.visibility_of_element_located((By.ID, "input-firstname"))).send_keys(user["first_name"])
        driver.find_element(By.ID, "input-lastname").send_keys(user["last_name"])
        driver.find_element(By.ID, "input-email").send_keys(reg_email)
        driver.find_element(By.ID, "input-telephone").send_keys(user["telephone"])
        driver.find_element(By.ID, "input-password").send_keys(user["password"])
        driver.find_element(By.ID, "input-confirm").send_keys(user["password"])

        agree_box = driver.find_element(By.NAME, "agree")
        if not agree_box.is_selected():
            agree_box.click()

        driver.find_element(By.XPATH, "//input[@value='Continue']").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(),'Your Account Has Been Created!')]")))
        time.sleep(1.5)

        user["email"] = reg_email
        user["is_registered"] = True
        persist_user_credentials(user, base_dir=DATA_DIR)
        logger.info(f"Registered and saved new user: {reg_email}")

        # Logout then login
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='My Account']"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Logout']"))).click()
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(),'Account Logout')]")))
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='My Account']"))).click()

    # Log in
    logger.info(f"Logging in as {user['email']}...")
    login_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Login']")))
    login_link.click()

    email_field = wait.until(EC.visibility_of_element_located((By.ID, "input-email")))
    email_field.clear()
    email_field.send_keys(user["email"])
    pwd_field = driver.find_element(By.ID, "input-password")
    pwd_field.clear()
    pwd_field.send_keys(user["password"])
    driver.find_element(By.XPATH, "//input[@value='Login']").click()

    wait.until(EC.visibility_of_element_located((By.XPATH, "//h2[text()='My Account']")))
    logger.info("Login verified successfully.")
    take_screenshot(driver, "post_login")
    time.sleep(1.5)  # Visual pause: logged-in account dashboard

    # STEP 3: Search product
    logger.info(f"STEP 3: Searching for '{product['search_term']}'...")
    search_bar = wait.until(EC.visibility_of_element_located((By.NAME, "search")))
    search_bar.clear()
    search_bar.send_keys(product["search_term"], Keys.ENTER)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-layout")))
    logger.info("Search results displayed.")
    take_screenshot(driver, "post_search")
    time.sleep(1.5)  # Visual pause: search results page

    # STEP 4: Add product to cart
    logger.info(f"STEP 4: Opening product '{product['product_name']}'...")
    product_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//div[contains(@class,'product-layout')]//h4/a[contains(text(),'{product['product_name']}')]")
    ))
    product_link.click()
    time.sleep(1.5)  # Visual pause: product details page

    add_btn = wait.until(EC.element_to_be_clickable((By.ID, "button-cart")))
    add_btn.click()
    logger.info("Clicked Add to Cart button.")

    success_alert = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success")))
    assert "Success: You have added" in success_alert.text, f"Unexpected alert text: {success_alert.text}"
    assert product["product_name"] in success_alert.text, f"Product name not in alert: {success_alert.text}"
    logger.info("Add to Cart success toast verified.")
    take_screenshot(driver, "post_add_to_cart")
    time.sleep(1.5)  # Visual pause: add to cart alert visible

    # STEP 5: Update quantity in cart
    logger.info("STEP 5: Navigating to cart to update quantity...")
    cart_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Shopping Cart']")))
    cart_link.click()

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#content form .table-responsive table tbody tr")))
    time.sleep(1.5)  # Visual pause: initial cart view
    qty_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#content form table tbody tr td:nth-child(4) input")))
    qty_input.clear()
    qty_input.send_keys(str(target_qty))

    update_btn = driver.find_element(By.CSS_SELECTOR, "#content form table tbody tr td:nth-child(4) button[type='submit']")
    update_btn.click()

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success")))
    logger.info(f"Cart updated to quantity {target_qty}.")
    take_screenshot(driver, "post_update")
    time.sleep(1.5)  # Visual pause: updated cart with success banner

    # STEP 6: Verify cart details (Product Name, Quantity, Price calculation)
    logger.info("STEP 6: Verifying cart details and line total calculation...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#content form table tbody tr")))
    row = driver.find_element(By.CSS_SELECTOR, "#content form table tbody tr")
    cols = row.find_elements(By.TAG_NAME, "td")

    actual_name = cols[1].text.split("\n")[0].replace("***", "").strip()
    actual_qty = int(cols[3].find_element(By.TAG_NAME, "input").get_attribute("value"))
    unit_price = parse_price(cols[4].text)
    line_total = parse_price(cols[5].text)
    expected_total = round(unit_price * actual_qty, 2)

    logger.info(f"Cart Verification -> Item: '{actual_name}', Qty: {actual_qty}, Unit Price: {unit_price}, Line Total: {line_total}")

    # Assertions with clear failure messages
    assert product["product_name"].lower() in actual_name.lower(), (
        f"Product name mismatch: Expected '{product['product_name']}', got '{actual_name}'"
    )
    assert actual_qty == target_qty, (
        f"Quantity mismatch: Expected {target_qty}, got {actual_qty}"
    )
    assert abs(expected_total - line_total) < 0.01, (
        f"Price calculation mismatch: {unit_price} x {actual_qty} = {expected_total}, but cart shows {line_total}"
    )

    logger.info(f"Calculation Verified: {unit_price} x {actual_qty} == {line_total}")
    take_screenshot(driver, "final_cart")
    time.sleep(2.0)  # Visual pause: observe final verified cart before closing
    logger.info("All 10 steps executed successfully!")


# STEP 10: Generate execution report & allow direct execution via python test_ecommerce_v1.py
if __name__ == "__main__":
    report_path = os.path.join(REPORTS_DIR, "report.html")
    logger.info(f"Starting test execution. Report will be saved to: {report_path}")
    exit_code = pytest.main([
        __file__,
        f"--html={report_path}",
        "--self-contained-html",
        "-v",
        "-s"
    ])
    sys.exit(exit_code)
