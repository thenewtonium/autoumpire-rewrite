"""
TargRel.py

Sets up the targetting table, by defining the TargRel class.
"""

from .Base import Base
from .Assassin import Assassin
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKey, select

class TargRel(Base):
    """
    TargRel class

    This is used to store the table of who is targetting who(m).
    Each instance represents an 'edge' in the targetting graph.
    """
    __tablename__ = "targetting_table"
    target_id = mapped_column(ForeignKey(Assassin.id), primary_key=True)
    target: Mapped[Assassin] = relationship(foreign_keys=[target_id])

    assassin_id = mapped_column(ForeignKey(Assassin.id), primary_key=True)
    assassin: Mapped[Assassin] = relationship(foreign_keys=[assassin_id])