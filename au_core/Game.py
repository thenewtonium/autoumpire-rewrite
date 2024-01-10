"""
Game.py

Defines the ORM model `Game` representing a game of assassins.
Also implements most of the game logic as methods of this class.
"""

from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from .enums import RegType
from .Base import Base
from .Registration import Registration
from .Player import Player
from .Assassin import Assassin
from .Police import Police
from .Pseudonym import Pseudonym
from .config import config
from datetime import timedelta

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
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    # game state
    live: Mapped[bool] = mapped_column(default=False)

    # settings
    n_targs: Mapped[int] = mapped_column(default=config["n_targs"])
    initial_competence: Mapped[timedelta] = mapped_column(default=timedelta(days=config["initial_competence"]))
    locale: Mapped[str] = mapped_column(default=config["locale"])

    # back-populated lists
    registrations: Mapped[List["Registration"]] = relationship(back_populates="game")

    #def __repr__(self) -> str:
    #    return f"Game(id={self.id},name={self.name},live={self.live})"

    # game logic
    
    def delete(self):
        """
        Delete this game. Only allowed if game is not live!
        """
        session = self.session

        if not self.live:
            session.delete(self)
            # delete orphaned registrations
            for reg in self.registrations:
                session.delete(reg)

            #session.commit()
        else:
            raise LiveGameError(f"Cannot delete game {self} as it is live.")

    def add_player_from_reg(self, registration: Registration) -> Player:
        session = self.session # self.session is actually a function call, so we only want to call this once
        registration.game = self
        registration.validate_w_session(session)

        # set constructor based on the type in the registration
        constructor = Player
        if registration.type == RegType.FULL:
            constructor = Assassin
        elif registration.type == RegType.POLICE:
            constructor = Police

        newplayer = constructor(reg=registration)#, game_id=self.id)
        newpseudonym = Pseudonym(owner=newplayer, text=registration.initial_pseudonym)
        session.add(newplayer)
        session.add(newpseudonym)

        return newplayer


    # TODO: perhaps remove this
    def add_registration(self, **info) -> Registration:
        """
        Register a player in the game, validating the data.

        :param info: Keyword arguments are passed into the constructor for the Registration
        :return: The Registration of the player just registered.
        """
        session = self.session

        newreg = Registration(game=self, **info)
        newreg.validate_w_session(session)
        session.add(newreg)
        #session.commit()

        return newreg
