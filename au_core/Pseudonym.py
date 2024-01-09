"""
Pseudonym.py

Defines the `Pseudonym` class.
"""

from typing import Union
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKey, UniqueConstraint, ForeignKeyConstraint
from .Base import Base
from .enums import PseudonymColour
from .Player import Player

class Pseudonym(Base):
    """
    Pseudonym class

    This represents a pseudonym.
    A UNIQUE constraint is imposed on the composite (game_id, text) so that each pseudonyn us unique per game.
    """

    __tablename__ = "pseudonyms"
    __table_args__ = (UniqueConstraint("game_id","text"),
                      ForeignKeyConstraint(["game_id","owner_id"],[Player.game_id,Player.id]))

    id: Mapped[int] = mapped_column(primary_key=True)  # reduce database size by referring using id

    # Note that game_id and text form a composite uniqueness constraint
    # (this is defined in __table_args__)
    game_id: Mapped # foreign key Player.game_id (see __table_args__)
    text: Mapped[str]

    colour: Mapped[PseudonymColour]

    owner_id: Mapped # foreign key Player.id (see __table_args__)
    owner: Mapped[Player] = relationship(back_populates="pseudonyms")
