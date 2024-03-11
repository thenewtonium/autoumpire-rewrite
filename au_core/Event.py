"""
Event.py

Defines the `Event` class.
"""

import re
from typing import List
from sqlalchemy import ForeignKey, DateTime, ScalarResult
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped
from .Base import Base
from .Game import Game
from .Pseudonym import Pseudonym
from datetime import datetime, timedelta

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

    def raw_full(self) -> str:
        """
        :return: The "raw" form of plaintext_full, i.e. the whole event & reports with <@xxx> references
        rather than parsed pseudonyms
        """
        return "---\n" \
               + f"[{datetime.strftime(self.datetimestamp, '%H:%M')}] {self.headline}\n" \
               + "---\n" \
               + "\n\n\n".join([f"{x.author.reference()} writes\n{x.body}" for x in self.reports]) \
               + "\n---"

Game.events: WriteOnlyMapped[List[Event]] = relationship(Event, lazy="write_only",
                                                         back_populates="game", passive_deletes=True)

#### INSERTIONS INTO `Game` ####

def Game_generate_headlines(self) -> str:
    from .templates import env
    template = env.get_template("headlines.jinja")

    events = self.session.scalars(self.events.select().order_by(Event.datetimestamp))
    return template.render(events=events)
Game.generate_headlines = Game_generate_headlines

def Game_events_in_week(self, week_n: int) -> ScalarResult[Event]:
    """
    :param week_n: The week number to query events in.
    :return: The result of querying Event objects whose datetimestamp falls in week_n
    """
    d = self.started
    upper_bound = datetime(year=d.year, month=d.month, day=d.day) + timedelta(weeks=week_n)
    lower_bound = upper_bound - timedelta(weeks=1)

    return self.session.scalars( self.events.select().where(
        (lower_bound <= Event.datetimestamp) & (Event.datetimestamp < upper_bound)
    ))
Game.events_in_week = Game_events_in_week

def Game_generate_news_page(self, week_n) -> str:
    from .templates import env
    template = env.get_template("news.jinja")

    return template.render(events=self.events_in_week(week_n), week_n=week_n)
Game.generate_news_page = Game_generate_news_page