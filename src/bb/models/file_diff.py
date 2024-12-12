from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


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
