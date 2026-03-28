"""API health check endpoint tests."""


def test_health_returns_200(client):
    """GET /api/health should return 200 with status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_response_is_json(client):
    """Health endpoint should return valid JSON with content-type header."""
    response = client.get("/api/health")
    assert "application/json" in response.headers.get("content-type", "")
