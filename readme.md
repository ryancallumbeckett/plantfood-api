Start app:
uvicorn main:app --reload 

Swagger UI:
http://127.0.0.1:8000/docs

OpenAPI Schema:
http://127.0.0.1:8000/openapi.json

Decode JWT Token:
http://jwt.io

Alembic:
SQL Alchemy database location is in ini file

Create revision version = alembic revision -m [task_name]
This creates a file in the versions folder with the task name

Upgrade =  alembic upgrade [revision_number]

Downgrade = alembic downgrade [-1]

Push to heroku:
git push heroku HEAD:master

Change