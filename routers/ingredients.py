
import sys
sys.path.append("..")
from fastapi import Depends, HTTPException, APIRouter
import models
from db import engine, get_db
from sqlalchemy.orm import Session
from typing import Optional
from core.conversion_utils import convert_units_to_grams, convert_units_to_lemma
from core.mongo_operator import MongoOperator
from sqlalchemy.sql import text


router = APIRouter(
    prefix="/ingredients",
    tags=["Ingredients"],
    responses={404: {"description": "Not found"}}
)

# models.Base.metadata.create_all(bind=engine)


@router.get("/")
async def get_ingredients(db: Session = Depends(get_db)):
    ingredient_model = db.query(models.Ingredients).first()
    if ingredient_model is not None:
        return ingredient_model
    raise http_exception()




@router.get("/{ingredient_id}/")
async def get_ingredient_by_id(ingredient_id: str, db: Session = Depends(get_db)):
    ingredient_model = db.query(models.Ingredients).filter(models.Ingredients.id == ingredient_id).first()
    if ingredient_model is not None:
        return ingredient_model
    raise http_exception()




@router.get("/ingredient/{ingredient_search}/")
async def search_ingredients(ingredient_name: str, db: Session = Depends(get_db)):

    ingredient_name = prep_string_for_search(ingredient_name)
    ingredient_model = db.query(models.Ingredients.ingredient_name, models.Ingredients.id, models.Ingredients.ingredient_image).\
                filter(models.Ingredients.__ts_vector__.match(ingredient_name)).all()
   
    if ingredient_model is not None:
        return ingredient_model

    raise http_exception()



@router.get("/ingredient/nutrition/{ingredient_id}/")
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


    ingredient_name = prep_string_for_search(ingredient_name)
    query = f"SELECT product_name, supermarket, product_price_gbp, product_quantity, product_unit, gbp_per_100g, gbp_per_unit FROM supermarket_products_current WHERE __ts_vector__ @@ to_tsquery('english', '{ingredient_name}');"
    product_model = db.execute(text(query)).all()

    if product_model:
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
