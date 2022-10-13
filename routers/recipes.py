
import sys
sys.path.append("..")
from fastapi import Depends, HTTPException, APIRouter
from .auth import get_current_user, user_exception, get_password_hash, verify_password
import models
from db import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import secrets
from datetime import datetime
from core.nlp_formatter import run_nlp
from core.query_builder import QueryBuilder


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

    postgres =  QueryBuilder("recipes.recipe_name, recipe_servings, recipe_time, recipe_link, protein_per_serving_grams, carbs_per_serving_grams, fat_per_serving_grams", limit_results)
    query = postgres.build_query(ingredients=ingredients)
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

    postgres =  QueryBuilder("recipes.recipe_name, recipe_servings, recipe_time, recipe_link, protein_per_serving_grams, carbs_per_serving_grams, fat_per_serving_grams", limit_results)
    query = postgres.build_query(nutrition=nutrients)
    recipe_model = db.execute(text(query)).all()

    if recipe_model is not None:
        return recipe_model


    raise http_exception()



@router.get("/advanced_search/")
async def advanced_search(keyword : str, ingredients: str, protein_operator: MoreLess = MoreLess.more_than, protein_quantity: Optional[float] = 0.0,
                                carbs_operator: MoreLess = MoreLess.more_than, carbs_quantity: Optional[float] = 0.0, 
                                fat_operator: MoreLess = MoreLess.more_than, fat_quantity: Optional[float] = 0.0, 
                                limit_results: Optional[int] = 5, db: Session = Depends(get_db)):
    
    nutrients = [{"nutrient" : "protein", "quantity": protein_quantity, "operator": protein_operator.value}, 
                {"nutrient" : "carbs" , "quantity": carbs_quantity, "operator": carbs_operator.value},   
                {"nutrient" : "fat" , "quantity": fat_quantity, "operator": fat_operator.value}]


    postgres =  QueryBuilder("recipes.recipe_name, recipe_servings, recipe_time, recipe_link, protein_per_serving_grams, carbs_per_serving_grams, fat_per_serving_grams", limit_results)
    query = postgres.build_query(keyword=keyword, ingredients=ingredients, nutrition=nutrients)
    recipe_model = db.execute(text(query)).all()

    if recipe_model is not None:
        return recipe_model

    raise http_exception()


