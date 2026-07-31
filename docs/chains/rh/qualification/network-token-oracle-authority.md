# Robinhood network, token, clock, and oracle qualification authority

Evidence date: 2026-07-30
Authority baseline: `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693`
Authority tree: `b68dffdddbdc7c5ae8423db049099c1632b478c9`

## 1. Executive readiness verdict

**Verdict: BLOCKED. Fork execution is not currently possible.** Public evidence is
sufficient to identify the Robinhood network, mainnet/testnet WETH and USDG
addresses, the mainnet Chainlink feed candidates, and the expected Arbitrum/Nitro
clock model. It is not sufficient to create an accepted fork configuration.

The ten blocking packet classes below correspond exactly to section 9:

1. no final signed immutable packet that incorporates the controlling profile
   scope, packet authority, revalidation triggers, and deferred lifecycle-
   registration disposition recorded below;
2. no owner-accepted mainnet or testnet block number, block hash, parent hash,
   timestamp, state root, parent-L1 identity/number evidence, finality policy, or
   adjacent-block clock fixture;
3. no approved archive-provider secret alias and no provider capability receipt for
   the required read-only JSON-RPC methods;
4. no approved fork engine and immutable version that preserves the Robinhood child
   block, ancestor `NUMBER`, timestamp, receipt `l1BlockNumber`, NodeInterface, and
   ArbSys relationships;
5. no accepted pinned proxy, implementation, admin, runtime/code-hash, storage, and
   behavior bindings for canonical mainnet/testnet WETH or USDG;
6. no accepted compiler-derived USDG layout or owner-approved overlay amount,
   actor, two-write set, and unchanged-state set;
7. no frozen H-07 artifact package, constructor packet, or deterministic deployment
   identities for GREEN, RIPE, and sGREEN;
8. no owner-accepted `ChainlinkPrices.vy` constructor packet, including ETH/BTC
   sentinel identities, BTC/USD disposition, timelocks, a production stale-time
   policy with operating margin, WETH/USD and USDG/USD feeds, testnet feeds, and
   accepted pin-round tuples;
9. no accepted Robinhood Chainlink sequencer uptime feed or fully bound combined
   Robinhood-signal plus parent-L1/inbox operational policy, and no approved
   production grace/recovery authority; and
10. no approved H-08/H-09 fixture/assertion APIs, output ceiling, or registration
    path for this new report.

Classification used throughout:

| Code | Meaning |
|---|---|
| **IV** | Independently verified from the frozen repository or an authoritative primary source, with any stated source/date boundary. |
| **CPC** | Credible public candidate. It is evidence for owner review, never accepted configuration. |
| **OAR** | Owner approval and an exact binding artifact are required. |
| **UA** | Unavailable in the authoritative public sources inspected. |
| **IUD** | Impossible until a deterministic plan or deployment creates the fact. |
| **PA** | Prohibited assumption. Qualification must fail if code attempts to infer or substitute it. |

An **IV** public fact is not automatically an accepted protocol configuration.
Acceptance still requires the owner packet in section 9. No **CPC** in this report
may be promoted by an implementation, test, operator, or reviewer without that
packet.

## 2. Exact repository baseline

| Fact | Evidence | Classification |
|---|---|---|
| Repository | `/Users/wigglez/dev/ripe-protocol` | IV |
| Frozen commit | `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693` | IV |
| Frozen tree | `b68dffdddbdc7c5ae8423db049099c1632b478c9` | IV |
| Isolated branch | `codex/rh-network-token-oracle-qualification` | IV |
| Isolated worktree | `/private/tmp/ripe-rh-network-token-oracle-qualification` | IV |
| Worktree root mode | `0700` (`drwx------`) | IV |
| Initial isolated status | clean; `HEAD` and tree exactly matched the frozen authority | IV |
| Initial primary status | clean `rh` worktree; not modified by this investigation | IV |
| Permitted repository change | this report only, left untracked, unstaged, and uncommitted | OAR, satisfied for this investigation |

Repository authorities inspected at the frozen baseline include:

- `config/network_profiles.py`;
- `config/block-clock-inventory.json`;
- `docs/chains/rh/shared-block-clock-specification.md`;
- `docs/chains/rh/schemas/deployment-manifest-v2.schema.json`;
- `docs/chains/rh/evidence/robinhood-manifest-phase-a.md`;
- `docs/chains/rh/deployment-owner-readiness.md`;
- `config/robinhood-parameters.json`;
- `config/robinhood_blueprint.py`;
- `config/contract-artifact-expectations.json`;
- the symbolic-input and binding-schedule registers in
  `config/robinhood_blueprint.py` and `config/robinhood-parameters.json`;
- H-04 through H-09 state and ownership in `docs/chains/rh/status.yaml`;
- `scripts/probes/action_block_identity_probe.py`;
- `docs/chains/rh/evidence/ledger-action-block-testnet-proof.md`;
- `contracts/tokens/GreenToken.vy`, `RipeToken.vy`, `SavingsGreen.vy`, and their
  ERC-20/ERC-4626 modules;
- `contracts/priceSources/ChainlinkPrices.vy`;
- token-control, fee-on-transfer, return-value, signature, oracle, and clock mocks
  and tests; and
- the current conditional fork-qualification architecture.

The frozen repository establishes the following lifecycle boundary:

| Track | Frozen state relevant to this pack | Classification |
|---|---|---|
| H-04 | schema-v2 parameters and binding schedules exist; unresolved identities keep `DefaultsRobinhood` fail-closed | IV |
| H-05 | deterministic blocked planning exists; execution remains unauthorized | IV |
| H-06 | candidate macOS/APFS operator class is qualified; final operator/machine/volume binding remains open | IV |
| H-07 | exact verifier, ABI, and artifact package is not complete | IV; completion OAR |
| H-08 | post-deployment assertion checker awaits approved graph, values, plan, artifacts, and fixtures | IV; completion IUD |
| H-09 | aggregate qualification awaits H-01 through H-08 and alone may issue non-authoritative `LOCAL_FORK_QUALIFIED` | IV; completion IUD |

The deployment-manifest v2 schema records source commit/tree, expected chain ID,
transaction block number/hash, finality, code-hash/storage-value postconditions, and
observation block number/hash. It does **not** itself supply a fork block,
`stateRoot`, archive-provider proof, token/feed authority, or clock-fidelity
evidence. Treating schema presence as those facts is **PA**.

The existing S5/H-02 action-block evidence uses four field classes. This report
does not replace them; it maps them as follows:

| Existing evidence class | This report | Reconciliation |
|---|---|---|
| verified local/source fact | IV | Retain the exact frozen-source or historical-evidence boundary; it is not current live proof. |
| proposed operational value | CPC until approved, then OAR-bound | A proposal is never an accepted runtime value. |
| owner-supplied/approved value | OAR until the immutable packet is present | The class describes provenance, not current completeness. |
| live observed value | UA until separately authorized and observed | A historical observation remains IV historical evidence but cannot become the new fork pin or archive proof. |

The prior evidence's endpoint-fingerprint, redirect prohibition, redaction, and
stop contracts are reused in section 4. Its credential-free public-endpoint pins
are historical and explicitly lack an archive-service guarantee, so they do not
close any section 3 or 4 gate.

## 3. Network and fork-pin authority

### Network matrix

| Network | Chain ID | Parent L1 for numbered L1 evidence | Repository profile | Public authority | Acceptance state |
|---|---:|---|---|---|---|
| Robinhood mainnet | `4663` | Ethereum mainnet | `robinhood-mainnet` | Robinhood Chain connecting/protocol registries and Paxos USDG network documentation | IV; exact fork pin OAR |
| Robinhood testnet | `46630` | Ethereum Sepolia | `robinhood-testnet` | Robinhood Chain connecting/protocol registries | IV; exact fork pin OAR |

The parent-L1 identity is not optional metadata. Every block
`l1BlockNumber`, receipt `l1BlockNumber`, EVM `NUMBER`, L1 header, and L1
protocol-contract observation must be interpreted against Ethereum mainnet for
Robinhood mainnet and Ethereum Sepolia for Robinhood testnet. Cross-parent reuse is
**PA**.

### Qualification-relevant official protocol registry

