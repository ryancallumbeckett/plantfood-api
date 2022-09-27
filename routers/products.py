
from datetime import datetime
import sys
sys.path.append("..")

from fastapi import Depends, HTTPException, APIRouter
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from routers.auth import get_current_user, user_exception
from .auth import get_current_user, user_exception, get_password_hash, verify_password
from datetime import datetime


router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Product(BaseModel):
    suppliers: list
    product_name: str
    product_url: Optional[str]
    product_price: float = None
    price_by_weight: Optional[str]
    quantity: float = None
    unit: str = None
    product_image: Optional[str]
    date: datetime


@router.get("/{product_id}")
async def read_product_by_id(product_id: str, db: Session = Depends(get_db)):
    product_model = db.query(models.Products).filter(models.Products.id == product_id).first()
    if product_model is not None:
        return product_model
    raise http_exception()


@router.get("/product/{product_search}")
async def search_products(product_name: str, supermarket: Optional[str] = None, db: Session = Depends(get_db)):

    if supermarket:
        product_model = db.query(models.Products).\
            filter(models.Products.supermarket == supermarket).\
                filter(models.Products.__ts_vector__.match(product_name)).all()
    else:
        product_model = db.query(models.Products).\
            filter(models.Products.__ts_vector__.match(product_name)).all()
         
    if product_model is not None:
        return product_model

    raise http_exception()


@router.post("/product")
async def add_product(product: Product, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        raise user_exception()
    for s in product.suppliers:
        product_model = models.CommunityProducts()
        product_model.supplier = s
        product_model.product_name = product.product_name
        product_model.product_url = product.product_url
        product_model.product_price = product.product_price
        product_model.quantity = product.quantity
        product_model.unit = product.unit
        product_model.product_image = product.product_image
        product_model.date = datetime.now()
        product_model.owner_id = user.get("id")

        db.add(product_model)
        db.commit()

    return successful_response(201)


@router.delete("/{product_id}")
async def delete_product(product_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise user_exception()

    todo_model = db.query(models.CommunityProducts).filter(models.CommunityProducts.product_id == product_id).filter(models.CommunityProducts.owner_id == user.get("id")).first()
    if todo_model is None:
        raise http_exception()

    db.query(models.CommunityProducts).filter(models.CommunityProducts.product_id == product_id).delete()
    db.commit()

    return successful_response(200)



@router.put("/{product_id}")
async def update_product(product_id: int, product: Product, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise user_exception()

    product_model = db.query(models.CommunityProducts).filter(models.CommunityProducts.product_id == product_id).filter(models.CommunityProducts.owner_id == user.get("id")).first()
    if product_model is None:
        raise http_exception()

    product_model.supplier = product.supplier
    product_model.product_name = product.product_name
    product_model.product_url = product.product_url
    product_model.product_price = product.product_price
    product_model.quantity = product.quantity
    product_model.unit = product.unit
    product_model.product_image = product.product_image
    product_model.date = datetime.now()

    db.add(product_model)
    db.commit()

    return successful_response(200)



def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction' : 'successful'
    }

def http_exception():
    return HTTPException(status_code=404, detail='Item not found')