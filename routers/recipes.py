
import sys
sys.path.append("..")
from fastapi import Depends, HTTPException, APIRouter
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import secrets




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


class Recipe(BaseModel):
    recipe_name: str
    recipe_link: str
    recipe_image: str
    recipe_servings: int
    recipe_time: float
    ingredients: str
    method: str
    cuisine: Optional[str]



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
    
    nutrients = [{"nutrient" : "protein", "quantity": protein_quantity, "operator": protein_operator.value}, 
                {"nutrient" : "carbs" , "quantity": carbs_quantity, "operator": carbs_operator.value},   
                {"nutrient" : "fat" , "quantity": fat_quantity, "operator": fat_operator.value}]

    select_statement = create_select_statement("recipes.recipe_name, recipe_servings, recipe_time, recipe_link, protein_per_serving_grams, carbs_per_serving_grams, fat_per_serving_grams")
    where_clause = json_where_clause_constructor(nutrients, "nutrition")
    where_clause = where_clause.rsplit('AND', 1)[0]
    query = select_statement + where_clause + "LIMIT {};".format(limit_results)
    print(f"SQL QUERY: {query}")
    recipe_model = db.execute(text(query)).all()

    if recipe_model is not None:
        return recipe_model


    raise http_exception()



@router.get("/advanced_search/")
async def advanced_search(search_query : str, ingredients: str, protein_operator: MoreLess = MoreLess.more_than, protein_quantity: Optional[float] = 0.0,
                                carbs_operator: MoreLess = MoreLess.more_than, carbs_quantity: Optional[float] = 0.0, 
                                fat_operator: MoreLess = MoreLess.more_than, fat_quantity: Optional[float] = 0.0, 
                                limit_results: Optional[int] = 5, db: Session = Depends(get_db)):
    
    nutrients = [{"nutrient" : "protein", "quantity": protein_quantity, "operator": protein_operator.value}, 
                {"nutrient" : "carbs" , "quantity": carbs_quantity, "operator": carbs_operator.value},   
                {"nutrient" : "fat" , "quantity": fat_quantity, "operator": fat_operator.value}]

    select_statement = create_select_statement("recipes.recipe_name, recipe_servings, recipe_time, recipe_link, protein_per_serving_grams, carbs_per_serving_grams, fat_per_serving_grams")
    query = json_query_generator_advanced(search_query, select_statement, ingredients, nutrients, limit_results)
    print(f"SQL QUERY: {query}")
    recipe_model = db.execute(text(query)).all()

    if recipe_model is not None:
        return recipe_model

    raise http_exception()


@router.post("/")
async def create_recipe(create_recipe: Recipe, db: Session = Depends(get_db)):

    recipe_id = secrets.token_hex(nbytes=16)

    recipe_model = models.Recipes()
    recipe_model.id = recipe_id
    recipe_model.recipe_name = create_recipe.recipe_name
    recipe_model.channel_id = "ryan-beckett"
    recipe_model.channel_name = "ryan-beckett"
    recipe_model.recipe_link = create_recipe.recipe_link
    recipe_model.recipe_servings = create_recipe.recipe_servings
    recipe_model.nutrition_score = float(0)
    recipe_model.ingredients_map = {}
    recipe_model.recipe_cuisine = {}

    details_model = models.RecipeDetails()
    details_model.id = recipe_id
    details_model.recipe_name = create_recipe.recipe_name
    details_model.channel_id = "ryan-beckett"
    details_model.channel_name = "ryan-beckett"
    details_model.ingredients_raw = create_recipe.ingredients
    details_model.channel_name = None
    details_model.method_raw = create_recipe.method
    details_model.method_formatted = None

    nutrition_model = models.RecipeNutrition()
    nutrition_model.id = recipe_id
    nutrition_model.recipe_name = create_recipe.recipe_name
    nutrition_model.channel_id = "ryan-beckett"
    nutrition_model.channel_name = "ryan-beckett"
    nutrition_model.protein_per_serving_grams = None
    nutrition_model.carbs_per_serving_grams = None
    nutrition_model.fat_per_serving_grams = None
    nutrition_model.calories_per_serving = None
    nutrition_model.nutrition_per_serving = None
    nutrition_model.daily_dozen = None

    db.add(recipe_model)
    db.commit()



    
    print("recipe created")





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
            where_clause =  where_clause + "ingredients_map->>'{}' = 'true' AND ".format(i)


    elif field == "nutrition":
        for x, obj in enumerate(query_list):
            if obj["quantity"] > 0:
                nutrient =  obj["nutrient"]
                quantity = obj["quantity"]
                op = obj["operator"]
                op = ">=" if op == "More than" else "<="
                where_clause =  where_clause + f"{nutrient}_per_serving_grams {op} {quantity} AND "
     
    return where_clause




def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction' : 'successful'
    }

def http_exception():
    return HTTPException(status_code=404, detail='Item not found')


