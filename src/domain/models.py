from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class LogEvent(BaseModel):
    timestamp: datetime
    level: str
    message: str
    host: str | None = None
    service: str | None = None
    user: str | None = None
    ip: str | None = None
    request_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_host_or_service(self) -> LogEvent:
        if not self.host and not self.service:
            raise ValueError("Either host or service must be provided")
        return self

    @property
    def source(self) -> str:
        return self.host or self.service or "unknown"


class AnomalyResult(BaseModel):
    event: LogEvent
    score: float
    is_anomaly: bool
    model_version: str
