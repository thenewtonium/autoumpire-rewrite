"""
TargRel.py

Sets up the targetting table, by defining the TargRel class.
"""

from .Base import Base
#from .Assassin import Assassin
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred
from sqlalchemy import ForeignKey

# TODO: put CHECK constraint on target and assassin game_id's
class TargRel(Base):
    """
    TargRel class

    This is used to store the table of who is targetting who(m).
    Each instance represents an 'edge' in the targetting graph.
    """

    __tablename__ = "targetting_table"
    target_id = mapped_column(ForeignKey("assassins.id", ondelete="CASCADE"), primary_key=True)
    target: Mapped["Assassin"] = deferred(relationship(foreign_keys=[target_id]))

    assassin_id = mapped_column(ForeignKey("assassins.id", ondelete="CASCADE"), primary_key=True)
    assassin: Mapped["Assassin"] = deferred(relationship(foreign_keys=[assassin_id]))