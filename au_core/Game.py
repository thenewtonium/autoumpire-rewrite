"""
Game.py

Defines the ORM model `Game` representing a game of assassins.
Also implements most of the game logic as methods of this class.
"""

import random
import concurrent.futures
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped
from sqlalchemy import select, func, and_, or_
from .enums import RegType
from .Base import Base
from .Registration import Registration
from .Player import Player
from .Assassin import Assassin
from .Police import Police
from .Pseudonym import Pseudonym
from .TargRel import TargRel
from .config import config
from datetime import datetime, timezone, timedelta
from warnings import warn

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
    registrations: WriteOnlyMapped[List["Registration"]] = relationship(back_populates="game")
    players: WriteOnlyMapped[List["Player"]] = relationship(back_populates="game")
    assassins: WriteOnlyMapped[List["Assassin"]] = relationship(back_populates="game", overlaps="players")

    events: WriteOnlyMapped[List["Event"]] = relationship(back_populates="game")

    #### game logic
    
    def delete(self):
        """
        Delete this game. Only allowed if game is not live!
        """
        session = self.session

        if not self.live:
            session.delete(self)
            # TODO: set relationship to delete orphans automatically
            # delete orphaned registrations
            for reg in self.registrations:
                session.delete(reg)

            #session.commit()
        else:
            raise LiveGameError(f"Cannot delete game {self} as it is live.")

    # TODO: when Registration and Player merged, replace with add_player
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

        newplayer = constructor(reg=registration, game=self)
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

    def _assign_targets_one_pass(self) -> bool:
        """
        One pass of the target-assignment algorithm. This will be repeated until it returns `False`
        :return: bool value of whether this function should be called again.
        """
        session = self.session # only fetch this once...

        # subquery which counts the number of targets a given assassin has
        count_targs = (
            select(func.count(TargRel.assassin_id))
                .where(TargRel.assassin_id == Assassin.id)
                .scalar_subquery()
        )
        # subquery which counts the number of assassins a given assassin has
        count_asses = (
            select(func.count(TargRel.assassin_id))
                .where(TargRel.target_id == Assassin.id)
                .scalar_subquery()
        )

        # TODO: use WriteOnlyCollection `assassins` to generate query
        # fetch all alive assassins in this game with fewer than `n_targs` targets
        need_targs = session.scalars(select(Assassin.id)
                                     .filter_by(alive=True, game_id=self.id)
                                     .where(count_targs < self.n_targs)
                                     )
        # queries all alive assassins in this game with fewer than `n_targs` assassins,
        # then turns this into a list so that we can call random.choice on it
        need_asses = list(session.scalars(select(Assassin.id)
                                          .filter_by(alive=True)
                                          .where(count_asses < self.n_targs)
                                          ).fetchall())

        #cont = False # whether to continue - will be set to True later iff need_targs is nonempty
        # TODO: make this require girth-3
        # TODO: also, have temporary store of problematic choices so that we don't keep picking them
        to_add = []
        for a in need_targs:
            #cont = True
            ok = False
            while not ok:
                # choose a target from the assassins who have an insufficient number targetting them
                t = random.choice(need_asses)
                # disallow self-targetting
                if t == a:
                    continue
                # check if `a` and `t` already have a targetting relation, in either direction
                # in which case disallow `t` as a choice of target
                res = session.scalars(select(TargRel)
                                      .where(
                    or_(
                        and_(TargRel.assassin_id == a, TargRel.target_id == t),
                        and_(TargRel.assassin_id == t, TargRel.target_id == a)
                    )
                                        )
                ).one_or_none()
                if res is not None:
                    continue
                ok = True
                break
            # set `a` to target `t` now that it has been verified as ok
            to_add.append(TargRel(assassin_id=a, target_id=t))
            need_asses.remove(t)

        session.add_all(to_add)
        return (len(to_add) > 0)

    def assign_targets(self):
        """
        Assigns targets to assassins in this game who have fewer than the number of targets required by the game settings (`n_targs`),
        choosing randomly from the assassins who have fewer than the requisite number of people targetting them.
        Currently, reflexive and symmetric targetting relations are forbidden,
        but the "girth > 3" requirement of the original AutoUmpire is not yet implemented.
        """
        while self._assign_targets_one_pass():
            pass

    def start(self):
        """
        Starts the game of assassins -- i.e. gives initial competence, and assigns initial targets.
        Does not email players, in case of mistake -- the Game.send_updates method should be invoked seperately for this.
        """
        session = self.session
        assassins = session.scalars(select(Assassin).filter_by(game_id=self.id))

        # CONCURRENTLY set initial competence
        # TODO: use sqlalchemy insert?
        inital_deadline = datetime.now(timezone.utc) + self.initial_competence
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(lambda a: setattr(a, "competence_deadline", inital_deadline), assassins)

        # assign initial targets
        self.assign_targets()

        # mark as live
        self.live = True

    def send_updates(self, message: str = ""):
        """
        :param message: The message body to send along with the updates.
        """
        session = self.session

        # fetch alive assassins in the game
        assassins = session.scalars(self.assassins.select().filter_by(alive=True))

        # concurrently call the send_update method of each live assassin
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(lambda a: a.send_update(message), assassins)

