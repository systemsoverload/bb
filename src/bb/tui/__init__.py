from bb.tui.app import PRReviewApp

def review_prs(repo_slug: str) -> None:
    app = PRReviewApp(repo_slug)
    app.run()


if __name__ == "__main__":
    review_prs("bitbucket/core")
