"""
Event.py

Defines the `Event` class.
"""

import re
from typing import List, Union
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from .Base import Base
from .Pseudonym import Pseudonym
from .Player import Player
from datetime import datetime

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
    game_id = mapped_column(ForeignKey("games.id"))

    game: Mapped["Game"] = relationship(back_populates="events")
    reports: Mapped[List["Report"]] = relationship(back_populates="event", order_by="Report.datetimestamp")

    # TODO: HTML-formatted headline using formatting functions in the Player and Pseudonym objects

    def HTML_headline(self) -> str:
        """
        :return: The HTML formatted headline of the event. (Not including datetimestamp)
        """
        return parse_refs_into_HTML(self.headline, self.session)

    def plaintext_headline(self) -> str:
        """
        :return: The parsed plaintext headline of the event.
        """
        return parse_refs_into_plaintext(self.headline, self.session)

    def plaintext_full(self) -> str:
        """
        :return: A plaintext form of the whole event including timestamp and reports.
        """
        return  "---\n"\
                + f"[{datetime.strftime(self.datetimestamp, '%I:%M %p')}] {self.plaintext_parsed_headline()}\n"\
                + "---\n"\
                + "\n\n\n".join([f"{x.author.text} writes\n{x.body}" for x in self.reports]) \
                + "\n---"

# Below are functions for decoding and rendering headlines encoded with references to Pseudonyms and Players,
# of the forms <@xxxx> and <#xxxx> respectively.
# TODO: docstrings

# TODO: allow escaping?
# regex pattern for identifying pseudonym/player references in texts
ref_capture_pattern = re.compile(r"(<[@#]\d+>)")
# regex pattern for extracting the id of the pseudonym/player from a reference
parsing_pattern = re.compile(r"<([@#])(\d+)>")

def _convert_ref(ref: str, session: Session) -> Union[str, Pseudonym]:
    """
    Helper function for parse_pseudonym_refs.
    This converts a reference into a Pseudonym or Player object if the reference is valid,
    otherwise it returns the original string.
    :param ref: String reference to a pseudonym or player
    :param game: The sqlalchemy Session to
    :return: Pseudonym or Player object corresponding to the referenced pseudonym or player, if valid,
    else the original string.
    """
    m = re.match(parsing_pattern, ref)

    # return original string if not a valid pseudonym reference
    if m is None:
        return ref

    # extract "type marker" capture group from match
    type = m.group(1)
    # extract id capture group from match
    id = int(m.group(2))

    if type == "@":
        return session.get(Pseudonym, id)
    elif type == "#":
        return session.get(Player, id)
    else:
        return ref

# TODO: change to use Game object
def _parse_refs(text: str, session: Session) -> List[Union[str,Pseudonym,Player]]:
    # split text by references, keeping the 'separators'
    l = re.split(ref_capture_pattern, text)

    # convert each of the references into Pseudonym or Player objects
    return [_convert_ref(s, session) for s in l]

def HTML_render(obj: Union[str, Pseudonym, Player]):
    """
    Helper function that gives the HTML rendering of a Pseudonym of Player object, or a string.
    For a Pseudonym, it wraps the text of the pseudonym in a <span> of the appropriate class.
    For a Player, it lists the player's pseudonyms separated by "AKA", then gives their real name in brackets.
    For a string, it simply reproduces the string.
    :param obj: The object to render as HTML
    :return: The appropriate HTML rendering of the object.
    """
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, Pseudonym):
        return obj.HTML_render()
    elif isinstance(obj, Player):
        return obj.HTML_render()
    else:
        raise TypeError(f"HTML_render expected argument of type str, Pseudonym, or Player; received {type(obj)}")

def parse_refs_into_HTML(text: str, session: Session):
    parsed = _parse_refs(text, session)
    return "".join( (HTML_render(x) for x in parsed))

def plaintext_render(obj: Union[str, Pseudonym, Player]):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, Pseudonym):
        return obj.text
    elif isinstance(obj, Player):
        return " AKA ".join( (p.text for p in obj.pseudonyms) ) + f" ({obj.reg.realname})"
    else:
        raise TypeError(f"plaintext_render expected argument of type str, Pseudonym, or Player; received {type(obj)}")

def parse_refs_into_plaintext(text: str, session: Session) -> str:
    parsed = _parse_refs(text, session)
    return "".join( (plaintext_render(x) for x in parsed) )

