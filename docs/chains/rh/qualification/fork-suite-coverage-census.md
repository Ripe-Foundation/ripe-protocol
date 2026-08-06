# Robinhood fork-suite coverage census and implementation design

Status: **READ-ONLY DESIGN; IMPLEMENTATION AND FORK EXECUTION BLOCKED**

Date: 2026-07-30

Revision note: corrected after independent review. The prior accepted byte
snapshot remains preserved, unchanged, at
`/Users/wigglez/dev/ripe-protocol-review-archives/fork-qualification/fork-suite-coverage-census.md`;
it is historical and is superseded as census/design guidance by this worktree
revision. Owner disposition was granted against corrected census SHA-256
`cd13c3028315784b6a48de097b95529e18ee8d0695f7cd3eca5d6f6fcae6038c`:
explicit read-only archive-fork qualification is an opt-in H-09 mode, while
network remains disabled by default. This decision-bound revision is the
controlling census and will be preserved separately as
`fork-suite-coverage-census-v2.md`.

## 1. Authority and result

This census is bound to:

- branch: `codex/rh-fork-suite-coverage-census`
- commit: `0d5994aa78f9d6f35b59bd7a2bc70fa18706e693`
- tree: `b68dffdddbdc7c5ae8423db049099c1632b478c9`
- isolated worktree: `/private/tmp/rh-fork-suite-coverage-census.bSf4TI`
- worktree mode: `0700`

The source baseline was clean before the report was created. The primary worktree
was not modified.

There is no Robinhood fork package at this baseline. The repository has extensive
local-Boa unit and composed-route coverage, 142 Base-fork tests, deterministic
profile/planning/evidence foundations, and useful probes. It has **zero tests that
qualify an exact Robinhood state through a pinned archive fork**. Consequently,
current Robinhood qualifying coverage is 0% for every chain-facing integration.

This report does not authorize RPC use, fork creation, account or signer use,
implementation, deployment, activation, evidence publication, or release.

## 2. Coverage accounting

The scenario matrix assigns one primary classification to each atomic acceptance
scenario:

- `real integration`: fully covered by a relevant real integration;
- `mock`: covered only by a mock;
- `local Boa`: covered only by local Boa state;
- `Base only`: covered only on Base;
- `partial`: useful assertions exist, but the acceptance scenario is incomplete;
- `absent`;
- `external identity`: blocked by an external identity or immutable chain input;
- `owner API`: blocked by a missing owner API;
- `inappropriate`: inappropriate for fork testing.

Two percentages are reported so local and Base work is not mistaken for Robinhood
qualification:

1. **RH qualifying coverage** is `real integration / applicable scenarios`.
2. **Reusable-pattern density** counts `real integration`, `mock`, `local Boa`,
   `Base only`, and `partial` as useful foundations. It does not imply
   qualification, completion, or readiness. `Inappropriate` rows are excluded
   from denominators.

| Major integration | Applicable rows | RH qualifying | Reusable-pattern density |
|---|---:|---:|---:|
| Chain pin, archive RPC, fork engine, and clocks | 8 | 0/8 = **0%** | 4/8 = **50%** |
| Canonical tokens and oracles | 12 | 0/12 = **0%** | 5/12 = **42%** |
| Uniswap, Curve, PriceDesk, rates, Teller snapshots, and PSM | 14 | 0/14 = **0%** | 8/14 = **57%** |
| Deposit through liquidation, AuctionHouse, and Deleverage | 10 | 0/10 = **0%** | 10/10 = **100%** |
| Roles, plans, artifacts, evidence, replay, and teardown | 12 | 0/12 = **0%** | 6/12 = **50%** |
| **Total** | **56** | **0/56 = 0%** | **33/56 = 59%** |

One additional Uniswap-oracle row is inappropriate for the launch fork suite and
is excluded. The aggregate 59% is retained only as a transparent arithmetic
summary of reusable patterns. It must not be presented without the 0% qualifying
coverage column.

## 3. Repository census

### 3.1 Test population

At the frozen tree there are 118 tracked Python files under `tests/`, of which
110 are `test_*.py` modules, and 3,332 source-level `test_*` functions. The
following mechanical inventory was generated from `git ls-files` plus anchored
`def test_` matching at the frozen tree:

| Area | Test modules | Tests | Coverage character |
|---|---:|---:|---|
| `tests/deployment/` | 11 | 299 | offline schemas, profiles, plans, discovery, gates |
| `tests/deployment_profiles/` | 3 | 24 | Ledger and Lootbox profile artifacts |
| `tests/inventory/` | 2 | 113 | block clocks and contract artifact ceilings |
| `tests/config/` | 8 | 540 | defaults, switchboards, and safety configuration |
| `tests/clock/` | 1 | 34 | synthetic clock profiles |
| `tests/data/` | 3 | 193 | Ledger, action-block, and MissionControl |
| `tests/tokens/` | 3 | 78 | local ERC20/ERC4626/signature behavior |
| `tests/registries/` | 2 | 34 | local registry behavior |
| `tests/modules/` | 2 | 42 | local governance and timelock, not Endaoment |
| `tests/core/auctionHouse/` | 8 | 93 | local Boa |
| `tests/core/bondRoom/` | 1 | 93 | local bond behavior |
| `tests/core/creditEngine/` | 8 | 162 | local Boa, including dynamic rates |
| `tests/core/deleverage/` | 9 | 282 | local Boa, including composed rollback |
| `tests/core/endaoment/` | 8 | 326 | PSM and stabilizer behavior |
| `tests/core/humanResources/` | 3 | 97 | local contributor behavior |
| `tests/core/lootbox/` | 5 | 165 | local rewards; `test_underscore_rewards.py` has explicit Base/Robinhood interval cases but no `@pytest.base` marker |
| `tests/core/teller/` | 4 | 116 | local Boa custody and exact receipt |
| `tests/priceSources/` recursively | 16 | 252 | mock/local feeds and Base adapters |
| `tests/probes/` | 3 | 75 | controlled action-block and token probes |
| `tests/vaults/` recursively | 10 | 314 | GuardedErc20 and vault behavior |

No `tests/deployment/fork/` directory exists. There are 142 tests marked for Base
and none marked for Robinhood or mainnet.

### 3.2 Deployment, profile, inventory, and configuration tests

Every relevant file in the required deployment/configuration scope is accounted
for below.

