"""Pytest configuration and fixtures."""

import pytest
from pubgator import PubGator


@pytest.fixture
def client():
    """Create a PubGator client for testing."""
    client = PubGator(rate_limit=True)
    yield client
    client.close()
