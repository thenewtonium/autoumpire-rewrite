"""
Death.py

Defines the Death class, for keeping track of deaths.
"""

from typing import Optional
from sqlalchemy import ForeignKey, DateTime, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .Base import Base, PluginHook
from .Player import Player
from .Game import Game
from .Event import Event
from datetime import datetime

# TODO: create a mixin for classes that have an event
# TODO: calculate `expires` somehow.
class Death(Base):
    __tablename__ = "deaths"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey(Event.id, ondelete="CASCADE"))
    killer_id: Mapped[int] = mapped_column(ForeignKey(Player.id))
    victim_id: Mapped[int] = mapped_column(ForeignKey(Player.id))
    expires: Mapped[Optional[datetime]] = mapped_column(DateTime)
    licit: Mapped[bool] # for the purpose of counting score

    event: Mapped[Event] = relationship(foreign_keys=[event_id])
    victim: Mapped["Player"] = relationship(foreign_keys=[victim_id])


def Player_dead_at(self, t: datetime) -> bool:
    """
    Queries deaths to determine whether a player was dead at a given time.
    This is important for correctly rendering Pseudonyms.
    :param t: The datetime that we are interested in.
    :return: Whether the Player was dead at time t
    """
    session = self.session
    res = session.scalars(Death.select(Death.expires, Death.event_id)
                          .filter_by(victim_id=self.id)
                          .where((Death.expires.is_(None)) | (Death.expires > t))
                          )
    for d in res:
        if d.event.datetimestamp <= t and (d.expires is None or d.expires > t):
            return True
    return False
Player.dead_at = Player_dead_at

licitnessHook = PluginHook()
# TODO: either move this into Death class or have as standalone function in the module (requires rewriting usages)
def Game_is_kill_licit(self, killer: Player, victim: Player):
    """
    Function to determine whether given kill is licit, self-defence notwithstanding.
    :param victim_id: Id of the Player who was killed
    :param killer_id: Id of the Player who made the kill
    :return: Whether the kill is licit.
    """
    return True if licitnessHook._execute_break_at_return(killer, victim) else False # converts None to False
Game.is_kill_licit = Game_is_kill_licit