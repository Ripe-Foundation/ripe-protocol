# Deleverage: corrected full-payoff and dust boundaries

## Current disposition

The corrected shared `Deleverage` source is integrated into `rh` at commit
`ad831669943ccfe7b9ed57454995dfce51630a66`. It has not been deployed or
configured on Robinhood. The constructor controls `fullPayoffBuffer`,
`overageBps`, `dustThreshold`, and `dustBps`; all four Robinhood values remain
zero and deferred. They currently have no Robinhood machine-facing parameter
or planning representation. A separately authorized future implementation
track must close that gap. This documentation page does not.

The historical S4 `deleverageCooldown == 0` decision remains closed and was not
reopened. `DefaultsRobinhood.vy` remains absent and fail-closed.

## Why the change exists

Trusted callers can request a full payoff, but that intent must not create an
unbounded collateral or accounting exception. The corrected path therefore:

1. recognizes full-payoff extras only for a trusted flow targeting the entire
   debt;
2. classifies the position owner, not merely the caller, and excludes an
   Underscore Earn-vault owner from the extras path;
3. limits extra collateral by both an absolute buffer and a debt-relative bps
   cap;
4. caps debt clearing at the real debt even when extra collateral is consumed;
5. permits a dust write-off only for a full-payoff flow, after nonzero
   collateral was consumed, and only when both the absolute and relative dust
   caps pass; and
6. treats the forgiven remainder as an explicit write-off: no GREEN is burned
   for that remainder.

The trusted-caller and owner boundary is in
[`Deleverage.vy` lines 682-733](../../../../contracts/core/Deleverage.vy#L682).
The dual collateral cap and capped debt clearing are in
[`Deleverage.vy` lines 757-783](../../../../contracts/core/Deleverage.vy#L757).
The write-off semantics are explicit at
[`Deleverage.vy` lines 773-782](../../../../contracts/core/Deleverage.vy#L773).

## Safe-conversion consistency

For Underscore Basic Earn vault assets, Deleverage values the actual amount
sent using `convertToAssetsSafe` plus the configured spread cap. A zero safe
conversion cannot be credited, and the post-withdraw assertion deliberately
matches AuctionHouse's preflight behavior. See
[`Deleverage.vy` lines 1184-1212](../../../../contracts/core/Deleverage.vy#L1184)
and the shared conversion helper at
[`Deleverage.vy` lines 1256-1268](../../../../contracts/core/Deleverage.vy#L1256).

## Hard ceilings and size constraint

The contract caps the absolute full-payoff buffer at `1e18`, dust threshold at
`1e16`, and both relative controls at `500` bps
([`Deleverage.vy` lines 203-213](../../../../contracts/core/Deleverage.vy#L203)).
Switchboard-only execution rechecks the selected ceiling
([`Deleverage.vy` lines 1375-1393](../../../../contracts/core/Deleverage.vy#L1375)).

The deployed runtime is **24,569 bytes**, leaving only **seven bytes** below
the EIP-170 limit. This is a release-critical constraint, not spare capacity;
any runtime-affecting change requires a fresh compile and independent artifact
review. The source-bound measurement is recorded at
[`Deleverage.vy` lines 5-8](../../../../contracts/core/Deleverage.vy#L5).

## What this does not authorize

This rationale does not authorize nonzero values, the missing machine-facing
representation, a cooldown change, Underscore inclusion, migration execution,
deployment, production configuration, activation, or release.
