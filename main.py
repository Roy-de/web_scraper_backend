import asyncio
import json
import multiprocessing
import os
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
import time
import traceback

from starlette.responses import StreamingResponse

import crud
import models
import schemas
from scraper_utils import BaseSpider
from scraper_utils.spiders.CostcoSpider import CostcoSpider
from scraper_utils.spiders.PalacioSpyder import PalacioSpyder

models.Base.metadata.create_all(bind=models.engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. Replace with specific origins for production.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.). Adjust as needed.
    allow_headers=["*"],  # Allows all headers. Adjust as needed.
)

processes = {}


# Dependency to get the database session
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.create_product(db, product)
    if db_product:
        return db_product
    raise HTTPException(status_code=400, detail="Failed to create product")


@app.get("/products/", response_model=list[schemas.ProductResponse])
def read_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return [
        schemas.ProductResponse(
            id=product.id,
            sku=product.sku,
            url=product.url,
            output=product.output,
            statusCode=200,
            message="Product retrieved successfully"
        )
        for product in products
    ]


@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id)
    if db_product:
        return schemas.ProductResponse(
            id=db_product.id,
            sku=db_product.sku,
            url=db_product.url,
            output=db_product.output,
            statusCode=200,
            message="Product retrieved successfully"
        )
    raise HTTPException(status_code=404, detail="Product not found")


@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    db_product = crud.update_product(db, product_id, product)
    if db_product:
        return db_product
    raise HTTPException(status_code=404, detail="Product not found")


@app.delete("/products/{product_id}", response_model=schemas.ProductResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.delete_product(db, product_id)
    if db_product:
        return db_product
    raise HTTPException(status_code=404, detail="Product not found")


def run_crawler_process(url: str, spider: BaseSpider):
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(spider, url=url)
    process.start()


class CrawlerRequest(BaseModel):
    sku: Optional[str]
    url: str


def read_result_file(result_file):
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            return json.load(f)
    else:
        return {"error": "No result found"}


@app.post("/run_crawler/")
async def run_crawler(request: CrawlerRequest, db: Session = Depends(get_db)):
    url = request.url

    if 'costco' in url:
        spider = CostcoSpider
        result_file = 'result_costco.json'
    elif 'elpalaciodehierro' in url:
        spider = PalacioSpyder
        result_file = 'result_palacio.json'
    else:
        raise HTTPException(status_code=200, detail="Unsupported URL")

    if url in processes:
        raise HTTPException(status_code=400, detail="Crawler is already running for this URL")

    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=20)

    try:
        # Create and start a new process for the crawler
        process = await loop.run_in_executor(executor, run_crawler_process, url, spider)
        processes[url] = process

        # Optionally, you can set a timeout or periodically check the status of the process
        while process.is_alive():
            await asyncio.sleep(10)

        # Wait for the process to complete
        await loop.run_in_executor(executor, process.join)

        result = await loop.run_in_executor(executor, read_result_file, result_file)

        return {"message": result}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up process entry if the process is completed or failed
        if url in processes:
            del processes[url]


@app.post("/terminate_crawler/")
async def terminate_crawler(url: str):
    global processes

    if url not in processes:
        raise HTTPException(status_code=404, detail="No running process for this URL")

    process = processes[url]
    process.terminate()

    # Remove the process reference
    del processes[url]

    return {'message': 'Crawler terminated successfully'}


@app.get("/export_csv/")
async def export_csv(db: Session = Depends(get_db)):
    # Query all products
    products = crud.get_products(db, skip=0, limit=1000)  # Adjust limit as needed

    # Convert the list of products to a pandas DataFrame
    df = pd.DataFrame([{
        "id": product.id,
        "sku": product.sku,
        "url": product.url,
        "output": product.output
    } for product in products])

    # Convert the DataFrame to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    # Return the CSV file as a StreamingResponse
    csv_buffer.seek(0)
    return StreamingResponse(
        content=csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"}
    )
