import json

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper_utils.BaseSelenium import BaseSelenium


class LiverPoolSeleniumSpider(BaseSelenium):
    name = 'LiverPoolSelenium'

    def __init__(self, url: str, result_file: str, browser: str = 'chrome'):
        super().__init__(browser)
        self.url = url
        self.result_file = result_file

    def run(self):
        # Navigate to the given URL
        self.navigate_to_page(self.url)

        try:
            # Wait until the page is fully loaded by checking for a critical element
            self.wait_for_element(By.TAG_NAME, 'body', timeout=2)

            # Check if the page is broken
            if self.is_link_broken():
                self.save_result("Link broken.")
            else:
                # Check if the product is in stock
                in_stock = self.check_if_in_stock()
                if in_stock:
                    self.save_result("Product is in stock.")
                else:
                    self.save_result("Product is out of stock.")
        except TimeoutException:
            print("Page did not load fully, the link might be broken or there was a loading issue.")

    def is_link_broken(self):
        try:
            # Check for specific broken link div
            broken_link_element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'o-content__noResultsNullSearch'))
            )
            if broken_link_element.is_displayed():
                return True

            # Fallback check using page title
            page_title = self.driver.title.lower()
            if "página no encontrada" in page_title or "lo sentimos" in page_title:
                return True

        except (NoSuchElementException, TimeoutException):
            return False
        return False

    def check_if_in_stock(self):
        try:
            # Explicitly wait for the "Comprar ahora" button to appear
            buy_now_button = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, 'opc_pdp_buyNowButton'))
            )
            if buy_now_button.is_displayed():
                return True
        except (NoSuchElementException, TimeoutException):
            return False
        return False

    def save_result(self, result):
        with open(self.result_file, 'w') as f:
            json.dump(result, f, indent=4)
