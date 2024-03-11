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
from tabulate import tabulate
from typing import Tuple, Any
from datetime import datetime

# TODO: 'status' entry combining Death, Competence, Wantedness
info_headers = ('id', 'real name', 'email', 'type', 'other info')#'college', 'address', 'WWS', 'notes')
def player_info_tuple(p: au.Player) -> Tuple:
    """
    Converts a Player object into a tuple with entries corresponding to info_headers.
    This is
    :param p: Player object to convert into a tuple
    :return: Tuple with the attributes of the Player object in the order described by `info_headers`
    """
    ret = (p.id, p.realname, p.email, p.type, p.info)
    #ret = (p.id, p.reg.realname, p.reg.email, p.type, p.reg.college, p.reg.address, p.reg.water, p.reg.notes)
    return ret #(str(x) for x in ret)

def main(game: au.Game, query: str):
    session = game.session

    # query registrations whose realname or email match the query text
    res1 = session.scalars(game.players.select()
                           .where(au.Player.realname.icontains(query)
                                  | au.Player.email.icontains(query))
                           .order_by(au.Player.id)
                           )
    """res1 = session.scalars(game.players.select()
                           .join(au.Registration)
                           .where(au.Registration.realname.icontains(query)
                                  | au.Registration.email.icontains(query))
                           .order_by(au.Registration.id)
                           )"""
    print(f"Players with names or email addresses containing the string '{query}':")
    tab = tabulate((player_info_tuple(p) for p in res1), headers=info_headers)
    print(tab)

if __name__ == '__main__':
    with au.db.Session() as session:
        game = session.scalar(au.Game.select().filter_by(name=args.game))
        if game is None:
            raise au.GameNotFoundError(f"No game with name {args.game}")
        main(game, args.query)
else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="searchplayer", aliases=["searchplayers"],
                       description="Searches for a player by real name or email address.")
    def cmd_searchplayer(argsraw: str = ""):
        if 'game' not in commands.state:
            print("You need to load a game first!")
            return

        main(commands.state['game'], argsraw)