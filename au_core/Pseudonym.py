"""
Pseudonym.py

Defines the `Pseudonym` class.
"""

from typing import Union
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKey, UniqueConstraint, ForeignKeyConstraint
from .Base import Base
from .enums import PseudonymColour
from .Player import Player

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
        """
        return f"<@{self.id}>"

    # TODO: add 'wanted' check when wanted list implemented
    def HTML_render(self) -> str:
        """
        Uses the `pseudonym.jinja` template to create the HTML rendering of this pseudonym.
        :return: The HTML code for the pseudonym
        """
        from .templates import env
        template = env.get_template("pseudonym.jinja")
        return template.render(pseudonym=self)