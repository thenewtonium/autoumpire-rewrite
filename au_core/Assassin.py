"""
Assassin.py

Defines the ORM model `Assassin` representing the instance of an assassin in a game.
An 'assassin' here means a full player -- i.e. a player with targets and a competence deadline.
"""

import random
import concurrent.futures
from typing import List, Optional
from .Player import Player
from .Base import Base
from .Game import Game
from sqlalchemy import ForeignKey, DateTime, select, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped
from datetime import datetime, timezone

# TODO: put CHECK constraint on target and assassin game_id's
class TargRel(Base):
    """
    TargRel class

    This is used to store the table of who is targetting who(m).
    Each instance represents an 'edge' in the targetting graph.
    """

    __tablename__ = "targetting_table"
    target_id = mapped_column(ForeignKey("assassins.id", ondelete="CASCADE"), primary_key=True)
    target: Mapped["Assassin"] = relationship(foreign_keys=[target_id])

    assassin_id = mapped_column(ForeignKey("assassins.id", ondelete="CASCADE"), primary_key=True)
    assassin: Mapped["Assassin"] = relationship(foreign_keys=[assassin_id])

class Assassin(Player):
    """
    Assassin class

    Extends the Player class by including vitality, competence, and targetting relationships.
    """

    __tablename__ = "assassins"
    id = mapped_column(ForeignKey(Player.id), primary_key=True)

    alive: Mapped[bool] = mapped_column(default=True)
    competence_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # lists of targets and assassins generated by persisting a relationship using a secondary join with targetting_table
    targets: Mapped[List["Assassin"]] = relationship(overlaps="assassins,target,assassin",
                                                     secondary=TargRel.__tablename__,
                                                     primaryjoin="Assassin.id==TargRel.assassin_id",
                                                     secondaryjoin="Assassin.id==TargRel.target_id")
    assassins: Mapped[List["Assassin"]] = relationship(overlaps="targets,assassin,target",
                                                       secondary=TargRel.__tablename__,
                                                       primaryjoin="Assassin.id==TargRel.target_id",
                                                       secondaryjoin="Assassin.id==TargRel.assassin_id")

    __mapper_args__ = {
        "polymorphic_identity": "assassin", # sets Player.type for objects of this class to "assassin"
    }

    # TODO: event-based structure for targets, so we have a 'wanted at'
    #  Maybe a a bit overwrought but allows us to track targetting!
    def licit_for(self, killer: Player) -> bool:
        # TODO: check for wantedness/incompetence
        if isinstance(killer, Assassin):
            if self in killer.targets:
                return (True, f'because {self.id} is a target of {killer.id}')
            if self in killer.assassins:
                return (True, f'because {self.id} is targetting {killer.id}')
            return (False, f'because {self.id} is neither a target of nor targetting {killer.id}')

    def send_update(self, body: str = ""):
        from .templates import env
        from babel.dates import format_datetime
        template = env.get_template("update-email.jinja")
        message = template.render(player=self.reg,
                                  message=body,
                                  targets=[t.reg for t in self.targets],
                                  competence_deadline=format_datetime(self.competence_deadline,
                                                                      locale=self.game.locale,
                                                                      tzinfo=self.competence_deadline.tzinfo
                                                                      )
                                  )
        self.reg.send_email(body=message)

#### INSERTIONS INTO `Game` CLASS ####

Game.assassins: WriteOnlyMapped[List[Assassin]] = relationship(back_populates="game", overlaps="players", passive_deletes=True)

@Game.method
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
    # TODO: also, have temporary store of problematic choices so that we don't keep picking them,
    #  and if we run out of choices we can 're-roll'
    to_add = []
    for a in need_targs:
        print(f"Finding a target for {a}... ", end="")
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
                (
                    (TargRel.assassin_id == a) & (TargRel.target_id == t)
                ) | (
                    (TargRel.assassin_id == t) & (TargRel.target_id == a)
                )
                                    )
            ).one_or_none()
            if res is not None:
                continue
            ok = True
            break
        print(f"chose {t}.")
        # set `a` to target `t` now that it has been verified as ok
        to_add.append(TargRel(assassin_id=a, target_id=t))
        need_asses.remove(t)

    session.add_all(to_add)
    return (len(to_add) > 0)

@Game.method
def assign_targets(self):
    """
    Assigns targets to assassins in this game who have fewer than the number of targets required by the game settings (`n_targs`),
    choosing randomly from the assassins who have fewer than the requisite number of people targetting them.
    Currently, reflexive and symmetric targetting relations are forbidden,
    but the "girth > 3" requirement of the original AutoUmpire is not yet implemented.
    """
    # TODO: store which players got new targets
    while self._assign_targets_one_pass():
        pass

@Game.method
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


@Game.startHook.register()
def onstart(game: Game):
    session = game.session
    assassins = session.scalars(game.assassins.select())
    inital_deadline = datetime.now(timezone.utc) + game.initial_competence
    # TODO: use UPDATE statement for this
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda a: setattr(a, "competence_deadline", inital_deadline), assassins)
    game.assign_targets()
    game.send_updates()