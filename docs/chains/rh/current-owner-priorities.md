# Robinhood current owner priorities

**Effective:** 31 July 2026

**Authority:** explicit owner directive

**Scope:** current prioritization, blocker treatment, and agent assignments

This document is a current-priority overlay. It does not rewrite historical
evidence, change integrated smart-contract bytes, close a technical blocker, or
authorize deployment, configuration, activation, or release.

## Active focus

Ready to begin deployment preparation from current configuration-source
baseline `e4473ce6485888f1b747761a5ee8693443108877`, tree
`33b705690007bda9b11900b5775bd9230e79f09e`. The earlier `ae0cb49…`
protocol/pause baseline and corrected PR #61 import ancestor `ad831669…` remain
historical evidence, not present branch authority. The deployment owner may
now advance:

- unresolved non-Deleverage external verification and deployment-produced
  bindings, while preserving configuration consistency;
- H-05 release-candidate planning readiness without migration execution;
- final H-06 operator machine/volume binding; and
- remaining predeployment infrastructure, qualification, rehearsal, SecOps,
  release-packet, rollback/abort, and signer-ceremony preparation.

H-04 source authority and H-05 blocked planning are integrated; M4 proof is
integrated. `DefaultsRobinhood.vy` exists, compiles, and is synchronized with
the derived ledger. The generator reports `configuration_consistent=true`,
`deployment_ready=false`, and 58 blockers. Repository configuration is
prepared and consistent; production/onchain configuration has not occurred.
No deployment, migration execution or history, activation, or release has
occurred. The smart-contract reassessment and
Robinhood fork/external-integration reports are consolidated in
[`reassessment-and-qualification-synthesis.md`](reassessment-and-qualification-synthesis.md);
affected gates must consume that synthesis.

The sole canonical deployment-owner handoff is
[`deployment-owner-quickstart.md`](deployment-owner-quickstart.md).

## Accepted synthesis posture

- Preserve the current Ledger and Teller contracts and their reviewed
  measurement/clock boundaries.
- Keep GuardedErc20 separate and Stock-specific.
- Launch Profile 1 with Chainlink at PriceDesk slot 1 and BlueChipYield at slot
  3, no Uniswap launch price source, no Curve registration, and neither LP
  token admitted. Priority source IDs remain `[1, 3]`.
- Treat RIPE/WETH V2 only as an optional externally held liquidity canary.
- Move GREEN/USDG and both LP admissions to Profile 2.
- Keep the PSM disabled, allowlisted, canary-first, and redemption-first until
  separately activated.
- Keep H-09 network-disabled by default with explicit opt-in read-only
  archive-fork qualification; H-10 owns live rehearsal.

Future work is grouped into the synthesis's large Packages A-F. Do not split
the eight reports into separate implementation trains.

## Parked lanes

### 1. All CCIP workflows are parked

CCIP is disabled and outside the current work queue.

- Do not perform CCIP research, implementation, review, external coordination,
  production packaging, testing, testnet work, deployment, promotion, or
  current-status investigation.
- Do not treat historical CCIP gaps as blockers for current non-CCIP work.
- Preserve historical CCIP documents and examples as technical records; do not
  rewrite them to imply that their risks or gates were resolved.
- Reopen CCIP only after an explicit owner instruction.

### 2. CreditEngine zero-backing reassessment and policy are parked

The integrated M2/M3 source and regression behavior remain unchanged.

- Do not reassess CreditEngine zero backing or design, remediate, review, or
  schedule zero-backing settlement or bad-debt policy work.
- Do not treat that policy lane as a blocker for current parameter, planning,
  tooling, documentation, or bounded non-policy proof work.
- Parking does not declare any residual safe, resolved, approved, or closed.
  It does not authorize Stock configuration, reachability, activation,
  deployment, or release.
- Reopen the reassessment/policy lane only after an explicit owner instruction.

### 3. Every Deleverage task is parked

Preserve the historical S4 zero-cooldown decision, integrated PR #61 bytes, and
the four zero-valued controls.

- Do not perform Deleverage contract, interface, ABI, parameter, configuration,
  test, fork, documentation, size/headroom, deployment, or operational work.
- Do not create a machine-facing representation task for
  `fullPayoffBuffer`, `overageBps`, `dustThreshold`, or `dustBps`.
- The provisional H-09 census path for Deleverage must not be implemented or
  executed unless this lane is explicitly reopened and the H-09 ceiling is
  resealed.
- Reopen only through explicit owner instruction.

### 4. Uniswap TWAP admission and activation are parked

The archival `RobinhoodUniswapV2RipePrices` research/monitoring prototype
source is present in the repository. It is not registered, configured,
admitted, deployed, or activated and is unavailable for protocol accounting.
No Uniswap launch price source is required; Profile 1 behavior and PriceDesk
priority source IDs `[1, 3]` remain unchanged.

- Do not add a checkpoint service, PriceDesk registration, Chainlink fallback,
  pool address, liquidity amount, funding or custody authority, migration,
  deployment-plan dependency, configuration, admission, deployment, or
  activation.
- An optional externally held RIPE/WETH V2 liquidity canary is operational
  preparation, not protocol oracle authority.
- Reopen work beyond archival prototype maintenance only after an approved
  security-relevant RIPE-price consumer and separate owner, risk, security,
  custody, and exposure decisions exist.

### 5. Sites account/workspace recovery is parked

Retain the known Sites project provenance and prior account/workspace mismatch
evidence.

- Do not recover access, create a replacement project, or change access.
- Do not treat Sites recovery as a deployment-preparation blocker.
- Reopen only through explicit owner instruction from the owning account or
  workspace.

### 6. Dashboard deployment is parked

The dashboard remains local-only in this handoff.

- Do not create or save a Sites version.
- Do not deploy, publish, or change dashboard access.
- Local rendering and validation do not authorize a dashboard deployment.

## Blocker interpretation

Historical blocker identifiers and technical evidence remain intact so future
work can re-enter with full provenance. A blocker can therefore remain
historically open while being `parked_nonblocking` for the current program.
That state means:

- no work is assigned to close it;
- no current non-parked task waits on it;
- it is not represented as technically resolved; and
- an explicit owner instruction is required before work resumes.

Ordinary baseline reconciliation still applies after a future change is
integrated into `rh`. PR #61 is merged and closed at head `7293cf87…` and
`master` squash merge `91eda49…`; its production contract changes are already
integrated into `rh`.

## Non-authorization

This directive authorizes deployment preparation within its separately
controlled implementation lanes. It does not authorize production-contract
edits, testnet or production actions, RPC or
account access, signer selection, signing, broadcasting, migration execution,
deployment, configuration, registration, activation, or release.
