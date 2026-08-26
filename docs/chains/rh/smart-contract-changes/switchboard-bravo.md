# SwitchboardBravo: GREEN reference-pool keeper

> Source rationale only. This page does not authorize deployment, Switchboard
> promotion, a lite-signer grant, configuration, activation, or release.

## Current disposition

Draft PR #211 adds `SwitchboardBravo.addGreenRefPoolSnapshot(_curvePricesId)`
so governance or a current MissionControl lite-action signer can trigger the
specialized `CurvePrices.addGreenRefPoolSnapshot()` path. The wrapper returns
Curve's boolean and emits `GreenRefPoolSnapshotAttempted`.

This is a new operational entrypoint, not a restatement of Bravo's asset-config
surface. Controlling decision: [`RH-D045`](../decision-register.md).

## Why Bravo, and why a call argument

At the keeper implementation head, composed SwitchboardAlpha runtime was 24,562
bytes (14 bytes below EIP-170). SwitchboardBravo was 23,666 bytes with 910
bytes of headroom and was already a registered Switchboard child, so
CurvePrices treats Bravo-originated calls as valid RIPE addresses.

Teller, CreditEngine, and Endaoment resolve Curve through a constructor
`CURVE_PRICES_ID` immutable. Bravo does not: the owner forbade a constructor
argument on this addition. The PriceDesk ID remains a call argument. On
Robinhood the keeper calls `addGreenRefPoolSnapshot(2)`. That `2` is
`CURVE_PRICES_ID` in [`config/robinhood_launch.py`](../../../../config/robinhood_launch.py)
— CurvePrices' PriceDesk registry ID. It is separate from the fact that the
currently deployed Bravo occupies Switchboard child ID 2.

Measured deployed runtime after the wrapper is 24,177 bytes, leaving 399 bytes
of EIP-170 headroom. That consumed 56% of Bravo's remaining budget. Bravo is
no longer the last comfortable config-contract margin; the runtime gate now
also enforces a Bravo-only 200-byte floor. That floor is not the retired
global RH-D026 mechanism.

The complete keeper addition changes `SwitchboardBravo`'s ABI and cumulative
seal. Later comment-only Bravo edits do not.

## Authorization and failure semantics

- Governance may call immediately.
- Otherwise the current MissionControl row must return true from
  `canPerformLiteAction(msg.sender)`; unauthorized callers revert `no perms`.
- Bravo's RipeHq address is constructor-immutable. It rereads MissionControl
  (ID 5) and PriceDesk (ID 7) from that HQ on each call. A zero PriceDesk
  pointer reverts `missing price desk`.
- `_curvePricesId` is resolved through that PriceDesk. Zero or disabled rows
  both store `empty(address)` and revert `invalid price source id` before the
  specialized `extcall`.
- The `extcall` is typed. Target reverts fail the keeper transaction. The
  wrapper does not copy Teller's fail-open Curve housekeeping.

A successful Curve update returns true and logs `didUpdate=true`. Same-block
duplicates, a paused Curve, missing configuration, and other legitimate
no-update cases return false and log `didUpdate=false`. A genuine Curve
revert leaves no operational event.

The intended CurvePrices call is privileged and state-changing. The unexpected
cross-source collision radius is empty today (no `__default__`, only
CurvePrices exposes `0x7cdb0a4d`); that is a repository test, not an on-chain
invariant.

## Lite-signer grant is the practical launch path

Keeper cadence cannot be a Safe transaction per snapshot. The operational
grant is two contract calls/steps:

1. `SwitchboardAlpha.setCanPerformLiteAction(keeper, True)`
2. `SwitchboardAlpha.executePendingAction(aid)`

With Robinhood's zero `actionTimeLock` they can confirm in the same block and
may be Safe-batched if policy allows. Revoke is one immediate call.
MissionControl accepts any address; use "keeper address/caller" until a
credential architecture is selected.

