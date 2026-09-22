from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    STALE = "stale"
    PARTIALLY_OBSERVED = "partially_observed"
    NOT_MONITORED = "not_monitored"
    NOT_APPLICABLE = "not_applicable"


SENSITIVE_KEYS = {
    "password", "passwd", "token", "access_token", "refresh_token", "authorization",
    "cookie", "set_cookie", "secret", "client_secret", "api_key", "private_key",
}


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _time(value: Any, name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 string") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _safe_attributes(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("attributes must be an object")
    if len(value) > 64:
        raise ValueError("attributes exceed the Development limit")
    safe: dict[str, Any] = {}
    for key, item in value.items():
        normalized = str(key).lower().replace("-", "_")
        if normalized in SENSITIVE_KEYS:
            raise ValueError(f"attribute key '{key}' is not permitted")
        if isinstance(item, (dict, list, tuple, set)):
            raise ValueError("nested telemetry attributes are not supported by the Development foundation")
        if isinstance(item, str) and len(item) > 2048:
            raise ValueError("telemetry string attribute exceeds the Development limit")
        safe[str(key)] = item
    return safe


@dataclass(frozen=True, slots=True)
class OperationalSignal:
    signal_id: str
    component_id: str
    source: str
    signal_type: str
    state: HealthState
    observed_at: datetime
    collected_at: datetime
    ttl_seconds: int
    correlation_id: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    collection_gaps: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "OperationalSignal":
        if not isinstance(value, Mapping):
            raise ValueError("signal must be an object")
        try:
            state = HealthState(value.get("state"))
        except (TypeError, ValueError) as exc:
            raise ValueError("state is not supported") from exc
        ttl = value.get("ttl_seconds", 60)
        if not isinstance(ttl, int) or ttl < 1 or ttl > 86400:
            raise ValueError("ttl_seconds must be an integer between 1 and 86400")
        gaps = value.get("collection_gaps", [])
        if not isinstance(gaps, list) or not all(isinstance(item, str) for item in gaps):
            raise ValueError("collection_gaps must be a list of strings")
        correlation = value.get("correlation_id")
        if correlation is not None and not isinstance(correlation, str):
            raise ValueError("correlation_id must be a string or null")
        return cls(
            signal_id=_text(value.get("signal_id"), "signal_id"),
            component_id=_text(value.get("component_id"), "component_id"),
            source=_text(value.get("source"), "source"),
            signal_type=_text(value.get("signal_type"), "signal_type"),
            state=state,
            observed_at=_time(value.get("observed_at"), "observed_at"),
            collected_at=_time(value.get("collected_at"), "collected_at"),
            ttl_seconds=ttl,
            correlation_id=correlation,
            attributes=_safe_attributes(value.get("attributes", {})),
            collection_gaps=tuple(gaps),
        )

    def fresh_at(self, now: datetime | None = None) -> bool:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        age = (current - self.observed_at).total_seconds()
        return 0 <= age <= self.ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "component_id": self.component_id,
            "source": self.source,
            "signal_type": self.signal_type,
            "state": self.state.value,
            "observed_at": self.observed_at.isoformat(),
            "collected_at": self.collected_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "correlation_id": self.correlation_id,
            "attributes": dict(self.attributes),
            "collection_gaps": list(self.collection_gaps),
        }
