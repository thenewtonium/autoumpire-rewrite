# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from assassins_data import config, engine, Player, Pseudonym, Assassin
from sqlalchemy.orm import Session
from sqlalchemy import select
from actions.assign_targets import assign_targets
from datetime import datetime, timezone, timedelta

# function which starts the game,
# i.e. instantiates players as assassins, and assigns targets
def start_game():
    # initialise registered players as assassins
    with Session(engine) as session:
        r = session.scalars(select(Player))
        for player in r:
            new_assassin = Assassin(player=player, alive=True,
                                    competence_deadline=datetime.now(timezone.utc)
                                                        +timedelta(days=config["initial_competence"])
                                    )
            new_pseudonym = Pseudonym(text=player.initial_pseudonym,owner=new_assassin)
            session.add(new_assassin)
            session.add(new_pseudonym)
        session.commit()
    # assign targets
    assign_targets()

if __name__ == "__main__":
    sys.exit(start_game())