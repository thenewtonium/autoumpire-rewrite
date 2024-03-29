"""
Base.py

Defines the Base class for all the ORM models to inherit from, so that SQLAlchemy can relate them together.
"""

from sqlalchemy.orm import DeclarativeBase, Session, load_only
from sqlalchemy import select, Select

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
    def select(self, *columns_to_load) -> Select:
        """
        :param *columns_to_load: positional arguments are passed to a load_only option on the select,
        i.e. which attributes of the class should be selected.
        :return: A select clause on this object
        """
        return select(self).options(*(load_only(attr) for attr in columns_to_load))


    # nice printed representation of ORM model instances
    def __repr__(self) -> str:
        return f"{type(self).__name__}({','.join([f'{c.key}={self.__getattribute__(c.key)}' for c in self.__table__.columns if self.__getattribute__(c.key) is not None])})"