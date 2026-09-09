# Ripe Reserve Engine implemented design

Status: implemented in draft PR #156. This file supersedes the earlier
pre-implementation design contained at this path.

The authoritative implementation is:

- [`RipeReserveEngine.vy`](../../contracts/core/RipeReserveEngine.vy)
- [`RipeReserveVesting.vy`](../../contracts/core/RipeReserveVesting.vy)
- [`SwitchboardFoxtrot.vy`](../../contracts/config/SwitchboardFoxtrot.vy)
- [`Addys.vy`](../../contracts/modules/Addys.vy)
- the focused tests under [`tests/core/ripeReserveEngine`](../../tests/core/ripeReserveEngine)
- the current [start-here guide](README.md)

## Final owner decisions

The implementation intentionally uses:

- RipeHQ slots 26 and 27 for the Engine and Vesting contract;
- live RipeHQ resolution for Vesting and the RIPE token;
- one global remaining allocation budget in Vesting;
- monotonic allocated and claimed accounting;
- mint-on-claim rather than acquisition-time escrow;
- a catch-up cliff using the snapshotted minimum vesting duration;
- direct and batched claims;
- optional RipeGov auto-deposit with a caller-requested lock duration;
- a strict release-velocity configuration check;
- immediate start, stop, availability, payment-token, and named-epoch override
  actions;
- timelocked controller configuration and allocation-budget actions; and
- one installed, one-shot rate override at a time.

The implementation intentionally does not add:

- acquisition-time RIPE escrow;
- per-run or per-campaign budgets;
- a separate outstanding-liability limit;
- pinned RIPE-token or Vesting identities;
- registry-version bindings, lifecycle nonces, or cycle IDs;
- override deviation limits, counters, budgets, or timelocks;
- a separate cliff parameter; or
- forfeiture, lost-key, burn, or recovery machinery.

## Registry replacement boundary

The Engine resolves Vesting dynamically. Replacing slot 27 while positions are
outstanding therefore requires governance to migrate the existing Vesting state
or restore the prior contract. `RipeReserveVesting.canRetire()` is the on-chain
signal for an ordinary no-liability retirement. This is an operational migration
requirement, not an automatic registry-version binding.

## Activation boundary

The source and tests do not authorize deployment or activation. The blocked
manifest at
[`config/ripe-reserve-engine-activation.json`](../../config/ripe-reserve-engine-activation.json)
must be completed and independently approved before activation.
