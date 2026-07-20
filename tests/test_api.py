from fastapi.testclient import TestClient

from bid_screenshot_assistant.api import app


client = TestClient(app)


def test_health_and_platform_catalog():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["platforms"] == 9

    platforms = client.get("/api/platforms")
    assert platforms.status_code == 200
    assert len(platforms.json()) == 9
