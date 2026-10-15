import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from goreecloud_observability import HealthState, HealthStore, OperationalSignal
from goreecloud_observability.store import SignalCapacityError
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

    def test_collected_before_observation_is_invalid(self):
        with self.assertRaisesRegex(ValueError, "collected_at must not precede"):
            signal(observed_at=(NOW + timedelta(seconds=5)).isoformat())

    def test_equal_observation_and_collection_times_are_valid(self):
        self.assertEqual(NOW, signal().observed_at)

    def test_future_collected_evidence_is_not_current_health(self):
        store = HealthStore()
        store.add(signal(collected_at=(NOW + timedelta(seconds=10)).isoformat()))
        self.assertEqual("stale", store.health("service:test", NOW)["state"])
        self.assertEqual("healthy", store.health("service:test", NOW + timedelta(seconds=10))["state"])

    def test_stale_only_is_stale(self):
        store = HealthStore()
        store.add(signal(age=61))
        self.assertEqual("stale", store.health("service:test", NOW)["state"])

    def test_explicit_stale_signal_is_not_an_aggregation_error(self):
        store = HealthStore()
        store.add(signal("healthy", "healthy"))
        store.add(signal("stale-report", "stale"))
        result = store.health("service:test", NOW)
        self.assertEqual("stale", result["state"])
        self.assertFalse(result["production_accepted"])

    def test_explicit_stale_does_not_hide_failure(self):
        store = HealthStore()
        store.add(signal("stale-report", "stale"))
        store.add(signal("failed-report", "failed"))
        self.assertEqual("failed", store.health("service:test", NOW)["state"])

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

    def test_secret_field_variants_are_rejected(self):
        for key in ("db_password", "oauthToken", "authorization_header",
                    "session_cookie", "x-api-key", "privateKey",
                    "recoveryCredentials", "apikey", "apiKey", "PRIVATEKEY",
                    "passwordHash", "clientsecret", "authToken", "oauthtoken"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError, "sensitive"):
                    signal(attributes={key: "synthetic-placeholder"})

    def test_benign_operational_field_names_remain_allowed(self):
        stored = signal(attributes={"request_count": 5, "readyState": True})
        self.assertEqual({"request_count": 5, "readyState": True}, stored.attributes)

    def test_nested_contract_attributes_are_accepted(self):
        attributes = {"checks": {"api": "healthy"}, "counts": [1, 2], "labels": [{"zone": "a"}]}
        self.assertEqual(attributes, signal(attributes=attributes).attributes)

    def test_nested_credentials_and_nonfinite_values_are_rejected(self):
        for attributes in (
            {"checks": {"authorization_header": "placeholder"}},
            {"samples": [{"apiKey": "placeholder"}]},
            {"stats": {"duration": float("inf")}},
            {"counts": [float("nan")]},
        ):
            with self.subTest(attributes=repr(attributes)):
                with self.assertRaises(ValueError):
                    signal(attributes=attributes)

    def test_nested_attribute_complexity_is_bounded(self):
        deep = {"status": "ok"}
        for _ in range(9):
            deep = {"nested": deep}
        for attributes in (
            deep, {"samples": list(range(65))},
            {"samples": [[0] * 64 for _ in range(5)]},
        ):
            with self.subTest(size=len(repr(attributes))):
                with self.assertRaises(ValueError):
                    signal(attributes=attributes)

    def test_collection_gaps_preserved(self):
        store = HealthStore()
        store.add(signal(collection_gaps=["metrics collector unavailable"]))
        result = store.health("service:test", NOW)
        self.assertEqual(["metrics collector unavailable"], result["collection_gaps"])
        self.assertEqual("partially_observed", result["state"])

    def test_component_capacity_rejects_new_identity_without_eviction(self):
        store = HealthStore(max_components=1, max_signals_per_component=2)
        store.add(signal("first", "healthy"))
        store.add(signal("second", "healthy"))
        with self.assertRaises(SignalCapacityError):
            store.add(OperationalSignal.from_mapping({
                **signal("third").to_dict(), "component_id": "service:other"
            }))
        self.assertEqual(["first", "second"], store.health("service:test", NOW)["signal_ids"])
        self.assertEqual("unknown", store.health("service:other", NOW)["state"])

    def test_expired_component_reclamation_requires_confirmation(self):
        store = HealthStore(max_components=1)
        store.add(signal("old", age=61))
        with self.assertRaisesRegex(ValueError, "explicit confirmation"):
            store.reclaim_expired_components(NOW)
        self.assertEqual("stale", store.health("service:test", NOW)["state"])
        self.assertEqual(["service:test"], store.reclaim_expired_components(NOW, confirm=True))
        self.assertEqual("unknown", store.health("service:test", NOW)["state"])
        store.add(signal("replacement"))
        self.assertEqual("healthy", store.health("service:test", NOW)["state"])

    def test_reclamation_preserves_fresh_and_future_collected_evidence(self):
        store = HealthStore(max_components=3)
        store.add(signal("stale", age=61))
        store.add(OperationalSignal.from_mapping({
            **signal("fresh").to_dict(), "component_id": "service:fresh",
        }))
        store.add(OperationalSignal.from_mapping({
            **signal("future", collected_at=(NOW + timedelta(seconds=10)).isoformat()).to_dict(),
            "component_id": "service:future",
        }))
        self.assertEqual(["service:test"], store.reclaim_expired_components(NOW, confirm=True))
        self.assertEqual("healthy", store.health("service:fresh", NOW)["state"])
        self.assertEqual("stale", store.health("service:future", NOW)["state"])
        self.assertEqual("healthy", store.health("service:future", NOW + timedelta(seconds=10))["state"])

    def test_invalid_store_limits_rejected(self):
        for limit in (0, -1, True):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    HealthStore(max_components=limit)
                with self.assertRaises(ValueError):
                    HealthStore(max_signals_per_component=limit)

    def test_concurrent_ingest_and_snapshot_preserve_store_integrity(self):
        store = HealthStore(max_signals_per_component=50)
        store.add(signal("initial", "healthy"))
        def write(index):
            store.add(signal(f"signal-{index}", "healthy"))
            return store.health("service:test", NOW)["state"]
        with ThreadPoolExecutor(max_workers=12) as executor:
            results = list(executor.map(write, range(250)))
        self.assertEqual(["healthy"] * 250, results)
        self.assertEqual(50, store.health("service:test", NOW)["evidence_count"])

    def test_boolean_ttl_rejected(self):
        with self.assertRaises(ValueError):
            signal(ttl_seconds=True)

    def test_oversized_signal_id_rejected(self):
        with self.assertRaises(ValueError):
            signal(signal_id="s" * 257)

    def test_bounded_metadata(self):
        for change in (
            {"component_id": "c" * 257},
            {"source": "x" * 257},
            {"correlation_id": "x" * 257},
            {"collection_gaps": ["gap"] * 33},
            {"collection_gaps": ["x" * 257]},
        ):
            with self.subTest(change=list(change)):
                with self.assertRaises(ValueError):
                    signal(**change)

    def test_scalar_attribute_values(self):
        for value in (float("nan"), float("inf"), object()):
            with self.subTest(value=str(value)):
                with self.assertRaises(ValueError):
                    signal(attributes={"duration_ms": value})
        stored = signal(attributes={"duration_ms": 2.5, "attempts": 3})
        self.assertEqual(2.5, stored.attributes["duration_ms"])

    def test_runtime_health_is_not_production_claim(self):
        self.assertEqual("healthy", health_payload()["status"])
        self.assertIs(health_payload()["production_accepted"], False)
        self.assertEqual("development-reference-runtime", health_payload()["scope"])
        self.assertFalse(readiness_payload()["production_accepted"])


if __name__ == "__main__":
    unittest.main()
