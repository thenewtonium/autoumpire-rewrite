"""
Report.py

Defines the Report class
"""

import re
from typing import List, Union, TYPE_CHECKING
from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .Base import Base
from .Pseudonym import Pseudonym
from .Event import Event, parse_pseudonym_refs
from datetime import datetime

class Report(Base):
    """
    Report class

    Represents a report associated to an Event.
    A report has
    - An author (a Pseudonym, rather than a Player)
    - Text body (where references to other players are encoded the same way as in Event headlines)
    - A parent Event
    For internal use, it also has an id (for the primary key) and a datetimestamp (by default when the report is created -
    used for ordering)
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    # TODO: programmatic default as fallback
    datetimestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    event_id = ForeignKey(Event.id)
    author_id = ForeignKey(Pseudonym.id)
    body: Mapped[str]

    event: Mapped[Event] = relationship(back_populates="reports")
    author: Mapped[Pseudonym] = relationship()

    def parsed_body(self) -> List[Union[str, Pseudonym]]:
        """
        :return: Parsed form of this Report's body -- i.e. a list of strings and Pseudonym objects representing this
        Report's body with references to pseudonyms substituted for Pseudonym objects
        """
        return parse_pseudonym_refs(self.body, self.session)
