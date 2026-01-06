from __future__ import annotations

import json
import re
from collections.abc import Iterable

from domain.models import LogEvent

DEFAULT_PLAIN_PATTERNS = [
    r"(?P<timestamp>\S+)\s+(?P<level>[A-Z]+)\s+(?P<host>\S+)\s+(?P<message>.+)",
    r"(?P<timestamp>\S+)\s+(?P<level>[A-Z]+)\s+(?P<service>\S+)\s+(?P<message>.+)",
]

USER_RE = re.compile(r"\buser=(?P<user>[A-Za-z0-9_.-]+)")
IP_RE = re.compile(r"\bip=(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\b")
REQUEST_RE = re.compile(r"\brequest_id=(?P<request_id>[A-Za-z0-9-]+)\b")


class LogParser:
    def __init__(self, plain_patterns: Iterable[str] | None = None) -> None:
        patterns = list(plain_patterns) if plain_patterns else DEFAULT_PLAIN_PATTERNS
        self.plain_regexes = [re.compile(pattern) for pattern in patterns]

    def parse_json_line(self, line: str) -> LogEvent:
        payload = json.loads(line)
        return LogEvent.model_validate(payload)

    def parse_plain_text(self, line: str) -> LogEvent:
        for regex in self.plain_regexes:
            match = regex.match(line)
            if not match:
                continue
            data = match.groupdict()
            message = data.pop("message", "")
            attributes = {
                k: v
                for k, v in data.items()
                if k not in {"timestamp", "level", "host", "service"}
            }
            user = _search_optional(USER_RE, message)
            ip = _search_optional(IP_RE, message)
            request_id = _search_optional(REQUEST_RE, message)
            payload = {
                "timestamp": data.get("timestamp"),
                "level": data.get("level"),
                "message": message,
                "user": user,
                "ip": ip,
                "request_id": request_id,
                "attributes": attributes,
            }
            if "host" in data:
                payload["host"] = data.get("host")
            if "service" in data:
                payload["service"] = data.get("service")
            return LogEvent.model_validate(payload)
        raise ValueError("Plain text log did not match any known pattern")

    def parse_lines(self, lines: Iterable[str], fmt: str) -> list[LogEvent]:
        fmt = fmt.lower()
        events: list[LogEvent] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if fmt == "jsonl":
                events.append(self.parse_json_line(line))
            elif fmt == "plain":
                events.append(self.parse_plain_text(line))
            else:
                raise ValueError(f"Unsupported format: {fmt}")
        return events


def _search_optional(regex: re.Pattern[str], message: str) -> str | None:
    match = regex.search(message)
    if not match:
        return None
    groupdict = match.groupdict()
    if groupdict:
        return next(iter(groupdict.values()))
    return match.group(0)
