"""
Death.py

Defines the Death class, for keeping track of deaths.
"""

from typing import Optional
from sqlalchemy import ForeignKey, DateTime, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .Base import Base
from datetime import datetime

class Death(Base):
    __tablename__ = "deaths"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    killer_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    victim_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    expires: Mapped[Optional[datetime]] = mapped_column(DateTime)
    licit: Mapped[bool] # for the purpose of counting score

    event: Mapped["Event"] = relationship(foreign_keys=[event_id])
    victim: Mapped["Player"] = relationship(foreign_keys=[victim_id])

# TODO: calculate `expires` somehow.
