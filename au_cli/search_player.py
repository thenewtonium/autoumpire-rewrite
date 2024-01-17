"""
search_player.py

A command line script to search for player info.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("query", help="Search query (searches in players' real names and email addresses)", type=str)

    parser.add_argument("-g", "--game", help="The name of the game to add the event to.",
                        type=str, required=True)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au
from sqlalchemy import or_

if __name__ == "__main__":
    def callback(game: au.Game):
        session = game.session

        # query registrations whose realname or email match the query text
        res1 = session.scalars(game.players.select()
                        .join(au.Registration)
                        .where(
                            or_(
                                au.Registration.realname.icontains(args.query),
                                au.Registration.email.icontains(args.query)
                            )
                        )
                        .order_by(au.Registration.id)
        )

        # print out results
        print("Id\tReference\tReal Name\tEmail\tCollege\tAddress\tWWWS\tNotes")
        [print(f"{x.id}\t{x.reference()}\t{x.reg.realname}\t{x.reg.email}\t{x.reg.college}\t{x.reg.address}\t{x.reg.water}") for x in res1]
    try:
        au.callback_on_game(args.game, callback, autocommit=False)
    except au.GameNotFoundError:
        print(f"Error: no game found with name {args.game}.")