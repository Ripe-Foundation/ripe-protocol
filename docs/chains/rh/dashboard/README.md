# Robinhood private program dashboard

This application is a human-facing visualization of
[`../status.yaml`](../status.yaml). The YAML ledger is the sole current
machine-readable authority. The dashboard must never become an independently
maintained status source. Repository documents are the durable handoff and
fallback.

Current candidate baseline:
`5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree
`7454b5456ebb6cd02d716a64b408629ab501629e`.

Ready to begin deployment preparation. PR #61 is merged and closed, and its
production contract changes are integrated into `rh`. H-04 schema v2, H-05
deterministic blocked planning, M4 proof, and H-06 candidate-class
qualification are integrated for their exact scopes. No Robinhood migration,
deployment, production configuration, activation, RPC, account, key, signer,
or release action has occurred.

Morpho V2 and BlueChipYield support are integrated. The bounded candidate
selects Chainlink at PriceDesk ID 1, unchanged CurvePrices for GREEN only at
ID 2, and BlueChipYield at ID 3; IDs 4/5 remain empty and priorities remain
`[1,3]`. USDG has no Curve feed and neither LP token nor any Curve higher
power is admitted. `DefaultsRobinhood.vy` exists and compiles, and the derived
ledger is synchronized. `configuration_consistent=true`,
`deployment_ready=false`, and the current blocker count is 80. Repository
configuration is prepared and consistent; production/onchain configuration
has not occurred.

DP15 and P-H04-399 retain the approved general reward values, while
`B-REWARD-PROMOTION` remains operationally open and Stock rewards remain
disabled. The GREEN/USDG pricing pool selection does not admit its LP token;
RIPE/WETH remains external-canary-only, Uniswap remains PriceDesk-inert, and
PSM reserves cannot fund LP liquidity.

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
zero-backing settlement/bad-debt policy, Deleverage, Uniswap TWAP, Sites
recovery, and dashboard deployment are the six parked, nonblocking lanes.
