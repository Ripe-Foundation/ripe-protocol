# Security review — a direct Relay lane for GREEN

Reviewer: Leto
Date: 2026-08-18
Revised: 2026-08-18 (rev 2 — rescoped, H-2 corrected, invariant corrected;
rev 3 — added H-3, post-deposit authority fields;
rev 4 — added H-4 custody exposure;
rev 5 — H-3 Relay resolution retracted, H-4 ceiling corrected to receivable;
rev 6 — bound effective Relay attribution, added live cross-layer privilege graph;
rev 7 — added M-3, token-level denylist for the Across GREEN/RIPE footgun)
Scope: the trust boundaries a direct, liquidity-based GREEN bridge lane would
touch on Base <-> Robinhood Chain. Reviewed against `rh` at `2985e73`.

Across token bridging for GREEN/RIPE has been rejected, so this review is
scoped to a **direct Relay lane**. H-1, H-2, and the medium findings are
properties of the *fast-fill-from-float* shape and apply to any future
liquidity-based lane. H-3 and H-4 are provider-specific. The original
RipeHq-side review did not audit Relay's contracts; those two findings now
consume the separate pinned-source and live privilege evaluation in
`relay-settlement-evaluation.md`.

Out of scope: the local-mint acquisition flow. That is a separate product path,
not a GREEN transfer route. RIPE has no fast lane in the selected venue-first
sequence and remains on CCIP only.

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

Recommendation: the payout component must be a Ripe-controlled contract reading a
Ripe-controlled gate, and it must fail closed. Prefer a **dedicated bridge
switch** over reusing `mintEnabled`, so the lane can be stopped without halting
borrowing and rewards. If a permissionless third-party solver market is ever
enabled for GREEN/RIPE, it must be documented as an outflow channel governance
**cannot** stop short of a token-wide pause.

Note for the float design: `Endaoment` is already a `canMintGreen` department.
If it is also the float holder, payout logic executes inside a contract that
holds mint authority — the blast radius of a fill bug is then minting, not just
inventory. Prefer a separate, non-mint-authorized payout contract funded by
Endaoment, so the fast lane never shares an address with mint rights. Relay's
pinned order format separately requires the solver identity to be an EVM EOA;
that signer must never be sufficient to move payout inventory.

### H-2 — Blacklist can block settlement indefinitely and move the exposure onto Ripe

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
instantly from float, so it is *Ripe's* rebalancing leg that is blocked. If the
float or settlement address is blacklisted — including by mistake, or by a
`canSetTokenBlacklist` department acting on a heuristic — the canonical leg
backing already-fronted fills is blocked until governance clears the flag, and
fronted capital sits unrecovered for that entire window.

A sharper tail risk: `burnBlacklistTokens` (`Erc20Token.vy:415-422`) lets
governance burn a blacklisted address's **entire balance**. A blacklisted float
address is therefore not merely blocked — its inventory is destroyable by a
single governance call.

Recommendation, in order of preference:

1. Bound the exposure rather than assume immunity: separate hard notional and
   age caps for the Relay receivable and the CCIP rebalancing backlog (see M-1),
   so a blocked settlement leg is capped rather than open-ended.
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

The circuit breaker for this must be driven by the *observed end-to-end fill
lifecycle* and act on the **send** side. Track its two stages separately:
(a) destination value paid but the origin Relay receivable not yet withdrawn,
and (b) origin value withdrawn but destination inventory not yet restored through
CCIP. Each stage needs a hard notional cap and maximum age. A breaker that only
reacts to the destination chain's state is one round-trip too late.

Recommendation: enforce both ledgers in the payout contract and fail closed when
either would exceed its notional or age bound. These caps are also the bound that
makes H-2 tolerable; one aggregate number must not hide which recovery path is
stalled.

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

### M-3 — Rejecting GREEN/RIPE at Ripe's boundary does not prevent the deposit

**Severity: Medium (user funds, no attacker profit). Mitigation available and
unilateral; not yet specified anywhere. Added rev 7.**

`across-settlement-evaluation.md` establishes that `SpokePool._depositV3`
performs no input-token allowlist check, that route enablement is dead code
(`SpokePool.sol:92`), and that `deposit(GREEN, ...)` therefore **succeeds
on-chain** and is then unrecoverable absent Across admin action. The synthesis
answers this with fail-closed allowlists at the API and client boundaries.

Those controls are correct and necessary, but they are **path-scoped**: they
govern transactions Ripe's own frontend constructs. They do not govern Across's
own app, third-party aggregators, or a direct `eth_sendTransaction` to the
SpokePool. Those paths are live today and reach the same footgun.

