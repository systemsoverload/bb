from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from bb.tui.app import PRReviewApp
    AppType = PRReviewApp
else:
    AppType = TypeVar('AppType')
