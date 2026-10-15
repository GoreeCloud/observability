# Observability v1 producer-to-ingestion qualification

**Status: SOURCE CONTRACT AND REPLAY TESTS PASSED; live integration and production acceptance remain outstanding.**  
**Reviewed:** 2026-10-15  
**Authoritative contract:** `contracts/operational-signal.schema.json` (v1, `additionalProperties: false`)  
**Manager producer pin:** `a7f6a65f442d3e517baddbe7b6ce7c250d142c8c`.

## Finding and correction — nested attributes

The Manager v1 producer adapter permits JSON-safe nested dictionaries and lists inside `attributes`, and the public schema defines `attributes` as an object without scalar-only value restrictions. An earlier Observability ingestion model rejected nested values.

**Corrective commit:** `d91ee8a53058c9e83fffbbfe5474cf28ba0e740d` allows nested v1-compatible objects and arrays, with recursive sensitive-key filtering, finite JSON numbers, string limits, maximum nesting depth eight, maximum per-object/array length 64 and a bounded node budget of 256. Positive interoperability-shaped and negative privacy/complexity regressions were added.

## Finding and correction — retries

An earlier `HealthStore.add` appended repeated same-producer signals, inflating `evidence_count`.

**Corrective commit:** `f6edc0b455758c2d7ce060db6489b5d88ff43fea` now treats an identical same-source/same-`signal_id` retry as a no-op; a conflicting reuse raises `ValueError` before mutation. Equal IDs from distinct producers remain independent evidence. Source tests cover all three behaviors.

**Verification:** exact-source GitHub CI succeeded at `97535ee97e73708aeceb2fc3549ec45abb022ca4`, running **48 tests**. The earlier red producer-contract run demonstrates that the regression previously detected scalar-only ingestion.

## Remaining acceptance requirements

- Run Manager-produced payloads through a live authenticated Observability ingress on exact compatible revisions; structural test fixtures are not live producer authentication.
- Qualify producer identity and authorization, bounded retention/deletion, concurrency and replay persistence semantics across restarts, and durable restore evidence.
- Verify collection completeness, unknown/stale/gap behavior, privacy and source trust in a representative target environment.

`reclaim_expired_components` remains a confirmation-gated Development-only in-memory library operation, not durable recovery. **No merge, deployment, independent human approval, or production qualification is claimed.**
