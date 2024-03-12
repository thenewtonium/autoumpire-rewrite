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
import json
import au_core as au
from typing import List, Optional, Tuple
from tabulate import tabulate
from dataclasses import dataclass

player_type_mapping = {
    "Full Player": au.Assassin,
    "Police": au.Police
}
TYPE_HEADING = "type"
REALNAME_HEADING = "real name"
EMAIL_HEADING = "email"
PSEUDONYM_HEADING = "initial pseudonym"

required_headings = [TYPE_HEADING, REALNAME_HEADING, EMAIL_HEADING, PSEUDONYM_HEADING, "college", "address", "water", "notes"]

class SignupsError(Exception):
    """base exception class for signup parsing errors"""

class MissingHeadingsError(SignupsError):
    """Exception raised when a CSV file being parsed is missing required headings."""

@dataclass
class InvalidRowError(SignupsError):
    """Exception raised when a row is invalid"""
    row: List[str]

@dataclass
class InvalidPlayerTypeError(InvalidRowError, ValueError):
    """Exception for when a row is invalid because the type column's value can't be found int player_type_mapping"""
    player_type: str

@dataclass
class DuplicateError(InvalidRowError):
    """Exception for when a row is invalid because it partially duplicates another player"""
    existing_player: au.Player

@dataclass
class DuplicateEmailError(DuplicateError):
    """Exception for when a row is invalid because it duplicates an existing player's email"""
    email: str

@dataclass
class DuplicatePseudonymError(DuplicateError):
    """Exception for when a row is invalid because it duplicates an existing pseudonym"""
    pseudonym: str

def parse_csv(filepath: str, game: au.Game) -> Tuple[List[au.Player], List[InvalidRowError]]:
    """
    :param filepath: Path of the csv file to load registrations from.
    :param game: au_core.Game object to add the registrations to
    :return: A tuple of a list of player objects created from valid registrations, and a list of errors
    """
    session = game.session

    registrations = []
    errors = []

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
                    raise MissingHeadingsError(f"CSV file is missing the following headings: {', '.join(missing_headings)}")
            # rest of rows are entries
            else:
                # first stash the row into an 'info' dict
                info = dict()
                for i in range(len(row)):
                    info[head[i]] = row[i]

                # collect error for invalid player type
                t = info.pop(TYPE_HEADING).strip()
                if t not in player_type_mapping:
                    errors.append(InvalidPlayerTypeError(row=row))
                    continue

                # TODO: validate email
                email = info.pop(EMAIL_HEADING).strip()
                # collect error for duplicate email
                dup = session.scalar(game.players.select().filter_by(email=email))
                if dup:
                    errors.append(DuplicateEmailError(email=email, existing_player=dup, row=row))
                    continue

                # TODO: ensure nonempty pseudonym
                initial_pseudonym = info.pop(PSEUDONYM_HEADING).strip()
                # collect error for duplicate initial pseudonym
                dup = session.scalar(au.Pseudonym.select(au.Pseudonym.owner_id)
                                     .where(au.Pseudonym.owner.has(au.Player.game_id == game.id))
                                     .filter_by(text=initial_pseudonym))
                if dup:
                    errors.append(DuplicatePseudonymError(pseudonym=initial_pseudonym, existing_player=dup, row=row))

                # extract realname
                # TODO: ensure nonempty real name
                realname = info.pop(REALNAME_HEADING)

                # construct Player and Pseudonym objects, and add to the list of new regs
                newplayer = player_type_mapping[t](realname=realname, email=email, info=info,
                                       pseudonyms=[au.Pseudonym(text=initial_pseudonym)])

                registrations.append(newplayer)
                # also queue it up so that duplicate checking works
                # TODO: replace this with seperately checking in `registrations` for duplicates
                game.players.add(newplayer)

    return (registrations, errors)

# originally function to run as a callback once loaded a game when this run as an os terminal command
# but also works for the main cli program

def main(game: au.Game, filepath: str, save: Optional[bool] = False):
    regs, errs = parse_csv(filepath=filepath, game=game)

    # case where there were problems
    if len(errs) != 0:
        print("Errors were found in the following rows:")
        for err in errs:
            print(', '.join(err.row))
            if isinstance(err, InvalidPlayerTypeError):
                print(f"-- {err.player_type} is not a valid player type (should be one of {', '.join(player_type_mapping.keys())})")
            elif isinstance(err, DuplicatePseudonymError):
                print(f"-- {err.pseudonym} is already the pseudonym of {err.existing_player.realname}")
            elif isinstance(err, DuplicateEmailError):
                print(f"-- {err.email} is already the email of {err.existing_player.realname}")
            else:
                print(f"-- {err}")
            print()
        return

    print("Successfully loaded the following registrations:")
    tab = tabulate( [ [r.realname, r.email, r.type, r.pseudonyms[0].text,  json.dumps(r.info)] for r in regs],
                    headers=["Real Name", "Email", "Player Type", "Initial Pseudonym", "Other Info"])
    print(tab)
    if not save:
        resp = input(f"Enter Y to add these registrations to game {game.name}? ").upper()

    if save or resp == "Y":
        game.session.commit()
        print("Successfully added all registrations to the game.")
    else:
        game.session.rollback()
        print("Aborted adding registrations from the CSV file.")

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
            raise(commands.GameNotLoadedError())

        main(commands.state['game'], argsraw)


    # helper commands for finding files
    @commands.register(aliases=['chdir'],
                       description="Changes the current working directory. (Used for finding csv files)")
    def cd(argsraw: str = ""):
        os.chdir(argsraw)
        print(f"Changed working directory to {os.getcwd()}")

    # util to iterate in 'chunks'
    # TODO: put this in its own file since it's also used by add_death.py for parsing
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
        contents = os.listdir(argsraw)
        print(f"Files and folders in {argsraw}")
        tab = tabulate(chunk(contents, 3))
        print(tab)

