# Robinhood private program dashboard

This application is a human-facing visualization of
[`../status.yaml`](../status.yaml). The YAML ledger is the sole current
machine-readable authority. The dashboard must never become an independently
maintained status source. Repository documents are the durable handoff and
fallback.

Current configuration-source subject:
`e4473ce6485888f1b747761a5ee8693443108877`, tree
`33b705690007bda9b11900b5775bd9230e79f09e`.

Ready to begin deployment preparation. PR #61 is merged and closed, and its
production contract changes are integrated into `rh`. H-04 schema v2, H-05
deterministic blocked planning, M4 proof, and H-06 candidate-class
qualification are integrated for their exact scopes. No Robinhood migration,
deployment, production configuration, activation, RPC, account, key, signer,
or release action has occurred.

Morpho V2 and BlueChipYield support are integrated. BlueChipYield is selected
at PriceDesk slot 3; `DefaultsRobinhood.vy` exists and compiles, and the
derived ledger is synchronized. `configuration_consistent=true`,
`deployment_ready=false`, and the current blocker count is 58. Repository
configuration is prepared and consistent; production/onchain configuration
has not occurred.

`fullPayoffBuffer`, `overageBps`, `dustThreshold`, and `dustBps` remain zero,
deferred, and absent from machine-facing Robinhood parameter/planning sources.
The deployment owner owns final disposition and binding; the gap is not fixed
here.

[`../deployment-owner-quickstart.md`](../deployment-owner-quickstart.md) is the
sole canonical human deployment handoff. `START-HERE.md` is a router, and the
legacy handoff/readiness paths are compatibility redirects.

## Authority and generated files

Run the status synchronization script before local development, tests, or a
production build. It parses `status.yaml`, verifies the RH-D mirror against
[`../decision-register.md`](../decision-register.md), derives Git and source
identities, and generates:

- `app/status.generated.json`; and
- `app/handoff/[slug]/handoff.generated.json`.

Those generated files are validation output only. They are ignored and
untracked; do not edit, stage, or commit them. `status.yaml` and the referenced
Markdown documents are the source. The generator classifies an uncommitted
candidate, committed feature, exact integrated `rh` authority, and later
integrated descendant from Git; none of those identities is manually
hardcoded.

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
source commit and separate authority. Sites account/workspace recovery and
dashboard deployment are parked. This refresh does not create or recover a
project, save a version, deploy, publish, or change access. Do not claim
authenticated owner access unless it is verified under existing credentials.

The current owner priorities are in
[`../current-owner-priorities.md`](../current-owner-priorities.md): CCIP,
zero-backing settlement/bad-debt policy, Sites recovery, and dashboard
deployment are the four parked, nonblocking lanes.
