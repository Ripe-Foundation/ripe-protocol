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
| Acquire collateral on Robinhood | USDC -> USDG, WETH -> WETH | **Across** | Preferred fast v1, two-step to the wallet and then into Ripe |
| Transfer GREEN directly | GREEN | **CCIP** | Only approved current route |
| Optional retail GREEN fast lane | GREEN | **Relay with a Ripe payout contract + solver EOA** | Blocked: H-1/H-2/H-4 owner gates plus H-3 engineering proof |
| Transfer RIPE directly | RIPE | **CCIP** | Only route; no Ripe-operated fast lane |

Across is already useful because its live Robinhood asset set matches Ripe's
selected collateral set. It should move commodity collateral, not protocol
tokens. A user can bridge USDC or WETH, deposit locally, and borrow or mint GREEN
on Robinhood without moving GREEN across a bridge:

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

CCIP remains the canonical direct GREEN/RIPE rail. Its current latency and
automatic-execution path must be measured and repaired before treating a second
bridge as the remedy. Relay remains a possible later retail GREEN overlay, not a
canonical settlement replacement.

## Why Across is collateral-only

Across already has Base <-> Robinhood routes for the selected collateral. On the
evaluated V4 path, `SpokePool` has no active token allowlist: an unsupported
GREEN/RIPE deposit can succeed on-chain even though no relayer can be repaid for
filling it. That creates a silent funds-stranding failure rather than a clean
revert. V5 was not evaluated and is not an authorized workaround.

GREEN/RIPE settlement also requires Across DAO route onboarding and a canonical
Ethereum settlement asset. Neither is under Ripe's unilateral control, and no
such asset is configured or proven in this repository. Across GREEN/RIPE is
therefore rejected explicitly at both API and client boundaries even if an
upstream route list later claims support.

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

For the current `bridgeableToBridgeable` route, prefer constructing the plain
deposit call locally from the allowlisted ABI and independently validated
structured values. If provider calldata is used, recursively decode it. Either
path ends in the same terminal validator and the same negative reachability
test: no signing path exists with any field, selector, message, or nested frame
unvalidated. Partial field coverage is not partial safety.

V1 stays two-step: bridge to the user's wallet, then use Ripe's existing deposit
flow. Atomic bridge-and-deposit would introduce a destination handler and make
Across's mutable `updatedMessage` an instruction surface. It requires a new
contract and separate adversarial review.

## CCIP remains canonical, but is not operationally proven

The current implementation is Chainlink CCIP burn/mint, not CCTP/CCDP. Four
GREEN/RIPE pools are registered, reciprocally wired, governance-owned, and
`RipeHq`-authorized on Base and Robinhood. No new bridge address may join that
mint-authorized set.

Before optimizing around CCIP latency:

1. Execute and retain evidence for a real test transfer in both directions for
   both tokens. The live-state capture performed no send.
2. Measure the complete cold OffRamp destination path with the live tokens and
   current FeeQuoter configuration. The historical isolated cold
   `releaseOrMint` measurement was `95,902` gas against a historical `90,000`
   combined default.
3. Bind a Safe/live signer backend; the current script is fork/preflight-only.
4. Select explicit, independent rate-limit policies and a non-zero incident
   administrator for GREEN and RIPE. All four pools currently have rate limiting
   disabled and a zero `rateLimitAdmin`.
5. Bind exact live creation provenance and supported retry/manual-execution
   behavior before declaring automatic execution ready.

Base finality remains a latency floor. A fast bridge appears faster because a
filler fronts capital before canonical finality; it does not remove finality or
reorg risk. CCIP rate limits remain the size rail and, for RIPE, the future
cross-chain arbitrage-capacity policy.

## Conditional Relay GREEN topology

Relay can support the intended shape without receiving Ripe mint authority:

