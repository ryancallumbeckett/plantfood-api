
from fastapi import FastAPI, Depends
import models
from database import engine
from routers import auth, users, ingredients, products, community_products


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ingredients.router)
app.include_router(products.router)
app.include_router(community_products.router)