| Scope | Files | Existing assurance |
|---|---|---|
| Deployment profile regression | `tests/deployment/test_base_profile_regression.py` (21), `tests/deployment/test_network_profiles.py` (24), `tests/deployment/test_network_clock_profiles.py` (13), `tests/deployment/test_secret_handling.py` (29) | Base and synthetic profile validation; no RH archive state |
| Plan and dependency gates | `tests/deployment/test_dependency_gate.py` (23), `tests/deployment/test_execution_plan.py` (31), `tests/deployment/test_migration_discovery.py` (26) | deterministic offline blocking and source discovery |
| Manifests | `tests/deployment/test_manifest_schema.py` (31), `tests/deployment/test_current_manifest_promotion.py` (47) | H-06 schema-v2/JCS/history behavior; no frozen-tree fork-evidence successor |
| Robinhood blueprint | `tests/deployment/test_robinhood_blueprint.py` (23), `tests/deployment/test_robinhood_omissions.py` (31) | blocked/omitted symbolic Profile 1 shape; no deployed system |
| Deployment profiles | `tests/deployment_profiles/test_ledger_artifact_bundle.py` (8), `tests/deployment_profiles/test_ledger_robinhood_profile.py` (9), `tests/deployment_profiles/test_lootbox_deployment_profiles.py` (7) | local Ledger artifact/profile and unrelated Lootbox profiles |
| Inventories | `tests/inventory/test_block_clock_inventory.py` (102), `tests/inventory/test_contract_artifacts.py` (11) | static clock inventory and local bytecode ceilings |
| Config/defaults | `tests/config/test_bond_booster.py` (25), `tests/config/test_defaults_robinhood.py` (38), `tests/config/test_switchboard_alpha.py` (147), `tests/config/test_switchboard_bravo.py` (56), `tests/config/test_switchboard_charlie.py` (91), `tests/config/test_switchboard_delta.py` (113), `tests/config/test_switchboard_echo.py` (50), `tests/config/test_training_wheels.py` (20) | complete mechanical inventory; local constructor/configuration assertions; `DefaultsRobinhood.vy` generation remains fail-closed |
| Probes | `tests/probes/test_action_block_identity_probe.py`, `tests/probes/test_stock_token_transfer_probe.py`, `tests/probes/test_probe_tooling.py` | controlled doubles and deterministic JSON; not immutable-state receipts |
| Clock harness | `tests/clock/test_clock_profiles.py`, `tests/utils/clock_profiles.py` | synthetic clock traces and rollback in local Boa |

The Robinhood blueprint currently reports unresolved dependencies, including
Ledger binding, H-04 parameters, H-05 plan/action data, oracle and liquidity
artifacts, PSM sequencing, H-08 proof, H-09 clean-deployment/negative suite,
H-10/H-11 rehearsal/release, and SecOps handoff.
`DefaultsRobinhood.vy` is intentionally absent until its inputs are resolved.

### 3.3 Existing Base fork tests

All 142 current Base-marked tests are in these mechanically enumerated files:

| File | Base-marked tests |
|---|---:|
| `tests/core/endaoment/test_endao_stabilizer.py` | 40 |
| `tests/priceSources/blueChip/test_bluechip_aavev3.py` | 3 |
| `tests/priceSources/blueChip/test_bluechip_compV3.py` | 2 |
| `tests/priceSources/blueChip/test_bluechip_euler.py` | 3 |
| `tests/priceSources/blueChip/test_bluechip_fluid.py` | 2 |
| `tests/priceSources/blueChip/test_bluechip_moonwell.py` | 3 |
| `tests/priceSources/blueChip/test_bluechip_morpho.py` | 3 |
| `tests/priceSources/curve/test_curve_prices.py` | 32 |
| `tests/priceSources/curve/test_green_ref_pool.py` | 28 |
| `tests/priceSources/test_aero_ripe.py` | 21 |
| `tests/priceSources/test_pyth_prices.py` | 3 |
| `tests/priceSources/test_stork_prices.py` | 1 |
| `tests/priceSources/test_superoethb.py` | 1 |
| **Total** | **142** |

They use Base addresses, Base whales, Etherscan-derived contracts, and
Base-specific pools/adapters. They provide useful behavioral patterns but do not
establish Robinhood identity, clocks, archive capability, or liquidity.

### 3.4 Core and composed-route tests

| Integration | Existing tests and reusable assertions | Qualification gap |
|---|---|---|
| Ledger | `tests/data/test_ledger.py`, `tests/data/test_ledger_action_block.py`, plus `tests/core/teller/test_teller_action_block.py`; profile and probe tests above | no real `ArbSys(0x64)`, receipt/L1/child/EVM relation, runtime failure, or RH composed-route proof |
| Teller | deposit, withdraw, custody, balance-delta, rollback, mutex, mutation, and composed M4 tests under `tests/core/teller/` | no canonical proxy/token behavior or fork snapshot sequence |
| GuardedErc20 | `tests/vaults/test_guarded_erc20.py`, consumer inventory and composed CreditEngine/AuctionHouse/Deleverage routes | no canonical proxy/control/return behavior or final VaultBook binding |
| CreditEngine | tests under `tests/core/creditEngine/`, including `test_credit_dyn_rate.py` and `test_stock_backing.py` | no RH oracle/fallback activation or canonical asset path |
| AuctionHouse | all files under `tests/core/auctionHouse/`, including auctions and stock delivery | no pinned-state liquidation with final roles, assets, and prices |
| Deleverage | all files under `tests/core/deleverage/`, including stock delivery and swap-collateral paths | no pinned-state liquidity, slippage, or action-block proof |
| PSM | PSM config, mint, redeem, view, transfer, fee, cap, interval, depeg, reserve, yield, and rollback tests under `tests/core/endaoment/` | no canonical USDG, activation ceremony, sequencer policy, or RH liquidity |

These tests should remain unit/composed-local tests. None can move into the fork
suite unchanged because their fixture graph does not bind immutable Robinhood
inputs.

### 3.5 Profiles, planners, manifests, and evidence APIs

