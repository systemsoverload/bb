from dataclasses import dataclass, field
from typing import Dict, List, Optional

from bb.models.base import BaseModel


@dataclass
class FileDiff(BaseModel):
    """Represents a single file's diff content and statistics"""

    filename: str
    lines: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(
        default_factory=lambda: {"additions": 0, "deletions": 0}
    )
    content_type: Optional[str] = None
    status: Optional[str] = None

    @classmethod
    def resource_path(cls) -> str:
        return "diff"  # Not actually used since diffs are accessed via PR

    def add_line(self, line: str) -> None:
        self.lines.append(line)
        if line.startswith("+") and not line.startswith("+++"):
            self.stats["additions"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            self.stats["deletions"] += 1

    @property
    def content(self) -> str:
        return "\n".join(self.lines)

    @property
    def stats_text(self) -> str:
        return f"+{self.stats['additions']} -{self.stats['deletions']}"

    @property
    def web_url(self) -> str:
        # TODO -  FileDiff doesn't have a direct web URL without context
        # Could be enhanced if we store PR reference
        return ""