The reason this matters more than its likelihood suggests is that the failure is
**indistinguishable from a correct transaction at signing time**: a genuine,
verified Across SpokePool, a real function, the user's own address as recipient.
Every heuristic a careful user applies returns "safe". User vigilance is
therefore not an available control, which makes a phishing page presenting
itself as a Ripe fast lane an unusually well-disguised griefing vector — the
attacker does not extract the funds, but GREEN is what looks broken.

**Ripe already owns a control that covers every path.** GREEN and RIPE both
initialize `Erc20Token` (`contracts/tokens/GreenToken.vy:38`,
`contracts/tokens/RipeToken.vy:38`), which carries a recipient-side denylist:

- `_transfer` asserts `not self.blacklisted[_recipient]`
  (`contracts/tokens/modules/Erc20Token.vy:208`);
- `transferFrom` additionally asserts `not self.blacklisted[msg.sender]`
  (`:195`), and the SpokePool *is* `msg.sender` for its own
  `safeTransferFrom` pull.

Blacklisting the SpokePool address therefore makes `deposit(GREEN, ...)` revert
at the token, converting a silent stranding into a clean on-chain failure —
with no Across governance dependency and no change to any Ripe contract.

**Blacklisting the terminal sink is sufficient; peripheries need not be
enumerated.** Every deposit path, however many hops precede it, must ultimately
land GREEN in the SpokePool. A periphery contract's own inbound leg succeeds and
its onward transfer to the SpokePool trips the recipient check, so the composite
call still reverts. This is the property that makes the control tractable.

Three constraints govern how it should be used:

1. **It is a denylist and fails open.** An Across SpokePool on a chain nobody
   listed is not covered. This is a complement to the client-side allowlist,
   which is fail-closed by construction, not a replacement for it. The reason to
   hold both is that they cover disjoint paths, not that either is redundant.
2. **It blocks the exit as well as the entrance** (`:207`, sender side). Applied
   *before* any GREEN reaches the SpokePool it is purely preventive. Applied
   *after*, it converts "stranded pending Across DAO action" into "stranded
   permanently", recoverable only by governance burn and re-mint. Ordering is
   the whole difference; this should be a launch-time action, not an incident
   response.
3. **It confers a new governance power over a third party's balance.**
   `burnBlacklistTokens` (`:415`) is gated on `msg.sender == governance()` — a
   stricter gate than `setBlacklist`'s delegated `canSetTokenBlacklist` (`:405`),
   so the blacklist-setter cannot burn and the privilege split is sound. But any
   GREEN already at a blacklisted SpokePool becomes governance-burnable. For
   stranded funds that is arguably the desired remedy; it should still be an
   explicit decision rather than a side effect.

**Recommendation.** Blacklist the Across SpokePool address on every chain where
GREEN or RIPE is deployed, as a pre-launch action, and add newly onboarded
chains to the same list. Do not blacklist the CCIP token pool — that is the one
approved route, and an operational error here breaks it. Record the denylist as
a standing obligation with an owner, since its fail-open direction means it
decays silently as Across deploys new chains.

### H-3 — Provider deposit authority must resolve to the connected wallet

**Severity: High (funds at risk). Required control identified; unresolved until
the exact GREEN quote/order schema is enumerated and the control is implemented.
Added rev 3.**

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

**Two independent pre-sign controls are required.** The later rewrite is a
separate off-chain signature plus a relayer's choice of fill function, so the
deposit contract cannot prevent it. But the address that receives that authority
*is* visible in the deposit calldata. An honest quote proxy must decode and reject
an attacker-named depositor first; the browser repeats the semantic check against
the values it rendered so a buggy or compromised proxy cannot attest to its own
malicious output. Both refuse before signing. The browser check is independent,
not the sole control; an on-chain depositor-to-payer binding does not exist.

**The rule, applied per provider, is:** enumerate every address-typed field in
the deposit payload; for each, determine whether it carries any authority after
the deposit lands — amendment, cancellation, refund receipt, speed-up,
delegation; then prove its **effective** beneficiary or authority is the
connected signer. An explicit address must equal the signer, not merely be
non-zero. A sentinel is acceptable only when the exact call frame proves it
resolves to that signer.

**Relay-specific correction — rev 4's reasoning was wrong and is retracted.** Rev 4 stated
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

Funds come from `msg.sender`; the attribution address is caller-supplied; the
Hub derives order ownership, recovery, and withdrawal paths from that event.
Naming an attacker changes the Hub attribution even though the Depository stores
no per-user balance. Same authority class as Across, with different mechanics.

