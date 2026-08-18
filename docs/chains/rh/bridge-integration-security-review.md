# Security review — a direct Relay lane for GREEN / RIPE

Reviewer: Leto
Date: 2026-08-18
Revised: 2026-08-18 (rev 2 — rescoped, H-2 corrected, invariant corrected;
rev 3 — added H-3, post-deposit authority fields;
rev 4 — added H-4 custody exposure;
rev 5 — H-3 Relay resolution RETRACTED, H-4 ceiling corrected to receivable)
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

### H-3 — Provider deposit fields that carry post-deposit authority must be asserted equal to the connected wallet

**Severity: High (funds at risk). Unresolved for Relay. Added rev 3.**

Across V4 supplies the worked example, established at pinned commit
`8aa73521538caff624f76d1fc9e6f8984a1b01be` and recorded in
`across-settlement-evaluation.md`. `SpokePool._depositV3` validates `depositor`
only as a bytes32 address format (`uint256(_bytes32) >> 160 == 0`,
`libraries/AddressConverters.sol:19`) while pulling funds from `msg.sender`, so
payer and recorded depositor are independent. The recorded depositor can then
sign an EIP-712 `UpdateDepositDetails` (`SpokePool.sol:163`) that rewrites
`updatedRecipient`, `updatedOutputAmount`, and `updatedMessage`; any relayer
fills against it via `fillRelayWithUpdatedDeposit` and is repaid normally. Funds
reach the signer on the ordinary success path.

The generalizable point is not the specific field. It is that **a deposit
parameter naming an address can confer authority that outlives the deposit
transaction**, and validating the *payout* field does not constrain the field
that can rewrite it. Two consequences bind this protocol:

**No server-side compensating control exists.** The rewrite is a separate,
later action — off-chain signature plus a relayer's choice of fill function. No
amount of deposit-time calldata validation, allowlisting, or quote proxying
observes it. The only moment the attack is preventable is before the user signs
the deposit, by refusing calldata that names anyone else. That makes the
client-side equality assertion the sole control, not a defence-in-depth layer.

**The rule, applied per provider, is:** enumerate every address-typed field in
the deposit payload; for each, determine whether it carries any authority after
the deposit lands — amendment, cancellation, refund receipt, speed-up,
delegation; assert equality with the connected signing address for every field
that does. Equality, not non-zero: a non-zero attacker address is the attack.

**NOT resolved for Relay — rev 4 was wrong and is retracted.** Rev 4 stated
that Relay has no field to assert equality against because it tracks no
per-depositor balance on-chain. That inference does not hold: Relay's
attribution is **event-driven and off-chain**, so the absence of on-chain
per-depositor storage says nothing about whether a field carries authority.

Read at the pinned commit (`relay-depository` `458a64c`,
`packages/ethereum-vm/src/RelayDepository.sol:103,118-132`), Relay has the same
field:

```solidity
/// @param depositor The address of the depositor - set to `address(0)` to credit `msg.sender`
function depositErc20(address depositor, address token, uint256 amount, bytes32 id) public {
    token.safeTransferFrom(msg.sender, address(this), amount);
    address depositorAddress = depositor == address(0) ? msg.sender : depositor;
    emit RelayErc20Deposit(depositorAddress, token, amount, id);
}
```

Funds come from `msg.sender`; the **credited** address is caller-supplied; the
Hub attributes off that event. Naming an attacker credits the attacker. Same
class as Across.

**And the safe value is inverted between the two providers.** For Relay,
`address(0)` is the documented self-credit sentinel — the *safe* value. For
Across, a zero depositor burns the refund leg and a non-zero attacker address is
the attack. So:

| | Across | Relay |
| --- | --- | --- |
| Safe values | `depositor == connected` only | `depositor == connected` **or** `address(0)` |
| `depositor != 0` as a check | wrong — the attack is non-zero | wrong — rejects the safe sentinel |

This is the strongest argument for the enumeration rule being *per provider*
rather than a shared checklist. A control correct for one provider is wrong for
the other in both directions, and the failure is silent. An implementer who
generalizes the Across rule to Relay writes a check that rejects safe deposits;
one who generalizes Relay's to Across writes a check that permits the attack.

**Constraint on the deferred atomic variant.** Atomic bridge-and-deposit is out
of v1, and this is a reason to keep it there. A destination-side fill handler
receiving funds and depositing on the user's behalf makes the message the
*deposit instruction*, and `updatedMessage` sits inside the same signature as
`updatedRecipient` — a non-empty message triggers the recipient's
`handleV3AcrossMessage` hook (`SpokePool.sol:531`, `:1034`). Whoever holds the
amendment authority therefore controls both where funds land and what the
handler is told to do with them. Any atomic design must treat the inbound
message as attacker-controlled and authenticate the deposit instruction
independently of the bridge payload.


