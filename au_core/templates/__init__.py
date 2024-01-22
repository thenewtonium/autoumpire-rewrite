"""
templates.__init__.py

Configures the Jinja2 environment.
"""

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader('au_core', 'templates'),
    autoescape=select_autoescape()
)
