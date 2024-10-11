import json
import time

from selenium.common import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from scraper_utils.BaseSelenium import BaseSelenium
from scraper_utils.result import Result


class CostcoSeleniumSpider(BaseSelenium):
    name = 'costco'

    def __init__(self, url: str = 'https://www.costco.com.mx/', result_file: str = 'result_costco.json',
                 browser: str = 'chrome'):
        super().__init__(browser)
        self.url = url
        self.result_file = result_file
        self.result = Result()

    def run(self):
        # Navigate to the URL
        self.navigate_to_page(self.url)

        try:
            # Wait until the page body is fully loaded
            self.wait_for_element(By.TAG_NAME, 'body', timeout=20)

            # Check if the page is broken
            if self.is_link_broken():
                self.result.status = 'Link broken'
                self.result.price = 0
                self.result.category = 'Link broken'
                self.save_result()
                return

            # Extract breadcrumbs (category)
            breadcrumbs = self.extract_breadcrumbs()
            if breadcrumbs:
                self.result.category = breadcrumbs[1]  # Adjust to get the correct category

            # Extract product prices and details
            original_price = self.extract_original_price()
            discount_value = self.extract_discount_value()
            price_after_discount = self.extract_price_after_discount()

            print(
                f"Original price: {original_price}, Discount value: {discount_value}, Price after discount: {price_after_discount}")

            self.result.price = price_after_discount or original_price

            # Check inventory status
            inventory_status = self.extract_inventory_status()
            self.result.status = inventory_status

            self.save_result()

        except TimeoutException:
            print("Page did not load fully, there might be a loading issue.")
        finally:
            self.close_browser()

    def is_link_broken(self):
        try:
            # This should match the container class or a reliable identifying element for that section
            wait = WebDriverWait(self.driver, 5)  # Increased timeout
            section_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-page-container")))
            link_working_div = self.driver.find_element(By.CSS_SELECTOR,
                                                        'div.product-price-container.col-xs-12.col-sm-12')
            if section_element or not link_working_div:
                # Section was found, meaning the link is not broken
                return False
        except (NoSuchElementException, TimeoutException):
            # In case the element or page fails to load, return True indicating the link is broken
            return True

    def extract_breadcrumbs(self):
        try:
            wait = WebDriverWait(self.driver, 5)
            breadcrumbs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ol.breadcrumb li a')))
            return [breadcrumb.text.strip() for breadcrumb in breadcrumbs]
        except (NoSuchElementException, StaleElementReferenceException):
            return []

    def extract_original_price(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            original_price = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.notranslate.ng-star-inserted')))
            return original_price.text.strip()
        except NoSuchElementException:
            return None

    def extract_discount_value(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            discount_value = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.discount span.discount-value sip-format-price span.notranslate')))
            return discount_value.text.strip()
        except NoSuchElementException:
            return None

    def extract_price_after_discount(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            price_after_discount = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.price-after-discount')))
            you_pay_value = price_after_discount.find_element(By.CSS_SELECTOR, "div.you-pay-value span.you-pay-value")
            return you_pay_value.text.strip()
        except NoSuchElementException:
            return None

    def extract_inventory_status(self):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                wait = WebDriverWait(self.driver, 10)
                buttons = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'button[type="submit"], button[type="button"]')
                ))

                if buttons:
                    for button in buttons:
                        button_text = button.text.strip()
                        is_disabled = button.get_attribute('disabled')

                        if button_text == "Agotado" or ("disabled" in button.get_attribute('class') and is_disabled):
                            return "Out of stock"
                        elif button_text == "Agregar al Carrito":
                            return "In stock"
                        elif button_text == "Seleccionar Código Postal":
                            return "In stock - Zip code required"
                        else:
                            try:
                                zip_code_form = self.driver.find_element(By.CSS_SELECTOR, 'input[name="postalCode"]')
                                if zip_code_form:
                                    return "In stock - Zip code required"
                            except NoSuchElementException:
                                pass
            except (StaleElementReferenceException, NoSuchElementException):
                retry_count += 1
                time.sleep(2)
                if retry_count >= max_retries:
                    return "Link broken"
            except Exception as e:
                print(f"Error: {e}")
                break  # Break the loop on unexpected errors

        return "Link broken"

    def save_result(self):
        with open(self.result_file, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=4)