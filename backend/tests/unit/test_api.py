from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["budget"] == 6

def test_api_config():
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["budget"] == 6
    assert data["max_upload_mb"] == 50

def test_demo_load_and_session():
    resp = client.post("/api/demo/load")
    assert resp.status_code == 201
    doc = resp.json()
    assert "doc_id" in doc
    doc_id = doc["doc_id"]
    assert doc["num_pages"] == 11
    
    # Create session
    s_resp = client.post("/api/sessions", json={"doc_id": doc_id})
    assert s_resp.status_code == 201
    s_data = s_resp.json()
    assert "session_id" in s_data