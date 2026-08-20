# Security review — a direct Relay lane for GREEN

Reviewer: Leto
Date: 2026-08-18
Revised: 2026-08-19 (rev 2 — rescoped, H-2 corrected, invariant corrected;
rev 3 — added H-3, post-deposit authority fields;
rev 4 — added H-4 custody exposure;
rev 5 — H-3 Relay resolution retracted, H-4 ceiling corrected to receivable;
rev 6 — bound effective Relay attribution, added live cross-layer privilege graph;
rev 7 — added M-3, token-level denylist for the Across GREEN/RIPE footgun;
rev 8 — added H-5, destination-side stranding on the live CCIP burn/mint path;
rev 9 — added H-6 refill/drain asymmetry and M-4 age-cap liveness trap;
rev 10 — corrected Relay order authorization, reconciliation, and cap semantics;
rev 11 — M-5 routing evidence pinned and claim narrowed; added H-7, H-8, M-6, M-7
against the implemented `FastLaneFloat`)
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

1. Bound the exposure rather than assume immunity: separate per-stage
   notional/age/entry-count health thresholds plus an aggregate hard
   notional/count allocation (see M-1), so a blocked settlement leg is bounded
   rather than open-ended.
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
CCIP. Each stage needs notional, age, and entry-count health thresholds, while a
separate aggregate notional/count allocation remains the hard invariant. A
breaker that only reacts to the destination chain's state is one round-trip too
late.

Recommendation: enforce both ledgers in the payout contract. A new fill fails
closed when stage A would exceed its threshold, either stage is already
unhealthy, or the aggregate hard allocation would be exceeded. A finalized A→B
proof records the remote fact even if it crosses a stage-B threshold, then
atomically pauses the lane; it must not become unrecordable merely because B is
full. The aggregate hard allocation is the loss boundary, while the stage
thresholds identify which recovery path is stalled.

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

The amount policy must include fees, not only `output <= input`. The pinned
Oracle credits the input to the solver and debits each signed fill fee from that
Hub balance. Require every such fee to use the approved origin input
chain/currency and, for the fixed 1:1 ledger, enforce with overflow-safe
arithmetic `output + feeSum == input`. Less creates a refill shortfall; greater
creates provider-custodied receivable that the exposure ledger fails to count.
Any treasury fee subsidy or separately tracked surplus is a different accounting
model and needs explicit budgeting/review
(`relay-protocol-oracle@55b22de`,
`src/services/attestation/index.ts:375-399,1917-1975`).

That order signature is returned to the user at quote time and proves only the
order fields, not a deposit. It cannot by itself authorize payout: otherwise the
quote recipient can claim inventory before depositing. The minimum topology
requires `fill` to be a top-level transaction sent directly by the configured
solver EOA after its service observes the deposit; wrappers, account abstraction,
and delegated EOA code fail closed. Before its HSM/MPC signs that second
transaction, the service must observe a successful finalized event from the
configured Depository and bind chain, contract, token, order id, effective
depositor, actual amount/net fee economics, recipient, and uniqueness. Dust,
wrong-field, duplicate, reverted, pre-finality, and reorged observations
authorize nothing. The current pinned examples also encode
Relay's Router as `output.extraData.fillContract`, and some use unequal minimum
and expected output amounts. A live quote that intentionally binds the Ripe
payout and its exact-output amount policy is therefore an onboarding blocker,
not an assumption the implementation may make.

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

The design therefore carries independent controls: (1) the Ripe-controlled
payout inventory/hot-contract ceiling; (2) a per-fill ceiling; (3) a hard
per-token, per-chain A+B allocation under one common-mode aggregate budget; and
(4) separate notional/age/entry-count health thresholds for the Relay receivable
and end-to-end CCIP backlog stages. The same two admin keys across Base and
Robinhood make provider loss correlated, which is why (3) needs the aggregate
budget.

Independent destination payout contracts cannot atomically observe a cross-chain
aggregate. Implement (3) by partitioning the governance-approved common-mode
budget into hard chain-local allocations whose sum cannot exceed it. Transition
exposure from the Relay-receivable ledger to the CCIP-backlog ledger only through
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

### H-5 — The live CCIP burn/mint path fails unsafely on the destination side

**Severity: High (user funds, live path today). Scope extension: this is the
CCIP RIPE/GREEN lane that is already deployed and proven by four owner
transactions, not a proposed lane. Added rev 8.**

The origin burn is final before any destination condition is evaluated. Traced
through the vendored pool:

- `BurnMintTokenPoolAbstract.lockOrBurn` runs `_validateLockOrBurn` **then**
  `_burn` (`solidity/src/v0.8/ccip/pools/BurnMintTokenPoolAbstract.sol:22-24`).
- `releaseOrMint` runs `_validateReleaseOrMint` **then**
  `IBurnMintERC20.mint(receiver, localAmount)` (`:39-46`), which enters
  `RipeToken.mint` (`contracts/tokens/RipeToken.vy:63`) and then
  `Erc20Token._mint` (`contracts/tokens/modules/Erc20Token.vy:293`).

