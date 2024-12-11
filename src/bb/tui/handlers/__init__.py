"""Input handling package for the TUI application"""

from typing import Protocol, Callable
from ..state import AppState

class InputHandler(Protocol):
    """Protocol defining input handler interface"""
    def __call__(self, state: AppState) -> bool:
        """Handle input and return whether to continue running"""
        ...

HandlerFunc = Callable[[AppState], bool]
