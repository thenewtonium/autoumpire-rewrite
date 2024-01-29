"""
Pseudonym.py

Defines the `Pseudonym` class.
"""

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKey, UniqueConstraint, ForeignKeyConstraint
from .Base import Base
from .enums import PseudonymColour
from .Player import Player
from datetime import datetime

class Pseudonym(Base):
    """
    Pseudonym class

    This represents a pseudonym.
    A UNIQUE constraint is imposed on the composite (game_id, text) so that each pseudonyn us unique per game.
    """

    __tablename__ = "pseudonyms"
    __table_args__ = (UniqueConstraint("game_id","text"),
                      ForeignKeyConstraint(["game_id","owner_id"],[Player.game_id, Player.id]))

    id: Mapped[int] = mapped_column(primary_key=True)  # reduce database size by referring using id

    # Note that game_id and text form a composite uniqueness constraint
    # (this is defined in __table_args__)
    game_id: Mapped[int]# = mapped_column(ForeignKey(Player.game_id))
    text: Mapped[str]

    # TODO: change to name to 'css_class' and type to to str
    colour: Mapped[PseudonymColour] = mapped_column(default=PseudonymColour.DEFAULT)

    owner_id: Mapped[int] = mapped_column(ForeignKey(Player.id))
    owner: Mapped[Player] = relationship(back_populates="pseudonyms",foreign_keys="[Pseudonym.owner_id,Pseudonym.game_id]")

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
        Otherwise the pseudonym will be rendered with the stored value.
        TODO: generate 'standard' colours with this function, using the id value, say
        TODO: colouring when wanted
        :param t: The datetimestamp of the event for which this pseudonym is being rendered
        :return: The CSS class to use when rendering this Pseudonym in HTML
        """
        if self.owner.dead_at(t):
            return "colourdead1"
        else:
            return self.colour.value

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