**The zero sentinel is safe only in a direct call.** For Relay,
`address(0)` resolves to the inner call's `msg.sender`. That is the connected
wallet when it calls the Depository directly; through a router or multicall it
is the intermediary contract. Across has no equivalent safe sentinel: zero
burns the refund leg. So:

| | Across | Relay |
| --- | --- | --- |
| Safe values | `depositor == connected` only | effective depositor equals connected; explicit equality is preferred |
| Zero | unsafe | allowed only when the connected wallet directly calls the Depository |
| `depositor != 0` as a check | wrong — the attack is non-zero | incomplete — does not prove effective attribution |

This is the strongest argument for the enumeration rule being *per provider*
rather than a shared checklist. A control correct for one provider is wrong for
the other in both directions, and the failure is silent. An implementer who
generalizes the Across rule to Relay writes a check that rejects safe deposits;
one who treats zero as universally safe for Relay can credit an intermediary.

For a direct Relay ERC-20 deposit, allow only the explicit-amount
`depositErc20(address,address,uint256,bytes32)` selector `0xe8017952`; reject the
full-allowance overload `0x5a1ee3ac`. The quote must include signed protocol
data: schema-decode the order, recompute its id, bind calldata `id` to that
order, verify the configured Ripe solver-EOA signature, and assert every input,
output, refund, call, deadline, fee, and extra-data field against the rendered
terms.
Unknown order versions, raw transfers, deposit-address routes, and unenumerated
periphery calls fail closed.

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


### H-4 — Relay receivables are exposed to three EOA authority roots

**Severity: High (funds at risk). Unresolved. Added rev 4.**

**Correction (rev 5): the exposure is the receivable, not the inventory.** Rev
4 described Ripe's destination inventory as "standing float parked in Relay's
Depository." That is not the flow. In Relay's model the payout contract holds
destination inventory in Ripe's custody and pays the user; the Depository holds
the *user's* origin-chain deposit, which Ripe later collects. So what Ripe
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

The same owner EOA is also a cross-layer superadmin. Live Relay-chain queries
confirmed that `0xF61A...775A` owns the 2-of-5 Oracle multisig, administers the
Oracle and Hub roles, and already holds Hub `OPERATOR_ROLE`. It can change the
multisig signer set or threshold, grant roles, directly mint/burn Hub balances,
replace RelayAllocator payload builders, suspend a solver alias, and then
repoint the Depository allocator. The 2-of-5 normal path is real, but it is not
a security boundary against compromise of this EOA. The separate allocator EOA
can independently authorize arbitrary Depository calls.

The pinned order path requires a **Ripe solver EOA** as a third authority root.
The Oracle credits fills to that EOA's Hub alias, and `RelayAllocator` lets the
20-byte spender submit a withdrawal with a caller-chosen receiver. The Ripe
payout contract can stop a compromised solver signer from moving destination
inventory only by independently revalidating every order; it cannot stop that
signer from redirecting the outstanding Hub receivable. Require audited HSM/MPC
custody and explicit full-receivable-loss acceptance, or stop until Relay
supports ERC-1271 solvers or restricts the receiver on-chain.

Two amplifiers that survive the correction and make the smaller number harder to
manage than it looks:

**Ripe cannot collect unilaterally.** The only exit from the Depository is
`execute(CallRequest, signature)` gated on `allocator.isValidSignatureNow`.
There is no autonomous depositor-controlled refund or exit path; recovery still
ends in allocator-authorized `execute`. So the *age* of Ripe's receivable is set
by Relay's willingness to sign, not by Ripe's
reconciliation cadence. "Withdraw more often to keep the exposure small" is not
a control Ripe holds — which means the cap has to be enforced where Ripe does
have control: by the payout contract declining to fill once the outstanding receivable
reaches the ceiling.

**The pool is shared.** A drain by either Relay EOA does not take only Ripe's
receivable; it takes the pool that every relayer's receivable is claimed
against. Ripe's loss is bounded by what it is owed, but the probability is not
independent of other participants' exposure.

The design therefore carries three independent numbers: (1) the Ripe-controlled
payout inventory/hot-contract ceiling; (2) a per-token, per-chain **and
aggregate** ceiling plus maximum age for outstanding Relay receivables; and (3)
the end-to-end CCIP rebalancing backlog notional and age caps from M-1. The same
two admin keys across Base and Robinhood make provider loss correlated, which is
why (2) needs an aggregate bound.

