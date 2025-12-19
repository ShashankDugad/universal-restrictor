"""
Pytest configuration and fixtures.
"""

import pytest
import os

# Set test environment before importing app
# API key must be at least 16 characters
os.environ["API_KEYS"] = "test-key-1234567890:test-tenant:free"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["REDIS_URL"] = ""


@pytest.fixture(scope="session")
def api_key():
    """Return test API key."""
    return "test-key-1234567890"


@pytest.fixture(scope="session")
def auth_headers(api_key):
    """Return auth headers."""
    return {"X-API-Key": api_key}
