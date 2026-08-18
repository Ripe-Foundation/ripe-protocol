# Security review — adding a fast bridge (Across / Relay) alongside CCIP

Reviewer: Leto
Date: 2026-08-18
Scope: the trust boundaries a fast bridge would touch for GREEN and RIPE on
Base <-> Robinhood Chain. Reviewed against `rh` at `2985e73`.

This is an adversarial review of the *integration shape*, not of Across's or
Relay's own contracts. It assumes the "fast-fill from float, settle later over
CCIP" pattern that both bridge evaluations converge on.

## What the current mint boundary actually is

Every cross-chain GREEN unit today is created by exactly one code path:

- `GreenToken.mint` (`contracts/tokens/GreenToken.vy:63`) — the only entry
  point, guarded by `RipeHq.canMintGreen(msg.sender)`.
- `RipeHq.canMintGreen` (`contracts/registries/RipeHq.vy:376-386`) requires
  **all** of: the global `mintEnabled` flag, the caller being a registered
  address (`addrToRegId != 0`), `hqConfig[regId].canMintGreen`, and the
  caller's own `Department.canMintGreen()` self-attestation.
- The self-attestation is immutable — `DeptBasics.vy:31-51` sets
  `CAN_MINT_GREEN` in the constructor and returns it from a `@view`. A
  department cannot flip its own capability at runtime.
- `Erc20Token._mint` (`contracts/tokens/modules/Erc20Token.vy:292-295`) adds
  `not blacklisted[_recipient]` and `not isPaused`.

RIPE is identical (`RipeToken.vy`, `RipeHq.vy:388-398`).

Two properties of this boundary drive everything below.

**There is no mint cap and no rate limit anywhere in the protocol.** Neither
`RipeHq` nor `Erc20Token` bounds how much an authorized department may mint.
The only throttle on the CCIP leg is the rate limiter *inside Chainlink's
pool*, which is bridge-local and not protocol-enforced.

**Revocation is slow; the only fast lever is global.** Removing a registered
department goes through `_startAddressDisableInRegistry` ->
`_confirmAddressDisableInRegistry`, gated on
`block.number >= confirmBlock` where `confirmBlock = block.number +
registryChangeTimeLock` (`contracts/registries/modules/AddressRegistry.vy:330-341,
349-351`). The same timelock applies to `initiateHqConfigChange` /
`confirmHqConfigChange`. The one immediate action is
`RipeHq.setMintingEnabled(false)` (`RipeHq.vy:419-424`), governance-only, and
it halts **all** GREEN and RIPE issuance protocol-wide — borrowing included,
not just the bridge.

Disable does correctly clear the reverse mapping (`addrToRegId[prevAddr] = 0`,
`AddressRegistry.vy:365`), so a disabled department stops passing
`canMintGreen`. No bug there.

## Findings

### H-1 — A liquidity-based fast bridge bypasses the protocol's cross-chain circuit breaker

**Severity: High (economic / control).**

`setMintingEnabled(false)` is the protocol's stated chain-local stop for
cross-chain issuance, and today it is complete: with CCIP burn/mint, no GREEN
can appear on a destination chain without passing `canMintGreen`.

An Across- or Relay-style fill is not a mint. It is a plain ERC-20 transfer of
pre-positioned inventory from the relayer to the user. `Erc20Token._transfer`
(`Erc20Token.vy:202-211`) checks `isPaused`, blacklist, and balance — it does
**not** consult `RipeHq.mintEnabled`. So the moment a fast lane exists,
`setMintingEnabled(false)` no longer stops cross-chain GREEN movement.

Exploit sketch: GREEN trades below peg on Base during an incident. Governance
disables minting to stop the bleed. The canonical bridge is now closed, but the
fast lane is not — holders keep routing GREEN across at par against the float
until the float is empty. Under the self-relay proposal that float is Ripe's
own capital, so the protocol funds its own exit while believing it is paused.
The one lever that *does* cover it is `Erc20Token.pause` — but that is a
token-wide freeze that also stops every user transfer, DEX pool, and vault
interaction. Nobody will reach for it quickly.

