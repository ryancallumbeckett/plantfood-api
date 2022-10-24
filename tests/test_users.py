
from jose import jwt
import schemas
from config import settings
from tests.dummy_data import new_user
import pytest


def test_create_user(client):
    result = client.post("/users/create_user/", json=new_user)
    user = schemas.UserBase(**result.json())
    assert user.email == "correct.email@correct.com"
    assert result.status_code == 201


def test_login(client, test_user):
    login = client.post("/auth/login/", data={"username": test_user["username"], "password": test_user["password"]})
    print(login.json())
    login_result = schemas.Token(**login.json())
    payload = jwt.decode(login_result.token, settings.secret_key, algorithms=settings.algorithm)
    username = payload.get("sub")
    assert username == test_user["username"]
    assert login.status_code == 200


@pytest.mark.parametrize("email, password, status_code", [
    ("wrongemail@gmail.com", "password1234", 401),
    ("correct.email@correct.com", "wrongpassword", 401),
    ("wrong.email@gmail.com", "wrongpassword", 401),
    (None, "password1234", 401),
    ("correct.email@correct.com", None, 401),
])
def test_incorrect_login(client, test_user, email, password, status_code):
    login = client.post("/auth/login/", data={"username": test_user["username"], "password": "an incorrect password"})
    assert login.status_code == status_code


