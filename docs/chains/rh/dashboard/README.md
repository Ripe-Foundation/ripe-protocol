# Robinhood private program dashboard

This application is a human-facing visualization of
[`../status.yaml`](../status.yaml). The YAML ledger is the sole current
machine-readable authority. The dashboard must never become an independently
maintained status source. Repository documents are the durable handoff and
fallback.

Current live `rh` parent:
`0372d48680c281ddaafe2f1982f0bcfa851071c9`, tree
`79fdc69de22eb8cfa2be3a2067c596d5fed92963`. Draft PR #73 contains production-
remediation source candidate `e12b1abe26218acb804d84670099c41169e5f515`,
tree `b680f0016f29f9a217054db9f80c0bbf9f0b9916`, followed only by the current
status-authority reconciliation. Rebind the production-source identity after
any production/configuration change.

Ready to begin deployment preparation. PR #61 is merged and closed, and its
production contract changes are integrated into `rh`. The current candidate
uses eight imperative Robinhood migration files. H-05 is deterministic
repository review only: no executable plan is authorized or censused, and the
retired declarative runner, transaction executor, and 86-key plan census are
not current authority. H-06 qualifies an operator/storage class only. No
Robinhood migration, deployment, production configuration, activation, RPC,
account, key, signer, or release action has occurred.

The bounded candidate selects Chainlink at PriceDesk ID 1 and unchanged
CurvePrices for GREEN only at ID 2; priorities are `[1,2]`. BlueChipYield
remains structurally selected at ID 3 in the blueprint but is not deployed or
finalized by the current migration candidate. IDs 4/5 remain empty, USDG has
no Curve feed, and neither LP token nor any Curve higher power is admitted.
`DefaultsRobinhood.vy` exists and compiles, and the derived ledger is
synchronized. `configuration_consistent=true`, `deployment_ready=false`, 28
canonical H-03 blockers remain open, and the current deployment-readiness
blocker count is 65. Repository configuration is prepared and consistent;
production/onchain configuration has not occurred.

Current source assigns `1,000,000e18` RIPE to rewards, zero to HR, and
`1,000,000e18` RIPE to bonds. `B-REWARD-PROMOTION` remains operationally open
and Stock rewards remain disabled. The GREEN/USDG pricing pool selection does not admit its LP token;
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
zero-backing settlement/bad-debt policy, Deleverage, UniswapV2Prices admission and deployment, Sites
recovery, and dashboard deployment are the six parked, nonblocking lanes.