| Component | Current implementation | Reuse boundary |
|---|---|---|
| Network profiles | `config/network_profiles.py` contains local, Base mainnet/testnet, and Robinhood mainnet/testnet; validates chain ID, dirty state, positive pin, operation policy, paths, identities, and manifest assertions | reuse validation functions; add no RH data to `config/BluePrint.py` |
| Base blueprint | `config/BluePrint.py` contains only `base` and `local` address/parameter graphs plus Base tokens, Curve, yield tokens, and whales | **do not reuse as RH fixture data** |
| RH blueprint | `config/robinhood_blueprint.py`, `config/robinhood-parameters.json` | consume only after owner blockers close; do not fill omissions in tests |
| Parameter generation | `scripts/params/generate_robinhood_defaults.py`, `scripts/params/regenerate_defaults.py`; tested by `tests/config/test_defaults_robinhood.py` | offline owner input; fork suite verifies deployed values, not generation |
| Migration entrypoint | `scripts/migrate.py` | plan mode is import-free; its fork mode loads account/funding state and is policy-blocked for RH, so it is not a qualification runner |
| Planning | `scripts/utils/migration.py`, `scripts/utils/migration_runner.py`, `scripts/utils/migration_helpers.py` | H-05 blocked-plan and deterministic report foundations; the frozen tree names no separate action-layer API, so the suite must wait for an owner-named interface rather than coin one |
| Evidence schema | `scripts/utils/manifest_schema.py`, `docs/chains/rh/schemas/deployment-manifest-v2.schema.json`, RH manifest runbook/evidence documents | H-06 schema v2 and candidate operator class are integrated; any successor fork-evidence interface/version is outside this frozen tree and cannot be assumed |
| Artifact verification | `config/contract-artifact-expectations.json`, `scripts/check_contract_artifacts.py`, inventory tests | verifies local compiler/artifact ceilings; H-07 owns verifier adapters, ABI export, and deterministic artifact handling, not deployed topology |
| Post-deployment assertions | H-08 proposes `scripts/check_deployment.py`, `scripts/utils/deployment_assertions.py`, `tests/deployment/test_post_deployment_assertions.py`, and `tests/deployment/test_registry_topology.py` | H-08, not H-07, owns deployed relationships/topology and read-only post-deployment assertions |
| Clock inventory | `config/block-clock-inventory.json`, `scripts/check_block_clock_inventory.py`, clock specifications and plans | static inventory and local harness only; final deployed clock assertions belong in H-08/H-09 consumption |
| Historical probe evidence | `docs/chains/rh/evidence/ledger-action-block-mainnet-fork.json`, `docs/chains/rh/evidence/ledger-action-block-testnet-fork.json` | historical controlled evidence, not a fresh pinned qualification receipt |

Current lifecycle state and ownership at this tree are decisive:

- H-05: integrated blocked planning; no authorized executable action layer;
- no separately named action-layer API exists in the frozen repository;
- H-06: schema-v2 implementation/candidate environment only;
- H-07: specified verifier/ABI/artifact handling; implementation absent;
- H-08: specified post-deployment checker/topology assertions; implementation
  absent;
- H-09: specified clean-deployment/negative suite, including
  `tests/deployment/fork/**` with network disabled by default; implementation
  absent;
- H-10: separately authorized test-environment deployment/live runbook lane;
- H-11: separately authorized production rehearsal/restricted-release lane;
- H-12: separately authorized CCIP artifact/integration lane.

The suite must not recreate any of these APIs under `tests/`.

The strings `H-ACT`, `RB-CLOCK-CURVE`, `RB-H07-CURVE-GRAPH`,
`RB-USDG-OVERLAY-LAYOUT`, and `LOCAL_FORK_QUALIFIED` do not occur in the frozen
repository. They came from non-repository conditional planning and are not
controlling names, APIs, stop codes, or verdicts here. This revision retains no
requirement that depends on those labels.

### 3.6 Fork and state helpers already present

`tests/conf_env.py` is the sole general fork harness:

- `--fork` accepts `local`, `mainnet`, or `base`, not Robinhood;
- remote blocks are fixed at mainnet `21,552,600` and Base `34,471,929`;
- an Alchemy URL is assembled from `WEB3_ALCHEMY_API_KEY`;
- an Anvil subprocess is started on a dynamically selected port;
- `boa.fork` and `boa.env.evm._fork_try_prefetch_state` are used;
- `tests/conf_env.py` configures Etherscan with `boa.set_etherscan`; Base-marked
  tests then use `boa.from_etherscan`.

Repository tests also use:

- `boa.env.anchor()` for local snapshot/reset;
- `boa.env.prank()` and local account generation;
- `boa.env.set_balance` and `time_travel`;
- `boa.env.set_storage(ARB_SYS, 0, value)` at six call sites in
  `tests/data/test_ledger_action_block.py`,
  `tests/core/teller/test_teller_withdraw.py`, and
  `tests/vaults/modules/test_stab_vault_claims.py`;
- controlled `ArbSys` and token mocks;
- local cache selection through `boa.interpret.set_cache_dir`.

Limitations:

1. the harness does not bind block hash, parent hash, state root, receipt root,
   finality, or archive-method capability;
2. it has no request recorder or RPC-method allowlist;
3. it has no proof that the fork was destroyed;
4. its session-scoped process and Boa caches can leak state across scenarios;
5. Titanoboa/PyEVM does not provide a proven Robinhood four-clock model;
6. the real Nitro `ArbSys` precompile at `0x64` is not demonstrated by the
   repository harness;
7. `anchor()` rolls back EVM state, not all Python trace/evidence globals;
8. `free_port` binds `('', 0)`, not an explicit loopback address, and the Anvil
   readiness loop has no deadline;
9. repository evidence records a sandbox run where `free_port` produced 57
   setup errors until loopback socket permission was granted;
10. `boa.env.set_storage` proves the repository has a storage-overlay primitive,
    but its six current uses target the local `ArbSys` double and prove nothing
    about canonical USDG layout;
11. Etherscan coupling and Base prefetch assumptions are inappropriate for RH.

## 4. Scenario-by-scenario matrix

### 4.1 Chain identity, archive RPC, and clocks

| ID | Scenario | Current coverage | Evidence and missing closure |
|---|---|---|---|
| N-01 | RH chain-ID/profile selection | partial | `network_profiles.py` validates expected IDs 4663/46630, but no immutable chain observation |
| N-02 | exact block, hash, parent, timestamp, state root, finality pin | external identity | no accepted pin record or archive read |
| N-03 | receipt, transaction, adjacent-header, and L1-origin coherence | external identity | probes use controlled evidence, not accepted chain state |
| N-04 | archive RPC code/storage/proof/call capability at the pin | external identity | no endpoint capability receipt |
| N-05 | read-only method allowlist and secret-free transcript | partial | secret tests and profile policy exist; no recording provider |
| N-06 | RPC child/L1/EVM `NUMBER`/timestamp/`ArbSys` semantics | external identity | engine and pin are missing; any mismatch must stop before qualification |
| N-07 | Ledger action source and failure semantics | local Boa | strong local doubles/mutants; no real `ArbSys(0x64)` |
| N-08 | snapshot, reset, replay, and fork destruction | partial | `anchor()` and local rollback exist; no process/fork destruction proof |

