# Relay settlement-layer evaluation -- deployed contracts, audits, privilege graph

Reviewer: Luna
Date: 2026-08-18
Scope: pin what Relay's own infrastructure actually is -- deployed contracts,
who controls fund movement, and what has and has not been independently
audited -- for the conditional direct Relay GREEN lane under discussion in
`bridge-integration-security-review.md`. The original RipeHq-side review scoped
out Relay's contracts; revisions 5-6 now consume this companion evaluation.

Evidence: [`evidence/relay-live-snapshot-20260818.json`](evidence/relay-live-snapshot-20260818.json),
captured via direct `eth_getCode` / `eth_call` / `eth_chainId` JSON-RPC calls
(curl + Foundry `cast`) against Base and Robinhood mainnet RPC endpoints, and
by cloning and reading source from `relayprotocol/relay-depository`,
`relay-settlement`, `relay-protocol-oracle`, and `relay-periphery` directly
(commits pinned in the evidence file). One earlier lead -- a summarized
WebFetch of the `relay-depository` GitHub page claiming the repo was archived
and merged into a nonexistent `settlement-protocol` repo -- turned out to be
wrong on both counts once checked against `gh api`. Treat AI-summarized
vendor docs as leads, not evidence; this document only asserts what was
independently confirmed against source or live chain state.

## Two separate systems, two separate trust models

Relay is not one contract. It is two systems bridged by an off-chain service:

1. **`RelayDepository`** (Solidity, one instance per supported chain, same
   address `0x4cd00e387622c35bddb9b4c962c136462338bc31` on Base and Robinhood via
   a CREATE2 factory) -- holds the pooled tokens deposited on the origin
   chain. A solver pays the user on the destination chain from inventory it
   controls outside the Depository, then withdraws its credited receivable
   from the origin-chain Depository. Ripe would therefore keep destination
   GREEN inventory in its own filler; it would not park that standing float in
   Relay's contract.
2. **`RelayHub` / `RelayOracle` / `RelayAllocator`** -- an internal ERC-6909
   ledger plus an off-chain attestor network, running on Relay's own
   dedicated settlement chain (chain ID `537713`, not Base or Robinhood).
   This is Relay's internal bookkeeping of who is owed what.

An off-chain "attestor" service watches deposit/withdrawal events on every
connected chain, and once `ORACLE_ROLE`-authorized signers agree, mints or
burns balances on the Hub. A separate off-chain process then turns a Hub
burn into a signed instruction the Depository will execute. **The Hub ledger
and the Depository's actual funds are two different systems, connected only
by off-chain software and a signature check.** Nothing on-chain in
`RelayDepository.sol` verifies that a payout it executes corresponds to a
correctly-attested Hub burn -- it just checks one signature.

## `RelayDepository.sol` -- confirmed live on both Base and Robinhood

Read directly from `relay-depository/packages/ethereum-vm/src/RelayDepository.sol`
(commit `458a64c`), then independently confirmed on-chain:

- Deployed at `0x4cd00e387622c35bddb9b4c962c136462338bc31` on **both** Base
  (8453) and Robinhood (4663) -- confirmed via `eth_getCode` returning real
  bytecode on both chains at 2026-08-18T18:20-18:21Z, and `eth_chainId`
  returning `0x1237` (4663) on the Robinhood RPC.
- Currently holds real funds: **8.556 ETH + 41,090.87 USDC on Base**,
  **3.161 native ETH on Robinhood**, as of 2026-08-18T18:21:50Z. This is not
  an empty or unused contract -- it is live, pooled, and already carrying
  value belonging to whoever else already deposits through it.
- `depositErc20` / `depositNative` do exactly one thing: pull the tokens in
  and emit an event. **There is no per-depositor balance tracked in this
  contract at all.** Attribution lives in the Hub, off this contract's
  storage. That does not make the caller-supplied `depositor` field inert:
  both deposit functions emit it as the address to credit (substituting
  `msg.sender` only when it is zero), and the pinned Oracle consumes that
  emitted address when deriving Hub order attribution and recovery.
