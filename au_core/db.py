"""
db.py

Creates the database engine used by autoumpire.
This is in its own file so that it can be imported by the modules defining each of the ORM models.
"""

import os
from .config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

cwd = os.getcwd()
os.chdir(os.path.dirname( os.path.abspath(__file__)))
engine = create_engine(config["db_address"], echo=config["verbose"])
os.chdir(cwd)

Session = sessionmaker(engine)