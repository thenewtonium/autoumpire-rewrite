"""
db.py

Creates the database engine used by autoumpire.
This is in its own file so that it can be imported by the modules defining each of the ORM models.
"""

import os
from .config import config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

cwd = os.getcwd()
os.chdir(os.path.dirname( os.path.abspath(__file__)))
engine = create_engine(config["db_address"], echo=config["verbose"])
os.chdir(cwd)

""""# this enables foreign keys when using SQLite
# so that delete cascades work correctly
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()"""

Session = sessionmaker(engine)