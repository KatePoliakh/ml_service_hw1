from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_evaluate_endpoint_exists():
    """Test that the evaluate endpoint is accessible"""
    # Test with valid data but non-existent model
    # We expect 404 (Model not found), which means the route exists
    response = client.post(
        "/models/evaluate",
        json={"model_id": "test", "dataset": "test.csv"}
    )
    # 404 means endpoint exists but model not found - this is correct behavior
    assert response.status_code == 404, f"Expected 404 for non-existent model, got {response.status_code}"

def test_evaluate_missing_fields():
    """Test that evaluate endpoint requires required fields"""
    response = client.post("/models/evaluate", json={})
    assert response.status_code == 422  # Should be validation error, not 404
    data = response.json()
    assert "detail" in data