### 4.2 Canonical tokens and oracles

| ID | Scenario | Current coverage | Evidence and missing closure |
|---|---|---|---|
| T-01 | canonical WETH address, proxy/implementation, code hash | external identity | candidate identity is not an accepted immutable input |
| T-02 | canonical USDG address, proxy/implementation, code hash | external identity | candidates exist outside the frozen owner graph; no accepted proof |
| T-03 | GREEN, sGREEN, RIPE, VaultBook, and handler identities | owner API | H-07 artifact identities and H-08 deployed relationship/topology assertions are absent |
| T-04 | decimals, name, symbol, and supply getters | partial | generic/local checks exist; canonical RH reads do not |
| T-05 | transfer/transferFrom return and balance-delta behavior | local Boa | adversarial return-shape and exact-delta tests exist |
| T-06 | pause, blocklist, fee, and privileged-transfer behavior | local Boa | generic mocks only; canonical controls/roles unknown |
| T-07 | permit support, domain, nonce, deadline, and replay | local Boa | local token behavior only; canonical USDG/WETH capability unknown |
| T-08 | USDG compiler-derived balance and total-supply slot identities | external identity | exact slots are not established in the frozen tree; proxy/source/layout/getter proof must precede any overlay |
| T-09 | exact USDG storage overlay and two-delta invariant | external identity | cannot execute until T-02/T-08 and owner assertion API close |
| O-01 | Chainlink feed/proxy/aggregator identity and decimals | external identity | no accepted per-profile feed manifest |
| O-02 | latest-round positivity, timestamps, answered-in-round, staleness | mock | Chainlink mocks cover behavior; no pinned RH rounds |
| O-03 | sequencer-down and grace-period behavior | external identity | no accepted RH sequencer feed or explicit operational-gating decision |

### 4.3 Uniswap, Curve, PriceDesk, dynamic rates, Teller snapshots, and PSM

| ID | Scenario | Current coverage | Evidence and missing closure |
|---|---|---|---|
| M-01 | Uniswap factory/router/quoter/position-manager identities | external identity | no accepted RH deployment graph |
| M-02 | RIPE/WETH pool identity, fee, tick spacing, observations | external identity | no accepted pool identity |
| M-03 | liquidity amount, range, owner/custodian, removal authority | owner API | economic and custody owner inputs unresolved |
| M-04 | exact-input/output swaps, both directions, slippage boundaries | absent | no RH Uniswap fixture or canonical liquidity |
| M-05 | future Uniswap V3 oracle manipulation/TWAP adapter | inappropriate | no launch security-critical Uniswap price source; retain for a later adapter tranche if architecture changes |
| C-01 | exact Curve source/compiler/blueprint identities and deployed registry graph | owner API | H-07 must provide deterministic artifacts; H-08 must provide deployed relationship/topology assertions |
| C-02 | USDG/GREEN pool identity, parameters, LP custody | owner API | Profile 2 graph and custody are not integrated |
| C-03 | add/remove liquidity, swaps, reserve-fraction stress | Base only | Curve patterns run on Base; no RH pool |
| C-04 | Profile 1 has reserved PriceDesk IDs 2-5 empty and no Curve dependency | partial | blueprint omissions are tested offline, not against a deployed profile |
| P-01 | PriceDesk source IDs/order and Profile 1/Profile 2 separation | local Boa | local fixture always installs Base-oriented sources and must not move unchanged |
| P-02 | dynamic-rate fallback during invalid/missing external price | local Boa | CreditEngine unit coverage exists |
| P-03 | dynamic-rate activation and threshold transitions | local Boa | local values/mocks only; final profile inputs absent |
| P-04 | ten Teller/Curve snapshot observations and `ma_exp_time` 600/866 separation | Base only | snapshot logic exists on Base/local; RH four-clock fidelity unproved |
| P-05 | PSM remains disabled in staging and uses Chainlink authority | partial | defaults/PSM unit tests prove local flags; no final deployed staging state |
| P-06 | Endaoment stabilizer behavior at configured weights/caps | Base only | Base fork/local behavior only |

### 4.4 Core lifecycle

| ID | Scenario | Current coverage | Evidence and missing closure |
|---|---|---|---|
| L-01 | canonical deposit and exact Teller receipt | local Boa | strong custody/delta/rollback tests |
| L-02 | borrow with final collateral, oracle, caps, and roles | local Boa | core behavior exists; all external bindings absent |
| L-03 | full and partial repay | local Boa | unit/composed behavior exists |
| L-04 | withdraw through canonical GuardedErc20/VaultBook | local Boa | exact delivery checks exist |
| L-05 | unhealthy position and liquidation transition | local Boa | prices/assets are mocks |
| L-06 | AuctionHouse creation, bid, settlement, stock delivery | local Boa | 93 tests; no RH clocks/assets/roles |
| L-07 | Deleverage stock delivery and collateral swap | local Boa | 282 tests; no RH DEX/liquidity |
| L-08 | Teller custody, balance snapshots, no-return/revert handling | local Boa | exact local semantics; canonical token behavior unknown |
| L-09 | GuardedErc20 internal/external movements, deficits, recovery | local Boa | extensive adversarial local tests |
| L-10 | deposit-to-liquidation composed route with action-block failure atomicity | partial | M4-style local routes exist, but no single canonical pinned-state route |

### 4.5 Roles, deterministic inputs, evidence, replay, and rollback

| ID | Scenario | Current coverage | Evidence and missing closure |
|---|---|---|---|
| G-01 | local role, pause, authority, and emergency semantics | local Boa | contract-level assertions exist |
| G-02 | exact deployer/owner/governance/multisig identities and handoff | external identity | final authority inputs and receipts absent |
| G-03 | deterministic H-05 plan bound to commit/tree/profile | partial | blocked-plan implementation exists; executable final plan does not |
| G-04 | typed owner action sequence and read-only rehearsal | owner API | the frozen tree names no action-layer API; do not encode a substitute in tests |
| G-05 | H-06 deterministic evidence and report hashing | partial | schema-v2/JCS/history exists; no frozen-tree fork-evidence successor is defined |
| G-06 | H-07 verifier/ABI/deterministic artifact identities | owner API | implementation not started |
| G-07 | H-08 assertion graph and state-delta policy | owner API | implementation not started |
| G-08 | H-09 clean-deployment/fork fixture contract, collection ledger, and result vocabulary | owner API | specification exists and requires network disabled by default; implementation and exact ledger/vocabulary are absent |
| G-09 | rejection of every forbidden Base address/profile assumption | partial | offline regression/omission checks exist; no final RH input manifest |
| G-10 | byte-for-byte deterministic replay on a recreated fork | absent | no fork runner or sealed scenario ledger |
| G-11 | rollback by destroying/recreating the disposable fork | partial | local rollback exists; compensating writes are forbidden |
| G-12 | clean-process, mode-0700 cache, environment, and residue proof | partial | known validation pattern exists; no suite runner/receipt |

