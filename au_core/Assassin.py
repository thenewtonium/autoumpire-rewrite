"""
Assassin.py

Defines the ORM model `Assassin` representing the instance of an assassin in a game.
An 'assassin' here means a full player -- i.e. a player with targets and a competence deadline.
"""

from typing import List
from .Player import Player
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class Assassin(Player):
    """
    Assassin class
    """

    __tablename__ = "assassins"

    alive: Mapped[bool] = mapped_column(default=True)
    competence_deadline: Mapped[datetime]

    targets: Mapped[List["Assassin"]] = relationship(secondary="targetting_table",
                                                     primaryjoin="Assassin.id==TargRel.assassin_id",
                                                     secondaryjoin="Assassin.id==TargRel.target_id")
    assassins: Mapped[List["Assassin"]] = relationship(overlaps="targets",
                                                       secondary="taretting_table",
                                                       primaryjoin="Assassin.id==TargRel.target_id")

    __mapper_args__ = {
        "polymorphic_identity": "assassin", # sets Player.type for objects of this class to "assassin"
    }
