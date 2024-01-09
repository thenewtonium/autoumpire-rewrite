"""
Police.py

Defines the ORM model `Police` representing the instance of a player who is Police in the game.
"""

from .Player import Player
from sqlalchemy.orm import Mapped

class Police(Player):
    """
    Police class

    Represents an instance of a Police player in the game.
    The only additional data from the base Player class is the rank to be displayed on the police page.
    """

    __tablename__ = "police"

    # TODO: deal with rank properly, including options for thematic rank names
    rank: Mapped[str]

    # TODO: Corrupt police to be implemented by a separate table
    # TODO: death time, for notifying a player when they have respawned?

    __mapper_args__ = {
        "polymorphic_identity": "police", # sets Player.type for objects of this class to "police"
    }
