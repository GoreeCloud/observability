from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
import math
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
    cleaned = value.strip()
    if len(cleaned) > 256:
        raise ValueError(f"{name} exceeds the Development length limit")
    return cleaned


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


def _sensitive_attribute_key(key: str) -> bool:
    # Normalize camelCase and separators so prefixed/suffixed credential fields cannot
    # bypass the base exact-key blocklist (e.g. db_password, oauthToken).
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    normalized = re.sub(r"[^a-z0-9]+", "_", separated.lower()).strip("_")
    pieces = set(normalized.split("_"))
    compact = normalized.replace("_", "")
    # Some producers emit unseparated aliases such as "apikey",
    # "privatekey" or "passwordhash"; block those as credential metadata.
    credential_fragments = (
        "password", "passwd", "passphrase", "secret", "credential",
        "authorization", "cookie", "privatekey", "apikey",
    )
    return (
        any(fragment in compact for fragment in credential_fragments)
        or compact.endswith("token")
        or normalized in SENSITIVE_KEYS
        or bool(pieces & {"password", "passwd", "passphrase", "secret",
                          "token", "credential", "credentials", "cookie",
                          "authorization", "bearer"})
        or "private_key" in normalized
        or "api_key" in normalized
    )


def _safe_attribute_value(value: Any, depth: int, remaining: list[int]) -> Any:
    """Validate nested v1 JSON attributes with bounded size and secret filtering."""
    remaining[0] -= 1
    if remaining[0] < 0 or depth > 8:
        raise ValueError("telemetry attributes exceed the Development complexity limit")
    if isinstance(value, Mapping):
        if len(value) > 64:
            raise ValueError("attributes exceed the Development limit")
        safe: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip() or len(key) > 128:
                raise ValueError("telemetry attribute key is invalid")
            if _sensitive_attribute_key(key):
                raise ValueError("sensitive telemetry attribute key is not permitted")
            safe[key] = _safe_attribute_value(item, depth + 1, remaining)
        return safe
    if isinstance(value, list):
        if len(value) > 64:
            raise ValueError("telemetry array exceeds the Development limit")
        return [_safe_attribute_value(item, depth + 1, remaining) for item in value]
    if not isinstance(value, (str, bool, int, float, type(None))):
        raise ValueError("telemetry attributes must be JSON-safe values")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite telemetry attributes are not permitted")
    if isinstance(value, str) and len(value) > 2048:
        raise ValueError("telemetry string attribute exceeds the Development limit")
    return value


def _safe_attributes(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("attributes must be an object")
    return _safe_attribute_value(value, 0, [256])


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
        if type(ttl) is not int or ttl < 1 or ttl > 86400:
            raise ValueError("ttl_seconds must be an integer between 1 and 86400")
        gaps = value.get("collection_gaps", [])
        if not isinstance(gaps, list) or not all(isinstance(item, str) for item in gaps):
            raise ValueError("collection_gaps must be a list of strings")
        if len(gaps) > 32 or any(len(item) > 256 for item in gaps):
            raise ValueError("collection_gaps exceed the Development limit")
        observed = _time(value.get("observed_at"), "observed_at")
        collected = _time(value.get("collected_at"), "collected_at")
        if collected < observed:
            raise ValueError("collected_at must not precede observed_at")
        correlation = value.get("correlation_id")
        if correlation is not None:
            correlation = _text(correlation, "correlation_id")
        return cls(
            signal_id=_text(value.get("signal_id"), "signal_id"),
            component_id=_text(value.get("component_id"), "component_id"),
            source=_text(value.get("source"), "source"),
            signal_type=_text(value.get("signal_type"), "signal_type"),
            state=state,
            observed_at=observed,
            collected_at=collected,
            ttl_seconds=ttl,
            correlation_id=correlation,
            attributes=_safe_attributes(value.get("attributes", {})),
            collection_gaps=tuple(gaps),
        )

    def fresh_at(self, now: datetime | None = None) -> bool:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        age = (current - self.observed_at).total_seconds()
        return self.collected_at <= current and 0 <= age <= self.ttl_seconds

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
