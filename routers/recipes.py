
import sys
sys.path.append("..")
from datetime import datetime
from fastapi import Depends, HTTPException, APIRouter
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from sqlalchemy.sql import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum



router = APIRouter(
    prefix="/recipes",
    tags=["recipes"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class NutritionSearch(BaseModel):
    protein: float
    fat: float
    carbs: float
    calories: float


class MoreLess(str, Enum):
    more_than = "More than"
    less_than = "Less than"



@router.get("/{recipe_id}")
async def get_recipe_by_id(recipe_id: str, db: Session = Depends(get_db)):

    recipe_model = db.query(models.Recipes).filter(models.Recipes.id == recipe_id).first()
    if recipe_model is not None:

        return recipe_model
        
    raise http_exception()



@router.get("/search_by_title/{recipe_name}")
async def search_by_recipe_name(recipe_name: str, db: Session = Depends(get_db)):

    recipe_query = prep_string_for_search(recipe_name)
    recipe_model = db.query(models.Recipes.recipe_name, models.Recipes.channel_name, models.Recipes.recipe_link, models.Recipes.recipe_time, models.Recipes.recipe_servings).\
                filter(models.Recipes.__ts_vector__.match(recipe_query)).all()
   
    if recipe_model is not None:
        return recipe_model

    raise http_exception()



@router.get("/search_by_ingredients/{ingredients}")
async def search_by_ingredients(ingredients: str, limit_results: Optional[int] = 5, db: Session = Depends(get_db)):

    select_statement = create_select_statement("recipes.id, recipes.recipe_name, recipes.recipe_servings, recipes.recipe_time, recipes.recipe_link")
    where_clause = json_where_clause_constructor(ingredients, "ingredients")
    where_clause = where_clause.rsplit('AND', 1)[0]
    query = select_statement + where_clause + "LIMIT {};".format(limit_results)
    recipe_model = db.execute(text(query)).all()

    if recipe_model is not None:
        return recipe_model

    raise http_exception()



@router.get("/search_by_nutrition/{macro_nutrients}")
async def search_by_macronutrients(protein_operator: MoreLess = MoreLess.more_than, protein_quantity: Optional[float] = 0.0,
                                carbs_operator: MoreLess = MoreLess.more_than, carbs_quantity: Optional[float] = 0.0, 
                                fat_operator: MoreLess = MoreLess.more_than, fat_quantity: Optional[float] = 0.0, 
                                limit_results: Optional[int] = 5, db: Session = Depends(get_db)):
    
    nutrients = [{"nutrient" : "PROCNT", "quantity": protein_quantity, "operator": protein_operator.value}, 
                {"nutrient" : "CHOCDF" , "quantity": carbs_quantity, "operator": fat_operator.value},   
                {"nutrient" : "FAT" , "quantity": fat_quantity, "operator": carbs_operator.value}]

    select_statement = create_select_statement("recipes.id, recipes.recipe_name, recipes.recipe_servings, recipes.recipe_time, recipes.recipe_link, recipe_nutrition.nutrition_per_serving")
    where_clause = json_where_clause_constructor(nutrients, "nutrition")
    where_clause = where_clause.rsplit('AND', 1)[0]
    query = select_statement + where_clause + "LIMIT {};".format(limit_results)
    recipe_model = db.execute(text(query)).all()

    if recipe_model is not None:
        return recipe_model


    raise http_exception()



@router.get("/advanced_search/")
async def advanced_search(search_query : str, ingredients: str, protein_operator: MoreLess = MoreLess.more_than, protein_quantity: Optional[float] = 0.0,
                                carbs_operator: MoreLess = MoreLess.more_than, carbs_quantity: Optional[float] = 0.0, 
                                fat_operator: MoreLess = MoreLess.more_than, fat_quantity: Optional[float] = 0.0, 
                                limit_results: Optional[int] = 5, db: Session = Depends(get_db)):
    
    nutrients = [{"nutrient" : "PROCNT", "quantity": protein_quantity, "operator": protein_operator.value}, 
                {"nutrient" : "CHOCDF" , "quantity": carbs_quantity, "operator": carbs_operator.value},   
                {"nutrient" : "FAT" , "quantity": fat_quantity, "operator": fat_operator.value}]

    select_statement = create_select_statement("recipes.id, recipes.recipe_name, recipes.recipe_servings, recipes.recipe_time, recipes.recipe_link, recipe_nutrition.nutrition_per_serving")
    query = json_query_generator_advanced(search_query, select_statement, ingredients, nutrients, limit_results)
    print(f"QUERY {query}")
    recipe_model = db.execute(text(query)).all()
    results = get_required_nutrients(recipe_model)

    if results is not None:
        return results

    raise http_exception()





def prep_string_for_search(string):
    string = string.strip()
    string = string.replace(" ", " & ")
    return string


def create_select_statement(select_columns):
    select_statement = "SELECT {} FROM recipe_nutrition JOIN recipes ON recipe_nutrition.id = recipes.id WHERE ".format(str(select_columns))
    return select_statement


def json_query_generator_advanced(keyword, select_statement, ingredient_list, nutrition_list, limit):
    keyword_where_clause = ts_vector_query_constructor(keyword)
    ingredients_where_clause =  json_where_clause_constructor(ingredient_list, "ingredients")
    nutrition_where_clause =  json_where_clause_constructor(nutrition_list, "nutrition")
    query = select_statement + keyword_where_clause + ingredients_where_clause + nutrition_where_clause
    query = query.rsplit('AND', 1)[0]
    final_query = query + "LIMIT {};".format(limit)
    return final_query


def ts_vector_query_constructor(keyword):
    keyword_query = "__ts_vector__ @@ to_tsquery('english', '{}')".format(keyword)
    return keyword_query + " AND "


def json_where_clause_constructor(query_list, field):
    where_clause = ''

    if field == "ingredients":
        query_list =  query_list.split(',')
        for x, i in enumerate(query_list): 
            i = i.strip()
            if (x + 1) < len(query_list):
                where_clause =  where_clause + "ingredients_map->>'{}' = 'true' AND ".format(i)
            else:
                where_clause =  where_clause + "ingredients_map->>'{}' = 'true' ".format(i)

    elif field == "nutrition":
        for x, obj in enumerate(query_list):
            nutrient =  obj["nutrient"]
            quantity = obj["quantity"]
            op = obj["operator"]
            op = ">" if op == "More than" else "<"
            if (x + 1) < len(query_list):
                where_clause =  where_clause + f"(nutrition_per_serving->'{nutrient}'->>'quantity')::float {op}= {quantity} AND "
            else:
                where_clause =  where_clause + f"(nutrition_per_serving->'{nutrient}'->>'quantity')::float {op}= {quantity} "


    return where_clause + " AND "



def get_required_nutrients(recipe_model):
    results = []
    for recipe in recipe_model:
        result = {"recipe_name" : recipe["recipe_name"], "recipe_link" : recipe["recipe_link"], "recipe_servings" : recipe["recipe_servings"], "recipe_time" : recipe["recipe_time"]}
        result.update({"protein": round(recipe["nutrition_per_serving"]["PROCNT"]["quantity"], 2),
                        "carbs": round(recipe["nutrition_per_serving"]["CHOCDF"]["quantity"], 2),
                        "fat": round(recipe["nutrition_per_serving"]["FAT"]["quantity"], 2)})
        results.append(result)

    return results


def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction' : 'successful'
    }

def http_exception():
    return HTTPException(status_code=404, detail='Item not found')


