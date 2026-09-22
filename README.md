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
