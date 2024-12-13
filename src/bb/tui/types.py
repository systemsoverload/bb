from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from bb.models import FileDiff, PullRequest, Repository
    from bb.tui.app import PRReviewApp

    AppType = PRReviewApp
    FileDiffType = FileDiff
    PullRequestType = PullRequest
    RepositoryType = Repository

else:
    AppType = TypeVar("AppType")
    FileDiffType = TypeVar("FileDiff")
    PullRequestType = TypeVar("PullRequest")
    RepositoryType = TypeVar("Repository")