Lite-signer status is a broad, unscoped protocol-operations role. Immediate
surfaces include Alpha's protocol-wide disable switches (`setCanDeposit(false)`,
withdraw, borrow, repay, liquidate, redeem, auction buy, Stability
claim/redeem, loot claim), Charlie pause/blacklist/lock/debt/loot, Delta
deleverage/HR/bond/boosters, Echo Endaoment yield plus the explicit
fund-transfer entrypoints `transferFundsToEndaomentPsmInEndaoment`,
`transferFundsToVaultInEndaoment`, and `transferUsdcToEndaomentFundsInPsm`,
and this wrapper. Alpha generic `addPriceSnapshot` is immediate. Pyth/Stork
payload paths exist but those sources are not current Robinhood deployments.
Echo PSM-disable paths are proposals that still require governance
`executePendingAction`. That unscoped operations power belongs in the
Robinhood launch risk register before the grant.

## Snapshots and dynamic rates are active

Owner authorized on 25 August 2026 that GREEN reference snapshots and
Curve-driven dynamic borrow rates are active at Robinhood launch, with
`DefaultsRobinhood.increasePerDangerBlock = 60`. Teller already snapshots on
housekeeping. This wrapper is an entrypoint only — it does not schedule,
retry, or guarantee cadence. One valid closed interval can produce a
weighted ratio; the ring need not be full. At `dangerTrigger`,
`minDynamicRateBoost = 100%` doubles the base rate before the per-danger-block
slope (`60 / 1_000_000 = 0.006%` ideal, not `0.60%`). A nonempty GREEN
ref-pool config also enables Endaoment `stabilizeGreenRefPool` through Echo;
that coupled capability is accepted with the live configuration. A shallow
pool can trip the threshold. That risk is accepted with the slope.

[`curve-launch-activation.md`](../curve-launch-activation.md) is stale on a
specific claim: it still says the launch candidate does not configure "the
GREEN reference-pool configuration or Teller snapshots" and does not activate
"Curve-driven dynamic rates." The inventory overlay, CAD-001, `status.yaml`,
and Blueprint still describe snapshots, rates, or raw `60` as inactive or
separately gated. This page does not rewrite those files.

## Launch follow-up

Merging this source does not make the wrapper available on the Bravo that
currently occupies Switchboard child ID 2. Before activation:

- Deploy the exact final Bravo runtime and authenticate source, compiler, ABI,
  constructor arguments, and the 24,177-byte runtime.
- Relinquish temporary local governance and keep the intended timelocks,
  including `actionTimeLock == 0`.
- Recheck every Bravo-local pending action; replacement creates fresh storage
  and can strand queued actions.
- Address-update that existing Switchboard child ID 2 slot, not a new slot. A
  newly deployed candidate is not a valid RIPE caller until that slot is
  updated. Prove candidate rejection before the update and Curve qualification
  after it.
- If MissionControl is also replaced in the wider rollout, migrate and verify
  lite-signer membership.
- Update the keeper address/caller, indexer, ABI consumers, and monitoring to
  the new Bravo address. Monitor failed receipts as well as events.
- Account for Robinhood EVM `block.number` reuse across child blocks
  (BN-011); duplicate `false` outcomes can be legitimate.

Several Blueprint Bravo anchors also remain separately stale.

## Tests

[`tests/config/test_switchboard_bravo_green_snapshot.py`](../../../../tests/config/test_switchboard_bravo_green_snapshot.py)
is the focused keeper suite. It uses a real `CurvePrices` deployment, a
non-default PriceDesk ID, the SwitchboardAlpha/MissionControl lite-signer
path, child-call traces for the no-write proof, the complete GREEN ring, and
compiled selector inventory:

- specialized `addGreenRefPoolSnapshot()` = `0x7cdb0a4d`
- wrapper `addGreenRefPoolSnapshot(uint256)` = `0xd9948a29`
