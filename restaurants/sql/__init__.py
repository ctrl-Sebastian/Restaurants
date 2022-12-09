import sys
from sqlalchemy import create_engine, asc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///restaurants.db', connect_args={"check_same_thread": False})

"Bind"
DBSession = sessionmaker(bind=engine)
cursor = DBSession()

from restaurants.sql.models import Restaurant, Menu, User