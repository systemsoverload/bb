"""Base screen functionality for TUI screens"""

from textual.screen import Screen

from bb.tui.state import PRState
from bb.tui.types import AppType


class BaseScreen(Screen):
    """Base screen with common functionality"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app: AppType = None
        self._state: PRState = None

    @property
    def app(self) -> AppType:
        """Get the main application instance"""
        if not self._app:
            self._app = super().app
        return self._app

    @property
    def state(self) -> PRState:
        """Get the application state"""
        if not self._state:
            self._state = self.app.state
        return self._state
