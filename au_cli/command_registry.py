"""
command_registry.py

Defines a decorator that registers a function as a command,
and a registry for the main program to look up commands.
"""

from typing import Optional, List, Callable
from dataclasses import dataclass, field

# registry of commands
COMMANDS = {}

# cli state, for passing data between commands
state = {}

@dataclass
class Command:
    """Class for all the information about a command"""
    f: Callable[[str], None]
    primary_name: str
    description: str = ""
    help_text: str = ""
    aliases: List[str] = field(default_factory=lambda: [])

def register(aliases: Optional[List[str]] = [], **kwargs):
    """
    Function decorator to register a command.
    All keyword arguments are passed to the Command constructor.
    A command must take a string of arguments as its first parameter.
    :return: An unmodified function
    """
    def register_decorator(func: Callable[[str], None]):
        # note: have to use kwargs for this scope to access the arg passed to the original function
        if "primary_name" not in kwargs:
            kwargs["primary_name"] = func.__name__

        cmd = Command(f=func, aliases=aliases, **kwargs)

        aliases.append(kwargs["primary_name"])
        for name in aliases:
            COMMANDS[name] = cmd
        return func
    return register_decorator

class InvalidCommandError(Exception):
    """
    Exception to raise when the user tries to call a command that doesn't exist.
    """