"""
Game.py

Defines the ORM model `Game` representing a game of assassins.
Also implements most of the game logic as methods of this class.
"""

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from sqlalchemy import ForeignKey
from .Base import Base, PluginHook
from .config import config
from datetime import datetime, timezone, timedelta

# setup for news pages generation from template


class LiveGameError(Exception):
    """
    Exception raised when an attempt is made to delete a live game.
    """

class Game(Base):
    """
    Settings are:
        n_targs             -   The number of targets each assassin should be assigned. Defaults to 3.
        initial_competence  -   The length of time until assassins go incompetent from the start of the game.
                                Defaults to 7 days.
        locale              -   The locale that should be used for generating emails.
                                This basically only affects datetime formatting.
                                Defaults to "en_GB".
    Defaults are taken from `au_core/config.json`; the defaults above are the default config values.
    """
    __tablename__ = "games"
    # TODO: change this to a uuid to prevent conflicts
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    # game state
    live: Mapped[bool] = mapped_column(default=False)
    started: Mapped[Optional[datetime]]

    # settings
    n_targs: Mapped[int] = mapped_column(default=config["n_targs"])
    initial_competence: Mapped[timedelta] = mapped_column(default=timedelta(days=config["initial_competence"]))
    locale: Mapped[str] = mapped_column(default=config["locale"])

    #### game logic
    def has(self, obj) -> bool:#: GameObject) -> bool:
        return obj.game_id == self.id

    deleteHook: PluginHook = PluginHook()
    def delete(self):
        """
        Delete this game. Only allowed if game is not live!
        """
        if not self.live:
            self.session.delete(self)
            self.deleteHook._execute()
        else:
            raise LiveGameError(f"Cannot delete game {self} as it is live.")

    startHook: PluginHook = PluginHook()
    def start(self):
        self.startHook._execute(self)
        # mark as live
        self.live = True
        self.started = datetime.now(timezone.utc)

class GameObject:
    """A 'mixin' class for defining classes for 'child' objects of games"""

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id = mapped_column(ForeignKey(Game.id))

    @declared_attr
    def game(self) -> Mapped[Game]:
        return relationship(Game)