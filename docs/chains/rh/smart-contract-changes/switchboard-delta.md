# SwitchboardDelta: bounded Deleverage governance actions

## Current disposition

The corrected shared `SwitchboardDelta` source entered `rh` at historical
import ancestor `ad831669943ccfe7b9ed57454995dfce51630a66`. Current `master`
and current `rh` (`5f5d22b7…`, tree `7454b545…`) both resolve
[`SwitchboardDelta.vy`](../../../../contracts/config/SwitchboardDelta.vy) to
Git blob `4e234df7626eb332836aceb5cbca2daaef2a0390`, SHA-256
`12604c00353b2b4e7519ffd316883e1e64394af53dd79f2c9866765d7385eb79`.
This is a historical/shared-source rationale, not a current `master..rh`
production delta. Its four new Robinhood values remain zero and no action has
been queued, executed, configured, or activated.

The current runtime template is 23,102 bytes, with 1,474 bytes of EIP-170
headroom and SHA-256
`77553ded4c1e8de0754b25e0dbb0fa18be25657b3134c90bc071a99306bfca61`.

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

## Current test path

[`tests/config/test_switchboard_delta.py`](../../../../tests/config/test_switchboard_delta.py)
is the current direct governance-action suite (Git blob
`787c4cb2f1adb4808de08ce8be272bba1e87b314`, SHA-256
`1850cd864fe9fa766f037e372339deef145dd9d275b5b0d191cc941707715dc4`).
The current Deleverage phase and permission suites also exercise execution-side
ceilings and authorization. These paths were inspected but not rerun for this
documentation-only refresh.

## What this does not authorize

Configuration remains unactivated. This page does not authorize a nonzero
value, queue or execution, machine-facing schema changes, defaults generation,
migration execution, deployment, activation, or release. The S4 zero-cooldown
decision remains closed and separate.
