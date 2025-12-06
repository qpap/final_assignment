
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aether.main import create_app
from aether.dependencies import reset_services


@pytest.fixture
def test_app() -> TestClient:
    reset_services()
    app = create_app(
        config_path="config/server_config.json",
        sensors_path="config/sensors.json",
    )
    with TestClient(app) as client:
        yield client
    reset_services()


def test_status_ok(test_app: TestClient) -> None:
    response = test_app.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "uptime_seconds" in data


def test_ingest_unauthorized(test_app: TestClient) -> None:
    payload = {
        "sensor_id": "sensor_unknown",
        "readings": {"pm25": 10.0},
    }
    response = test_app.post("/ingest", json=payload)
    assert response.status_code == 403