@router.post("/")
async def create_recipe(create_recipe: Recipe, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        raise user_exception()

    result = run_nlp(create_recipe.ingredients, create_recipe.recipe_servings)

    recipe_id = secrets.token_hex(nbytes=16)
    recipe_model = models.Recipes()
    recipe_model.id = recipe_id
    recipe_model.recipe_name = create_recipe.recipe_name
    recipe_model.channel_id = user.get("id")
    recipe_model.channel_name = user.get("username")
    recipe_model.recipe_link = create_recipe.recipe_link
    recipe_model.recipe_image = create_recipe.recipe_image
    recipe_model.recipe_time = create_recipe.recipe_time
    recipe_model.recipe_servings = create_recipe.recipe_servings
    recipe_model.nutrition_score = result["micronutrient_score"]
    recipe_model.ingredients_map = result["ingredients_map"]
    recipe_model.recipe_cuisine = create_recipe.cuisine

    details_model = models.RecipeDetails()
    details_model.id = recipe_id
    details_model.recipe_name = create_recipe.recipe_name
    details_model.channel_id = user.get("id")
    details_model.channel_name = user.get("username")
    details_model.ingredients_raw = create_recipe.ingredients
    details_model.ingredients_formatted = result["ingredients_formatted"]
    details_model.method_raw = create_recipe.method
    details_model.method_formatted = None
    details_model.last_updated = datetime.now()

    nutrition_model = models.RecipeNutrition()
    nutrition_model.id = recipe_id
    nutrition_model.recipe_name = create_recipe.recipe_name
    nutrition_model.channel_id = user.get("id")
    nutrition_model.channel_name = user.get("username")
    nutrition_model.protein_per_serving_grams = result["protein_per_serving_grams"]
    nutrition_model.carbs_per_serving_grams = result["carbs_per_serving_grams"]
    nutrition_model.fat_per_serving_grams = result["fat_per_serving_grams"]
    nutrition_model.calories_per_serving = result["calories_per_serving"]
    nutrition_model.nutrition_per_serving = result["nutrition_per_serving"]

    db.add(recipe_model)
    db.add(nutrition_model)
    db.add(details_model)
    db.commit()

    return successful_response(201)



@router.delete("/{recipe_id}")
async def delete_recipe_by_id(recipe_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise user_exception()

    recipe_model = db.query(models.Recipes).filter(models.Recipes.id == recipe_id).filter(models.Recipes.channel_id == user.get("id")).first()
    if recipe_model is None:
        raise http_exception()

    details_model = db.query(models.RecipeDetails).filter(models.RecipeDetails.id == recipe_id).filter(models.RecipeDetails.channel_id == user.get("id")).first()
    if details_model is None:
        raise http_exception()

    nutrition_model = db.query(models.RecipeNutrition).filter(models.RecipeNutrition.id == recipe_id).filter(models.RecipeNutrition.channel_id == user.get("id")).first()
    if nutrition_model is None:
        raise http_exception()
    
    db.query(models.Recipes).filter(models.Recipes.id == recipe_id).delete()
    db.query(models.RecipeDetails).filter(models.RecipeDetails.id == recipe_id).delete()
    db.query(models.RecipeNutrition).filter(models.RecipeNutrition.id == recipe_id).delete()

    db.commit()

    return successful_response(200)


@router.put("/{recipe_id}")
async def update_recipe_by_id(recipe_id: str, recipe: Recipe, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise user_exception()

    recipe_model = db.query(models.Recipes).filter(models.Recipes.id == recipe_id).filter(models.Recipes.channel_id == user.get("id")).first()
    if recipe_model is None:
        raise http_exception()

    details_model = db.query(models.RecipeDetails).filter(models.RecipeDetails.id == recipe_id).filter(models.RecipeDetails.channel_id == user.get("id")).first()
    if details_model is None:
        raise http_exception()

    nutrition_model = db.query(models.RecipeNutrition).filter(models.RecipeNutrition.id == recipe_id).filter(models.RecipeNutrition.channel_id == user.get("id")).first()
    if nutrition_model is None:
        raise http_exception()

    result = run_nlp(recipe.ingredients, recipe.recipe_servings)

    recipe_model.recipe_name = recipe.recipe_name
    recipe_model.recipe_link = recipe.recipe_link
    recipe_model.recipe_image = recipe.recipe_image
    recipe_model.recipe_time = recipe.recipe_time
    recipe_model.recipe_servings = recipe.recipe_servings
    recipe_model.nutrition_score = result["micronutrient_score"]
    recipe_model.ingredients_map = result["ingredients_map"]
    recipe_model.recipe_cuisine = recipe.cuisine

    details_model.recipe_name = recipe.recipe_name
    details_model.ingredients_raw = recipe.ingredients
    details_model.ingredients_formatted = result["ingredients_formatted"]
    details_model.method_raw = recipe.method
    details_model.method_formatted = None
    details_model.last_updated = datetime.now()

    nutrition_model.recipe_name = recipe.recipe_name
    nutrition_model.protein_per_serving_grams = result["protein_per_serving_grams"]
    nutrition_model.carbs_per_serving_grams = result["carbs_per_serving_grams"]
    nutrition_model.fat_per_serving_grams = result["fat_per_serving_grams"]
    nutrition_model.calories_per_serving = result["calories_per_serving"]
    nutrition_model.nutrition_per_serving = result["nutrition_per_serving"]

    db.add(recipe_model)
    db.add(nutrition_model)
    db.add(details_model)
    db.commit()

    return successful_response(200)



def prep_string_for_search(string):
    string = string.strip()
    string = string.replace(" ", " & ")
    return string



def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction' : 'successful'
    }

def http_exception():
    return HTTPException(status_code=404, detail='Item not found')




