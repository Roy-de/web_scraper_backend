import json
import logging
from scraper_utils.BaseSpider import BaseSpider

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
        self.result_file = 'result_palacio.json'

    def parse(self, response, **kwargs):
        result = {'link_works': "Link does not work"}

        # Check if the response status is 410
        if response.status == 410:
            result['error'] = "Link does not work (410 Gone)"
            self.save_result(result)
            return

        # Check if the product main info div exists to determine if the link works
        product_info = response.css('div.l-pdp-b-content.b-product_main_info.m-pdpv2').get()
        if product_info:
            result['link_works'] = "Link works"

            # Check if the 'Add to Cart' button is disabled to determine stock status
            is_disabled = response.css("button.b-add_to_cart_v2-btn.m-disabled").get()
            result['stock'] = "Not Available" if is_disabled else "Available"
        else:
            result['error'] = "Product main info not found"

        # Save the result to a file
        self.save_result(result)

    def save_result(self, result):
        try:
            logger.debug(f"Saving result to {self.result_file}: {result}")
            with open(self.result_file, 'w') as f:
                json.dump(result, f, indent=4)
            logger.debug(f"Successfully saved result to {self.result_file}")
        except Exception as e:
            logger.error(f"Failed to save result to {self.result_file}: {e}")
