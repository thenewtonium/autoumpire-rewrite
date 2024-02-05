"""
au_cli/__main__.py

The AutoUmpire command line interface
"""

import pathlib
import sys

import au_core as au

import commands
# command files
# TODO: move these into a seperate folder
import help
import load_csv
import search_player
import view_player

@commands.register(aliases=["exit"], description="Exit this program.")
def quit(*args):
    """
    Command to exit the CLI
    """
    exit()


@commands.register(primary_name="switchgame",
                   aliases=['loadgame'],
                   description="Load / create an assassins game. ",
                   help_text="""Run with no arguments, this command shows you all games currently in the program's database.
    Run with an integer as an argument, it loads the game with the corresponding numerical id, if it exists.
    Run with a name as an argument, it loads the game of that name if it exists, or creates a new game if it does not.
    Usage: switchgame [id | name]""")
def load_game(arg: str = ""):
    """
    Command to load a a game. If no argument is passed then it displays the games available.
    If an integer is passed it tries to fetch by id.
    If a string is passed it tries to fetch by name,
    and if no such game exists, offers to create it
    :param arg:
    """
    session = commands.state['session']
    # case where no game name is given
    if arg == "":
        # first display the games that exist
        games = session.scalars(au.Game.select(au.Game.name, au.Game.id).order_by(au.Game.id))
        print("The following games were found in the database:")
        [print(f"{g.id}: {g.name}") for g in games]
        print()
        # then ask the user to select a game
        print("Enter the numerical id of the game you wish to load, or enter a name for a new game.")
        print("To cancel, enter nothing.")
        arg = input(":").strip()
        # cancel condn
        if arg == "":
            return
    # determine whether the user entered an id or a name
    try:
        id = int(arg)
    except ValueError as e:
        id = None
        name = str(arg.strip())
    # if the user entered an id, fetch by id
    if id:
        game = session.get(au.Game, id)

        if not game:
            print(f"{id} is not in the list!")

    # otherwise we try to load the game by name then create it if it doesn't exist
    else:
        game = session.scalar(au.Game.select(au.Game.id, au.Game.name).filter_by(name=name))
        # if loading failed, create a new game
        if game is None:
            print(f"No game found with name {name}")
            game = au.Game(name=name)
            session.add(game)
            session.commit()
            print(f"Created a NEW game, with id {game.id}, called {game.name}")
        # announce loading of game in either case.
        print(f"Loaded game {game.name}.")
    # put the loaded game in the state dict
    commands.state['game'] = game



with au.db.Session() as session:
    commands.state['session'] = session

    load_game()
    # if player didn't load a game then quit
    if 'game' not in commands.state:
        print("Quitting...")
        sys.exit()

    # print welcome text once loaded a game
    dir = pathlib.Path(__file__).parent;
    # print the welcome text set in `welcome.txt`
    with open((dir / "welcome.txt").resolve()) as f:
        print("".join(f.readlines()))

    while True:
        # load the name of the current game for display purposes
        if 'game' in commands.state:
            gamename = commands.state['game'].name
        else:
            gamename = ""
        # displays a dagger emoji where the user inputs their command
        whole_cmd = str(input(gamename + u' \U0001F5E1 '))
        # we look for the first space in order to extract the command name
        i = whole_cmd.find(" ")
        # how to extract the name depends on whether the input has a space in or not
        if i != -1:
            cmd_head = whole_cmd[:i]
            cmd_args = whole_cmd[i:].lstrip()
        else:
            cmd_head = whole_cmd
            cmd_args = ""
        # throw error if command doesn't exist
        if cmd_head not in commands.COMMANDS:
            raise commands.InvalidCommandError(f'No command exists called `{cmd_head}`')
        # we execute the named command with the subsequent text and the state dict passed as arguments
        try:
            commands.COMMANDS[cmd_head].f(cmd_args)
        except Exception as e:
            print(e)

