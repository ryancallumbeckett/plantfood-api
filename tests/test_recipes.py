from jose import jwt
import schemas
from config import settings
from tests.dummy_data import new_user
import pytest


def test_root(client):
    result = client.get("/")
    assert result.status_code == 200

# def test_search_recipes(client):
#     result = client.get("/recipes/search_by_title/burger")
#     assert result.status_code == 200
    
# def test_search_recipes_2(client):
#     result = client.get("/recipes/search_by_title/pad")
#     assert result.status_code == 200
    

