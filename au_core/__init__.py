"""
au_core

This module implements the core logic of AutoUmpire.
"""

from .enums import *
from .config import config
from . import db

# ORM class imports
from .Base import Base
from .Game import Game
from .Registration import Registration
from .Player import Player
from .Assassin import Assassin
from .Pseudonym import Pseudonym
from .Event import Event
from .Report import Report
from .Death import Death

# registers tables for all the ORM models derived from Base
Base.metadata.create_all(db.engine)

# module-level functions
from typing import Optional, Union, Callable, Any, TYPE_CHECKING
from sqlalchemy import select
# type checking only...
from sqlalchemy.orm import Session


class GameNotFoundError(Exception):
    """
    Exception raised when trying to fetch a game but the game is not found
    """


# TODO: change fetch_game_with session to mirror callback_on_game syntax
# TODO: after above, use a function to convert w_session functions to callback functions?
def fetch_game_w_session(session: Session, id: Optional[int] = None, name: Optional[str] = None) -> Game:
    """
    Fetches a game by either id or name, using a passed Session object.
    Only one of the parameters may be set, or a TypeError is raised.
    This is not recommended method for interacting with a game; use callback_on_game instead

    :param session: the sqlalchemy.orm.Session to fetch the game with
    :param id: id of game to fetch
    :param name: name of game to fetch
    :return: Game with the specified id/name
    """
    # require exactly one of id and name as an argument
    fetchmethods = (id, name)
    n = sum(a is not None for a in fetchmethods)
    if n != 1:
        raise TypeError(f"fetch_game expected exactly 1 of {', '.join(fetchmethods)}, got {n}.")

    # if id set, fetch by id
    if id is not None:
        fetchedgame = session.scalars(select(Game).filter_by(id=id)).one_or_none()
        if fetchedgame is None:
            raise GameNotFoundError(f"There is no game with id = {id}")

    #  if name set, fetch by name
    if name is not None:
        fetchedgame = session.scalars(select(Game).filter_by(name=name)).one_or_none()
        if fetchedgame is None:
            raise GameNotFoundError(f"There is no game with name = '{name}'")

    return fetchedgame


def callback_on_game(identifier: Union[int, str], callback: Callable[[Game], Any], autocommit: bool = False) -> Any:
    """
    Fetches an assassins game based on the passed identifier (either name or id, determined based on datatype),
    then runs the callback on it.

    The reason for a callback is that Game objects require a live Session to function properly.
    So that layers built on top of au_core do not have to mess about with Sessions,
    this function ensures the fetched Game object has a live session for the duration of the callback's runtime.
    If this Session is needed in the callback, it can be obtained by the get_session method of the passed Game.

    :param identifier: The name (if str) or id (if int) of the game to run the callback on
    :param callback:  The callback function to run on the fetched game.
    :param autocommit: Whether to commit the database session after (successfully) running `callback`. Defaults to `False`.
    :return: The return value of `callback` run on the fetched game
    """
    with db.Session() as session:
        if type(identifier) is int:
            game = fetch_game_w_session(session, id=identifier)
        elif type(identifier) is str:
            game = fetch_game_w_session(session, name=identifier)
        else:
            raise TypeError(f"callback_on_game expected identifier to be of type str or int, got {type(identifier)}")

        ret = callback(game)
        if autocommit:
            session.commit()
        return ret


class GameNameTakenError(Exception):
    """
    Exception raised when trying to create a new game with the same name as an existing one.
    """


def create_game_w_session(session: Session, name: str) -> Game:
    """
    Creates a new game of Assassins in the AutoUmpire database.

    :param session: the sqlalchemy.orm.Session to create the game with
    :param name: The name that the game to be created. Standard format is "[term name] [year]", e.g. "Lent 2020".
    :return: The created Game
    """
    # first, check whether a game already exists of this name
    try:
        fetch_game_w_session(session, name=name)
    except GameNotFoundError:
        pass
    else:
        raise GameNameTakenError(f"A game with the name {name} already exists.")

    # create the game
    newgame = Game(name=name)
    session.add(newgame)
    # session.commit()
    return newgame


def create_game_then_callback(name: str, callback: Callable[[Game], Any] = lambda x: None,
                              autocommit: bool = True) -> Any:
    """
    The callback-based game-creation function.
    This function to create_game_w_session as callback_on_game is to fetch_game_w_session.

    :param name: The name of the game to create. Standard format is "[term name] [year]", e.g. "Lent 2020".
    :param callback: Function to run on the newly-created Game object. Defaults to a function always returning None
    :param autocommit: Whether to commit the database session after (successfully) running `callback`.
    Defaults to `True` as I can't really see a use case for having this set to `False`.
    :return: The return value of `callback` when run on the created Game
    """
    with db.Session() as session:
        game = create_game_w_session(session, name)
        ret = callback(game)
        if autocommit:
            session.commit()
        return ret
