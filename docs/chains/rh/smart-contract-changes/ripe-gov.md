# RipeGov SC-12 early-release accounting and lifecycle policy

> [!IMPORTANT]
> This record describes the owner-facing policy and rollout consequences of
> the SC-12 review candidate. Source integration, deployment, configuration,
> activation, migration, and release remain separate authority gates.

## Economic exit-fee rule

An early release leaves the fee inside the same permissionless asset pool. It
does not transfer assets out of the vault. Instead, it burns enough of the
exiting address's shares that the address retains the largest indivisible share
balance satisfying the exact post-state claim bound:

```text
claim(postShares) <= target < claim(postShares + 1)
target = floor(claim(preShares) * (100% - exitFee))
```

`claim` is the SharesVault conversion with the virtual asset/share terms and
integer flooring. This maximality rule—not an assumption of one-asset-unit fee
accuracy—is the integration guarantee. At a high share price, one fewer share
can reduce the claim by more than one asset base unit. Any additional charge in
that state is forced by indivisible-share granularity rather than an
approximation in the burn calculation.

The rule requires actual shares held by another address. A genuine
single-address holder cannot release early until another address holds shares;
the ordinary post-unlock withdrawal path remains available under its existing
rules. The check is intentionally address-level, not beneficial-owner-level.
The contract cannot identify common control across permissionless addresses,
so one economic owner can split a position, release one address, and recapture
some or all redistributed value through another controlled address. Same-pool
redistribution therefore does not guarantee an unrecapturable economic
penalty. A stronger property would require an external fee destination or a
separately approved mechanism.

## Governance-point lifecycle

Early release first accrues governance points through the release block and
then preserves every saved point while reducing shares. This is accepted,
pre-existing policy. In contrast, an enabled ordinary partial withdrawal
proportionally reduces saved points with the withdrawn share fraction. Until a
complete withdrawal, early release is therefore more points-favorable than an
equivalent ordinary partial withdrawal.

At a 100% exit fee, the release can leave a record with `lastShares == 0` and
nonzero `govPoints`:

- the zero-share record accrues no new points;
- it cannot be exported for migration because migration requires nonzero
  source shares;
- a later deposit into the same asset reattaches the saved points to a live
  position; and
- a later complete ordinary withdrawal clears the reattached points and the
  corresponding user/global totals.

This interim point stock becomes immediately material if Boardroom or another
governance-power consumer is active. Rollout review must inventory those
consumers and must not treat zero shares as proof of zero governance power.

## Underscore forced-release activation blocker

`Teller.releaseLock` permits a non-self caller when
`TellerUtils.isUnderscoreOwnerOrLego(user, caller, missionControl)` succeeds.
The predicate accepts either the owner of the specific Underscore wallet or any
address registered in the configured Underscore registry/LegoBook. The latter
branch is not bound to the target user. With a nonzero `underscoreRegistry`, a
malicious, compromised, or overly permissive registered address can therefore
invoke an exposed Teller release route for an unrelated user. SC-12 does not
create that pre-existing authorization, but an attacker holding shares in the
same pool can receive part of a victim's forced-release fee through the
documented redistribution rule.

The affected branch is dormant in the initial Robinhood configuration because
`DefaultsRobinhoodLive.underscoreRegistry()` returns the zero address. A
nonzero registry is a **blocked activation state**, not an accepted risk.
[Issue #161](https://github.com/Ripe-Foundation/ripe-protocol/issues/161) must
remain open until one of these separately authorized dispositions is complete:

1. bind each registered Lego/address to a wallet/user relationship it is
   actually authorized to control, including negative tests proving an
   unrelated registered caller cannot release the victim's lock and a complete
   Teller/TellerUtils caller and compatibility review; or
2. obtain explicit owner and security-reviewer acceptance of the broad
   authorization, binding the exact registered contracts, callable surfaces,
   monitoring, and incident controls.

No deployment or activation package may configure a nonzero Underscore
registry before one of those dispositions is recorded. PR #144 does not
redesign Teller or grant authority to accept this risk.

## Reviewed reentrancy boundary

`RipeGov.adjustLock` and `RipeGov.releaseLock` do not carry local
`@nonreentrant` decorators. This is reviewed with no production change: both
methods accept only the exact Teller, both Teller entry points are already
`@nonreentrant`, and a Boardroom or Lootbox callback cannot call RipeGov as
Teller. The external dependencies remain protocol-registered components within
the existing trust model. A defense-in-depth RipeGov decorator, if desired,
requires a separate authorized change with runtime-size, artifact-identity,
callback, and full-regression validation.

## Verification and rollout consequences

Focused tests must keep the production formula independent from its oracle.
The committed oracle evaluates the post-state claim predicate with monotonic
search, rather than repeating the closed-form rearrangement. Reachable states
cover fee boundaries, virtual terms, a zero target, high-share-price donation
granularity, repeated releases, and multiple holders. A separate pure checked
`uint256` model characterizes addition, multiplication, and denominator
boundaries that cannot be reached safely through ordinary deposits.

The Base RipeGov migration candidate has its own integration delta and artifact
identity. Its pre-SC-12 size evidence is stale and may not be replaced with the
RH measurement. [Issue #150](https://github.com/Ripe-Foundation/ripe-protocol/issues/150)
must rebase and remeasure that exact candidate before it relies on this source.

No item in this record authorizes deployment, migration, configuration,
activation, governance-power consumption, or release.
