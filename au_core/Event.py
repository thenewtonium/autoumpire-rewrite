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

    def parsed_headline(self) -> List[Union[str, Pseudonym]]:
        """
        :return: Parsed form of this Event's headline -- i.e. a list of strings and Pseudonym objects representing this
        Event's headline with references to pseudonyms substituted for Pseudonym objects
        """
        return parse_refs(self.headline, self.session)

    def plaintext_parsed_headline(self) -> str:
        """
        :return: This Event's headline with pseudonym references replaced by the text of the pseudonyms
        """
        return f"[{self.datetimestamp}] "\
               + "".join(
            [x.text if isinstance(x, Pseudonym)
                else " AKA ".join([y.text for y in x.pseudonyms]) + f" ({x.reg.realname})" if isinstance(x,Player)
                else x
             for x in self.parsed_headline()
            ]
        ).strip()

    def plaintext_parsed_full(self) -> str:
        """
        :return: A plaintext form of the whole event including reports.
        """
        return  f"---\n{self.plaintext_parsed_headline()}\n---\n"\
                + "\n\n\n".join([f"{x.author.text} writes\n{x.body}" for x in self.reports]) \
                + "\n---"


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
def parse_refs(text: str, session: Session) -> List[Union[str,Pseudonym,Player]]:
    """
    Parses a text with references to pseudonyms in the form <@xxxxx> into a list of strings and Pseudonym objects,
    where the Pseudonym objects "take the place" of the <@xxxxx>'s in the original text.
    :param text: Text with pseudonym references
    :param session: The sqlalchemy Session to use to parse the pseudonyms
    :return: List representing the text, with references of the form <@xxxxx> where xxxxx is an integer
    (of any number of digits) replaced by Pseudonym objects corresponding to the pseudonym with id xxxxx,
    and references of the form <#xxxxx> replaced by Player objects corresponding to the player with id xxxxx.
    """
    # split text by references, keeping the 'separators'
    l = re.split(ref_capture_pattern, text)

    # convert each of the references into Pseudonym or Player objects
    return [_convert_ref(s, session) for s in l]

def plaintext_from_parsed_refs(parsed: List[Union[str,Pseudonym,Player]]) -> str:
    """
    Turns the output of `parsed_refs` into a string.
    :param parsed:
    :return:
    """
    return "".join(
            [x.text if isinstance(x, Pseudonym)
                else " AKA ".join([y.text for y in x.pseudonyms]) + f" ({x.reg.realname})" if isinstance(x,Player)
                else x
             for x in parsed
            ])

