from fastapi.testclient import TestClient

from src.service.app import app


def test_logs_stream_has_sse_format():
    client = TestClient(app)
    resp = client.get("/api/logs", headers={"accept": "text/event-stream"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
