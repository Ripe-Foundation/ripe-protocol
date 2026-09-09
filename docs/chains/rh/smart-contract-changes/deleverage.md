# Deleverage: corrected full-payoff and dust boundaries

## Current disposition

The current repository baseline is
`0642f086d19e3cc62faaf67da096b6511e405320`, tree
`d869d4149380b368f9678ed03efc0b59a6c804e2`. The corrected shared
`Deleverage` source entered `rh` at historical import ancestor
`ad831669943ccfe7b9ed57454995dfce51630a66`. Current `master` and current `rh`
both resolve [`Deleverage.vy`](../../../../contracts/core/Deleverage.vy)
to Git blob `b43d373039b352d6eab240be714134764901b947`, so this is a
historical/shared-source rationale rather than a current `master..rh` delta.
The current source SHA-256 is
`d64a08573d1af100a8d6ca9d72811a87414654107fd09fe105322dde53a9c138`.
`DefaultsRobinhood.vy` exists, compiles, and is source-authoritative.

The constructor controls `fullPayoffBuffer`, `overageBps`, `dustThreshold`, and
`dustBps`. All four remain zero and deferred and, as applicable, outside the
currently selected launch value projection. No Deleverage configuration has
been applied onchain. The historical S4 `deleverageCooldown == 0` decision
remains closed and was not reopened. Every Deleverage task remains parked unless
an explicit owner instruction reopens it; this documentation correction does
not reopen or implement Deleverage work.

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

The current compiler runtime template is 24,473 bytes (SHA-256
`baa883c99f91d41f7b3091090b246b415c77f5d7ffffebfd5e3366ab15366d57`),
leaving 103 template bytes below EIP-170. Binding the 96-byte immutables section
produces the documented 24,569-byte runtime and seven-byte deployed-code
headroom. These are different artifact stages and must not be conflated. The
bound-runtime constraint is release-critical; any runtime-affecting change
requires a fresh compile and independent artifact review. It is recorded at
[`Deleverage.vy` lines 5-8](../../../../contracts/core/Deleverage.vy#L5).

## Current test paths

The full-payoff/dust behavior remains covered by the current phase and
permission suites, while later integrated composition evidence covers actual
Stock delivery and swap-collateral ordering:

- [`test_deleverage_phase1.py`](../../../../tests/core/deleverage/test_deleverage_phase1.py),
  Git blob `fde41135726465e2c07970c74d19965b7f5b8702`, SHA-256
  `d4cf8c2f1ab80c0625c53e42f92d431af4ab9d6aace06aa16dc0d159bb497cee`;
- [`test_deleverage_phase2.py`](../../../../tests/core/deleverage/test_deleverage_phase2.py),
  Git blob `fb4a94dca9d0e2f79734a60f34cfcb02ca9b3a2b`, SHA-256
  `a48428668184a66b653669958334f0f6a74f3c051c062161349c23d15b0be416`;
- [`test_deleverage_phase3.py`](../../../../tests/core/deleverage/test_deleverage_phase3.py),
  Git blob `55d751dce38b78d5bbe8dd61a3b629cbc5a9500f`, SHA-256
  `e82044c2e6e911f0280624656b4c4eb25f72993a1c435549e790348335b2d85f`;
- [`test_deleverage_stock_delivery.py`](../../../../tests/core/deleverage/test_deleverage_stock_delivery.py),
  Git blob `d8a0d95317b45ac7a20016945a05f14ae3eead6d`, SHA-256
  `c74b1b0d8b22e5a064109c6f811b98010d40aa979600683d57d3d67e5a385d54`;
  and
- [`test_deleverage_swap_collateral.py`](../../../../tests/core/deleverage/test_deleverage_swap_collateral.py),
  Git blob `bb0560048f91a89b7c413ff177360bb4ae0a759f`, SHA-256
  `3b900a98eb348fa5db94a0090974bb47c7cab3e5e86d951569a978b8181632b9`.

The later integrated Deleverage tests were inspected for this current rebind.
No behavioral suite was rerun for this documentation-only refresh.

## What this does not authorize

This rationale does not authorize nonzero values, the missing machine-facing
representation, a cooldown change, Underscore inclusion, migration execution,
deployment, production configuration, activation, or release.
