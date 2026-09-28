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
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DATA_DIR = os.path.join(BASE_DIR, "test_data")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

sys.path.append(BASE_DIR)
from utils.data_reader import get_test_data, persist_user_credentials

log_file = os.path.join(REPORTS_DIR, "test_execution.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()


def take_screenshot(driver, step_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(SCREENSHOTS_DIR, f"{timestamp}_{step_name}.png")
    driver.save_screenshot(filepath)
    return filepath


def parse_price(price_str):
    cleaned = re.sub(r"[^\d.]", "", price_str)
    return float(cleaned) if cleaned else 0.0


@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=options)
    browser.implicitly_wait(5)
    yield browser
    browser.quit()


def test_ecommerce_flow(driver):
    wait = WebDriverWait(driver, 10)

    data = get_test_data(source_type="json", base_dir=DATA_DIR)
    base_url = data.get("base_url", "https://tutorialsninja.com/demo/")
    user = data["user"]
    product = data["product"]
    target_qty = int(product["target_quantity"])

    driver.get(base_url)
    time.sleep(1.5)

    account_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='My Account']")))
    account_menu.click()
    time.sleep(1.0)

    if not user.get("is_registered", False):
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

        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='My Account']"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[text()='Logout']"))).click()
        wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(),'Account Logout')]")))
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='My Account']"))).click()

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
    take_screenshot(driver, "post_login")
    time.sleep(1.5)

    search_bar = wait.until(EC.visibility_of_element_located((By.NAME, "search")))
    search_bar.clear()
    search_bar.send_keys(product["search_term"], Keys.ENTER)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-layout")))
    take_screenshot(driver, "post_search")
    time.sleep(1.5)

    product_link = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//div[contains(@class,'product-layout')]//h4/a[contains(text(),'{product['product_name']}')]")
    ))
    product_link.click()
    time.sleep(1.5)

    add_btn = wait.until(EC.element_to_be_clickable((By.ID, "button-cart")))
    add_btn.click()

    success_alert = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success")))
    assert "Success: You have added" in success_alert.text
    assert product["product_name"] in success_alert.text
    take_screenshot(driver, "post_add_to_cart")
    time.sleep(1.5)

    cart_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@title='Shopping Cart']")))
    cart_link.click()

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#content form .table-responsive table tbody tr")))
    time.sleep(1.5)

    qty_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#content form table tbody tr td:nth-child(4) input")))
    qty_input.clear()
    qty_input.send_keys(str(target_qty))

    update_btn = driver.find_element(By.CSS_SELECTOR, "#content form table tbody tr td:nth-child(4) button[type='submit']")
    update_btn.click()

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-success")))
    take_screenshot(driver, "post_update")
    time.sleep(1.5)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#content form table tbody tr")))
    row = driver.find_element(By.CSS_SELECTOR, "#content form table tbody tr")
    cols = row.find_elements(By.TAG_NAME, "td")

    actual_name = cols[1].text.split("\n")[0].replace("***", "").strip()
    actual_qty = int(cols[3].find_element(By.TAG_NAME, "input").get_attribute("value"))
    unit_price = parse_price(cols[4].text)
    line_total = parse_price(cols[5].text)
    expected_total = round(unit_price * actual_qty, 2)

    assert product["product_name"].lower() in actual_name.lower()
    assert actual_qty == target_qty
    assert abs(expected_total - line_total) < 0.01

    take_screenshot(driver, "final_cart")
    time.sleep(2.0)


if __name__ == "__main__":
    report_file = os.path.join(REPORTS_DIR, "report.html")
    pytest.main([
        __file__,
        f"--html={report_file}",
        "--self-contained-html",
        "-v"
    ])
