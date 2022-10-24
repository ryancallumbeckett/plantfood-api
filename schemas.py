from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class CreateUser(UserBase):
    password: str
    public_channel: bool

    class Config:
        orm_mode = True


class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str


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


class Token(BaseModel):
    token: str