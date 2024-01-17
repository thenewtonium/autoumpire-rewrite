"""
lookup_pseudonyms.py

A command line script to list the pseudonyms associated with a given player,
including the references used in reports.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--id",
                        help="The ID of the player to list the pseudonyms for (you can find this using `search_player.py`).",
                        type=int, required=True)
    parser.add_argument("-g", "--game", help="The name of the game that the player is in.",
                        type=str, required=True)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au

if __name__ == "__main__":
    def callback(game: au.Game):
        player = game.session.get(au.Player, args.id)
        print("Player info:")
        print("Id\tReference\tReal Name\tEmail\tCollege\tAddress\tWWWS\tNotes")
        print(f"{player.id}\t{player.reference()}\t{player.reg.realname}\t{player.reg.email}\t{player.reg.college}\t{player.reg.address}\t{player.reg.water}")
        print("----")
        print("Player pseudonyms:")
        print("Reference\tPseudonym")
        [print(f"{x.reference()}\t{x.text}") for x in player.pseudonyms]
    try:
        au.callback_on_game(args.game, callback, autocommit=False)
    except au.GameNotFoundError:
        print(f"Error: no game found with name {args.game}.")