### H-4 — A bounded fronted-notional cap does not bound custody risk; Relay's Depository is two EOA keys

**Severity: High (funds at risk). Unresolved. Added rev 4.**

M-1's caps and H-1's "bounded float" both bound Ripe's exposure to *its own*
settlement lag — how much has been fronted and not yet reconciled. They say
nothing about the float while it sits idle in the provider's custody, which is
the larger number: enough inventory to serve bursts, not merely to cover
in-flight fills.

**Correction (rev 5): the exposure is the receivable, not the inventory.** Rev
4 described Ripe's destination inventory as "standing float parked in Relay's
Depository." That is not the flow. In Relay's model the filler holds destination
inventory in its **own** custody and pays the user from it; the Depository holds
the *user's* origin-chain deposit, which the filler later collects. So what Ripe
has inside Relay's custody is an **outstanding, unwithdrawn receivable**, not
its whole inventory. The correct loss ceiling is that receivable. This matches
the cap framing in `relay-settlement-evaluation.md` and supersedes the wording
here.

The custody finding itself stands, live-queried on Base and Robinhood at
2026-08-18T18:21Z for the Depository at
`0x4cd00e387622c35bddb9b4c962c136462338bc31`:

- `allocator` = an **EOA**, sole signer for `execute()`, able to move 100% of
  the pooled balance to any address via arbitrary calldata
  (`RelayDepository.sol:155-181`); and
- `owner` = an **EOA**, able to repoint `allocator` instantly via `setAllocator`
  (`:92-96`) — `onlyOwner`, no timelock, no two-step handoff.

Two amplifiers that survive the correction and make the smaller number harder to
manage than it looks:

**Ripe cannot collect unilaterally.** The only exit from the Depository is
`execute(CallRequest, signature)` gated on `allocator.isValidSignatureNow`.
There is no depositor-initiated withdrawal and no refund path. So the *age* of
Ripe's receivable is set by Relay's willingness to sign, not by Ripe's
reconciliation cadence. "Withdraw more often to keep the exposure small" is not
a control Ripe holds — which means the cap has to be enforced where Ripe does
have control: by the filler declining to fill once the outstanding receivable
reaches the ceiling.

**The pool is shared.** A drain by either EOA does not take only Ripe's
receivable; it takes the pool that every relayer's receivable is claimed
against. Ripe's loss is bounded by what it is owed, but the probability is not
independent of other participants' exposure.

So the two independent numbers are: (1) fronted-unsettled notional and age caps
(M-1), enforced by the filler; and (2) a ceiling on **outstanding Relay
receivable**, also enforced by the filler as a refusal to fill, since Ripe
cannot shrink it from the collection side.

Recommendation: size (2) as an amount the protocol can lose outright without
impairing GREEN's backing, and state it that way in the governance decision
rather than as a liquidity parameter. If no such amount is large enough to make
the lane useful, that is the answer to whether the lane ships.

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
6. For every provider, each address-typed deposit field carrying post-deposit
   authority is asserted equal to the connected signing address, and the client
   refuses to sign otherwise (H-3). Equality, not non-zero.
7. **Reachability, not just per-assertion correctness (H-3).** Obligation 6 is
   satisfiable by a suite that tests each assertion in isolation while a code
   path still reaches the signing call with a field unvalidated — a present but
   bypassable decoder passes such a suite cleanly, and that is the failure mode
   being defended against. The gate must therefore be a negative test: no
   reachable path to signing exists with any enumerated authority field
   unvalidated. Where a route constructs calldata locally rather than decoding
   a provider's (Across `bridgeableToBridgeable`), the equivalent obligation is
   that no provider-supplied bytes reach an address-typed field on that path.

## Sign-off

Not signed off. H-1, H-2, H-3, and H-4 are all unresolved and must be answered
by the design before implementation starts. H-3's rev-4 status of "resolved for
Relay" was wrong and is retracted — Relay carries the same authority-bearing
`depositor` field with an inverted safe value.

H-4 is the one that should be settled first. It is not a design detail to be
refined during implementation — it asks whether the protocol is willing to
place a standing balance in a contract whose withdrawal authority is a single
EOA signature. If the answer is no, H-1's and M-1's filler controls are moot for
Relay, and the retail GREEN lane does not ship in this form regardless of how
well the Ripe-side pieces are built.
