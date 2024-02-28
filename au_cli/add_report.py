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
    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au
from typing import Optional
from view_reports import EventNotFoundError

# TODO: handle non-id parameters
def main(game: Optional[au.Game] = None,
         event_id: Optional[int] = None,
         author_id: Optional[int] = None,
         body: Optional[str] = None):
    if event_id is None:
        event_id = int(input("Enter the ID of the event to attach the report to: "))
    if game is None:
        session = au.db.Session()
        need_to_close_session = True
        event = session.get(au.Event, event_id)
    else:
        session = game.session
        event = session.scalar(game.events.select().filter_by(id=event_id))
        need_to_close_session = False

    if event is None:
        raise EventNotFoundError(f"There is no event with id {event_id}")

    print("You are adding a report to the following event:")
    print(event.datetimestamp.strftime("%A, %d %B %Y"))
    print(event.plaintext_headline(True))
    print("---")
    print(f"(Raw headline: {event.headline})")

    if author_id is None:
        author_id = int(input("Enter the ID of pseudonym for the author of the report: "))
    author = session.get(au.Pseudonym, author_id)

    if body is None or body.strip() == "":
        print("Enter the text of the report:")
        body = input().strip()
    new_report = au.Report(author=author, body=body)
    event.reports.append(new_report)

    print(f"Updated event {event_id} now as follows:")
    print(event.plaintext_full())
    resp = input("Enter Y to confirm addition of report: ").upper()
    if resp == "Y":
        session.commit()
        print(f"Successfully added report (id={new_report.id})")
    else:
        print("Did not add report.")
        session.rollback()

    if need_to_close_session:
        session.close()

if __name__ == "__main__":
    main(None, args.event, args.author, args.body)
else:
    import commands
    # command used by the main cli program
    @commands.register(primary_name="addreport", aliases=['add_report'],
                       description="Add a report to an event")
    def cmd_add_event(argsraw: str = ""):
        game = commands.state['game']
        main(game, int(argsraw))
