"""
Police.py

Defines the ORM model `Police` representing the instance of a player who is Police in the game.
"""

from .Player import Player
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class Police(Player):
    """
    Police class

    Represents an instance of a Police player in the game.
    The only additional data from the base Player class is the rank to be displayed on the police page.
    """

    __tablename__ = "police"
    id = mapped_column(ForeignKey(Player.id), primary_key=True)

    # TODO: deal with rank properly, including options for thematic rank names
    rank: Mapped[str] = mapped_column(default="")

    # TODO: Corrupt police to be implemented by a separate table
    # TODO: death time, for notifying a player when they have respawned?

    __mapper_args__ = {
        "polymorphic_identity": "police", # sets Player.type for objects of this class to "police"
    }
