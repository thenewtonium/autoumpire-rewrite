"""
add_report.py

A command line script to add a report to an assassins event.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("body", help="The body of the report to add.", type=str)
    parser.add_argument("-a", "--author",
                        help="The id of pseudonym to use for the author of the report.",
                        type=int, required=True)
    parser.add_argument("-e", "--event",
                        help="The id of the event to attach the report to.",
                        type=int, required=True)
    parser.add_argument("-g", "--game", help="The name of the game in which the event occurred..",
                        type=str, required=True)
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au

if __name__ == "__main__":
    def callback(game: au.Game):
        session = game.session

        event = session.get(au.Event, args.event)
        author = session.get(au.Pseudonym, args.author)

        new_report = au.Report(author=author, body=args.body)
        event.reports.append(new_report)

        print(f"Updated event (id={args.event}) now as follows:")
        print(event.plaintext_parsed_full())
        resp = input("Enter Y to confirm addition of report: ").upper()
        if resp == "Y":
            session.commit()
            print(f"Successfully added report (id={new_report.id})")
        else:
            print("Did not add report.")
            session.rollback()
    try:
        au.callback_on_game(args.game, callback, autocommit=False)
    except au.GameNotFoundError:
        print(f"Error: no game found with name {args.game}.")
