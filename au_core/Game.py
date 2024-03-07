"""
Game.py

Defines the ORM model `Game` representing a game of assassins.
Also implements most of the game logic as methods of this class.
"""

import random
import concurrent.futures
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped
from sqlalchemy import select, func, and_, or_, ScalarResult, ForeignKey
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

    # back-populated lists
    registrations: WriteOnlyMapped[List["Registration"]] = relationship(back_populates="game", passive_deletes=True)
    players: WriteOnlyMapped[List["Player"]] = relationship(back_populates="game", passive_deletes=True)
    events: WriteOnlyMapped[List["Event"]] = relationship(back_populates="game", passive_deletes=True)

    # TODO: `Game.has` method for verifying that an object is the child of a given game?

    #### game logic
    
    def delete(self):
        """
        Delete this game. Only allowed if game is not live!
        """
        session = self.session

        if not self.live:
            session.delete(self)
            #[session.delete(reg) for reg in session.scalars(self.registrations.select())]
            #[session.delete(player) for player in session.scalars(self.players.select())]
            #[session.delete(event) for event in session.scalars(self.events.select())]
        else:
            raise LiveGameError(f"Cannot delete game {self} as it is live.")

    startHook: PluginHook = PluginHook()
    def start(self):
        self.startHook._execute(self)
        # mark as live
        self.live = True
        self.started = datetime.now(timezone.utc)


    def generate_headlines(self) -> str:
        from .templates import env
        template = env.get_template("headlines.jinja")

        events = self.session.scalars(self.events.select().order_by(Event.datetimestamp))
        return template.render(events=events)

    def events_in_week(self, week_n: int) -> ScalarResult[Event]:
        """
        :param week_n: The week number to query events in.
        :return: The result of querying Event objects whose datetimestamp falls in week_n
        """
        d = self.started
        upper_bound = datetime(year=d.year, month=d.month, day=d.day) + timedelta(weeks=week_n)
        lower_bound = upper_bound - timedelta(weeks=1)

        return self.session.scalars( self.events.select().where(
            and_(lower_bound <= Event.datetimestamp, Event.datetimestamp < upper_bound)
        ))

    def generate_news_page(self, week_n) -> str:
        from .templates import env
        template = env.get_template("news.jinja")

        return template.render(events=self.events_in_week(week_n), week_n=week_n)

    def is_kill_licit(self, killer: Player, victim: Player):
        """
        Function to determine whether given kill is licit, self-defence notwithstanding.
        :param victim_id: Id of the Player who was killed
        :param killer_id: Id of the Player who made the kill
        :return: Whether the kill is licit.
        """
        session = self.session
        # TODO: abstract this into a plugin architecture
        if isinstance(killer, Assassin) and (victim in killer.targets or victim in killer.assassins):
            return True
        return False


class GameObject:
    """A 'mixin' class for defining classes for 'child' objects of games"""

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id = mapped_column(ForeignKey(Game.id))
    game: Mapped[Game] = relationship()