| Contract | Robinhood mainnet | Robinhood testnet | Qualification use | Classification |
|---|---|---|---|---|
| Rollup (L1) | `0x23A19d23e89166adedbDcB432518AB01e4272D94` | `0xdc5F8E399DBd8a9F5F87AeC4C23Beb12431b386D` on Sepolia | bind the parent rollup identity and any owner-approved assertion/finality evidence | IV address; behavior/pin OAR |
| Sequencer Inbox (L1) | `0xBd0D173EEb87D57A09521c24388a12789F33ba96` | `0xA0D9dB3DC9791D54b5183C1C1866eFe1eCA7D414` on Sepolia | candidate parent-chain batch/liveness observation point | IV address; liveness policy CPC/OAR |
| Delayed Inbox (L1) | `0x1A07cc4BD17E0118BdB54D70990D2158AbAD7a2D` | `0xF2939afA86F6f933A3CE17fCAB007907B6b0B7a4` on Sepolia | candidate parent-chain delayed-message/liveness context | IV address; liveness policy CPC/OAR |
| L1 WETH | `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2` | Sepolia WETH `0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9` | corroborate parent/token-bridge profile; never substitute for L2 WETH | IV address; L2 substitution PA |
| L2 WETH | `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` | `0x7943e237c7F95DA44E0301572D358911207852Fa` | canonical WETH identity candidate | IV address; pin/code/behavior OAR |
| L2 Proxy Admin | `0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF` | `0xE743e696B00789Ef489cF617477771764E9283a0` | public candidate for bridge-proxy administration, including L2 WETH | IV address; exact WETH binding OAR |
| NodeInterface | `0x00000000000000000000000000000000000000C8` | same | standard Arbitrum child/L1 mapping helper for clock evidence | IV address; accepted calls/results OAR |

The protocol registry also publishes gateways, Bridge, Outbox, Multicall, Permit2,
and other precompiles. They are **IV addresses** but are not required inputs to this
network/token/oracle qualification unless an approved fixture invokes them. Their
publication must not be mistaken for accepted code, admin, or behavior.

The repository requires source-chain ID matching, a positive block number for
evidence mode, and a clean evidence run. It forbids fork submission. Its current
validator does not bind the block hash, parent hash, timestamp, `stateRoot`, or
archive capability. A positive block number alone is therefore **PA** as a
qualification pin.

### Required accepted fork-pin record

The controlling qualification order is Profile 1 Robinhood mainnet first, Profile
1 Robinhood testnet after its exact oracle/external-identity packet exists, and
Profile 2 as the staged Curve/follow-on lane. Each qualification-profile/network
combination requires an independent immutable record. No pin, provider receipt,
external manifest, oracle packet, or evidence may cross-fill another combination.

```yaml
qualification_profile: profile-1 | profile-2
network_profile_id: robinhood-mainnet | robinhood-testnet
chain_id: 4663 | 46630
parent_l1: ethereum-mainnet | ethereum-sepolia
pin:
  child_block_number: <positive integer>
  child_block_hash: <0x + 64 lowercase hex>
  parent_hash: <0x + 64 lowercase hex>
  timestamp: <integer Unix seconds>
  state_root: <0x + 64 lowercase hex>
  block_l1_block_number: <integer as returned on the child block>
  representative_transaction_hash: <0x + 64 lowercase hex>
  receipt_child_block_number: <integer>
  receipt_l1_block_number: <integer>
adjacent_clock_fixture:
  previous_child_block_number: <pin.child_block_number - 1>
  previous_child_block_hash: <0x + 64 lowercase hex>
  previous_parent_hash: <0x + 64 lowercase hex>
  previous_timestamp: <integer Unix seconds>
  previous_state_root: <0x + 64 lowercase hex>
  previous_block_l1_block_number: <integer>
finality:
  policy_id: <owner-controlled identifier>
  accepted_tag_or_confirmations: <exact value>
  observation_block_number: <integer>
  observation_block_hash: <0x + 64 lowercase hex>
  selected_at_utc: <RFC 3339 timestamp>
authority:
  owner_record_id: <immutable identifier>
  owner_record_sha256: <64 lowercase hex>
```

Required properties:

- `eth_getBlockByNumber(pin.child_block_number)` and
  `eth_getBlockByHash(pin.child_block_hash)` must return the same number, hash,
  parent hash, timestamp, `stateRoot`, and `l1BlockNumber`.
- The previous block's number must be `N-1`, and the pin's `parentHash` must equal
  the previous block's hash.
- The representative transaction receipt must be in child block `N` and must carry
  the accepted receipt `l1BlockNumber` on the profile's exact `parent_l1`.
- The pin must satisfy the owner finality policy at the recorded observation block.
  `latest`, `safe`, or `finalized` queried at runtime is not a substitute for the
  recorded immutable number/hash pair.
- The provider must reproduce the exact header, code, storage, calls, proofs, and
  receipt at both accepted blocks. A provider that returns `null`, a pruned-state
  error, a missing trie-node error, or data from a different block is not archive
  capable for this qualification.
- The `stateRoot` is an accepted header fact, not proof that every returned storage
  value is correct. Required token/feed accounts must also have owner-approved
  `eth_getProof` account/storage proofs, or an owner-approved equivalent rooted in
  that exact `stateRoot`.

No accepted block record exists now: **UA + OAR**. Reusing a historical report pin,
the current tip, a block number without a hash, or the same number from a different
provider is **PA**.

## 4. RPC capability and secret-handling contract

### Secret aliases

| Profile | Repository alias | Policy |
|---|---|---|
| Mainnet | `ROBINHOOD_MAINNET_RPC_URL` | IV alias name; provider/secret binding OAR |
| Testnet | `ROBINHOOD_TESTNET_RPC_URL` | IV alias name; provider/secret binding OAR |

The owner packet must contain the secret-manager reference or environment alias,
never the URL, key, token, credential, or expanded value. The runtime contract must:

1. resolve the approved alias only inside the authorized process;
2. reject missing, empty, whitespace, placeholder, public, or wrong-profile values;
3. prevent expansion in command arguments, exception text, captured stdout/stderr,
   pytest node IDs, JSON evidence, shell history, and process summaries;
4. render only `<rpc profile=... reference=... redacted>`;
5. clear the value from child environments that do not require RPC;
6. record the provider identity and capability receipt without recording a secret;
7. forbid fallback to Robinhood's rate-limited public endpoint; and
8. fail if the actual method inventory exceeds the approved whitelist.

Robinhood officially recommends a provider archive endpoint for historical reads
and names Alchemy as its recommended provider. The published candidate shapes are
`https://robinhood-mainnet.g.alchemy.com/v2/{API_KEY}` and
`https://robinhood-testnet.g.alchemy.com/v2/{API_KEY}`. Alchemy is **CPC**, not a
preselected provider; QuickNode, Blockdaemon, dRPC, and Validation Cloud are also
officially listed public candidates. The owner must select and approve an
archive-capable product. Robinhood's public endpoints are rate-limited and not
recommended for production, so they are public discovery/historical-evidence
references only (**IV**) and **PA** for accepted fork qualification.

Reuse the frozen H-02/S5 endpoint-identity contract: compute lowercase SHA-256 over
the exact UTF-8 endpoint bytes with no newline or normalization before contact,
compare it to the secret-free owner packet, disable HTTP redirects, and treat every
3xx or fingerprint mismatch as a hard stop. The URL and credential must never enter
commands, packets, journals, output, or repository evidence. Historical endpoint
fingerprints in the S5 record bind only those historical observations; they are
**PA** as the new owner/provider selection.

### Permitted JSON-RPC methods

The candidate qualification whitelist is read-only:

| Method | Qualification purpose | Status |
|---|---|---|
| `eth_chainId` | bind profile to chain | required; OAR |
| `eth_getBlockByNumber` | exact numbered header and adjacent header | required; OAR |
| `eth_getBlockByHash` | number/hash cross-check | required; OAR |
| `eth_getTransactionByHash` | bind representative transaction to the pin | required; OAR |
| `eth_getTransactionReceipt` | child block and receipt `l1BlockNumber` | required; OAR |
| `eth_getCode` | proxy, implementation, feed, ArbSys, and token runtime | required; OAR |
| `eth_getStorageAt` | implementation/admin slots and approved storage checks | required; OAR |
| `eth_getProof` | account/storage proof rooted in the accepted `stateRoot` | required unless owner approves an equivalent; OAR |
| `eth_getBalance` | fork engine account hydration and no-value assertions | permitted only if actually required; OAR |
| `eth_getTransactionCount` | fork engine account hydration | permitted only if actually required; OAR |
| `eth_call` | metadata, proxy, token behavior, feed, NodeInterface, and ArbSys reads at the exact pin | required; OAR |
| `eth_getLogs` | bounded event/proxy-upgrade evidence for named contracts and block range | permitted only for approved fixtures; OAR |
| `eth_syncing` | self-hosted/reference-node synchronization check | diagnostic only; not pin authority |

The approved runner must capture method names and counts, redact parameters that
could contain a secret, and prove that the observed set is a subset of the owner
whitelist. Unsupported required methods stop before `boa.fork` or any equivalent
engine call.

The following are prohibited: `eth_send*`, `personal_*`, `wallet_*`, `account_*`,
`admin_*`, `miner_*`, `txpool_*`, signing methods, unlocked accounts, transaction
submission, debug/trace namespaces, and any provider-specific mutation method.
`eth_blockNumber`, `latest`, an unpinned client-version string, and provider marketing
claims are **PA** as block, archive, or fork-engine proof.

### Provider capability receipt

