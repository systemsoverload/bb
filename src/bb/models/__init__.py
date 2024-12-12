"""Models for Bitbucket data structures and UI state"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional

from .file_diff import FileDiff
from .pullrequest import PullRequest  # noqa


class ViewState(Enum):
    """Available view states in the TUI"""
    LIST = auto()
    DETAIL = auto()
    DIFF = auto()
    SEARCH = auto()

@dataclass
class User:
    """Bitbucket user information"""
    display_name: str
    uuid: str
    account_id: Optional[str] = None
    links: Optional[Dict] = None

@dataclass
class Branch:
    """Repository branch information"""
    name: str
    target: Dict

__all__ = ["FileDiff", "PullRequest", "Branch", "User", "ViewState"]
