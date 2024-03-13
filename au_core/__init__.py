"""
au_core

This module implements the core logic of AutoUmpire.
"""

from .config import config
from . import db

# ORM class imports
from .Base import Base
from .Game import Game
from .Player import Player
from .Assassin import Assassin
from .Police import Police
from . import targetting
from .Pseudonym import Pseudonym
from .Event import Event
from .Report import Report
from .Death import Death
from . import competency

# registers tables for all the ORM models derived from Base
Base.metadata.create_all(db.engine)

class GameNotFoundError(Exception):
    """
    Exception raised when trying to fetch a game but the game is not found
    """