# Robinhood canonical launch-input verification

> **Evidence only — not configuration or deployment authority**

Retrieval and inspection date: `2026-08-01`. This is a read-only reconciliation package. It does not edit, replace, approve, publish, deploy, configure, or activate any launch input.

## Executive verdict

The exact `rh` source is internally consistent, but it is **not deployment-ready**. The canonical check reports `configuration_consistent=true`, `deployment_ready=false`, and exactly `58` blockers. No blocker is closed by this report. Official documentation and repository evidence partially corroborate several candidates, but immutable-pin observations, owner decisions, SecOps bindings, and deployment-produced identities remain outside this evidence-only authority.

The prior PR #66 census is independently reproducible: `322` PR-bound historical rows minus `70` explicit Profile 2 omissions equals `252` selected records. Those records include five asset tuples with `31` leaves each (`155` leaves). After canonical scalar/list normalization, `244` values are exact semantic matches; `7` PR typed-null deployment identities are refined to current named symbolic bindings but remain unresolved; and `1` priority-list value is intentionally transformed. Every selected record has exactly one classification in the TSV: `229` `already_accepted_current_authority`, `15` `selected_external_fact_unverified`, `7` `deployment_produced_unresolved`, and `1` `intentionally_transformed`. There are zero selected-record rows in the other five states: `0` independently verified, `0` superseded, `0` reopened, `0` obsolete implementation details, and `0` unexplained conflicts. Those latter classes occur only in supplementary implementation/decision rows where applicable.

## Baseline

| Binding | Exact value | Result |
|---|---|---|
| Local `rh` | `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353` | exact |
| Cached `origin/rh` | `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353` | exact |
| Credential-free live `origin/rh` | `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353` | exact |
| Commit tree | `7454b5456ebb6cd02d716a64b408629ab501629e` | exact |
| PR #66 commit | `0f79b626c6ec4788ba43b3132ada9ebec6084f2a` | inspected as history, not current authority |
| PR #66 tree | `d198a3e70b420a5d1de1f272f9c785506d91da4d` | exact |
| Isolated checkout | detached, mode `0700` | no feature branch; active worktrees untouched |
| Primary worktree before inspection | tracked/index/ordinary-untracked clean | pre-existing ignored files inventoried and untouched |

## Current source authority

Only `config/BluePrint.py` and `contracts/config/DefaultsRobinhood.vy` are human-edited launch-input authorities in this reconciliation. `config/robinhood_blueprint.py` and `config/robinhood-parameters.json` are derived evidence, Markdown is explanatory evidence, tests enforce contracts, and migrations consume approved values. PR #66 is historical input/provenance, not proof of current implementation, addresses, code, controls, operators, funding, or onchain configuration.

The current selected Profile 1 address candidates are USDG `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`, SteakHouse USDG vault `0xBeEff033F34C046626B8D0A041844C5d1A5409dd`, and governance/safe `0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf`. GREEN, RIPE, sGREEN, guardian, training-wheels, and contributor-template addresses remain deployment-produced and unresolved.

## PR #66 reconciliation

The TSV rows `P-H04-001` through `P-H04-435` are sparse identifiers but collectively contain all `252` selected records. Each row carries the PR path/value, current destination/value, authority class, current blocker, required action, and downstream consumer. Numeric-string normalization is representation-only; it is not a value change. Seven deployment-produced rows replace historical typed-null descriptions with exact named symbolic bindings while staying unresolved. `P-H04-304` is the sole selected-record value transformation: raw PR priority IDs `[1,2,3]` become current `[1,3]`.

Known implementation incompatibilities are separately typed because they are not extra selected input records:

| TSV record | PR #66 detail | Current disposition |
|---|---|---|
| `SUP-PR-001` | `DefaultsRobinHood.vy` casing | superseded by `DefaultsRobinhood.vy` |
| `SUP-PR-002` | five constructor inputs | superseded by the current eight ordered Defaults bindings |
| `SUP-PR-003` | BlueChipYield PriceDesk ID 2 | intentionally transformed to ID 3 |
| `SUP-PR-004` | priority `[1,2,3]` | intentionally transformed to `[1,3]` |
| `SUP-PR-005` | mainnet-only migration layout | obsolete; current migration architecture is shared |
| `SUP-PR-006` | custom runner/history | obsolete; do not resurrect |
| `SUP-PR-007` | older Morpho implementation | superseded by integrated Morpho V2 code/tests |
| `SUP-PR-008` | disabled legacy Curve create/fund implementation | obsolete implementation; Curve concept is separately reopened in `SUP-CURVE-001` |

Unresolved identities in PR #66 remain candidates only. Later Curve, AAPL, reward, LP, PSM, and CCIP decisions are represented by current blockers and supplementary rows. No mismatch was silently resolved and there is no unexplained conflict.

## Current readiness result

The canonical check-only generator returned:

```text
H04_OK sha256=0750856092889476e3ec8e54305e74dc0152c576dfa687a8c08934fc85c0893c configuration_consistent=true deployment_ready=false blockers=58
```

