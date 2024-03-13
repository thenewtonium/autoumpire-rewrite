"""
competency.py

Implements competency
"""

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, ScalarSelect, Exists
from .Game import TempStateChange, Game
from .Player import Player
from .Assassin import Assassin
from .Death import licitnessHook, Death
from .Event import Event
from datetime import datetime

class CompetencyExtension(TempStateChange):
    """Represents an extension of competency granted to an assassin"""
    __tablename__ = "competency_extensions"

    id: Mapped[int] = mapped_column(primary_key=True) # needs a primary key...

    # the assassin to whom competency was granted
    assassin_id: Mapped[int] = mapped_column(ForeignKey(Assassin.id))

def competent_subquery(assassin_id, at: Optional[datetime] = None) -> ScalarSelect:
    """Produces a subquery for whether an assassin is competent"""
    if at is None:
        at = datetime.utcnow()
    return ((CompetencyExtension.select()
                          .where(CompetencyExtension.assassin_id == assassin_id)
                          .where((CompetencyExtension.when <= at) & (CompetencyExtension.expires > at))
                          ).exists())


def Assassin_is_inco(self: Assassin, at: Optional[datetime] = None) -> bool:
    return not self.session.scalar(competent_subquery(self.id, at).select())
Assassin.is_inco = Assassin_is_inco


### set kills of an inco player as licit
@licitnessHook.register()
def _inco_licitness(killer: Player, victim: Player) -> Optional[bool]:
    if (isinstance(victim, Assassin)):
        return True if victim.is_inco() else None

def is_inco_corpse_subquery(assassin_id) -> Exists:
    return (Death.select().where(Death.victim_id == assassin_id,
                              Death.event.has(
                                  ~CompetencyExtension.exists_including(Event.datetimestamp,
                                                                       CompetencyExtension.assassin_id == assassin_id)
                              ))).exists()

def Game_generate_inco_list(self: Game) -> str:
    session = self.session
    # fetch incos
    incos_stmt = (self.assassins.select().where(competent_subquery(Assassin.id) == False))
    live_incos_stmt = incos_stmt.where(~Death.player_dead_subquery(Assassin))
    incos_corpses_stmt = self.assassins.select().where(is_inco_corpse_subquery(Assassin.id))
    live_incos = session.scalars(live_incos_stmt)
    inco_corpses = session.scalars(incos_corpses_stmt)

    from .templates import env
    template = env.get_template("inco_list.jinja")

    return template.render(live_incos=live_incos, inco_corpses=inco_corpses)
Game.generate_inco_list = Game_generate_inco_list