### 4.6 Decision-register traceability

The scenario IDs above are census-local handles, not a replacement decision
register. The controlling specification states that its recommendations are not
approvals. Required reconciliation is:

| Census rows | Frozen-tree decision register | Effect |
|---|---|---|
| N-01 through N-06 | DR-001 mainnet facts, DR-002 test environment, DR-003 network-profile API, DR-013 gas/finality/retries | provider, archive, pin, finality, retry, and clock inputs remain open |
| T-01 through T-09; O-01 through O-03 | DR-009 USDG/PSM, DR-012 external addresses | canonical identities require checksum, code/type/interface/decimals, primary-source provenance, and final re-query |
| M-01 through M-04; C-01 through C-03 | DR-012 external addresses, DR-013 gas/finality/retries | DEX graph, liquidity, slippage, and operational bounds remain open |
| P-05 and P-06 | DR-009 USDG/PSM | disabled scaffold and activation remain separate decisions |
| G-02 | DR-011 governance/admin roles | signer backend, Safe/timelock/guardian graph, and deployer-removal proof remain open and belong before H-10 |
| G-03 and G-04 | DR-004 migration namespace/version | final executable planning/actions cannot be inferred from current blocked H-05 reports |
| G-05 and G-10 | DR-005 manifest/release evidence | evidence retention/schema and immutable replay linkage remain reviewable |
| G-08 and G-12 | DR-014 CI plus H-09 | protected fork/live job policy and isolation remain separately gated |

## 5. Reuse and non-reuse decisions

### 5.1 Reusable infrastructure

- pure validators from `config/network_profiles.py`;
- canonical JSON and hash primitives from integrated H-06 schema v2 or a
  separately approved successor;
- local artifact compiler/checker mechanics, with deterministic artifact/ABI
  identity consumed through H-07 and deployed topology through H-08;
- `ClockController` trace ideas for expected relationships, consumed only
  through H-08;
- Teller exact-balance-delta assertions;
- GuardedErc20 delivery/deficit/return-shape assertions;
- CreditEngine dynamic-rate transition cases;
- AuctionHouse and Deleverage composed-route ordering and rollback cases;
- PSM fee/cap/interval/reserve/depeg case shapes;
- Base Curve/price-source test case shapes, after removing every Base address,
  whale, pool, and Etherscan assumption;
- `migration_runner.py` source discovery and current-Git identity mechanics,
  after replacement by the final owner interfaces.

### 5.2 Fixtures with accidental Base assumptions

`tests/conf_env.py`, `tests/conf_core.py`, and `config/BluePrint.py` must not be
imported by the future suite as domain fixtures:

- `--fork` has no Robinhood mode;
- remote construction assumes Alchemy and Etherscan;
- `ADDYS`, `PARAMS`, `CORE_TOKENS`, `CURVE_PARAMS`, `WHALES`, and
  `YIELD_TOKENS` are Base/local graphs;
- the PriceDesk fixture registers IDs 1 through 10 and therefore occupies every
  Profile 1 reserved-empty slot 2 through 5, not merely Curve ID 2;
- PSM remote setup assumes Base USDC;
- Chainlink stale-time behavior is altered for remote fixtures;
- Ledger is not constructed from the final RH action-block owner binding.

### 5.3 Tests that move unchanged

**None.** Existing tests should remain in their current unit, local-composition,
Base-regression, schema, inventory, or probe lanes. The future suite may reuse
their assertions through owner-bound fixtures, but copying or moving them
unchanged would import false chain assumptions or downgrade their existing role.

### 5.4 Tests that remain unit/offline tests

- all mock-token, mutation, revert, reentrancy, fee-on-transfer, and malformed
  return tests;
- H-05 plan semantics, H-06 schema/filesystem failures, H-07
  verifier/ABI/artifact validation, and H-08 assertion/topology validation;
- defaults/blueprint omission generation;
- block-clock source inventory;
- contract bytecode ceiling and local artifact generation;
- controlled action-block and stock-token probes;
- dynamic-rate arithmetic edge cases;
- PSM arithmetic, interval, cap, fee, depeg, and reserve permutations;
- future Uniswap oracle manipulation tests unless a price-source adapter is
  separately approved.

Fork tests verify final owner outputs and canonical integration; they do not
replace these faster diagnostic suites.

## 6. Active owner-agent dependencies

Parallel owner work exists in isolated worktrees at the same frozen commit, but
their current reports are untracked and are **not integrated APIs or final
authority**. Implementation must re-read their integrated successors, not import
these worktrees.

| Owner lane | Current dependency required by the fork suite |
|---|---|
| Ledger | final `0x64` action-block constructor/runtime identity, real clock/receipt assertions, and critical-route failure expectations |
| Teller | canonical custody/receipt matrix, token return behavior, snapshot ownership, and withdrawal responsibility |
| GuardedErc20 | final VaultBook/handler graph, canonical token control behavior, delivery invariants, and H-08 assertions |
| Network/token/oracle | accepted pin record, read-only archive endpoint capability, canonical WETH/USDG identities and layouts, Chainlink feed graph, sequencer policy |
| Uniswap | deployment/pool identity, liquidity amounts/ranges, custodian/removal authority, and launch slippage thresholds; no launch oracle adapter |
| Curve | H-07 deterministic source/artifact identities, H-08 registry/pool topology assertions, an owner-approved Profile 2 vector, LP custody, and four-clock requirements |
| PSM/liquidity/activation | final disabled-staging state, Chainlink authority, activation preconditions, caps/fees/reserves, emergency/rollback expectations |
| Deployment owner | final H-05 plan, an owner-named typed action interface, H-06 evidence interface, H-07, H-08, H-09, authority inputs, and deterministic artifact/collection ledger |
| H-09 fork architecture | owns `tests/deployment/fork/**`, the network-disabled default, explicit read-only archive-fork opt-in, disposable runtime, deterministic teardown/replay, and qualification evidence contract |
| H-10 live/rehearsal architecture | separately owns any live testnet, real transaction, external signer/account, deployed rehearsal artifact, persistent external state, or operational execution |

