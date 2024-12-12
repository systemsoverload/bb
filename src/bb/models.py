"""Models for BitBucket data structures and UI state"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum, auto

class ViewState(Enum):
    """Available view states in the TUI"""
    LIST = auto()
    DETAIL = auto()
    DIFF = auto()
    SEARCH = auto()

@dataclass
class User:
    """BitBucket user information"""
    display_name: str
    uuid: str
    account_id: Optional[str] = None
    links: Optional[Dict] = None

@dataclass
class Branch:
    """Repository branch information"""
    name: str
    target: Dict

@dataclass
class PullRequest:
    """Represents a pull request with its key attributes"""
    id: int
    title: str
    author: str
    description: str
    status: str
    approvals: List[str]
    comments: int
    branch: str
    created: str
    reviewers: List[str]
    source_commit: Optional[str] = None
    destination_commit: Optional[str] = None
    links: Dict = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, pr_data: Dict) -> 'PullRequest':
        """Create a PullRequest instance from API response data"""
        return cls(
            id=pr_data['id'],
            title=pr_data['title'],
            author=pr_data['author']['display_name'],
            description=pr_data.get('description', ''),
            status='Approved' if any(p['approved'] for p in pr_data.get('participants', [])) else 'Open',
            approvals=[p['user']['display_name'] for p in pr_data.get('participants', []) if p['approved']],
            comments=len(pr_data.get('comments', [])),
            branch=pr_data['source']['branch']['name'],
            created=format_date(pr_data['created_on']),
            reviewers=[r['user']['display_name'] for r in pr_data.get('reviewers', [])],
            source_commit=pr_data.get('source', {}).get('commit', {}).get('hash'),
            destination_commit=pr_data.get('destination', {}).get('commit', {}).get('hash'),
            links=pr_data.get('links', {})
        )

    @property
    def web_url(self) -> Optional[str]:
        """Get web URL for the pull request"""
        return self.links.get('html', {}).get('href')

    @property
    def api_url(self) -> Optional[str]:
        """Get API URL for the pull request"""
        return self.links.get('self', {}).get('href')

@dataclass
class FileDiff:
    """Represents a single file's diff content and statistics"""
    filename: str
    lines: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {"additions": 0, "deletions": 0})
    content_type: Optional[str] = None
    status: Optional[str] = None

    def add_line(self, line: str):
        """Add a line to the diff and update statistics"""
        self.lines.append(line)
        if line.startswith('+') and not line.startswith('+++'):
            self.stats["additions"] += 1
        elif line.startswith('-') and not line.startswith('---'):
            self.stats["deletions"] += 1

    @property
    def content(self) -> str:
        """Get the complete diff content"""
        return '\n'.join(self.lines)

    @property
    def stats_text(self) -> str:
        """Get a formatted string of the diff statistics"""
        return f"+{self.stats['additions']} -{self.stats['deletions']}"

def format_date(date_str: str) -> str:
    """Format date string from API response"""
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date.strftime('%Y-%m-%d %H:%M:%S UTC')
    except (ValueError, AttributeError):
        return date_str
