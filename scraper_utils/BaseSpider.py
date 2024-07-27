import scrapy


class BaseSpider(scrapy.Spider):
    def __init__(self, url=None, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]

    def parse(self, response, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
