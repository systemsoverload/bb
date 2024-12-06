"""Version information for bb CLI"""

__version__ = "0.1.2"  # Follow semantic versioning

def get_user_agent():
    """Return the formatted user agent string"""
    return f"bb-cli/{__version__}"
