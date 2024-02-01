"""
au_cli/__main__.py

The AutoUmpire command line interface
"""

import pathlib
dir = pathlib.Path(__file__).parent;
# print the welcome text set in `welcome.txt`
with open( (dir / "welcome.txt").resolve() ) as f:
    print("".join(f.readlines()))

import command_registry
# command files
# TODO: move these into a seperate folder
import help

@command_registry.register(aliases=["exit"], description="Exit this program.")
def quit(arg: str):
    """
    Command to exit the CLI
    """
    exit()

import au_core as au

with au.db.Session() as session:
    # TODO: create gamestate dict which is passed to commands
    # TODO: then separate game loading into a command, which is also called at startup
    # first display the games that exist
    games = session.scalars(au.Game.select(au.Game.name, au.Game.id).order_by(au.Game.id))
    print("The following games were found in the database:")
    [print(f"{g.id}: {g.name}") for g in games]
    print()
    print("Enter the number of the game you wish to load, or type a name to create a new game.")
    game = None
    while not game:
        res = input("> ")
        try:
            id = int(res)
        except ValueError as e:
            id = None
            name = str(res.strip())

        if id:
            game = session.get(au.Game, id)

            if not game:
                print(f"{id} is not in the list!")
        else:
            # TODO: create a helper fn for all these Y confirmations
            response = input(f"Type Y to create a game called {name}: ").upper()
            if response == "Y":
                game = au.Game(name=name)
                session.add(game)
                session.commit()
                print(f"Successfully created a new game with name {game.name}")
            else:
                print("Did not create a new game. Enter a number for a game in the previous list, or the name for a new game.")

    print(f"Loaded game {game.name}.")

    while True:
        # displays a dagger emoji where the user inputs their command
        whole_cmd = str(input(game.name + u' \U0001F5E1 '))
        i = whole_cmd.find(" ")
        if i != -1:
            cmd_head = whole_cmd[:i]
            cmd_args = whole_cmd[i:].strip()
        else:
            cmd_head = whole_cmd
            cmd_args = ""
        try:
            command_registry.COMMANDS[cmd_head].f(cmd_args)
        except Exception as e:
            print(e)

