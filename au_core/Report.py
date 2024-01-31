"""
Report.py

Defines the Report class
"""

from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .Base import Base
from .Pseudonym import Pseudonym
from .Event import Event, parsing_pattern
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
    event_id = mapped_column(ForeignKey(Event.id))
    author_id = mapped_column(ForeignKey(Pseudonym.id))
    body: Mapped[str]

    # TODO: programmatic default as fallback
    # (only used internally for ordering of reports)
    datetimestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped[Event] = relationship(back_populates="reports")
    author: Mapped[Pseudonym] = relationship()

    def author_css_class(self) -> str:
        """
        :return: The css class of the author at the time the parent event happened.
        """
        return self.author.css_class(self.event.datetimestamp)

    def HTML_body(self) -> str:
        """
        :return: The HTML-formatted body of this report.
        """
        return parsing_pattern.sub(lambda m: self.event._HTML_repl_ref(m), self.body)

    def plaintext_body(self):
        """
        :return: The parsed plaintext body of this report.
        """
        return parsing_pattern.sub(lambda m: self.event._plaintext_repl_ref(m), self.body)