# This file defines the ORM classes through which AutoUmpire interacts with database tables.
# This avoids faffing about as much with database transactions,
# as SQLAlchemy sorts things out behind the scenes.
# It also makes it more readable for people familiar with Python.

from typing import List, Union
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import create_engine, String, ForeignKey, select, Column, Table
from enum import Enum
from email_validator import validate_email, EmailNotValidError
from datetime import datetime


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

    def __repr__(self) -> str:
        return self.value


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

# TargRel class:
# short for "targetting relation"
# -- corresponds to a table storing who is targetting who
class TargRel(Base):
    __tablename__ = "targetting_table"
    target_id = mapped_column(ForeignKey(f"assassins.id"), primary_key=True)
    target: Mapped["Assassin"] = relationship(foreign_keys=[target_id])

    assassin_id = mapped_column(ForeignKey("assassins.id"), primary_key=True)
    assassin: Mapped["Assassin"] = relationship(foreign_keys=[assassin_id])

    def __repr__(self) -> str:
        return f"{self.assassin.player.realname} targetting {self.target.player.realname}"

# Assassin class:
# This stores active players
class Assassin(Base):
    __tablename__ = "assassins"
    id = mapped_column(ForeignKey(Player.id), primary_key=True)
    player: Mapped["Player"] = relationship(back_populates="instances")
    alive: Mapped[bool] = mapped_column(default=True)
    competence_deadline: Mapped[datetime]
    pseudonyms: Mapped[List["Pseudonym"]] = relationship(back_populates="owner")

    targets: Mapped[List["Assassin"]] = relationship(secondary=TargRel.__tablename__,
                                                     primaryjoin="Assassin.id==TargRel.assassin_id",
                                                     secondaryjoin="Assassin.id==TargRel.target_id")
    assassins: Mapped[List["Assassin"]] = relationship(overlaps="targets",
                                                       secondary=TargRel.__tablename__,
                                                       primaryjoin="Assassin.id==TargRel.target_id",
                                                       secondaryjoin="Assassin.id==TargRel.assassin_id")

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
    "check_email_deliverability": True,
    "initial_competence": 7,
    "locale": "en_GB"
}

try:
    # load config file
    with open('au_core/config.json') as f:
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
