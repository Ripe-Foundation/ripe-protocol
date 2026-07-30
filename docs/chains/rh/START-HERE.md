# Robinhood deployment: start here

**Currentness date:** 30 July 2026  
**Protocol authority:** `rh` at
`ad831669943ccfe7b9ed57454995dfce51630a66`  
**Protocol tree:** `3467f4a75aa37203d615407d5baf9c5fc9035639`  
**Sole current machine authority:** [`status.yaml`](status.yaml)  
**Private presentation mirror:** [Robinhood program status](https://ripe-robinhood-status.mickhagen.chatgpt.site)

Agents should pair this page with [`AGENT-HANDOFF.md`](AGENT-HANDOFF.md).
The dashboard is generated from `status.yaml`; it is not a second status
source. Repository documents remain the complete durable fallback.

## Bottom line

**Corrected PR #61 is integrated into `rh`, but nothing is deployed or
active.** Upstream PR #61 remains independently open and unmerged as of the
fresh live check. No Robinhood migration history, migration execution,
production configuration, activation, or release exists.

The current ledger contains:

- 28 workstreams;
- 19 RH-D decisions;
- 18 open H-03 blockers;
- 21 H-04 rows: 20 approved and operative, one retired and non-operative
  (`D-H04-19`), zero open;
- 14 binding schedules;
- nine hard gates;
- nine dashboard handoff documents;
- two parked lanes; and
- zero live actions.

## What is integrated

- Corrected PR #61: shared Deleverage, AuctionHouse, SwitchboardDelta,
  artifacts, inventory, migrations, ABIs, and tests.
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
must be handled by a separately authorized future implementation track. This
documentation refresh does not fix it.

Required identities, `TrainingWheels`, and `liteSigners` also remain unresolved.
`DefaultsRobinhood.vy` is therefore absent and the generator remains
fail-closed. Do not substitute Base values, zero addresses, or placeholders.

## Decisions that remain closed or deferred

- The historical S4 `deleverageCooldown == 0` decision remains closed and was
  not reopened by PR #61.
- CCIP is deferred indefinitely, disabled, and nonblocking.
- Zero-backing settlement and bad-debt policy are deferred and nonblocking.
- Parking does not declare a technical residual safe, resolved, or approved.

## Current critical path

1. Bind unresolved identities and separately authorize machine-facing
   representation for the four Deleverage controls.
2. Render and verify `DefaultsRobinhood.vy` only after every required binding
   exists.
3. Rebuild deterministic H-05 reports for release-candidate readiness; retain
   typed blocked/non-executable rows and do not execute migrations.
4. Bind H-06 to the final operator machine, selected volume, and frozen release
   candidate.
5. Complete H-07 artifact readiness, M5 disabled configuration, H-08/H-09
   proof, SecOps, rehearsal, and release preparation.

Actual deployment remains outside the pause process. Testnet, production,
configuration, activation, and release each require separate authority.

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
