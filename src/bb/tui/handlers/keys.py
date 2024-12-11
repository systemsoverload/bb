"""Key handling functions for the TUI application"""

from readchar import key
from typing import Dict, Callable

from ..state import AppState, ViewState
from . import HandlerFunc


def handle_list_next(state: AppState) -> bool:
    """Move to next PR in list view"""
    state.current_pr_index = min(len(state.prs) - 1, state.current_pr_index + 1)
    return True

def handle_list_prev(state: AppState) -> bool:
    """Move to previous PR in list view"""
    state.current_pr_index = max(0, state.current_pr_index - 1)
    return True

def handle_refresh(state: AppState) -> bool:
    """Refresh PRs"""
    state.status_message = "Refreshing PRs..."
    return True

def handle_switch_to_detail(state: AppState) -> bool:
    """Switch to detail view"""
    if state.current_pr:
        state.view_state = ViewState.DETAIL
    return True

def handle_switch_to_diff(state: AppState) -> bool:
    """Switch to diff view"""
    if state.current_pr:
        state.view_state = ViewState.DIFF
        state.status_message = "Loading diff..."
    return True

def handle_switch_to_list(state: AppState) -> bool:
    """Switch back to list view"""
    state.view_state = ViewState.LIST
    state.reset_scroll()
    return True

def handle_start_search(state: AppState) -> bool:
    """Enter search mode"""
    state.view_state = ViewState.SEARCH
    state.reset_search()
    return True

def handle_finish_search(state: AppState) -> bool:
    """Complete search and return to list"""
    state.view_state = ViewState.LIST
    return True

def handle_search_backspace(state: AppState) -> bool:
    """Handle backspace in search mode"""
    state.search_term = state.search_term[:-1]
    return True

def handle_next_file(state: AppState) -> bool:
    """Move to next file in diff view"""
    if state.file_diffs:
        state.current_file_index = (state.current_file_index + 1) % len(state.file_diffs)
        state.reset_scroll()
    return True

def handle_prev_file(state: AppState) -> bool:
    """Move to previous file in diff view"""
    if state.file_diffs:
        state.current_file_index = (state.current_file_index - 1) % len(state.file_diffs)
        state.reset_scroll()
    return True

def handle_scroll_down(state: AppState) -> bool:
    """Scroll down in diff view"""
    if state.current_file_diff:
        max_scroll = len(state.current_file_diff.lines) - state.viewport_height
        state.scroll_position = min(max_scroll, state.scroll_position + 1)
    return True

def handle_scroll_up(state: AppState) -> bool:
    """Scroll up in diff view"""
    state.scroll_position = max(0, state.scroll_position - 1)
    return True

def handle_page_down(state: AppState) -> bool:
    """Page down in diff view"""
    if state.current_file_diff:
        max_scroll = len(state.current_file_diff.lines) - state.viewport_height
        state.scroll_position = min(max_scroll,
                                  state.scroll_position + state.viewport_height)
    return True

def handle_page_up(state: AppState) -> bool:
    """Page up in diff view"""
    state.scroll_position = max(0, state.scroll_position - state.viewport_height)
    return True

def handle_scroll_top(state: AppState) -> bool:
    """Scroll to top of diff"""
    state.scroll_position = 0
    return True

def handle_scroll_bottom(state: AppState) -> bool:
    """Scroll to bottom of diff"""
    if state.current_file_diff:
        state.scroll_position = max(0, len(state.current_file_diff.lines) - state.viewport_height)
    return True

def handle_approve_pr(state: AppState) -> bool:
    """Approve current PR"""
    if state.current_pr:
        state.status_message = f"Approved PR #{state.current_pr.id}"
        state.view_state = ViewState.LIST
    return True

def handle_add_comment(state: AppState) -> bool:
    """Add comment to current PR"""
    if state.current_pr:
        state.status_message = f"Comment feature not yet implemented for PR #{state.current_pr.id}"
        state.view_state = ViewState.LIST
    return True

def handle_quit(state: AppState) -> bool:
    """Handle quit command based on current view"""
    if state.view_state in [ViewState.DETAIL, ViewState.DIFF]:
        state.view_state = ViewState.LIST
        state.reset_scroll()
        return True
    return False

# Key mapping definitions by view state
KEY_HANDLERS: Dict[ViewState, Dict[str, HandlerFunc]] = {
    ViewState.LIST: {
        key.DOWN: handle_list_next,
        'j': handle_list_next,
        key.UP: handle_list_prev,
        'k': handle_list_prev,
        'v': handle_switch_to_detail,
        'D': handle_switch_to_diff,
        'r': handle_refresh,
        '/': handle_start_search,
        'q': handle_quit,
    },
    ViewState.DETAIL: {
        'v': handle_switch_to_list,
        'D': handle_switch_to_diff,
        'a': handle_approve_pr,
        'c': handle_add_comment,
        'q': handle_quit,
    },
    ViewState.DIFF: {
        'v': handle_switch_to_detail,
        'q': handle_quit,
        key.DOWN: handle_scroll_down,
        'j': handle_scroll_down,
        key.UP: handle_scroll_up,
        'k': handle_scroll_up,
        key.RIGHT: handle_next_file,
        'l': handle_next_file,
        key.LEFT: handle_prev_file,
        'h': handle_prev_file,
        'f': handle_page_down,
        'b': handle_page_up,
        'g': handle_scroll_top,
        'G': handle_scroll_bottom,
    },
    ViewState.SEARCH: {
        key.ENTER: handle_finish_search,
        key.BACKSPACE: handle_search_backspace,
    }
}
