from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    sku: str
    url: str
    output: Optional[str] = None


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    url: Optional[str] = None
    output: Optional[str] = None


class ProductResponse(ProductCreate):
    id: int
    statusCode: int
    message: str

    class Config:
        from_attributes = True