The owner must approve a secret-free receipt containing: profile, provider product,
archive tier, provider documentation/version date, alias name, exact method
whitelist, per-method support result, retention guarantee, rate/quota bounds,
pin/adjacent-block reproduction hashes, proof support, timeout/retry bounds, and
receipt SHA-256. A retry may repeat only the same immutable request. It may not
change the block, provider, method, or parameters.

If the owner selects parent-L1 protocol observation for sequencer evidence, it must
also provide separate Ethereum-mainnet and/or Sepolia archive aliases, endpoint
fingerprints, provider receipts, and method inventories. The frozen repository
defines no accepted aliases for those parent providers: **UA + OAR**. An L2 alias
must not be reused or silently redirected to L1.

## 5. Block-clock evidence requirements

Robinhood's official EVM-difference documentation states that `block.number` is an
estimate of the L1 Ethereum block and that `ArbSys(0x64).arbBlockNumber()` returns
the Robinhood child block. Arbitrum's upstream documentation distinguishes child
RPC block numbers, receipt `l1BlockNumber`, block `l1BlockNumber`, EVM
`block.number`, and sequencer timestamps. These are **IV** platform semantics, but
the exact values at a selected pin remain **OAR**.

| Clock surface | Required relationship at the pin | Classification |
|---|---|---|
| RPC child block | `block.number == N`; hash/header match the accepted record | OAR |
| Adjacent child block | previous number is `N-1`; `pin.parentHash == previous.hash` | OAR |
| ArbSys child number | `ArbSys(0x64).arbBlockNumber() == N` at the pin | IV semantic; value OAR |
| Receipt child number | representative `receipt.blockNumber == N` | IV semantic; value OAR |
| Block L1 number | record the block's approximate first non-Arbitrum ancestor number | IV semantic; value OAR |
| Receipt L1 number | record the ancestor number usable for the transaction's EVM `NUMBER` context | IV semantic; value OAR |
| EVM `NUMBER` | replayed/probe execution for the representative context equals the accepted receipt `l1BlockNumber` | OAR; any child-number substitution is failure |
| Timestamp | EVM `TIMESTAMP` at the pin equals the accepted child header timestamp | OAR |
| Timestamp sequence | previous timestamp `<=` pin timestamp; no fabricated parent-chain equality | IV semantic; values OAR |
| Block vs receipt L1 number | record both; do not assume they are equal because upstream describes different precision | PA to infer equality |
| NodeInterface mapping | owner-approved calls at `0x00000000000000000000000000000000000000C8` agree with the accepted child/L1 mapping fixture | IV address/semantic candidate; values OAR |
| Repeated ancestor number | fixture includes consecutive child blocks sharing one ancestor/EVM `NUMBER`, or records that no approved pair was found and blocks repeated-number qualification | OAR |
| ArbOS version | `ArbSys.arbOSVersion()` equals the accepted version for the pin | OAR |

The official Robinhood full-node guide currently publishes:

- Nitro image tag `offchainlabs/nitro-node:v3.11.2-3599aca`;
- ArbOS profile `61`; and
- separate Robinhood mainnet/testnet chain-info files.

These are **IV public candidates** for a reference node, not an accepted fork-engine
binding. The frozen probe records full Nitro commit
`3599acae1ad2fab4059fc46453c9cd3294126641`, ArbSys interface commit
`7e88c8cc53c2e96201a23c638f1536557b9cb68b`, and expected raw
`arbOSVersion()` return `116` under its pinned offset rule. Acceptance of the full
source closure, image digest, chain-info hash, genesis hash, ArbOS return, and fork
engine remains **OAR**.

The frozen toolchain is Titanoboa `0.2.7`, Vyper `0.4.3`, and pytest `8.4.2`
(**IV**). The existing probe also records two disqualifying limitations (**IV**):

- Boa/PyEVM cannot natively execute Nitro's `0xfe` ArbSys precompile and uses a
  controlled double; and
- Boa exposes the child state number through local `NUMBER`, not Robinhood's
  ancestor-number behavior.

Therefore Titanoboa `0.2.7` is **not** an accepted clock-faithful Robinhood fork
engine. The owner must approve a versioned engine/reference-node composition that
passes the relationships above. Failure is `RB-CLOCK-CURVE`; `CurvePrices.vy` must
not be patched to accommodate the harness.

Clock-sensitive repository consumers include Ledger's same-action discriminator,
Curve snapshot/repeated-number/staleness/danger logic, Chainlink future/stale
checks, and governance/configuration timelocks. The frozen repository's exact clock
profiles are `B-ORD`, `R-REP128`, `R-PLUS1`, `R-J2-J4`, `BOUNDARY-OPEN`,
`BOUNDARY-WINDOW`, `R-STRESS60`, and `MIXED` (**IV**). `R-REP128` is the controlling
repeated-number profile; `R-J2-J4` and `R-STRESS60` retain owner-open jump
candidates. Repository `7,200` block-domain values are parameter/planning values,
not an accepted fork-vector length or chain guarantee. Child-block time travel is
not a substitute for native ancestor-number behavior: **PA**.

## 6. Canonical token matrix

| Token/network | Address or deterministic expectation | Decimals | Authority/classification | Accepted now? |
|---|---|---:|---|---|
| WETH/mainnet | `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` | expected `18`; pin must prove | Address IV from Robinhood registry; decimals CPC | No; proxy/code/admin OAR |
| WETH/testnet | `0x7943e237c7F95DA44E0301572D358911207852Fa` | expected `18`; pin must prove | Address IV from Robinhood protocol registry; decimals CPC | No; proxy/code/admin OAR |
| USDG/mainnet | `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168` | issuer source says `6`; pin must prove | Address IV from Robinhood and Paxos; decimals/source binding CPC | No; proxy/code/layout OAR |
| USDG/testnet | `0x7E955252E15c84f5768B83c41a71F9eba181802F` | issuer source says `6`; pin must prove | Address IV from Paxos; decimals/source binding CPC | No; proxy/code/layout OAR |
| GREEN | direct frozen source expectation; address absent | `18` | Metadata/decimals IV; address IUD | No |
| RIPE | direct frozen source expectation; address absent | `18` | Metadata/decimals IV; address IUD | No |
| sGREEN | frozen ERC-4626 source over canonical GREEN; address absent | inherits GREEN decimals, expected `18` | Metadata/decimals rule IV; address IUD | No |

Frozen deterministic token metadata:

| Token | Name | Symbol | Source expectation |
|---|---|---|---|
| GREEN | `Green USD Stablecoin` | `GREEN` | IV |
| RIPE | `Ripe DAO Governance Token` | `RIPE` | IV |
| sGREEN | `Savings Green USD` | `sGREEN` | IV |
| USDG | `Global Dollar` | `USDG` | IV issuer-source fact; deployed binding CPC |

The H-04 core-token binding schedule requires exact Robinhood GREEN, RIPE, and
sGREEN addresses; source/runtime/ABI/compiler identities; token metadata; RipeHq
and plan placement; cross-record equality; H-05 typed-plan and H-06 binding; and no
Base address. None of those deployment identities may be inferred from the source.

`config/contract-artifact-expectations.json` has no GREEN, RIPE, or sGREEN artifact
entry at this baseline (**IV**). Their exact compiler input closure, settings, ABI,
creation bytecode, runtime bytecode, constructor encoding, source hashes,
deployment mechanism, and expected address are **IUD/OAR** until H-07 and the
deterministic H-05 plan produce them.

Canonical identity rules:

- only the listed official profile-specific WETH/USDG addresses are public
  candidates;
- a symbol/name match, bridged copy, mock, locally deployed clone, or Base address
  is **PA**;
- a noncanonical USDG clone can test generic ERC-20 behavior but can never satisfy
  canonical USDG qualification;
- testnet and mainnet records are independent and must never cross-fill; and
- a deterministic expected GREEN/RIPE/sGREEN address becomes accepted only when
  its exact H-05/H-06/H-07 inputs are frozen and recomputation matches.

### Chainlink constructor asset identities

`ChainlinkPrices.vy` requires nonzero `_wethAddr`, `_ethAddr`, and `_btcAddr` and
accepts `_ethUsdFeed` and `_btcUsdFeed` constructor choices. The frozen blueprint
tracks the unresolved package as `I-CHAINLINK-CORE` (CM-015/CM-016, owner
`OWN-ORACLE`, gate `B-ORACLE-FREEZE`) and its timelocks as
`I-CHAINLINK-TIMELOCKS` (CM-016, owner `OWN-H04`, gates `B-H04-PARAMS` and
`B-ORACLE-FREEZE`). Therefore:

