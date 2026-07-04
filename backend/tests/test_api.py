from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """
    Test that root endpoint returns correct status message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FRIDAY API is online."}

def test_health_check():
    """
    Test that health check endpoint returns status ok.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "FRIDAY API"}
