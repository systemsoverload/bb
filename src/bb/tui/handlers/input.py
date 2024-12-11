"""Main input handling logic for the TUI application"""

from typing import Optional

from ..state import AppState, ViewState
from .keys import KEY_HANDLERS


class InputHandler:
    """Handles keyboard input and manages state transitions"""

    def __init__(self, state: AppState):
        self.state = state
        self.last_key: Optional[str] = None

    def handle_search_input(self, ch: str) -> bool:
        """Handle input in search mode"""
        if len(ch) == 1 and ch.isprintable():
            self.state.search_term += ch
        return True

    def handle_input(self, ch: str) -> bool:
        """
        Handle keyboard input based on current view state
        Returns whether to continue running the application
        """
        # Update last key for multi-key combinations (like 'gg')
        if ch != 'g':
            self.last_key = ch

        # Special handling for 'gg' combination
        if ch == 'g' and self.last_key == 'g':
            if self.state.view_state == ViewState.DIFF:
                return self.handle_key_press('g')
            self.last_key = None
            return True

        # Get handlers for current view state
        handlers = KEY_HANDLERS.get(self.state.view_state, {})

        # Special handling for search state
        if self.state.view_state == ViewState.SEARCH:
            if ch in handlers:
                return handlers[ch](self.state)
            return self.handle_search_input(ch)

        # Handle the key if there's a mapping for it
        if ch in handlers:
            return handlers[ch](self.state)

        # Default to continuing if no handler found
        return True

    def handle_key_press(self, key: str) -> bool:
        """Handle a single key press"""
        handlers = KEY_HANDLERS.get(self.state.view_state, {})
        handler = handlers.get(key)
        if handler:
            return handler(self.state)
        return True
