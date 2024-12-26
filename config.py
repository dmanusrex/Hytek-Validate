"""Config parsing and options"""

import configparser
from platformdirs import user_config_dir
import uuid
import os
import pathlib


class appConfig:
    """Get/Set program options"""

    # Name of the configuration file
    _CONFIG_FILE = "hytekvalidate.ini"
    # Name of the section we use in the ini file
    _INI_HEADING = "HytekValidate"
    # Configuration defaults if not present in the config file
    _CONFIG_DEFAULTS = {
        _INI_HEADING: {
            "hytek_db": "testdata\2024 Western Region SC Champs-Test.mdb",  # Location of Database
            "ev3_file": "testdata\Meet Events-2024 Western Region SC Championships-23Feb2024-001.ev3",  # Location of EV3 File
            "meet_config_file": "testdata\Western Region SC Championships-2024.json",  # Location of Config File
            "report_file": "testdata\en_Reports.txt",  # Location of Report File
            "opt_ignore_existing_bonus": "False",  # Ignore Existing Bonus
            "opt_ignore_cache": "False",  # Ignore Cache
            "Theme": "System",  # Theme- System, Dark or Light
            "Scaling": "100%",  # Display Zoom Level
            "Colour": "blue",  # Colour Theme
            "client_id": "",  # Unique ID for the client
        }
    }

    def __init__(self):
        self._config = configparser.ConfigParser(interpolation=None)
        self._config.read_dict(self._CONFIG_DEFAULTS)
        userconfdir = user_config_dir("HytekValidate", "Swimm Ontario")
        pathlib.Path(userconfdir).mkdir(parents=True, exist_ok=True)
        self._CONFIG_FILE = os.path.join(userconfdir, self._CONFIG_FILE)
        self._config.read(self._CONFIG_FILE)
        client_id = self.get_str("client_id")

        if client_id is None or len(client_id) == 0:
            client_id = str(uuid.uuid4())
        try:
            uuid.UUID(client_id)
        except ValueError:
            client_id = str(uuid.uuid4())
        self.set_str("client_id", client_id)

    def save(self) -> None:
        """Save the (updated) configuration to the ini file"""
        with open(self._CONFIG_FILE, "w") as configfile:
            self._config.write(configfile)

    def get_str(self, name: str) -> str:
        """Get a string option"""
        return self._config.get(self._INI_HEADING, name)

    def set_str(self, name: str, value: str) -> str:
        """Set a string option"""
        self._config.set(self._INI_HEADING, name, value)
        return self.get_str(name)

    def get_float(self, name: str) -> float:
        """Get a float option"""
        return self._config.getfloat(self._INI_HEADING, name)

    def set_float(self, name: str, value: float) -> float:
        """Set a float option"""
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_float(name)

    def get_int(self, name: str) -> int:
        """Get an integer option"""
        return self._config.getint(self._INI_HEADING, name)

    def set_int(self, name: str, value: int) -> int:
        """Set an integer option"""
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_int(name)

    def get_bool(self, name: str) -> bool:
        """Get a boolean option"""
        return self._config.getboolean(self._INI_HEADING, name)

    def set_bool(self, name: str, value: bool) -> bool:
        """Set a boolean option"""
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_bool(name)
