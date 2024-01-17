"""
Assassin.py

Defines the ORM model `Assassin` representing the instance of an assassin in a game.
An 'assassin' here means a full player -- i.e. a player with targets and a competence deadline.
"""

from typing import List, Optional
from .Player import Player
from .TargRel import TargRel
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

# setup for message generation from template
from jinja2 import Environment, PackageLoader, select_autoescape
from babel.dates import format_datetime
env = Environment(
    loader=PackageLoader('au_core', 'templates'),
    autoescape=select_autoescape()
)
template = env.get_template("update-email.jinja")

class Assassin(Player):
    """
    Assassin class

    Extends the Player class by including vitality, competence, and targetting relationships.
    """

    __tablename__ = "assassins"
    id = mapped_column(ForeignKey(Player.id), primary_key=True)

    alive: Mapped[bool] = mapped_column(default=True)
    competence_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # lists of targets and assassins generated by persisting a relationship using a secondary join with targetting_table
    targets: Mapped[List["Assassin"]] = relationship(overlaps="assassins,target,assassin",
                                                     secondary=TargRel.__tablename__,
                                                     primaryjoin="Assassin.id==TargRel.assassin_id",
                                                     secondaryjoin="Assassin.id==TargRel.target_id")
    assassins: Mapped[List["Assassin"]] = relationship(overlaps="targets,assassin,target",
                                                       secondary=TargRel.__tablename__,
                                                       primaryjoin="Assassin.id==TargRel.target_id",
                                                       secondaryjoin="Assassin.id==TargRel.assassin_id")

    __mapper_args__ = {
        "polymorphic_identity": "assassin", # sets Player.type for objects of this class to "assassin"
    }

    def send_update(self, body: str = ""):
        message = template.render(player=self.reg,
                                  message=body,
                                  targets=[t.reg for t in self.targets],
                                  competence_deadline=format_datetime(self.competence_deadline,
                                                                      locale=self.game.locale,
                                                                      tzinfo=self.competence_deadline.tzinfo
                                                                      )
                                  )
        self.reg.send_email(body=message)