| Constructor field | Current authority | Required owner input |
|---|---|---|
| `_ripeHq`, `_tempGov` | symbolic deployment dependencies | exact deterministic identities and governance handoff |
| `_minPriceChangeTimeLock`, `_maxPriceChangeTimeLock` | unresolved H-04 classes | exact values/bounds and cross-record equality |
| `_wethAddr` | official profile-specific WETH address is IV | accepted pin/code/behavior binding |
| `_ethAddr` | no accepted Robinhood native-ETH sentinel address | exact nonzero sentinel identity and semantics; OAR |
| `_btcAddr` | no accepted Robinhood BTC asset/sentinel identity | exact nonzero identity and semantics; OAR |
| `_ethUsdFeed` | mainnet ETH/USD is CPC; testnet UA | accepted per-profile feed or explicit blocked profile |
| `_btcUsdFeed` | mainnet BTC/USD is CPC; testnet UA | accepted per-profile feed or explicit owner-approved zero/no-price posture |
| `_defaultStaleTime` | H-04 `priceStaleTime` is `86,400`, but adapter constructor binding is unresolved | exact nonzero value and policy; OAR |

The constructor permits a zero BTC feed but does not permit a zero BTC asset
identity. A zero-feed decision would leave BTC without a default price and must be
an explicit owner posture; omission is not acceptance.

### GREEN, RIPE, and sGREEN constructor expectations

| Token | Exact frozen constructor fields | Value state |
|---|---|---|
| GREEN | `_ripeHq`, `_initialGov`, `_minHqTimeLock`, `_maxHqTimeLock`, `_initialSupply`, `_initialSupplyRecipient` | source signature IV; every deployed value OAR/IUD |
| RIPE | `_ripeHq`, `_initialGov`, `_minHqTimeLock`, `_maxHqTimeLock`, `_initialSupply`, `_initialSupplyRecipient` | source signature IV; every deployed value OAR/IUD |
| sGREEN | `_asset`, `_ripeHq`, `_initialGov`, `_minHqTimeLock`, `_maxHqTimeLock`, `_initialSupply`, `_initialSupplyRecipient` | source signature IV; every deployed value OAR/IUD; `_asset` must equal accepted GREEN |

The blueprint assigns each initial-supply quantity to `OWN-H04` and each
initial-supply recipient to `OWN-SECOPS`; deployment identities belong to
`OWN-H05`. These values are address- and artifact-determining. “Constructor
encoding” without every named value, owner record, and H-04/H-05/H-06/H-07
cross-check is incomplete.

## 7. Proxy, code, layout, and token-behavior matrix

### Proxy and code authority

| Token | Public/repository evidence | Missing accepted evidence | Classification |
|---|---|---|---|
| WETH mainnet | Robinhood registry address; Blockscout labels it a proxy with `aeWETH` implementation name | exact proxy type, implementation address, implementation slot, admin/beacon, proxy/implementation runtime hashes, upgrade history/freeze policy, ABI/compiler/source closure | Address IV; explorer structure CPC; remainder OAR |
| WETH testnet | Robinhood protocol registry address and L2 Proxy Admin address | exact proxy type, implementation address/slot, whether the published admin controls this proxy, runtime hashes, upgrade history/freeze policy, ABI/compiler/source closure | Addresses IV; deployed binding OAR |
| USDG mainnet/testnet | Paxos says interaction is through a proxy and USDG uses UUPS upgradeability; official addresses exist | pin-specific implementation, UUPS implementation slot, default admin/upgrade authority, proxy and implementation code hashes, source/compiler match, pending upgrade state, upgrade-freeze window | Source model IV; deployed bindings OAR |
| GREEN | frozen Vyper source is a direct deployable contract | H-07 artifacts, constructor, address, code hash, owner confirmation of direct/non-proxy policy | Source IV; deployment IUD/OAR |
| RIPE | frozen Vyper source is a direct deployable contract | same as GREEN | Source IV; deployment IUD/OAR |
| sGREEN | frozen Vyper ERC-4626 source is a direct deployable contract | same plus exact GREEN underlying and asset equality | Source IV; deployment IUD/OAR |

No proxy policy may be inferred from “ordinary source.” For GREEN, RIPE, and
sGREEN, the candidate expectation is direct deployment with no proxy, beacon, or
delegatecall, but owner acceptance is required. For USDG and WETH, reading only the
proxy runtime or only the implementation runtime is insufficient.

At the accepted pin, qualification must:

1. read the proxy runtime, implementation/admin/beacon slots applicable to the
   declared proxy type, and the resolved implementation runtime;
2. hash raw runtime bytes with Keccak-256 and compare exact owner values;
3. bind verified source, compiler/version/settings, creation/runtime artifacts, ABI,
   constructor/initializer, and metadata;
4. prove the implementation is not zero, self-referential, an EOA, or a different
   proxy;
5. prove no pending/proposed implementation or admin change violates the owner
   freeze window;
6. repeat code/slot reads after all tests and fail on drift; and
7. keep source verification labels and explorer names as CPC, never bytecode proof.

### Token behavior authority

| Behavior | GREEN / RIPE / sGREEN frozen expectation | USDG issuer-source candidate | WETH required proof |
|---|---|---|---|
| `transfer` / `transferFrom` return | ABI `bool`, exactly `true` on success | ABI `bool`, source returns `true` | detect exact return shape; owner bind |
| Empty/nonstandard return | rejected by strict qualification path | not expected | detect and owner decide; no silent assumption |
| Fee on transfer | none; exact sender/recipient balance deltas | none in pinned source candidate | exact wrap/transfer/unwrap delta proof |
| Pause | transfers/approvals/mint/burn blocked by token pause | transfers and approvals paused; supply controller may mint/burn | discover declared pause/emergency controls |
| Blocklist/freeze/sanctions | sender, recipient, spender checks; governance can burn blacklisted balance | asset-protection role can freeze/unfreeze/wipe; source also declares `SanctionedAddressListUpdate` | enumerate every active blocking mechanism and external list, not only pause/freeze; prove address, code, authority, call paths, and effects |
| Permit | EIP-2612 digest, 65-byte signature parameter, ERC-1271 support | standard `(v,r,s)` EIP-2612 and EIP-3009 in issuer source | do not assume permit |
| EIP-712 name/version | token name and `v1.0.0`; current chain ID; verifying contract | `Global Dollar` and version `1` in the pinned source candidate | owner bind or explicitly mark unsupported |
| Domain on chain change | GREEN/RIPE/sGREEN recompute if chain ID differs | issuer source recomputes | fork must retain Robinhood chain ID |
| Decimals | GREEN/RIPE `18`; sGREEN reads underlying decimals | `6` in issuer source | expected `18`, pin must prove |
| Zero transfer | frozen Ripe tokens reject amount zero | issuer behavior must be proven at pin | prove declared behavior |
| Upgradeability | no proxy logic in frozen token source | UUPS | explorer labels proxy; exact model OAR |

The repository already contains strict-return, false-return, fee-on-transfer,
pause/blocklist, signature/domain, and balance-delta mocks/tests. Those are **IV**
test assets, not proof of public-token behavior. Qualification must execute each
behavior against the canonical pinned token or its exact forked state.

### USDG layout and overlay prerequisites

Canonical upstream head
`paxosglobal/usdg-contract@5afb581e076f69ae46eb2e360f4dc63a71514a78`
pins submodule
`paxosglobal/paxos-token-contracts@74999fc56a91c6e78e829ed5b5b7da4ada9a79d4`.
In that source, `BaseStorage.sol` places `initializedV1` in slot `0`, `balances` in
slot `1`, and `totalSupply_` in slot `2`. `USDG.sol` declares 6 decimals and UUPS
upgrade authorization by `DEFAULT_ADMIN_ROLE`. These are **IV source facts** and
only **CPC** for a Robinhood deployment until the accepted implementation is
compiler/source matched.

The slot order is load-bearing on the exact Solidity inheritance linearization:
`PaxosTokenV2 is BaseStorage, EIP2612, EIP3009,
AccessControlDefaultAdminRulesUpgradeable`. EIP-712 reached through the permit/
authorization parents also declares state. A parent reorder, inserted base, changed
compiler/layout rule, or different implementation can move the slots even if
`BaseStorage.sol` itself is unchanged. Qualification must use the compiler-emitted
storage layout for the exact matched implementation; reading `BaseStorage.sol`
alone is **PA**.

The USDG overlay is prohibited until one immutable evidence bundle proves:

1. canonical network and proxy address;
2. exact proxy type, proxy runtime hash, implementation address and runtime hash,
   upgrade authority, and frozen upgrade state;
3. exact implementation source commit/submodule, compiler, optimizer/settings,
   metadata, ABI, and storage-layout output;
4. deployed layout equality for `balances` mapping slot `1` and `totalSupply_` slot
   `2`;
5. getter-to-slot equality:
   `balanceOf(actor) == storage[keccak256(pad(actor), pad(1))]` and
   `totalSupply() == storage[2]`;
6. USDG decimals exactly `6`, and an owner-approved positive overlay quantity `Q`
   expressed in exact base units with its human-unit derivation;
7. a deterministic actor, initial actor balance, initial total supply, and proof
   that the actor is not paused, frozen, sanctioned, blocklisted, or subject to any
   other transfer/supply control;
8. pre-overlay hashes for all touched slots, code, implementation/admin slots, and
   named control storage.

