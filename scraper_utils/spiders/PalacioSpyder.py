import json
import logging
from scraper_utils.BaseSpider import BaseSpider
from scraper_utils.result import Result

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PalacioSpyder(BaseSpider):
    name = 'palacio'

    custom_settings = {
        'HTTPERROR_ALLOWED_CODES': [410],
    }

    def __init__(self, url='https://www.elpalaciodehierro.com/', *args, **kwargs):
        super(PalacioSpyder, self).__init__(url, *args, **kwargs)
        self.result = Result()
        self.result_file = 'result_palacio.json'

    def parse(self, response, **kwargs):

        # Check if the response status is 410
        if response.status == 410:
            result = "Link broken"
            self.result.status = result
            return
        price = response.css("span.b-product_price-value::text").get()
        self.result.price = price.strip()

        category = response.css("h2.b-product_main_info-brand a::text").get()
        self.result.category = category.strip()
        # Check if the product main info div exists to determine if the link works
        product_info = response.css('div.l-pdp-b-content.b-product_main_info.m-pdpv2').get()
        if product_info:

            # Check if the 'Add to Cart' button is disabled to determine stock status
            is_disabled = response.css("button.b-add_to_cart_v2-btn.m-disabled").get()
            result = "Out of stock" if is_disabled else "In stock"
        else:
            result = "Link broken"

        # Save the result to a file
        self.result.status = result

        self.save_result()

    def save_result(self):
        with open(self.result_file, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=4)
