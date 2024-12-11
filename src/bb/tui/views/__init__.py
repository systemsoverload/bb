from rich.layout import Layout
from rich.console import Console

from ..state import AppState


class BaseView:
    """Base class for all views"""
    def __init__(self, state: AppState, console: Console):
        self.state = state
        self.console = console

    def generate(self) -> Layout:
        """Generate the view layout - must be implemented by subclasses"""
        raise NotImplementedError
