"""
Player.py

Defines the Player class, which represents the instance of a player in a game,
and which the Assassin and Police classes inherit from as "types" of players.
"""

from typing import List
from .Base import Base
from .Registration import Registration
from sqlalchemy.orm import Mapped, mapped_column, relationship, load_only
from sqlalchemy import ForeignKeyConstraint, ForeignKey, select
from datetime import datetime
from .Death import Death

# TODO: uniqueness constraint on reg_id + type? I.e. only one instance of each TYPE of player per person
class Player(Base):
    """
    Player class

    Represents an instance of a generic player in a game.
    This is specialised into Assassins (Full Players) and Police using joined table inheritance.

    The reason for this class is to have an umbrella player type for Pseudonyms to point to as their owner.
    The reason they do not point simply to the initial Registration is,
    when someone dies as a Full Player and signs up as Police,
    the pseudonyms should be kept separate.
    """

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]

    reg_id: Mapped[int] = mapped_column(ForeignKey(Registration.id))
    reg: Mapped[Registration] = relationship(foreign_keys=[reg_id])

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    game: Mapped["Game"] = relationship(back_populates="players")

    pseudonyms: Mapped[List["Pseudonym"]] = relationship(back_populates="owner",foreign_keys="[Pseudonym.owner_id]")

    __mapper_args__ = {
        "polymorphic_identity": "player",
        "polymorphic_on": "type",
    }

    def dead_at(self, t: datetime) -> bool:
        """
        Queries deaths to determine whether a player was dead at a given time.
        This is important for correctly rendering Pseudonyms.
        :param t: The datetime that we are interested in.
        :return: Whether the Player was dead at time t
        """
        session = self.session
        res = session.scalars(select(Death).options(load_only(Death.expires, Death.event_id))
                              .filter_by(victim_id=self.id)
                              .where((Death.expires.is_(None)) | (Death.expires > t))
                              )
        for d in res:
            if d.event.datetimestamp <= t and (d.expires is None or d.expires > t):
                return True
        return False

    def HTML_render(self, css_class: str) -> str:
        """
        Uses the `player.jinja` template to create the HTML rendering of this player,
        to be used in headlines when they die,
        which reveals all their real name, and all their pseudonyms separated by AKA
        :return: The HTML code for the player to be used in headlines when they die.
        """
        from .templates import env
        template = env.get_template("player.jinja")
        return template.render(player=self, css_class=css_class)

    def plaintext_render(self) -> str:
        return " AKA ".join( (p.text for p in self.pseudonyms) ) + f" ({self.reg.realname})"