The result binds commit `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`, tree `7454b5456ebb6cd02d716a64b408629ab501629e`, and derived-ledger SHA-256 `0750856092889476e3ec8e54305e74dc0152c576dfa687a8c08934fc85c0893c`. The blocker category census is: `18` address facts/identities; `1` ledger-action fork binding; `8` PSM configuration/execution inputs; `16` AAPL/stock inputs; `1` stability input; `4` LP inputs; `1` rewards promotion; `1` CCIP promotion; `2` role bindings; `3` initial-supply recipients; and `3` Endaoment native-metadata inputs.

### Exact blocker map

Each key appears exactly once as the `Current blocker` in one dedicated TSV blocker row:

- `BLK-001` — `address:ARB_SYS:unverified`
- `BLK-002` — `address:BTC_SENTINEL:unverified`
- `BLK-003` — `address:CHAINLINK_BTC_USD:unverified`
- `BLK-004` — `address:CHAINLINK_ETH_USD:unverified`
- `BLK-005` — `address:CHAINLINK_USDG_USD:unverified`
- `BLK-006` — `address:CONTRIBUTOR_TEMPLATE:unresolved`
- `BLK-007` — `address:GOVERNANCE:unverified`
- `BLK-008` — `address:GREEN_TOKEN:unresolved`
- `BLK-009` — `address:GUARDIAN:unresolved`
- `BLK-010` — `address:MORPHO_V2_FACTORY:unverified`
- `BLK-011` — `address:NATIVE_ETH_SENTINEL:unverified`
- `BLK-012` — `address:RIPE_TOKEN:unresolved`
- `BLK-013` — `address:SAFE:unverified`
- `BLK-014` — `address:SGREEN_TOKEN:unresolved`
- `BLK-015` — `address:STEAKHOUSE_USDG_VAULT:unverified`
- `BLK-016` — `address:TRAINING_WHEELS:unresolved`
- `BLK-017` — `address:USDG:unverified`
- `BLK-018` — `address:WETH:unverified`
- `BLK-019` — `input:Deployment.DP-04.ledger.actionBlockSourceBinding:unresolved`
- `BLK-020` — `input:Deployment.DP-08.psm.allowlists:unresolved`
- `BLK-021` — `input:Deployment.DP-08.psm.maxMintPerInterval:unresolved`
- `BLK-022` — `input:Deployment.DP-08.psm.maxRedeemPerInterval:unresolved`
- `BLK-023` — `input:Deployment.DP-08.psm.mintFee:unresolved`
- `BLK-024` — `input:Deployment.DP-08.psm.numBlocksPerInterval:unresolved`
- `BLK-025` — `input:Deployment.DP-08.psm.redeemFee:unresolved`
- `BLK-026` — `input:Deployment.DP-08.psm.reserveFunding:unresolved`
- `BLK-027` — `input:Deployment.DP-09.psm.executionBinding:unresolved`
- `BLK-028` — `input:Deployment.DP-10.aapl.P8:unresolved`
- `BLK-029` — `input:Deployment.DP-10.aapl.auction:unresolved`
- `BLK-030` — `input:Deployment.DP-10.aapl.decimals:unresolved`
- `BLK-031` — `input:Deployment.DP-10.aapl.feed:unresolved`
- `BLK-032` — `input:Deployment.DP-10.aapl.globalCap:unresolved`
- `BLK-033` — `input:Deployment.DP-10.aapl.identity:unresolved`
- `BLK-034` — `input:Deployment.DP-10.aapl.perUserCap:unresolved`
- `BLK-035` — `input:Deployment.DP-10.aapl.risk:unresolved`
- `BLK-036` — `input:Deployment.DP-10.aapl.route:unresolved`
- `BLK-037` — `input:Deployment.DP-10.aapl.vault:unresolved`
- `BLK-038` — `input:Deployment.DP-11.stock.m2Movement:unresolved`
- `BLK-039` — `input:Deployment.DP-11.stock.m3CreditContainment:unresolved`
- `BLK-040` — `input:Deployment.DP-11.stock.m4ComposedProof:unresolved`
- `BLK-041` — `input:Deployment.DP-11.stock.m5ActivationBinding:unresolved`
- `BLK-042` — `input:Deployment.DP-11.stock.vaultArtifact:unresolved`
- `BLK-043` — `input:Deployment.DP-11.stock.vaultSlot:unresolved`
- `BLK-044` — `input:Deployment.DP-13.stability.specialStabPoolId:unresolved`
- `BLK-045` — `input:Deployment.DP-14.lp.decimals:unresolved`
- `BLK-046` — `input:Deployment.DP-14.lp.depositLimits:unresolved`
- `BLK-047` — `input:Deployment.DP-14.lp.identities:unresolved`
- `BLK-048` — `input:Deployment.DP-14.lp.oracleArtifacts:unresolved`
- `BLK-049` — `input:Deployment.DP-15.rewards.promotion:unresolved`
- `BLK-050` — `input:Deployment.DP-16.ccip.promotion:unresolved`
- `BLK-051` — `input:Deployment.DP-18.roles.guardian:unresolved`
- `BLK-052` — `input:Deployment.DP-18.roles.trainingWheelsAllowlist:unresolved`
- `BLK-053` — `input:Deployment.DP-19.supply.GREEN.recipient:unresolved`
- `BLK-054` — `input:Deployment.DP-19.supply.RIPE.recipient:unresolved`
- `BLK-055` — `input:Deployment.DP-19.supply.SGREEN.recipient:unresolved`
- `BLK-056` — `input:Deployment.DP-21.endaoment.nativeDecimals:unresolved`
- `BLK-057` — `input:Deployment.DP-21.endaoment.nativeName:unresolved`
- `BLK-058` — `input:Deployment.DP-21.endaoment.nativeSymbol:unresolved`

