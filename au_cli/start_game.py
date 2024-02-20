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
    parser.add_argument("-f", "--force", action="store_true", help="Include to skip confirmation.")
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au

def main(game: au.Game, confirm=True):
    if confirm:
        # TODO: Add more info. about what starting the game does.
        print(f"About to start the game {game.name}.")
        resp = input("Enter Y to confirm: ").upper()
        if resp != "Y":
            return
    game.start()
    game.session.commit()

if __name__ == "__main__":
    with au.db.Session() as session:
        game = session.scalar(au.Game.select().filter_by(name=args.game))
        if game is None:
            raise au.GameNotFoundError(f"No game with name {args.game}")
        main(game, not args.force)
else:
    import commands

    # command used by the main cli program
    @commands.register(primary_name="start", description="Starts the current game.")
    def cmd_startgame(argsraw: str = ""):
        if 'game' not in commands.state:
            raise(commands.GameNotLoadedError())
        main(commands.state['game'])