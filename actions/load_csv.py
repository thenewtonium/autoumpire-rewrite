# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

# actual imports
import csv
from assassins_data import Player, engine
from sqlalchemy.orm import Session
from sqlalchemy import select

required_headings = ["realname", "email", "initial_pseudonym", "college", "address", "water", "notes"]
blank_allowed = ["notes"]


# function to bulk-register players from a csv file
# the order of columns is free,
# but they must be headed by the attribute names given in required_headings above
# which correspond to the attribute names of the Player class
def load_csv(filepath, save=False):
    ok_players = []
    session = Session(engine)
    with open(filepath) as csvfile:
        reader = csv.reader(csvfile)
        initial = True # gives special treatment to first row
        for row in reader:
            # first row is headings
            if initial:
                # verify all required headings present
                ok = True
                for h in required_headings:
                    if h not in row:
                        ok = False
                        break
                if not ok:
                    print(f"Error! File must have headings {', '.join(required)}")
                    break
                else:
                    initial = False
                    head = row
            # rest of rows are entries
            else:
                try:
                    # set player attributes based on the head row
                    newplayer = Player()
                    for i in range(len(row)):
                        setattr(newplayer, head[i], row[i])
                        # throw error if a field is blank other than "notes",
                        if row[i] == "" and head[i] not in blank_allowed:
                            raise Exception(f"Required field {head[i]} empty.")

                    # throw error if email already taken by a player
                    res = session.scalars(select(Player).where(Player._email == newplayer.email)).one_or_none()
                    if res is not None:
                        raise Exception(f"Email {newplayer.email} already registered for {res.realname} of {res.college}.")
                    # if got through above without error,
                    # add row to ok rows
                    session.add(newplayer)
                    session.flush()
                    ok_players.append(newplayer)
                except Exception as e:
                    #raise e
                    print(f"Problem in row {', '.join(row)}\n{e}")

    # if not autosaving, ask for confirmation
    if not save:
        print("About to add the following players:")
        [print(p) for p in ok_players]
        resp = input("Enter Y to confirm registration of the above players: ")
        if resp.upper() == "Y":
            save = True

    if save:
        #with Session(engine) as session:
            #session.add_all(ok_players)
        session.commit()
    else:
        print("Did not register players.")
    session.close()
    #return ok_players

# code to run when called by command line
# this script takes an argument for the filepath,
# and has a flag -s for whether to ask to confirm before registring or not;
# this is so that it can be called from command line by another non-python program,
# e.g. a web-interface
# (however I will in fact use flask for this so it's not really necessary,
# but I want to have a self-contained cli version of autoumpire-rewrite!)
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="The path of the CSV file to load.", type=str)
    parser.add_argument("-s", "--save", help="Include this flag to skip confirmation of adding loaded players",
                        action='store_true')
    args = parser.parse_args()

    sys.exit(load_csv(args.filepath,args.save))