```text
user deposits origin GREEN -> origin Relay Depository
Ripe payout contract transfers destination GREEN -> user
Relay Oracle/Hub attributes fill -> Ripe receives origin-chain receivable
Ripe withdraws origin GREEN -> CCIP rebalances inventory to destination
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

Relay GREEN is blocked until all of the following close:

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
must answer how its two EOAs are secured and whether GREEN can use isolated,
delayed multisig/contract control or a token-isolated Depository. Ripe must also
either obtain ERC-1271 solver/restricted-receiver support or approve a dedicated
solver EOA under an audited HSM/MPC policy. Otherwise governance/treasury must
explicitly accept a capped outstanding receivable as an instantaneous, uninsured
100% loss. If a tolerable cap is too small for a useful lane, do not ship it.

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
| Payout inventory ceiling | GREEN held in Ripe's destination hot contract | Treasury funding policy and on-chain balance/withdrawal controls |
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

## Why RIPE stays CCIP-only

Minting RIPE locally without a matching burn violates global supply
conservation. A fast lane could therefore move only pre-existing inventory.
Ripe should not operate a directional treasury float in its own governance
token.

More importantly, Robinhood currently has no RIPE venue: the Curve and Aerodrome
RIPE components are omitted/disabled, and the monitoring-only RIPE/WETH adapter
is not a protocol venue. Arbitrage is venue-first. When a venue exists, market
makers can hold bilateral inventory, trade locally, and batch-rebalance through
CCIP. CCIP latency affects required inventory and spread; it does not require a
bridge per trade.

Sequence RIPE as: prove CCIP reliability, set a RIPE-specific rate policy,
launch and qualify a venue, then measure demand. Only then reconsider a
third-party retail fast lane. Do not make Ripe the RIPE solver.

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

1. **Measure and harden CCIP:** real transfers, full destination gas, signer
   backend, provenance, retry path, and independent GREEN/RIPE rate policies.
2. **Build Across collateral v1:** two-step only, feature-gated until the
   Robinhood Ripe product is deployable; exact V4 selector/message and complete
   consent validation are phase zero.
3. **Owner gate Relay before engineering:** resolve H-4 first, then H-1 and H-2.
   Obtain formal GREEN onboarding, vendor key-custody answers, and an accepted
   exposure/loss budget plus solver-EOA policy or contract-account support.
4. **Only if approved, design the GREEN payout and solver:** independent review,
   a separately reviewed cross-chain exposure-transition proof/coordinator,
   unit/fuzz/invariant suite, testnet canary, capped treasury funding,
   monitoring, and incident rehearsal before any mainnet value.
5. **RIPE venue first:** no RIPE fast-lane work until a real second venue and
   market-maker demand exist.

## Required negative tests

Across collateral:

- unsupported, unknown, stale, or under-capacity route never reaches signing;
- GREEN/RIPE is rejected by address at API and client even if upstream lists it;
- attacker `depositor`, recipient, token, amount, chain, spender, target,
  deadline, exclusivity pair, or nested call never reaches signing;
- `unsafeDeposit`, non-empty message/V5, periphery, callback, and unknown
  selector never reaches signing;
- no alternate sign path bypasses the terminal validator; and
- exact allowance, quote expiry, refund, replacement, cancellation, and status
  behavior are exercised end to end.

Conditional Relay GREEN:

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
- Relay's accepted full-loss receivable cap is absent, exceeded, too old, or too
  small for a useful lane;
- Relay's deployed key model is neither migrated nor explicitly accepted;
- the required Ripe solver EOA lacks approved HSM/MPC custody and explicit
  receiver-redirection risk acceptance, unless Relay adds a contract-account or
  restricted-receiver path;
- blacklist policy cannot restore the settlement path;
- a fast bridge asks for Ripe mint authority; or
- a RIPE fast lane is proposed before a venue and independent market-maker
  inventory exist.

The source/evidence records are suitable to merge as research. The Relay design
is **not** signed off: H-1, H-2, and H-4 remain owner decisions. H-3 has a
concrete fail-closed admission rule but remains an engineering gate until the
exact GREEN order is enumerated, implemented, and tested. This document
authorizes none of the later phases.
