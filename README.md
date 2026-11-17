# livespec-runtime

Built with [livespec](https://livespec-ai.org/)

Shared runtime library for livespec-governed projects.

Hosts runtime code consumed by canonical [`livespec`](https://github.com/livespec-ai/livespec) skills, impl-plugin skills, doctor invariants, hooks, and CI workflows. Its first module was `livespec_runtime.cross_repo` (cross-repo work-item dependency resolution per `livespec/SPECIFICATION/contracts.md` §"Cross-repo dependency awareness"); the package now also carries `github_auth`, `github_budget`, `hygiene_scan`, `needs_attention`, `spec_governance` and `work_items`.

This library is NOT enforcement-suite code — those live in [`livespec-dev-tooling`](https://github.com/livespec-ai/livespec-dev-tooling). The split is intentional: enforcement-suite is build-time tooling consumed via `[dependency-groups].dev`; runtime is invoked at sub-command execution time and consumed via `[project.dependencies]` or `[dependency-groups].dev` depending on the consumer.

## Status

**v0.32.0 — cross_repo resolution surface shipped.** <!-- x-release-please-version --> `livespec_runtime.cross_repo` is fully implemented: typed `DependsOnEntry` union, `providers.github`, `retry`, and `resolve_ref` have all landed. The module is present and in active use by livespec consumers. See [`CHANGELOG.md`](CHANGELOG.md) for the per-release history.

## Consumption

Consumers add this library via `uv` git source:

```toml
[dependency-groups]
dev = [
    "livespec-runtime",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/livespec-ai/livespec-runtime.git", tag = "v0.32.0" } # x-release-please-version
```

Or as a runtime dependency:

```toml
[project]
dependencies = [
    "livespec-runtime>=0.32.0", # x-release-please-version
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/livespec-ai/livespec-runtime.git", tag = "v0.32.0" } # x-release-please-version
```

## Governance

- The `SPECIFICATION/` tree at the repo root is the live spec for this library, governed by livespec via its own seeded template (seeded under epic `li-6d2wpj`; later revisions accrete under `SPECIFICATION/history/`).
- This library's own impl tracking lives in a per-repo beads/Dolt **tenant database** on the shared dolt-server (tenant `livespec-runtime`), via [`livespec-orchestrator-beads-fabro`](https://github.com/livespec-ai/livespec-orchestrator-beads-fabro); the beads client config is committed at `.beads/config.yaml`. The pre-cutover plaintext `work-items.jsonl` / `memos.jsonl` snapshot is frozen read-only under [`archive/`](archive/README.md).
- The `compat` block on the `livespec-runtime` top-level key in `.livespec.jsonc` pins this library's compatibility with `livespec-core` per the pin-and-bump contract.

## Observability

The livespec family dogfoods its own telemetry. CI runs, Red→Green commit-gate cycles, the beads+fabro dispatcher, sandbox runs, and harness sub-agents are published to a shared Honeycomb environment:

- **[livespec family — all activity](https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/krThv8DvcwS)** — the cross-repo activity board (Honeycomb, `livespec` environment).

## Merging

Pull requests land on master through the livespec-ai merge queue (ruleset master-incident-recovery-bypass); ci-green is the required check.
