import json

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper_utils.BaseSelenium import BaseSelenium
from scraper_utils.result import Result


class LiverPoolSeleniumSpider(BaseSelenium):
    name = 'LiverPoolSelenium'

    def __init__(self, url: str, result_file: str, browser: str = 'chrome'):
        super().__init__(browser)
        self.url = url
        self.result_file = result_file
        self.result = Result()

    def run(self):
        # Navigate to the given URL
        self.navigate_to_page(self.url)

        try:
            # Wait until the page is fully loaded by checking for a critical element
            self.wait_for_element(By.TAG_NAME, 'body', timeout=2)

            # Check if the page is broken
            if self.is_link_broken():
                self.result.status = "Link broken"
                self.result.price = 0
                self.result.category = "Link broken"
            else:
                # Check if the product is in stock
                in_stock = self.check_if_in_stock()
                if in_stock:
                    self.result.status = "In stock"
                else:
                    self.result.status = "Out of stock"

                breadcrumbs = self.extract_breadcrumbs()
                self.result.category = breadcrumbs[2]
                price = self.extract_prices()
                self.result.price = price
            self.save_result(self.result)
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

    def extract_breadcrumbs(self):
        try:
            self.driver.set_window_size(1920, 1080)

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.driver.execute_script("window.scrollTo(0, 0);")

            # Locate the breadcrumb list
            breadcrumb_container = WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.m-breadcrumb"))
            )

            self.scroll_to_element(breadcrumb_container)

            breadcrumb_elements = WebDriverWait(self.driver, 6).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.m-breadcrumb-list li"))
            )

            # Extract text from each breadcrumb element
            breadcrumbs = []
            for element in breadcrumb_elements:
                # We check if the element has an 'a' tag or a 'span' tag with a strong element for the active breadcrumb
                breadcrumb_text = element.find_element(By.CSS_SELECTOR,
                                                       "a.a-breadcrumb__label, span.a-breadcrumb__label strong").text.strip()
                breadcrumbs.append(breadcrumb_text)

            # Print the extracted breadcrumb elements
            print("Breadcrumbs:", breadcrumbs)

            # Add the current category (the last breadcrumb which is not a link)
            current_category = self.driver.find_element(By.CSS_SELECTOR,
                                                        "ul.m-breadcrumb-list li.active span.a-breadcrumb__label strong")
            if current_category:
                breadcrumbs.append(current_category.text.strip())

            # Reverse breadcrumbs to start from the most specific to the most general
            return list(reversed(breadcrumbs))
        except (NoSuchElementException, TimeoutException):
            return []

    def extract_prices(self):
        try:
            price = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.a-product__paragraphDiscountPrice.m-0.d-inline"))
            )
            parts = price.text.strip().split('\n')
            main_price = parts[0]

            return main_price
        except (NoSuchElementException, TimeoutException):
            return None

    def save_result(self, result):
        with open(self.result_file, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=4)

    def scroll_to_element(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView();", element)

