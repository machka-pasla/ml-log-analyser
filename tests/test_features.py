from datetime import datetime, timezone

from application.features import FeatureExtractor
from domain.models import LogEvent


def test_feature_extraction_shape() -> None:
    event = LogEvent(
        timestamp=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc),
        host="auth-svc",
        level="INFO",
        message="User login succeeded",
        user="alice",
        ip="10.0.0.10",
        request_id="req-1",
    )
    extractor = FeatureExtractor()
    features = extractor.transform([event])
    assert features.shape == (1, len(extractor.feature_names))
    assert features[0][0] >= 0
