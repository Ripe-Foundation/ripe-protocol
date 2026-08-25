# Ripe Reserve Engine

The Ripe Reserve Engine accepts an approved payment token and allocates newly
issued RIPE under a configurable vesting schedule. Payment is collected at
acquisition, while RIPE is minted only when vested RIPE is successfully claimed.

This document describes the implementation in PR #156. Older proposal and design
review files in this directory are historical evidence, not the current contract
specification.

## Contracts and registry slots

- [`RipeReserveEngine.vy`](../../contracts/core/RipeReserveEngine.vy) is registry
  slot 26 (`RIPE_RESERVE_ENGINE_ID`).
- [`RipeReserveVesting.vy`](../../contracts/core/RipeReserveVesting.vy) is registry
  slot 27 (`RIPE_RESERVE_VESTING_ID`).
- [`SwitchboardFoxtrot.vy`](../../contracts/config/SwitchboardFoxtrot.vy) provides
  the named governance surface.
- [`Addys.vy`](../../contracts/modules/Addys.vy) resolves both addresses through
  RipeHQ.

The Engine also resolves the live Vesting and RIPE token addresses through
RipeHQ. It does not pin either address. Before replacing Vesting while positions
are outstanding, governance must migrate those positions or wait until
`canRetire()` is true. `canRetire()` requires Vesting to be paused with no
outstanding RIPE allocation.

## Acquisition

`previewAcquireRipe(paymentAmount, requestedVestingLength)` returns a
`ReserveEngineQuote`. A successful acquisition calls:

```text
acquireRipe(
    paymentAmount,
    requestedVestingLength,
    expectedVestingLength,
    expectedEpoch,
    minRipeOut,
    deadlineBlock,
)
```

The expected vesting length, expected epoch, minimum RIPE allocation, and deadline
protect the caller from state changes between preview and execution. Acquisitions
are full-fill only. The Engine verifies the exact payment-token balance increase,
so fee-on-transfer, short-receipt, false-return, and reentrant settlement cannot
create an allocation.

The quote includes base and bonus RIPE, vesting duration, creation block,
claim-start block, maturity block, and epoch rate information. The stable
`positionId` is created only during execution and is emitted by `RipeAllocated`.

## Allocation budget

Vesting stores one global `remainingAllocationBudget`. Creating a position:

- requires the full base-plus-bonus allocation to fit;
- decrements the remaining budget by that full allocation; and
- increments monotonic `totalAllocatedRipe` accounting.

Claims never replenish the budget. `totalClaimedRipe` is also monotonic.
Foxtrot changes the remaining budget through a normal timelocked action.

## Vesting and claims

Every position stores `creationBlock`, `claimStartBlock`, and `maturityBlock`.
The epoch's snapshotted minimum vesting length is the claim cliff:

```text
claimStartBlock = creationBlock + snapshottedMinVestingLength
maturityBlock   = creationBlock + selectedVestingLength
```

Nothing is claimable before `claimStartBlock`. At the cliff, all RIPE accrued
linearly since creation becomes claimable. Vesting then continues linearly from
creation through maturity. If the selected and minimum durations are equal, the
entire allocation becomes claimable at the cliff/maturity block.

Claims use:

```text
claimVestedRipe(positionId, autoDeposit, requestedLockDuration)
claimVestedRipeMany(positionIds, autoDeposit, requestedLockDuration)
```

Batch callers should remove duplicate position IDs before submission. A duplicate
causes the complete batch to revert atomically after the first occurrence is
claimed in the same transaction.

RIPE is minted only after Vesting records a valid nonzero claim. Direct claims
mint to the beneficiary. Auto-deposit claims mint temporarily to the Engine and
deposit the exact amount into the live core RipeGov vault for the beneficiary.
The caller's lock duration is a request; RipeGov applies its live lock terms.

Both settlement modes reject a RIPE-blacklisted beneficiary before claim state is
changed. Any downstream failure reverts the complete claim transaction.
A blacklisted beneficiary's allocation is not forfeited: it remains outstanding
until the beneficiary can claim or governance migrates the position. Accordingly,
that liability continues to keep Vesting's `canRetire()` false.

