# Security review — a direct Relay lane for GREEN / RIPE

Reviewer: Leto
Date: 2026-08-18
Revised: 2026-08-18 (rev 2 — rescoped, H-2 corrected, invariant corrected)
Scope: the trust boundaries a fast, liquidity-based bridge lane would touch for
GREEN and RIPE on Base <-> Robinhood Chain. Reviewed against `rh` at `2985e73`.

Across token bridging for GREEN/RIPE has been rejected, so this review is
scoped to a **direct Relay lane**. The findings are properties of the
*fast-fill-from-float* shape rather than of any one vendor, so they apply to
any future liquidity-based lane; they are not claims about Relay's own
contracts, which are out of scope here.

Out of scope: the local-mint acquisition flow. That is a separate product path,
not a GREEN transfer route.

## What the current mint boundary actually is

Every cross-chain GREEN unit today is created by one code path:

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

Mint authority is **not** exclusive to the bridge. Departments constructed with
mint rights today:

| Capability | Departments |
| --- | --- |
| `canMintGreen` | `Endaoment`, `EndaomentPSM`, `CreditEngine`, `AuctionHouse` |
| `canMintRipe` | `BondRoom`, `Lootbox`, `HumanResources`, `VaultBook` |

(plus the two CCIP pools once registered — see `ccip-live-state.md`). Any
invariant about mint authority must be phrased as *no new bridge address joins
this set*, never as *only the pools can mint*.

Two further properties drive the findings.

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
it halts **all** GREEN and RIPE issuance protocol-wide — borrowing, auction
keeper rewards, bond payouts, and staking rewards included.

Disable does correctly clear the reverse mapping (`addrToRegId[prevAddr] = 0`,
`AddressRegistry.vy:365`), so a disabled department stops passing
`canMintGreen`. No bug there.

## Findings

### H-1 — A liquidity-based fast lane bypasses the protocol's cross-chain circuit breaker

**Severity: High (economic / control). Unresolved.**

`setMintingEnabled(false)` is the protocol's stated chain-local stop for
cross-chain issuance, and today it is complete: with CCIP burn/mint, no GREEN
can appear on a destination chain without passing `canMintGreen`.

A Relay fill is not a mint. It is a plain ERC-20 transfer of pre-positioned
inventory from the filler to the user. `Erc20Token._transfer`
(`Erc20Token.vy:202-211`) checks `isPaused`, blacklist, and balance — it does
**not** consult `RipeHq.mintEnabled`. So the moment a fast lane exists,
`setMintingEnabled(false)` no longer stops cross-chain GREEN movement.

Exploit sketch: GREEN trades below peg on Base during an incident. Governance
disables minting to stop the bleed. The canonical bridge is now closed, but the
fast lane is not — holders keep routing GREEN across at par against the float
until the float is empty. Under a self-relay design that float is Ripe's own
capital, so the protocol funds its own exit while believing it is paused. The
one lever that *does* cover it is `Erc20Token.pause`, but that is a token-wide
freeze that also stops every user transfer, DEX pool, and vault interaction.
Nobody will reach for it quickly.

Recommendation: the filler must be a Ripe-controlled contract reading a
Ripe-controlled gate, and it must fail closed. Prefer a **dedicated bridge
switch** over reusing `mintEnabled`, so the lane can be stopped without halting
borrowing and rewards. If a permissionless third-party solver market is ever
enabled for GREEN/RIPE, it must be documented as an outflow channel governance
**cannot** stop short of a token-wide pause.

Note for the float design: `Endaoment` is already a `canMintGreen` department.
If it is also the float holder, fill logic executes inside a contract that
holds mint authority — the blast radius of a fill bug is then minting, not just
inventory. Prefer a separate, non-mint-authorized filler contract funded by
Endaoment, so the fast lane never shares an address with mint rights.

### H-2 — Blacklist on the settlement leg blocks it indefinitely, and float-fronting moves the exposure onto Ripe

