
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expiration_time: int
    mongo_username: str
    mongo_password: str

    class Config:
        env_file = ".env"

settings = Settings()
