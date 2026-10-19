# GoreeCloud Observability

GoreeCloud Observability is the platform-wide operational-health, telemetry, diagnostics, performance, and operational-evidence foundation for GoreeCloud.

**Lifecycle:** Development  
**Foundation version:** `0.1.0-dev`  
**Platform Contract:** `0.4`  
**License:** `AGPL-3.0-or-later`

This repository now contains a bounded reference implementation for operational-signal normalization and component health aggregation. It is intentionally **not** a production monitoring deployment or proof that any GoreeCloud component is monitored.

## Current source capabilities

- Canonical states: `healthy`, `degraded`, `failed`, `unavailable`, `unknown`, `stale`, `partially_observed`, `not_monitored`, `not_applicable`.
- Signal provenance, observation/collection timestamps, TTL freshness, correlation context, and collection-gap preservation.
- Missing evidence => `unknown`; stale-only evidence => `stale`; neither is converted to healthy.
- Obvious secret-bearing telemetry attribute names are rejected.
- Local-only Development HTTP runtime with `/healthz`, `/readyz`, signal ingestion, and component-health query.
- Contract 0.4 declaration covering all nine Integral Platform Systems.
- Standard-library tests and CI.

## GoreeCloud UI Integral Platform System status

**GoreeCloud UI (GC UI)** is GoreeCloud's fifth Integral Platform System (of nine) and permanently replaces Glaze and Glaze UI. The current Observability reference collector has no GUI; a future dashboard or administrator interface must use GC UI and satisfy real conformance evidence.

A separate [GC UI Platform Contract 2.1 candidate](docs/GC_UI_CONTRACT_2_1_CANDIDATE.md) and pinned CI evaluate this **headless non-applicability** without changing the canonical Contract 0.4 manifest or claiming a lifecycle promotion, runtime migration or production monitoring acceptance.

## Run locally

```bash
python -m goreecloud_observability
```

The reference runtime binds to `127.0.0.1:8790` by default and refuses non-loopback binding.

## Test

```bash
python -m unittest discover -s tests -v
```

## License

GoreeCloud Observability is licensed under `AGPL-3.0-or-later`. See `LICENSE`.

See `SPECIFICATIONS.md`, `IMPLEMENTED-FEATURES.md`, `PLANNED-FEATURES.md`, and `goreecloud.platform.yaml` for the evidence boundary.

Tracking: #1
