"""
add_event.py

A command line script to add an event in an assassins game.
"""

import re
from datetime import datetime
dtstamp_pattern = re.compile(r"\[?(\d+)[-\./](\d+)[-\./](\d+)\s*(\d+)[:\.](\d+)\]?:?")

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

    # TODO: use `datetime.strptime` for this?
    # regex expression for parsing the string datetimestamp
    m = dtstamp_pattern.match(args.datetime)
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
from typing import Optional

# TODO: consider whether should refer to 'events' as 'headlines'
#  to make clearer what role they play in what the end user sees.
def main(game: au.Game, datetimestamp: Optional[datetime] = None, headline: Optional[str] = None, deaths = False):
    # request datetimestamp if not specified
    while datetimestamp == None:
        dtstr = input('Please enter the date and time of the event, in the format YYYY-MM-DD HH:MM (24-hour clock): ').strip()
        # exit condn
        if dtstr == '':
            return

        # parse entered datetime
        m = dtstamp_pattern.match(dtstr)
        if m:
            datetimestamp = datetime(year=int(m.group(1)),
                             month=int(m.group(2)),
                             day=int(m.group(3)),
                             hour=int(m.group(4)),
                             minute=int(m.group(5)))
        else:
            print(f"{dtstr} is not a valid datetime! (Note: to abort the command, enter nothing below.)")

    # request headline
    if headline is None or headline.strip() == "":
        print("Please the 'headline' for the event below (or nothing to abort the command):")
        print(datetimestamp.strftime("%A, %d %B"))
        headline = input(datetimestamp.strftime("[%I:%M %p] ")).strip()

    # exit condn
    if headline == "":
        return

    # instantiate event object
    new_event = au.Event(headline=headline, datetimestamp=datetimestamp)
    game.events.add(new_event)

    print("Type Y to confirm adding the following event:")
    print(new_event.plaintext_headline(with_ts=True))
    resp = input().upper()
    if resp == "Y":
        game.session.commit()
        print(f"Successfully added event. Event id is {new_event.id}.")
        # TODO: link to recording deaths
        #print(f"To record a death in this event, run `adddeath {new_event.id}`")
    else:
        game.session.rollback()
        print("Did not add event.")
        return

if __name__ == "__main__":
    with au.db.Session() as session:
        game = session.scalar(au.Game.select().filter_by(name=args.game))
        if game is None:
            raise au.GameNotFoundError(f"No game with name {args.game}")
        main(game, datetimestamp, args.headline)

else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="addevent", aliases=['addheadline'],
                       description="Record an event in the game.")
    def cmd_add_event(argsraw: str = ""):
        if 'game' not in commands.state:
            print("You need to load a game first!")
            return
        # parse argsraw into a datetimestamp & headline
        m = dtstamp_pattern.match(argsraw)
        if m:
            datetimestamp = datetime(year=int(m.group(1)),
                             month=int(m.group(2)),
                             day=int(m.group(3)),
                             hour=int(m.group(4)),
                             minute=int(m.group(5)))
            headline = m.string[m.end():]
            main(commands.state['game'], datetimestamp, headline)
        else:
            main(commands.state['game'])
