# GoreeCloud Observability — Specifications

## Scope

The Development foundation normalizes bounded operational signals and derives attributable component-health state. It does not replace the domain interpretation performed by Privacy Shield, Wardveil Security, GoreeCloud Identity, Everkeep, GoreeCloud Policy, GoreeCloud Mesh, or GoreeCloud Manager.

## Operational signal

A signal identifies component, source, signal type, health state, observation time, collection time, freshness TTL, optional correlation ID, minimized attributes, and known collection gaps.

## Health-state integrity

- No signals => `unknown`.
- Signals present but none fresh => `stale`.
- Fresh failure/unavailability outranks lower-severity fresh states.
- Fresh `unknown`, `not_monitored`, or `partially_observed` evidence prevents a healthy result.
- `not_applicable` is returned only when all current applicable evidence is explicitly not applicable.
- The aggregate retains contributing signal IDs/sources and collection gaps.

## Privacy and security

Telemetry attributes are bounded and reject obvious secret-bearing keys such as password, token, secret, authorization, cookie, private key, and API key. This is a defensive baseline, not a substitute for Privacy Shield/Wardveil review.

## Runtime

The local Development runtime provides:
- `GET /healthz`
- `GET /readyz`
- `POST /v1/signals`
- `GET /v1/components/{component_id}/health`

The reference runtime is in-memory, loopback-only, and not production accepted.
