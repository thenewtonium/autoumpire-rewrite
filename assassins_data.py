# This file defines the ORM classes through which AutoUmpire interacts with database tables.
# This avoids faffing about as much with database transactions,
# as SQLAlchemy sorts things out behind the scenes.
# It also makes it more readable for people familiar with Python.

from typing import List, Union
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import create_engine, String, ForeignKey, select, Column, Table
from enum import Enum
from email_validator import validate_email, EmailNotValidError


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
    _email: Mapped[str] = mapped_column(unique=True)
    realname: Mapped[str]
    address: Mapped[str]
    college: Mapped[str]
    _water: Mapped[WaterStatus]
    notes: Mapped[str] = mapped_column(default="")
    initial_pseudonym: Mapped[str] = mapped_column(unique=True)
    # seed: Optional[Mapped[int]] # will omit for now
    instances: Mapped[List[Union["Assassin"]]] = relationship(back_populates="player")

    # email property - setter enforces valid email -- will change this!!
    @property
    def email(self) -> Mapped[str]:
        return self._email

    @email.setter
    def email(self, value):
        cd = config["check_email_deliverability"]
        try:
            emailinfo = validate_email(value, check_deliverability=cd)
            value = emailinfo.normalized
        # if email invalid, first assume a crsID was given,
        # so try to validate again with @cam.ac.uk appended
        except EmailNotValidError as e:
            attempt = value + "@" + config["default_email_domain"]
            try:
                emailinfo = validate_email(attempt, check_deliverability=cd)
                value = emailinfo.normalized
            except: # if assuming CRSid doesn't work then raise original error
                raise e
        self._email = value

    # WaterStatus property - setter enforces Enum value -- will change this!!
    @property
    def water(self) -> Mapped[WaterStatus]:
        return self._water

    @water.setter
    def water(self, value):
        self._water = WaterStatus(value)

    def __repr__(self) -> str:
        return f"{self.realname}, {self.email}, {self.initial_pseudonym}, {self.college}, {self.address}, {self.water.value}, {self.notes}"


targetting_table = Table(
    "targetting_table",
    Base.metadata,
    Column("target_id", ForeignKey("assassins.id"), primary_key=True),
    Column("assassin_id", ForeignKey("assassins.id"), primary_key=True),
)


# Assassin class:
# This stores active players
class Assassin(Base):
    __tablename__ = "assassins"
    id = mapped_column(ForeignKey(Player.id), primary_key=True)
    player: Mapped["Player"] = relationship(back_populates="instances")
    # when a player dies, we don't delete them from the database but just set this to false
    # or maybe we do want to move?
    alive: Mapped[bool] = mapped_column(default=True)

    pseudonyms: Mapped[List["Pseudonym"]] = relationship(back_populates="owner")

    targets: Mapped[List["Assassin"]] = relationship(secondary=targetting_table,
                                                     primaryjoin="Assassin.id==targetting_table.c.assassin_id",
                                                     secondaryjoin="Assassin.id==targetting_table.c.target_id")
    assassins: Mapped[List["Assassin"]] = relationship(secondary=targetting_table,
                                                       primaryjoin="Assassin.id==targetting_table.c.target_id",
                                                       secondaryjoin="Assassin.id==targetting_table.c.assassin_id")

    def __repr__(self) -> str:
        return (f"player=({self.player}), pseudonyms=({self.pseudonyms}), "
                f"targets=({[t.player.realname for t in self.targets]}), "
                f"assassins=({[a.player.realname for a in self.assassins]}), "
                f"alive={self.alive}")


# Pseudonym class:
# This stores pseudonyms, ensuring uniqueness
class Pseudonym(Base):
    __tablename__ = "pseudonyms"
    id: Mapped[int] = mapped_column(primary_key=True)  # reduce database size by referring using id
    text: Mapped[str] = mapped_column(unique=True)
    owner_id = mapped_column(ForeignKey(Assassin.id))
    owner: Mapped[Union["Assassin"]] = relationship(back_populates="pseudonyms")

    def __repr__(self) -> str:
        return f"{self.text} ({self.owner.player.realname})"


##########DATABASE SETUP########

# load config file and generate engine from database address
# anything importing this module will be able to access both of these under
# `assassins_data.config` and `assassins_data.engine`.
import json

defaults = {
    "verbose": True,
    "n_targs": 3,
    "check_email_deliverability": True
}

try:
    # load config file
    with open('config.json') as f:
        config = json.load(f)

    for c in defaults.keys():
        if c not in config.keys():
            config[c] = defaults[c]

    try:
        engine = create_engine(config["db_address"], echo=config["verbose"])
        # register table metadata based on ORM models above
        Base.metadata.create_all(engine)
    except BaseException as e:
        print("Error whilest trying to create database engine. Is db_address in config.json correct?")
except BaseException as e:
    raise Exception("Error whilest trying to load config.json. Does this file exist?")
