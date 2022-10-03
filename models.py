
from typing import Collection
from psycopg2 import Date
from sqlalchemy import Boolean, Column, Float, Integer, String, ForeignKey, DateTime, Index, Computed
from sqlalchemy.orm import relationship
from database import Base
from ts_vector import TSVector


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    products = relationship("CommunityProducts", back_populates="owner")


class Products(Base):
    __tablename__ = "supermarket_products_current"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True)
    supermarket = Column(String)
    product_name = Column(String)
    product_url = Column(String)
    product_price_gbp = Column(Float)
    product_quantity = Column(Float)
    product_unit = Column(String)
    gbp_per_100g = Column(String)
    gbp_per_unit = Column(String)
    product_image = Column(String)
    date = Column(DateTime) 

    __ts_vector__ = Column(TSVector(),Computed(
         "to_tsvector('english', product_name || ' ' || supermarket)",
         persisted=True))

    __table_args__ = (Index('ix_video___ts_vector__',
          __ts_vector__, postgresql_using='gin'),)


class CommunityProducts(Base):
    __tablename__ = "community_products"

    product_id = Column(Integer, primary_key=True, index=True)
    supplier = Column(String)
    product_name = Column(String)
    product_url = Column(String)
    product_price = Column(Float)
    price_by_weight = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    product_image = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime) 

    owner = relationship("Users", back_populates="products")




# ALTER TABLE supermarket_products ADD COLUMN __ts_vector__ tsvector 
# GENERATED ALWAYS AS (to_tsvector('english', product_name || ' ' || supermarket)) STORED;