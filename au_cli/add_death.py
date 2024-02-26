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
                        type=int)

    parser.add_argument("-k", "--killer",
                        help="The id of the Player who made the kill.",
                        type=int)

    parser.add_argument("-v", "--victim",
                        help="The id of the Player who died.",
                        type=int)

    parser.add_argument("-l", "--licit",
                        help="Include this flag to mark the kill as licit regardless of targets, wantedness, etc.",
                        action="store_true")

    args = parser.parse_args()

# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import au_core as au
from typing import Optional


def same_game(obj1, obj2):
    return (obj1 is not None) and (obj2 is not None) and (obj1.game_id == obj2.game_id)

def main(event_id: Optional[int] = None,
         killer_id: Optional[int] = None,
         victim_id: Optional[int] = None,
         licit: Optional[bool] = None):
    with au.db.Session() as session:
        # get event
        if event_id is None:
            event_id = int(input("Enter the id of the event where this death happened: ").strip())
        event = session.get(au.Event, event_id)
        if event is None:
            print(f"Error - no event exists with id {event_id}")
            return

        # get victim
        if victim_id is None:
            victim_id = int(input("Enter the id of the VICTIM: ").strip())
            return
        victim = session.get(au.Player, victim_id)
        if not same_game(victim, event):
            print(f"Error - no player with id {victim_id} exists in game {event.game.name}")
            return

        # get killer
        if killer_id is None:
            killer_id = int(input("Enter the id of the KILLER: ").strip())
            return
        killer = session.get(au.Player, killer_id)
        if not same_game(killer, event):
            print(f"Error - no player with id {killer_id} exists in game {event.game.name}")
            return

        # determine licitness
        if licit is None:
            licit, reason = victim.licit_for(killer)
            if not licit:
                print(f"This kill is illicit {reason}.")
                print("Enter Y below if it was licit anyway,"
                             " for example because the victim was bearing, "
                             "otherwise just press enter")
                resp = input(":").strip().upper()
                if resp == "Y":
                    licit = True


        new_death = au.Death(event_id=event.id, victim_id=victim.id, killer_id=killer.id, licit=licit)

        print(f"Enter Y to confirm the {'licit' if licit else 'illicit'} death of {victim.reg.realname} at the hands of "
              f"{killer.reg.realname}, during the following event:")
        print(event.plaintext_headline())
        resp = input().upper()
        if resp == "Y":
            session.add(new_death)
            session.commit()
            print("Successfuly added death.")
            event.game.assign_targets()
        else:
            session.rollback()
            print("Did not add the death.")

if __name__ == "__main__":
    main(event_id=args.event, killer_id=args.killer, victim_id=args.victim, licit=(True if args.licit else None))
else:
    import re
    keyword_pattern = re.compile(r"(at|by|on|licitl|illicit)")

    import commands
    from load_csv import chunk
    # command used by the main cli program
    # TODO: add help info about using cli command to search events, once this is created!
    # TODO: add help info about using the links on the headline pages to find event ids.
    @commands.register(primary_name="addkill", aliases=['add_kill'],
                       description="Record a kill",
                       help_text="""Records a kill during an existing event.
The event is referenced by its id, which is given to you its creation.
Syntax: 
addkill [licit | illicit] [at <event id>] [by <killer id>] [on <victim id>]""")
    def cmd_add_death(argsraw: str = ""):
        # parse the arguments given
        args = {}
        for kw, arg in chunk(keyword_pattern.split(argsraw)[1:], 2):
            args[kw] = arg.strip()

        if "licit" in args and "illicit" in args:
            print("Error - you have tried to mark the kill as both licit and illicit!")
            return
        with au.db.Session() as session:
            if "at" in args:
                event_id = int(args['at'])
            else:
                event_id = None
            if "by" in args:
                killer_id = int(args['by'])
            else:
                killer_id = None
            if "on" in args:
                victim_id = int(args['on'])
            else:
                victim_id = None
            if "licit" in args:
                if "illicit" in args:
                    print("Error - a kill cannot be both licit and illicit!")
                    return
                licit = True
            elif "illicit" in args:
                licit = False
            else:
                licit = None

            main(event_id=event_id,
                 killer_id=killer_id,
                 victim_id=victim_id,
                 licit=licit)