- The pinned Oracle trace is explicit: the EVM attestor reads the deposit-event
  `from` as `depositor`
  (`src/services/attestation/vm/ethereum-vm/index.ts:163-187,277-292`); the
  service uses it for the Hub alias/order address
  (`src/services/attestation/index.ts:544-558`), recovery
  (`:1459-1486,1509-1519`), and the fill source (`:1926-1944`). The recover-mode
  verifier binds both owner and recipient back to it
  (`src/common/recover-mode-verification.ts:160-180`). All anchors are at
  `relay-protocol-oracle@55b22de6358c212c22eebb48d2df5b793a16e863`.
- The repository's own
  `packages/ethereum-vm/deployments/scripts/test-deposit-and-withdrawal.js`
  (`:69-78`, at the pinned Depository commit) demonstrates the consequence:
  after attesting the event, it sets both the Hub withdrawal `owner` and
  `recipient` to `message.result.depositor`. A
  direct Depository call must therefore encode the connected signer as
  `depositor`; lack of local balance storage is not a substitute for that
  binding. Any surrounding router, refund, or delegation fields still require
  their own complete authority enumeration.
- For an ERC-20 route, the narrow admitted call is the explicit-amount overload
  `depositErc20(address,address,uint256,bytes32)` (`0xe8017952`). The sibling
  selector `0x5a1ee3ac` deposits the caller's **entire existing allowance** and
  is unnecessary for Ripe; it must be rejected. Relay quotes must request
  `includeProtocolData=true`; that returns the solver-signed order material, not
  a Relay Oracle attestation or proof that a deposit occurred. It must be
  schema-decoded so the order id, effective depositor, configured solver-EOA
  signature, refund/output/call fields, deadlines, fees, and extra data can be
  rebound independently before signing (`relay-docs@94bf717
  references/api/changelog.mdx:83-87`; `relay-kit@a5f6cb5
  packages/sdk/src/types/api.ts:2957-2979`). Zero depositor resolves to
  `msg.sender` and is safe only when the wallet calls the Depository directly,
  not through an intermediary.
- Because the quote recipient receives that solver signature before depositing,
  it cannot itself authorize a Ripe payout. The minimum proposed topology admits
  only a top-level `fill` transaction directly from the configured solver EOA
  after its service observes the deposit; Relay's EVM verifier inspects the
  top-level calldata suffix, so an inner wrapper call is not equivalent
  (`relay-protocol-oracle@55b22de
  src/services/attestation/vm/ethereum-vm/index.ts:407-468`).
- Custom payout quoting is not yet established by the pinned examples. Relay's
  standard EVM `output.extraData` canonically ABI-encodes a `fillContract`, but
  the captured examples point it at Relay's Router rather than a Ripe payout;
  some examples also have unequal `minimumAmount` and `expectedAmount`. Relay
  must demonstrate a live token-specific custom/exact-output policy before the
  proposed payout may assume either shape
  (`relay-settlement@98ad1a0 packages/sdk/src/order/index.ts:269-305`;
  `relay-docs@94bf717 features/price-stabilization.mdx:630-636` and
  `references/api/api_resources/contract-addresses.mdx:33`).
- Amount admission must include signed fees. The Oracle credits the input to the
  solver and then debits each successful-fill fee from that Hub balance, after
  requiring the fee currency to match the input. A payout policy that checks
  only `output <= input` can therefore create an origin shortfall; require
  overflow-safe `output + feeSum <= input` in the approved input currency. The
  proposed fixed 1:1 payout ledger goes further and requires equality; otherwise
  any surplus receivable must also be counted in the provider full-loss
  allocation. A shortfall requires an explicitly budgeted treasury subsidy
  (`relay-protocol-oracle@55b22de
  src/services/attestation/index.ts:375-399,1917-1975`).
- The only way funds leave is `execute(CallRequest, signature)`
  (`RelayDepository.sol:159-181`), where `CallRequest` is an **arbitrary
  array of `{to, data, value, allowFailure}` calls**, gated by exactly one
  check: `allocator.isValidSignatureNow(eip712Hash, signature)`. It supports
  EIP-1271, so `allocator` could in principle be a contract wallet -- but see
  below, on the live deployment it is not.
