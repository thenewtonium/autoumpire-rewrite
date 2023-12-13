"""
db.py

Creates the database engine used by autoumpire.
This is in its own file so that it can be imported by the modules defining each of the ORM models.
"""

from .config import config
from sqlalchemy import create_engine

db = create_engine(config["db_address"], echo=config["verbose"])