import json

from selenium.common import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from scraper_utils.BaseSelenium import BaseSelenium
from scraper_utils.result import Result


class CostcoSeleniumSpider(BaseSelenium):
    name = 'costco'

    def __init__(self, url: str = 'https://www.costco.com.mx/', result_file: str = 'result_costco.json',
                 browser: str = 'chrome'):
        super().__init__(browser)
        self.reuse_driver = False
        self.url = url
        self.result_file = result_file
        self.result = Result()

    def run(self, reuse_driver=True):
        # Navigate to the URL
        self.reuse_driver = reuse_driver

        # Only navigate if not reusing driver or the URL has changed
        if not self.reuse_driver or self.driver.current_url != self.url:
            self.navigate_to_page(self.url)

        try:
            # Wait until the page body is fully loaded
            self.wait_for_element(By.TAG_NAME, 'body', timeout=5)

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

    def is_link_broken(self):
        try:
            # Try to locate the element that indicates the section is present
            try:
                # This should match the container class or a reliable identifying element for that section
                section_element = self.driver.find_element(By.CSS_SELECTOR, "div.product-page-container")
                if section_element:
                    # Section was found, meaning the link is not broken
                    return False
            except NoSuchElementException:
                # Section not found, potentially broken link
                return True
        except (NoSuchElementException, TimeoutException):
            # In case the element or page fails to load, return True indicating the link is broken
            return True

        return False  # Link is not broken if the section is found

    def extract_breadcrumbs(self):
        try:
            breadcrumbs = self.driver.find_elements(By.CSS_SELECTOR, 'ol.breadcrumb li a')
            breadcrumb_texts = [breadcrumb.text.strip() for breadcrumb in breadcrumbs]
            return breadcrumb_texts
        except NoSuchElementException or StaleElementReferenceException:
            return []

    def extract_original_price(self):
        try:
            original_price = self.driver.find_element(By.CSS_SELECTOR,
                                                      'span.notranslate.ng-star-inserted').text
            print(original_price)
            return original_price.strip()
        except NoSuchElementException:
            return None

    def extract_discount_value(self):
        try:
            discount_value = self.driver.find_element(By.CSS_SELECTOR,
                                                      'div.discount span.discount-value sip-format-price span.notranslate').text
            return discount_value.strip()
        except NoSuchElementException:
            return None

    def extract_price_after_discount(self):
        try:
            price_after_discount = self.driver.find_element(By.CSS_SELECTOR,
                                                            'div.price-after-discount div.you-pay-value span.you-pay-value').text
            return price_after_discount.strip()
        except NoSuchElementException:
            return None

    def extract_inventory_status(self):
        try:
            # Fetch all buttons on the page
            buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button[type="button"]')

            # Iterate through each button and check the text content
            for button in buttons:
                button_text = button.text.strip()

                # Check for "Agotado" (Out of stock)
                if button_text == "Agotado":
                    return "Out of stock"
                # Check for "Agregar al Carrito" (In stock)
                elif button_text == "Agregar al Carrito":
                    return "In stock"
                elif button_text == "Establecer Código Postal":
                    return "In stock - Zip code required"
        except NoSuchElementException:
            pass

        try:
            # zip_code_button = self.driver.find_elements(By.CSS_SELECTOR, 'button.bd-view-pricing')
            # if zip_code_button and 'Seleccionar Código Postal' in zip_code_button.text:
            #     return "In stock - Zip code required"
            zip_code_form = self.driver.find_element(By.CSS_SELECTOR, 'form[novalidate] input[name="postalCode"]')
            if zip_code_form:
                return "In stock - Zip code required"
        except NoSuchElementException:
            pass

        return "Link broken"

    def save_result(self):
        with open(self.result_file, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=4)