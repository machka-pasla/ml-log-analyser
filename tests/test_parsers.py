import pytest

from application.parsers import LogParser


def test_parse_json_line() -> None:
    parser = LogParser()
    line = (
        '{"timestamp":"2026-01-15T10:00:00+00:00","host":"auth-svc","level":"INFO",'
        '"message":"User login succeeded","user":"alice","ip":"10.0.0.10","request_id":"req-1"}'
    )
    event = parser.parse_json_line(line)
    assert event.host == "auth-svc"
    assert event.level == "INFO"
    assert event.user == "alice"


def test_parse_plain_text() -> None:
    parser = LogParser()
    line = (
        "2026-01-15T10:00:00+00:00 INFO auth-svc User login succeeded "
        "user=alice ip=10.0.0.10 request_id=req-1"
    )
    event = parser.parse_plain_text(line)
    assert event.host == "auth-svc"
    assert event.level == "INFO"
    assert event.user == "alice"
    assert event.ip == "10.0.0.10"
    assert event.request_id == "req-1"


def test_parse_lines_unknown_format() -> None:
    parser = LogParser()
    with pytest.raises(ValueError):
        parser.parse_lines(["x"], "xml")
