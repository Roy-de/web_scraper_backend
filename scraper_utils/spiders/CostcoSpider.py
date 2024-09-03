import json
import re

from scraper_utils.BaseSpider import BaseSpider

from scraper_utils.result import Result


class CostcoSpider(BaseSpider):
    name = 'costco'

    def __init__(self, url='https://www.costco.com.mx/', *args, **kwargs):
        super(CostcoSpider, self).__init__(url, *args, **kwargs)
        self.result = Result()
        self.result_file = 'result_costco.json'

    def parse(self, response, **kwargs):

        # Capture the entire page content
        item = {'url': response.url,
                'full_html': response.body.decode('utf-8').strip() if response.body else 'No HTML content found'}

        # Extracting the specific section
        response.css('div.product-price-container').get()

        # Check if the section contains only skeletons
        skeleton_check = response.css('sip-skeleton')
        if skeleton_check:
            # Check if all relevant parts of the section are skeletons
            if (response.css('div.product-price sip-skeleton').get() and
                    response.css('div.product-information sip-skeleton').get() and
                    response.css('div.add-to-cart sip-skeleton').get()):
                result = 'Link broken'
                item[
                    'error_message'] = ('The link seems to be broken or content is not available. Only loading '
                                        'placeholders found.')
                self.result.status = result
                return

        breadcrumbs = response.css('ol.breadcrumb li a::text').getall()

        if breadcrumbs:
            self.result.category = breadcrumbs[1]

        # Extract details
        price = response.css('span.notranslate.ng-star-inserted::text').get()
        item['price'] = price.strip() if price else 'N/A'
        self.result.price = item['price']

        # Extract inventory status
        inventory_status_list = response.css('.pdp-message::text').getall()
        item['inventory_status'] = ' '.join(
            [status.strip() for status in inventory_status_list]) if inventory_status_list else 'N/A'

        out_of_stock_button = response.css('button.outOfStock::text').get()
        in_stock_button = response.css('button#add-to-cart-button::text').get()
        zip_code_button = response.css('button.bd-view-pricing::text').get()
        if out_of_stock_button:
            result = "Out of stock"
        else:
            if zip_code_button and 'Seleccionar Código Postal' in zip_code_button:
                result = "In stock - Zip code required"
            elif in_stock_button:
                result = "In stock"
            else:
                result = "Link broken"

        self.logger.info(f"Assigned price: {self.result.price}")
        # Save result to file
        self.result.status = result
        self.logger.info(f"Assigned status: {self.result.status}")

        self.save_result()

    def save_result(self):
        with open(self.result_file, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=4)
