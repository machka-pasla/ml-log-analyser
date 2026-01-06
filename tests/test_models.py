from datetime import datetime, timezone

from application.features import FeatureExtractor
from domain.models import LogEvent
from infrastructure.models.baseline import FrequencyBaselineDetector
from infrastructure.models.isolation_forest import IsolationForestDetector


def _event(message: str, level: str = "INFO") -> LogEvent:
    return LogEvent(
        timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc),
        host="auth-svc",
        level=level,
        message=message,
        user="alice",
        ip="10.0.0.10",
        request_id="req-1",
    )


def test_baseline_scores_unseen_message_higher() -> None:
    detector = FrequencyBaselineDetector()
    normal = [_event("User login succeeded")]
    detector.train(normal)
    scores = detector.score(
        [_event("User login succeeded"), _event("Privilege escalation attempt")]
    )
    assert scores[1] > scores[0]


def test_isolation_forest_scores_between_zero_and_one() -> None:
    events = [
        _event("User login succeeded"),
        _event("Request completed"),
        _event("Cache hit"),
        _event("Session refreshed"),
        _event("Policy check passed"),
    ]
    detector = IsolationForestDetector(feature_extractor=FeatureExtractor())
    detector.train(events)
    scores = detector.score(events)
    assert all(0.0 <= score <= 1.0 for score in scores)
