# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from assassins_data import engine, Player, Pseudonym, Assassin
from sqlalchemy.orm import Session
from sqlalchemy import select
from actions.assign_targets import assign_targets

def start_game():
    # initialise registered players as assassins
    with Session(engine) as session:
        r = session.scalars(select(Player))
        for player in r:
            new_assassin = Assassin(player=player, alive=True)
            new_pseudonym = Pseudonym(text=player.initial_pseudonym,owner=new_assassin)
            session.add(new_assassin)
            session.add(new_pseudonym)
        session.commit()
    # assign targets
    assign_targets()

if __name__ == "__main__":
    sys.exit(start_game())