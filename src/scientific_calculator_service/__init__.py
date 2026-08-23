"""Safe scientific-calculator web service."""

from .app import VERSION, app

__version__ = VERSION

__all__ = ["VERSION", "__version__", "app"]
