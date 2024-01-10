"""
Player.py

Defines the Player class, which represents the instance of a player in a game,
and which the Assassin and Police classes inherit from as "types" of players.
"""

from typing import List
from .Base import Base
from .Registration import Registration
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKeyConstraint, ForeignKey

# TODO: uniqueness constraint on reg_id + type? I.e. only one instance of each TYPE of player per person
class Player(Base):
    """
    Player class

    Represents an instance of a generic player in a game.
    This is specialised into Assassins (Full Players) and Police using joined table inheritance.

    The reason for this class is to have an umbrella player type for Pseudonyms to point to as their owner.
    The reason they do not point simply to the initial Registration is,
    when someone dies as a Full Player and signs up as Police,
    the pseudonyms should be kept separate.
    """

    __tablename__ = "players"
    __table_args__ = (ForeignKeyConstraint(["reg_id", "game_id"], [Registration.id, Registration.game_id]),)

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]

    reg_id: Mapped[int] = mapped_column(ForeignKey(Registration.id))
    game_id: Mapped[int] = mapped_column(ForeignKey(Registration.game_id))

    reg: Mapped[Registration] = relationship(foreign_keys=[reg_id, game_id])

    pseudonyms: Mapped[List["Pseudonym"]] = relationship(back_populates="owner",foreign_keys="[Pseudonym.owner_id]")

    __mapper_args__ = {
        "polymorphic_identity": "player",
        "polymorphic_on": "type",
    }
