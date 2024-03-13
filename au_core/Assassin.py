"""
Assassin.py

Defines the ORM model `Assassin` representing the instance of an assassin in a game.
An 'assassin' here means a full player -- i.e. a player with targets and a competence deadline.
"""

import random
import concurrent.futures
from typing import List, Optional
from .Player import Player
from .Base import Base
from .Game import Game
from sqlalchemy import ForeignKey, DateTime, select, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped
from sqlalchemy.types import Integer
from datetime import datetime, timezone



class Assassin(Player):
    """
    Assassin class

    Represents a Full Player.
    """

    __tablename__ = "assassins"
    id = mapped_column(ForeignKey(Player.id, ondelete="CASCADE"), primary_key=True)

    alive: Mapped[bool] = mapped_column(default=True)
    #competence_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "assassin", # sets Player.type for objects of this class to "assassin"
    }

    def send_update(self, body: str = ""):
        from .templates import env
        from babel.dates import format_datetime
        template = env.get_template("update-email.jinja")
        message = template.render(player=self.reg,
                                  message=body,
                                  targets=[t.reg for t in self.targets],
                                  competence_deadline=format_datetime(self.competence_deadline,
                                                                      locale=self.game.locale,
                                                                      tzinfo=self.competence_deadline.tzinfo
                                                                      )
                                  )
        self.reg.send_email(body=message)


#### INSERTIONS INTO `Game` CLASS ####

Game.assassins: WriteOnlyMapped[List[Assassin]] = relationship(Assassin, lazy="write_only", overlaps="players",
                                                               back_populates="game", passive_deletes=True)


def Game_send_updates(self, message: str = ""):
    """
    :param message: The message body to send along with the updates.
    """
    session = self.session

    # fetch alive assassins in the game
    assassins = session.scalars(self.assassins.select().filter_by(alive=True))

    # concurrently call the send_update method of each live assassin
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda a: a.send_update(message), assassins)
Game.send_updates = Game_send_updates
