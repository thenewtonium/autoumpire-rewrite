"""
add_death.py

A command line script to register a death in assassins.
"""

# parse command line arguments first so that --help doesn't boot up au_core
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--event",
                        help="The id of the event where the death happened.",
                        type=int, required=True)

    parser.add_argument("-k", "--killer",
                        help="The id of the Player who made the kill.",
                        type=int, required=True)

    parser.add_argument("-v", "--victim",
                        help="The id of the Player who died.",
                        type=int, required=True)

    parser.add_argument("-l", "--licit",
                        help="Include this flag to mark the kill as licit regardless of targets, wantedness, etc.",
                        action="store_true")

    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au

if __name__ == "__main__":
    with au.db.Session() as session:
        event = session.get(au.Event, args.event)
        # TODO: verify players are in correct game
        victim = session.get(au.Player, args.victim)
        killer = session.get(au.Player, args.killer)
        licit = args.licit
        if not licit:
            licit = event.game.is_kill_licit(victim=victim, killer=killer)

        new_death = au.Death(event_id=event.id, victim_id=victim.id, killer_id=killer.id, licit=licit)

        print(f"Enter Y to confirm the {'licit' if licit else 'illicit'} death of {victim.reg.realname} at the hands of "
              f"{killer.reg.realname}, during the following event:")
        print(event.plaintext_headline())
        resp = input().upper()
        if resp == "Y":
            session.add(new_death)
            session.commit()
            print("Successfuly added death.")
        else:
            session.rollback()
            print("Did not add the death.")
