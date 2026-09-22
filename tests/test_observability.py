import unittest
from datetime import datetime, timedelta, timezone

from goreecloud_observability import HealthState, HealthStore, OperationalSignal
from goreecloud_observability.runtime import health_payload, readiness_payload


NOW = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)


def signal(signal_id="s1", state="healthy", age=0, **extra):
    observed = NOW - timedelta(seconds=age)
    payload = {
        "signal_id": signal_id,
        "component_id": "service:test",
        "source": "test-producer",
        "signal_type": "readiness",
        "state": state,
        "observed_at": observed.isoformat(),
        "collected_at": NOW.isoformat(),
        "ttl_seconds": 60,
        "attributes": {},
        "collection_gaps": [],
    }
    payload.update(extra)
    return OperationalSignal.from_mapping(payload)


class ObservabilityTests(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual("unknown", HealthStore().health("missing", NOW)["state"])

    def test_stale_only_is_stale(self):
        store = HealthStore()
        store.add(signal(age=61))
        self.assertEqual("stale", store.health("service:test", NOW)["state"])

    def test_failure_outranks_healthy(self):
        store = HealthStore()
        store.add(signal("healthy", "healthy"))
        store.add(signal("failed", "failed"))
        self.assertEqual("failed", store.health("service:test", NOW)["state"])

    def test_unknown_prevents_healthy(self):
        store = HealthStore()
        store.add(signal("healthy", "healthy"))
        store.add(signal("unknown", "unknown"))
        self.assertEqual("unknown", store.health("service:test", NOW)["state"])

    def test_secret_attribute_name_rejected(self):
        with self.assertRaises(ValueError):
            signal(attributes={"access_token": "do-not-store"})

    def test_collection_gaps_preserved(self):
        store = HealthStore()
        store.add(signal(collection_gaps=["metrics collector unavailable"]))
        self.assertEqual(["metrics collector unavailable"], store.health("service:test", NOW)["collection_gaps"])

    def test_runtime_health_is_not_production_claim(self):
        self.assertEqual("healthy", health_payload()["status"])
        self.assertFalse(readiness_payload()["production_accepted"])


if __name__ == "__main__":
    unittest.main()
