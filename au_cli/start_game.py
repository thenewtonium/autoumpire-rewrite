"""
start_game.py

A command line script to start an assassins game.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("game", help="The name of the game to start",
                        type=str)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au

if __name__ == "__main__":
    def callback(game: au.Game):
        game.start()
    try:
        au.callback_on_game(args.game, callback, autocommit=True)
    except au.GameNotFoundError:
        print(f"Error: no game found with name {args.game}.")