Future real-integration coverage for Uniswap, Curve, canonical tokens, oracles,
PSM, Teller, GuardedErc20, Ledger, AuctionHouse, Deleverage, and other protocol
components is composed inside the opt-in H-09 archive-fork architecture.
Component-specific reports remain authoritative for their individual semantics,
parameters, acceptance assertions, custody, and activation decisions. H-09
composition does not reopen or replace those owner boundaries.

Non-repository parallel planning proposed the following Curve vector:
`A=100`, fee `4_000_000`, off-peg multiplier `20_000_000_000`, separate fresh
forks for `ma_exp_time=600` and `866`, ten snapshots, staleness over 7,200
unchanged EVM numbers, 100 USDG plus 100 GREEN initial liquidity, and
two-direction reserve-fraction stress. **None of those literals has provenance
in the frozen tree.** They are unverified external proposals, excluded from
implementation inputs until an owner integrates a source and H-07/H-08 bind its
artifact and deployed topology.

The same boundary applies to the external proposal that canonical USDG uses
balance slot 1 and total-supply slot 2. The frozen repository does not prove
those slot numbers. Before any overlay, owner evidence must establish the
canonical proxy, implementation, compiler-derived layout, exact slots, and
getter-to-slot behavior at the immutable pin. Only a separately approved H-08
state-delta policy may then define permissible changes. All other storage, code,
account, and admin values must remain identical.

## 7. Future implementation tranche

### 7.1 Controlling owner disposition: opt-in H-09 archive-fork mode

The frozen specification already assigns H-09:

- `tests/deployment/test_clean_deployment.py`;
- `tests/deployment/test_resume_reconciliation.py`;
- `tests/deployment/test_reproducible_artifacts.py`; and
- `tests/deployment/fork/**` fixtures **with network disabled by default**.

The owner resolves the prior conflict as follows:

1. H-09 retains `tests/deployment/fork/**`.
2. Network access remains disabled by default. Normal collection, ordinary
   repository tests, and default H-09 execution require no RPC endpoint and
   must not attempt network access, acquire accounts/signers, broadcast
   transactions, or mutate live protocol/chain state.
3. Read-only Robinhood archive-fork qualification is an explicit opt-in H-09
   mode. It requires an affirmative operator action and fails closed before
   network access when any required input is absent or inconsistent.
4. The opt-in mode binds at minimum: expected chain ID; exact fork block number
   and hash; approved archive endpoint identity or fingerprint; canonical
   contract/proxy/token/oracle/pool/custody identities; expected Robinhood
   profile; reproducible evidence destination; and explicit read-only mode.
5. Endpoint credentials and secrets remain external to the repository and are
   never emitted into evidence.
6. Account impersonation and state alteration are permitted only inside the
   disposable local fork engine. The mode never uses a real signer and never
   submits a transaction to Robinhood.
7. Every execution uses an isolated disposable runtime and proves deterministic
   teardown and replay. Repeated runs over the same frozen inputs reproduce the
   same material assertions and evidence identities.
8. H-10 remains the separately authorized live-test/rehearsal lane for live
   testnet activity, real transactions, external signers/accounts, deployed
   rehearsal artifacts, persistent external state, or operational execution.
   Read-only archive-fork qualification does not move to H-10 merely because it
   reads from an RPC endpoint.

The three named H-09 files outside `fork/**` remain separate H-09 outputs and
are not silently superseded by this subtranche. This disposition approves
architecture only; it does not authorize implementation or execution of any
proposed path. No additional standalone review is required for this bounded
decision before the combined implementation plan consumes it.

### 7.2 Candidate file ceiling

The future tranche has a **maximum ceiling of exactly 33 paths**, all under
`tests/deployment/fork/`. This is a proposed consumer-only decomposition, not an
H-09-sealed ledger. It applies only to the fork subtranche, uses per-gate fixture
owners, and avoids numeric filenames that would churn the ledger when a case is
inserted. The owner disposition approves this decomposition as planning
authority only. H-09 must still seal the final path/node ceiling before any file
is created.

```text
tests/deployment/fork/conftest.py
tests/deployment/fork/offline/conftest.py
tests/deployment/fork/offline/test_entry_gates.py
tests/deployment/fork/offline/test_process_isolation.py
tests/deployment/fork/offline/test_collection_contract.py
tests/deployment/fork/network/conftest.py
tests/deployment/fork/network/test_network_profiles.py
tests/deployment/fork/network/test_pin_archive.py
tests/deployment/fork/network/test_rpc_inventory.py
tests/deployment/fork/network/test_clocks.py
tests/deployment/fork/network/test_fork_lifecycle.py
tests/deployment/fork/identity/conftest.py
tests/deployment/fork/identity/test_canonical_tokens.py
tests/deployment/fork/identity/test_protocol_artifacts.py
tests/deployment/fork/identity/test_token_metadata_returns.py
tests/deployment/fork/identity/test_token_permit_controls.py
tests/deployment/fork/identity/test_usdg_overlay.py
tests/deployment/fork/identity/test_chainlink.py
tests/deployment/fork/identity/test_sequencer.py
tests/deployment/fork/markets/conftest.py
tests/deployment/fork/markets/test_uniswap_deployment_pool.py
tests/deployment/fork/markets/test_uniswap_liquidity_swaps.py
tests/deployment/fork/markets/test_curve_artifact_pool.py
tests/deployment/fork/markets/test_pricedesk_profiles.py
tests/deployment/fork/markets/test_dynamic_rate.py
tests/deployment/fork/markets/test_teller_snapshots.py
tests/deployment/fork/markets/test_psm_staging.py
tests/deployment/fork/lifecycle/conftest.py
tests/deployment/fork/lifecycle/test_core_lifecycle.py
tests/deployment/fork/lifecycle/test_liquidation_auction_house.py
tests/deployment/fork/lifecycle/test_deleverage.py
tests/deployment/fork/lifecycle/test_roles_governance.py
tests/deployment/fork/lifecycle/test_replay_evidence_rollback.py
```

There are no local `provider.py`, `scenarios.py`, `artifacts.py`,
`assertions.py`, `evidence.py`, overlay-schema, golden-manifest, or fork-profile
modules. Those names previously risked bypassing owner boundaries.

### 7.3 Fixture ownership

The root `conftest.py` may only enforce safe-default network disablement, select
the explicitly requested read-only H-09 execution mode, validate its complete
input envelope before network access, and reject environment drift. Each
gate-local `conftest.py` may only compose and lifecycle-manage fixtures returned
by owners:

