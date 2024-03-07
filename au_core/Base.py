"""
Base.py

Defines the Base class for all the ORM models to inherit from, so that SQLAlchemy can relate them together.
"""

from sqlalchemy.orm import DeclarativeBase, Session, load_only, Mapped, mapped_column
from sqlalchemy import select, Select
from typing import Callable, Any, List, Optional, Set
from dataclasses import dataclass, field

class Base(DeclarativeBase):
    """
    The declarative base class used by all AutoUmpire's ORM models

    On top of the standard DeclarativeBase class I define a `session` property that fetches the object's session.
    This is in order to make au_core self-contained;
    otherwise we would have to import the sqlalchemy.orm.Session class.
    """

    @property
    def session(self) -> Session:
        """
        :return: The sqlalchemy.orm.Session to which this object is attached.
        """
        return Session.object_session(self)

    @classmethod
    def select(cls, *columns_to_load) -> Select:
        """
        :param *columns_to_load: positional arguments are passed to a load_only option on the select,
        i.e. which attributes of the class should be selected.
        :return: A select clause on this object
        """
        return select(cls).options(*(load_only(attr) for attr in columns_to_load))

    @classmethod
    def method(cls, f: Callable[..., Any]) -> Callable[..., Any]:
        """
        A function decorator for adding additional methods to classes post-declaration.
        This is useful e.g. for methods of `Game` that refer to classes defined later.
        However, IDEs will not recognise methods registered in this way, so the 'classic' approach may be preferable.
        :return: A function decorator
        """
        setattr(cls, f.__name__, f)


    # nice printed representation of ORM model instances
    def __repr__(self) -> str:
        return f"{type(self).__name__}({','.join([f'{c.key}={self.__getattribute__(c.key)}' for c in self.__table__.columns if self.__getattribute__(c.key) is not None])})"

class MissingDependencyError(Exception):
    """Exception raised when trying to register a function to a plugin hook with a dependency not registered to the hook"""

@dataclass
class PluginHook:
    """
    Defines a 'hook' by which plugins can attach functions to be executed at a given event, e.g. the start of a game
    """
    hooked_functions: List[Callable] = field(default_factory=lambda: [])

    def register(self, awaits: Optional[Set[Callable]] = {}) -> Callable[[Callable], Callable]:
        """
        :param awaits:
        :return: a function decorator registering f to this PluginHook with priority above all elements of `awaits`
        """
        def register_dec(f: Callable):
            """
            Registers the function f in the list of hooked functions at the first position after all elements of `awaits`
            :param f: The function to register to the hook
            :return: An unchanged f
            """
            for i in range(len(self.hooked_functions)):
                if len(awaits) == 0:
                    self.hooked_functions.insert(i, f)
                    break
                else:
                    awaits.discard(self.hooked_functions[i])

            # throw error if we couldn't insert due to a missing dependency
            if len(awaits) > 0:
                raise MissingDependencyError(f"{f.__name__} has {', '.join([a.__name__ for a in awaits])} as dependencies, "
                                             f"but these aren't registered to the PluginHook {self.__name__}")
            return f
        return register_dec

    # 'private' because should never be called directly except by the event that triggers the hook
    def _execute(self, *args, **kwargs):
        """
        Executes all the functions hooked to this PluginHook, in order of priority.
        :param args: Positional arguments are passed to each hooked function
        :param kwargs: Keyword arguments are passed to each hooked function
        """
        for hf in self.hooked_functions:
            # TODO: decide what to do about errors
            hf(*args, **kwargs)

    def _execute_return_last(self, *args, **kwargs) -> Any:
        """
        Executes all hooked functions as `_execute`, but returns the *last non-`None` return value`.
        :param args: Positional arguments are passed to each hooked function
        :param kwargs: Keyword arguments are passed to each hooked function
        :return: The last non-`None` return value of the hooked functions, executed in order of priority.
        """
        ret = None
        for hf in self.hooked_functions:
            r = hf(*args, **kwargs)
            if r is not None:
                ret = r
        return ret

    def _execute_break_at_return(self, *args, **kwargs) -> Any:
        """
        Executes hooked functions in order until the first non-`None` return value, and returns this.
        :param args: Positional arguments are passed to each hooked function
        :param kwargs: Keyword arguments are passed to each hooked function
        :return: The first non-`None` value returned when executing hooked functions in order of priority
        """
        for hf in self.hooked_functions:
            r = hf(*args, **kwargs)
            if r is not None:
                return r





