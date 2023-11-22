# This file defines the ORM classes through which AutoUmpire interacts with database tables.
# This avoids faffing about as much with database transactions,
# as SQLAlchemy sorts things out behind the scenes.
# It also makes it more readable for people familiar with Python.
# It also defines a function to get a database engine for the address in config.json.

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import create_engine, String, ForeignKey, select
from enum import Enum

# load config file and generate engine from database address
# anything importing this module will be able to access both of these under
# `assassins_data.config` and `assassins_data.engine`.
import json
try:
    with open('config.json') as f:
        config = json.load(f)
except BaseException as e:
    raise Exception("Error whilest trying to load config.json. Does this file exist?")
try:
    engine = create_engine(config["db_address"], echo=True)
except BaseException as e:
    print("Error whilest trying to create database engine. Is db_address in config.json correct?")

#####DATABASE ORM MODELS######

# Base class which models inherit from.
# This is what the documentation said you have to do.
class Base(DeclarativeBase):
    pass

# water status enum type
class WaterStatus(Enum):
    FULL = "Full Water"
    CARE = "Water With Care"
    NO = "No Water"

# Player class:
# This stores initial signup data
class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    realname: Mapped[str]
    address: Mapped[str]
    college: Mapped[str]
    water: Mapped[WaterStatus]
    notes: Mapped[str]
    initial_pseudonym: Mapped[str]
    #seed: Optional[Mapped[int]] # will omit for now


