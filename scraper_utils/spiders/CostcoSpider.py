from scraper_utils.BaseSpider import BaseSpider
import json


class CostcoSpider(BaseSpider):
    name = 'costco'

    def __init__(self, url='https://www.costco.com.mx/', *args, **kwargs):
        super(CostcoSpider, self).__init__(url, *args, **kwargs)
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
                self.save_result(result)
                return

        # Extract details
        original_price = response.css('.price-original .price-value span.notranslate::text').get()
        discount_amount = response.css('.discount-value span.notranslate::text').get()
        final_price = response.css('.price-after-discount .you-pay-value span::text').get()

        # Clean up and assign details if data is available
        item['original_price'] = original_price.strip() if original_price else 'N/A'
        item['discount_amount'] = discount_amount.strip() if discount_amount else 'N/A'
        item['final_price'] = final_price.strip() if final_price else 'N/A'

        # Extract inventory status
        inventory_status_list = response.css('.pdp-message::text').getall()
        item['inventory_status'] = ' '.join(
            [status.strip() for status in inventory_status_list]) if inventory_status_list else 'N/A'

        out_of_stock_button = response.css('button.outOfStock::text').get()
        zip_code_button = response.css('button.bd-view-pricing::text').get()
        if out_of_stock_button:
            result = "Not Available"
            print("The item is out of stock")
        else:
            if zip_code_button and 'Seleccionar Código Postal' in zip_code_button:
                result = "Zip code required and in stock"
                print("Zip code required.")
            else:
                result = "No zip code required but in stock"
                print("No zip code requirement button found.")
            print("The item is in stock")

        self.logger.info(f"Scraped data: {result}")
        # Save result to file
        self.save_result(result)

    def save_result(self, result):
        with open(self.result_file, 'w') as f:
            json.dump(result, f, indent=4)
