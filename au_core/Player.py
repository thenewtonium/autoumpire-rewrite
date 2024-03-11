"""
Player.py

Defines the Player class, which represents the instance of a player in a game,
and which the Assassin and Police classes inherit from as "types" of players.
"""

from typing import List, Tuple
from .Game import GameObject, Game
from .Base import Base
from sqlalchemy.orm import Mapped, relationship, WriteOnlyMapped, deferred, mapped_column
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import JSON

class Player(Base, GameObject):
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
    type: Mapped[str] # for polymorphism

    realname: Mapped[str] # required for event rendering
    email: Mapped[str] # TODO: abstract into a 'contact' so that can extend to also msg over discord

    # info given to assassins -- stored as native JSON so that this info can easily be changed across games
    # without breaking an existing database or proliferating new tables
    # 'standard' setup is
    # college
    # address
    # water weapons status
    # notes
    #
    # but e.g. in COVID it may have been useful to add a 'self-isolating' parameter apart from notes
    # to give it additional salience.
    info: Mapped[dict] = deferred(mapped_column(MutableDict.as_mutable(JSON)))
    # note: this requires that the backend supports native JSON types

    __mapper_args__ = {
        "polymorphic_identity": "player",
        "polymorphic_on": "type",
    }

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


Game.players: WriteOnlyMapped[List[Player]] = relationship(Player,  lazy="write_only",
                                                           back_populates="game", passive_deletes=True)