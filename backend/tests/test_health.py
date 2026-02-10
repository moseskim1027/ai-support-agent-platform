"""Tests for health check endpoints"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_readiness_check():
    """Test readiness check endpoint"""
    response = client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_liveness_check():
    """Test liveness check endpoint"""
    response = client.get("/api/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