So the two sides are asymmetric, and the asymmetry is the finding.

**Origin-side conditions all fail before the burn — the user keeps their
tokens:** token `isPaused`, `blacklisted[sender]` or `blacklisted[pool]` on the
inbound `_transfer` (`:207-208`), and the outbound rate limit, which is consumed
inside `_validateLockOrBurn` (`TokenPool.sol:214`) ahead of `_burn`. All safe.

**Destination-side conditions all fail after the burn.** Six of them, each
reverting `releaseOrMint` on RIPE that no longer exists on the origin:

1. **RMN curse** on the destination lane (`TokenPool.sol:230`) — Chainlink's
   control, not Ripe's.
2. **Inbound rate limit** exceeded (`TokenPool.sol:238`).
3. **`RipeHq.mintEnabled == False`** on the destination — `canMintRipe` returns
   `False` at `contracts/registries/RipeHq.vy:392` before it reads any config.
4. **Destination token `isPaused`** — `_mint` asserts it (`Erc20Token.vy:296`).
5. **`blacklisted[recipient]`** on the destination — `_mint` asserts it (`:295`).
6. **Pool loses `canMintRipe`** in the destination `hqConfig` (`RipeHq.vy:397`).

None of the six is visible to the origin chain. `mintEnabled` is chain-local —
the two RipeHq deployments hold independent state — so Base keeps burning and
dispatching while Robinhood is closed.

**The trigger is a routine action, not an attack.** `setMintingEnabled(false)`
is the protocol's standard incident lever; it is what governance reaches for
during bad debt, an oracle fault, or a depeg, none of which are about bridging.
Pulling it strands every in-flight bridge message, and it does so precisely when
the protocol can least absorb a second problem. Condition 5 is worse in one
respect: `setBlacklist` is gated on the **delegated** `canSetTokenBlacklist`
(`Erc20Token.vy:405`), not on `governance()` — so unlike pause (`:589`) and
`setMintingEnabled` (`RipeHq.vy:420`), a non-governance role can strand
in-flight supply.

**Condition 2 is currently latent and the standing recommendation creates it.**
All four pools have rate limiting disabled (`false, 0, 0`) with a zero
`rateLimitAdmin` (`ccip-live-state.md:53`), and this repository's advice is to
set a policy. Note what that does: **an inbound bucket is a stranding trigger,
an outbound bucket is free safety.** Outbound consumes before the burn and
reverts the origin transaction cleanly; inbound consumes after it and reverts
the mint on tokens already destroyed.

Recovery in all six cases requires clearing the destination condition *and* a
manual re-execution of the failed CCIP message. That runbook does not exist and
nobody owns it. Meanwhile global supply is deflated: `_burn` decremented the
origin `totalSupply` (`Erc20Token.vy:316`) and `_mint` never ran, so for a
governance token the holder's weight is gone for the duration.

**Recommendation — the general rule first.** On a burn/mint bridge, every
admission check belongs on the **send** side; the receive side should be as
close to unconditional as the design allows. A destination-side check is not a
safety control, it is a stranding trigger, because the value it would protect
has already been destroyed elsewhere. Concretely:

1. **Size each lane's inbound bucket strictly above its outbound bucket**, so
   anything that can leave can always arrive. This keeps the entire safety
   benefit of rate limiting and removes condition 2. Do not set symmetric
   buckets. For the exact-entry fast-lane refill, also require
   `maxFillAmount` to fit one message under both capacities whenever rate
   limiting is enabled, and under every applicable per-message limit; otherwise
   an admitted entry can be permanently too large to restore even though the
   aggregate bucket policy is asymmetric. Pool-admin changes must pause and
   drain every larger exact-entry refill before lowering either remote
   capacity/limit; a cross-chain monitor pauses new fills on uncoordinated drift.
   Lowering local `maxFillAmount` applies only to new fills and must not
   invalidate restoration of existing larger entries.
2. **Give `setMintingEnabled(false)` a documented bridge interaction.** The
   cheap fix is operational: disable the origin lane first, let the in-flight
   window drain, then disable minting. The alternative — a mint path for the
   registered CCIP pool that bypasses `mintEnabled` — is a contract change that
   deliberately removes the circuit breaker from the bridge, and should not be
   taken without its own review. Prefer the runbook.
3. **Check for in-flight messages before blacklisting a recipient**, and treat
   that as a required step of the delegated procedure, since the authority is
   weaker than governance.
4. **Write the manual-execution runbook and name its owner** before the first
   sized transfer, not after the first stranded one.

Items 1 and 4 are prerequisites to sizing any RIPE transfer beyond the owner's
existing canaries.

### H-6 — `setMintingEnabled(false)` stops the fast lane's refill but not its drain

**Severity: High (float loss during incident response). Applies to the proposed
payout contract composed with the live CCIP lane. Added rev 9.**

