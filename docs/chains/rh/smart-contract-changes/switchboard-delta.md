# SwitchboardDelta: bounded Deleverage governance actions

## Current disposition

The corrected shared `SwitchboardDelta` source entered `rh` at historical
import ancestor `ad831669943ccfe7b9ed57454995dfce51630a66` and remains
present at frozen protocol/pause baseline `ae0cb49…`. The older hash is not
current branch authority. Its four new Robinhood values remain zero and no
action has been queued, executed, configured, or activated.

The controls currently lack Robinhood machine-facing parameter and planning
representation. The deployment owner owns final disposition and binding, but
closing the gap requires a separately authorized machine implementation track;
this rationale does not implement it.

## Four timelocked actions

Governance can initiate distinct timelocked actions for:

1. full-payoff absolute buffer;
2. full-payoff overage bps;
3. dust absolute threshold; and
4. dust relative bps.

Each action checks governance permission, validates its hard ceiling before
queueing, receives a unique action ID and confirmation block, stores the
pending value, and emits a typed pending event. The source is
[`SwitchboardDelta.vy` lines 644-721](../../../../contracts/config/SwitchboardDelta.vy#L644).

## Hard ceilings

- Full-payoff buffer: `1e18`.
- Dust threshold: `1e16`.
- Overage: `500` bps.
- Dust: `500` bps.

The same ceilings exist in Deleverage and are rechecked when a Switchboard
executes the selected parameter update
([`Deleverage.vy` lines 203-213](../../../../contracts/core/Deleverage.vy#L203),
[`Deleverage.vy` lines 1375-1393](../../../../contracts/core/Deleverage.vy#L1375)).
Queue-time and execution-time checks are complementary: neither makes a
nonzero Robinhood value approved.

## What this does not authorize

Configuration remains unactivated. This page does not authorize a nonzero
value, queue or execution, machine-facing schema changes, defaults generation,
migration execution, deployment, activation, or release. The S4 zero-cooldown
decision remains closed and separate.
