from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from application.model import IAnomalyDetector
from domain.models import AnomalyResult, LogEvent

NUMBER_RE = re.compile(r"\b\d+\b")
IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


class FrequencyBaselineDetector(IAnomalyDetector):
    def __init__(self, model_version: str = "baseline") -> None:
        self.template_counts: Counter[str] = Counter()
        self.total: int = 0
        self.max_count: int = 0
        self.model_version = model_version

    def train(self, events: list[LogEvent]) -> None:
        templates = [_event_template(event) for event in events]
        self.template_counts = Counter(templates)
        self.total = sum(self.template_counts.values())
        self.max_count = max(self.template_counts.values(), default=0)

    def score(self, events: list[LogEvent]) -> list[float]:
        scores: list[float] = []
        for event in events:
            template = _event_template(event)
            count = self.template_counts.get(template, 0)
            if self.max_count == 0:
                scores.append(1.0)
            else:
                frequency = count / self.max_count
                scores.append(1.0 - frequency)
        return scores

    def predict(self, events: list[LogEvent], threshold: float) -> list[AnomalyResult]:
        scores = self.score(events)
        results = []
        for event, score in zip(events, scores, strict=True):
            results.append(
                AnomalyResult(
                    event=event,
                    score=score,
                    is_anomaly=score >= threshold,
                    model_version=self.model_version,
                )
            )
        return results

    def save(self, path: str) -> None:
        payload = {
            "template_counts": dict(self.template_counts),
            "total": self.total,
            "max_count": self.max_count,
            "model_version": self.model_version,
        }
        Path(path).mkdir(parents=True, exist_ok=True)
        with open(Path(path) / "baseline.json", "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)

    @classmethod
    def load(cls, path: str):
        with open(Path(path) / "baseline.json", encoding="utf-8") as handle:
            payload = json.load(handle)
        instance = cls(model_version=payload.get("model_version", "baseline"))
        instance.template_counts = Counter(payload.get("template_counts", {}))
        instance.total = int(payload.get("total", 0))
        instance.max_count = int(payload.get("max_count", 0))
        return instance


def _normalize_message(message: str) -> str:
    normalized = message
    normalized = IP_RE.sub("<IP>", normalized)
    normalized = UUID_RE.sub("<UUID>", normalized)
    normalized = HEX_RE.sub("<HEX>", normalized)
    normalized = NUMBER_RE.sub("<NUM>", normalized)
    return normalized


def _event_template(event: LogEvent) -> str:
    normalized = _normalize_message(event.message)
    level = event.level.upper()
    source = event.source
    return f"{level}|{source}|{normalized}"
