from dataclasses import dataclass
from typing import List, Dict

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
            created=pr_data['created_on'],
            reviewers=[r['user']['display_name'] for r in pr_data.get('reviewers', [])]
        )


class FileDiff:
    """Represents a single file's diff content and statistics"""
    def __init__(self, filename: str):
        self.filename = filename
        self.lines: List[str] = []
        self.stats = {"additions": 0, "deletions": 0}

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
