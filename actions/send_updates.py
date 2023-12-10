# some nonsense to allow us to import from the above directory
import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from assassins_data import Assassin, Player, config
from jinja2 import Environment, FileSystemLoader, select_autoescape
from babel.dates import format_datetime
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)
template = env.get_template("update-email.jinja")

# function which sends emails to a player
# this may be updated to also send discord DMs
def send_email(to: Player, body: str, subject: str = "Assasins Update", type: str = "text"):
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = config["email"]["from"]
    message['To'] = to.email
    message.attach(MIMEText(body, type))
    msg = message.as_string()

    with SMTP(host=config["email"]["host"], port=config["email"]["port"]) as server:
        server.starttls()
        server.login(config["email"]["username"], config["email"]["password"])
        server.sendmail(config["email"]["from"], to.email, msg)

# function which sends an update to a specified assassin
def send_update(assassin: Assassin, body: str = "", subject: str = "Assasins Update"):
    body_with_info = template.render(player=assassin.player,
                    message=body,
                    targets=[t.player for t in assassin.targets],
                    competence_deadline=format_datetime(assassin.competence_deadline,
                                            locale=config["locale"],
                                            tzinfo=assassin.competence_deadline.tzinfo
                                            )
                    )
    send_email(assassin.player, body_with_info, subject=subject, type="text")