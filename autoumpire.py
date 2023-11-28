# Main AutoUmpire file.
# This brings up a commandline-style interface to type commands

from email_validator import validate_email, EmailNotValidError
from assassins_data import config, WaterStatus, Player

##### COMMAND FUNCTION DEFS #####

# `help` command
def cmd_help():
    print(
"""AutoUmpire Help:
    add_player - You will be prompted for the signup data to add to the system.
    exit - Exits AutoUmpire.
    help - Displays this text.
"""
    )

# `exit` command
def cmd_exit():
    print("Exiting AutoUmpire...")
    exit()

# `add player` command
from actions.add_player import add_player
def cmd_add_player():
    # Ask for
    realname = str(input("Enter player's full real name: ")).strip().title()

    # Ask for email address, validating it.
    email = ""
    invalid_email = True
    while invalid_email:
        email = input("Enter player's email address or crsID: ")
        try:
            emailinfo = validate_email(email, check_deliverability=True)
            email = emailinfo.normalized
            invalid_email = False
        except EmailNotValidError as e:
            # if there is a error, assume first that it is is a crsID, and re-verify
            try:
                email = email + "@" + config["default_email_domain"]
                emailinfo = validate_email(email, check_deliverability=True)
                email = emailinfo.normalized
                invalid_email = False
            except:
                print(str(e))
    print(f"Email address recorded as {email}.")

    # Ask for intial pseudonym
    initial_pseudonym = str(input("Enter player's (initial) pseudonym: "))

    # Ask for College
    college = str(input("Enter player's College: ")).strip().title()
    # (to-do: maybe add verification)

    # Ask for Address
    address = str(input("Enter player's Address (on a single line): "))

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
            water = ws_selector[int(s)]
        except:
            print(f"`{s}` is not a valid selection.")
        else:
            invalid_selection = False

    # Ask for notes
    notes = str(input("Enter player notes (one line only): "))

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


# registry of commands.
command_reg = {
    "help" : cmd_help,
    "`help`": cmd_help,  # this is an alias in case the user is an idiot
    "`help`.": cmd_help,  # ditto
    "exit": cmd_exit,
    "add player": cmd_add_player
}


##### COMMANDLINE CODE #####
def main():
    print("Welcome to AutoUmpire Reloaded!")
    print("Type commands below. If you do not know where to start, type `help`.")

    while True:
        cmd = str(input('> ')).strip().lower()
        command_reg[cmd]()

# run `main` only if called from command line.
import sys
if __name__ == '__main__':
    sys.exit(main())