**Severity: High (funds at risk). Unresolved. Corrected in rev 2.**

`_mint` rejects a blacklisted recipient (`Erc20Token.vy:294`). CCIP burn/mint
burns on the origin chain *before* the destination mint is attempted, so a
destination-side rejection leaves a message that cannot execute. Pause is
recoverable by unpausing and manually executing. Blacklist blocks execution for
as long as the flag is set.

**Correction (rev 2):** rev 1 called this permanent and proposed a
"blacklist-exempt settlement address". Both were wrong.

- Blacklisting is **reversible in code**: `setBlacklist` takes a `bool` and can
  be set back to `False` (`Erc20Token.vy:405-411`). The accurate risk is
  *indefinitely policy-blocked settlement* — bounded by a governance decision
  that may never come, not by the contract.
- There is **no blacklist-exemption primitive**. `setBlacklist` exempts only
  the token itself and the zero address (`Erc20Token.vy:408`). Any address the
  protocol uses for settlement, contract or EOA, is blacklistable. That
  mitigation cannot be assumed; it would have to be built.

The exposure still inverts under fast-fill-then-settle. The user is paid
instantly from float, so it is *Ripe's* rebalancing leg that blocks. If the
float or settlement address is blacklisted — including by mistake, or by a
`canSetTokenBlacklist` department acting on a heuristic — the canonical leg
backing already-fronted fills is blocked until governance clears the flag, and
fronted capital sits unrecovered for that entire window.

A sharper tail risk: `burnBlacklistTokens` (`Erc20Token.vy:415-422`) lets
governance burn a blacklisted address's **entire balance**. A blacklisted float
address is therefore not merely blocked — its inventory is destroyable by a
single governance call.

Recommendation, in order of preference:

1. Bound the exposure rather than assume immunity: hard caps on fronted-unsettled
   notional and on oldest-unsettled age (see M-1), so a blocked settlement leg
   is capped rather than open-ended.
2. Check blacklist status of recipient, float, and settlement addresses at fill
   time, before the fast payout — cheap and catches the common case.
3. If a protected-settlement-address primitive is wanted, it is **new work** on
   `Erc20Token` with its own review; do not plan around it as if it exists.

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
unsettled age, both enforced in the filler contract, both failing closed. These
caps are also the bound that makes H-2 tolerable.

### M-2 — Hold the line on mint authority: a new mint-authorized bridge has no fast kill switch

**Severity: Medium (design constraint, currently satisfied).**

`ccip-integration-decision.md` already rejects a separately registered mint
adapter. That decision is correct, and the code gives a sharper reason than the
doc does: with no per-department mint cap, a compromised mint-authorized bridge
can mint unbounded GREEN, and the only response that lands inside the timelock
window is `setMintingEnabled(false)` — which halts the entire protocol's
issuance, not just the bridge.

Relay must therefore be integrated **strictly as a liquidity/inventory lane
with zero RipeHq authorization**. No new `hqConfig` entry, no new
`canMintGreen`/`canMintRipe` department. Any proposal that routes the fast lane
through `GreenToken.mint` should be rejected on this basis alone.

## Test obligations

Whatever design lands, these must be red-before-green:

1. Fill reverts when the dedicated bridge gate is off (H-1).
2. Fill reverts when recipient, float, or settlement address is blacklisted
   (H-2).
3. Fronted-unsettled notional cap and staleness cap both fail closed (M-1).
4. Invariant: the set of addresses satisfying `RipeHq.canMintGreen` /
   `canMintRipe` is unchanged by the Relay integration — specifically, no
   filler, float, settlement, or Relay-owned address joins it. Assert against
   the enumerated department set above plus the registered CCIP pools; do
   **not** assert that only the pools can mint, which is false today (M-2).
5. Token pause halts the fast lane as well as the canonical lane.

## Sign-off

Not signed off. H-1 and H-2 remain unresolved and must be answered by the
design before implementation starts.