- H-05 owns deterministic plan inputs; a separately owner-named interface must
  own typed permitted actions;
- H-06 owns evidence records, canonical serialization, and hashing;
- H-07 owns verifier/ABI/deterministic artifact identities;
- H-08 owns deployed relationships, topology assertions, and allowed state
  deltas;
- H-09 owns the safe-default/qualification-mode contract, node ledger, result
  vocabulary, ceiling, archive endpoint identity/fingerprint policy,
  reproducible evidence destination, disposable-runtime proof, and
  teardown/replay contract;
- network/token/oracle owners supply immutable external identities;
- DEX and protocol owners supply approved pool, custody, parameter, and role
  manifests.

The suite may compare owner outputs; it may not define fallbacks, infer omitted
values, synthesize a canonical token, or replace a missing API with a test-local
dataclass/JSON schema.

### 7.4 Profile separation and input boundaries

Each run consumes one immutable, content-addressed input envelope:

- repository commit and tree;
- network profile and expected chain ID;
- exact fork block number/hash/parent/state root/timestamp/finality and L1
  fields;
- approved archive endpoint identity or endpoint fingerprint, with its secret
  endpoint/credentials supplied only through an opaque external alias;
- explicit read-only mode and affirmative operator opt-in;
- reproducible evidence destination outside the repository;
- fork-engine/version/capability identity;
- canonical token/proxy/implementation/layout graph;
- Chainlink and sequencer policy graph;
- Uniswap and Curve graph plus custody and economic inputs;
- protocol artifact, constructor, role, and parameter graph;
- H-05 plan hash and the owner-named typed-action hash;
- H-06/H-07/H-08/H-09 schema/interface versions and content hashes.

Profile 1 and Profile 2 are separate runs and separate forks. Profile 1 must prove
that reserved PriceDesk IDs 2-5 remain empty and that PSM uses Chainlink without
Curve. Profile 2 adds the owner-bound Curve graph. Mainnet and testnet manifests
must never inherit from Base or from each other. An explicit input hash is
required for every parameter expansion.

### 7.5 Fail-closed entry gates

Collection or preflight stops before an RPC call when any of these is true:

1. repository commit/tree or final H-09 ceiling differs;
2. the worktree is dirty, has unapproved untracked/ignored residue, or the index
   is nonempty;
3. any owner API/version/hash is missing or inconsistent;
4. a manifest field is omitted, symbolic, a candidate, or inherited from Base;
5. explicit read-only mode, affirmative operator opt-in, approved endpoint
   identity/fingerprint, or external evidence destination is absent;
6. an RPC URL/key is present outside the single opaque owner-approved alias, or
   any secret would be committed or emitted into evidence;
7. the plan requests a real account/signer, broadcast, live-state mutation,
   deployment, activation, publication, or impersonation outside the isolated
   disposable fork;
8. the exact pin/finality/archive capability is unproved;
9. the fork engine cannot preserve the required clock relationships;
10. canonical contract/proxy/token/layout/oracle/pool/custody/role identities
    are unresolved;
11. the required action lacks an owner-named typed interface or the assertion
    cannot be represented by H-08;
12. evidence, isolation, destruction, or replay semantics are ambiguous.

After the first RPC read, any identity mismatch, unexpected RPC method,
unexpected state delta, Base address, clock divergence, code/storage mismatch,
token-control surprise, oracle invalidity, pool/custody mismatch, plan drift, or
teardown failure stops the run. Exact machine-readable stop codes must come from
the eventual H-08/H-09 contract; the frozen tree supplies none for these cases.

No missing input becomes a skip or xfail in explicit qualification mode.
Precondition absence is a failed qualification receipt. Safe-default mode may
deselect network groups only according to the H-09-sealed offline ledger and
must never be reported as qualification.

### 7.6 Test groups and execution order

Run serially in this order:

1. **Default H-09:** run `offline/` only, with no RPC endpoint required or
   exposed. Ordinary repository execution ends here.
2. **Opt-in preflight:** after affirmative operator action, validate the full
   read-only input envelope and evidence destination before exposing the
   archive endpoint alias.
3. **Immutable network gate:** run `network/`; destroy the fork after the clock
   probe.
4. **Canonical identity gate:** run `identity/`; any storage overlay gets its
   own new process and fork.
5. **Market/Profile gate:** run `markets/`; Profile 1 first, then Profile 2;
   every owner-approved clock profile uses a separate new process/fork.
6. **Core lifecycle gate:** run `lifecycle/`; start from a new pristine fork for
   each destructive scenario group, then destroy all prior forks, recreate from
   immutable inputs, replay, compare evidence, and prove destruction.

Do not use pytest-xdist initially. Parallelism can be considered only after H-09
defines independent provider/rate/cache/fork namespaces and deterministic merge
semantics.

### 7.7 Collection expectations

Collection has three distinct states:

1. **Current/pre-scaffold:** `tests/deployment/fork/` does not exist, so no fork
   collection count is claimed.
2. **H-09 safe-default scaffold:** collection succeeds against an exact offline
   ledger; network-bearing groups are deselected by the explicit safe-default
   policy, and missing owner inputs fail offline preflight tests at execution
   before RPC. This is the behavior for normal collection, ordinary repository
   tests, and default H-09 execution.
3. **Explicit qualification mode:** all owner-approved qualification nodes
   collect only after affirmative operator opt-in and complete read-only input
   binding; zero skips, xfails, or deselections are permitted.

H-09 must eventually publish:

- the exact 33-or-fewer path ledger;
- separate exact ordered node-ID ledgers for safe-default and each explicitly
  authorized network/profile qualification mode;
- parameter hashes and total collected-node counts;
- safe-default deselections and zero qualification-mode deselections;
- the only permitted verdict vocabulary.

Once H-09 seals either ledger, collection is repeated in a second clean process
and its ordered node-ID digest must match before execution begins. Missing owner
inputs then produce deterministic failing preflight nodes rather than collection
failure, so the digest remains testable. This report intentionally does not
invent future node counts.

### 7.8 Clean-process, cache, and environment requirements

Use a new Python process for each clock profile, USDG overlay, market deployment,
core destructive group, and replay. Each process receives a unique mode-0700
external root containing:

- `PYTHONPYCACHEPREFIX`;
- `XDG_CACHE_HOME`;
- `HYPOTHESIS_STORAGE_DIRECTORY`;
- Boa cache selected through `boa.interpret.set_cache_dir`;
- pytest `--basetemp`;
- evidence scratch space.

