import os

from textual.features import parse_features

from bb.tui.app import PRReviewApp


def review_prs(repo_slug: str) -> None:
    app = PRReviewApp(repo_slug,)
    features = set(parse_features(os.environ.get("TEXTUAL", "")))
    features.add("debug")
    features.add("devtools")
    app.run()


if __name__ == "__main__":
    review_prs("bitbucket/core")
