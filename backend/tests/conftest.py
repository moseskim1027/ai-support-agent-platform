"""Pytest configuration and fixtures for test suite"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up environment variables for testing"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"

    # Set required API keys with dummy values
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing-only"

    # Set optional service URLs to avoid connection attempts
    os.environ["POSTGRES_URL"] = "postgresql://test:test@localhost:5432/test_db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["QDRANT_URL"] = "http://localhost:6333"

    yield

    # Cleanup after tests (optional)
    # Could remove env vars here if needed
