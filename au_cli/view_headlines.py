"""
view_headlines.py

A command to view the headlines for events on a given date, and also the ids of the relevant events
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("date",
                        help="The date to display the headlines for. Format is YYYY-MM-DD.",
                        type=str)
    parser.add_argument("-g", "--game", help="The name of the game to search for headlines in.",
                        type=str, required=True)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au
from tabulate import tabulate
from typing import Tuple

import re
from datetime import datetime, timedelta
date_pattern = re.compile(r"\[?(\d+)[-\./](\d+)[-\./](\d+)\]?:?")

def main(game: au.Game, date: str):
    session = game.session
    if (date is None or date.strip() == ""):
        events = session.scalars(game.events.select())
        print("All headlines:")
    else:
        try:
            week_n = int(date)
            events = game.events_in_week(week_n)
            print(f"Headlines from week {week_n}:")
        except ValueError:
            m = date_pattern.match(date)
            if (m is None):
                print(f"{date} is not a valid date! Format must be YYYY-MM-DD")
                return
            lower_bound = datetime(year=int(m.group(1)),
                            month=int(m.group(2)),
                            day=int(m.group(3)))
            upper_bound = lower_bound + timedelta(days=1)
            events = session.scalars(game.events.select().where(
                (lower_bound <= au.Event.datetimestamp) & (au.Event.datetimestamp < upper_bound))
            )
            normalised_date = lower_bound.strftime("%A, %d %B")
            print(f"Headlines from {normalised_date}:")
    # TODO: consider including deaths, competence awarded, etc.
    tab = tabulate(((e.id,
                     e.datetimestamp.strftime("%Y-%m-%d"),
                     e.datetimestamp.strftime("%I:%M %p"),
                     e.plaintext_headline(),
                     e.headline) for e in events),
                   headers=("id","date", "time","parsed headline", "raw headline"))
    print(tab)

if __name__ == '__main__':
    with au.db.Session() as session:
        game = session.scalar(au.Game.select().filter_by(name=args.game))
        if game is None:
            raise au.GameNotFoundError(f"No game with name {args.game}")
        main(game, args.date)
else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="viewheadlines", aliases=["viewevents"],
                       description="Gives the headlines and IDs of events on a given date.")
    def cmd_search_headlines(argsraw: str = ""):
        if 'game' not in commands.state:
            print("You need to load a game first!")
            return

        main(commands.state['game'], argsraw)