# Robinhood private program dashboard

This application is a human-facing visualization of
[`../status.yaml`](../status.yaml). The YAML ledger is the sole current
machine-readable authority. The dashboard must never become an independently
maintained status source. Repository documents are the durable handoff and
fallback.

Current program subject:
`ad831669943ccfe7b9ed57454995dfce51630a66`, tree
`3467f4a75aa37203d615407d5baf9c5fc9035639`.

Corrected PR #61 is integrated; upstream PR #61 remains independently open and
unmerged as of the fresh live check. H-04 schema v2, H-05 deterministic blocked
planning, M4 proof, and H-06 candidate-class qualification are integrated for
their exact scopes. No Robinhood migration history, deployment, migration
execution, production configuration, activation, or release exists.

`fullPayoffBuffer`, `overageBps`, `dustThreshold`, and `dustBps` remain zero,
deferred, and absent from machine-facing Robinhood parameter/planning sources.
That gap is not fixed here. `DefaultsRobinhood.vy` remains absent and
fail-closed. Actual deployment is outside the pause process.

## Authority and generated files

Run the status synchronization script before local development, tests, or a
production build. It parses `status.yaml`, verifies the RH-D mirror against
[`../decision-register.md`](../decision-register.md), derives Git and source
identities, and generates:

- `app/status.generated.json`; and
- `app/handoff/[slug]/handoff.generated.json`.

Those generated files are validation output only. They are ignored and
untracked; do not edit, stage, or commit them. `status.yaml` and the referenced
Markdown documents are the source.

The page and authorized integrity tests must derive current subjects, counts,
H-04 lifecycle, hard gates, parked lanes, handoff counts, and fingerprints from
the current authority or source files. Do not duplicate current literals in
presentation code.

## Local validation

The package scripts provide deterministic status synchronization, production
build, Node integrity tests, and lint. The build must remain compatible with
the existing Vinext/Sites application structure and exact dependency lockfile.
Dependency versions are documentation tooling outside the H-01 launch
toolchain scope and are not changed by this refresh.

Browser review covers desktop and 375px mobile layouts, keyboard traversal,
heading hierarchy, landmarks, visible focus, contrast, accessibility, and the
application console. These checks validate presentation only; they do not
attest protocol readiness.

## Hosting boundary

[`./.openai/hosting.json`](.openai/hosting.json) retains project ID
`appgprj_6a66dcdcb9288191bc8eeef24335bb1c`. The dashboard is an optional
private explicit-allowlist mirror. Publication requires an exact validated
source commit and separate authority. This refresh does not create a project,
save a version, deploy, or change access. Do not claim authenticated owner
access unless it is verified under existing credentials.

The current owner priorities are in
[`../current-owner-priorities.md`](../current-owner-priorities.md): CCIP and
zero-backing settlement/bad-debt policy are the two parked, nonblocking lanes.
