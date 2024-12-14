"""Version information for bb CLI - consumed by pyproject.toml for package versioning"""

__version__ = "0.3.0"


def get_user_agent():
    """Return the formatted user agent string"""
    return f"bb-cli/{__version__}"
