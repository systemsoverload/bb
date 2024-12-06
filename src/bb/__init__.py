"""BitBucket CLI tool"""
from .version import __version__
from .cli.main import cli

__all__ = ['cli', '__version__']