## Blocker closure summary

| Closure view | Result |
|---|---|
| Fully closable by this read-only report | `0` |
| Closed in canonical readiness | `0` |
| Partially evidenced | official/repository candidates exist for chain identities, WETH, USDG, feeds, ArbSys/sentinels, Morpho factory/vault, AAPL token/feed, Curve registries, and four active AAPL repository artifacts; they remain blockers |
| Owner-decision blockers | PSM parameters/allowlists/reserves; AAPL P8/caps/risk/auction/route; stability ID; reward/CCIP promotion; role/recipient choices; Endaoment metadata; Curve parameters/funding/custody; fork/finality/liveness policy |
| RPC-required blockers | all accepted-pin network headers/clock/finality/archive observations; external token/feed/code/control observations; Morpho; Curve registry/factory; AAPL; any onchain operator/control binding |
| Deployment-produced blockers | GREEN, RIPE, sGREEN, contributor template, training wheels, guardian; AAPL/LP vault and slot/M5 bindings where activated; Curve pool; supply recipients and deployment records |
| Operator/SecOps blockers | archive endpoint binding, governance/safe/guardian/training-wheels allowlist, supply recipients, reserve custody, monitoring/liveness/freeze policy |
| Intentionally deferred | LP admission/oracles; inactive stock/LP/CCIP work remains blocked until separately promoted |

“Partially evidenced” never means closed. A mutable page, explorer label, candidate address, active-worktree packet, or passing offline test does not satisfy immutable onchain acceptance.

## Network and proposed immutable fork pin

