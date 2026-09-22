# Implemented Features

These entries describe source implementation only and do not imply release, deployment, monitoring coverage, production, certification, or Stable acceptance.

## OBS-FOUNDATION-001 — Health vocabulary

Implemented explicit healthy/degraded/failed/unavailable/unknown/stale/partially-observed/not-monitored/not-applicable states.

## OBS-FOUNDATION-002 — Signal model and freshness

Implemented provenance-bearing signals with observation/collection time, TTL freshness, correlation context, minimized attributes, and collection gaps.

## OBS-FOUNDATION-003 — Integrity-preserving aggregation

Implemented missing => unknown, stale-only => stale, and severity-aware fresh aggregation so missing/unknown evidence cannot become healthy.

## OBS-FOUNDATION-004 — Development runtime and CI

Implemented local-only ingestion/query/health endpoints, Contract 0.4 declaration, unit tests, and CI.
