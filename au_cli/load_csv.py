"""
load_csv.py

A command line utility for loading player registrations from a CSV file.

TODO: pretty-printing of signups
TODO: request to load a game when run from os terminal without -g flag set
"""

# when running from os terminal -- parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("filepath", help="The path of the CSV file to load.", type=str)

    parser.add_argument("-s", "--save", help="Include this flag to skip confirmation of adding loaded players",
                        action='store_true')
    parser.add_argument("-g", "--game", help="The name of the game to load the CSV into.",
                        type=str, required=True)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
import os
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import csv
import au_core as au
from typing import List, Optional
from warnings import warn
from tabulate import tabulate

required_headings = ["realname", "email", "initial_pseudonym", "college", "address", "water", "notes", "type"]
blank_allowed = ["notes"]

class MissingHeadingsError(Exception):
    """
    Exception raised when a CSV file being parsed is missing required headings.
    """
    def __init__(self, *args, **kwargs):
        self.missing_headings = kwargs["missing_headings"]
        super().__init__(*args)

# TODO: Return failed rows as well, and display these in another table
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

# originally function to run as a callback once loaded a game when this run as an os terminal command
# but also works for the main cli program

def main(game: au.Game, filepath: str, save: Optional[bool] = False):
    regs = parse_csv(filepath=filepath, game=game)
    print("Successfully loaded the following registrations:")
    tab = tabulate( [ [getattr(r, a) for a in required_headings] for r in regs] , headers=required_headings )
    print(tab)
    if not save:
        resp = input(f"Enter Y to add these registrations to game {game.name}? ").upper()

    if save or resp == "Y":
        for reg in regs:
            game.add_player_from_reg(reg)
        game.session.commit()
        print("Successfully added all registrations to the game.")
    else:
        print("Aborted adding registrations frome the CSV file.")

# code when run from the os terminal
# TODO: use loadgame function here for if '-g' flag not set
if __name__ == '__main__':
    with au.db.Session() as session:
        game = session.scalar(au.Game.select().filter_by(name=args.game))
        if game is None:
            raise au.GameNotFoundError(f"No game with name {args.game}")
        main(game, args.filepath, save=args.save)
else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="loadcsv", description="Loads players from a CSV file.")
    def cmd_loadcsv(argsraw: str = ""):
        if 'game' not in commands.state:
            print("You need to load a game first!")
            return

        main(commands.state['game'], argsraw)


    # helper commands for finding files
    @commands.register(aliases=['chdir'],
                       description="Changes the current working directory. (Used for finding csv files)")
    def cd(argsraw: str = ""):
        os.chdir(argsraw)
        print(f"Changed working directory to {os.getcwd()}")

    # util to iterate in 'chunks'
    from itertools import islice
    def chunk(it, size):
        """
        Util for iterating 'in chunks' over an iterator.
        Used in the `ls` command.
        :param it: Iterator to 'chunk'
        :param size: Size of the chunks.
        The last chunk will be smaller than this if the iterator's length does not divide by this.
        :return: An iterator returning tuples of `size` elements at a time from `it`.
        """
        it = iter(it)
        return iter(lambda: tuple(islice(it, size)), ())

    @commands.register(aliases=['dir'],
                       description="Lists the files in the current working directory. (Used for finding csv files)")
    def ls(argsraw: str = ""):
        if argsraw == "":
            argsraw = os.getcwd()
        print(args)
        contents = os.listdir(argsraw)
        print(f"Files and folders in {argsraw}")
        tab = tabulate(chunk(contents, 3))
        print(tab)

