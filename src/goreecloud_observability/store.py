from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from .model import HealthState, OperationalSignal


_PRECEDENCE = {
    HealthState.FAILED: 90,
    HealthState.UNAVAILABLE: 80,
    HealthState.DEGRADED: 70,
    HealthState.STALE: 65,
    HealthState.UNKNOWN: 60,
    HealthState.PARTIALLY_OBSERVED: 50,
    HealthState.NOT_MONITORED: 40,
    HealthState.HEALTHY: 20,
    HealthState.NOT_APPLICABLE: 10,
}


class SignalCapacityError(Exception):
    """A new component cannot be stored without discarding existing evidence."""


class HealthStore:
    def __init__(self, max_signals_per_component: int = 256, max_components: int = 1024) -> None:
        if type(max_signals_per_component) is not int or max_signals_per_component < 1:
            raise ValueError("max_signals_per_component must be positive")
        if type(max_components) is not int or max_components < 1:
            raise ValueError("max_components must be positive")
        self._max = max_signals_per_component
        self._max_components = max_components
        self._signals: dict[str, deque[OperationalSignal]] = {}
        self._lock = RLock()

    def add(self, signal: OperationalSignal) -> None:
        with self._lock:
            queue = self._signals.get(signal.component_id)
            if queue is None:
                if len(self._signals) >= self._max_components:
                    raise SignalCapacityError("component capacity exhausted")
                queue = deque(maxlen=self._max)
                self._signals[signal.component_id] = queue
            queue.append(signal)

    def health(self, component_id: str, now: datetime | None = None) -> dict[str, Any]:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._lock:
            signals = list(self._signals.get(component_id, ()))
        if not signals:
            return self._aggregate(component_id, HealthState.UNKNOWN, [], ["no operational evidence collected"])

        fresh = [signal for signal in signals if signal.fresh_at(current)]
        if not fresh:
            return self._aggregate(component_id, HealthState.STALE, signals, ["all collected operational evidence is stale"])

        states = {signal.state for signal in fresh}
        if states == {HealthState.NOT_APPLICABLE}:
            state = HealthState.NOT_APPLICABLE
        else:
            applicable = [signal for signal in fresh if signal.state is not HealthState.NOT_APPLICABLE]
            state = max((signal.state for signal in applicable), key=lambda item: _PRECEDENCE[item]) if applicable else HealthState.NOT_APPLICABLE

        gaps = list(dict.fromkeys(gap for signal in fresh for gap in signal.collection_gaps))
        return self._aggregate(component_id, state, fresh, gaps)

    @staticmethod
    def _aggregate(component_id: str, state: HealthState, signals: list[OperationalSignal], gaps: list[str]) -> dict[str, Any]:
        return {
            "component_id": component_id,
            "state": state.value,
            "evidence_count": len(signals),
            "signal_ids": [signal.signal_id for signal in signals],
            "sources": list(dict.fromkeys(signal.source for signal in signals)),
            "collection_gaps": gaps,
            "production_accepted": False,
        }
