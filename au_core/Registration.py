"""
Registration.py

Defines the ORM model `Registration` representing initial player registrations.
"""

from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred, Session
from sqlalchemy import ForeignKey, select, UniqueConstraint
from .Base import Base
from .enums import RegType, College, WaterStatus
from .config import config
from email_validator import validate_email, EmailNotValidError
from warnings import warn

# imports for sending emails
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    __table_args__ = (UniqueConstraint("game_id", "initial_pseudonym"),)

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
    initial_pseudonym: Mapped[str] # unique per game (see __table_args__)
    type: Mapped[RegType]

    # related objects
    game: Mapped["Game"] = relationship(back_populates="registrations")

    # TODO: separate default subject into a config option & game setting
    # TODO: (much much later...) discord integration
    def send_email(self, body: str, subject: str = "Assassins' Guild Update", mimetype: str = "text"):
        """
        Sends an email to this registration.
        :param body: Body of the email to send
        :param subject: Subject of the email to send (defaults to `Assassins Update`)
        :param mimetype: MIME type of the body (defaults to `text`)
        :return:
        """
        # prepare the email
        message = MIMEMultipart()
        message['Subject'] = subject
        message['From'] = config["email"]["from"]
        message['To'] = self.email
        message.attach(MIMEText(body, mimetype))
        msg = message.as_string()

        # send the email with SMTP
        with SMTP(host=config["email"]["host"], port=config["email"]["port"]) as server:
            server.starttls()
            server.login(config["email"]["username"], config["email"]["password"])
            server.sendmail(config["email"]["from"], self.email, msg)

    def validate(self, enforce_unique_email: bool = True):
        """
        Function wrapping validate_w_session -- creates a fresh session and passes this to validate_w_session.
        :param enforce_unique_email:
        :return:
        """
        self.validate_w_session(self.game.session, enforce_unique_email)

    # TODO: get Session from self.Game rather than passing into this method
    def validate_w_session(self, session: Session, enforce_unique_email: bool = True):
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