Only then may a fresh disposable fork apply exactly two matching deltas:

- actor balance slot: `+Q`; and
- slot `2` total supply: `+Q`.

Every other account, storage slot, allowance, nonce, role, pause/freeze/sanction/
blocklist identity and state, proxy/admin/implementation value, code byte, and
balance must remain unchanged. Post-write getters must equal the two storage
values. Any mismatch, extra write, unknown layout, proxy drift, or source/compiler
mismatch stops
`RB-USDG-OVERLAY-LAYOUT`. Rollback means destroying and recreating the disposable
fork from the accepted pin, never compensating writes.

## 8. Chainlink and sequencer matrix

### Mainnet feed candidates

Chainlink's current official Robinhood mainnet registry produced these public
candidates on 2026-07-30:

| Use | Feed name | Proxy | Secondary proxy | Current aggregator/contract | Decimals | Heartbeat | Deviation | Version | Classification |
|---|---|---|---|---|---:|---:|---:|---:|---|
| WETH/USD via ETH/USD | `ETH / USD` | `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9` | `0x5058aDee53b04e374d8bEDbAD634Bc4778F50b22` | `0x6091E64eb7138EEF066a80FD3A0d7427B91f2721` | `8` | `86400` | `0.5%` | `6` | CPC |
| BTC constructor route | `BTC / USD` | `0xa2c5184bF03d373Dc9dE4876eb4Bce595B460251` | `0x5a74F49d16fd0Cb866766d7e8EDb54DE36F6645A` | `0xc5845F87AD59a7a3D4bF9B90a0C19dbA38475EeC` | `8` | `86400` | `0.5%` | `6` | CPC; launch constructor decision required |
| USDG/USD | `USDG / USD` | `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2` | `0x901f56689360B89D7767a8acE28B7801e6348fa2` | `0x8bEeE3503F6860D5dac4cE26b5eEe92982951c2e` | `8` | `86400` | `0.5%` | `6` | CPC |
| Registry completeness; no current launch route | `USDC / USD` | `0x9e6f4605992a899eE2999999F3Ec80C41F452546` | `0x8929d7B1989459b3b1ec69066A06eab5c93B6d85` | `0xDADD7441395913A7468FAC020709e86AEfC04Ef9` | `8` | `86400` | `0.5%` | `6` | CPC |
| Registry completeness; no current launch route | `USDT / USD` | `0xbf3550B6fAe1671da7C238Af12e03Ac586BEf3B1` | `0x84dD63d9162DaA201c4Ea0a6dDbfBFB274F4514D` | `0x5644F992083C57aF913d5BdebA1D046c92Fb3424` | `8` | `86400` | `0.5%` | `6` | CPC |
| AAPL/USD if Stock is separately reopened | `Robinhood AAPL / USD` | `0x6B22A786bAa607d76728168703a39Ea9C99f2cD0` | `0x4bDbb3150014c6Ab2C6D9347B0779c49015a2f3f` | `0xBb11A21267cFDb63d4935d99a499133DD1744ACb` | `8` | `86400` registry value | `0.5%` | `6` | CPC; not launch-required under the parked Stock posture |

This is the qualification-relevant subset inspected on the evidence date, not the
complete mutable Robinhood registry, which also contains additional crypto,
exchange-rate, equity, and ETF feeds. BTC/USD is included because the frozen
constructor requires a BTC-asset decision. USDC/USD and USDT/USD are included to
close the specific public-registry review gap but remain unused unless an approved
protocol route names them. No statement that feeds are “fully enumerated” is
permitted unless an immutable registry snapshot and complete inventory hash are
attached.

The frozen `ChainlinkPrices.vy` constructor maps WETH to the ETH/USD feed and can
map the nonzero BTC identity to BTC/USD (**IV**). It rejects an answer `<= 0`,
cached feed decimals `> 18`, a future `updatedAt`, round ID zero,
`answeredInRound < roundId`, and a round older than the effective stale time. A
missing feed returns zero/no-feed. The effective stale time is the maximum of the
caller and configured values, so a larger configuration cannot be tightened by a
smaller call value.

Three fail-open/cached-state exposures are controlling:

1. `_staleTime == 0` disables staleness checking entirely. Every accepted
   registered feed must have a nonzero owner-approved configured stale time.
2. The adapter does not independently reject `updatedAt == 0`; it normally becomes
   stale, but with stale time zero the round can be accepted if its other fields
   pass. `updatedAt > 0` below is a qualification requirement, **not** a claim about
   current adapter enforcement. Adapter acceptance of that fixture fails
   qualification and requires separately authorized hardening or a fail-closed
   configuration proof.
3. Feed decimals are read and cached at registration, not re-read on every price.
   An aggregator/proxy change that alters decimals can silently mis-scale. The
   owner bundle and tests must bind both cached and current decimals and fail on
   proxy, aggregator, or decimal drift.

H-04 fixes `Defaults.genConfig.priceStaleTime` at `86,400` seconds (**IV
repository authority**). The owner must prove the selected feed heartbeat and
approve the exact adapter stale policy; a public heartbeat is not an acceptance
decision or uptime guarantee. The controlling disposition does **not** accept
`86,400` as the final production stale policy because it has no publisher-lateness
margin against the currently published `86,400` heartbeat. The network/oracle owner
must approve a policy with operating margin or separately accept the resulting
outage risk.

No Robinhood testnet ETH/USD, BTC/USD, USDG/USD, or equity-feed packet was found in
the official sources inspected: **UA + OAR**. Mainnet feeds must not be reused on
testnet: **PA**.

Stock activation is parked at this baseline. Therefore no equity feed is required
for the current launch fork profiles. If the owner reopens AAPL, it must supply the
exact token identity, multiplier/oracle-pause policy, session calendar, off-hours
stale policy, and accepted feed packet. Chainlink states that Robinhood equity feeds
are 24/5, may hold the last price off-hours without a heartbeat, and pause publishing
for corporate actions. Applying the crypto `86400` rule without the equity policy is
**PA**.

The AAPL registry object is internally mixed: it says `feedType: "Crypto"` while
`docs.assetClass` is `"Equity"` and `docs.marketHours` is
`"us_equities_24/5"`. The equity documentation controls the behavioral caution;
the registry heartbeat/category is not proof of continuous crypto cadence. This
inconsistency is another reason its heartbeat remains CPC rather than accepted
policy.

### Accepted feed bundle

For every required feed and profile, the owner must bind:

- asset and quote;
- primary proxy and whether the secondary proxy is permitted;
- current and proposed aggregator addresses;
- proxy, aggregator, and implementation runtime hashes;
- proxy/admin/upgrade model and freeze window;
- verified source/compiler/ABI;
- `description()`, `decimals()`, heartbeat, deviation threshold, feed category,
  market-hours/session behavior, and deprecation status;
- accepted pin block number/hash/state root;
- exact accepted `latestRoundData()` tuple:
  `(roundId, answer, startedAt, updatedAt, answeredInRound)`; and
- an owner record ID/SHA-256 and evidence date.

At the accepted pin, a valid price requires:

```text
feed exists and has non-empty code
roundId > 0
answer > 0
updatedAt > 0
updatedAt <= accepted block timestamp
answeredInRound >= roundId
configured stale limit > 0
accepted block timestamp - updatedAt <= accepted stale limit
cached decimals == current on-chain decimals == accepted decimals <= 18
proxy -> aggregator == accepted aggregator
all runtime hashes match
```

These are qualification invariants. In particular, `updatedAt > 0`, nonzero
configured stale time, and cached/current-decimal equality must be proven even
though the current adapter does not fully enforce them.

Zero, negative, future, stale, incomplete, missing, wrong-decimal, wrong-proxy, or
code-drifted data is unavailable price, never a fallback. The PriceDesk must not
select a different source implicitly; Uniswap and Curve are expressly prohibited
as Profile 1 fallback price authorities.

### Sequencer uptime

| Fact | Classification |
|---|---|
| Robinhood documentation recommends checking a Chainlink L2 sequencer uptime feed | IV public statement |
| Chainlink's current supported-network table does not list Robinhood | IV public registry observation |
| The current Robinhood feed JSON contains no sequencer uptime entry | IV public registry observation |
| Exact Robinhood mainnet/testnet sequencer feed proxy, implementation, code hashes, and round tuple | UA + OAR |
| Chainlink semantics: answer `0` up, `1` down; `startedAt` is the status-change time | IV platform semantics |
| `3600` seconds in Chainlink's example consumer | CPC example only; not accepted |
| Exact grace period and recovery policy | OAR |
| Current `ChainlinkPrices.vy` sequencer enforcement | absent; IV repository fact |
| Official Robinhood mainnet/testnet sequencer WebSocket feeds | IV public endpoints; operational signal only, not a Chainlink uptime contract or immutable archive proof |
| Official parent-L1 Rollup, Sequencer Inbox, and Delayed Inbox addresses | IV addresses; a liveness derivation/SLA remains CPC/OAR |

