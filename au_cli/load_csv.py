"""
load_csv.py

A command line utility for loading player registrations from a CSV file.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("filepath", help="The path of the CSV file to load.", type=str)

    parser.add_argument("-s", "--save", help="Include this flag to skip confirmation of adding loaded players",
                        action='store_true')
    parser.add_argument("-g", "--game", help="The name of the game to load the CSV into.",
                        type=str)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import csv
import au_core as au
from typing import List, Optional
from warnings import warn

required_headings = ["realname", "email", "initial_pseudonym", "college", "address", "water", "notes", "type"]
blank_allowed = ["notes"]

class MissingHeadingsError(Exception):
    """
    Exception raised when a CSV file being parsed is missing required headings.
    """
    def __init__(self, *args, **kwargs):
        self.missing_headings = kwargs["missing_headings"]
        super().__init__(*args)

def parse_csv(filepath: str, game: au.Game) -> List[au.Registration]:
    """

    :param filepath: Path of the csv file to load registrations from.
    :param game: au_core.Game object to add the registrations to
    :return: A list of au_core.Registration objects corresponding to the rows of the CSV file.
    """

    registrations = []

    with open(filepath) as csvfile:
        reader = csv.reader(csvfile)
        initial = True # gives special treatment to first row
        for row in reader:
            # first row is headings
            if initial:
                # save the initial row as the 'headings' row
                head = row
                initial = False

                # verify all required headings present
                missing_headings = [h for h in required_headings if h not in head]
                if len(missing_headings) > 0:
                    raise MissingHeadingsError(f"CSV file is missing the following headings: {', '.join(missing_headings)}",
                                               missing_headings=missing_headings)
            # rest of rows are entries
            else:
                # set Registration attributes based on the head row
                newreg = au.Registration(game=game)
                for i in range(len(row)):
                    setattr(newreg, head[i], row[i])

                # validate the registration
                try:
                    newreg.validate(enforce_unique_email=True)
                    registrations.append(newreg)
                except Exception as e:
                    warn(e)

    return registrations

if __name__ == '__main__':
    def callback(game: au.Game):
        regs = parse_csv(filepath=args.filepath, game=game)
        print("Successfully loaded the following registrations:")
        [print(r) for r in regs]
        if not args.save:
            resp = input(f"Enter Y to add these registrations to game {game.name}? ").upper()

        if args.save or resp == "Y":
            for reg in regs:
                game.add_player_from_reg(reg)
            game.session.commit()
            print("Successfully added all registrations to the game.")
        else:
            print("Aborted adding registrations frome the CSV file.")
    try:
        au.callback_on_game(identifier=args.game, callback=callback)
    except au.GameNotFoundError:
        resp = input(f"No game called {args.game} found. Enter Y to create a game of this name: ").upper()
        if resp == "Y":
            print(f"Creating game {args.game}...")
            au.create_game_then_callback(name=args.game, callback=callback)
        else:
            print("Aborted loading CSV file.")