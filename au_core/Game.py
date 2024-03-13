"""
Game.py

Defines the ORM model `Game` representing a game of assassins.
Also implements most of the game logic as methods of this class.
"""

from typing import Optional, Union
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, backref
from sqlalchemy import ForeignKey, ScalarSelect
from .Base import Base, PluginHook
from .config import config
from datetime import datetime, timezone, timedelta
from warnings import warn

# setup for news pages generation from template


class LiveGameError(Exception):
    """
    Exception raised when an attempt is made to delete a live game.
    """

class Game(Base):
    """
    Represents a game of assassins,
    allowing multiple games to be stored in the same database and storing game settings.
    """
    __tablename__ = "games"
    # TODO: change this to a uuid to prevent conflicts?
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    # game state
    live: Mapped[bool] = mapped_column(default=False)
    # TODO: replace with a 'start event'
    #  -- i.e. the event that all the StateChanges that happen at the game start attach to
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
            self.deleteHook._execute(self)
        else:
            raise LiveGameError(f"Cannot delete game {self} as it is live.")

    startHook: PluginHook = PluginHook()
    def start(self):
        if self.started:
            raise LiveGameError("This game has already been started")

        now = datetime.utcnow()
        self.startHook._execute(self, now)
        # mark as live
        self.live = True
        self.started = datetime.now(timezone.utc)


class GameObject:
    """A mixin for objects associated to a particular Game"""

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey(Game.id), nullable=False)

    @declared_attr
    def game(self) -> Mapped[Game]:
        return relationship(Game)

    # this doesn't work because of some nonsense about MySQL not supporting multi-table delete
    def __init_subclass__(cls, **kwargs):
        """Make all GameObjects delete when orphaned"""
        """"@Game.deleteHook.register()
        def on_game_delete(game: Game):
            print("cascading " + cls.__name__)
            try:
                game.session.execute(cls.delete().filter_by(game_id=game.id))
            except Exception as e:
                print(f"failed cascade due to {e.__class__.__name__}: {e}")"""


class StateChange(Base):
    """
    An abstract model for state changes occurring in a game, e.g. deaths, target assignment, etc.
    Currently, this has a datestamp for when it occurred,
    but I intend to instead have state changes "attach" to Event objects.
    """
    __abstract__ = True
    when: Mapped[datetime]

class TempStateChange(StateChange):
    """
    An abstract extension of StateChange for events for states that only apply for a limited time,
    such as going wanted, or police death.
    """
    __abstract__ = True
    expires: Mapped[Optional[datetime]]

    @classmethod
    def exists_including(cls, dt: datetime, *whereclause, **filter_by) -> ScalarSelect:
        return (cls.select().where(cls.when <= dt,
                                   ((cls.expires.is_(None)) | (cls.expires > dt)),
                                   *whereclause)
                .filter_by(**filter_by)).exists()