An Arbitrum One, Base, X Layer, or any same-address feed is not a Robinhood feed:
**PA**. Until Chainlink publishes an exact Robinhood address or the owner supplies
an equally authoritative verified deployment packet, any configuration claiming
on-chain sequencer protection must fail as missing feed.

The controlling policy is:

1. prefer an official Robinhood Chainlink sequencer uptime feed if an exact
   proxy/implementation becomes available and is owner-accepted; otherwise
2. require one explicitly approved operational policy that combines the selected
   Robinhood sequencer signal **and** parent-L1/inbox evidence.

The combined fallback must define the exact events/state/signals, finality, maximum
no-batch interval, contradiction handling, false-positive/false-negative bounds,
downtime and recovery timestamps, degraded-provider behavior, monitor, pause,
escalation, and recovery owners. It is operational gating, not in-protocol
Chainlink protection. Published addresses/endpoints alone do not define “up,”
“down,” a timeout, or recovery; describing them as an adapter check is **PA**.

Down, unknown, or contradictory state stops every price-dependent activation and
operation. Under Chainlink, recovery remains stopped until authoritative up status,
the approved grace period has elapsed, a fresh complete post-recovery price round
exists, and the monitoring owner confirms recovery. The operational policy must
bind an equally exact recovery timestamp/finality rule and the same four gates.
`3,600` seconds is a mandatory fork-test recovery vector, but it is not the frozen
production grace policy. Restarting the clock from a local/test timestamp is
**PA**.

## 9. Exact missing owner-input packet

The following is the consolidated minimum packet. It must be immutable, hash-bound,
profile-specific, and signed/approved by the named owners. Secret values are not
part of the packet.

| # | Record | Exact minimum input | Frozen repository cross-reference and owner/gate |
|---:|---|---|---|
| 1 | Scope | incorporate the controlling disposition below into the final signed packet; Profile 1 mainnet first, Profile 1 testnet after its oracle/external packet, Profile 2 staged; owner/approval IDs; expiry/revalidation; packet SHA-256; deferred report-registration disposition | Policy scope is recorded here but the immutable packet remains open; H-07 protocol/security/independent reviewers plus `OWN-H08`, `OWN-H09`, and `OWN-SECOPS`; `status.yaml` remains sole machine-readable authority |
| 2 | Fork pin | complete section 3 record per profile; parent L1; adjacent headers; roots/proofs; representative receipt; L1 fields; finality | H-02/S5 network and action-block evidence; `BN-*`/`CM-*` clock registers; exact new acceptance by `OWN-S5`/`OWN-H09` |
| 3 | RPC | approved L2 and any selected L1 archive product; aliases only; endpoint fingerprints; read-only whitelist; `eth_getProof`; retention/rate/retry receipt; redaction | `config/network_profiles.py`; H-02/S5 endpoint contract; `I-LEDGER-BLOCK-SOURCE` (CM-008, `OWN-S5`, `B-S5-LEDGER`) |
| 4 | Engine | exact engine/version/source/artifact; Nitro/ArbOS/ArbSys/NodeInterface closure; chain-info/genesis/image hashes; every section 5 relationship | `I-LEDGER-BLOCK-SOURCE`; H-07 artifact and H-09 qualification owners; Titanoboa `0.2.7` alone is not acceptable |
| 5 | Canonical tokens | accepted mainnet/testnet WETH and USDG; all proxy/implementation/admin/beacon/UUPS slots; runtimes/source/compiler/ABI; accepted decimals; domains; every pause/freeze/sanction/blocklist/fee/return behavior; upgrade freeze | `I-WETH` (CM-024/CM-031, `OWN-H04`, `B-H05-PLAN`); `I-USDG` (CM-016/CM-024/CM-048, `OWN-T8`, `B-H05-PLAN`); `I-ENDAOMENT-NATIVE-METADATA` and `BS-H04-ENDAOMENT-METADATA-RC` (CM-031, `OWN-H04`, `B-H04-PARAMS`/`B-H05-PLAN`) |
| 6 | USDG overlay | exact implementation/layout/linearization proof; slots `1`/`2`; getter proof; owner-approved positive `Q`; actor; exact two writes; unchanged set; destruction rollback; failure code | `I-USDG`; compiler/layout authority remains owner-supplied; `RB-USDG-OVERLAY-LAYOUT` |
| 7 | Ripe-token artifacts | exact GREEN/RIPE/sGREEN H-07 closure; every section 6 constructor value; compiler/settings; ABI/creation/runtime; direct/proxy policy; deterministic addresses; RipeHq/GREEN asset equality | `I-GREEN`/`I-RIPE`/`I-SGREEN` (`OWN-H05`); six `*-INITIAL-SUPPLY*` rows (`OWN-H04` quantities, `OWN-SECOPS` recipients); `BS-H04-CORE-TOKEN-IDENTITIES-RC`, `BS-H04-SUPPLY-RECIPIENTS-OP` |
| 8 | Oracles | every `ChainlinkPrices.vy` constructor field; accepted ETH/USD, BTC/USD, and USDG/USD disposition per profile; exact pin rounds; nonzero stale policy; cached/current decimals; timelocks; missing/secondary/upgrade policy; AAPL parked or separate packet | `I-CHAINLINK-CORE` (CM-015/CM-016, `OWN-ORACLE`, `B-ORACLE-FREEZE`); `I-CHAINLINK-TIMELOCKS` (CM-016, `OWN-H04`); `I-USDG-FEED` (CM-016/CM-048, `OWN-ORACLE`) |
| 9 | Sequencer | one section 8 policy; exact feed or L1/endpoint observation definition; code/source if on-chain; aliases if L1; grace/down/recovery/fresh-round rules; monitor/pause authority; residual risk | `B-ORACLE-FREEZE`, `B-SECOPS-HANDOFF`; `OWN-ORACLE` and `OWN-SECOPS` |
| 10 | Lifecycle | H-07 artifact authority; H-08 fixture/assertion API; H-09 API/output ceiling; exact path ceiling; registration in the lifecycle indexes; maximum result remains non-authoritative `LOCAL_FORK_QUALIFIED` | H-07/H-08/H-09; follow-up registration in `status.yaml`, `START-HERE.md`, `AGENT-HANDOFF.md`, and/or `decision-register.md` only under separate file authority |

The packet must say explicitly: “Public candidates in
`network-token-oracle-authority.md` are not accepted configuration unless repeated
in this owner record.” Silence is not acceptance.

## 10. Fork fixtures and negative-test specification

### Required positive fixtures

| Fixture | Required contents | Gate |
|---|---|---|
| `FIX-RH-NETWORK` | profile, chain ID, exact block/adjacent headers, state roots, finality record | all exact |
| `FIX-RH-RPC` | redacted provider receipt, archive proof, method inventory, retry transcript | no secret; whitelist subset |
| `FIX-RH-CLOCK` | parent-L1 identity, block and receipt L1 fields, NodeInterface mapping, ArbSys child/version values, EVM `NUMBER`, EVM timestamp, repeated-ancestor pair | all section 5 relationships |
| `FIX-RH-WETH` | proxy/implementation/admin/code, metadata, wrap/unwrap/transfer deltas, control/return behavior | owner record match |
| `FIX-RH-USDG` | proxy/UUPS/admin/code/source/layout, metadata, permit/control behavior, overlay pre/post/unchanged set | owner record match |
| `FIX-RH-RIPE-TOKENS` | H-07 artifacts, every constructor input, deterministic deployments, metadata, permit, pause/blocklist/fee/return tests | H-04/H-05/H-06/H-07 match |
| `FIX-RH-ORACLES` | every adapter constructor input; ETH/BTC/USDG feed disposition; proxy/aggregator/code; metadata; cached/current decimals; accepted round tuples and nonzero stale policy | owner record match |
| `FIX-RH-SEQUENCER` | exact Chainlink feed or exact combined Robinhood-signal plus parent-L1/inbox operational policy; down/unknown/contradictory/recovery/grace/fresh-round/monitor-confirmation states | owner record match |

Every evidence artifact must include schema version, profile, frozen repository
commit/tree, owner packet ID/hash, fixture ID, engine ID/hash, pin number/hash/state
root, UTC evidence time, result, failure code if any, and artifact SHA-256. It must
contain no URL credential, signer, account key, or expanded secret.

### Exact fail-closed negative tests

The codes below are required qualification outcomes. They do not authorize
implementation in this tranche.

