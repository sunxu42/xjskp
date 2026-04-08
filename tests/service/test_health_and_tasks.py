from fastapi.testclient import TestClient

from src.service.app import app


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_tasks_endpoint():
    client = TestClient(app)
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "demo_branch_task"
