# Observability v1 producer-to-ingestion qualification

**Status: NOT ACCEPTED — source-contract audit only.**  
**Review date:** 2026-10-15.  
**Contract:** `contracts/operational-signal.schema.json` (v1, `additionalProperties: false`).  
**Manager producer pin:** `a7f6a65f442d3e517baddbe7b6ce7c250d142c8c`.

## Confirmed structural gap

Manager `integrations/observability.py::build_operational_signal` accepts JSON-safe nested dictionaries and lists inside `attributes`. The authoritative v1 schema specifies `attributes` as an object without scalar-only value restrictions. The current Observability `OperationalSignal._safe_attributes` rejects nested dictionary or list values. A Manager-produced, schema-shaped signal with nested attributes can therefore fail ingestion even when all required top-level fields are valid.

**Scope:** This is verified from producer, schema, and ingestion source inspection, not from a live cross-service call. No deployed or authenticated telemetry producer has been accepted.

## Replay and recovery review

`HealthStore.add` currently appends retained signals to a bounded per-component queue without duplicate `signal_id`/`source` detection. Replays may increase `evidence_count`; producer-scoped deduplication and deterministic handling of conflicting duplicate payloads are not yet qualified. `reclaim_expired_components` is an explicit confirmation-gated Development-only library operation; it does not provide durable retention, audited deletion, or disaster recovery.

## Required acceptance

1. Define canonical v1 nested attribute support (including privacy filtering, depth and payload bounds) and test Manager producer → Observability model ingestion for both scalar and nested values; do not silently change published contract semantics.
2. Define producer-scoped signal identity and retry/replay policy. Demonstrate idempotent retries and fail-closed conflicting duplicate evidence without mutating health state.
3. Add an authenticated live producer transport test, ingestion authorization, bounded retention/deletion and restore evidence with explicit environmental scope.
4. Verify `unknown`/`stale` states, collection gaps and timestamp integrity at the exact candidate revisions before promotion.

**Execution note:** Proposed store replay-handling source updates were blocked by connected GitHub tool safety checks. No deduplication fix is claimed. This audit is not independent approval or production qualification.
