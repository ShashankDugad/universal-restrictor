"""
API endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
import os

# Set test environment - key must be 16+ chars
os.environ["API_KEYS"] = "test-key-1234567890:test-tenant:free"
os.environ["ANTHROPIC_API_KEY"] = ""

from restrictor.api.server import app

client = TestClient(app)

# Test API key (must match what's in API_KEYS)
TEST_API_KEY = "test-key-1234567890"


class TestHealthEndpoint:
    """Test /health endpoint."""
    
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_status(self):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_returns_version(self):
        response = client.get("/health")
        data = response.json()
        assert "version" in data


class TestAnalyzeEndpoint:
    """Test /analyze endpoint."""
    
    def test_analyze_requires_auth(self):
        response = client.post("/analyze", json={"text": "test"})
        assert response.status_code in [401, 403]
    
    def test_analyze_with_valid_key(self):
        response = client.post(
            "/analyze",
            json={"text": "Hello, how are you?"},
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200
    
    def test_analyze_returns_action(self):
        response = client.post(
            "/analyze",
            json={"text": "Hello"},
            headers={"X-API-Key": TEST_API_KEY}
        )
        data = response.json()
        assert "action" in data
        assert data["action"] in ["allow", "allow_with_warning", "redact", "block"]
    
    def test_analyze_detects_email(self):
        response = client.post(
            "/analyze",
            json={"text": "Contact me at test@example.com"},
            headers={"X-API-Key": TEST_API_KEY}
        )
        data = response.json()
        assert data["action"] == "redact"
        assert "pii_email" in [d["category"] for d in data["detections"]]
    
    def test_analyze_detects_aadhaar(self):
        response = client.post(
            "/analyze",
            json={"text": "My Aadhaar is 2345 6789 0123"},
            headers={"X-API-Key": TEST_API_KEY}
        )
        data = response.json()
        assert data["action"] == "redact"
    
    def test_analyze_safe_text(self):
        response = client.post(
            "/analyze",
            json={"text": "The weather is nice today."},
            headers={"X-API-Key": TEST_API_KEY}
        )
        data = response.json()
        assert data["action"] == "allow"


class TestCategoriesEndpoint:
    """Test /categories endpoint."""
    
    def test_categories_requires_auth(self):
        response = client.get("/categories")
        assert response.status_code in [401, 403]
    
    def test_categories_returns_list(self):
        response = client.get(
            "/categories",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0


class TestMetricsEndpoint:
    """Test /metrics endpoint."""
    
    def test_metrics_returns_prometheus_format(self):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "restrictor_" in response.text
