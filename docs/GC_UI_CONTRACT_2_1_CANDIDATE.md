# Observability — GC UI Platform Contract 2.1 candidate

**Status:** Non-authoritative **shadow declaration** and independently pinned source-level CI only, October 19, 2026. The original `goreecloud.platform.yaml` (Contract 0.4), development runtime, API behavior, deployment and production-acceptance status are unchanged.

GoreeCloud UI is **Integral Platform System #5 of nine**, permanently replacing Glaze and Glaze UI. The present Observability reference collector is **headless**: it has no owned dashboard, app, public website or admin interface, so the candidate records `platform_systems.gc_ui: not-applicable-justified` with the current README as evidence. If an interface is introduced, GC UI becomes applicable and must be validated using real design, browser/native, accessibility and deployment evidence; the headless exception cannot be carried forward automatically.

The [2.1 candidate](../goreecloud.platform.v2.1.candidate.yaml) preserves all seven currently blocked external platform integrations, explicitly separates Observability's own authority, keeps `status: nonconformant`, and contains no acceptance tests or release evidence. The `lab` lifecycle and `next_gate: forge` fields are **conservative schema-testing placeholders**, not approved lifecycle reclassification from Contract 0.4 Development.

The [opt-in CI](../.github/workflows/gc-ui-contract-2-1.yml) calls the independently versioned [GoreeCloud Platform Contract 2.1](https://github.com/GoreeCloud/GoreeCloud/blob/1499491159250d5f15dad4e2835fbeee2fda9ce9/.github/workflows/reusable-platform-manifest-v2-1.yml) using an immutable evaluated implementation revision. It verifies the exact PR head and candidate result, uploads bounded source evidence, and **may pass while reporting nonconformant**. The older 0.4 workflow remains separately pinned and unchanged.

Before an authoritative manifest cutover or any Anchor qualification: reconcile canonical GoreeCloud Drive governance Markdown in place; receive owner-approved lifecycle transition evidence; validate target runtime, trusted producer identity, privacy/retention, authorized telemetry, recovery, source and deployment/security acceptance; qualify GC UI only if the system introduces an actual interface. No source-only CI check proves deployed Observability services, downstream consumer adoption or complete GC UI migration.

Track this activity with [GC UI cutover issue #13](https://github.com/GoreeCloud/gc-ui/issues/13).
