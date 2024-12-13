from unittest.mock import MagicMock, patch

import pytest
from textual.pilot import Pilot
from textual.widgets import DataTable

from bb.tui.app import PRReviewApp
from bb.tui.screens.pr_list import PRListScreen
from bb.tui.state import PRState


@pytest.fixture
def app():
    """Fixture to create a test app instance"""
    app = PRReviewApp("test/repo")
    return app


@pytest.fixture
async def pilot(app):
    """Fixture to create a Pilot for testing"""
    async with app.run_test() as pilot:
        yield pilot


class TestPRListScreen:
    async def test_screen_mount(self, pilot: Pilot):
        """Test that the PR list screen mounts correctly"""
        # Push the PR list screen
        await pilot.push_screen(PRListScreen())

        # Verify screen components
        assert pilot.app.screen_stack[-1].name == "pr_list"
        assert isinstance(await pilot.query_one("#pr_table"), DataTable)

        # Verify table structure
        table = await pilot.query_one("#pr_table")
        assert len(table.columns) == 5  # ID, Title, Author, Status, Approvals
        assert table.cursor_type == "row"

    @patch("bb.tui.screens.pr_list.get_prs")
    async def test_pr_loading(self, mock_get_prs, pilot: Pilot):
        """Test PR data loading and display"""
        # Mock PR data
        mock_prs = [
            {
                "id": 1,
                "title": "Test PR",
                "author": {"display_name": "Test Author"},
                "status": "OPEN",
                "participants": [
                    {"approved": True, "user": {"display_name": "Approver"}}
                ],
            }
        ]
        mock_get_prs.return_value.unwrap.return_value = mock_prs

        # Push screen and wait for data load
        screen = PRListScreen()
        await pilot.push_screen(screen)
        await pilot.pause()  # Wait for async operations

        # Verify table contents
        table = await pilot.query_one("#pr_table")
        assert table.row_count == 1
        assert table.get_cell_at(0, 0) == "1"  # ID
        assert table.get_cell_at(0, 1) == "Test PR"  # Title

    async def test_keyboard_navigation(self, pilot: Pilot):
        """Test keyboard navigation in PR list"""
        screen = PRListScreen()
        await pilot.push_screen(screen)

        # Simulate keyboard input
        table = await pilot.query_one("#pr_table")
        initial_row = table.cursor_row

        await pilot.press("j")  # Move down
        assert table.cursor_row == min(initial_row + 1, table.row_count - 1)

        await pilot.press("k")  # Move up
        assert table.cursor_row == initial_row

    async def test_view_details_action(self, pilot: Pilot):
        """Test viewing PR details"""
        screen = PRListScreen()
        await pilot.push_screen(screen)

        # Mock some PR data in state
        screen.state.prs = [MagicMock(id=1, title="Test PR")]

        # Simulate viewing details
        await pilot.press("v")

        # Verify screen transition
        assert pilot.app.screen_stack[-1].name == "pr_detail"


class TestPRDetailScreen:
    @patch("bb.tui.screens.pr_detail.PRDetailScreen.load_pr_details")
    async def test_detail_screen_mount(self, mock_load_details, pilot: Pilot):
        """Test PR detail screen mounting"""
        # Set up test PR in state
        pr = MagicMock(
            id=1,
            title="Test PR",
            author="Test Author",
            description="Test Description",
            branch="feature/test",
            status="OPEN",
            created="2024-01-01",
            reviewers=["Reviewer1"],
            approvals=["Approver1"],
        )
        pilot.app.state.current_pr = pr

        # Push detail screen
        from bb.tui.screens.pr_detail import PRDetailScreen

        screen = PRDetailScreen()
        await pilot.push_screen(screen)

        # Verify screen components
        assert await pilot.query_one("#pr_title")
        assert await pilot.query_one("#pr_meta")
        assert await pilot.query_one("#pr_description")

    async def test_diff_loading(self, pilot: Pilot):
        """Test diff content loading"""
        # Similar structure to above, but testing diff loading
        pass


def test_app_state():
    """Test PRState management"""
    state = PRState("test", "repo")

    # Test PR selection
    pr = MagicMock(id=1)
    state.set_current_pr(pr)
    assert state.current_pr == pr
    assert state.file_diffs == []
    assert state.current_file_index == 0

    # Test diff management
    diffs = [MagicMock(), MagicMock()]
    state.set_file_diffs(diffs)
    assert state.file_diffs == diffs
    assert state.current_file_index == 0
