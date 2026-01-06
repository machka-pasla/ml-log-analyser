from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime

import numpy as np

from domain.models import LogEvent

LEVEL_MAP = {
    "DEBUG": 0,
    "INFO": 1,
    "NOTICE": 2,
    "WARNING": 3,
    "ERROR": 4,
    "CRITICAL": 5,
    "ALERT": 6,
}

IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
DIGIT_RE = re.compile(r"\d")
WORD_RE = re.compile(r"\w+")
SPECIAL_RE = re.compile(r"[^A-Za-z0-9\s]")
NUMBER_RE = re.compile(r"\b\d+\b")
HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
KEYWORD_RE = re.compile(
    r"(failed|denied|invalid|unauthorized|sudo|root|admin|attack|malware|ransom|"
    r"sql|injection|timeout|panic|crash|exfil|phish|brute|token|expired|forbidden|"
    r"suspicious|blocked|violation)",
    re.IGNORECASE,
)


class FeatureExtractor:
    def __init__(self) -> None:
        self.feature_names = [
            "level_code",
            "message_len",
            "message_words",
            "unique_word_ratio",
            "digit_count",
            "digit_ratio",
            "uppercase_ratio",
            "special_char_count",
            "keyword_hits",
            "ip_count",
            "has_ip",
            "hour",
            "hour_sin",
            "hour_cos",
            "weekday",
            "is_weekend",
            "has_user",
            "user_length",
            "has_request_id",
            "request_length",
            "attributes_count",
            "host_hash",
            "template_hash",
        ]

    def transform(self, events: list[LogEvent]) -> np.ndarray:
        rows = [self._event_to_features(event) for event in events]
        return np.array(rows, dtype=float)

    def _event_to_features(self, event: LogEvent) -> list[float]:
        level_code = LEVEL_MAP.get(event.level.upper(), 7)
        message = event.message or ""
        message_len = float(len(message))
        words = WORD_RE.findall(message)
        message_words = float(len(words))
        unique_word_ratio = _safe_ratio(len(set(words)), len(words))
        digit_count = float(len(DIGIT_RE.findall(message)))
        digit_ratio = _safe_ratio(digit_count, message_len)
        uppercase_ratio = _uppercase_ratio(message)
        special_char_count = float(len(SPECIAL_RE.findall(message)))
        keyword_hits = float(len(KEYWORD_RE.findall(message)))
        ip_count = float(len(IP_RE.findall(message)))
        has_ip = 1.0 if event.ip or ip_count else 0.0
        hour, hour_sin, hour_cos, weekday, is_weekend = _time_features(event.timestamp)
        has_user = 1.0 if event.user else 0.0
        user_length = float(len(event.user)) if event.user else 0.0
        has_request = 1.0 if event.request_id else 0.0
        request_length = float(len(event.request_id)) if event.request_id else 0.0
        attributes_count = float(len(event.attributes)) if event.attributes else 0.0
        host_hash = _hash_bucket(event.source)
        template_hash = _hash_bucket(_normalize_message(message))
        return [
            float(level_code),
            message_len,
            message_words,
            unique_word_ratio,
            digit_count,
            digit_ratio,
            uppercase_ratio,
            special_char_count,
            keyword_hits,
            ip_count,
            has_ip,
            hour,
            hour_sin,
            hour_cos,
            weekday,
            is_weekend,
            has_user,
            user_length,
            has_request,
            request_length,
            attributes_count,
            host_hash,
            template_hash,
        ]


def _time_features(timestamp: datetime) -> tuple[float, float, float, float, float]:
    hour = float(timestamp.hour)
    weekday = float(timestamp.weekday())
    radians = 2 * math.pi * hour / 24.0
    hour_sin = float(math.sin(radians))
    hour_cos = float(math.cos(radians))
    is_weekend = 1.0 if weekday >= 5 else 0.0
    return hour, hour_sin, hour_cos, weekday, is_weekend


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _uppercase_ratio(message: str) -> float:
    if not message:
        return 0.0
    letters = sum(1 for ch in message if ch.isalpha())
    if letters == 0:
        return 0.0
    upper = sum(1 for ch in message if ch.isupper())
    return float(upper) / float(letters)


def _hash_bucket(value: str, buckets: int = 1000) -> float:
    if not value:
        return 0.0
    digest = hashlib.md5(value.encode("utf-8")).hexdigest()
    bucket = int(digest, 16) % buckets
    return float(bucket) / float(buckets)


def _normalize_message(message: str) -> str:
    normalized = message
    normalized = UUID_RE.sub("<UUID>", normalized)
    normalized = IP_RE.sub("<IP>", normalized)
    normalized = HEX_RE.sub("<HEX>", normalized)
    normalized = NUMBER_RE.sub("<NUM>", normalized)
    return normalized
