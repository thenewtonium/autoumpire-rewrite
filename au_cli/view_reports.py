"""
view_reports.py

A command line script to view the reports for a given event
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("id",
                        help="The ID of the event to view the reports for (you can find this using `view_headlines.py`).",
                        type=int)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au
from typing import Optional
from tabulate import tabulate

class EventNotFoundError(Exception):
    """
    Exception raised when trying to display information based on a nonexistent id
    """

def main(id: int, game: Optional[au.Game] = None):
    if game is None:
        session = au.db.Session()
        need_to_close_session = True
        event = session.get(au.Event, id)
    else:
        event = game.session.scalar(game.events.select().filter_by(id=id))
        need_to_close_session = False

    if event is None:
        raise EventNotFoundError(f"There is no event with id {id}")

    print("Event date: " + event.datetimestamp.strftime("%A, %d %B %Y"))
    print("Parsed headline + reports:")
    print(event.plaintext_full())
    print()
    print("Raw headline + reports:")
    print(event.raw_full())

    # TODO: display deaths, competency info

    if need_to_close_session:
        session.close()

if __name__ == "__main__":
    main(args.id)
else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="viewreports", aliases=["view_reports", "eventinfo", "event_info"],
                       description="Fetches information on a player, including their pseudonyms, using their id")
    def cmd_viewplayer(rawargs):
        id = int(rawargs)
        game = commands.state['game']
        main(id, game)
