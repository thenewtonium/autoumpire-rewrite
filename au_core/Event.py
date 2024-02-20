"""
Event.py

Defines the `Event` class.
"""

import re
from typing import List, Union
from sqlalchemy import ForeignKey, DateTime, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from .Base import Base
from .Pseudonym import Pseudonym
from .Player import Player
from datetime import datetime

# TODO: allow escaping?
# regex pattern for extracting the id of the pseudonym/player from a reference
parsing_pattern = re.compile(r"<([@#])(\d+)>")

class Event(Base):
    """
    Event class

    This represents an "event" in assassins.
    Generally, this will be either a kill or an attempt.
    An event has
    - a datetimestamp
    - a headline
    - associated reports
    - a parent Game

    In the headline, players should be represented in the format <@xxxxxxxx>,
    where xxxxxxxx is replaced by the id of the **pseudonym** to use for them.
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    headline: Mapped[str]
    datetimestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    game_id = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))

    game: Mapped["Game"] = relationship(back_populates="events")
    reports: Mapped[List["Report"]] = relationship(back_populates="event", order_by="Report.datetimestamp")

    def _HTML_repl_ref(self, m: re.Match) -> str:
        id = int(m[2])
        p = self.session.get(Pseudonym, id)
        if m[1] == "@":
            # TODO: move rendering code here!
            return p.HTML_render(css_class=p.css_class(self.datetimestamp))
        elif m[1] == "#":
            return p.owner.HTML_render(css_class=p.css_class(self.datetimestamp))

    def _plaintext_repl_ref(self, m: re.Match) -> str:
        id = int(m[2])
        p = self.session.get(Pseudonym, id)
        if m[1] == "@":
            return p.text
        elif m[1] == "#":
            return p.owner.plaintext_render()
        else:
            return

    def week(self) -> int:
        """
        :return: The week number in which this event occurred
        """
        return 1 + (self.datetimestamp.date() - self.game.started.date()).days // 7

    def HTML_headline(self) -> str:
        """
        :return: The HTML formatted headline of the event. (Not including datetimestamp)
        """
        return parsing_pattern.sub(lambda m: self._HTML_repl_ref(m), self.headline)

    def plaintext_headline(self, with_ts: bool = False) -> str:
        """
        :param with_ts: Whether to include the timestamp in the headline. Defaults to False.
        :return: The parsed plaintext headline of the event.
        """
        return ((self.datetimestamp.strftime("[%I:%M %p] ") if with_ts else "") +
                parsing_pattern.sub(lambda m: self._plaintext_repl_ref(m), self.headline))

    def plaintext_full(self) -> str:
        """
        :return: A plaintext form of the whole event including timestamp and reports.
        """
        return  "---\n"\
                + f"[{datetime.strftime(self.datetimestamp, '%I:%M %p')}] {self.plaintext_headline()}\n"\
                + "---\n"\
                + "\n\n\n".join([f"{x.author.text} writes\n{x.plaintext_body()}" for x in self.reports]) \
                + "\n---"