| Failure code | Negative stimulus | Required fail-closed assertion and evidence |
|---|---|---|
| `RHQ-PIN-MISMATCH` | wrong child number, hash, parent hash, timestamp, `stateRoot`, parent-L1 profile, or L1 field; number/hash calls disagree | stop before fork creation; emit expected/observed non-secret fields and both raw-response hashes |
| `RHQ-RPC-NONARCHIVE` | `null`, pruned state, missing trie node, latest-state substitution, missing old code/storage/proof | stop before scenarios; no provider fallback; record method, block, error class, response hash |
| `RHQ-RPC-METHOD` | required method unsupported or an unapproved method observed | stop; exact missing/unexpected method set; no broadened whitelist at runtime |
| `RHQ-CHAIN-ID` | observed chain ID is not profile chain ID | stop before any state read beyond identity; no cross-profile retry |
| `RB-CLOCK-CURVE` | child/receipt/NodeInterface/ArbSys mismatch; EVM `NUMBER` equals child number; wrong timestamp; no repeated ancestor pair; wrong ArbOS version | stop both profiles before Curve scenario; do not patch `CurvePrices.vy` |
| `RHQ-PROXY-BINDING` | wrong proxy type, implementation/admin/beacon slot, zero/EOA/self implementation, proposed upgrade drift | stop token/feed qualification; no direct-implementation fallback |
| `RHQ-CODE-HASH` | proxy, implementation, token, feed, or ArbSys runtime differs before or after tests | stop and destroy fork; record address, expected/observed hashes, pin |
| `RHQ-TOKEN-DECIMALS` | any token or feed decimals differ from the owner-accepted per-address value, including sGREEN/asset inequality | stop before amount construction; no rescaling guess |
| `RHQ-TOKEN-RETURN` | return is false, empty when strict bool required, short, long, malformed, or noncanonical | revert caller path; state/balances/allowances unchanged |
| `RHQ-TOKEN-PERMIT-DOMAIN` | wrong name/version/chain ID/verifying contract, nonce, deadline, signature shape, signer, or replay | permit fails; allowance and nonce unchanged except a successful canonical case increments exactly once |
| `RHQ-TOKEN-BEHAVIOR` | pause/freeze/sanction/blocklist mechanism does not block expected actor; undisclosed mechanism exists; unexpected fee; wrong balance delta; unauthorized wipe/mint/burn | revert/zero acceptance; exact pre/post balances, allowance, supply, every control/list identity and state unchanged |
| `RB-USDG-OVERLAY-LAYOUT` | layout/source/linearization/getter mismatch, wrong slot or owner `Q`, extra write, code/admin drift, compensating rollback | stop and destroy fork; never label clone/unknown layout canonical |
| `RHQ-ORACLE-ROUND` | zero/negative answer, round ID zero, `updatedAt=0`, future/stale time, `answeredInRound < roundId`, wrong decimals, proxy/aggregator drift | qualification rejects and prevents price-dependent action; if the current adapter returns nonzero, preserve that as failing evidence and block rather than claiming adapter rejection |
| `RHQ-ORACLE-STALE-DISABLED` | any registered feed has configured stale time zero or accepts `updatedAt=0` | fail configuration/qualification; no caller-supplied value may disguise the zero configuration |
| `RHQ-ORACLE-CACHED-DECIMALS` | cached decimals differ from current proxy/aggregator decimals before or after an upgrade | fail and prevent pricing; no rescaling or cache assumption |
| `RHQ-ORACLE-CONSTRUCTOR` | zero/incorrect ETH or BTC sentinel, wrong WETH/BTC identity, missing required constructor field, or unapproved zero BTC feed posture | fail artifact/configuration before scenarios |
| `RHQ-SEQUENCER-DOWN` | Chainlink answer is not exactly `0`, or selected operational policy reports down/unknown | stop all price-dependent actions; price round validity cannot override |
| `RHQ-SEQUENCER-GRACE` | status recovered but elapsed time is `<=` approved grace, authoritative recovery time is invalid, no fresh post-recovery price, or no monitoring-owner confirmation | remain stopped; required `3,600` fork vector proves `3,599` and `3,600` fail and only post-boundary recovery with every other gate may pass; production grace remains OAR |
| `RHQ-ORACLE-MISSING-FEED` | zero address, no code, absent required ETH/BTC/USDG testnet feed, missing sequencer feed under on-chain policy, or unapproved equity feed | fail configuration and scenario setup; no mainnet/testnet or cross-chain substitution |

Additional invariants:

- each negative test runs on a fresh disposable fork or restores by destruction and
  recreation, never compensating transactions or storage writes;
- a failure in one required profile cannot be masked by a pass in another;
- an expected revert is a pass only if the intended failure code and unchanged
  post-state are both proven;
- accepted price data is never synthesized;
- mocks exercise failure handling but cannot close canonical identity gates; and
- H-09 alone aggregates results. A test runner cannot emit a stronger verdict.

## 11. What can be automated now

The following can be implemented offline after separate file/scope authorization;
none was implemented by this report:

1. validate the owner-packet schema, hashes, profile separation, and expiry;
2. lint RPC aliases and evidence for secret leakage without resolving a secret;
3. validate method inventories against the exact whitelist;
4. recompute repository commit/tree, source hashes, compiler inputs, ABI hashes,
   creation/runtime artifacts, constructors, and deterministic addresses once H-07
   inputs exist;
5. compare owner-supplied block/header/proof/receipt JSON fixtures without RPC;
6. validate proxy/implementation/admin/code-hash records from owner-supplied
   evidence;
7. compile the exact owner-approved USDG source and compare storage-layout output;
8. generate the owner-`Q` two-write USDG overlay plan and unchanged-state assertions
   without applying it;
9. run existing local mocks for malformed returns, fees, every pause/freeze/
   sanction/blocklist mechanism, permit domains, zero stale configuration,
   stale/zero/negative/incomplete rounds, cached-decimal drift, sequencer states,
   and missing feeds;
10. validate Chainlink candidate registry snapshots against owner-approved feed
    records while preserving CPC status;
11. generate H-08/H-09 fixture manifests, negative-test ledgers, and SHA-256
    inventories from approved APIs; and
12. prepare a separate, reviewable registration patch for `status.yaml`,
    `START-HERE.md`, `AGENT-HANDOFF.md`, and/or `decision-register.md` once the
    lifecycle owner specifies the canonical index targets; do not apply it before
    separately authorized cross-agent synthesis.

Automation must stop on missing owner fields. It must not fill them from this
report, public registries, historical evidence, Base configuration, a current
chain tip, or a mock.

## 12. What remains impossible

Without the section 9 packet and separately authorized execution:

- a fork cannot be started;
- archive capability cannot be proven;
- the accepted block/state root cannot be selected or reproduced;
- clock fidelity cannot be demonstrated;
- current proxy/implementation/admin/runtime state cannot be bound;
- canonical USDG storage cannot be overlaid;
- current token pause/freeze/permit/fee/return behavior cannot be proven at the pin;
- ETH/BTC sentinel identities and the complete `ChainlinkPrices.vy` constructor
  cannot be accepted;
- a Chainlink round or cached/current-decimal binding cannot be accepted;
- Robinhood sequencer protection or an alternative operational-liveness policy
  cannot be accepted;
- the public testnet WETH identity cannot be promoted to accepted runtime/behavior
  configuration, and testnet oracle identities remain unavailable;
- GREEN, RIPE, and sGREEN exact deployment addresses and deployed code cannot exist
  before the deterministic plan/deployment creates them; and
- H-08/H-09 cannot produce even non-authoritative `LOCAL_FORK_QUALIFIED`.

Public investigation cannot make deployment-only facts available. A report,
official address, verified source, explorer label, passing mock, or green offline
suite cannot substitute for a pinned runtime/layout/behavior proof.

## 13. Source links and evidence dates

All public sources were read on 2026-07-30. Links are primary official
documentation, canonical upstream repositories, or the official Robinhood
explorer.

