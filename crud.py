from sqlalchemy.orm import Session

import models
import schemas


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(sku=product.sku, url=product.url, output=product.output)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return schemas.ProductResponse(
        id=db_product.id,
        sku=db_product.sku,
        url=db_product.url,
        output=db_product.output,
        statusCode=201,
        message="Product created successfully"
    )


def update_product(db: Session, product_id: int, product: schemas.ProductUpdate):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product:
        if product.sku is not None:
            db_product.sku = product.sku
        if product.url is not None:
            db_product.url = product.url
        if product.output is not None:
            db_product.output = product.output
        db.commit()
        db.refresh(db_product)
        return schemas.ProductResponse(
            id=db_product.id,
            sku=db_product.sku,
            url=db_product.url,
            output=db_product.output,
            statusCode=200,
            message="Product updated successfully"
        )
    return None


def delete_product(db: Session, product_id: int):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return schemas.ProductResponse(
            id=db_product.id,
            sku=db_product.sku,
            url=db_product.url,
            output=db_product.output,
            statusCode=200,
            message="Product deleted successfully"
        )
    return None
