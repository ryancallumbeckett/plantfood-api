
import sys 
sys.path.append("..")
from routers.oauth2 import get_current_user, user_exception
from .oauth2 import get_current_user, user_exception, get_password_hash, verify_password
from fastapi import Depends, HTTPException, APIRouter, status
from schemas import CreateUser, UserVerification
from db import engine, get_db
from sqlalchemy.orm import Session
import secrets
import models


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

# models.Base.metadata.create_all(bind=engine)


@router.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Users).all()


@router.get("/user/{user_id}")
async def read_user_query(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_model is not None:
        return user_model
    raise 'Ivalid user_id'


@router.get("/user/")
async def read_user_parameter(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
    print(user_model.username)
    if user_model is not None:
        return user_model
    raise 'Ivalid user_id'


@router.put("/user/update_password/")
async def update_password(user_verification: UserVerification, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if current_user is None:
        raise user_exception()
  
    user_model = db.query(models.Users).filter(models.Users.id == current_user.get("id")).first()

    if user_model is not None:
        if user_verification.username == user_model.username and verify_password(user_verification.password, user_model.hashed_password):
            user_model.hashed_password = get_password_hash(user_verification.new_password)

        db.add(user_model)
        db.commit()

        return 'Successful'
    return 'Invalid user or request'

 


@router.delete("/user/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if current_user is None:
        raise user_exception()
    
    user_model = db.query(models.Users).filter(models.Users.id == current_user.get("id")).first()

    if user_model is None:
        raise "Invalid user or request"

    db.query(models.Users).filter(user_id == current_user.get("id")).delete()
    db.commit()

    return "Delete successful"



@router.post("/create_user/", status_code=status.HTTP_201_CREATED)
async def create_new_user(create_user: CreateUser, db: Session = Depends(get_db)):
    new_user = models.Users()
    user_id = secrets.token_hex(nbytes=16)
    new_user.id = user_id
    new_user.email = create_user.email
    new_user.username = create_user.username
    new_user.first_name = create_user.first_name
    new_user.last_name = create_user.last_name

    hash_password = get_password_hash(create_user.password)

    new_user.hashed_password =  hash_password
    new_user.is_active = True
    new_user.public_channel = create_user.public_channel

    db.add(new_user)

    if create_user.public_channel is True:
    
        create_channel_model = models.Channels()
        channel_name = create_user.username
        create_channel_model.id = user_id
        create_channel_model.channel_name = channel_name
        create_channel_model.channel_path = channel_name.replace(" ", "-").lower()
        create_channel_model.recipe_count = 0
        create_channel_model.website = None
        create_channel_model.facebook = None
        create_channel_model.instagram = None
        create_channel_model.youtube = None
        create_channel_model.user_id = user_id

        db.add(create_channel_model)
    
    db.commit()

    return "User created successfully"



def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction' : 'successful'
    }

def http_exception():
    return HTTPException(status_code=404, detail='Item not found')



