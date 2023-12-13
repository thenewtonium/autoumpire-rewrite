"""
Base.py

Defines the Base class for all the ORM models to inherit from, so that SQLAlchemy can relate them together.
"""

from sqlalchemy.orm import DeclarativeBase, Session

class Base(DeclarativeBase):
    """The declarative base class used by all AutoUmpire's ORM models"""

    def get_session(self) -> Session:
        """
        :return: The sqlalchemy.orm.Session to which this object is attached.
        """
        return Session.object_session(self)