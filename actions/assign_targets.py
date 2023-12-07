# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

# actual imports
from assassins_data import config, engine, Assassin, targetting_table
from sqlalchemy import select, func, and_, or_, insert
from sqlalchemy.orm import Session
import random

# function to assign targets to assassins
# this will usually be called by other parts of autoumpire,
# e.g. on game start and after a death,
# but can also be called as a command in itself if needed
def assign_targets():
    with Session(engine) as session:
        # subquery which counts the number of targets a given assassin has
        count_targs = (
            select(func.count(targetting_table.c.assassin_id))
                .where(targetting_table.c.assassin_id == Assassin.id)
                .scalar_subquery()
        )
        # queries all alive assassins with fewer than config["n_targs"] targets
        need_targs = session.scalars(select(Assassin.id)
                            .filter_by(alive=True)
                            .where(count_targs < config["n_targs"])
                            )
        # subquery which counts the number of assassins a given assassin has
        count_asses = (
            select(func.count(targetting_table.c.assassin_id))
                .where(targetting_table.c.target_id == Assassin.id)
                .scalar_subquery()
        )
        # queries all alive assassins with fewer than config["n_targs"] assassins
        need_asses = list(session.scalars(select(Assassin.id)
                            .filter_by(alive=True)
                            .where(count_asses < config["n_targs"])
                            ).fetchall())

        for a in need_targs:
            # randomly pick a target for `a`,
            # verify
            ok = False
            while not ok:
                # choose a target from the assassins who have an insufficient number targetting them
                t = random.choice(need_asses)
                # disallow self-targetting
                if t == a:
                    continue
                # check if `a` and `t` already have a targetting relation, in either direction
                # in which case disallow `t` as a choice of target
                res = session.scalars(select(targetting_table)
                                      .where(
                    or_(
                        and_(targetting_table.c.assassin_id == a, targetting_table.c.target_id == t),
                        and_(targetting_table.c.assassin_id == t, targetting_table.c.target_id == a)
                    )
                                        )
                ).one_or_none()
                if res is not None:
                    continue
                ok = True
                break
            #print(a,t)
            # set `a` to target `t` now that it has been verified as ok
            session.execute(insert(targetting_table).values(assassin_id=a,target_id=t))
            need_asses.remove(t)

        session.commit()

if __name__ == "__main__":
    assign_targets()