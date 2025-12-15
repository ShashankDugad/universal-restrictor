"""
API package for Universal Restrictor.

Run the server with:
    uvicorn restrictor.api.server:app --reload
"""

from .server import app

__all__ = ["app"]
