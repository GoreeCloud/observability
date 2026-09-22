# GoreeCloud Observability — User Manual

This Development foundation is intended for developers and platform integrators.

## Start

```bash
python -m goreecloud_observability
```

## Health

`GET /healthz` reports the reference process health. `GET /readyz` reports Development-runtime readiness. Neither establishes estate monitoring coverage.

## Submit a signal

Send a JSON operational signal to `POST /v1/signals`. See `contracts/operational-signal.schema.json`.

## Query component health

`GET /v1/components/{component_id}/health` returns the current in-memory aggregate.

Do not submit credentials, secrets, raw user content, or unnecessary personal information as telemetry attributes.
