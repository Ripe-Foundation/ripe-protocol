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
CurvePrices' PriceDesk registry ID. It is separate from Bravo also being
Switchboard child ID 2.

Measured deployed runtime after the wrapper is 24,177 bytes, leaving 399 bytes
of EIP-170 headroom. That consumed 56% of Bravo's remaining budget. Bravo is
no longer the last comfortable config-contract margin; the runtime gate now
also enforces a 200-byte Bravo floor.

## Authorization and failure semantics

- Governance may call immediately.
- Otherwise the current MissionControl must return true from
  `canPerformLiteAction(msg.sender)`; unauthorized callers revert `no perms`.
- Bravo resolves the current PriceDesk through the current RipeHq
  `PRICE_DESK_ID`. A zero pointer reverts `missing price desk`.
- `_curvePricesId` is resolved through that PriceDesk. Zero or disabled rows
  both store `empty(address)` and revert `invalid price source id` before the
  specialized `extcall`.
- The `extcall` is typed. Target reverts fail the keeper transaction. The
  wrapper does not copy Teller's fail-open Curve housekeeping.

A successful Curve update returns true and logs `didUpdate=true`. Same-block
duplicates and a paused Curve return false and log `didUpdate=false`. A
genuine Curve revert leaves no operational event.

## Lite-signer grant is the practical launch path

Keeper cadence cannot be a Safe transaction per snapshot. The operational
grant is:

1. `SwitchboardAlpha.setCanPerformLiteAction(keeper, True)`
2. `SwitchboardAlpha.executePendingAction(aid)`

That is two Safe transactions even with Robinhood's zero timelock. Revoke is
one transaction. Lite-signer status is not scoped to this function. The same
key can disable or pause through Alpha, Charlie, Delta, and Echo, call Alpha's
generic `addPriceSnapshot`, and push Pyth/Stork payloads. That unscoped
disable/pause power belongs in the Robinhood launch risk register before the
grant.

## Launch follow-up

Merging this source does not make the wrapper available on the currently
deployed Bravo. Before activation:

- Deploy the exact final Bravo runtime and authenticate source, compiler, ABI,
  constructor arguments, and the 24,177-byte runtime.
- Relinquish temporary local governance and keep the intended timelocks,
  including `actionTimeLock == 0`.
- Recheck every Bravo-local pending action; replacement creates fresh storage
  and can strand queued actions.
- Perform an address update of existing Switchboard child ID 2, not a new
  slot. Prove candidate rejection before registration and Curve qualification
  after registration.
- If MissionControl is also replaced in the wider rollout, migrate and verify
  lite-signer membership.
- Update keeper, indexer, ABI consumers, and monitoring to the new Bravo
  address. Monitor failed receipts as well as events.
- Account for Robinhood EVM `block.number` reuse across child blocks;
  duplicate `false` outcomes can be legitimate.

[`curve-launch-activation.md`](../curve-launch-activation.md) and several
Blueprint Bravo anchors remain separately stale. This page does not refresh
them.

## Tests

[`tests/config/test_switchboard_bravo_green_snapshot.py`](../../../../tests/config/test_switchboard_bravo_green_snapshot.py)
is the focused keeper suite. It uses a real `CurvePrices` deployment, a
non-default PriceDesk ID, the SwitchboardAlpha/MissionControl lite-signer
path, child-call traces for the no-write proof, the complete GREEN ring, and
compiled selector inventory:

- specialized `addGreenRefPoolSnapshot()` = `0x7cdb0a4d`
- wrapper `addGreenRefPoolSnapshot(uint256)` = `0xd9948a29`
