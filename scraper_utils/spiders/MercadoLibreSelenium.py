import json
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper_utils.BaseSelenium import BaseSelenium
from scraper_utils.result import Result


class MercadoLibreSeleniumSpider(BaseSelenium):
    name = "MercadoLibreSelenium"

    def __init__(self, url: str, result_file: str, browser: str = 'chrome'):
        super().__init__(browser)
        self.url = url
        self.result_file = result_file
        self.result = Result()

    def save_result(self, result):
        with open(self.result_file, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=4)

    def run(self):
        # Navigate to the given URL
        self.navigate_to_page(self.url)

        try:
            # Wait until the page is fully loaded by checking for a critical element
            self.wait_for_element(By.TAG_NAME, 'body', timeout=2)

            # Check if the page is broken
            if self.is_link_broken():
                self.result.status = "Link broken"
            else:
                # Check if the product is in stock or available through external vendors
                availability_status = self.check_if_in_stock()
                self.result.status = availability_status
                price = self.extract_price()
                self.result.price = f"${price}"
                categories = self.extract_breadcrumbs()
                self.result.category = categories[2]
            self.save_result(self.result)
        except TimeoutException:
            print("Page did not load fully, the link might be broken or there was a loading issue")

    def is_link_broken(self):
        try:
            # Check for the specific div that indicates a valid page structure
            valid_div_element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@class="ui-pdp-container ui-pdp-container--pdp"]'
                               '/div[@class="ui-pdp-container__row ui-pdp--relative ui-pdp-with--separator--fluid '
                               'pb-24" and @id="ui-pdp-main-container"]')
                )
            )
            if valid_div_element.is_displayed():
                return False

        except (NoSuchElementException, TimeoutException):
            return True

        # Fallback check using page title
        page_title = self.driver.title.lower()
        if "página no encontrada" in page_title or "lo sentimos" in page_title:
            return True

        return False

    def check_if_in_stock(self):
        try:
            # Explicitly wait for the "Comprar ahora" button to appear
            buy_now_button = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, ':R9b9k5l9im:'))
            )
            if buy_now_button.is_displayed():
                return "In stock"

        except (NoSuchElementException, TimeoutException):
            # If "Comprar ahora" button is not found, check for external vendors
            try:
                external_vendor_element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.ID, ':R16qakck4um:'))
                )
                if external_vendor_element.is_displayed():
                    return "Available through external vendors"
            except (NoSuchElementException, TimeoutException):
                return "Out of stock"

        return "Out of stock"

    def extract_price(self):
        try:
            price = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,"span.andes-money-amount__fraction"))
            )
            print(price.text)
            return price.text
        except (NoSuchElementException, TimeoutException):
            return None

    def extract_breadcrumbs(self):
        try:
            # Wait until the breadcrumb container is present
            breadcrumb_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ol.andes-breadcrumb"))
            )

            # Extract breadcrumb items
            breadcrumb_elements = breadcrumb_container.find_elements(By.CSS_SELECTOR, "li.andes-breadcrumb__item")
            breadcrumbs = []

            for element in breadcrumb_elements:
                # Extract text from each breadcrumb link
                link_element = element.find_element(By.CSS_SELECTOR, "a.andes-breadcrumb__link")
                breadcrumbs.append(link_element.text.strip())

            # Print the extracted breadcrumb elements
            print("Breadcrumbs:", breadcrumbs)

            return list(reversed(breadcrumbs))
        except (NoSuchElementException, TimeoutException) as e:
            print("An error occurred:", e)
            return []


if __name__ == '__main__':
    spider = MercadoLibreSeleniumSpider(
        url="https://www.mercadolibre.com.mx/asador-electrico-george-foreman-grd6090b-gris/p/MLM18983601?pdp_filters=item_id:MLM1431792087",
        result_file="result_mercado.json"
    )
    spider.run()
