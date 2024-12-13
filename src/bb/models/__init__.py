from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional

from .base import BaseModel, BitbucketClient
from .filediff import FileDiff
from .pullrequest import PullRequest
from .repository import PullRequestCollection, Repository


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


__all__ = [
    "BaseModel",
    "Branch",
    "BitbucketClient",
    "FileDiff",
    "PullRequest",
    "PullRequestCollection",
    "Repository",
    "User",
]
