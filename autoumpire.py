# Main AutoUmpire file.
# This brings up a commandline-style interface to type commands

from email_validator import validate_email, EmailNotValidError
from assassins_data import config, engine, WaterStatus, Player
from sqlalchemy.orm import Session
from sqlalchemy import select
from os import getcwd

##### COMMAND FUNCTION DEFS #####

# `help` command
def cmd_help():
    print(
"""AutoUmpire Help:
    add player - Register a player. You will be prompted for their initial signup information.
    exit - Exits AutoUmpire.
    help - Displays this text.
    load csv - Register many players at once, from a CSV file which you will be prompted for.
"""
    )

# `exit` command
def cmd_exit():
    print("Exiting AutoUmpire...")
    exit()

# `add player` command
from actions.add_player import add_player
def cmd_add_player():
    # give exit instructions
    print("(To cancel, leave a field blank)")

    # Ask for email address, validating it.
    email = ""
    invalid_email = True
    while invalid_email:
        # ask for email
        email = input("Enter player's email address or crsID: ")
        # "escape" by leaving blank
        if email == "":
            return
        # validate email
        try:
            emailinfo = validate_email(email, check_deliverability=True)
            email = emailinfo.normalized
        # if email invalid, first assume a crsID was given,
        # so try to validate again with @cam.ac.uk appended
        except EmailNotValidError as e:
            try:
                email = email + "@" + config["default_email_domain"]
                emailinfo = validate_email(email, check_deliverability=True)
                email = emailinfo.normalized
            # if email invalid and a crsID also not given,
            # print the validation error to the user
            # and skip to asking email again
            except:
                print(str(e))
                continue
        # if got to this point email should have been validated
        # check if email already taken
        # (the email column is set to UNIQUE anyway,
        # but this makes it clearer to the user that there's a duplicate)
        with Session(engine) as session:
            res = session.scalars(select(Player).where(Player.email == email)).one_or_none()
        # if email not already in DB, accept it
        if res == None:
            invalid_email = False # not actually necessary but ¯\_(ツ)_/¯
            break
        else:
            print(f"Email {email} already registered for player {res.realname} of {res.college}.")
    print(f"Email address recorded as {email}.")

    # Ask for real name
    realname = str(input("Enter player's full real name: ")).strip().title()
    # "escape" by leaving blank
    if realname == "":
        return

    # Ask for intial pseudonym
    initial_pseudonym = str(input("Enter player's (initial) pseudonym: "))
    # "escape" by leaving blank
    if initial_pseudonym == "":
        return

    # Ask for College
    college = str(input("Enter player's College: ")).strip().title()
    # "escape" by leaving blank
    if college == "":
        return
    # (to-do: maybe add verification)

    # Ask for Address
    address = str(input("Enter player's Address (on a single line): "))
    # "escape" by leaving blank
    if address == "":
        return

    # Ask for water status
    # First list out the options with corresponing indices to respond with
    print("Select water status. Options are:")
    ws_selector = list(WaterStatus)
    [print(f"{index}: {value.value}") for index, value in enumerate(ws_selector)]
    # Then ask for a selection, validating that this selects something
    invalid_selection = True
    while invalid_selection:
        try:
            s = input()
            # "escape" by leaving blank
            if str(s) == "":
                return
            # get corresponding option
            water = ws_selector[int(s)]
        except:
            print(f"`{s}` is not a valid selection.")
        else:
            invalid_selection = False # not actually necessary but ¯\_(ツ)_/¯
            break

    # Ask for notes
    notes = str(input("Enter player notes (one line only): "))
    # no escape because last input anyway

    print(
f"""--Summary of player--
Real Name: {realname}
Email Address: {email}
(Initial) Pseudonym: {initial_pseudonym}
College: {college}
Address: {address}
Water Weapons Status: {water.value}
Notes: {notes}
---
Type Y to add this player.
"""
    )
    if str(input()).upper() == "Y":
        player = Player(
                    realname=realname,
                    email=email,
                    initial_pseudonym=initial_pseudonym,
                    college=college,
                    address=address,
                    water=water,
                    notes=notes
        )
        add_player(player)
    else:
        print("Did not add player.")

# `load csv` command
from actions.load_csv import load_csv, required_headings
def cmd_load_csv():
    print("Enter filepath of CSV file to load initial player dater from.")
    print(f"Current directory is {getcwd()}.")
    print("The CSV must have headings")
    print(', '.join(required_headings))
    print("but these may be in any order.")
    load_csv(str(input("CSV file path: ")))

# registry of commands.
command_reg = {
    "help" : cmd_help,
    "`help`": cmd_help,  # this is an alias in case the user is an idiot
    "`help`.": cmd_help,  # ditto
    "exit": cmd_exit,
    "add player": cmd_add_player,
    "load csv": cmd_load_csv
}


##### COMMANDLINE CODE #####
def main():
    print("Welcome to AutoUmpire Reloaded!")
    print("Type commands below. If you do not know where to start, type `help`.")

    while True:
        cmd = str(input('> ')).strip().lower()
        if cmd in command_reg.keys():
            command_reg[cmd]()
            print(end="") # flushes output; > doesn't show otherwise
        else:
            print("Invalid command. Type `help` to see commands.")

# run `main` only if called from command line.
import sys
if __name__ == '__main__':
    sys.exit(main())