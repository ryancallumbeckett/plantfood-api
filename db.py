from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from configparser import ConfigParser

config = ConfigParser()
config.read('./config.cfg')

SQLALCHEMY_DATABASE_URL = f"postgresql://{config['POSTGRES']['username']}:{config['POSTGRES']['password']}@{config['POSTGRES']['host']}/{config['POSTGRES']['database']}"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

