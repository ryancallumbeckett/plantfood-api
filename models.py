
import json
from typing import Collection
from uuid import UUID
from psycopg2 import Date
from sqlalchemy import Boolean, Column, Float, Integer, String, ForeignKey, DateTime, Index, Computed
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from database import Base
from ts_vector import TSVector


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    products = relationship("CommunityProducts", back_populates="owner")


class Recipes(Base):
    __tablename__ = "recipes"

    id = Column(String, primary_key=True, index=True)
    recipe_name = Column(String, index=True)
    channel_id = Column(String, index=True)
    channel_name = Column(String, index=True)
    recipe_link = Column(String)
    recipe_image= Column(String)
    recipe_time = Column(Float)
    recipe_servings = Column(Integer)
    nutrition_score = Column(Float)
    ingredients_map = Column(JSONB)
    recipe_cuisine = Column(JSONB)

    __ts_vector__ = Column(TSVector(),Computed(
         "to_tsvector('english', recipe_name)",
         persisted=True))

    __table_args__ = (Index('recipe_name__ts_vector__',
          __ts_vector__, postgresql_using='gin'),)


class RecipeDetails(Base):
    __tablename__= "recipe_details"

    id = Column(String, primary_key=True, index=True)
    recipe_name = Column(String, index=True)
    channel_id = Column(String, index=True)
    channel_name = Column(String, index=True)
    ingredients_raw = Column(ARRAY(String))
    ingredients_formatted = Column(String)
    method_raw = Column(ARRAY(String))
    method_formatted = Column(ARRAY(JSONB))

    id = Column(Integer, primary_key=True, index=True)


class RecipeNutrition(Base):
    __tablename__= "recipe_nutrition"

    id = Column(String, primary_key=True, index=True)
    recipe_name = Column(String, index=True)
    channel_id = Column(String, index=True)
    channel_name = Column(String, index=True)
    protein_per_serving_grams = Column(Float)
    carbs_per_serving_grams = Column(Float)
    fat_per_serving_grams = Column(Float)
    calories_per_serving = Column(Float)
    nutrition_per_serving = Column(JSONB)
    daily_dozen = Column(JSONB)

    id = Column(Integer, primary_key=True, index=True)


class Ingredients(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String, unique=True, index=True)
    ingredient_image = Column(String)
    ingredient_categories = Column(JSONB)
    supermarket_aisle = Column(String)
    synonyms = Column(ARRAY(String))
    nutrition_information = Column(JSONB)
    nutrition_source = Column(String)
    nutrition_source_ingredient = Column(String)
    usda_id = Column(String)

    __ts_vector__ = Column(TSVector(),Computed(
         "to_tsvector('english', ingredient_name)",
         persisted=True))

    __table_args__ = (Index('ix_video___ts_vector__',
          __ts_vector__, postgresql_using='gin'),)



class Products(Base):
    __tablename__ = "supermarket_products_current"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True)
    supermarket = Column(String)
    product_name = Column(String)
    product_url = Column(String)
    product_price_gbp = Column(Float)
    product_quantity = Column(Float)
    product_unit = Column(String)
    gbp_per_100g = Column(String)
    gbp_per_unit = Column(String)
    product_image = Column(String)
    date = Column(DateTime) 

    __ts_vector__ = Column(TSVector(),Computed(
         "to_tsvector('english', product_name || ' ' || supermarket)",
         persisted=True))

    __table_args__ = (Index('ix_video___ts_vector__',
          __ts_vector__, postgresql_using='gin'),)


class CommunityProducts(Base):
    __tablename__ = "community_products"

    product_id = Column(Integer, primary_key=True, index=True)
    supplier = Column(String)
    product_name = Column(String)
    product_url = Column(String)
    product_price = Column(Float)
    price_by_weight = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    product_image = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime) 

    owner = relationship("Users", back_populates="products")




# ALTER TABLE supermarket_products ADD COLUMN __ts_vector__ tsvector 
# GENERATED ALWAYS AS (to_tsvector('english', product_name || ' ' || supermarket)) STORED;