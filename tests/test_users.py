from .database import client, session

def test_root(client, session):
    res = client.get("/")
    assert res.json().get('message') == "Hello World"
    assert res.status_code == 200


new_user = {
  "username": "Test User 4",
  "email": "test_user4@testuser.com",
  "first_name": "Test",
  "last_name": "User",
  "password": "password",
  "public_channel": True
}


def test_create_user(client, session):
    res = client.post("/users/create_user/", json=new_user)
    print(res.json())
    assert res.status_code == 201


