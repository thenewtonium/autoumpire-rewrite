"""
Pseudonym.py

Defines the `Pseudonym` class.
"""

from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy import ForeignKey, UniqueConstraint
import sqlalchemy
from . import db
from .Base import Base
from .Game import Game
from .Player import Player
from datetime import datetime


class Pseudonym(Base):
    """
    Pseudonym class

    This represents a pseudonym.
    A UNIQUE constraint is imposed on the composite (game_id, text) so that each pseudonym is unique per game.
    """

    __tablename__ = "pseudonyms"

    id: Mapped[int] = mapped_column(primary_key=True)  # reduce database size by referring using id

    # Note that game_id and text form a composite uniqueness constraint
    # (this is defined in __table_args__)
    #game_id: Mapped[int] = mapped_column(ForeignKey(Game.id))
    text: Mapped[str]

    owner_id: Mapped[int] = mapped_column(ForeignKey(Player.id, ondelete="CASCADE"))
    owner: Mapped[Player] = relationship(back_populates="pseudonyms",foreign_keys=[owner_id])

    UniqueConstraint("text", "owner.game_id")

    def reference(self) -> str:
        """
        :return: The text form of a reference to this pseudonym, to be used in Event headlines and Reports.
        Replace @ with # to reveal the player's identity.
        """
        return f"<@{self.id}>"

    def css_class(self, t: datetime) -> str:
        """
        Determines the CSS class that should be used it the HTML rendering of this pseudonym.
        If the player is DEAD at time `t`, their pseudonym is rendered with `colourdead1`.
        Otherwise the pseudonym will be rendered with the stored value
        :param t: The datetimestamp of the event for which this pseudonym is being rendered
        :return: The CSS class to use when rendering this Pseudonym in HTML
        """
        if self.owner.dead_at(t):
            return "colourdead1"
        else:
            return "colourlive" + (self.id % 7)

    # TODO: add 'wanted' check when wanted list implemented
    # TODO: move rendering to Event class
    def HTML_render(self, css_class: Optional[str] = None) -> str:
        """
        Uses the `pseudonym.jinja` template to create the HTML rendering of this pseudonym.
        :return: The HTML code for the pseudonym
        """
        if css_class is None:
            css_class = self.colour.value

        from .templates import env
        template = env.get_template("pseudonym.jinja")
        return template.render(pseudonym=self, css_class=css_class)

"""@sqlalchemy.event.listens_for(db.Session, "transient_to_pending")
def intercept_transient_to_pending(session, object):
    \"""This is yucky but I need to somehow sync game_id with owner.game_id\"""
    if isinstance(object, Pseudonym):
        object.game_id = object.owner.game_id"""


Player.pseudonyms: Mapped[List[Pseudonym]] = relationship(Pseudonym, back_populates="owner",
                                                            foreign_keys=[Pseudonym.owner_id],
                                                            cascade="all, delete-orphan")

def Player_plaintext_all_pseudonyms(self: Player) -> str:
    return " AKA ".join((p.text for p in self.pseudonyms))
Player.plaintext_all_pseudonyms = Player_plaintext_all_pseudonyms