## Epoch controller

Each committed epoch snapshots its payment cap, minimum payment, vesting terms,
and base payout rate. Later configuration changes do not rewrite that epoch.
Controller changes are based on the previous committed epoch's utilization and
timing data, with bounded idle decay across skipped epochs.

The configured minimum payment may be fractional. It must be nonzero, no greater
than the epoch cap, and large enough to produce at least one RIPE wei at the
minimum legal base payout rate. Changing payment tokens revalidates these raw-unit
values against the new scale, but a decimal change does not inherently force a
configuration rewrite; operators must review the resulting whole-token amounts.

The configured `maxAllInPayoutRate` caps the base rate after applying the maximum
vesting bonus. When minimum and maximum vesting lengths differ, configuration
validation also requires:

```text
maxVestingBonus * minVestingLength
    < 10_000 * (maxVestingLength - minVestingLength)
```

This ensures the maximum-duration option cannot have an equal or faster average
RIPE release rate because of its bonus.

## One-shot rate override

Governance may immediately install or cancel one named-epoch override through
Foxtrot. Target epoch `0` resolves to the earliest applicable epoch: the current
epoch when it has no successful acquisition, otherwise the next epoch, and before
genesis the first epoch.

The resolved epoch is stored and emitted. The override is consumed only when its
target epoch is first committed by a successful acquisition. A later acquisition
misses and clears an unconsumed override whose target epoch has passed. Start,
stop, and controller-configuration changes invalidate an installed override.
Pause and acquisition-availability changes preserve it, so reopening requires
explicit cancellation or revalidation. Payment-token changes require the Engine
to be stopped, which has already invalidated the override.

After a successful override, the overridden rate becomes the historical starting
point for the following controller transition. It does not snap back after the
one-shot override is consumed.

## Governance

Foxtrot actions are split deliberately:

- Engine configuration and Vesting allocation-budget changes are timelocked.
- Start, stop, payment-token changes, availability changes, and rate-override
  installation or cancellation are immediate.

The Engine and Vesting use the protocol's registered-Switchboard authorization
convention. Foxtrot is the intended named semantic entrypoint.

Pausing the Engine stops acquisitions but does not stop claims. Claims are halted
by pausing Vesting or RIPE, or by disabling the Engine's RipeHQ mint permission.
`stopReserveEngine` is reflected by the Engine's `ReserveEngineStopped` event;
indexers should subscribe to the Engine lifecycle events.

## Validation

The dedicated workflow is
[`ripe-reserve-engine.yml`](../../.github/workflows/ripe-reserve-engine.yml).
Its gate validates the blocked activation draft, generated ABIs, controller
simulation binding, complete focused tests, per-contract coverage, runtime sizes,
and gas evidence.

Useful local commands:

```bash
python scripts/qualify_ripe_reserve_engine_activation.py --check-draft
python scripts/export_abis.py --check
python scripts/simulations/ripe_reserve_engine_controller.py \
  --check docs/ripe-reserve-engine/controller-simulation-v2.json
python -m pytest -q -o addopts='' \
  tests/core/ripeReserveEngine \
  tests/config/test_switchboard_foxtrot.py \
  tests/deployment/test_ripe_reserve_engine_activation.py \
  tests/deployment/test_abi_export.py \
  tests/test_ripe_reserve_engine_workflow.py
```

The committed activation manifest remains fail-closed. Passing source and test
validation does not approve production parameters, deployment, registry updates,
allocation budget, payment token, or activation.

Once those inputs are approved and populated, `--require-ready` cross-binds the
approved Engine config and Vesting budget to observed deployment state; binds the
payment token and epoch length across approval, deployment, and fork evidence; and
requires the expected live pause, running, availability, mint-permission, and
Switchboard states. A synthetic complete-ready fixture and independent field
mutations keep that path executable and fail-closed.
