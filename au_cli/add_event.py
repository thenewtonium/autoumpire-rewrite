"""
add_event.py

A command line script to add an event in an assassins game.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("headline", help="The headline of the event to create.", type=str)

    parser.add_argument("-t", "--datetime",
                        help="The datetimestamp to give the event. Format is 'YYYY-MM-DD HH:MM', with 24-hour time",
                        type=str, required=True)

    parser.add_argument("-g", "--game", help="The name of the game to add the event to.",
                        type=str, required=True)
    args = parser.parse_args()

    from datetime import datetime
    import re

    # regex expression for parsing the string datetimestamp
    m = re.match(r"(\d+)[-\./](\d+)[-\./](\d+)\s*(\d+)[:\.](\d+)",args.datetime)
    datetimestamp = datetime(year=int(m.group(1)),
                             month=int(m.group(2)),
                             day=int(m.group(3)),
                             hour=int(m.group(4)),
                             minute=int(m.group(5)))

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au

if __name__ == "__main__":
    def callback(game: au.Game):
        new_event = au.Event(headline=args.headline, datetimestamp=datetimestamp)
        game.events.add(new_event)

        print("Type Y to confirm adding the following event:")
        print(new_event.plaintext_parsed_headline())
        resp = input().upper()
        if resp == "Y":
            game.session.commit()
            print(f"Successfully added event. Event id is {new_event.id}.")
        else:
            game.session.rollback()
            print("Did not add event.")

    try:
        au.callback_on_game(args.game, callback, autocommit=False)
    except au.GameNotFoundError:
        print(f"Error: no game found with name {args.game}.")
