"""Guard the public Observability v1 producer/ingestion contract."""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from goreecloud_observability import OperationalSignal


class ObservabilityProducerCompatibilityTests(unittest.TestCase):
    def test_schema_valid_manager_nested_attributes_can_be_ingested(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "contracts" / "operational-signal.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["attributes"], {"type": "object"})
        now = datetime(2026, 10, 15, 12, tzinfo=timezone.utc).isoformat()
        raw = {
            "signal_id": "manager-review", "component_id": "goreecloud-manager",
            "source": "goreecloud-manager", "signal_type": "readiness",
            "state": "healthy", "observed_at": now, "collected_at": now,
            "ttl_seconds": 60,
            "attributes": {"checks": {"api": "healthy"}, "counts": [1, 2]},
        }
        self.assertEqual(set(raw).difference(schema["properties"]), set())
        signal = OperationalSignal.from_mapping(raw)
        self.assertEqual(signal.attributes, raw["attributes"])


if __name__ == "__main__":
    unittest.main()
