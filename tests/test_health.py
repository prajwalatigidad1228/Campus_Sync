"""
Tests for the /api/health endpoint.
Run with: pytest tests/
"""

import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client


def test_health_returns_200(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_payload(client):
    resp = client.get("/api/health")
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_404(client):
    resp = client.get("/this-does-not-exist", headers={"Accept": "application/json"})
    assert resp.status_code == 404
