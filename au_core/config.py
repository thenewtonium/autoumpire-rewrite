"""
config.py

Defines default config values, then loads the `config.json` file.
Config values are imported from this module under `config`.
"""

import json
from pathlib import Path, PurePath

config_path = ( Path(__file__).parent / PurePath("config.json") ).resolve()

# default config values
config = {
    "verbose": False,
    "n_targs": 3,
    "initial_competence": 7,
    "locale": "en_GB"
}

class MissingConfigError(FileNotFoundError):
    """Raise this when config.json is missing"""

try:
    # load database config file
    with config_path.open() as f:
        _loaded_config = json.load(f)
except FileNotFoundError as e:
    raise MissingConfigError(f"Couldn't find config file at {config_path}")

for k in _loaded_config:
    config[k] = _loaded_config[k]

del _loaded_config # free up memory
