"""
targetting.py

Implements targetting between Assassins
"""

import random

from typing import List, Optional, Tuple, Set
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, ScalarResult, select, func
from .Base import Base
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

class Seed(Base):
    """
    Represents seeds assigned to assassins
    The reason this isn't just a field of Assassin objects is modularity.
    """
    __tablename__ = "seeds"
    assassin_id: Mapped[int] = mapped_column(ForeignKey(Assassin.id), primary_key=True)
    val: Mapped[int]

    assassin: Mapped[Assassin] = relationship(back_populates="seed")

### Insertions into Assassin class

Assassin.seed: Mapped[Seed] = relationship(Seed, back_populates="assassin")


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
def _target_licitness(killer: Player, victim: Player) -> Optional[bool]:
    if (isinstance(killer, Assassin) and isinstance(victim, Assassin)):
        return True if (killer.has_target(victim) or victim.has_target(killer)) else None


### Target assignment algorithm

# subquery which counts the number of live targets a given assassin has
# TODO: replace with TargRel.count()
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

    # enforce girth>3, i.e. t can't have a target who is targetting a, nor vice versa
    # TODO: optional enforcement -- basically, we should aim for girth > 3,
    #  but if this is impossible, drop the condition and try again.

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
        #print(f"Finding a target for {a.id}... ", end="")
        candidate_targs = [t for t in need_asses if t != a]

        t = _try_rand_target(candidate_targs, a)
        while len(candidate_targs) > 0 and not t:
            t = _try_rand_target(candidate_targs, a)

        if t:
            #print(f"chose {t.id}.")
            # set `a` to target `t` now that it has been verified as ok
            session.add(TargRel(assassin=a, target=t, when=datetimestamp))
            need_asses.remove(t)

        else:
            raise TargettingError(f"No target could be found for {a.id} satisfying the girth-3 requirement")

    return True


def Game_assign_targets(self: Game):
    """
    Assigns targets to assassins in this game who have fewer than the number of targets required by the game settings (`n_targs`),
    choosing randomly from the assassins who have fewer than the requisite number of people targetting them.
    """
    now = datetime.utcnow()
    # TODO: sometimes we get a TargettingError even at the beginning,
    #  so need to implement a retry!
    while _assign_targets_one_pass(self, datetimestamp=now):
        pass
Game.assign_targets = Game_assign_targets

import math
from scipy.sparse.csgraph import floyd_warshall
from scipy.sparse import csr_matrix, lil_matrix
from numpy import ndarray

def _matrix_assign_targs(n: int, num_targs: int) -> Tuple[List[Set[int]], ndarray]:
    """
    Anonymously assigns targets to assassins, so that we can use seeding to place "good" assassins far from each other.
    :param n: Number of assassins
    :param num_targs: Number of targets that should be assigned to each assassin
    :return: A tuple of,
    a list where the ith element is the set of targets to assign to the ith assassin,
    a 2d numpy array representing the distance between assassins in the targetting graph
    """
    graph_mat = lil_matrix((n, n))
    targs = [set() for a in range(n)]
    asses = [set() for t in range(n)]  # track assassins for easy lookup in girth-3 check
    for a in range(n):
        #print(f"Finding targets for {a}")
        targets_targets = set().union(*[targs[t] for t in targs[a]])
        asses_asses = set().union(*[asses[a_2] for a_2 in asses[a]])
        # get all valid targets for a
        candidate_targs = [t for t in range(n)
                           if t != a  # don't allow reflexive targetting
                           and len(asses[t]) < num_targs  # make sure the target needs another assassin
                           and t not in targs[a] and a not in targs[t]  # make sure no targetting exists between a and t
                           and t not in targets_targets and t not in asses_asses]  # require girth > 3
        # throw error if assigning targets is impossible
        if len(candidate_targs) < num_targs:
            raise TargettingError(f"Insufficient valid targets for the {a}th assassin")
        # choose randomly the correct number of targets
        a_targs = random.sample(candidate_targs, num_targs)
        #print(f"Chose {a_targs}")
        # store these as a's targets, and update associated structures
        targs[a] = set(a_targs)
        for t in a_targs:
            asses[t].add(a)
            graph_mat[a, t] = 1
            graph_mat[t, a] = 1

    del asses  # unneeded so free up space

    # get the distances between assassins through the targetting graph;
    # note that targetting relations can be traversed either way
    dist_mat = floyd_warshall(csr_matrix(graph_mat), return_predecessors=False)

    return targs, dist_mat

MAX_TRIES = 20

@Game.startHook.register()
def onstart(game: Game, now: datetime):
    """
    Initial assignment of targets. Unlike with retargetting, we use seeding to determine who gets what targets.
    """
    session = game.session
    # count the number of assassins
    n = session.scalar(Assassin.count().filter_by(game_id=game.id))

    # keep trying to assign targets
    count = 0
    while True:
        try:
            targs, dist_mat = _matrix_assign_targs(n, game.n_targs)
            break
        except TargettingError:
            count = count+1
            if count > MAX_TRIES:
                raise TargettingError(f"Could not assign targets, after {count} tries...")
            else:
                print(f"Failed targetting attempt {count}")

    # now do seeding
    # the algorithm is shamelessly stolen from autoumpire-0.3,
    # but here we use "functional" syntax
    to_be_seeded = {i for i in range(1, n)}
    seeds = [0]
    seed_rev_lookup = [0 for i in range(0, n)]
    while len(to_be_seeded) > 0:
        # the product here computes the "shininess" of each non-seeded player
        # the non-seeded player with the greatest "shininess" is chosen as the next seed
        tup = max(( (i, math.prod((dist_mat[i][j] - 1 for j in seeds))) for i in to_be_seeded), key=lambda x: x[1])
        new_seed = tup[0]
        seed_rev_lookup[new_seed] = len(seeds)
        seeds.append(new_seed)
        to_be_seeded.remove(new_seed)

    del dist_mat # unneeded so free up space

    # fetch assassin ids in order of seed, counting NULL as 0
    assassins_by_seed = (list(
                                session.scalars(select(Assassin.id).select_from(Seed).join(Assassin)
                                          .where((Seed.val > 0) & Seed.assassin.has(Assassin.game_id == game.id))
                                          .order_by(Seed.val.desc()))
                         )
                         + list(
                                session.scalars(select(Assassin.id)
                                          .where(~(
                                                   select(Seed.assassin_id)
                                                   .where(Seed.assassin_id == Assassin.id)
                                                  ).exists())
                                                )
                         )
                         + list(
                                session.scalars(select(Assassin.id).select_from(Seed).join(Assassin)
                                          .where((Seed.val < 0) & Seed.assassin.has(Assassin.game_id == game.id))
                                          .order_by(Seed.val.desc()))
                         ))
    # now use this list of ids to assign targets to the assassins
    for a_prio in range(n):
        a_id = assassins_by_seed[a_prio] # id in the database of the a_prio-th ranked assassin
        a = seeds[a_prio] # corresponding index of the above assassin in the targetting matrix
        for t in targs[a]:
            t_prio = seed_rev_lookup[t] # ranking of the assassin's new target
            t_id = assassins_by_seed[t_prio] # id in the database of the assassin's new target
            # create targetting relation in the database
            session.add(TargRel(assassin_id=a_id, target_id=t_id, when=now))
            #print(f"{a_id} targetting {t_id}")