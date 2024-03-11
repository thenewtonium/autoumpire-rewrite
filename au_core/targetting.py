"""
targetting.py

Implements targetting between Assassins
"""

import random
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, ScalarResult, select, func
from .Game import StateChange, Game
from .Player import Player
from .Assassin import Assassin
from .Death import licitnessHook
from datetime import datetime


class TargRel(StateChange):
    """Represents the assignment of targets to Assassings"""
    __tablename__ = "targetting_table"
    target_id: Mapped[int] = mapped_column(ForeignKey(Assassin.id, ondelete="CASCADE"), primary_key=True)
    assassin_id: Mapped[int] = mapped_column(ForeignKey(Assassin.id, ondelete="CASCADE"), primary_key=True)

    target: Mapped[Assassin] = relationship(foreign_keys=[target_id])
    assassin: Mapped[Assassin] = relationship(foreign_keys=[assassin_id])


### Insertions into Assassin class


def Assassin_get_targets(self) -> ScalarResult:
    """
    Method inserted into the Assassin class by targetting.py
    :return: An sqlalchemy.ScalarResult with the targets of this assassin.
    """
    return self.session.scalars(Assassin.select(Assassin.id).join(TargRel, TargRel.target_id == Assassin.id)
                                .where((TargRel.assassin_id == self.id)))
Assassin.get_targets = Assassin_get_targets


def Assassin_get_assassins(self) -> ScalarResult:
    """
    Method inserted into the Assassin class by targetting.py
    :return: An sqlalchemy.ScalarResult with the targets of this assassin.
    """
    return self.session.scalars(Assassin.select(Assassin.id).join(TargRel, TargRel.assassin_id == Assassin.id)
                                .where((TargRel.target_id == self.id)))
Assassin.get_assassins = Assassin_get_assassins


def Assassin_has_target(self, player: Player) -> bool:
    """
    Method inserted into the Assassin class by targetting.py
    :return: Whether player is a target of this assassin.
    """
    return (True if self.session.scalar(TargRel.select()
                                       .where( (TargRel.target_id == player.id) & (TargRel.assassin_id == self.id) ))
            else False)
Assassin.has_target = Assassin_has_target


### Set kills between targets as licit
@licitnessHook.register()
def target_licitness(killer: Player, victim: Player) -> Optional[bool]:
    if (isinstance(killer, Assassin) and isinstance(victim, Assassin)):
        return True if (killer.has_target(victim) or victim.has_target(killer)) else None


### Target assignment algorithm

# subquery which counts the number of live targets a given assassin has
count_targs = (
        select(func.count(TargRel.assassin_id))
            .where(TargRel.assassin_id == Assassin.id)
            .where(TargRel.target.has(Assassin.alive == True))
            .scalar_subquery()
    )

# subquery which counts the number of assassins a given assassin has
count_asses = (
        select(func.count(TargRel.assassin_id))
            .where(TargRel.target_id == Assassin.id)
            .where(TargRel.assassin.has(Assassin.alive == True))
            .scalar_subquery()
    )

class TargettingError(Exception):
    """Exception raised when the algorithm fails to assign targets"""


def _try_rand_target(candidate_targs: List[Assassin], a: Assassin) -> Optional[Assassin]:
    # choose a target from the assassins who have an insufficient number targetting them
    t = random.choice(candidate_targs)

    # check if `a` and `t` already have a targetting relation, in either direction
    # in which case disallow `t` as a choice of target
    if a.has_target(t) or t.has_target(a):
        candidate_targs.remove(t)
        return None

    # enforce girth-3, i.e. t can't have a target who is targetting a, nor vice versa

    for sub_targ in t.get_targets():
        if sub_targ.has_target(a):
            candidate_targs.remove(t)
            return None

    for sub_targ in a.get_targets():
        if sub_targ.has_target(t):
            candidate_targs.remove(a)
            return None

    return t


def _assign_targets_one_pass(game: Game, datetimestamp: datetime) -> bool:
    """
    One pass of the target-assignment algorithm. This will be repeated until it returns `False`
    :return: bool value of whether this function should be called again.
    """
    session = game.session # only fetch this once...

    # fetch all alive assassins in this game with fewer than `n_targs` targets
    need_targs = session.scalars(Assassin.select(Assassin.id)
                                 .filter_by(alive=True, game_id=game.id)
                                 .where(count_targs < game.n_targs)
                                 )
    # queries all alive assassins in this game with fewer than `n_targs` assassins,
    # then turns this into a list so that we can call random.choice on it
    need_asses = list(session.scalars(Assassin.select(Assassin.id)
                                      .filter_by(alive=True, game_id=game.id)
                                      .where(count_asses < game.n_targs)
                                      ).fetchall())

    # break condn
    if len(need_asses) == 0:
        return False

    for a in need_targs:
        print(f"Finding a target for {a.id}... ", end="")
        candidate_targs = [t for t in need_asses if t != a]

        t = _try_rand_target(candidate_targs, a)
        while len(candidate_targs) > 0 and not t:
            t = _try_rand_target(candidate_targs, a)

        if t:
            print(f"chose {t.id}.")
            # set `a` to target `t` now that it has been verified as ok
            session.add(TargRel(assassin=a, target=t, when=datetimestamp))
            need_asses.remove(t)

        else:
            raise TargettingError(f"No target could be found for {a.id} satisfying the girth-3 requirement")

    return True


@Game.startHook.register()
def Game_assign_targets(self: Game):
    """
    Assigns targets to assassins in this game who have fewer than the number of targets required by the game settings (`n_targs`),
    choosing randomly from the assassins who have fewer than the requisite number of people targetting them.
    """
    now = datetime.utcnow()
    # TODO: sometimes we get a TargettingError even at the beginning,
    # so need to implement a retry!
    while _assign_targets_one_pass(self, datetimestamp=now):
        pass
Game.assign_targets = Game_assign_targets