- `setAllocator(address)` (`:91-97`) is `onlyOwner`, takes effect
  **immediately**, no timelock, no two-step handoff. `Ownable` here is
  Solady's single-step variant, not `Ownable2Step`.

**Privilege graph, live-queried on both Base and Robinhood
(2026-08-18T18:21Z):**

| Role | Address | Contract or EOA? | Powers |
| --- | --- | --- | --- |
| `allocator` | `0x63C1d3E9C646184529C5694630a01C00dF171b56` | **EOA** (`eth_getCode` empty on Base) | Sole signer for `execute()` -- can move 100% of this contract's pooled balance, on either chain, to any address, via any calldata |
| `owner` | `0xF61A305199fa1135d76FFaB3752D42F55cBd775A` | **EOA** (`eth_getCode` empty on Base) | Can instantly repoint `allocator` to any address, no delay |

Neither address is the `RelayOracleMultisig`-style M-of-N contract that
exists elsewhere in Relay's own codebase (`RelayOracleMultisig.sol`,
`relay-settlement/smart-contracts/contracts/`). That contract is a real,
functioning on-chain threshold multisig (EIP-1271, sorted-signature
threshold check) -- Relay clearly knows how to build one. It is simply not
what is wired up as `allocator`/`owner` on the live Base/Robinhood
Depository today.

This is not an inference from missing documentation. A Zellic finding on the
`RelayAllocator`/Chain-Signatures NEAR-MPC signing path (finding 3.3 in the
Settlement Protocol audit, detailed below) drew this response from the
vendor directly: *"we will actually never use [that flow]... we will keep
relying on **the permissioned role** in the short term."* That is Uneven
Labs, Relay's own team, confirming in writing that production custody today
is a permissioned (i.e. centralized) signer, not the decentralized scheme
present in the repository. The live EOA `allocator`/`owner` addresses are
that permissioned role, observed directly.

## A Ripe solver is also an EOA authority, not the payout contract

The pinned order and withdrawal path adds a third signer-address boundary that
belongs to Ripe rather than Relay:

- Relay's order type says `solver` **must be an ethereum-vm EOA**
  (`relay-settlement/packages/sdk/src/order/index.ts:23-25`). The pinned Oracle
  verifies its order signature with viem `verifyMessage`
  (`relay-protocol-oracle/src/services/attestation/index.ts:299-311`) and credits
  successful fills to that solver's Hub alias (`:1910-1944`). A Ripe payout
  contract cannot itself be the solver identity under this path.
- `RelayAllocator.submitWithdrawRequest` lets a 20-byte spender EOA call
  directly (`RelayAllocator.sol:226-280`). `WithdrawRequest.receiver` is chosen
  by that caller (`:171-181`), and submission burns the spender's Hub balance
  (`:283-301`). The later Depository exit still needs Relay's allocator
  signature, but the legitimate solver is authorized to direct where its own
  receivable is paid.

A Ripe-operated lane therefore needs two components: (1) a non-mint-authorized
contract holding destination inventory and enforcing the pause, order terms, and
exposure caps at payout, and (2) a solver-signing EOA held under an audited
HSM/MPC policy. The contract must independently revalidate every solver-signed
order; the EOA signature alone cannot authorize inventory movement. Even then,
compromise of the solver signer can redirect Ripe's outstanding Hub receivable.
That is another full-receivable-loss root unless Relay supports an ERC-1271
solver or an on-chain receiver restriction. If governance will not accept the
EOA exception, lack of that provider support is a stop condition.

## `RelayHub` / `RelayOracle` -- a live quorum exists, but one EOA controls every layer

Read from `relay-settlement/smart-contracts/contracts/{RelayHub,RelayOracle,
RelayOracleMultisig,RelayAllocator}.sol` (commit `98ad1a0`):

- `RelayHub` is an ERC-6909-style multi-token ledger. `mint`/`burn` are
  `onlyRole(OPERATOR_ROLE)`. Ordinary balance moves (`transfer`,
  `transferFrom`) do real Solidity 0.8 underflow-checked arithmetic, so a
  burn genuinely cannot exceed a spender's on-chain Hub balance.
