"""
au_cli/help.py

Implements the `help` command
"""

import command_registry
from typing import Optional

@command_registry.register(primary_name='help',
                           aliases=["`help`", "`help`."],
                           description="Displays help text",
                           help_text="""When run without an argument, lists available commands with brief descriptions.
With an argument, displays help information for that command.
Usage: help [command_name]""")
def clihelp(command_name: str = ""):
    if command_name == "":
        print("Available commands:")
        cmd_names = [v for k, v in command_registry.COMMANDS.items() if v.primary_name == k]
        cmd_names.sort(key=lambda x: x.primary_name)
        [print(f"- {n.primary_name}: {n.description}") for n in cmd_names]
    elif command_name not in command_registry.COMMANDS:
        raise command_registry.InvalidCommandError(f"No command exists of the name {command_name}")
    else:
        cmd = command_registry.COMMANDS[command_name]
        print(f"{cmd.primary_name}: {cmd.description}")
        print(f"Aliases: " + ", ".join(cmd.aliases))
        print(cmd.help_text)

if __name__ == "__main__":
    help("")