It is already recorded that a fast fill never consults `mintEnabled`: the fill is
a plain `safeTransfer`, and `Erc20Token._transfer` (`:202-211`) checks
`isPaused`, blacklist and balance only. The conclusion drawn from that was that
a dedicated lane gate is needed because `setMintingEnabled(false)` no longer
stops cross-chain movement. That is correct but it is only half of the
interaction, and the missing half reverses the sign of the finding.

The destination float is refilled over CCIP, and per H-5 that refill is a
burn/mint transfer whose destination mint enters `RipeToken.mint` →
`RipeHq.canMintRipe` or `GreenToken.mint` → `RipeHq.canMintGreen`. Both return
`False` on `mintEnabled` before reading the caller's token-specific config
(`contracts/registries/RipeHq.vy:377-399`). So the same single action has
opposite effects on the two legs:

| Leg | Path | Effect of destination `mintEnabled = False` |
|---|---|---|
| **Fill** (float out) | `safeTransfer` | **Unaffected — keeps running at full rate** |
| **Refill** (float in) | CCIP `releaseOrMint` → `mint` | **Blocked, and the origin token is already burned** |

**The protocol's emergency lever therefore disables restoration while leaving
the drain running.** The resulting sequence during an incident that has nothing
to do with bridging:

1. Governance disables minting on the destination for an unrelated reason — bad
   debt, an oracle fault, a depeg.
2. Fills continue. The float drains at whatever rate demand sets.
3. Every in-flight and subsequent CCIP replenishment strands (H-5): burned on
   the origin, un-mintable on the destination.
4. Stage-B notional and age climb, since "origin withdrawn, destination
   inventory not yet restored" is exactly the state a stranded refill produces.
5. The stage-B age cap eventually trips and halts the lane — *after* the drain,
   not before it. Unpausing is a governance action, i.e. the same body already
   consumed by the original incident.

**Fix — gate the fill on both, through the token's live HQ.** First require
`token.ripeHq() == expectedHq`, then require
`!lanePaused && RipeHq(expectedHq).mintEnabled()`. `ripeHq` is mutable through
the token's confirmed HQ-change flow; without the equality check, CCIP minting
can move to a new HQ while the payout keeps reading a stale old HQ that still
reports `true`. An HQ change therefore retires this immutable payout and
requires redeployment. The dedicated pause still handles lane-specific
incidents without halting protocol issuance, while `setMintingEnabled(false)`
again stops cross-chain movement. Both staticcalls fail closed.

**Second fix — do not size `maxStageBAge` off the four-point sample.** The
measured CCIP hops are 18m52s–24m46s, but the adjacent Base→Robinhood sequences
1806/1807 were sent 96 seconds apart and arrived 384 seconds apart. Their 4m48s
latency spread is intra-lane, so direction and drift over the hour do not explain
it; the samples are different assets and cannot rule out token/pool-specific
effects. Commit batching is a plausible mechanism, not a proven one, and `24m46s` is the
maximum of four observations rather than a bound or SLA. A stage-B refill is
one relevant hop, so the sum of two opposite-direction samples is not its
parameter either.

The four samples measure only `ccipSend`→destination receipt, while stage B
starts at authenticated `withdrawnAt`. Do not fix a numeric threshold until the
withdrawal finalization/detection, origin-proof generation/delivery and
destination inclusion, rebalancer queue/batch cadence, nonce, submission, and
source inclusion delay before `ccipSend` are also measured,
together with source finality and consecutive-sequence commit/execution timing
across multiple rounds. If that evidence confirms next-round inclusion for
healthy traffic, include a full measured time-to-next-round bound, destination
execution/finality, and margin. A stranded message is not a slow message:
recovery needs the destination condition cleared *and* a manual re-execution,
which is unbounded in wall-clock and currently depends on a runbook that does
not exist (H-5, item 4).

That conflation is itself the defect: a tripped threshold is supposed to mean
"exposure is too large or too old," and here it would mean "a CCIP message
failed." The reconciliation/monitoring model should distinguish **in-flight**
from **known-failed** replenishment and alarm immediately on the latter. There is
no selected authenticated destination failure proof, and a reverting callback
cannot persist its own flag, so the watcher triggers the guardian's existing
pause without clearing exposure; `known-failed` is not writable payout state.
Otherwise a failure ages silently until it presents as a threshold breach with
no indication of cause.

**Third — the fix relocates the harm, it does not remove it, and the two ends
are not equivalent.** A rejected fill strands a user who has already deposited:
Depository deposits are permissionless and there is no permissionless timeout
refund, so the origin leg is irreversible before the destination leg is
attempted. Gating `fill` on `mintEnabled` therefore adds a *new trigger* for
that pre-existing condition — a protocol-wide incident with no bridge component
now rejects fills for users whose deposit cannot be undone.

