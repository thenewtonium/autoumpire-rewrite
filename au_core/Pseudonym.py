"""
Pseudonym.py

Defines the `Pseudonym` class.
"""

from typing import Union
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKey, UniqueConstraint, ForeignKeyConstraint
from .Base import Base
from .enums import PseudonymColour
from .Assassin import Assassin

class Pseudonym(Base):
    """
    Pseudonym class

    This represents a pseudonym.
    A UNIQUE constraint is imposed on the composite (game_id, text) so that
    """

    __tablename__ = "pseudonyms"
    __table_args__ = (UniqueConstraint("game_id","text"),
                      ForeignKeyConstraint(["game_id","owner_id"],[Assassin.game_id,Assassin.id]))

    id: Mapped[int] = mapped_column(primary_key=True)  # reduce database size by referring using id

    # Note that game_id and text form a composite uniqueness constraint
    # (this is defined in __table_args__)
    game_id: Mapped
    text: Mapped[str]

    colour: Mapped[PseudonymColour]

    owner_id: Mapped
    owner: Mapped[Union["Assassin"]] = relationship(back_populates="pseudonyms")
