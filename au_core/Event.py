"""
Event.py

Defines the `Event` class.
"""

import re
from typing import List, Union, TYPE_CHECKING
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .Base import Base
from .Pseudonym import Pseudonym
from datetime import datetime

if TYPE_CHECKING:
    from .Game import Game
    from sqlalchemy.orm import Session

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

    game: Mapped[Game] = relationship(back_populates="events")
    reports: Mapped[List["Report"]] = relationship(back_populates="event", order_by="Report.datetimestamp")

    def parsed_headline(self) -> List[Union[str, Pseudonym]]:
        """
        :return: Parsed form of this Event's headline -- i.e. a list of strings and Pseudonym objects representing this
        Event's headline with references to pseudonyms substituted for Pseudonym objects
        """
        return parse_pseudonym_refs(self.headline, self.session)

# TODO: allow escaping?
# regex pattern for identifying pseudonym references in texts
pseudonym_ref_capture_pattern = re.compile(r"(<@\d+>)")
# regex pattern for extracting the id of the pseudonym from a pseudonym reference
pseudonym_id_capture_pattern = re.compile(r"<@(\d+)>")

def _convert_pseudonym_ref(ref: str, session: Session) -> Union[str, Pseudonym]:
    """
    Helper function for parse_pseudonym_refs.
    This converts a pseudonym reference into a Pseudonym object if the reference is valid,
    otherwise it returns the original string.
    :param ref: String reference to a pseudonym
    :param game: The sqlalchemy Session to
    :return: Pseudonym object corresponding to the referenced pseudonym, if valid, else the original string.
    """
    m = re.match(pseudonym_id_capture_pattern, str)

    # return original string if not a valid pseudonym reference
    if m is None:
        return ref

    # extract id capture group from match
    id = int(m.group(1))

    # fetch the Pseudonym object by id
    return session.get(Pseudonym, id)

# TODO: change to use Game object
def parse_pseudonym_refs(text: str, session: Session) -> List[Union[str,Pseudonym]]:
    """
    Parses a text with references to pseudonyms in the form <@xxxxx> into a list of strings and Pseudonym objects,
    where the Pseudonym objects "take the place" of the <@xxxxx>'s in the original text.
    :param text: Text with pseudonym references
    :param session: The sqlalchemy Session to use to parse the pseudonyms
    :return: List representing the text, with references of the form <@xxxxx> where xxxxx is an integer
    (of any number of digits) replaced by Pseudonym objects corresponding to the pseudonym with id xxxxx.
    """
    # split text by pseudonym references, keeping the 'separators'
    l = re.split(pseudonym_ref_capture_pattern, text)

    return [_convert_pseudonym_ref(s, session) for i, s in enumerate(l) if l % 2 == 1]

