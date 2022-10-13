
from fastapi import FastAPI
import models
from db import engine
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, posts, users, recipes, ingredients, products


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(recipes.router)
app.include_router(ingredients.router)
app.include_router(products.router)
app.include_router(posts.router)


@app.get("/")
def root():
    return {"message" : "Hello World"}