| Source | Use | Classification/date |
|---|---|---|
| [Robinhood: Connecting to Robinhood Chain](https://docs.robinhood.com/chain/connecting/) | chain IDs, provider/archive guidance, public endpoint limitation | IV, 2026-07-30 |
| [Robinhood: Run a full node](https://docs.robinhood.com/chain/run-a-full-node/) | Nitro image, ArbOS 61, chain-info/genesis model | IV public candidate, 2026-07-30 |
| [Robinhood: Differences from Ethereum](https://docs.robinhood.com/chain/differences-from-ethereum/) | L1-estimate `block.number`, ArbSys child number | IV, 2026-07-30 |
| [Robinhood: Token contracts](https://docs.robinhood.com/chain/contracts/) | canonical mainnet WETH/USDG addresses | IV, 2026-07-30 |
| [Robinhood: Protocol contracts](https://docs.robinhood.com/chain/protocol-contracts/) | parent-L1 identities, mainnet/testnet WETH, proxy admins, NodeInterface, inboxes | IV addresses; behavior/pin OAR, 2026-07-30 |
| [Robinhood: Oracles and price feeds](https://docs.robinhood.com/chain/oracles-and-price-feeds/) | AggregatorV3, staleness, sequencer recommendation, equity behavior | IV, 2026-07-30 |
| [Paxos: USDG main networks](https://docs.paxos.com/guides/stablecoin/usdg/mainnet) | mainnet USDG and supply-control addresses, chain ID | IV, 2026-07-30 |
| [Paxos: USDG test networks](https://docs.paxos.com/guides/stablecoin/usdg/testnet) | testnet USDG and supply-control addresses | IV, 2026-07-30 |
| [Paxos USDG canonical repository](https://github.com/paxosglobal/usdg-contract/tree/5afb581e076f69ae46eb2e360f4dc63a71514a78) | token source, UUPS, decimals, source pin | IV source; deployed binding CPC, 2026-07-30 |
| [Paxos token submodule](https://github.com/paxosglobal/paxos-token-contracts/tree/74999fc56a91c6e78e829ed5b5b7da4ada9a79d4) | storage and token behavior source | IV source; deployed binding CPC, 2026-07-30 |
| [Chainlink Robinhood feed registry JSON](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json) | current mainnet feed candidates and metadata | CPC, 2026-07-30 |
| [Chainlink: Robinhood tokenized equities](https://docs.chain.link/data-feeds/tokenized-equity-feeds/robinhood) | multiplier, corporate-action pause, 24/5/off-hours behavior | IV platform behavior; feed acceptance OAR, 2026-07-30 |
| [Chainlink: L2 sequencer uptime feeds](https://docs.chain.link/data-feeds/l2-sequencer-feeds) | supported network list, status/grace semantics | IV, 2026-07-30 |
| [Arbitrum: Block numbers and time](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time) | child/L1/EVM/ArbSys/timestamp relationships | IV, 2026-07-30 |
| [Arbitrum: RPC methods](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/rpc-methods) | receipt/block `l1BlockNumber` distinctions | IV, 2026-07-30 |
| [Offchain Labs Nitro commit](https://github.com/OffchainLabs/nitro/commit/3599acae1ad2fab4059fc46453c9cd3294126641) | canonical source provenance for published short commit | IV source existence; acceptance OAR, 2026-07-30 |
| [Robinhood Blockscout: WETH](https://robinhoodchain.blockscout.com/address/0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73) | proxy/implementation-name public candidate | CPC, 2026-07-30 |
| [Robinhood Blockscout: USDG](https://robinhoodchain.blockscout.com/address/0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168) | proxy/implementation-name public candidate | CPC, 2026-07-30 |

Source integrity notes:

- the Chainlink registry values were read as public JSON, not by calling a feed;
- the feed table is a qualification-relevant subset of a mutable registry, not a
  complete feed inventory;
- GitHub source refs were read without cloning into the repository;
- explorer labels were not treated as code-hash, layout, admin, or current-state
  proof;
- no historical repository evidence was upgraded to current public-chain fact; and
- all drift-prone public candidates require revalidation and owner acceptance at the
  eventual fork pin.

## 14. Explicit non-actions

This investigation did not:

- connect to a Robinhood, Ethereum, Chainlink, token, or other JSON-RPC endpoint;
- query a public chain, start a fork, create a local chain, replay a transaction, or
  call a contract;
- access, resolve, display, validate, or transmit an RPC secret, API key, signer,
  account, private key, mnemonic, or credential;
- run a migration, deployment, configuration, verification submission, overlay, or
  state mutation;
- modify a contract, configuration, manifest, inventory, migration, schema, test,
  existing document, Git index, commit, remote, public-chain, service, or protocol
  state; the sole local archive copy below is explicitly authorized;
- stage, commit, push, merge, deploy, publish, activate, release, or reconcile;
- promote a public candidate to accepted configuration;
- infer a testnet value from mainnet, a Robinhood value from Base/Arbitrum One, or a
  deployed identity from a symbol/source; or
- authorize fork execution. This report is authority preparation only.

This report remains untracked in a mode-0700 worktree under `/private/tmp`. The
controlling disposition below authorizes exactly one byte-identical mode-0600
archive copy under mode-0700 directories at
`/Users/wigglez/dev/ripe-protocol-review-archives/qualification/network-token-oracle-authority.md`.
It does not authorize a Git-tracked copy, lifecycle registration, commit, push, or
any other external mutation.

### Controlling owner scope and policy disposition

**Disposition date: 2026-07-30. Status: controlling policy; all ten blocker classes
remain open. This disposition does not authorize fork execution.**

Qualification scope:

1. Qualify Profile 1 Robinhood mainnet first as the launch-critical fork profile.
2. Qualify Profile 1 Robinhood testnet as the deployment-rehearsal profile only
   after its exact oracle and external-identity packet exists.
3. Keep Profile 2 as the staged Curve/follow-on profile.
4. Give every profile its own immutable pin, provider receipt, external manifest,
   oracle packet, and evidence; prohibit cross-profile substitution.
5. Do not accept a public candidate unless it is repeated in the final signed owner
   packet.
6. Revalidate after any pin, provider, engine, proxy, implementation, admin, code
   hash, token behavior, oracle, sequencer policy, constructor, compiler, artifact,
   or deployment-plan change.

Fork pin and provider:

7. Do not select or invent a block number, hash, parent hash, state root, parent-L1
   record, or finality evidence in this report.
8. Do not select or resolve an RPC URL or secret.
9. Require a deployment-owner-selected archive-capable provider using secret aliases
   only.
10. Require exact method, proof, retention, retry, timeout, rate-limit, and endpoint-
    fingerprint evidence before fork creation.
11. Require an independently selected immutable fork engine/version that proves the
    complete child/L1/EVM/NodeInterface/ArbSys clock relationship.
12. Do not accept Titanoboa `0.2.7` alone as that proof.

Canonical tokens:

13. Preserve the official Robinhood mainnet/testnet WETH and USDG addresses as IV
    public facts and CPC configuration candidates.
14. Do not accept them until the pin proves proxy type, implementation, admin/
    beacon/UUPS slots, runtimes, code hashes, source/compiler/ABI, decimals,
    domains, controls, fees, transfer returns, and upgrade state.
15. Preserve direct, non-proxy deployment as the preferred GREEN/RIPE/sGREEN
    architecture.
16. Require a separate owner/security decision for any proxy, beacon, or delegatecall
    proposal for those Ripe tokens.
17. Keep final GREEN/RIPE/sGREEN addresses IUD until H-05/H-07 close constructors,
    artifacts, initial supplies, recipients, and deterministic identities.
18. Bind sGREEN exactly to the accepted GREEN asset.

USDG overlay:

19. Do not approve a fixed overlay quantity in this report.
20. Require the final fork packet to select one exact positive `Q` derived from the
    approved scenario envelope.
21. Prohibit the overlay until compiler-derived and deployed evidence proves the
    proxy, implementation, source, linearization, balance mapping slot `1`,
    `totalSupply_` slot `2`, getter correspondence, and decimals.
22. Permit only `deterministic actor balance += Q` and `total supply += Q`.
23. Require every other storage/code/admin value to remain unchanged.
24. Define rollback as fork destruction and recreation, never compensating writes.

Oracle policy:

25. Keep Chainlink as the Profile 1 price authority.
26. Do not add Uniswap or Curve as a fallback source.
27. Require accepted ETH/USD, BTC/USD-disposition, and USDG/USD constructor packets
    for every profile.
28. Keep AAPL/equity feeds outside the initial launch packet unless Stock activation
    is explicitly reopened.
29. If Stock is reopened, require a separate 24/5 packet covering token identity,
    sessions/off-hours, multiplier, corporate-action pause, and accepted rounds.
30. Require a nonzero stale policy for every registered feed.
31. Do not accept `86,400` seconds as final production stale policy because it has no
    publisher-lateness margin against the currently published heartbeat.
32. Require the network/oracle owner either to approve a feed/stale policy with
    acceptable operating margin or separately accept the outage risk.
33. Make zero stale time, `updatedAt=0`, stale, future, negative, incomplete, wrong-
    decimal, wrong-proxy, and cached-decimal drift mandatory failures.

Sequencer policy:

34. Prefer an official Robinhood Chainlink sequencer uptime feed if an exact proxy/
    implementation becomes available and is accepted.
35. Do not invent or substitute a sequencer feed address.
36. If no official feed exists, require an explicitly approved operational policy
    combining the selected Robinhood sequencer signal and parent-L1/inbox evidence.
37. Describe that fallback truthfully as operational gating, not an in-adapter
    Chainlink check.
38. Stop every price-dependent activation and operation on down, unknown, or
    contradictory state.
39. Use `3,600` seconds as a required fork-test recovery vector, not a frozen
    production policy.
40. Require authoritative up status, elapsed approved grace, a fresh complete
    post-recovery round, and monitoring-owner confirmation for recovery.
41. Bind monitor, pause, escalation, and recovery authority before deployment
    qualification closes.

Lifecycle:

42. Preserve all ten blocker classes as open until the final immutable packet
    supplies their exact artifacts.
43. Do not create local substitute H-07, H-08, or H-09 authorities.
44. Cap the eventual verdict at `LOCAL_FORK_QUALIFIED`; it is not deployment,
    activation, or release authority.
45. Do not register this report in `status.yaml` or another lifecycle index until
    separately authorized during cross-agent synthesis.
