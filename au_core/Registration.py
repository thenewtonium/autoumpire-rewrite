"""
Registration.py

Defines the ORM model `Registration` representing initial player registrations.
"""

from typing import Union
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKey, select
from .Base import Base
from .enums import RegType, College, WaterStatus
from email_validator import validate_email, EmailNotValidError
from warnings import warn

class DuplicateWarning(Warning):
    """
    Warning to be issued when duplicate registration values are present that are allowed but may be confusing
    """

class DuplicateError(Exception):
    """
    Exception to be raised when disallowed duplicate registration values are present.
    """

class Registration(Base):
    """
    Registration class

    Represents initial signup data.
    This data can be shared between an instance of a player as an Assassin and as Police.

    Signup data is
        Info shared with assassins:
        realname    -   The player's real name
        college     -   The player's college*
        address     -   The player's address
        water       -   The player's Water Weapons Status
        notes       -   Any additional info the player wishes to share

        Info needed for AutoUmpire:
        type                -   The type of signup, as an enums.RegType
        email               -   The player's email address
        initial_pseudonym   -   The pseudonym the player should start the game with
        (may want to add `seed` for more intelligent targetting, and `discord_id` for discord integration)
    """
    __tablename__ = "registrations"
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id = deferred(mapped_column(ForeignKey("games.id")))

    # info shared with assassins
    realname: Mapped[str]
    college: Mapped[College] # TODO: Consider whether to make this str
    address: Mapped[str]
    water: Mapped[WaterStatus] # TODO: Consider whether to make this str
    notes: Mapped[str]

    # other signup data
    email: Mapped[str]
    initial_pseudonym: Mapped[str]
    type: Mapped[RegType]

    # related objects
    game: Mapped["Game"] = relationship(back_populates="registrations")

    def __repr__(self) -> str:
        return (f"Registration(id={self.id},game_id={self.game_id},type={self.type},realname={self.realname},college={self.college},"
                f"address={self.address},notes={self.notes},email={self.email},initial_pseudonym={self.initial_pseudonym})")

    # TODO: get Session from self.Game rather than passing into this method
    def validate_w_session(self, session: Session, enforce_unique_email=True):
        """
        Function to validate the registration
        Ensures `realname` is nonempty and normalises to title case.
        Ensures `email` if valid and normalises
        :param session: The sqlalchemy.orm.session to be used to check for duplicates
        :param enforce_unique_email: Whether to require the email to be unique. Defaults to `True`. Setting to `False` is useful for testing purposes.
        """
        # ensure realname nonempty
        if self.realname in (None, ""):
            raise ValueError("Empty realname")
        # normalise to title case
        self.realname = self.realname.title()
        # check for duplication, and warn if duplicated
        # TODO: rewrite using Game.registrations ?
        res = session.scalars(select(Registration).filter_by(game_id=self.game_id, realname=self.realname)).fetchall()
        if len(res) > 0:
            warn(DuplicateWarning(f"{self.realname} is also the name of existing assassin(s) {', '.join(str(a) for a in res)}"))

        # ensure address nonempty
        if self.address in (None, ""):
            raise ValueError("Empty address")

        # convert unspecified notes to ""
        if self.notes is None:
            self.notes = ""

        # validate enum types
        # TODO: maybe don't apart from RegType? college and water are basically address / notes resp!
        self.college = College(self.college)
        self.water = WaterStatus(self.water)
        self.type = RegType(self.type)

        # ensure email valid
        emailinfo = validate_email(self.email, check_deliverability=False)
        # normalise email
        self.email = emailinfo.normalized
        # check for duplication
        # TODO: rewrite using Game.registrations ?
        res = session.scalars(select(Registration).filter_by(game_id=self.game_id, email=self.email)).fetchall()
        if len(res) > 0:
            if enforce_unique_email:
                raise DuplicateError(f"{self.email} is already registered to {res[0]}")
            else:
                warn(DuplicateWarning(f"{self.email} is also the email of existing assassin(s) {', '.join(str(a) for a in res)}"))

        # ensure initial_pseudonym nonempty
        if self.initial_pseudonym in (None, ""):
            raise ValueError("Empty initial_pseudonym")
        # check for duplication and throw error if duplicate
        # TODO: rewrite using Game.registrations ?
        res = session.scalars(select(Registration).filter_by(game_id=self.game_id, initial_pseudonym=self.initial_pseudonym)).one_or_none()
        if res is not None:
            raise DuplicateError(f"{self.initial_pseudonym} is already the initial pseudonym of {res}")