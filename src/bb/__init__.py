"""Bitbucket CLI tool"""

from .cli.main import cli
from .version import __version__

__all__ = ["cli", "__version__"]