Set `PYTHONDONTWRITEBYTECODE=1` and run pytest with
`-p no:cacheprovider`. Do not create `.pytest_cache`, bytecode, Anvil state, fork
databases, manifests, or evidence in the repository. Begin from an environment
allowlist after unsetting Alchemy, generic RPC, private-key, mnemonic, cloud, and
Etherscan variables. Qualification must not use `boa.from_etherscan`, a whale,
a real signer, or a funded external account. A deterministic account may be
impersonated and local state may be altered only after the disposable fork is
created and proven isolated; those actions and deltas are fork-local evidence
and never produce a Robinhood submission.

Fresh processes are required because Boa contract/name caches, fork prefetch
state, Python evidence globals, transient storage, subprocess lifetime, and
clock traces are not all governed by `boa.env.anchor()`.

### 7.9 Deterministic evidence and rollback

The owner-approved H-06 evidence interface must record, without secrets:

- all input/API hashes and repository identities;
- engine/runtime/library identities;
- explicit read-only mode and affirmative opt-in;
- exact pin, approved endpoint identity/fingerprint, and archive-method
  capability receipt, without URL credentials;
- external evidence-destination identity;
- ordered RPC method inventory;
- ordered scenario/action/assertion IDs;
- canonical code, proxy, implementation, storage, and role identities;
- transactionless call results and local-fork action receipts;
- allowed pre/post state digests and unexpected-delta proof;
- ordered pytest node digest and result;
- fork process identity, termination, storage disposal, and residue proof;
- second-run byte-for-byte evidence digest.

Rollback means terminate and destroy the disposable fork, verify its storage and
process are gone, and recreate it from the immutable pin. It never means
compensating token transfers, storage writes, administrative calls, or a reverse
migration.

The result vocabulary is undefined at this frozen tree. H-09 must define it;
tests may not coin a qualification verdict.

### 7.10 Runtime estimate

The following are **unvalidated planning estimates**, not measured fork-suite
runtimes. Repository-only anchors are 2,866 selected local cases in 276.58
seconds in `docs/chains/rh/evidence/dependency-security-gate.md` and 3,785 local
passes in 539.62 seconds in `docs/chains/rh/hardening/hardening-pass-report.md`.
Neither anchor measures archive latency, fork recreation, Curve/Uniswap setup,
or replay. Conditional on an accepted archive provider and capable fork engine:

| Gate | Estimate |
|---|---:|
| offline collection/preflight | 5-10 minutes |
| immutable network, archive, token, and oracle gates | 20-40 minutes per network profile |
| four-clock and Ledger probes | 15-30 minutes per clock profile |
| Uniswap venue/liquidity/slippage | 30-60 minutes per profile |
| Curve Profile 2, two clock profiles, snapshots, stress | 60-120 minutes |
| PSM and core lifecycle | 45-90 minutes |
| destruction plus complete deterministic replay | approximately one additional full pass |
| **full cold serial qualification** | **6-10 hours** |

A later owner-approved isolated shard design could reduce wall time to roughly
3-5 hours. Provider throttling, archive latency, or engine recreation may make
these estimates longer.

### 7.11 Smallest independent review strategy

Although implemented as one tranche, review it as five non-overlapping deltas:

1. file ceiling, owner imports, entry gates, and environment/process isolation;
2. pin/archive/clock and canonical identity tests;
3. Uniswap/Curve/PriceDesk/rate/Teller/PSM tests;
4. core lifecycle, AuctionHouse, Deleverage, roles, and emergency behavior;
5. H-05 through H-09 bindings, replay, evidence, rollback, residue proof, and
   explicit confirmation that no H-10 through H-12 live authority was inferred.

For each delta, review only new suite files plus the exact owner API hashes they
consume. No production contract, migration, shared fixture, profile, generator,
schema, or configuration edit belongs in this tranche. A change outside the
sealed file list stops review and requires a new authorization.

## 8. Highest-risk missing scenarios

1. **Clock fidelity:** the fork engine has no proven model for child/L1/EVM
   `NUMBER`, timestamp, and `ArbSys`; a false model could qualify stale pricing
   and Ledger behavior incorrectly.
2. **Canonical USDG overlay:** a wrong proxy/layout/slot proof could corrupt
   unrelated canonical storage while appearing to fund the test.
3. **Immutable pin/archive capability:** without state-root and historical
   code/storage/proof reads, results cannot be replayed or attributed to one RH
   state.
4. **Sequencer policy:** there is no accepted sequencer feed or explicit
   operational-gating decision, leaving oracle grace behavior undefined.
5. **Liquidity identity and custody:** RIPE/WETH and USDG/GREEN pools, depth,
   ranges, ownership, and removal authority are unresolved.
6. **Owner action/assertion/evidence interfaces:** the frozen tree has no named
   typed-action interface; H-07, H-08, and H-09 implementations are missing,
   and H-06 has no approved fork-evidence successor. Local substitutes would
   invalidate the ownership model.
7. **Canonical composed route:** no pinned-state deposit-to-liquidation run
   proves Teller, Ledger, GuardedErc20, CreditEngine, AuctionHouse, Deleverage,
   prices, clocks, and token behavior together.
8. **Destruction/replay proof:** current snapshot helpers cannot demonstrate
   that overlays and scenario state are gone before a byte-identical replay.

## 9. Implementation recommendation

Do not start the 33-file tranche yet. Close dependencies in this order:

1. preserve the approved H-09 network-disabled default and explicit opt-in
   read-only mode as the implementation boundary;
2. final immutable network pin, approved archive endpoint
   identity/fingerprint, archive-method receipt, fork-engine clock
   capability, canonical WETH/USDG/feed/sequencer identities;
3. H-07 verifier/ABI/deterministic artifacts and H-08 deployed
   relationship/topology assertions, including Curve and protocol identities;
4. final Ledger, Teller, GuardedErc20, Uniswap, Curve, and PSM owner inputs;
5. final H-05 deterministic plan and an owner-named typed-action interface;
6. owner-approved H-06 fork evidence and H-08 assertion/state-delta interfaces;
7. H-09 safe-default/qualification-mode contract, explicit operator action,
   external evidence destination, disposable-runtime and replay proof,
   path/node ledgers, collection counts, stop codes, and result vocabulary;
8. implement/review `offline/`, `network/`, `identity/`, `markets/`, and finally
   `lifecycle/`.

Any different ordering risks encoding a test-local substitute or reviewing
against identities that later change. Governance identities and handoff
assertions in the fork suite remain read-only expectations; H-10 testnet action,
H-11 production rehearsal, and H-12 CCIP integration require their own fresh
authority and are outside this tranche.