The fix is still right, because a fully drained float during an incident is the
worse outcome. But the relocation should be recorded as a chosen position, and
the two sides differ in three ways that "the harm moves" understates:

- **Consent and bound.** Ripe's float loss is bounded by caps the protocol
  chose and can absorb — that is precisely what the caps are for. The stranded
  user consented to nothing, is bounded by no cap they can observe, and recovers
  only through Relay's allocator signature, which carries no timeout and no
  obligation to them.
- **Visibility at the moment of decision.** Governance disabling minting during
  an oracle fault is not thinking about the bridge, and nothing on-chain tells
  them how many irreversible deposits are currently in flight. The decision is
  made blind unless the runbook makes it otherwise.
- **What the caps actually bound.** The spec's conclusion that the caps are the
  security boundary is true *for Ripe's float*. This channel is not bounded by
  them at all. The qualifier belongs in the sentence, or the conclusion reads as
  covering an exposure it does not touch.

**Sequencing narrows the residual, and costs nothing.** Ripe cannot stop the
origin deposit — it is permissionless — but Ripe controls admission upstream of
it, because the API/UI quote gate is what puts users on the path. The incident
sequence should therefore be: **close the quote gate, wait out the deposit→fill
window, then disable minting** — the same ordering H-5 requires for the
replenishment leg, and for the same reason. With that sequencing the residual is
not "everyone in flight," it is "users who deposited inside the drain window,
plus users who bypassed quoting entirely." That is a smaller and more honestly
stated number than an unsequenced acceptance, and it is the number the owner
should be asked to accept.

The corresponding runbook obligation is one line: **before `setMintingEnabled(false)`,
read outstanding in-flight deposit notional and count; if nonzero, either wait
out the window or record the accepted stranding.** Without it this finding is
discovered during an incident rather than decided before one.

Note that a quote-side admission threshold narrows this residual but cannot
close it: a quote does not reserve destination capacity, so concurrent quotes
can consume the same headroom, and `mintEnabled` and `lanePaused` are step
functions with no headroom to reserve against in the first place.

### M-4 — The age cap is the one control that can brick the contract enforcing it

**Severity: Medium (liveness, self-inflicted). Implementation trap in the
proposed two-stage ledger. Added rev 9.**

The exposure ledger holds a per-entry `{orderId, amount, timestamp}` so that age
is enforceable rather than only notional, and the age cap is correctly
identified as mattering more than the notional one — Relay's withdrawal is gated
on a vendor signature with no timeout, so *how long* exposure has been
outstanding is the real signal.

Enforcing "no outstanding entry older than `maxAge`" requires the oldest
outstanding entry, and the obvious implementation iterates the entry set on
every `fill`. That is O(n) on the hot path, it grows with volume, and it is
reachable adversarially: a compromised solver key that cannot exceed the
notional cap can still emit many minimum-size fills and raise the cost of every
subsequent `fill` until the lane is unusable. The control most relied upon is
the one whose naive implementation is a self-DoS.

A FIFO head pointer makes it O(1), but only if entries clear in insertion order.
Whether Relay's withdrawals settle in order is not established, and a single
out-of-order settlement forces the head pointer to stall or the code to fall
back to iteration.

**Recommendation: add a third cap — maximum outstanding entry count, enforced
in aggregate at `fill`, not per stage.** Per-stage entry counts are useful
health thresholds, but they cannot carry this guarantee: entries are created
only by `fill`, moved between stages by verified transitions, and removed only
by verified restoration, so an A->B transition changes both per-stage counts
while leaving the total untouched. Worse, a verified transition must remain
recordable even when the destination stage is at its limit — a remote fact
cannot be refused because a local counter is full — so per-stage counts are not
invariants at all and the sum of the two maxima does not bound live storage.
Admission is the only point where entry creation can be refused, so the
aggregate count checked at `fill` is what actually bounds storage and the batch
size `recordWithdrawn`/`recordRestored` must handle. It is O(1) to check. It does **not** make an entry
scan O(1); `fill` still must not scan. Use a structure with direct oldest lookup
and arbitrary removal (for example, a chronological linked list when local
timestamps are sufficient, or an indexed min-heap for authenticated remote
timestamps submitted out of order). This cap is the only one of the three that
protects the contract's own liveness rather than the balance sheet.

**Separately, a framing correction for whoever implements the spec.** Comparing
the signed output payment with the signed input amount is worth keeping, but it
does not establish solvency. Both values are fields in a solver-signed order,
not observations of an origin deposit — the payout contract cannot verify the
deposit happened. Both are therefore attacker-controlled under key compromise
and the check passes trivially when they are equal. Its real value is catching a
*buggy* solver overpaying against a genuine deposit. The aggregate cap remains
the loss boundary.

### M-5 — The Relay swap lane sells GREEN into Ripe's own borrow-rate reference pool

**Severity: Medium (cost transferred to borrowers; not a fund-loss path).
Applies to the swap-lane route that works today, not to the specced inventory
lane. Added rev 10.**

