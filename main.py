import json
import multiprocessing
import os
import traceback
from concurrent.futures import ProcessPoolExecutor
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from starlette.middleware.cors import CORSMiddleware

from scraper_utils import BaseSpider, BaseSelenium
from scraper_utils.result import Result
from scraper_utils.spiders.CostcoSeleniumSpider import CostcoSeleniumSpider
from scraper_utils.spiders.MercadoLibreSelenium import MercadoLibreSeleniumSpider
from scraper_utils.spiders.LiverpoolSelenium import LiverPoolSeleniumSpider
from scraper_utils.spiders.CostcoSpider import CostcoSpider
from scraper_utils.spiders.PalacioSpyder import PalacioSpyder

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. Replace with specific origins for production.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.). Adjust as needed.
    allow_headers=["*"],  # Allows all headers. Adjust as needed.
)

processes = {}


def run_scrapy_crawler_process(url: str, spider: BaseSpider, result_file: str):
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(spider, url=url)
    process.start()
    return read_result_file(result_file)


def run_selenium_crawler_process(url: str, spider_class: BaseSelenium, result_file: str):
    try:
        spider = spider_class(url=url, result_file=result_file)
        spider.run()
        return read_result_file(result_file)
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}


class CrawlerRequest(BaseModel):
    sku: Optional[str]
    url: str


def clean_json_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f)


def read_result_file(result_file):
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            return json.load(f)
    else:
        return {"No result found"}


@app.post("/run_crawler/")
async def run_crawler(request: CrawlerRequest):
    url = request.url
    result = Result()
    # Determine the spider type and result file based on URL
    if 'costco' in url:
        spider = CostcoSeleniumSpider
        result_file = 'result_costco.json'
        clean_json_file(result_file)
        spider_type = 'selenium'
    elif 'elpalaciodehierro' in url:
        spider = PalacioSpyder
        result_file = 'result_palacio.json'
        clean_json_file(result_file)
        spider_type = 'scrapy'
    elif 'liverpool' in url:
        spider = LiverPoolSeleniumSpider
        result_file = "result_liverpool.json"
        clean_json_file(result_file)
        spider_type = 'selenium'
    elif 'mercadolibre' in url:
        spider = MercadoLibreSeleniumSpider
        result_file = "result_mercadolibre.json"
        clean_json_file(result_file)
        spider_type = 'selenium'
    else:

        result.status = "URL not supported"
        result.price = "0"
        result.category = "URL not supported"
        return {"message": result}

    if url in processes:
        raise HTTPException(status_code=400, detail="Crawler is already running for this URL")

    try:
        if spider_type == 'scrapy':
            # For Scrapy spiders, use ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as pool:
                result_future = pool.submit(run_scrapy_crawler_process, url, spider, result_file)
                processes[url] = result_future
                result = result_future.result()
        else:
            # For Selenium spiders, run directly in the main process (single-threaded)
            result = run_selenium_crawler_process(spider_class=spider, url=url, result_file=result_file)

        return {"message": result}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up process entry if the process is completed or failed
        if url in processes:
            del processes[url]
