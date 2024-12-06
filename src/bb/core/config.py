import os
from pathlib import Path
from typing import TypeVar

import tomli
import tomli_w

from bb.utils import rget

CONF_DIR = Path(os.path.expanduser("~/.config/bb/"))
CONF_PATH = Path(os.path.expanduser("~/.config/bb/config.toml"))


class BBConfig:
    def __init__(self, create=True):
        if not CONF_DIR.is_dir() and create:
            CONF_DIR.mkdir()
            with open(CONF_PATH, "w+"):
                pass

        with open(CONF_PATH, "rb+") as f:
            self._conf = tomli.load(f)

    def update(self, path, value):
        """
        >> BBConfig().update("auth.app_password", "1234")
        >> BBConfig().update("arbitrary", "abc123")
        """
        # XXX - This is fairly brittle and cant handle nested dictionaries
        key, *subkey = path.split(".")
        setting = self._conf.get(key)
        if subkey:
            if setting:
                setting.update({subkey[0]: value})
            else:
                self._conf[key] = {subkey[0]: value}

        else:
            self._conf[key] = value

    def delete(self, path):
        # XXX - This is fairly brittle and cant handle nested dictionaries
        key, *subkey = path.split(".")
        if rget(self._conf, path):
            if subkey:
                del self._conf[key][subkey[0]]
            else:
                del self._conf[key]

    T = TypeVar("T")

    def get(self, path, default: T = "") -> T:
        res = rget(self._conf, path, default=default)

        return res if res else default

    def write(self):
        with open(CONF_PATH, "rb+") as f:
            conf = tomli.load(f)
            conf.update(self._conf)
            f.seek(0)
            f.truncate()
            tomli_w.dump(conf, f)