The measured Relay route for GREEN is two swaps around an ETH bridge: on Base
`GREEN --[KyberSwap]--> ETH`, then ETH is bridged, then on Robinhood
`ETH --[0x]--> GREEN`. Relay's solver never touches GREEN. The consequence
already recorded is that a user "bridging GREEN" is really trading against both
pools, and that this breaks the local peg at size. There is a second consequence
that has not been connected, and it lands on Base rather than Robinhood.

Ripe's borrow rate is a function of that pool. `CreditEngine._getDynamicBorrowRate`
(`contracts/core/CreditEngine.vy:1065`) resolves `CURVE_PRICES_ID` from the
`PriceDesk`, reads `CurvePrices.getCurrentGreenPoolStatus()`, and when the
weighted GREEN ratio exceeds `dangerTrigger` applies both a `rateBoost` scaled by
how far past the trigger the pool sits and a `dangerBoost` proportional to
`numBlocksInDanger`. The protocol treats a GREEN-heavy reference pool as
distress and prices credit accordingly. That is the intended design.

**The direction that matters is the one the product wants.** Bridging GREEN
*from Base to Robinhood* — the direction that puts GREEN on the new chain, the
direction a launch would encourage — executes `GREEN -> ETH` on Base, which is a
GREEN sale into the reference pool and moves the ratio toward the trigger. The
reverse direction relieves it. So the flow the product is designed to generate
is the flow that raises borrow rates for every Base borrower, and none of those
borrowers took any action.

**What is not the finding: single-transaction manipulation.** `getCurrentGreenPoolStatus`
does not read spot state. `_getWeightedGreenRatio` (`contracts/priceSources/CurvePrices.vy:1093`)
walks a ring buffer of snapshots chronologically, weights each by its duration,
rejects out-of-order or future updates outright, and skips stale ones. A
flash-loan or single-block imbalance does not move it. That defense is sound and
this finding does not claim otherwise.

The exposure is the opposite shape, which is why the TWAP does not address it: a
sustained product flow is not manipulation, it is a genuine and persistent
imbalance, and a duration-weighted average reports it faithfully. The control
that stops manipulation is silent by design about real pressure.

**Recommendation.** The existing "do not expose the swap lane until the
Robinhood GREEN pool is deep" constraint is correct and should be recorded with
this as its primary justification rather than peg optics alone, because this
consequence is quantifiable and lands on a party who never opted in. Before any
surfacing decision:

1. **Measure the transfer function** — GREEN volume through the swap lane
   against reference-pool ratio movement and the resulting `rateBoost` and
   `dangerBoost` at current configuration. Until that number exists, "small
   transfers are fine today" is a statement about the user's slippage only.
2. **Alarm on the attribution gap.** A rate rise caused by bridge flow is
   indistinguishable on-chain from one caused by market stress, and it is the
   `dangerBoost` term — which accrues with `numBlocksInDanger` and unwinds
   through a separate recovery path with hysteresis — that makes a transient
   flow leave a persistent mark. Operators need to be able to tell the two
   apart before they respond to one as if it were the other.
3. **Treat this as an argument for the inventory lane on its merits.** The
   specced 1:1 filler has no swap legs, so it exerts no reference-pool pressure
   in either direction. That is a real advantage over the swap route
   independent of price impact, and it has not been counted as one.

**Direct routing evidence, and the caveat that bounds it (rev 11).** The
identification is no longer inferred from `router: "kyberswap"`. At Base block
`50,196,592`, live `CurvePrices.greenRefPoolConfig()` returns reference pool
`0xd6c283...459dc` paired with USDC `0x833589...2913`, and the sampled Relay
quote's nested Kyber calldata contains that exact pool address immediately
followed by that USDC address. The sampled route therefore does sell GREEN
through the borrow-rate reference pool as a matter of decoded calldata.

The claim is correspondingly narrowed: this is proven of **the sampled live
route**, not of "the swap lane" as a class. Kyber routing is dynamic and a
future quote may select a different pool — which cuts both ways, since it also
means a route measured clean today can select the reference pool tomorrow. The
durable control is therefore not "check whether the quoted path touches
`0xd6c283...`" but the route-shape refusal recorded in the fast-lane doc:
reject protocol-token swap legs outright, or recursively decode and validate
every quoted path before admission.

**The pressure is live on the current Base deployment, and the pool is small.**
Verified by direct `eth_call` at Base block `50,180,753`:
`getCurrentGreenPoolStatus()` reports `weightedRatio = 50.61%` against
`dangerTrigger = 60.00%` with `numBlocksInDanger = 0`, and the reference pool
holds roughly 6,073 USDC / 5,809 GREEN (~$11.9k, `A = 100`). A 9.4-point gap on
a pool that size puts the trigger within reach of ordinary bridging volume
rather than of an attacker — but that reach is a StableSwap sanity check, not a
simulation, and item 1 below is what turns it into a number.

