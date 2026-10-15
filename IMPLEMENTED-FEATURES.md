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

Second-pass solo-maintainer audit: OperationalSignal ingestion rejects contradictory event timestamps when collected_at precedes observed_at. Equal timestamps remain valid; synthetic unit and HTTP negative-path tests verify fail-closed behavior. No production authenticated telemetry is asserted.

Solo-maintainer audit: deeply nested JSON is rejected with HTTP 400, and collection times before observations are rejected. Development-only behavior; no live telemetry authority claimed.

Operational evidence is not fresh until its declared collection time; this is tested with synthetic signals. The CI workflow verifies the exact checked-out source commit before running tests.

### Development HTTP request boundary — 2026-10-15

Local-only ingestion rejects nonloopback Host aliases, browser Origin POSTs, and non-JSON media types; attribute filtering also rejects compact credential names such as apikey, passwordHash, and privatekey. These source safeguards do not establish producer authentication or production telemetry privacy.

### Concurrent stabilization audit — 2026-10-15

Development telemetry JSON responses now include Cache-Control: no-store and X-Content-Type-Options: nosniff, verified through local HTTP tests. Sensitive attribute matching also blocks concatenated credential aliases.

### Source-stabilization checkpoint — 2026-10-15

Loopback HTTP ingestion rejects ambiguous framing and cross-site browser metadata. The in-memory store adds explicit confirmation-gated expired-component reclamation for Development recovery only; it preserves current and future-collected evidence, never evicts silently and provides no network reclamation endpoint. No durable telemetry recovery is asserted.

### Development-to-production status boundary — 2026-10-15

Development Observability `/healthz` includes `production_accepted: false` in addition to its development scope. API health must not be mistaken for authenticated telemetry sources, retention or production monitoring acceptance.
