"""
delete_game.py

A command line script to delete an assassins game.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("game", help="The name of the game to delete.",
                        type=str)
    parser.add_argument("-f", "--force", action="store_true")
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au

def main(game: au.Game, confirm=True) -> bool:
    if game.live:
        print("Cannot delete this game as it is live! End the game first to delete it.")
        return False
    if confirm:
        # TODO: Add more info. about what starting the game does.
        print(f"About to delete game {game.name}.")
        resp = input("Enter Y to confirm: ").upper()
        if resp != "Y":
            return False
    session = game.session
    game.delete()
    session.commit()
    return True

if __name__ == "__main__":
    with au.db.Session() as session:
        game = session.scalar(au.Game.select().filter_by(name=args.game))
        if game is None:
            raise au.GameNotFoundError(f"No game with name {args.game}")
        main(game, not args.force)
else:
    import commands

    # command used by the main cli program
    @commands.register(primary_name="deletegame", description="Deletes the current game.")
    def cmd_startgame(argsraw: str = ""):
        if 'game' not in commands.state:
            raise(commands.GameNotLoadedError())
        if main(commands.state['game']):
            del commands.state['game']

    # temporary command to end a game so that it can be deleted
    @commands.register(primary_name="endgame")
    def cmd_endgame(argsraw: str=""):
        if 'game' not in commands.state:
            raise(commands.GameNotLoadedError())
        commands.state['game'].live = False