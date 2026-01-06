from __future__ import annotations

import json
import random
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from domain.models import LogEvent

NORMAL_LEVELS = ["INFO", "DEBUG", "WARNING"]
ANOMALY_LEVELS = ["ERROR", "CRITICAL", "ALERT"]
HOSTS = ["edge-gw", "auth-svc", "payments", "core-db", "web-01"]
USERS = ["alice", "bob", "carol", "dave", "ops"]
MESSAGES = [
    "User login succeeded",
    "Session refreshed",
    "Token validated",
    "Request completed",
    "Cache hit",
    "Policy check passed",
]
ANOMALY_MESSAGES = [
    "Multiple failed logins detected",
    "Privilege escalation attempt",
    "Unexpected outbound connection to 203.0.113.45",
    "Service crash detected",
    "Suspicious command execution",
]


def generate_events(
    total: int = 500,
    anomaly_ratio: float = 0.05,
    start_time: datetime | None = None,
) -> list[LogEvent]:
    start_time = start_time or datetime.now(timezone.utc) - timedelta(minutes=total)
    events: list[LogEvent] = []
    anomaly_count = int(total * anomaly_ratio)
    normal_count = total - anomaly_count

    events.extend(_generate_normal_events(normal_count, start_time))
    events.extend(
        _generate_anomaly_events(anomaly_count, start_time + timedelta(minutes=normal_count))
    )
    random.shuffle(events)
    return events


def to_json_lines(events: Iterable[LogEvent]) -> list[str]:
    lines: list[str] = []
    for event in events:
        payload = event.model_dump()
        payload["timestamp"] = event.timestamp.isoformat()
        lines.append(json.dumps(payload, ensure_ascii=True))
    return lines


def to_plain_lines(events: Iterable[LogEvent]) -> list[str]:
    lines: list[str] = []
    for event in events:
        source = event.host or event.service or "unknown"
        line = f"{event.timestamp.isoformat()} {event.level} {source} {event.message}"
        if event.user:
            line += f" user={event.user}"
        if event.ip:
            line += f" ip={event.ip}"
        if event.request_id:
            line += f" request_id={event.request_id}"
        lines.append(line)
    return lines


def _generate_normal_events(count: int, start_time: datetime) -> list[LogEvent]:
    events: list[LogEvent] = []
    for i in range(count):
        timestamp = start_time + timedelta(minutes=i)
        host = random.choice(HOSTS)
        message = random.choice(MESSAGES)
        user = random.choice(USERS)
        ip = f"10.0.0.{random.randint(2, 250)}"
        request_id = f"req-{random.randint(1000, 9999)}"
        events.append(
            LogEvent(
                timestamp=timestamp,
                level=random.choice(NORMAL_LEVELS),
                host=host,
                message=message,
                user=user,
                ip=ip,
                request_id=request_id,
                attributes={"latency_ms": random.randint(10, 250)},
            )
        )
    return events


def _generate_anomaly_events(count: int, start_time: datetime) -> list[LogEvent]:
    events: list[LogEvent] = []
    for i in range(count):
        timestamp = start_time + timedelta(minutes=i)
        host = random.choice(HOSTS)
        message = random.choice(ANOMALY_MESSAGES)
        user = random.choice(USERS)
        ip = f"203.0.113.{random.randint(1, 250)}"
        request_id = f"anomaly-{random.randint(10000, 99999)}"
        events.append(
            LogEvent(
                timestamp=timestamp,
                level=random.choice(ANOMALY_LEVELS),
                host=host,
                message=message,
                user=user,
                ip=ip,
                request_id=request_id,
                attributes={"latency_ms": random.randint(500, 2000)},
            )
        )
    return events
