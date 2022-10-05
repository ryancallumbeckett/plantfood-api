
from audioop import avg
import sys
sys.path.append("..")
from datetime import datetime
from fastapi import Depends, HTTPException, APIRouter
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from pydantic import BaseModel, Field
from typing import Optional
from routers.auth import get_current_user, user_exception
from .auth import get_current_user, user_exception, get_password_hash, verify_password
from datetime import datetime
from core.conversion_utils import convert_units_to_grams, convert_units_to_lemma
from mongo_operator import MongoOperator


router = APIRouter(
    prefix="/ingredients",
    tags=["ingredients"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/{ingredient_id}")
async def get_product_by_id(ingredient_id: str, db: Session = Depends(get_db)):
    ingredient_model = db.query(models.Ingredients).filter(models.Ingredients.id == ingredient_id).first()
    if ingredient_model is not None:
        return ingredient_model
    raise http_exception()




@router.get("/ingredient/{ingredient_search}")
async def search_ingredients(ingredient_name: str, db: Session = Depends(get_db)):

    ingredient_name = prep_string_for_search(ingredient_name)
    ingredient_model = db.query(models.Ingredients.ingredient_name, models.Ingredients.id, models.Ingredients.ingredient_image).\
                filter(models.Ingredients.__ts_vector__.match(ingredient_name)).all()
   
    if ingredient_model is not None:
        return ingredient_model

    raise http_exception()



@router.get("/ingredient/nutrition/{ingredient_id}")
async def get_nutrition_by_id(ingredient_id: str, db: Session = Depends(get_db)):

    ingredient_model = db.query(models.Ingredients.ingredient_name, models.Ingredients.id, models.Ingredients.ingredient_image, 
                    models.Ingredients.nutrition_information, models.Ingredients.nutrition_source).\
                    filter(models.Ingredients.id == ingredient_id).first()
   
    if ingredient_model is not None:
        return ingredient_model

    raise http_exception()



@router.get("/ingredient/nutrition/{ingredient_name}")
async def get_nutrition_by_name(ingredient_name: str, db: Session = Depends(get_db)):

    ingredient_model = db.query(models.Ingredients.ingredient_name, models.Ingredients.id, models.Ingredients.ingredient_image, 
                    models.Ingredients.nutrition_information, models.Ingredients.nutrition_source).\
                    filter(models.Ingredients.ingredient_name == ingredient_name).first()
   
    if ingredient_model is not None:
        return ingredient_model

    raise http_exception()




@router.get("/ingredients/calculate_price/{ingredient_name}")
async def get_estimated_price(ingredient_name: str, 
                                ingredient_quantity: float, 
                                ingredient_unit: str, 
                                grams_per_cup: Optional[int] = None, 
                                db: Session = Depends(get_db)):

    #Find the converion metrics for the ingredient
    mongo = MongoOperator()
    results_object = mongo.fuzzy_search(ingredient_name, "ingredient_name")
    results = list(results_object)
    grams_per_cup = results[0]["grams_per_cup"]
    grams_per_quantity = results[0]["grams_per_quantity"]
    ingredient_unit = ingredient_unit.upper()

    if ingredient_unit != "EACH":
        unit_lemma =  convert_units_to_lemma(ingredient_unit.lower())
        gram_weight = convert_units_to_grams(ingredient_quantity, unit_lemma, grams_per_cup, ingredient_name)
        ingredient_unit = "G"
    else:
        gram_weight = grams_per_quantity

    #Make calls to postgresdb
    ingredient_name = prep_string_for_search(ingredient_name)
    product_model = db.query(models.Products.product_name, models.Products.supermarket, models.Products.product_price_gbp, models.Products.product_quantity, models.Products.gbp_per_100g, models.Products.gbp_per_unit).\
        filter(models.Products.__ts_vector__.match(ingredient_name)).\
            order_by(func.length(models.Products.product_name)).\
                order_by(models.Products.product_price_gbp.asc()).all()


    if product_model:
        #Try to process the ingredient with the unit given, otherwise process as possible
        product_model =  product_model[0]
        if ingredient_unit == "EACH":
            if product_model["gbp_per_unit"] is not None:
                price_per_unit = product_model["gbp_per_unit"]
                estimated_cost = round(float(price_per_unit) * ingredient_quantity, 2)
            else:
                price_per_100g = product_model["gbp_per_100g"]
                quantity = product_model["product_quantity"]
                estimated_cost = round(float(price_per_100g) * (quantity/100), 2)

        elif ingredient_unit == "G":
            if product_model["gbp_per_100g"] is not None:
                price_per_100g = product_model["gbp_per_100g"]
                estimated_cost = round(float(price_per_100g) * (gram_weight/100), 2)
            else:
                price_per_unit = product_model["gbp_per_unit"]
                estimated_cost = round(float(price_per_unit) * ingredient_quantity, 2)

        return estimated_cost, product_model

    raise http_exception()





def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction' : 'successful'
    }

def http_exception():
    return HTTPException(status_code=404, detail='Item not found')


def prep_string_for_search(string):
    string = string.strip()
    string = string.replace(" ", " & ")
    return string
