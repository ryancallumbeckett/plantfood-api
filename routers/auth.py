
import sys 
sys.path.append("..")
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
import models
from sqlalchemy.orm import Session
from db import SessionLocal, engine
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets
from config import settings

SECRET_KEY = settings.secret_key
ALGORITHM =  settings.algorithm
ACCESS_TOKEN_EXPIRATION_TIME = settings.access_token_expiration_time


class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str
    public_channel: bool

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.username == username).first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user



def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):

    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_TIME)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)



async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        if username is None or user_id is None:
            raise user_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise user_exception()


@router.post("/create_user")
async def create_new_user(create_user: CreateUser, db: Session = Depends(get_db)):
    create_user_model = models.Users()
    user_id = secrets.token_hex(nbytes=16)
    create_user_model.id = user_id
    create_user_model.email = create_user.email
    create_user_model.username = create_user.username
    create_user_model.first_name = create_user.first_name
    create_user_model.last_name = create_user.last_name

    hash_password = get_password_hash(create_user.password)

    create_user_model.hashed_password =  hash_password
    create_user_model.is_active = True
    create_user_model.public_channel = create_user.public_channel

    db.add(create_user_model)

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


@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise token_exception()
    token_expires = timedelta(minutes=20)
    token = create_access_token(user.username, user.id, expires_delta=token_expires)
    return {"token": token}



#Exceptions
def user_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate" : "Bearer"}
    )
    return credentials_exception


def token_exception():
    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate" : "Bearer"}
    )
    return token_exception_response

