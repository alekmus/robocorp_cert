from Browser import Browser, SelectAttribute
from RPA.PDF import PDF
from RPA.Dialogs import Dialogs
from RPA.Robocorp.Vault import Vault
import logging
import requests
import os
import sys
import shutil

os.environ["RPA_SECRET_MANAGER"]="RPA.Robocorp.Vault.FileSecrets"
os.environ["RPA_SECRET_FILE"]=fr"{os.getcwd()}\vault.json"

logger = logging.getLogger(__name__)

stdout = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    level=logging.INFO,
    format="[{%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    handlers=[stdout],
)

def main():
    print(Vault().get_secret("test")["secret_greeting"])
    order_site = ask_for_order_website()
    if not os.path.exists("output/receipts"):
        os.mkdir("output/receipts")
    try:
        driver = open_order_website(order_site)
        accept_modal(driver)
        orders = download_orders()
        i = 0
        for order in orders:
            try:
                select_parts(order, driver)
                show_robot_model(driver)
                submit_order(driver)
                i = add_screenshot_to_pdf(i)
                accept_modal(driver)
            except:
                print(order)
                logger.info("Unsuccessful purchase")
    finally:
        driver.close_browser()
    create_a_zip_file()

def ask_for_order_website():
    dialog = Dialogs()
    dialog.add_text_input("Order website", "Give url to the .csv file: https://robotsparebinindustries.com/#/robot-order")
    result = dialog.run_dialog()
    return result["Order website"]

def create_a_zip_file():
    shutil.make_archive("output/receipts", "zip", "output/receipts")
    shutil.rmtree("output/receipts",ignore_errors=True)

def add_screenshot_to_pdf(i):
    PDF().add_files_to_pdf(
        files=["output/receipt.pdf","output/robot.png"], 
        target_document = f"output/receipts/out_{i}.pdf")
    return i+1

def submit_order(driver:Browser):
    while (driver.get_element_count('xpath=//button[@id="order-another"]') == 0):
        driver.click('xpath=//button[@id="order"]')
    receipt_html = driver.get_property('xpath=//div[@id="receipt"]', property="outerHTML")
    PDF().html_to_pdf(receipt_html, "output/receipt.pdf")
    driver.click('xpath=//button[@id="order-another"]')
    
def show_robot_model(driver:Browser):
    driver.click('xpath=//button[text()="Preview"]')
    driver.take_screenshot(f"{os.getcwd()}/output/robot.png", 'xpath=//div[@id="robot-preview"]')

def select_parts(order:str, driver:Browser):
        parts = order.split(",")
        select_head(parts[1], driver)
        select_body(parts[2], driver)
        select_legs(parts[3], driver)
        select_address(parts[4], driver)

def select_head(head, driver:Browser):
    driver.select_options_by('xpath=//select[@id="head"]', SelectAttribute["value"], head)

def select_body(body, driver:Browser):
    driver.click(f'xpath=//input[@id="id-body-{body}"]')

def select_legs(legs, driver:Browser):
    driver.type_text(
        'xpath=//input[contains(@placeholder, "Enter the part number for the legs")]',
        legs
    )

def select_address(address, driver:Browser):
    driver.type_text('xpath=//input[@id="address"]', address)

def download_orders():
    resp = requests.get(url="https://robotsparebinindustries.com/orders.csv")
    lines = resp.content.decode("utf-8").split("\n")
    return lines[1:]

def accept_modal(driver:Browser):
    driver.click('xpath=//button[text()="OK"]')

def open_order_website(site):
    driver = Browser()
    driver.open_browser(site)
    return driver

if __name__ == "__main__":
        main()