Recommendation: the filler must be a Ripe-controlled contract that reads a
Ripe-controlled gate (`RipeHq.mintEnabled()`, or better a dedicated bridge
switch so it can be tripped without halting borrowing) and refuses to fill when
it is off. If a permissionless third-party solver market is ever enabled for
GREEN/RIPE, it must be documented as an outflow channel governance **cannot**
stop short of a token-wide pause.

### H-2 — Blacklist on the settlement leg strands capital permanently, and float-fronting moves the loss onto Ripe

**Severity: High (funds at risk).**

`_mint` rejects a blacklisted recipient (`Erc20Token.vy:294`). CCIP burn/mint
burns on the origin chain *before* the destination mint is attempted, so a
destination-side rejection leaves a message that cannot execute. Pause is
recoverable (unpause, then manually execute). Blacklist is not: the message
reverts on every retry for as long as the flag is set, with the origin-side
supply already destroyed.

Today the party bearing that risk is the sanctioned user, which is arguably the
point. Under fast-fill-then-settle it inverts: the user is paid instantly from
float, and it is *Ripe's* rebalancing leg that gets stuck. Concretely, if the
float/ops address that receives settlement is ever blacklisted — including by
mistake, or by a `canSetTokenBlacklist` department acting on a heuristic — the
canonical leg backing already-fronted fills becomes permanently unredeemable.

Recommendation: settlement must land on a contract address that is explicitly
excluded from blacklisting, with an invariant test asserting it. Blacklist
status of both the recipient and the float address must be checked at fill
time, before the fast payout, not after.

### M-1 — `mintEnabled` is chain-local, so the two legs can disagree and the IOU gap is unbounded

**Severity: Medium (escalates to High without a circuit breaker).**

RipeHq on Base and RipeHq on Robinhood Chain are independent deployments with
independent `mintEnabled` state. Disabling minting on the destination chain does
nothing to stop the origin chain from burning and dispatching. In-flight
messages then pile up unexecutable while the fast lane keeps fronting against a
settlement path that is closed.

The circuit breaker for this must be driven by *observed settlement backlog*
(fronted-but-unsettled notional, and age of the oldest unsettled fill), and it
must act on the **send** side. A breaker that only reacts to the destination
chain's state is one round-trip too late.

Recommendation: hard caps on (a) total fronted-unsettled notional and (b) oldest
unsettled age, both enforced in the filler contract, both failing closed.

### M-2 — Hold the line on mint authority: a second mint-authorized adapter has no fast kill switch

**Severity: Medium (design constraint, currently satisfied).**

`ccip-integration-decision.md` already rejects a separately registered mint
adapter. That decision is correct and the code says why more sharply than the
doc does: with no per-department mint cap, a compromised mint-authorized bridge
can mint unbounded GREEN, and the only response that lands inside the timelock
window is `setMintingEnabled(false)` — which halts the entire protocol's
issuance, not just the bridge.

Across and Relay must therefore be integrated **strictly as liquidity/inventory
bridges with zero RipeHq authorization**. No new `hqConfig` entry, no new
`canMintGreen`/`canMintRipe` department. Any proposal that routes a fast bridge
through `GreenToken.mint` should be rejected on this basis alone.

## Test obligations

Whatever design lands, these must be red-before-green:

1. Fill reverts when the bridge gate is off (H-1).
2. Fill reverts when recipient or float address is blacklisted (H-2).
3. Fronted-unsettled notional cap and staleness cap both fail closed (M-1).
4. Invariant: no address other than the two CCIP pools ever satisfies
   `RipeHq.canMintGreen` / `canMintRipe` (M-2).
5. Token pause halts the fast lane as well as the canonical lane.

## Sign-off

Not signed off. H-1 and H-2 are unresolved and must be answered by the design
before implementation starts.