[Robinhood Connecting](https://docs.robinhood.com/chain/connecting/) publishes mainnet chain ID `4663`, testnet chain ID `46630`, parent networks Ethereum mainnet/Sepolia, official explorer/RPC candidates, and the need for archive-capable providers for historical state. [Robinhood Protocol Contracts](https://docs.robinhood.com/chain/protocol-contracts/) publishes the Rollup, SequencerInbox, Delayed Inbox, bridge proxy-admin, WETH, and NodeInterface candidates. These are independently corroborated public identities, not an accepted pin.

The repository contains a historical adjacent pair in `docs/chains/rh/evidence/ledger-action-block-mainnet-fork.json`:

- proposed child `N=19,342,402` (`0x1272442`), hash `0xc6c7cd0d7d238e472a265e4e4b854c29341d29a072d1d9ad4b1d963f96244f65`, timestamp `1785015874`;
- previous child `19,342,401` (`0x1272441`), hash `0xc13ace60537ea60742a2d3efa8007c92fe2cda40e2e3353cf3f01dcb86055792`;
- the proposed child parent equals the previous hash; historical observations record block L1 `25,612,556`, ArbSys child `19,342,402`, and raw ArbOS version `116`.

Status: **historical candidate, not owner-selected or accepted**. It is preferable to “latest” because it is immutable, but it still lacks an accepted archive-endpoint fingerprint, fresh number/hash/header equivalence, state root, representative receipt and L1 relationship, finality record, NodeInterface observations, current code/control reads, and owner record. Deterministic forks must start from the accepted pin, retain chain ID `4663`, prohibit submission, isolate caches, execute named fixtures, restore Boa process-global state, and destroy/recreate the disposable fork rather than compensate mutations.

Mainnet parent candidates: Rollup `0x23A19d23e89166adedbDcB432518AB01e4272D94`, SequencerInbox `0xBd0D173EEb87D57A09521c24388a12789F33ba96`, Delayed Inbox `0x1A07cc4BD17E0118BdB54D70990D2158AbAD7a2D`. L2 NodeInterface is `0x00000000000000000000000000000000000000C8`; ArbSys is `0x0000000000000000000000000000000000000064`. These remain pin-specific observation inputs.

## External source register

Every public source below was retrieved on `2026-08-01`. “High” confidence means high confidence that the publisher currently says the observed value; it does not mean immutable onchain acceptance.

| Source | Publisher | Exact observed value used here | Classification | Confidence | Mutability | RPC still required | Conflict/ambiguity |
|---|---|---|---|---|---|---|---|
| [Connecting](https://docs.robinhood.com/chain/connecting/) | Robinhood | chain IDs 4663/46630, Ethereum/Sepolia parents, public RPC/explorer candidates, archive-provider guidance | independently verified external documentation | high | mutable page/endpoints | yes | public RPC is rate-limited and not accepted archive proof |
| [Protocol contracts](https://docs.robinhood.com/chain/protocol-contracts/) | Robinhood | Rollup, SequencerInbox, Delayed Inbox, WETH, L2 Proxy Admin `0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF`, NodeInterface | independently verified external documentation | high | mutable registry | yes | publication does not bind pin/code/admin behavior |
| [Token contracts](https://docs.robinhood.com/chain/contracts/) | Robinhood | WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`; USDG `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168` | independently verified external documentation | high | live/mutable registry | yes | address only |
| [Stock Token APIs](https://docs.robinhood.com/chain/stock-token-apis/) | Robinhood | per-chain asset address/multiplier model; AAPL candidate `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` in current documentation/API evidence | selected external fact candidate | medium-high | mutable API/page | yes | no runtime/control/multiplier-state proof |
| [USDG mainnet](https://docs.paxos.com/guides/stablecoin/usdg/mainnet) and [pinned USDG source](https://github.com/paxosglobal/usdg-contract/tree/5afb581e076f69ae46eb2e360f4dc63a71514a78) | Paxos | Robinhood USDG address; UUPS/6-decimal/source candidates | independently verified source/documentation | high for source commit; medium for deployed binding | page mutable; Git commit immutable | yes | exact implementation/compiler/layout/admin still unknown |
| [Robinhood feed registry JSON](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json) | Chainlink | ETH/BTC/USDG/AAPL proxies, secondary proxies, aggregators, 8 decimals, 86,400s heartbeat candidates | selected external fact candidate | high for retrieved registry | mutable registry/proxies | yes | 86,400 stale threshold has no heartbeat margin |
| [Tokenized equity feeds](https://docs.chain.link/data-feeds/tokenized-equity-feeds/robinhood) | Chainlink | underlying-price × multiplier; 24/5, off-hours and corporate-action semantics | independently verified platform behavior | high | mutable documentation/live system | yes for AAPL | registry category/heartbeat does not itself prove equity cadence |
| [L2 sequencer feeds](https://docs.chain.link/data-feeds/l2-sequencer-feeds) | Chainlink | no Robinhood entry in inspected supported-network list | independently verified negative registry observation | medium-high | mutable list | yes/owner policy | absence is not proof no contract can ever exist |
| [Pinned Robinhood registry](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/deployments/prod/robinhood.yaml) | Curve | AddressProvider plus registry/factory IDs 7/11/12/13 | independently verified source candidate | high for pinned bytes | immutable Git commit; deployments mutable | yes | runtime/admin/registry position not accepted |
| [Contract addresses](https://docs.morpho.org/developers/contracts/addresses/) and [Vault V2 README](https://github.com/morpho-org/vault-v2/blob/main/README.md) | Morpho | Robinhood factory `0x0FBad98595b0186dA120E41f77C102beb49f803c`; immutable-factory/noncustodial Vault V2 model | independently verified external documentation | high | mutable docs/main branch | yes | factory/vault/code/control binding remains open |
| [WETH explorer](https://robinhoodchain.blockscout.com/address/0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73) and [USDG explorer](https://robinhoodchain.blockscout.com/address/0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168) | Robinhood Blockscout | proxy/source labels and public history candidates | corroborating public candidate | medium | mutable explorer/index | yes | labels are not runtime/code/layout/admin proof |

## Token findings

All addresses below are Robinhood mainnet chain `4663` unless marked deployment-produced. “Unknown” means the field remains blocked; it is not an invitation to infer a default.

| Token | Identity/class | Proxy, implementation and code | Metadata/supply/returns/permit | Controls, multiplier and upgradeability | Acceptance/RPC |
|---|---|---|---|---|---|
| WETH | canonical external candidate `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` | explorer labels proxy/`aeWETH`; exact proxy type, implementation, admin/beacon, proxy/implementation runtime hashes and source/compiler unknown | expected name/symbol/18 decimals, wrapping supply behavior, ERC-20 return shape; permit/nonstandard return behavior unknown | published L2 Proxy Admin is a candidate; exact authority, pause/freeze/sanctions and upgrade history/freeze policy unknown; no multiplier | address independently documented; all deployed behavior requires RPC |
| USDG | canonical external candidate `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168` | upstream model is UUPS; exact implementation/admin, proxy/implementation runtime hashes, compiler/source/layout and implementation slot unknown | source candidate Global Dollar/USDG/6 decimals, supply, EIP-2612/EIP-3009, standard bool returns | source has admin/upgrade, pause/freeze/wipe/sanctions controls; exact deployed roles/pending upgrades unknown; no multiplier | address/source independently documented; deployed binding requires RPC; no overlay authorized |
| GREEN | deployment-produced unresolved | frozen direct-deploy source expectation; address, artifacts, runtime/implementation hash and direct/non-proxy owner policy unresolved | GREEN/18 decimals; supply and recipient deployment inputs; bool returns; EIP-2612/1271-style permit in frozen source | pause/blocklist/sanctions/governance; no multiplier; no source proxy logic | deployment and post-deploy RPC required |
| RIPE | deployment-produced unresolved | frozen direct-deploy source expectation; address/artifacts/code/policy unresolved | RIPE/18 decimals; supply/recipient inputs; bool returns; frozen-source permit behavior | pause/blocklist/sanctions/governance; no multiplier; no source proxy logic | deployment and post-deploy RPC required |
| sGREEN | deployment-produced unresolved ERC-4626 | frozen direct-deploy source expectation; exact GREEN underlying/address/artifacts/code unresolved | name/symbol owner-bound; decimals from GREEN; share supply/ERC-4626 behavior; frozen-source permit behavior | pause/blocklist/sanctions/governance; no multiplier; no source proxy logic | deployment and post-deploy RPC required |
| SteakHouse USDG | owner-selected external vault candidate `0xBeEff033F34C046626B8D0A041844C5d1A5409dd` | exact runtime hash, factory membership, immutability/upgrade model and source binding unknown | name/symbol/decimals/supply, ERC-4626/PPS and return/permit behavior require observation | owner/curator/allocator/guardian controls unknown; no token multiplier | selected but unverified; RPC required |
| AAPL | owner-selected external stock-token candidate `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9` | proxy type/address relationship, implementation/admin, runtime hashes, source/compiler and storage layout unknown | name/symbol, candidate 18 decimals, total-supply and permit/return behavior unaccepted | transfer/sanctions/pause/freeze/corporate-action authorities, current/pending multiplier, upgrade model/history unknown | documentation candidate only; RPC and owner approval required |

[Robinhood Token Contracts](https://docs.robinhood.com/chain/contracts/) and [Paxos USDG documentation](https://docs.paxos.com/guides/stablecoin/usdg/mainnet) corroborate address/source candidates. [Robinhood Stock Token APIs](https://docs.robinhood.com/chain/stock-token-apis/) corroborates the AAPL candidate and multiplier model, but does not prove live proxy, code, controls, multiplier, decimals, or state.

## Oracle findings

| Route | Proxy candidate | Aggregator candidate | Public metadata | Acceptance |
|---|---|---|---|---|
| ETH/USD for WETH | `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9` | `0x6091E64eb7138EEF066a80FD3A0d7427B91f2721` | 8 decimals; 86,400s heartbeat | candidate; RPC/owner binding required |
| BTC/USD | `0xa2c5184bF03d373Dc9dE4876eb4Bce595B460251` | `0xc5845F87AD59a7a3D4bF9B90a0C19dbA38475EeC` | 8 decimals; 86,400s heartbeat | candidate; constructor posture and RPC required |
| USDG/USD | `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2` | `0x8bEeE3503F6860D5dac4cE26b5eEe92982951c2e` | 8 decimals; 86,400s heartbeat | candidate; RPC/owner binding required |
| AAPL/USD | `0x6B22A786bAa607d76728168703a39Ea9C99f2cD0` | `0xBb11A21267cFDb63d4935d99a499133DD1744ACb` | 8 decimals; equity 24/5/corporate-action semantics | candidate; activation parked and RPC/owner policy required |

Source: [Chainlink Robinhood feed registry](https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json) and [Chainlink tokenized equities](https://docs.chain.link/data-feeds/tokenized-equity-feeds/robinhood). At the accepted pin, every active feed must prove proxy/aggregator/code/control identity and a complete `latestRoundData()` with `roundId>0`, `answer>0`, `updatedAt>0`, no future/stale timestamp, `answeredInRound>=roundId`, and cached/current decimals equality. The current `86,400` staleness value equals the published heartbeat and has no operating margin; the oracle owner must approve a production policy.

For all four feed candidates, current proxy upgradeability, proxy owner/admin, aggregator owner, proposed aggregator, runtime hashes and deprecation state remain unaccepted. The repository adapter rejects `answer<=0`, future/stale rounds, round ID zero, `answeredInRound<roundId`, and feed decimals above 18; however it does not independently reject `updatedAt==0`, and stale time zero disables the age check. Qualification therefore requires `updatedAt>0` and a nonzero approved stale limit even where the adapter would otherwise fail open. AAPL additionally needs exact market-session, off-hours, multiplier and corporate-action pause policy; the registry heartbeat is not sufficient.

USDG and the PSM remain Chainlink-only. Curve must not provide a USDG feed. Uniswap remains unavailable for protocol accounting. Curve ID 2 is not a global priority; priority remains `[1,3]`. No official Robinhood Chainlink sequencer uptime feed was found in the inspected official registries. Do not invent one: liveness needs a separately approved operational policy using Robinhood sequencer signals plus parent-L1/inbox evidence.

## Curve findings

The owner-directed active Curve lane reopens launch inclusion but is not integrated into this baseline. [Curve's pinned Robinhood deployment registry](https://github.com/curvefi/curve-core/blob/6222dda9959091db94d61f6d6378234a624cdd66/deployments/prod/robinhood.yaml) supplies candidates: AddressProvider `0x4574921eb950d3Fd5B01562162EC566Cb8bc3648`; MetaRegistry ID 7 `0xe6dA14500f0b5783E2325F9C5a7eE5d99DA0fB42`; TricryptoNG ID 11 `0x6E28493348446503db04A49621d8e6C9A40015FB`; StableSwapNG ID 12 `0x8271e06E5887FE5ba05234f5315c19f3Ec90E8aD`; TwoCryptoNG ID 13 `0xe7FBd704B938cB8fe26313C3464D4b7B7348c88C`. Runtime provenance, current registry positions, implementations, admins, fee receivers, mutability, and pool inventory still require accepted-pin proof.

The active candidate selects USDG/GREEN ordering, decimals 6/18, `A=100`, `fee=4_000_000`, off-peg multiplier `20_000_000_000`, and `ma_exp_time=600`; `866` is a test vector only. No canonical GREEN/USDG pool is accepted. The pool address, CREATE ordering, liquidity, custodian, funding source, approvals, min-mint, slippage, withdrawal authority, and minimum retained reserves are deployment/owner inputs and must not be fabricated. PSM reserves cannot fund LP liquidity.

Intended topology after separately authorized integration: Chainlink ID 1; Curve ID 2; BlueChipYield ID 3; priority `[1,3]`; GREEN may use Curve GREEN/USDG; USDG stays Chainlink-only; LP tokens remain separate.

## Morpho and BlueChipYield findings

[Morpho's official addresses page](https://docs.morpho.org/developers/contracts/addresses/) independently corroborates Robinhood Morpho V2 factory `0x0FBad98595b0186dA120E41f77C102beb49f803c`; this closes only the documentation cross-check, not readiness. The selected SteakHouse vault remains `0xBeEff033F34C046626B8D0A041844C5d1A5409dd`. At the pin, qualification must prove factory membership, `asset()==USDG`, decimals, nonzero/normalized `totalSupply`, positive `convertToAssets(10**decimals)`, code compatibility, ownership/curator/allocator controls, and upgradeability.

The integrated `BlueChipYieldPrices.vy` is current repository authority. It uses defensive raw reads and fails closed on non-factory vaults, asset/decimal mismatch, zero supply/PPS, overflow, and malformed return data. PR #66's older Morpho implementation is superseded and must not return.

## AAPL findings

The complete baseline census remains `16` unresolved readiness inputs: DP-10 token identity, control/multiplier verification, decimals, feed, P8, per-user/global caps, vault, risk, auction, route; and DP-11 movement, credit-containment, composed proof, activation binding, vault artifact, and vault slot. The active candidate worktree carries four repository evidence artifacts for vault artifact/M2/M3/M4, but it is not integrated; therefore the canonical baseline correctly retains all 16 blockers.

| Exact readiness inputs | Count | Current classification | What closes them |
|---|---:|---|---|
| DP-10 `identity`, `decimals`, `feed` | 3 | external canonical candidates, unverified | official candidates plus accepted-pin proxy/code/control/multiplier/decimal/feed observations |
| DP-10 `P8`, `perUserCap`, `globalCap`, `risk`, `auction`, `route` | 6 | owner-selected values unresolved | exact signed owner packet; this report does not approve values |
| DP-10 `vault` | 1 | deployment-produced identity unresolved | approved artifact/deployment ordering, manifest and receipt |
| DP-11 `m2Movement`, `m3CreditContainment`, `m4ComposedProof`, `vaultArtifact` | 4 | active repository candidate evidence; not integrated | owner review, exact-baseline integration and canonical regeneration; fork evidence where specified |
| DP-11 `vaultSlot`, `m5ActivationBinding` | 2 | deployment/operator binding unresolved | authorized deployment slot and M5 activation record |

The other 12 items remain external facts, owner decisions, deployment identities, operator bindings, or fork observations. Candidate token `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9`, feed `0x6B22A786bAa607d76728168703a39Ea9C99f2cD0`, and candidate decimals `18` are not accepted without pin-specific proof. This report does not approve P8, caps, vault, risk, auction, route, slot, or M5.

Repository history also records a successful read-only AAPL observation at child block `17,558,441` with proxy hash, beacon/registry `0xe10b6f6B275de231345c20D14Ab812db62151b00`, implementation `0xb35490d6f9163DE4F80d88dc75c3516eb64C5aE2`, 18 decimals, unpaused state, and multiplier `1e18`. That is valuable historical behavior evidence, but it is not the proposed network pin, not a current final-freeze observation, and cannot close the current AAPL identity/control/feed blockers.

## Reward findings

Current numeric Defaults match the selected PR #66 inputs: shared reward budget `1,000 RIPE`; `0.009 RIPE/block`; borrower/staker `10%/90%`; auto-stake `0%/0%`; lock ratio `75%`; stability share `33%`; stability reward `1 RIPE per USD claimed`. Emission alone is `64.8 RIPE/day`, giving approximately `15d 10h 22m 24s` before considering shared stability spending. The active reward candidate does not close `B-REWARD-PROMOTION`/DP-15. The owner still must approve shared-budget/runway policy, operating/monitoring controls, recipients, and promotion. A byte hash proves bytes, not activation authority.

## LP findings

The published non-admission conclusion remains controlling: GREEN/USDG liquidity may support GREEN pricing, but the GREEN/USDG LP token is not automatically admitted; RIPE/WETH LP is not admitted; neither LP is a launch oracle; PSM reserves cannot supply LP capital; priority remains `[1,3]`; and Curve at ID 2 is not globally prioritized. After Curve authority is integrated, LP documentation saying slot 2 is empty or Curve is Profile-2-only must be corrected without weakening those boundaries.

## Owner decisions and deployment-produced inputs

Owner inputs include fork/finality/liveness policy; oracle staleness margin; Curve parameters/custody/funding/slippage/minimum reserves; PSM fees/limits/intervals/allowlists/reserve custody/execution; AAPL P8/caps/risk/auction/route; reward and CCIP promotion; stability pool ID; Endaoment metadata; LP posture; and governance/role/recipient handoffs.

Deployment-produced values include GREEN/RIPE/sGREEN, contributor-template, training-wheels and guardian identities; exact initial-supply recipients and receipts; Curve pool address; and any approved AAPL/LP vault/slot/M5 bindings. They require authorized deployment artifacts, constructor arguments, code hashes, manifests, receipts, and owner records. This report produces none.

## Consolidated RPC authorization request

No RPC call was made. If the owner elects to close the observation lane, authorize **one** bounded packet:

- **Endpoint class:** owner-approved, archive-capable Robinhood mainnet endpoint supplied only through redacted secret alias `ROBINHOOD_MAINNET_RPC_URL`, plus owner-approved Ethereum-mainnet archive endpoint `ETHEREUM_MAINNET_RPC_URL` for parent L1. Record provider/network/service tier and a SHA-256 endpoint fingerprint; prohibit redirects and public fallback. Never print credentials or full URLs.
- **Exact proposed block:** Robinhood child `19,342,402` (`0x1272442`) and adjacent `19,342,401` (`0x1272441`); parent-L1 reads at the returned `l1BlockNumber`/receipt relationship. This is a proposal, not authorization to accept the pin.
- **Methods:** `eth_chainId`; `eth_getBlockByNumber`; `eth_getBlockByHash`; `eth_getTransactionReceipt` for one transaction selected from N; `eth_getCode`; `eth_getStorageAt`; `eth_getProof`; bounded `eth_getLogs` only for declared proxy/factory upgrade events; and read-only `eth_call` for the exact ABI getters below. No traces.
- **Exact L2 addresses:** ArbSys `0x0000000000000000000000000000000000000064`; NodeInterface `0x00000000000000000000000000000000000000C8`; WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`; published L2 Proxy Admin `0xa3Acd31AFb851B4eB9DAD00F5204c01D924267dF`; USDG `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`; SteakHouse `0xBeEff033F34C046626B8D0A041844C5d1A5409dd`; governance/safe `0xe488a42D33b3Af5d3E5Cd5680938d8369716D1bf`; AAPL `0xaF3D76f1834A1d425780943C99Ea8A608f8a93f9`; Morpho factory `0x0FBad98595b0186dA120E41f77C102beb49f803c`.
- **Exact feed addresses:** ETH proxy/secondary/aggregator `0x78F3556b67E17Df817D51Ef5a990cDaF09E8d3A9`, `0x5058aDee53b04e374d8bEDbAD634Bc4778F50b22`, `0x6091E64eb7138EEF066a80FD3A0d7427B91f2721`; BTC `0xa2c5184bF03d373Dc9dE4876eb4Bce595B460251`, `0x5a74F49d16fd0Cb866766d7e8EDb54DE36F6645A`, `0xc5845F87AD59a7a3D4bF9B90a0C19dbA38475EeC`; USDG `0x61B7e5650328764B076A108EFF5fa7282a1B9aD2`, `0x901f56689360B89D7767a8acE28B7801e6348fa2`, `0x8bEeE3503F6860D5dac4cE26b5eEe92982951c2e`; AAPL `0x6B22A786bAa607d76728168703a39Ea9C99f2cD0`, `0x4bDbb3150014c6Ab2C6D9347B0779c49015a2f3f`, `0xBb11A21267cFDb63d4935d99a499133DD1744ACb`.
- **Exact Curve addresses:** AddressProvider `0x4574921eb950d3Fd5B01562162EC566Cb8bc3648`; MetaRegistry `0xe6dA14500f0b5783E2325F9C5a7eE5d99DA0fB42`; TricryptoNG factory `0x6E28493348446503db04A49621d8e6C9A40015FB`; StableSwapNG factory `0x8271e06E5887FE5ba05234f5315c19f3Ec90E8aD`; TwoCryptoNG factory `0xe7FBd704B938cB8fe26313C3464D4b7B7348c88C`.
- **Exact L1 addresses:** Rollup `0x23A19d23e89166adedbDcB432518AB01e4272D94`; SequencerInbox `0xBd0D173EEb87D57A09521c24388a12789F33ba96`; Delayed Inbox `0x1A07cc4BD17E0118BdB54D70990D2158AbAD7a2D`.
- **Storage slots:** EIP-1967 implementation `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`, admin `0xb53127684a568b3173ae13b9f8a6016e019219e8b0f4b6471176d5517024d3a`, and beacon `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50` for contracts whose verified proxy model uses them. Do **not** read or write USDG balance/supply slots for an overlay unless exact deployed source/compiler/layout is separately accepted.
- **Exact `eth_call` ABI surface:** on WETH/USDG/AAPL/SteakHouse, `name()`, `symbol()`, `decimals()`, `totalSupply()`; on AAPL, `uiMultiplier()`, `newUIMultiplier()`, `effectiveAt()`, `tokenPaused()`, `oraclePaused()` and, on its beacon/registry only after the beacon slot resolves, `implementation()` and `paused()`; on each feed proxy, `description()`, `decimals()`, `aggregator()`, `latestRoundData()`; on Morpho factory, `isVaultV2(address)` with SteakHouse; on SteakHouse, `asset()`, `decimals()`, `totalSupply()`, `convertToAssets(uint256)` with exactly `10**D` where `D` is the preceding accepted `decimals()` result, `owner()`, `curator()`; on Curve AddressProvider, `get_address(uint256)` for `7,11,12,13`; on the returned registries/factories, `pool_count()`, at most `32` total `pool_list(uint256)` entries, and at most `32` matching `get_coins(address)` calls plus `admin()` and `fee_receiver()` only where the pinned official ABI exposes that exact selector; on ArbSys, `arbBlockNumber()` and `arbOSVersion()`; on NodeInterface, `l2BlockRangeForL1(uint64)` for the block/receipt L1 values. Unsupported/reverting selectors stop that component; they are not replaced by guessed ABI. No account-dependent balance, allowance, role-membership or blocklist call is authorized.
- **Exact parent-L1 read surface:** `eth_chainId`; `eth_getBlockByNumber` for the child-returned L1 number and `finalized`; `eth_getBlockByHash` for the returned L1 header hash if present; `eth_getCode` at the three listed L1 protocol addresses; the three EIP-1967 slots only where code/source proves that proxy model; and bounded upgrade-event `eth_getLogs` at those three addresses over the owner-selected finality window. No unspecified Rollup/Inbox ABI call is authorized until the owner selects a finality/liveness policy and exact ABI packet.
- **Expected maximum:** `204` JSON-RPC requests total (`180` Robinhood L2 + `24` Ethereum L1). Stop on chain mismatch, redirect, non-archive response, missing code/header/receipt, inconsistent hash/parent/state, unsupported ABI, cap exhaustion, or any credential redaction failure.
- **Safety:** every call is read-only. No account, signer, key, transaction, submission, trace mutation, impersonation, funding, storage write, state override, overlay, deployment, configuration, or other state change.

This single request is the only next authorization needed for RPC research; deployment and owner decisions remain separately gated.

## Conflicts and uncertainties

- `configuration_consistent=true` is not deployment readiness.
- Morpho/Robinhood/Curve/Chainlink public pages are mutable and cannot prove pin-specific runtime or controls.
- The AAPL registry metadata mixes equity session behavior with a generic feed category; equity behavior controls the caution.
- An `86,400` feed heartbeat and an `86,400` stale threshold have zero delay margin.
- The historical pin was observed through a public endpoint without an accepted archive guarantee.
- Active Curve/AAPL/reward/migration/LP worktrees are candidate evidence only and were not modified or integrated.
- No Chainlink Robinhood sequencer contract was found; operational liveness policy remains owner-controlled.
- `unexplained_conflict=0`; typed unresolved items remain blockers rather than hidden conflicts.

## Downstream handoffs

### Curve agent

Use `SUP-CURVE-001`–`003`: the five official registry/factory candidates, USDG/GREEN ordering, 6/18 decimals, candidate parameters, and topology are available. Runtime/admin/registry/pool-existence proof, owner funding/custody/slippage/minimum-reserve decisions, a deployment-produced pool address, and fork observations remain blocked.

### Migration agent

Use current `BluePrint.py`, `DefaultsRobinhood.vy`, their derived ledger, the current eight-binding constructor, Chainlink ID 1, BlueChipYield ID 3, and priority `[1,3]`. Consume the dedicated `BLK-*` keys as typed blockers. Do not use PR #66 casing, five-arg constructor, BlueChip ID 2, global priority 2, mainnet-only migrations, custom history/runner, unresolved identities, legacy Morpho, or legacy Curve create/fund assumptions. Registry/deployment ordering must preserve deployment-produced identities.

### AAPL agent

Use the official token/feed candidates only as public candidates and preserve all 16 canonical blockers until integration. Four active repository artifacts may be proposed for vaultArtifact/M2/M3/M4; the other 12 inputs need exact external facts, owner decisions, deployment/slot/M5 bindings, and authorized pin observations.

### H-09 fork agent

Proposed profile: Robinhood mainnet `4663`, Ethereum mainnet parent, child `19,342,402` plus adjacent block. Offline work can validate schemas, block-pair structure, manifest identity, fixture routing, submission prohibition, cache isolation, restore/teardown, and failure contracts. Header/receipt/L1/NodeInterface/ArbSys/code/control/feed/factory/vault tests remain blocked on the single authorized archive-RPC packet.

### Deployment owner

Select product parameters and promotion policies; have SecOps bind archive endpoints, governance/safe/guardian/training-wheels/recipients/custody/monitoring; produce deployment identities only through authorized deployments; require testnet evidence where the release plan calls for it; and reserve production-only receipts/code/control/state proof for the post-deployment gate. None of those lifecycle transitions is authorized here.

## Recommended critical path

1. Owner accepts or replaces the proposed immutable historical pin and approves exact finality/liveness/staleness policies.
2. Execute the single bounded archive-RPC packet, publish its immutable evidence, and reconcile every observed fact back to a typed blocker.
3. Close owner/SecOps product, role, recipient, custody, monitoring, and promotion packets without changing canonical source prematurely.
4. Finish and separately approve Curve, AAPL, rewards, PSM, CCIP, and LP authority lanes; correct stale documentation only after integration authority.
5. Produce deployment identities, artifacts, constructors, code hashes, manifests, receipts, and handoffs through the authorized lifecycle.
6. Regenerate canonical evidence, require `configuration_consistent=true` and `deployment_ready=true`, then run the separately authorized H-09 fork qualification. A green check never authorizes deployment or activation.

## Validation contract

The final handoff must verify: exact baseline/live ref; `252` classified PR rows; `58` dedicated blocker rows with exact key-set equality and one-to-one mapping; every Markdown TSV identifier exists; local Markdown targets exist; external links are syntactically valid and sourced from primary publishers; TSV has exactly `19` columns and unique IDs; alternate-index `git diff --cached --check` includes both outputs; both SHA-256 hashes are recorded; the real Git index is unchanged; isolated status contains exactly the two untracked outputs; and ignored/generated residue is zero. The complete protocol suite is intentionally not run.

TSV companion: `canonical-launch-input-verification.tsv` (`335` evidence rows plus header at generation time).
