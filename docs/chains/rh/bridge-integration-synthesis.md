# Bridge integration synthesis — Base and Robinhood Chain

**Status:** Recommendation and implementation gates only. Evidence accepted;
Relay design not signed off. No onboarding, deployment, role change, signing,
transaction, or production integration is authorized.

**Date:** 2026-08-18

**Repository baseline:** `rh` at `2985e73`

**Scope:** moving Ripe collateral and the GREEN/RIPE protocol tokens between
Base (8453) and Robinhood Chain (4663) using CCIP, Across, or Relay.

Source records:

- [`ccip-live-state.md`](ccip-live-state.md)
- [`across-settlement-evaluation.md`](across-settlement-evaluation.md)
- [`relay-settlement-evaluation.md`](relay-settlement-evaluation.md)
- [`bridge-integration-security-review.md`](bridge-integration-security-review.md)
- API/web implementation plan: [Ripe API PR #30](https://github.com/Ripe-Foundation/api/pull/30)

## Recommendation

Do not replace CCIP with one generic fast bridge. The products and settlement
models are different:

| Product | Assets | Selected rail | Current disposition |
| --- | --- | --- | --- |
| Acquire collateral on Robinhood | USDC -> USDG, WETH -> WETH | **Across** | Available fast v1, two-step to the wallet and then into Ripe |
| Transfer GREEN/RIPE directly today | GREEN, RIPE | **CCIP** | Live canonical route; four owner-supplied messages prove successful automatic execution for both tokens in both directions |
| Optional fast protocol-token lane | GREEN, RIPE | **Relay with a Ripe payout contract + solver EOA** | Technically applicable to either token; blocked on the same H-1/H-2/H-4 owner gates plus H-3 engineering proof |
| Across protocol-token lane | GREEN, RIPE | **Across after formal token onboarding** | Not a unilateral Ripe integration: requires an Ethereum settlement representation, compatible canonical-bridge adapters/routes, and Across DAO configuration |

Across is already usable because its live Robinhood asset set matches Ripe's
selected collateral set. The currently deployable integration moves collateral,
not protocol tokens. A user can bridge USDC or WETH, deposit locally, and borrow
or mint GREEN on Robinhood without moving GREEN across a bridge:

```text
Base USDC/WETH -> Across -> Robinhood USDG/WETH -> user wallet
    -> existing Ripe deposit flow -> local GREEN issuance
```

That is a collateral-acquisition flow. It is not a faster GREEN bridge and must
not be presented as one.

It is also a launch-sequencing recommendation, not a currently usable Ripe flow:
the non-CCIP Robinhood deployment is not yet ready, and the USDG PSM activation
is deferred pending its own price-path approval. Borrowing through the local
CreditEngine does not depend on that PSM, but both paths require the destination
Ripe deployment to exist first.

CCIP remains the canonical direct GREEN/RIPE rail. The owner-supplied 2026-08-19
messages correct the earlier untested-path premise: both Robinhood -> Base
messages completed through the automatic OffRamp `execute(bytes32[2],bytes)`
path, as did both Base -> Robinhood messages. Relay remains a possible
inventory-backed overlay for either protocol token, not a canonical settlement
replacement. Whether operating that inventory is worthwhile is an owner
decision outside this technical record.

## Why Across v1 is collateral-only, and what token onboarding requires

Across already has Base <-> Robinhood routes for the selected collateral. On the
evaluated V4 path, `SpokePool` has no active token allowlist: an unsupported
GREEN/RIPE deposit can succeed on-chain even though no relayer can be repaid for
filling it. That creates a silent funds-stranding failure rather than a clean
revert. V5 was not evaluated and is not an authorized workaround.

GREEN/RIPE settlement also requires Across DAO route onboarding and a canonical
Ethereum settlement asset. Neither is under Ripe's unilateral control, and no
such asset is configured or proven in this repository. A standard Across token
integration therefore requires, in order:

1. define the canonical Ethereum representation for each token;
2. provide canonical bridge adapters that can move that representation between
   Ethereum, Base, and Robinhood without granting Across independent mint
   authority;
3. have the Across DAO configure the HubPool L1 token and both
   `poolRebalanceRoutes`; and
4. have Across include the token in root-bundle construction so relayer refunds
   and pool rebalances are executable.

Until those steps are complete and verified onchain, Across GREEN/RIPE is
rejected explicitly at both API and client boundaries even if an upstream route
list claims support. This is a technical onboarding dependency, not a claim
that Across can never support the tokens.

Across collateral v1 has these hard admission controls:

1. **Three fail-closed gates per attempt:** live provider route intersected with
   Ripe's address-based allowlist; a current quote from an actual filler; and a
   fresh capacity read. `unknown` is disabled, never a cached positive.
2. **Swap API only:** `/suggested-fees` is legacy. Re-derive field shapes from
   the current Swap API and do not treat captured V4 quote fields as an
   integration contract.
3. **Exact V4 call shape:** allow only plain `deposit(...)` selector
   `0xad5425c6`, require `message == 0x`, and reject `unsafeDeposit(...)`
   selector `0x8b15788e`, periphery swaps, callbacks, V5-tagged messages, and
   undecodable nested calls.
4. **Independent client consent proof:** before enabling sign, bind
   `depositor`, recipient, token addresses, input/output amounts, destination,
   quote/fill deadlines, exclusivity encoding, and exclusive relayer to the
   values rendered to the user. `depositor` equals the connected signer; it is
   not merely non-zero.
5. **Correct exclusivity decoding:** zero parameter requires zero relayer. A
   non-zero parameter is an offset when at or below `31_536_000`, otherwise an
   absolute timestamp. Resolve it to an effective future deadline, bound the
   duration, and require a known non-zero filler.
6. **Exact-amount approval:** approve only the displayed input amount to the
   independently allowlisted spender. Validate `tx.to` and spender separately.
7. **Sign-time freshness:** re-quote and re-read capacity immediately before
   signature. Capacity is solver inventory and changes without an event.

For the current `bridgeableToBridgeable` route, the phase-zero validator can be
smaller than a generic recursive decoder, but it cannot disappear. The Swap API
does not expose every deposit field as structured JSON, and its supported
integration contract is to execute the returned `swapTx`. Decode that one flat,
known ABI; validate every field; locally re-encode the canonical deposit prefix;
and require a byte-for-byte prefix match before signing. The captured response
also contains trailing bytes after the canonical ABI payload, so the client must
accept only an explicitly documented and configured metadata suffix rather than
silently stripping or copying arbitrary bytes. Until Across confirms the suffix
for Ripe's registered integrator, the sign path stays disabled. Any wrapper,
periphery route, or later provider-supplied nested call still requires recursive
decoding. Every path ends in the same negative reachability test: no signing path
exists with any field, selector, message, suffix, or nested frame unvalidated.
Partial field coverage is not partial safety.

V1 stays two-step: bridge to the user's wallet, then use Ripe's existing deposit
flow. Atomic bridge-and-deposit would introduce a destination handler and make
Across's mutable `updatedMessage` an instruction surface. It requires a new
contract and separate adversarial review.

## CCIP remains canonical; live transfers now prove the send path

The current implementation is Chainlink CCIP burn/mint, not CCTP/CCDP. Four
GREEN/RIPE pools are registered, reciprocally wired, governance-owned, and
`RipeHq`-authorized on Base and Robinhood. No new bridge address may join that
mint-authorized set.

The owner supplied four production messages on 2026-08-19. At the
`2026-08-19T17:13:01Z` evidence cutoff:

| Direction | Token | Message | State at cutoff | Observed delivery |
| --- | --- | --- | --- | ---: |
| Robinhood -> Base | RIPE | `0x43423...58fe` | `SUCCESS`; automatic OffRamp `execute` | 1,132 s |
| Robinhood -> Base | GREEN | `0x880f6d...a9bb` | `SUCCESS`; automatic OffRamp `execute` | 1,165 s |
| Base -> Robinhood | RIPE | `0x56fd97...97f` | `SUCCESS`; automatic OffRamp `execute` | 1,198 s |
| Base -> Robinhood | GREEN | `0x351ed0...506bd` | `SUCCESS`; automatic OffRamp `execute` | 1,486 s |

All four receipt transactions used selector `0xf58e03fc`, decoded as
`execute(bytes32[2],bytes)`, and succeeded with 190,229, 190,262, 168,365, and
168,398 total transaction gas respectively. All four messages carried a
`90,000` destination token-gas amount. This disproves the claim that the lane
had never run and proves automatic execution for these four live cases. It does
not by itself measure the worst-case cold `releaseOrMint` subcall or prove every
future payload will fit.

Remaining technical hardening:

1. Retain the four-message API and receipt evidence as a reproducible baseline.
2. Measure the complete cold OffRamp destination path with the live tokens and
   current FeeQuoter configuration. The historical isolated cold
   `releaseOrMint` measurement was `95,902` gas against a historical `90,000`
   combined default; the successful live executions bound real behavior but do
   not expose that subcall's cold gas separately.
3. Bind a Safe/live signer backend to the repository script if that script is
   intended for operations; the owner transactions prove a live signer exists
   outside it.
4. Select explicit, independent rate-limit policies and a non-zero incident
   administrator for GREEN and RIPE. All four pools currently have rate limiting
   disabled and a zero `rateLimitAdmin`.
5. Bind exact live creation provenance and supported retry/manual-execution
   behavior.

Base finality remains a latency floor. A fast bridge appears faster because a
filler fronts capital before canonical finality; it does not remove finality or
reorg risk. CCIP rate limits remain the size rail and, for RIPE, the future
cross-chain arbitrage-capacity policy.

## Conditional Relay protocol-token topology

Relay can support the same inventory-backed shape for GREEN or RIPE without
receiving Ripe mint authority:

```text
user deposits origin token -> origin Relay Depository
Ripe payout contract transfers existing destination token -> user
Relay Oracle/Hub attributes fill -> Ripe receives origin-chain receivable
Ripe withdraws origin token -> CCIP rebalances inventory to destination
```

Destination inventory stays in the Ripe-controlled payout contract. **Ripe's** Relay
custody exposure begins only after a fill, as the filled-but-not-yet-withdrawn
origin receivable backed by a shared Depository; the user's origin funds enter
that Depository at deposit time. These values must never be conflated.

The pinned Relay order path also requires `order.solver` to be an EVM EOA and
credits that identity's Hub alias. The Ripe-operated lane therefore has two
Ripe-side components, not one: a non-mint-authorized payout contract that holds
inventory and enforces policy, plus a solver-signing EOA under an audited
HSM/MPC policy. The contract independently revalidates every signed order before
payout. Under the pinned withdrawal path, that EOA can choose the receiver for
its Hub receivable, so its compromise is another full-receivable-loss root.

Each Relay token lane is blocked until all of the following close:

### H-4 first — accept or remove the deployed key risk

The live normal Oracle path is 2-of-5, but that quorum is not an independent
root of trust:

- Depository allocator `0x63C1...1b56` is an EOA that can sign arbitrary calls
  moving the entire pooled balance.
- Depository owner `0xF61A...775A` is an EOA that can replace the allocator
  immediately.
- The same `0xF61A...775A` EOA owns the live Oracle multisig, administers the
  Oracle and Hub, already holds Hub `OPERATOR_ROLE`, and owns the live
  `RelayAllocator`. It can mutate the quorum, grant roles, mint/burn Hub
  balances, replace withdrawal payload builders, suspend Ripe's solver alias,
  and replace the Depository allocator without delay.
- Relay requires Ripe's solver identity to be an EOA. That signer can direct its
  outstanding Hub receivable to a caller-chosen receiver even though the payout
  inventory remains in a separate contract.

Key custody was excluded from the relevant audit. Before design sign-off, Relay
must answer how its two EOAs are secured and whether the Ripe lane can use isolated,
delayed multisig/contract control or a token-isolated Depository. Ripe must also
either obtain ERC-1271 solver/restricted-receiver support or approve a dedicated
solver EOA under an audited HSM/MPC policy. Otherwise governance/treasury must
explicitly configure the capped outstanding receivable it accepts as exposed to
instantaneous, uninsured 100% loss.

### H-1 — restore a fast-lane circuit breaker

`RipeHq.setMintingEnabled(false)` stops CCIP destination minting but does not
stop an ERC-20 inventory transfer. A fast lane therefore bypasses today's
cross-chain stop.

The destination payout component must be a separate Ripe-controlled contract
with zero mint authority and its own guardian-controlled bridge switch. It
rechecks the switch, every order field, and every exposure limit at fill
execution; a valid solver-EOA signature alone is insufficient. An API precheck
prevents a good-faith user from entering a lane that will not fill; it is UX
admission, not enforcement. A user can call Relay's permissionless deposit
directly, so only the payout contract can bound Ripe's inventory exposure.

### H-2 — bound blacklist-blocked settlement

Destination CCIP mint rejects a blacklisted payout/settlement address after the
origin burn. The block is reversible in code but may be policy-blocked
indefinitely, and no blacklist-exemption primitive exists. The payout contract
must check recipient, inventory, withdrawal, and settlement addresses before
paying and stop immediately on a blacklist or unhealthy settlement path.

If governance policy could never clear a settlement address, the direct Relay
lane does not ship. Caps bound loss; they do not create recovery.

### H-3 — prove every Relay order and deposit authority

Relay's Depository has no on-chain user balance, but its caller-supplied
`depositor` is not inert. The emitted value drives Hub order attribution,
recovery, and withdrawal ownership.

For the direct ERC-20 path:

- allow only explicit-amount `depositErc20(address,address,uint256,bytes32)`
  selector `0xe8017952`;
- reject the full-allowance overload `0x5a1ee3ac`;
- require effective depositor to be the connected signer—an explicit address
  equals it; zero is allowed only when the wallet is proven to call the
  Depository directly;
- request `includeProtocolData=true`, schema-decode the signed order, recompute
  the order id, bind calldata `id`, and verify the configured Ripe solver-EOA
  signature;
- bind every input, output, refund, call, deadline, fee, and extra-data field.

Unknown order versions, opaque payloads, raw transfers, deposit-address routes,
and unenumerated periphery calls fail closed.

## Exposure accounting for a Ripe-operated Relay lane

The implementation needs four independent bounds:

| Bound | What it limits | Enforcement |
| --- | --- | --- |
| Per-transfer quote cap | One user's fill | API display plus payout contract at execution |
| Payout inventory ceiling | GREEN or RIPE held in Ripe's destination hot contract | Treasury funding policy and on-chain balance/withdrawal controls |
| Relay receivable cap and age | Filled value not yet withdrawn from Relay | Chain-local payout allocation; governance-bounded aggregate |
| CCIP rebalance backlog cap and age | Withdrawn origin inventory not yet restored on destination | Payout contract/reconciler, independently from Relay status |

Governance first sets one common-mode receivable loss budget, then partitions it
into hard per-origin-chain/token allocations whose sum cannot exceed that budget.
Each destination payout contract enforces only its local allocation; the design
does not pretend independent contracts can atomically read a cross-chain
aggregate.

Reserve local receivable exposure **before** transferring destination tokens,
then perform the external transfer (checks-effects-interactions). Concurrent
fills must not overshoot the local allocation. Capacity may move from the Relay
receivable ledger to the CCIP backlog only after a finalized origin withdrawal
is proven. An API status, requested withdrawal, or unsigned indexer observation
is insufficient. The proof/coordinator mechanism for that cross-chain transition
is an unresolved implementation gate and requires its own replay, finality,
authorization, and compromise analysis. Until it exists, no production lane
can safely release the reservation early.

A requested short withdrawal cadence reduces duration only when Relay actually
signs and the withdrawal confirms; Ripe cannot unilaterally collect from the
Depository.

The payout design must additionally preserve these invariants:

- no payout, solver, keeper, Relay, settlement, or reconciliation address receives
  `RipeHq` mint authority;
- bridge pause and cap checks happen in the same transaction as the payout;
- exposure cannot be released from an unverified off-chain status assertion;
- chain-local receivable allocations cannot sum above the governance-approved
  common-mode loss budget;
- token transfers use exact amounts, safe return-value handling,
  reentrancy protection, and balance-delta checks where token behavior warrants;
- no arbitrary target or calldata execution exists in the payout contract;
- privileged funding, pause, and reconciliation roles are separated and held by
  approved multisigs; the Relay-required solver EOA is an explicit exception
  backed by an audited HSM/MPC policy and never directly authorizes payout; and
- upgrades, emergency recovery, and loss socialization are explicit owner
  decisions, not implicit implementation choices.

No payout contract or solver-key policy is designed or authorized by this
synthesis. Any candidate is new custody/signing infrastructure and requires
red-before-green unit/fuzz/invariant tests plus an independent audit before real
funds.

## GREEN and RIPE have the same fast-fill mechanics

From a contract standpoint, RIPE is not a different bridge design. A Relay lane
for either token moves only pre-existing inventory:

- the origin deposit transfers existing tokens into Relay's Depository;
- the destination payout transfers existing tokens from a non-mint-authorized
  Ripe contract;
- no bridge component calls `RipeHq` minting; and
- CCIP later burns on the inventory-surplus chain and mints the same amount on
  the inventory-deficit chain.

Global supply is conserved across deposit, payout, withdrawal, and rebalance.
The technical implementation should deploy or configure independent per-token
payout inventory, caps, accounting, pause state, and reconciliation so a fault
or exhausted float in one token cannot consume the other's capacity. GREEN and
RIPE then pass the same H-1 through H-4 gates. Whether Ripe chooses to supply
either inventory is deliberately outside this document.

## API and web architecture

The API/web plan in PR #30 is the implementation authority for the application
shape, subject to the security gates above:

- global route registry, separate from deployment-scoped protocol reads;
- live route support, quote, and lane-health as distinct fail-closed gates;
- quote proxy that allowlists targets and decodes provider calls;
- independent browser validation against rendered terms;
- one all-bridgeable-chain wallet transport with protocol reads still scoped to
  the selected deployment;
- exact approvals and a raw-viem bridge write path feeding the existing
  transaction toaster;
- provider status adapters and persisted records for escrowed, filled,
  refunded, and failed states; and
- separate collateral-acquisition and protocol-token surfaces with explicit
  trust/failure disclosures.

The Across collateral sign path cannot ship before its terminal validator and
negative reachability test. The conditional Relay lane adds lane-health,
receivable, and operational backlog surfaces only if its owner gates close.

## Phase order

1. **Finish CCIP hardening:** retain the four live transfers, measure full
   destination gas, bind the repository signer backend if operationally
   required, record provenance/retry behavior, and set independent GREEN/RIPE
   rate policies.
2. **Build Across collateral v1:** two-step only, feature-gated until the
   Robinhood Ripe product is deployable; exact V4 selector/message and complete
   consent validation are phase zero.
3. **Owner gate Relay before engineering:** resolve H-4 first, then H-1 and H-2.
   Obtain formal per-token onboarding, vendor key-custody answers, and an accepted
   exposure/loss budget plus solver-EOA policy or contract-account support.
4. **Only if approved, design each token payout and solver lane:** independent review,
   a separately reviewed cross-chain exposure-transition proof/coordinator,
   unit/fuzz/invariant suite, testnet canary, capped treasury funding,
   monitoring, and incident rehearsal before any mainnet value.

## Required negative tests

Across collateral:

- unsupported, unknown, stale, or under-capacity route never reaches signing;
- GREEN/RIPE is rejected by address at API and client even if upstream lists it;
- a golden captured Swap API quote decodes and canonically re-encodes to the
  expected V4 prefix and configured metadata suffix;
- attacker `depositor`, recipient, token, amount, chain, spender, target,
  deadline, exclusivity pair, suffix, or nested call never reaches signing;
- fields from two individually valid quotes cannot be spliced; quote id/expiry,
  decoded output, and the bridge-step output remain one bound record;
- stale/future quote timestamps, expired or too-near/too-far fill deadlines,
  `uint32` overflow, either exclusivity encoding, and an unknown filler fail
  closed;
- `unsafeDeposit`, non-empty message/V5, periphery, callback, and unknown
  selector never reaches signing;
- no alternate sign path bypasses the terminal validator; and
- exact allowance, quote expiry, refund, replacement, cancellation, and status
  behavior are exercised end to end.

Conditional Relay protocol token:

- bridge pause, token pause, blacklist, unhealthy settlement, amount cap, age
  cap, and aggregate cap each prevent payout;
- configured chain-local allocations cannot sum above the approved aggregate
  budget, and concurrent/fuzzed fills cannot overshoot a local allocation;
- receivable exposure is reserved before transfer and released only after a
  finalized origin withdrawal; forged, stale, replayed, or wrong-chain
  transition evidence cannot release it;
- wrong effective depositor, order id, solver signature, refund/output field,
  selector, order version, or opaque call cannot reach signing;
- the full-allowance overload can never be selected;
- loss or unavailability of either Relay EOA leaves the payout contract safely refusing
  new exposure; a compromised Ripe solver signer cannot bypass payout-contract
  checks, and its receiver-redirection loss is bounded by the receivable cap;
  and
- the set of `RipeHq.canMintGreen`/`canMintRipe` addresses is unchanged.

CCIP:

- both assets in both directions on testnet and forked real paths;
- cold destination gas with the full OffRamp path;
- pause, blacklist, mint-disable, retry, manual execution, and rate-limit
  boundaries; and
- cross-chain supply conservation through burn, in-flight, mint, and failure.

## Stop conditions and assurance

Stop rather than degrade when:

- route status, quote, capacity, calldata, order schema, or settlement health is
  unknown;
- provider bytes cannot be completely decoded or reconstructed;
- Across attempts GREEN/RIPE, `unsafeDeposit`, V5, a message, or an unevaluated
  wrapper;
- Relay's accepted full-loss receivable cap is absent, exceeded, or too old;
- Relay's deployed key model is neither migrated nor explicitly accepted;
- the required Ripe solver EOA lacks approved HSM/MPC custody and explicit
  receiver-redirection risk acceptance, unless Relay adds a contract-account or
  restricted-receiver path;
- blacklist policy cannot restore the settlement path;
- a fast bridge asks for Ripe mint authority.

The source/evidence records are suitable to merge as research. The Relay design
is **not** signed off: H-1, H-2, and H-4 remain owner decisions. H-3 has a
concrete fail-closed admission rule but remains an engineering gate until the
exact per-token order is enumerated, implemented, and tested. This document
authorizes none of the later phases.
