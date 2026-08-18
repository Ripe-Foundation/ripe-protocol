# Relay settlement-layer evaluation -- deployed contracts, audits, privilege graph

Reviewer: Luna
Date: 2026-08-18
Scope: pin what Relay's own infrastructure actually is -- deployed contracts,
who controls fund movement, and what has and has not been independently
audited -- for the conditional direct Relay GREEN lane under discussion in
`bridge-integration-security-review.md`. That review scopes out "Relay's own
contracts" deliberately; this document is the other half.

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
   address `0x4cd00e387622c35bddb9b4c962c136462338bc31` on every EVM chain via
   a CREATE2 factory) -- holds the actual pooled tokens. This is what Ripe
   would deposit GREEND float into and what pays users out.
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
  contract at all.** Attribution lives entirely in the Hub, off this
  contract's storage.
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

## `RelayHub` / `RelayOracle` -- a real quorum exists, but for a different layer

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
  (sorted ECDSA signatures, EIP-1271, owner-managed signer set/threshold) that
  can hold `ORACLE_ROLE`. **Whether it actually does, and what its live
  threshold/signer count is, was not independently verifiable** -- the Hub
  and Oracle live on Relay's own settlement chain (ID `537713`), and no
  public RPC for that chain was found during this review. `oracle` and
  `oracleMultisig` addresses are pinned in the evidence file from the repo's
  `deployments/hub-contracts/prod.json`, unverified against live chain
  state.
- `RelayAllocator.submitWithdrawRequest` (the orchestration contract, not the
  Depository's `allocator` field) does burn Hub balance on-chain before
  building a withdrawal payload -- so *if* the Hub ledger is correct, this
  step is genuinely bounded by it.

Net: **the Hub ledger layer has a real, on-chain, auditable quorum
mechanism available and apparently used.** The Depository -- the layer that
actually releases Ripe's tokens -- does not use it. A compromised or
misattributed Oracle signature can mint bad Hub balance, but that alone
doesn't move real funds; a compromised or misused `allocator` EOA on the
Depository does, directly, with no quorum in between.

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

1. A direct question to Relay/Uneven Labs about current `allocator`/`owner`
   key management (HSM? Fireblocks/Turnkey-style MPC custody of that single
   EOA? multiple approvals off-chain even though on-chain is single-sig?) --
   this is explicitly outside every audit's scope, so it can only be
   answered by the vendor, not by reading more source.
2. The receivable cap treated as a **full, instant, uninsured loss-tolerance
   number** ("what are we okay losing entirely if this key is ever
   compromised or misused"), not an expected-loss model -- there's no
   dispute window, no insurance fund, and no on-chain recourse once
   `execute()` succeeds.
3. Minimizing *time* exposure as much as size: withdraw Ripe's Hub-attested
   receivable back out of the Depository on a short, automated cadence
   rather than letting it accumulate, since the binary risk is a function of
   how long and how much sits in the shared pool while attributed to Ripe,
   not just the peak amount.

This does not, on its own, block the GREEN retail lane -- it changes what
the receivable cap number has to represent, and it adds a vendor question
that isn't answerable from source alone.
