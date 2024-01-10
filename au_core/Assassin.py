"""
Assassin.py

Defines the ORM model `Assassin` representing the instance of an assassin in a game.
An 'assassin' here means a full player -- i.e. a player with targets and a competence deadline.
"""

from typing import List, Optional
from .Player import Player
from .TargRel import TargRel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class Assassin(Player):
    """
    Assassin class
    """

    __tablename__ = "assassins"
    id = mapped_column(ForeignKey(Player.id), primary_key=True)

    alive: Mapped[bool] = mapped_column(default=True)
    competence_deadline: Mapped[Optional[datetime]]

    targets: Mapped[List["Assassin"]] = relationship(secondary=TargRel.__tablename__,
                                                     primaryjoin="Assassin.id==TargRel.assassin_id",
                                                     secondaryjoin="Assassin.id==TargRel.target_id")
    assassins: Mapped[List["Assassin"]] = relationship(overlaps="targets",
                                                       secondary=TargRel.__tablename__,
                                                       primaryjoin="Assassin.id==TargRel.target_id",
                                                       secondaryjoin="Assassin.id==TargRel.assassin_id")

    __mapper_args__ = {
        "polymorphic_identity": "assassin", # sets Player.type for objects of this class to "assassin"
    }
