# Robinhood deployment: start here

**Currentness date:** 30 July 2026
**Frozen protocol/pause authority:** `rh` at
`ae0cb49bad9ad615deb11cbca5d3a2c20e38bb4c`
**Protocol tree:** `a6a34a385b48819bbf66249d518d76da3806b033`
**Sole current machine authority:** [`status.yaml`](status.yaml)
**Private presentation mirror:** [Robinhood program status](https://ripe-robinhood-status.mickhagen.chatgpt.site)

Agents should pair this page with
[`deployment-owner-readiness.md`](deployment-owner-readiness.md) and
[`AGENT-HANDOFF.md`](AGENT-HANDOFF.md).
The dashboard is generated from `status.yaml`; it is not a second status
source. Repository documents remain the complete durable fallback.

## Bottom line

**Ready to begin deployment preparation.** PR #61 is merged and closed on
`master`; its production contract changes are integrated into `rh`. Nothing is
deployed, configured, or active. No Robinhood migration has been executed, and
no production configuration, activation, RPC, account, key, or signer action
exists.

The frozen protocol/pause baseline is `ae0cb49…`. The documentation-only
handoff commit is a descendant whose authority is derived by the dashboard
generator. Its publication does not integrate it into `rh`, and a later
integrated `rh` tip or descendant requires independent reconciliation.

The current ledger contains:

- 28 workstreams;
- 19 RH-D decisions;
- 18 open H-03 blockers;
- 21 H-04 rows: 20 approved and operative, one retired and non-operative
  (`D-H04-19`), zero open;
- 14 binding schedules;
- nine hard gates;
- ten dashboard handoff documents;
- four parked lanes; and
- zero live actions.

## What is integrated

- Corrected PR #61: shared Deleverage, AuctionHouse, SwitchboardDelta,
  artifacts, inventory, ABIs, and tests. The import ancestor is
  `ad831669…`; the current frozen baseline is `ae0cb49…`.
- H-04 schema v2: typed parameter manifest, fail-closed generator, tests, and
  evidence.
- H-05: deterministic, import-free predeployment planning and sealed blocked
  reports. This is planning, not migration execution.
- H-06: a candidate macOS/APFS operator/storage class. This is not a final
  operator, machine, volume, deployment, or release authorization.
- M1-M4 Stock containment and composed-route proof.

## The four-control machine gap

`fullPayoffBuffer`, `overageBps`, `dustThreshold`, and `dustBps` remain zero
and deferred. The integrated contracts expose them, but Robinhood's
machine-facing parameter and planning sources do not represent them. That gap
belongs to the deployment owner, but machine implementation still requires
separate authority. This documentation refresh does not fix it.

Required identities, `TrainingWheels`, and `liteSigners` also remain unresolved.
`DefaultsRobinhood.vy` is therefore absent and the generator remains
fail-closed. Do not substitute Base values, zero addresses, or placeholders.

## Decisions that remain closed or deferred

- The historical S4 `deleverageCooldown == 0` decision remains closed and was
  not reopened by PR #61.
- CCIP is deferred indefinitely, disabled, and nonblocking.
- Zero-backing settlement and bad-debt policy are deferred and nonblocking.
- Sites account/workspace recovery is parked and nonblocking.
- Dashboard deployment and access changes are parked and nonblocking.
- Parking does not declare a technical residual safe, resolved, or approved.

## Deployment-owner sequence

The complete ten-step ownership map is in
[`deployment-owner-readiness.md`](deployment-owner-readiness.md). In short:
bind final protocol inputs and authorities; dispose and represent the four
zero-valued controls; generate Defaults only from complete approved inputs;
finalize deterministic planning; bind H-06; freeze artifacts and offline
verification; rehearse under later testnet authority; complete SecOps; and
assemble the restricted-release packet and signer ceremony.

Smart-contract reassessment and Robinhood fork/external-integration
qualification do not block preparation from starting. Relevant findings must
be consumed before affected gates close. Testnet, production, configuration,
activation, and release each require separate authority.

## Current checked inventory

The direct block-clock checker binds 99 production occurrences across 94 lines
and 17 files. It preserves historical S5 fingerprint
`924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4`
and current post-S5 fingerprint
`07fc837ee5c9c56a4cf979c64e3d678753eeb6c263e4100d7a1f0cb4704f2122`.
The direct contract-artifact checker covers eight production contracts,
including Deleverage's 24,569-byte runtime with seven bytes of EIP-170
headroom.

## Read next

- [`deployment-owner-readiness.md`](deployment-owner-readiness.md) for the
  ordered ownership map and exact boundary.
- [`current-owner-priorities.md`](current-owner-priorities.md) for active and
  parked work.
- [`decision-register.md`](decision-register.md) for the 19 canonical RH-D
  decisions.
- [`../rh-summary.md`](../rh-summary.md) for stable architecture and the launch
  checklist.
- [`smart-contract-changes/README.md`](smart-contract-changes/README.md) for
  source-bound contract rationale.
- [`robinhood-deployment-support-specification.md`](robinhood-deployment-support-specification.md)
  and [`robinhood-deployment-validation-plan.md`](robinhood-deployment-validation-plan.md)
  for predeployment sequencing and validation.