Note this is a Base-side finding reached from Robinhood work, and it is
unaffected by every bridge control in this review: no cap, pause, allowlist or
denylist here touches it, because nothing about it is a bridge transaction from
Ripe's contracts' point of view.

### H-7 — Every immediate emergency lever in `FastLaneFloat` is undone in one transaction by a pre-staged timelock action

**Severity: High (defeats the incident-response model; no key compromise
required beyond the one the levers exist to answer). Added rev 11. Reproduced
by `tests/core/test_fast_lane_float_audit.py`.**

`FastLaneFloat` splits its controls into fast levers that only ever tighten
(`pauseLane`, `clearSolverSigner`, `lowerCaps`, `raiseFloatFloor`) and slow
levers that loosen and must pass the timelock (`ACTION_UNPAUSE`,
`ACTION_SET_SOLVER`, `initiateCapRaise`, `ACTION_LOWER_FLOOR`). The split is the
right shape. The timelock does not implement it.

`timeLock._initiateAction` (`contracts/modules/TimeLock.vy:65`) stamps
`confirmBlock = block.number + actionTimeLock` and
`expiration = confirmBlock + self.expiration` at **initiate** time. The float
constructs the module as `timeLock.__init__(_minTimeLock, _maxTimeLock,
_minTimeLock, _maxTimeLock)`, so `expiration == _maxTimeLock`: once matured, an
action stays confirmable for a further `_maxTimeLock` blocks. Nothing in
`confirmChange` re-reads the state the action loosens. So for that entire
window the "delay" on loosening is zero, and the only question is whether a
matured action happens to be sitting there.

Three instances, each proven:

- **`ACTION_UNPAUSE` vs. the guardian pause.** A guardian halts the lane; one
  `confirmChange` of a previously-staged unpause reopens it in the same block.
  `test_poc_f1_stale_unpause_defeats_guardian_pause`.
- **`initiateCapRaise` vs. `lowerCaps`.** `lowerCaps` is the only immediate
  lever that tightens the loss bound, and the caps are stated as the security
  boundary. A matured raise restores the pre-incident caps with **no**
  re-validation — not against live exposure, not against the values just set.
  `test_poc_f1c_stale_cap_raise_undoes_emergency_lower_caps`.
- **`ACTION_SET_SOLVER` vs. `clearSolverSigner`.** A guardian burns a
  compromised solver key; a matured set-solver reinstates it immediately. See
  H-8 for what that costs.

Two aggravating details. Guardians can pause and clear but **cannot cancel** —
`cancelChange` requires `gov._canGovern`, so the party trusted to react fastest
cannot neutralise the thing that reverses its reaction. And this is invisible
in review: the staged action is initiated during ordinary operations, long
before the incident, and looks like routine maintenance at the time.

The existing tests do not catch it because they only exercise the intended
ordering — `test_unpause_requires_the_timelock` initiates *after* the pause and
correctly observes the delay. The defect is in the other ordering.

**Recommendation.** Bind each pending action to the state it loosens, at
confirm time rather than initiate time. Cheapest correct form: keep a
monotonic `controlEpoch`, bump it in `pauseLane`, `clearSolverSigner` and
`lowerCaps`, stamp it into `PendingChange` at initiate, and reject
`confirmChange` when it no longer matches. That makes every tightening action
automatically invalidate every staged loosening, without enumerating which
action loosens what — the enumeration is precisely what has decayed twice
already in this review. Additionally, let guardians call `cancelChange`;
cancelling is a tightening operation and belongs with the other fast levers.

### H-8 — Reinstating a cleared solver signer revives its entire unfilled pre-signed backlog

**Severity: High (direct fund-loss path, bounded only by the caps). Added
rev 11. Reproduced by `tests/core/test_fast_lane_float_audit.py`.**

Independent of H-7, and it survives a fully-elapsed timelock.

`fill` protects against replay with `isFilled[orderId]`, which records only
orders that were **filled**. An order that was signed and never submitted
leaves no trace. Two other properties make that permanent: `_order.deadline` is
checked (`block.timestamp <= _order.deadline`) but **not bounded**, so a signer
can mint orders valid for centuries; and clearing `solverSigner` invalidates
nothing at order level, because validity is recomputed against whatever address
is configured at fill time.

So the response to a solver-key compromise is incomplete by construction.
`clearSolverSigner` stops the bleeding while the address is unset. The moment
governance restores that same address — after remediation, believing the
incident closed, or via a stale H-7 action — every order the attacker signed
during the compromise becomes live again, and can be drained straight into the
caps.
`test_poc_f2_stale_set_solver_revives_presigned_orders` walks it: three
max-size orders signed up front, the signer cleared, fills reverting, then a
single `confirmChange` followed by all three filling for `3 x maxFillAmount`.

**Recommendation.** Two changes, both small:

