
import sys 
sys.path.append("..")

from fastapi import Depends, HTTPException, APIRouter
import models
from db import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from routers.auth import get_current_user, user_exception
from .auth import get_current_user, user_exception, get_password_hash, verify_password

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str


@router.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Users).all()


@router.get("/user/{user_id}")
async def read_user_query(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_model is not None:
        return user_model
    raise 'Ivalid user_id'


@router.get("/user")
async def read_user_parameter(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
    print(user_model.username)
    if user_model is not None:
        return user_model
    raise 'Ivalid user_id'


@router.put("/user/password")
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

 


@router.delete("/user")
async def delete_user(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if current_user is None:
        raise user_exception()
    
    user_model = db.query(models.Users).filter(models.Users.id == current_user.get("id")).first()

    if user_model is None:
        raise "Invalid user or request"

    db.query(models.Users).filter(models.Users.id == current_user.get("id")).delete()
    db.commit()

    return "Delete successful"



def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction' : 'successful'
    }

def http_exception():
    return HTTPException(status_code=404, detail='Item not found')