Independent destination payout contracts cannot atomically observe a cross-chain
aggregate. Implement (2) by partitioning the governance-approved common-mode
budget into hard chain-local allocations whose sum cannot exceed it. Transition
capacity from the Relay-receivable ledger to the CCIP-backlog ledger only through
a separately reviewed proof/coordinator that verifies origin finality, replay,
and chain/domain binding. A provider API or unsigned indexer status cannot release
exposure. That transition mechanism remains an implementation gate.

Recommendation: size (2) as an amount the protocol can lose outright without
impairing GREEN's backing, and state it that way in the governance decision
rather than as a liquidity parameter. Request withdrawals immediately, but do
not call cadence a unilateral mitigation: Relay controls the signature needed
to collect. Require a vendor answer on both Relay EOAs' custody and whether the
roles will move to isolated, delayed multisig control or a token-isolated
Depository. Separately approve the Ripe solver EOA's HSM/MPC policy and
receiver-redirection risk. If no accepted full-loss amount is large enough to
make the lane useful, the lane does not ship.

## Test obligations

Whatever design lands, these must be red-before-green:

1. Fill reverts when the dedicated bridge gate is off (H-1).
2. Fill reverts when recipient, float, or settlement address is blacklisted
   (H-2).
3. Relay-receivable and CCIP-rebalancing notional/age caps each fail closed and
   cannot release or double-count exposure across the stage transition (M-1).
4. Invariant: the set of addresses satisfying `RipeHq.canMintGreen` /
   `canMintRipe` is unchanged by the Relay integration — specifically, no
   filler, float, settlement, or Relay-owned address joins it. Assert against
   the enumerated department set above plus the registered CCIP pools; do
   **not** assert that only the pools can mint, which is false today (M-2).
5. Token pause halts the fast lane as well as the canonical lane.
6. For every provider, the effective beneficiary of each address-typed field
   carrying post-deposit authority is proven to be the connected signer, and
   the client refuses to sign otherwise (H-3). Explicit fields require equality;
   sentinels require proof of their call-frame semantics.
7. **Reachability, not just per-assertion correctness (H-3).** Obligation 6 is
   satisfiable by a suite that tests each assertion in isolation while a code
   path still reaches the signing call with a field unvalidated — a present but
   bypassable decoder passes such a suite cleanly, and that is the failure mode
   being defended against. The gate must therefore be a negative test: no
   reachable path to signing exists with any enumerated authority field
   unvalidated. Where a route constructs calldata locally rather than decoding
   a provider's (Across `bridgeableToBridgeable`), the equivalent obligation is
   that no provider-supplied bytes reach an address-typed field on that path.
8. Across v1 accepts only plain `deposit(...)` selector `0xad5425c6`, requires
   `message == 0x`, and rejects `unsafeDeposit(...)` selector `0x8b15788e` at
   every nesting level. A negative reachability test proves there is no signing
   path for `unsafeDeposit` or a non-empty message.
9. Relay allows only explicit-amount ERC-20 deposit selector `0xe8017952`; the
   full-allowance overload `0x5a1ee3ac`, opaque orders, and unenumerated route
   shapes cannot reach signing. Order id, effective depositor, configured solver
   signature, refund authority, and all rendered terms are bound.
10. Relay receivable accounting refuses a fill when its chain-local allocation
    or maximum age would be exceeded; configured allocations cannot sum above
    the aggregate full-loss budget. Forged, replayed, stale, or wrong-chain
    transition evidence cannot release exposure. Ripe-controlled destination
    inventory is not counted as provider custody.
11. A valid signature from the configured Ripe solver EOA is insufficient by
    itself to move payout inventory: the contract independently revalidates the
    order, pause, limits, recipient, and exact amount. A hostile withdrawal
    receiver can lose at most the already-reserved receivable allocation.

## Sign-off

Not signed off. H-1, H-2, and H-4 remain unresolved owner decisions. H-3's
rev-4 rationale was wrong and is retracted; the required answer is now the
effective-depositor and complete-order admission rule above, but H-3 remains an
implementation/admission blocker until the exact GREEN route is enumerated and
tested. No implementation or live GREEN-route conformance evidence exists yet.

H-4 is the one that should be settled first. It is not a design detail to be
refined during implementation — it asks whether the protocol is willing to
accept full, instant loss of the capped outstanding Relay receivable under two
Relay EOA authorities, including one cross-layer superadmin, plus the required
Ripe solver EOA. Destination inventory remains contract-controlled, but that
does not restore value already fronted. If the answer is no, H-1's and M-1's
payout controls are moot for Relay, and the retail GREEN lane does not ship in
this form regardless of how well the Ripe-side pieces are built.
