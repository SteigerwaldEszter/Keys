from apiflask import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class = Base)



auth = HTTPTokenAuth()