1. **Version the signer.** Keep `signerEpoch`, increment it in
   `clearSolverSigner` and on every `ACTION_SET_SOLVER` confirmation, and
   include it in `ORDER_TYPEHASH`. Clearing the signer then invalidates every
   outstanding signature by that key permanently, and reinstating the address
   does not revive them.
2. **Bound the deadline.** Reject `_order.deadline > block.timestamp +
   MAX_ORDER_HORIZON`. A fast lane quotes in seconds; an order valid for more
   than a few minutes has no legitimate use and is only ever a bearer
   instrument someone can stockpile.

### M-6 — `pauseLane` does not stop value leaving, and `ACTION_WITHDRAW` ignores the drain floor

**Severity: Medium. Added rev 11. Reproduced by
`tests/core/test_fast_lane_float_audit.py`.**

`minFloatBalance` was added (H-6 follow-up) to halt the drain at a chosen floor
"whatever the cause". It is enforced in `fill` and in `canFill`, and nowhere
else. `confirmChange`'s `ACTION_WITHDRAW` branch transfers `p.numVal` to
`FLOAT_RECIPIENT` with no check against `minFloatBalance` and none against
`outstandingNotional`. The floor is therefore cause-agnostic only across the
causes that flow through `fill`.

Compounding it, `lanePaused` gates `fill` alone. A guardian pause is the signal
"stop, something is wrong", and it leaves a matured withdrawal fully
confirmable.
`test_poc_f3_paused_lane_still_confirms_full_withdrawal_below_floor` pauses the
lane and then empties the contract to zero against a floor of 1,000e18, while
entries are outstanding.

Governance being able to recover inventory is legitimate and should stay. The
defect is that it is not visibly separated from the floor's stated guarantee,
and that a pause does not hold it. **Recommendation:** require
`balance - amount >= minFloatBalance` for withdrawals below the floor to go
through an explicitly-named second action type rather than silently through the
ordinary one; require `outstandingEntries == 0` for a full sweep; and refuse
`ACTION_WITHDRAW` confirmation while `lanePaused` is set, so that halting the
lane halts every outflow rather than one of them.

### M-7 — The drain floor is the one cap that can be deployed inert

**Severity: Medium. Added rev 11. Reproduced by
`tests/core/test_fast_lane_float_audit.py`.**

The constructor asserts every other bound non-zero — `_maxOutstandingEntries !=
0`, `_maxFillAmount != 0 and _maxAggregateExposure != 0 and _maxEntryAge != 0`
— and omits `_minFloatBalance`. A deployment that passes `0` compiles, deploys
and passes the entire existing suite with the floor disabled
(`test_poc_f4_floor_can_be_zero_at_deploy`). `ACTION_LOWER_FLOOR` can likewise
take it to zero, since `assert _numVal < self.minFloatBalance` admits `0`
(`test_poc_f4_floor_can_be_lowered_to_zero`).

This matters more than an ordinary parameter check because of what the floor is
for. It exists precisely because the enumerated liveness gates were found
incomplete — it is the control that catches the causes nobody listed. A control
of that kind failing silently open at deploy time is the worst available
failure mode, and there is no runtime signal: `isHealthy()` does not consider
the floor at all.

**Recommendation.** Assert `_minFloatBalance != 0` in the constructor alongside
the other caps, require `ACTION_LOWER_FLOOR` to keep it non-zero, and include
`balance >= minFloatBalance` in `isHealthy()` so an inert or breached floor is
externally observable.

## Test obligations

Whatever design lands, these must be red-before-green:

1. Fill reverts when the dedicated bridge gate is off (H-1).
2. Fill reverts when recipient, float, or settlement address is blacklisted
   (H-2).
3. New fills fail closed at the stage-A health thresholds and aggregate hard
   allocation. A verified A→B proof that crosses a stage-B threshold records the
   transition and pauses; it never releases, loses, or double-counts exposure
   (M-1).
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
    receiver can lose at most the already-reserved receivable allocation. The
    quote recipient and any wrapper cannot call `fill`; only a top-level call
    from the configured solver EOA after its independent deposit observation is
    admitted.
12. `deposit` of GREEN or RIPE into a listed Across SpokePool reverts at the
    token, on a fork, from an address holding no Ripe privilege and using a
    transaction Ripe's frontend did not construct — the third-party path, which
    is the only one the client allowlist cannot reach (M-3). A companion test
    proves the CCIP token pool is *not* blacklisted, so the approved route still
    mints and burns.
13. On a fork, with a RIPE CCIP transfer already burned on the origin, each of
    the six destination conditions is asserted to revert `releaseOrMint`
    individually: RMN curse, inbound rate limit, `mintEnabled == False`,
    destination `isPaused`, blacklisted recipient, and a pool `hqConfig` entry
    without `canMintRipe` (H-5). Each case asserts origin `totalSupply` already
    decreased, proving the burn is unrecoverable by revert.
