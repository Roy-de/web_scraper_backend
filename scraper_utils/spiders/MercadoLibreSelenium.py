import json
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper_utils.BaseSelenium import BaseSelenium


class MercadoLibreSeleniumSpider(BaseSelenium):
    name = "MercadoLibreSelenium"

    def __init__(self, url: str, result_file: str, browser: str = 'chrome'):
        super().__init__(browser)
        self.url = url
        self.result_file = result_file

    def save_result(self, result):
        with open(self.result_file, 'w') as f:
            json.dump(result, f, indent=4)

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
                # Check if the product is in stock or available through external vendors
                availability_status = self.check_if_in_stock()
                self.save_result(availability_status)
        except TimeoutException:
            print("Page did not load fully, the link might be broken or there was a loading issue.")

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
                return "In stock."

        except (NoSuchElementException, TimeoutException):
            # If "Comprar ahora" button is not found, check for external vendors
            try:
                external_vendor_element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.ID, ':R16qakck4um:'))
                )
                if external_vendor_element.is_displayed():
                    return "Available through external vendors."
            except (NoSuchElementException, TimeoutException):
                return "Out of stock."

        return "Out of stock."


if __name__ == '__main__':
    spider = MercadoLibreSeleniumSpider(
        url="https://www.mercadolibre.com.mx/asador-electrico-george-foreman-grd6090b-gris/p/MLM18983601?pdp_filters=item_id:MLM1431792087",
        result_file="result_mercado.json"
    )
    spider.run()
