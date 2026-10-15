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

Development in-memory collector capacity is bounded to 1,024 component identities and 256 signals per component by default. Additional identities are rejected without evicting other components; a 503 capacity response does not imply durable recovery, production acceptance, or a monitoring deployment. Ingest and read snapshots use a shared lock to prevent concurrent iteration errors.

Development telemetry attribute validation rejects credential-bearing field names even when prefixed, suffixed, camel-cased, or separator-delimited (for example synthetic db_password and oauthToken keys), while preserving ordinary operational attributes. This remains a best-effort source guard and is not a substitute for trusted producer, privacy-policy, or production telemetry acceptance.

Development signal parsing enforces a 256-character ceiling on identifiers, source and correlation fields, bounds collection gaps to 32 entries with 256 characters each, requires a genuine integer TTL (not a boolean), and restricts telemetry attribute values to finite JSON scalars. This limits input ambiguity and memory amplification but is not a complete retention or producer-trust policy.

Development telemetry enforces a 256-character ceiling on signal/component/source/correlation identifiers, collection gaps of at most 32 entries of 256 characters, integer-only TTL, and finite JSON-scalar attributes. These resource and serialization guards are not producer authentication or a complete privacy/retention policy.

Development parser rejects non-finite floating-point results from JSON exponent parsing. This closes the parser-level overflow ambiguity without establishing authenticated telemetry producers or production safety.

Development health aggregation treats healthy signals containing collection gaps as partially observed instead of fully healthy. Existing failed/degraded evidence retains severity priority. This is a source-only rule and not live monitoring coverage.
