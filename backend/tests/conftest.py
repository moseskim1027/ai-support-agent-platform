"""Pytest configuration and fixtures for test suite"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up environment variables for testing"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"

    # Set required API keys with dummy values
    os.environ["GEMINI_API_KEY"] = "AIza-test-key-for-testing-only"

    # Set service URLs to match local Docker containers
    # CI will override these with its own environment variables
    os.environ["POSTGRES_URL"] = (
        "postgresql://postgres:postgres@localhost:5432/ai_support"  # noqa: E501
    )
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["QDRANT_URL"] = "http://localhost:6333"

    yield

    # Cleanup after tests (optional)
    # Could remove env vars here if needed


@pytest.fixture(scope="function")
def client():
    """Create a test client for the FastAPI app

    Function scope ensures each test gets a fresh client instance
    to avoid state pollution between tests.
    """
    from app.main import app

    return TestClient(app)
