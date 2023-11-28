# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

# actual imports
from assassins_data import engine, Player, WaterStatus
from sqlalchemy.orm import Session

# function to add a player to the database
# this will either be called by the add player command in autoumpire.py
# or when this file is run from the command line
def add_player(player : Player):
    with Session(engine) as session:
        session.add(player)
        session.commit()

# code to run when called by command line
# this is set up to run by FLAGS;
# see the list of `parser.add_argument(...)` statements for reference
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-r", "--realname", help="Player's real name")
    parser.add_argument("-e", "--email", help="Player's email address")
    parser.add_argument("-a", "--address", help="Player's address")
    parser.add_argument("-c", "--college", help="Player's college")
    parser.add_argument("-w", "--water", help="Player's water weapons status")
    parser.add_argument("-n", "--notes", help="Player's notes")
    parser.add_argument("-p", "--pseudonym", help="Player's initial pseudonym")

    args = parser.parse_args()

    try:
        ws = WaterStatus(args.water)
    except Exception as e:
        print("Error! Water Status must be one of:")
        [print(s.value) for s in WaterStatus]
        print("----")
        raise e

    player = Player(
                realname=args.realname,
                email=args.email,
                address=args.address,
                college=args.college,
                water=ws,
                notes=args.notes,
                initial_pseudonym=args.pseudonym
    )
    sys.exit(add_player(player))