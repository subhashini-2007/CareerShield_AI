"""Automated tests for health diagnostics and root API."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns application metadata and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "CareerShield AI"
    assert "version" in data
    assert "docs_url" in data
    assert "health_url" in data


def test_health_endpoint_contract(client: TestClient):
    """Test health check returns complete contract without leaking secrets."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    # Validate high-level contract
    assert "status" in data
    assert "timestamp" in data
    assert "app" in data
    assert "database" in data
    assert "model" in data

    # Validate database health details
    db = data["database"]
    assert "connected" in db
    assert "engine" in db
    assert isinstance(db["connected"], bool)

    # Validate model health details
    model = data["model"]
    assert "loaded" in model
    assert "status" in model
    assert model["status"] in ["trained", "not_trained"]

    # Security check: Ensure no connection strings or passwords leaked
    raw_text = response.text.lower()
    assert "password" not in raw_text
    assert "secret" not in raw_text
    assert "credentials" not in raw_text


def test_cors_preflight_headers(client: TestClient):
    """Verify CORS middleware returns allow-origin for authorized origins."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_health_endpoint_active_model_status(client: TestClient):
    """Verify health endpoint reports trained model loaded with canonical version when baseline is available."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    model = data["model"]
    assert model["loaded"] is True
    assert model["status"] == "trained"
    assert "CareerShield-AI-Baseline-TFIDF-LogReg" in model["version"]


def test_health_endpoint_error_handling_graceful(client: TestClient, monkeypatch):
    """Verify health endpoint handles model-loading exceptions gracefully without 500 crashes."""
    from app.api.v1.endpoints import health

    def faulty_get_ml_service():
        raise RuntimeError("Simulated ML engine memory corruption")

    monkeypatch.setattr(health, "get_ml_service", faulty_get_ml_service)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    model = data["model"]
    assert model["loaded"] is False
    assert model["status"] == "not_trained"
    assert model["version"] == "not-loaded"