- `RelayOracle.execute()` lets **anyone** submit an `Execution` (a batch of
  MINT/BURN/TRANSFER actions against the Hub), gated by one check: a valid
  signature from an address holding `ORACLE_ROLE`. There is no on-chain
  proof-of-deposit check -- the contract trusts whatever produced that
  signature to have verified the real cross-chain event.
- `RelayOracleMultisig.sol` is a genuine on-chain M-of-N implementation
  (sorted ECDSA signatures, EIP-1271, owner-managed signer set/threshold).
  The repository publishes the production Relay-chain RPC at
  `https://rpc.chain.relay.link`; live queries on chain ID `537713` confirmed
  that the deployed multisig `0x2a72...fa2b0` holds `ORACLE_ROLE` and currently
  has five signers with threshold two.
- `RelayAllocator.submitWithdrawRequest` (the orchestration contract, not the
  Depository's `allocator` field) does burn Hub balance on-chain before
  building a withdrawal payload -- so *if* the Hub ledger is correct, this
  step is genuinely bounded by it.
- The quorum is **not an independent root of trust**. Live role queries found
  that EOA `0xF61A...775A` owns the Oracle multisig, holds `ADMIN_ROLE` on both
  the Oracle and Hub, and already holds Hub `OPERATOR_ROLE`. It can change the
  multisig signer set or threshold without a timelock, grant Oracle/Hub roles,
  and directly mint or burn Hub balances. The same EOA owns the Base and
  Robinhood Depositories and can repoint their allocator immediately. It also
  owns the live `RelayAllocator`: at block `3950912`, its `HUB` and `ORACLE`
  point to the current Hub and 2-of-5 multisig. As owner it can replace
  chain/depository payload builders and suspend any spender alias
  (`RelayAllocator.sol:199-223`), controlling the correctness and availability
  of Ripe's withdrawal path. A second EOA, `0x63C1...1b56`, is the current direct
  Depository allocator and can authorize arbitrary pooled-fund movement without
  consulting the Hub.

Net: the 2-of-5 Oracle quorum is live, but the privilege graph collapses back
to single on-chain signer-address authority. Compromise or misuse of
`0x63C1...1b56` is sufficient to
move Depository funds directly. Compromise or misuse of `0xF61A...775A` can
change the attestation quorum, mutate Hub balances, and replace the Depository
allocator or withdrawal payload builder, crossing every layer without delay.
The direct Relay lane must be
risk-accepted against that deployed graph, not against the stronger quorum
architecture that merely exists in source.

## Audit coverage -- weaker than the three-firm list suggests

Three reports exist and were read directly (not summarized secondhand);
full detail in the evidence file. Headline: **none of them covers what
matters most for this decision -- whether a single EOA is an acceptable
custody model for the Depository's `allocator`/`owner`.**

1. **Certora, "Relay Escrow," June 2025.** Scope is **Solana programs
   only** (`relay-escrow`/`relay-forwarder` Rust). Does not touch
   `RelayDepository.sol`, the EVM contract Base/Robinhood actually use. 9/9
   findings fixed, but all Solana-specific.
2. **Zellic, "Relay Protocol Oracle," April 2026.** Explicitly **excludes
   "Related on-chain contracts"** -- this audits the off-chain attestor/API
   service, not `RelayOracle.sol`/`RelayOracleMultisig.sol`. 2 critical + 3
   high findings, but the 2 criticals are Solana/Sui-specific (Sui support
   was removed rather than patched). Two **High** findings *do* hit the
   `EthereumVmAttestor` used for Base/Robinhood: a 60-second (~5 block)
   finalization window before attesting a deposit, and a matching gap on the
   withdrawal side -- Zellic's stated impact: "loss of funds in the
   depository" on reorg. Both are marked fixed by commit reference in the
   report; fix presence in the live running service isn't something a
   GitHub source tree can confirm. The report's own closing line: *"multiple
   reoccurring patterns resulting in serious issues from the attestation
   system of the oracle, which is essential and critical infrastructure of
   the protocol"* -- and recommends a follow-up assessment that, as far as
   this review found, hasn't been published.
3. **Zellic, "Relay Settlement Protocol," report dated Nov 2025.** This one
   *does* cover the EVM `RelayDepository.sol`, plus `RelayAllocator.sol`,
   `RelayHub.sol`, the payload builders, and `RelayMultisigSigner.sol`.
   **Explicitly excludes "Key custody"** -- the exact question this document
   is raising. One finding worth carrying forward as independently
   re-verified, not just cited: finding 3.2, *"RelayHub allows for arbitrary
   token transfers"* (quote: *"Anyone can transfer any amount of anyone's
   RelayHub tokens, at any time"*), rated Critical/High but scored
   Informational only because the file was outside the engagement's defined
   scope. Checked against the current cloned source (commit `98ad1a0`,
   8 months after the report): the Hub-level allowance skip this finding
   describes is still present verbatim in `RelayHub.transferFrom`, but
   `ERC20View.transferFrom` now independently checks and burns the Hub
   allowance itself before ever calling into the Hub -- so the practical
   path appears closed, just fixed at the caller rather than at the function
   the audit flagged. Finding 3.3 is the one that produced the "permissioned
   role" admission quoted above.

**No bug bounty program for Relay/Uneven Labs was found** via search
(Immunefi, Cantina, Sherlock, Code4rena, HackenProof). Absence of evidence,
not evidence of absence -- worth asking Relay directly rather than assuming
either way.

## What this means for the receivable/custody cap Gina asked to separate out

The three-limit framing (filler inventory cap / Relay receivable cap / CCIP
rebalancing cap) is right, but the Relay receivable cap needs to be sized
against a sharper fact than "our own outstanding fronted-but-unwithdrawn
value." The `RelayDepository` on each chain is a **shared pool**. A
compromised or misused `allocator` key drains the whole pool on that chain in
one `execute()` call, not just Ripe's slice of it -- and that key is a bare
EOA with no on-chain quorum, no timelock on rotation, and (per the audit
scoping above) no independent review of whether that's an acceptable custody
model. That risk exists **the moment Ripe's receivable balance is nonzero**,
regardless of size, and caps reduce the *magnitude* of a bad day but do not
change the fact that the loss event is binary and uninsured as far as this
review could confirm.

Concretely, before sign-off I'd want:

1. A direct question to Relay/Uneven Labs about current `allocator`/owner and
   cross-layer superadmin key management (HSM? Fireblocks/Turnkey-style MPC
   custody of those EOAs? multiple approvals off-chain even though on-chain is
   single-sig?), and whether these roles will move to isolated, delayed
   multisig control before onboarding GREEN. This is explicitly outside every
   audit's scope, so the off-chain custody answer must come from the vendor.
2. ERC-1271 solver or restricted-withdrawal-receiver support from Relay, or an
   explicit Ripe governance decision accepting a dedicated solver EOA under an
   audited HSM/MPC policy. The payout contract must revalidate the order rather
   than treating this signer as authority to transfer inventory.
3. The receivable cap treated as a **full, instant, uninsured loss-tolerance
   number** ("what are we okay losing entirely if this key is ever
   compromised or misused"), not an expected-loss model -- there's no
   dispute window, no insurance fund, and no on-chain recourse once
   `execute()` succeeds.
4. Minimizing *time* exposure as much as size: request withdrawal of Ripe's
   Hub-attested receivable immediately and on a short cadence, while treating
   that cadence as a vendor SLA rather than a unilateral mitigation. Relay must
   still authorize the Depository call, and exposure releases only after the
   withdrawal is confirmed/finalized. The binary risk is a function of how long
   and how much sits in the shared pool while attributed to Ripe, not just the
   peak amount.

This is not a categorical technology rejection, but it **does block design
sign-off** until treasury/governance accepts the receivable cap as a full-loss
number, the vendor answers the key-custody question, and the solver-EOA boundary
is removed or explicitly accepted. It does not put the Ripe-controlled
destination inventory behind the allocator key; it puts the
filled-but-not-yet-withdrawn origin-chain receivable there. If no acceptable
full-loss cap leaves enough throughput for a useful lane, the lane does not ship.
