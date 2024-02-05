"""
view_player.py

A command line script to inspect information on a given player by id
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("id",
                        help="The ID of the player to list the pseudonyms for (you can find this using `search_player.py`).",
                        type=int)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au
from typing import Optional
from search_player import info_headers, player_info_tuple
from tabulate import tabulate

class PlayerNotFoundError(Exception):
    """
    Exception raised when trying to display information based on a nonexistent id
    """

def main(id: int, game: Optional[au.Game] = None):
    if game is None:
        session = au.db.Session()
        need_to_close_session = True
        player = session.get(au.Player, id)
    else:
        player = game.session.scalar(game.players.select().filter_by(id=id))
        need_to_close_session = False

    if player is None:
        raise PlayerNotFoundError(f"There is no player with id {id}")

    # display the player info as displayed in searchplayer
    infotab = tabulate((player_info_tuple(player),), headers=info_headers)
    print("Player Info:")
    print(infotab)
    print()

    # display the player's pseudonyms
    pseutab = tabulate(((pn.text, pn.id)  for pn in player.pseudonyms), headers=('Pseudonym', 'Id'))
    print(f"{player.reg.realname}'s Pseudonyms:")
    print(pseutab)
    print()

    # if the player is an assassin, display their targets and assassins
    if isinstance(player, au.Assassin):
        print("Competence deadline: " + player.competence_deadline.strftime("%a %d %b, %H:%M"))
        print()

        targtab = tabulate((player_info_tuple(t) for t in player.targets), headers=info_headers)
        print(f"{player.reg.realname}'s Targets:")
        print(targtab)
        print()

        asstab = tabulate((player_info_tuple(t) for t in player.assassins), headers=info_headers)
        print(f"Assassins targetting {player.reg.realname}:")
        print(asstab)
        print()

    if need_to_close_session:
        session.close()

if __name__ == "__main__":
    main(args.id)
else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="viewplayer",
                       description="Fetches information on a player, including their pseudonyms, using their id")
    def cmd_viewplayer(rawargs):
        id = int(rawargs)
        game = commands.state['game']
        main(id, game)
