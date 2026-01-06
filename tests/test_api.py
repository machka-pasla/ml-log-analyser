import importlib
import os
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from application.features import FeatureExtractor
from application.training import train_model
from domain.models import LogEvent
from infrastructure.registry import ModelRegistry


def test_health_and_ingest(tmp_path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/test.db"
    os.environ["ARTIFACT_DIR"] = str(tmp_path / "artifacts")
    os.environ["MODEL_TYPE"] = "baseline"

    settings_module = importlib.import_module("infrastructure.settings")
    importlib.reload(settings_module)

    events = [
        LogEvent(
            timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc),
            host="auth-svc",
            level="INFO",
            message="User login succeeded",
            user="alice",
            ip="10.0.0.10",
            request_id="req-1",
        )
    ]
    registry = ModelRegistry(settings_module.settings.artifact_dir)
    train_model(events, "baseline", registry, FeatureExtractor())

    api_module = importlib.import_module("api.main")
    importlib.reload(api_module)

    with TestClient(api_module.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["model_loaded"] is True

        payload = {
            "format": "jsonl",
            "lines": [
                '{"timestamp":"2026-01-15T10:01:00+00:00","host":"auth-svc","level":"INFO","message":"User login succeeded"}'
            ],
        }
        ingest_response = client.post("/ingest", json=payload)
        assert ingest_response.status_code == 200
        assert ingest_response.json()["received"] == 1
