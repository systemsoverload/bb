if __name__ == "__main__":
    # Incredibly hacky path masher for local dev. I cant figure out how to get the textual console
    # working when the app is wrapped in click. The following will ensure your local env and entire
    # project is included in your local path for running `textual run --dev ~/dev/bb/src/bb/tui/__init__.py`
    # directly
    import os
    import sys
    from pathlib import Path

    # Add project root to path
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    sys.path.insert(0, root)

    # Add virtualenv site-packages to path
    venv_path = (
        Path(root) / "../" / ".venv" / "lib" / "python3.12" / "site-packages"
    )  # adjust Python version as needed
    sys.path.insert(0, str(venv_path))


import os

from textual.features import parse_features

from bb.tui.app import PRReviewApp


def review_prs(repo_slug: str) -> None:
    app = PRReviewApp(
        repo_slug,
    )
    features = set(parse_features(os.environ.get("TEXTUAL", "")))
    features.add("debug")
    features.add("devtools")
    app.run()


if __name__ == "__main__":
    review_prs("bitbucket/core")
