"""
Assassin.py

Defines the ORM model `Assassin` representing the instance of an assassin in a game.
An 'assassin' here means a full player -- i.e. a player with targets.
"""

from typing import List
from .Base import Base
from .Registration import Registration
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKeyConstraint
from datetime import datetime

class Assassin(Base):
    """
    Assassin class
    """

    __tablename__ = "assassins"
    __table_args__ = (ForeignKeyConstraint(["id, game_id"], [Registration.id, Registration.game_id]))

    # Each assassin is keyed by the initial registration,
    # which is used to access identifying information.
    id = mapped_column(primary_key=True)
    registration: Mapped[Registration] = relationship()

    game_id: Mapped
    game: Mapped["Game"] = relationship()

    alive: Mapped[bool] = mapped_column(default=True)
    competence_deadline: Mapped[datetime]

    pseudonyms: Mapped[List["Pseudonym"]] = relationship(back_populates="owner")

    targets: Mapped[List["Assassin"]] = relationship(secondary="targetting_table",
                                                     primaryjoin="Assassin.id==TargRel.assassin_id",
                                                     secondaryjoin="Assassin.id==TargRel.target_id")
    assassins: Mapped[List["Assassin"]] = relationship(overlaps="targets",
                                                       secondary="taretting_table",
                                                       primaryjoin="Assassin.id==TargRel.target_id",
