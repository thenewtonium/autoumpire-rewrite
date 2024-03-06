"""
generate_headlines.py

A command line script to generate the headlines page
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-g", "--game", help="The name of the game to generate headlines for.",
                        type=str)
    parser.add_argument("path", help="The filepath to save the headlines page to.",
                        type=str)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
import os
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import au_core as au

def main(game: au.Game, path: str):
    page = game.generate_headlines()
    print("Headlines page HTML: ")
    print(page)
    if path is None or path.strip() == "":
        path = str(input(f"Enter save path (current directory is {os.getcwd()}): "))

    if path.strip() == "":
        print("Did not save.")
        return

    with open(path, "w") as f:
        f.write(page)

    print(f"Saved headlines to {path}")


if __name__ == "__main__":
    with au.db.Session() as session:
        game = session.scalar(au.Game.select().filter_by(name=args.game))
        if game is None:
            raise au.GameNotFoundError(f"No game with name {args.game}")
        main(game, args.path)
else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="generateheadlines", description="Generates the headline page")
    def cmd_gen_headlines(argsraw: str):
        if 'game' not in commands.state:
            raise(commands.GameNotLoadedError())
        main(commands.state["game"], argsraw)