14. For every configured lane, inbound bucket capacity and rate are strictly
    greater than the same lane's outbound bucket, asserted against live pool
    config rather than intended config (H-5). This is the invariant that keeps a
    rate-limit policy from becoming a stranding trigger, and it silently breaks
    whenever either side is retuned alone. For a fast-lane refill, separately
    assert `maxFillAmount` fits one message under both enabled capacities and
    every applicable per-message limit.
15. With destination `mintEnabled == False`, `fill` reverts (H-6). The paired
    negative test is the one that fails today: assert that a fill *succeeds*
    when the gate reads `lanePaused` alone, proving the coupling is what closes
    it rather than some incidental check. After `token.confirmHqChange`, the old
    payout also reverts even if its stale expected HQ still reports
    `mintEnabled == True`.
16. A drain scenario, not a unit assertion: create N fills and dispatch their
    refills while minting is enabled, then disable destination minting so those
    in-flight refills strand. Assert every subsequent fill attempt reverts and
    the float cannot drain beyond the already-reserved exposure (H-6).
17. `fill` performs no linear scan over outstanding entries (M-4): exercise one
    entry and the maximum entry count, then assert gas stays within the audited
    bound of the selected O(1) / O(log `maxEntries`) structure. A gas-griefing
    test using minimum-size fills from a valid solver signature must not be able
    to raise `fill` cost without the configured bound.
18. The data-bearing CCIP rebalancer pins out-of-order execution on every refill.
    A proof-order race may make one callback fail pending manual re-execution;
    that failed message cannot head-of-line block later independent refills.
19. Incident-sequencing rehearsal, not a contract test (H-6): from a state with
    open quotes and deposits inside the deposit-to-fill window, the runbook's
    ordering — close the quote gate, drain the window, then disable minting —
    is executed end to end, and the count of users stranded is recorded. The
    same rehearsal run in the reverse order establishes the delta the owner is
    accepting. A runbook whose stranded count has never been measured is an
    assumption, not a control.

## Sign-off

Not signed off. **Eight highs open, seven mediums.**

`FastLaneFloat` (`contracts/core/FastLaneFloat.vy`, head `80e15c8`) is code now,
not a specification, and the four findings added in rev 11 are against the
implementation rather than the design. Its own suite is 34 green; that number
establishes the implemented behaviour matches the implementer's model of it, and
H-7 and H-8 are both cases where that model is the thing at fault, so a green
suite is not evidence against them. Each is reproduced in
`tests/core/test_fast_lane_float_audit.py`, red against the current contract.

H-7 and H-8 together mean the contract's incident response does not currently
work: the fast levers can be reversed in one transaction (H-7) and clearing a
compromised signer is not durable (H-8). Both are cheap to fix — one epoch
counter each — and both must land before the contract holds value, because
neither is detectable after the fact from the contract's own state.

Not signed off. H-1, H-2, and H-4 remain unresolved owner decisions. H-3's
rev-4 rationale was wrong and is retracted; the required answer is now the
effective-depositor and complete-order admission rule above, but H-3 remains an
implementation/admission blocker until the exact GREEN route is enumerated and
tested. No implementation or live GREEN-route conformance evidence exists yet.

H-6 is the finding to act on while the payout contract is still a specification
rather than code, because its fix is one clause in one check and its cost after
the fact is float. It also demonstrates why the two lanes cannot be reviewed
separately: the fill path and the refill path were each assessed correctly in
isolation, and the defect is only visible when a single governance action is
applied to both at once.

Its fix is not free, and the cost lands on someone who did not choose it: gating
`fill` on `mintEnabled` converts a float drain into stranded user deposits that
no cap bounds. That trade is the right one, but it is an owner acceptance rather
than a resolved finding, and it is only correctly sized once the quote-gate-first
sequencing above is the assumed procedure. Sign-off on H-6 means accepting a
measured stranded-user count, not accepting that the code change is sufficient.

H-5 applies to the lane the owner is already using, which makes it the only
finding here that is not contingent on a future decision. It does not block the
canaries already performed, but obligations 13 and 14 plus the manual-execution
runbook should land before any sized RIPE transfer, and the inbound/outbound
asymmetry should be settled in the same governance action that sets rate limits
at all — otherwise the fix for one gap installs the other.

M-3 is the cheapest item on this list and the only one that closes a live
exposure rather than gating a future one: the Across GREEN/RIPE footgun is
reachable today, through paths Ripe's frontend does not mediate, and the control
is a transaction Ripe can send unilaterally. It should not wait on the Relay
decisions below.

H-4 is the one that should be settled first. It is not a design detail to be
refined during implementation — it asks whether the protocol is willing to
accept full, instant loss of the capped outstanding Relay receivable under two
Relay EOA authorities, including one cross-layer superadmin, plus the required
Ripe solver EOA. Destination inventory remains contract-controlled, but that
does not restore value already fronted. If the answer is no, H-1's and M-1's
payout controls are moot for Relay, and the retail GREEN lane does not ship in
this form regardless of how well the Ripe-side pieces are built.
