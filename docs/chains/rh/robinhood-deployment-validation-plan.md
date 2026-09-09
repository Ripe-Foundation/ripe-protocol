# Robinhood deployment validation plan

> **24 August 2026 PriceDesk supersession:** the BlueChip-at-ID-3 and
> Uniswap-absent planning statements below are historical. BlueChip is deferred
> at chain-local ID `0`; before PR #206, live ID 3 is the legacy functional
> UniswapV2Prices fallback, and the required PR #206 `2026082100/01` history
> promotes the authenticated inert monitoring replacement there. Launch
> priorities remain `[1, 2]`. See [`current-owner-priorities.md`](current-owner-priorities.md).

> **11 August 2026 CCIP supersession:** this plan's `1000`-deferred and
> disabled/not-deployed CCIP statements are preserved historical validation
> design. GREEN and RIPE CCIP topology is already live and is now an observed
> external-state assertion, not a launch deployment stage. Further mutation and
> release remain separately gated; see
> [`ccip-live-state.md`](ccip-live-state.md).

> **1 August 2026 currentness overlay:** Ready to continue bounded launch
> preparation. The retired shared-migration candidate was bound to exact
> transaction-executor parent `25c0d58e1243449276e4ac4cae8d7abb8272f376`, tree
> `2dd9ddb30c1bc09cc82b8ed1ffd67949a20a4abf`; those identities are historical
> evidence, not current plan authority. PR #61, Morpho V2 and BlueChipYield
> support and H-04 source authority are integrated. `DefaultsRobinhood.vy`
> exists, compiles, and matches
> the derived ledger. Source/configuration readiness reports exactly 64
> blockers with `configuration_consistent=true` and
> `deployment_ready=false`. No executable migration plan is authorized or
> currently censused. The former shared declarative source, runner,
> transaction executor, 17-stage/action census, and 86-key plan census are
> retired historical evidence. H-06 is a class qualification only. Repository configuration is prepared and
> consistent; production/onchain configuration has not occurred. No Robinhood
> migration, live execution, deployment, activation, RPC, account, key,
> signer, or release action has occurred for the non-CCIP launch candidate. The
> current repository-review candidate contains eight imperative
> `migrations/robinhood-mainnet/` files, `0000` through `0007`; they do not
> constitute an executable plan. Historical reservation `1000` is represented
> as confirmed external CCIP state, not as a deferred or executable launch mutation. The
> current PriceDesk topology is
> ID 1 Chainlink and ID 2 unchanged CurvePrices for GREEN only. ID 3
> BlueChipYield remains blueprint-selected but is not deployed or finalized by
> the current candidate; IDs 4/5 are empty and priorities are `[1,2]`; see
> [`curve-launch-activation.md`](curve-launch-activation.md). Historical
> future-path labels below remain narrow validation design, not current
> lifecycle authority.

- Status: Phase G completion draft; future tests and rehearsals are not implemented
- Starting specification checkpoint: `1b2c755`
- Completion commit: recorded in the Track 7 handoff after final validation
- Current migration review surface: eight imperative files under
  `migrations/robinhood-mainnet/`, `0000` through `0007`; the former
  `migrations/robinhood/` declarative source is retired and no executable plan
  is authorized or currently censused
- Candidate identity: uncommitted validation uses explicit preview artifacts
  bound to the complete prospective tree. Preview and synthetic-proof
  artifacts are non-production, non-executable, history-ineligible, and
  domain-separated from clean-HEAD production artifacts.
- Test history: proposed `migration_history/robinhood-testnet/v1/`
- Mainnet history: proposed `migration_history/robinhood-mainnet/v1/`
- Evidence date: 2026-07-23, America/Denver
- Planning correction: on 2026-07-24, the proposed deployment clock-profile
  test was renamed to `tests/deployment/test_network_clock_profiles.py` to
  avoid a pytest basename collision with the integrated Track 6 S1 test; no
  implementation is implied
- Minimum-change correction: on 2026-07-24, V-03 was clarified to require each
  slice's selected minimum disposition rather than infer a production change
  from a reservation. S3 is retained, S4 remains necessity-gated, and S5 now
  requires the owner-selected fresh-RH action-block Ledger while the deployed
  Base Ledger remains untouched.

## 1. Purpose and authority boundary

This is Deliverable B from
`docs/chains/rh/track-7-robinhood-deployment-support.md`. It defines future
validation for the network-profile, migration, manifest, verification, ABI,
deployment, role-handoff and release-evidence system specified in
`docs/chains/rh/robinhood-deployment-support-specification.md`.

Nothing in this plan authorizes:

- editing code, tests, defaults, dependencies, migrations, manifests, ABIs or CI;
- installing a tool or selecting a dependency;
- accessing a secret or production account;
- deploying, verifying, signing or broadcasting;
- approving a provider, address, role, Safe, parameter, confirmation count,
  finality policy, contract inventory or live version; or
- enabling Stock Token, PSM, SavingsGreen, Stability Pool or CCIP value paths.

Every proposed state-changing test requires fresh owner approval at the named
gate. A listed test is not evidence that the test exists or passed.

## 2. Validation principles

1. Start from a clean checkout at a full frozen commit.
2. Resolve and record dependency-security gates before deployment rehearsal.
3. Use one canonical Robinhood migration source for both profiles and isolated
   histories.
4. Reject unknown networks and chain-ID mismatch before account loading.
5. Build artifacts from declared inputs; never reuse an undeclared cache.
6. Treat plan/step IDs and semantic hashes—not transaction position—as
   progression identity.
7. Record complete immutable step evidence before current-manifest promotion.
8. Prove absence as aggressively as presence.
9. Use pinned clean forks for reproducible evidence; latest/dirty forks are
   local exploration only.
10. Treat receipt success, configured finality and post-state assertions as
    separate requirements.
11. Preserve Base behavior through explicit regression tests without preserving
    unsafe fallbacks.
12. Stop at every owner, security, external-action and production-value gate.
13. Bind temporary local governance explicitly to the nonzero deployment
    sender; reject final RipeHq governance, zero, and inferred role identities.

## 3. Prerequisite gate matrix

| Gate | Required evidence | Blocks |
| --- | --- | --- |
| V-00 source freeze | Full commit, clean tree, input hashes, canonical plan hash | Every stage |
| V-01 dependency security | Dated authoritative alerts, selected pin set, upstream release-note review, clean resolution, security approval | Any deployment/fork rehearsal |
| V-02 Track 6 S1/S2 | Integrated reviewed clock harness/inventory and exact dependency profile | Stages 2–5 |
| V-03 Track 6 S3–S10 | Integrated indispensable source/tooling artifacts or explicit unchanged/configuration/not-applicable dispositions for reservations `0010`–`0080`; S5 includes an approved RH action-block source and explicit no-Base-migration record | Clean graph execution |
| V-04 Track 8 | Reviewed minimum-containment specification/artifacts and owner-selected vault posture for launch-mandatory Stock Tokens | CM-021–026/030/043 and Stock Token lifecycle |
| V-05 Track 4 | Approved USDG reserve/feed/PSM parameter manifest and disabled/omitted decision | CM-046/048 |
| V-06 Track 1 | Supported CCIP release, toolchain, chain selectors, router/registry/pool/admin facts and owner decision | CM-051–053 and bridge tests |
| V-07 network operations | Provider, RPC policy, fee caps, confirmation/finality, account backend and public role addresses approved | Any nonlocal submission |
| V-08 release inventory | Approved component dispositions, external addresses, parameters, live-version policy and migration plan | Stages 4–5 |
| V-09 runbook approval | Reviewed deploy/abort/verification/handoff/incident runbooks and accountable operators | Stages 4–5 |
| V-10 legal/product/risk | Stock Token lifecycle, PSM and CCIP gates as applicable | Their value-path tests |

## 4. Evidence taxonomy

| Evidence class | Examples | Retention |
| --- | --- | --- |
| Committable immutable | Source/artifact hashes, sanitized step manifests, public receipts, assertion results, verification links/status, decision references | Hash-linked migration history/release bundle after review |
| Local controlled | Failure records, gas estimates, nonce/mempool state, provider timing, full fork snapshots, complete Safe proposal payload | Operator workspace with access controls and retention policy |
| Never stored | Secrets, credentialed RPC URLs, API keys, private keys, signatures, seed/hardware-wallet data, environment dumps | Prohibited |

Every case below names the expected committable evidence. Local diagnostics may
exist, but they do not replace the named artifact.

## 5. Stage 1 — static and unit validation

### 5.1 Objectives

Stage 1 proves:

- dependency alert and pin provenance;
- deliberate Track 6 S1 exact-version failure/reapproval when pins change;
- network-profile schema and unknown-network rejection;
- secret-safe environment handling;
- chain-ID mismatch rejection;
- deterministic migration discovery and duplicate failure;
- immutable plan hashing, semantic resume and explicit skip behavior;
- manifest schema, progression and atomic current-index generation;
- source/compiler/constructor/artifact hashes;
- verifier provider/language selection and rate policy;
- deterministic ABI identity/collision/stale-output handling;
- explicit excluded-integration dispositions; and
- Base-profile compatibility.

### 5.2 Proposed future test files

| Proposed file | Coverage / CM IDs | Prerequisite | Fixture / network | Expected evidence | Tier / owner |
| --- | --- | --- | --- | --- | --- |
| `tests/deployment/test_network_profiles.py` | Schema, canonical IDs, full-URL env references, RPC rate/quota policy, fee/finality/fork policy, per-run fork pin evidence and unknown profile; CM-055/059 | D-001/002/004/013 | Static profile fixtures, separate fork-evidence fixtures and mocked RPC identities; external network disabled | Unit report and schema fixtures | Fast / deployment-tooling owner |
| `tests/deployment/test_secret_handling.py` | Lazy env lookup, no test-key fallback, full RPC redaction, no env/manifest leakage; CM-055 | V-01 | Isolated process environments and fake sensitive URLs/keys; external network disabled | Captured sanitized logs and negative assertions | Fast / security owner |
| `tests/deployment/test_migration_discovery.py` | Numeric parsing, stable order, duplicate/gap/semantic-ID rejection, reservation ledger, and rejection of testnet-only canonical migrations; CM-055 | Namespace implementation | Disposable shared-source and isolated-history trees; no EVM/network | Unit report | Fast / deployment-tooling owner |
| `tests/deployment/test_execution_plan.py` | Plan hash, preconditions, explicit skips, irreversibility, idempotent satisfaction, source/profile drift rejection; CM-055 | D-009/014 | Synthetic plans, mocked receipts and typed state; no external network | Golden plan hashes and unit report | Fast / deployment-tooling + security |
| `tests/deployment/test_manifest_schema.py` | Every disposition, legitimate zero vs missing, hash chain, immutable steps, atomic current index; CM-056 | Schema implementation | Disposable filesystem with valid/invalid golden manifests | Schema fixtures and golden hashes | Fast / release-evidence owner |
| `tests/deployment/test_verifier_adapters.py` | Etherscan-v2/Blockscout selection, unsupported provider/language/form, timeout/rate/error states; CM-057 | Adapter implementation | Mocked HTTP/provider responses and virtual clock; external network disabled | Mocked request classifications | Fast / verifier owner |
| `tests/deployment/test_abi_export.py` | Clean build, Vyper/Solidity index input, deterministic paths, collisions, stale/missing output, compile failure; CM-057/058 | Artifact index interface | Disposable source/output trees and declared artifact-index fixtures | Golden inventory/hashes | Fast / compiler owners |
| `tests/deployment/test_robinhood_omissions.py` | Every component's omitted, deferred, blocked or disabled sub-surface, including Base-only CM-007/017–020/035–042/050/060, inactive scaffolds, Stock paths and CM-051–054/058 | Approved inventory | Synthetic RH graph/manifests and clean local EVM where state is needed | Negative graph/manifest fixtures and assertion report | Fast + Integration / protocol + deployment owners |
| `tests/deployment/test_registry_topology.py` | HQ IDs 1–22, Switchboard 1–5, Chainlink at PriceDesk ID 1, reserved PriceDesk semantics at IDs 2–5, VaultBook 1–4, and no shifted/reused IDs | Approved graph and Track 8 inputs | Synthetic registry plans plus clean local EVM | Registry-plan fixture and assertion report | Fast + Integration / protocol-oracle owners |
| `tests/deployment/test_base_profile_regression.py` | Base selection, history isolation, intended compatibility and rejection of known unsafe behavior | D-011 decision | Frozen Base profile/history fixtures; mocked provider; no external network | Base fixture diff | Fast / Base deployment owner |
| `tests/deployment/test_dependency_gate.py` | Alert snapshot, pin provenance, upstream release-note checklist, S1 exact-profile trip | V-01/S1 | Dated sanitized alert/metadata fixtures and clean resolver environment when approved | Sanitized gate report | Fast / security + Track 6 owner |

### 5.3 Target command interface

These commands are future interfaces, not currently runnable:

```bash
python -m pytest -q tests/deployment/test_network_profiles.py
python -m pytest -q tests/deployment/test_secret_handling.py
python -m pytest -q tests/deployment/test_migration_discovery.py
python -m pytest -q tests/deployment/test_execution_plan.py
python -m pytest -q tests/deployment/test_manifest_schema.py
python -m pytest -q tests/deployment/test_verifier_adapters.py
python -m pytest -q tests/deployment/test_abi_export.py
python -m pytest -q tests/deployment/test_robinhood_omissions.py
python -m pytest -q tests/deployment/test_registry_topology.py
python -m pytest -q tests/deployment/test_base_profile_regression.py
```

The implementation plan must also identify the repository's authoritative full
suite command after dependency review. Parallel test execution is not accepted
until shared-state isolation is proven.

### 5.4 Exit criteria

- all Stage 1 files exist and pass in a newly created clean environment;
- selected dependency versions and upstream behavior review are approved;
- Track 6 exact-version checks pass without weakening;
- no test accesses a secret or external network;
- every selected/disabled/omitted profile and component has a fixture; and
- Base regression explicitly distinguishes intended behavior from defects that
  must be removed.

## 6. Stage 2 — local clean deployment

### 6.1 Proposed future tests

| Proposed file | Coverage | Prerequisite | Fixture/network | Expected evidence | Tier / owner |
| --- | --- | --- | --- | --- | --- |
| `tests/deployment/test_clean_deployment.py` | Full `0010`–`0900` selected graph from empty state | V-00–V-05 and approved inventory | Deterministic local EVM; clean artifacts | Plan, immutable step chain, addresses/code/registry/assertion report | Integration / deployment owner |
| `tests/deployment/test_resume_reconciliation.py` | Failure before/after deployment, registration, capability and handoff boundaries | D-009 implementation | Fresh local EVM per case | Last valid step, local failure record, correct semantic resume/refusal | Integration / security owner |
| `tests/deployment/test_current_manifest_promotion.py` | Partial run never changes current index; terminal run promotes atomically | CM-056 implementation | Local filesystem/EVM | Prior/current hash evidence and fault-injection results | Integration / evidence owner |
| `tests/deployment/test_post_deployment_assertions.py` | Addresses, bytecode, constructors, registry, capabilities, flags, parameters, omissions | Approved graph/defaults | Local clean deployment | Complete assertion bundle | Integration / protocol owner |
| `tests/deployment/test_reproducible_artifacts.py` | Two builds from frozen commit produce identical source/input/ABI/bytecode hashes | V-01 and compiler interface | Two disposable clean environments | Artifact inventories and hash equality | Slow / compiler owners |
| `tests/deployment/test_network_clock_profiles.py` | Base ordinary plus Robinhood repeated, +1 and jump profiles | Integrated S1/S2 | Local EVM clock harness | S1/S2 coverage report | Integration / Track 6 owner |

### 6.2 Required local cases

- execute the same `migrations/robinhood/` source under both canonical profiles;
- prove history paths cannot cross-read or cross-write;
- prove faucet/funding and mock/test-token setup cannot enter the canonical
  migration source or histories;
- prove profile-specific approved values do not change migration step identity;
- deploy only canonical artifacts intended for Base/Robinhood;
- reject `DefaultsBase` and `DefaultsLocal` in a Robinhood plan;
- apply only the approved CM-049 parameter manifest;
- validate every RipeHq, Switchboard, PriceDesk and VaultBook ID;
- prove the exact PriceDesk sequence Chainlink ID 1, Curve ID 2, and
  BlueChipYield ID 3, followed by priority IDs `[1,3]`;
- prove priority sources 1 and 3 are checked before GREEN reaches Curve ID 2,
  GREEN composes through Curve plus Chainlink USDG, USDG has no Curve feed, and
  zero, stale, invalid, incompatible, reverting, recursive, or unsafe pricing
  fails closed;
- prove post-registration Curve pause/ID-2 disable and governed recovery keep
  BlueChipYield at ID 3 and preserve priority IDs `[1,3]`;
- prove AAPL remains Guarded-only, auction-only, Stability-excluded,
  stock-reward-disabled, absent from Defaults, and typed blocked on 12 of its
  16 canonical inputs;
- prove approved reward values are consumed while `B-REWARD-PROMOTION` and all
  checkpoint, identity, monitoring, response, operator, qualification,
  rehearsal, and release prerequisites remain open;
- prove pool deployment/funding is distinct from LP asset admission, both LP
  tokens remain absent, PSM reserves do not fund liquidity, and Uniswap remains
  PriceDesk-inert;
- prove optional mint capabilities remain withheld until the owning step;
- prove every unsupported integration has no address, registration, capability,
  route, approval or enabled flag;
- inject partial failures at every semantic action boundary;
- resume only under an identical plan/source/profile/prior-state hash;
- mechanically prove that only Switchboard, SwitchboardAlpha, SwitchboardBravo,
  SwitchboardCharlie, SwitchboardDelta, SwitchboardEcho, PriceDesk,
  ChainlinkPrices, CurvePrices, BlueChipYieldPrices, and VaultBook receive
  `binding:temporary-local-governance` in their production constructors;
- reject zero temporary governance, final RipeHq governance used as temporary
  governance, and a temporary binding different from the executor sender before
  any transaction;
- prove the deployment sender completes all required setup while RipeHq final
  governance remains unchanged and distinct;
- prove PriceDesk is registered at RipeHq ID 7 before the GREEN Curve feed is
  added, because production CurvePrices resolves PriceDesk through RipeHq;
- keep final `0900` relinquishment after every setup/assertion action, finalize
  all required action and registry timelocks, and reject any pending action;
- record and verify all 11 per-contract relinquishment receipts, zero local
  governance, removal of temporary power, and sole effective final RipeHq
  governance;
- fault before, during, and after the relinquishment loop; record the exact
  retained set, prohibit current promotion, and restore a fresh backend from
  immutable receipts so resume executes only remaining relinquishments;
- regenerate the current index and compare immutable inputs;
- reject dirty source, stale compiler output and mismatched chain identity; and
- rebuild twice and compare all declared artifact hashes.

### 6.3 Exit criteria

One completely clean deployment and every injected failure/resume case pass from
fresh state. No manual repair, positional skip, broad state-changing retry or
manifest edit is permitted.

## 7. Stage 3 — pinned fork or production-like rehearsal

### 7.1 Boundary

Stage 3 uses no production authority and submits nothing to the source RPC.
Forks require exact source chain ID and block. Latest/dirty forks may be used for
local exploration only and cannot satisfy this stage.

### 7.2 Proposed future tests

| Proposed file | Coverage | Prerequisite | Fixture/network | Expected evidence | Tier / owner |
| --- | --- | --- | --- | --- | --- |
| `tests/deployment/fork/test_profile_and_fees.py` | RPC identity, fee methods, gas estimates, receipt/finality model | V-07 without production account | Pinned Robinhood testnet/mainnet read-only fork | Sanitized profile/fee observation | Fork / operations |
| `tests/deployment/fork/test_forbidden_base_addresses.py` | No Base address in RH graph except explicit CCIP remote-mapping context | Approved inventory | Pinned fork plus derived Base manifest denylist | Context-aware negative report | Fork / security |
| `tests/deployment/fork/test_verifier_capabilities.py` | Live config endpoint, formats, compilers and effective rate policy | Instance facts | Public read-only explorer | Sanitized capability record | Fork / verifier owner |
| `tests/deployment/fork/test_role_handoff_rehearsal.py` | Safe/multisig proposal construction and deployer-authority loss without production authority | Approved mock backend | Local/pinned fork, submission disabled | Public proposal digest/assertion report | Fork / security |
| `tests/deployment/fork/test_abort_boundaries.py` | Every irreversible boundary and remediation path | Reviewed runbook | Fresh pinned fork per case | Abort/remediation evidence | Fork / deployment + security |
| `tests/deployment/fork/test_live_version_policy.py` | Base/RH artifact parity or approved bounded divergence | Component-level policy | Pinned Base and RH forks | Code-hash/version matrix | Fork / protocol owner |

The Base denylist is derived at test time from the frozen Base manifest. A Base
token/pool address may appear only as a typed CCIP remote-chain mapping after
Track 1 approval; it must never appear as a Robinhood-local contract, oracle,
reserve, vault, treasury destination or executable route.

### 7.3 Exit criteria

- selected provider facts and effective explorer limits are dated;
- exact pinned-block evidence is reproducible;
- gas/receipt/finality and verification behavior match the reviewed policies;
- the full artifact set rebuilds from the frozen commit;
- every irreversible boundary has a tested abort/remediation result; and
- no rehearsal uses production authority or writes to a public chain.

## 8. Stage 4 — Robinhood test environment

### 8.1 Fresh approval boundary

Stage 4 is state-changing and requires fresh owner approval, an approved
nonproduction signer, funded test account, selected provider, finality/fee
policies, runbooks and all applicable gates V-00–V-10. Nothing in this document
grants that approval.

### 8.2 Ordered validation

1. Freeze commit, plan, profiles, artifacts, graph, parameters, addresses and
   account capabilities.
2. Prove chain ID `46630` before loading the approved signer.
3. Deploy the complete selected graph through `0900`; `1000` remains absent
   unless Track 1 is closed and separately approved.
4. Verify receipts/finality and every postcondition before the next semantic
   action.
5. Verify every supported contract and record truthful unsupported states.
6. Configure one approved reserve. Configure the launch-mandatory Stock Token
   only after Track 8's minimum-containment, exact-token, security, risk, and
   owner gates close; otherwise the release is blocked rather than silently
   omitting the product requirement.
7. Exercise approved deposit, borrow, repay, withdraw, liquidation and bad-debt
   behavior; when a path is not approved, prove its flag/route remains disabled.
8. Execute one local-governance parameter change through its actual timelock and
   observe repeated/jumping EVM `NUMBER` cases.
9. Prove Base governance or cross-chain dispatch has no privileged local path.
10. Execute approved PSM behavior or prove mint/redeem/auto-deposit/yield remain
    disabled.
11. Execute CCIP bridge/reconciliation only after V-06 and a separate external
    action approval.
12. Reconcile manifests, verification, roles and GREEN/RIPE supply as applicable.
13. Keep the environment live for an owner-approved soak period and record
    onchain/public evidence without secrets.

### 8.3 Proposed future tests/runbooks

| Proposed file | Coverage | Prerequisite | Fixture / network | Expected evidence | Tier / owner |
| --- | --- | --- | --- | --- | --- |
| `tests/deployment/live/test_robinhood_testnet_deployment.py` | Full planned graph and manifest chain | V-00–V-09 and exact approved plan | Official RH testnet through approved provider/account; fresh state-changing authorization | Public receipts, immutable manifests, assertions | Live / deployment owner |
| `tests/deployment/live/test_robinhood_testnet_lifecycle.py` | Approved reserve/Stock lifecycle | V-04/V-08/V-10 and accepted deployment | Official RH testnet, exact approved assets/limits | State-transition and accounting report | Live / protocol-risk owner |
| `tests/deployment/live/test_robinhood_governance.py` | Timelock, role and no-Base-governance assertions | V-02/V-07/V-08 and approved roles | Official RH testnet/local governance and signer backend | Public governance receipts/events | Live / governance-security owner |
| `tests/deployment/live/test_robinhood_psm.py` | Approved PSM path or disabled invariants | V-05/V-10 and exact PSM disposition | Official RH testnet with approved reserve/feed, or disabled scaffold | Configuration/negative assertion report | Live / risk-oracle owner |
| `tests/deployment/live/test_robinhood_ccip.py` | Pools, remotes, limits, supply reconciliation | V-06/V-10 and separate external-action approval | Base Sepolia plus RH testnet through approved providers/accounts | CCIP public evidence and supply reconciliation | Live / Track 1-security owner |
| `docs/chains/rh/runbooks/robinhood-testnet-deployment.md` | Operator plan/abort/handoff/soak procedure | V-09 and exact candidate plan | Dry rehearsal first; official RH testnet only after fresh authorization | Reviewed signed-off runbook revision | Document + Live / operations owner |

All paths are proposed future paths.

### 8.4 Exit criteria

Every selected component is verified/asserted, every disabled/omitted component
passes negative assertions, role handoff is complete, the soak period passes,
and all open failures have owner dispositions. A successful core deployment does
not waive Stock Token, PSM, SavingsGreen or CCIP gates.

## 9. Stage 5 — mainnet rehearsal and restricted release

### 9.1 Rehearsal

Before any broadcast:

- freeze and sign off source, dependencies, graph, addresses, parameters, plan,
  artifacts, manifests and runbooks;
- re-query authoritative dependency alerts and all external/network facts;
- reproduce artifacts from two clean environments;
- rehearse the exact migration, verification, role-transfer, pause, abort and
  remediation runbooks without production authority;
- confirm balances, fee caps, replacement policy, confirmation/finality and
  explorer limits;
- require every launch gate and accountable owner signature; and
- generate the terminal planned release bundle with no unresolved required
  production field.

### 9.2 Restricted release

Restricted release requires a separate owner authorization naming the exact plan
hash and production account backend. It starts with small approved limits and
disabled value paths. After deployment:

1. wait for selected finality;
2. run complete configuration/role/bytecode/omission assertions;
3. verify contracts or record an owner-approved truthful unsupported state;
4. perform only owner-approved minimal smoke actions;
5. enable no Stock/PSM/Savings/CCIP path without its individual gate;
6. reconcile GREEN/RIPE supply after CCIP activation, if any; and
7. archive the final immutable manifest chain and release bundle.

### 9.3 Exit criteria

The final history is complete, hash-linked and reproducible; the current index
matches its immutable head; deployer authority is absent; limits/flags match the
approved restricted posture; every smoke action is reconciled; and owners accept
the release evidence.

## 10. Required negative-case matrix

Every row is a future named test. `Fast` uses mocks/local unit state,
`Integration` uses a clean local deployment, `Fork` is pinned/read-only, and
`Live` requires fresh owner authorization.

| Case ID / proposed test | Proposed file | Prerequisite and fixture | Expected evidence | Tier / owner |
| --- | --- | --- | --- | --- |
| NEG-001 unknown profile | `tests/deployment/test_network_profiles.py::test_unknown_profile_fails_closed` | Profile registry; arbitrary string | Error before env/account/provider access | Fast / tooling |
| NEG-002 mismatched chain ID | `tests/deployment/test_network_profiles.py::test_chain_id_mismatch_before_account_load` | Mock RPC returns wrong ID | No account load/sign; sanitized error | Fast / security |
| NEG-003 Base RPC/address leakage | `tests/deployment/fork/test_forbidden_base_addresses.py::test_no_local_base_address` | Frozen Base denylist and RH plan | Context-aware zero-hit report | Fork / security |
| NEG-004 missing RPC credential | `tests/deployment/test_secret_handling.py::test_missing_rpc_env_fails_lazily` | Selected live-capable profile, env absent | Relevant command fails; unrelated help/unit command works | Fast / tooling |
| NEG-005 missing explorer key/keyless policy | `tests/deployment/test_verifier_adapters.py::test_key_policy_is_explicit` | Mock adapter profiles | Keyed adapter fails safely; keyless adapter honors interval | Fast / verifier |
| NEG-006 explorer incompatibility | `tests/deployment/test_verifier_adapters.py::test_unsupported_provider_or_format` | Unsupported response/format | `provider_unsupported`, never success | Fast / verifier |
| NEG-007 stale external address | `tests/deployment/test_execution_plan.py::test_external_fact_changed_after_freeze` | Provenance timestamp/hash differs | Plan invalidated before signing | Fast / security |
| NEG-008 duplicate migration ID | `tests/deployment/test_migration_discovery.py::test_duplicate_numeric_id_rejected` | Two filenames share ID | Deterministic discovery failure | Fast / tooling |
| NEG-009 out-of-order/reused ID | `tests/deployment/test_migration_discovery.py::test_executed_id_cannot_be_inserted_or_reused` | Prior immutable history | Discovery/progression failure | Fast / tooling |
| NEG-010 partial deployment | `tests/deployment/test_resume_reconciliation.py::test_partial_deploy_keeps_prior_current_index` | Fault after contract creation | Orphan/failure local record; current unchanged | Integration / evidence |
| NEG-011 stale current manifest | `tests/deployment/test_current_manifest_promotion.py::test_incomplete_chain_cannot_promote` | Missing/failed step | Promotion rejected | Integration / evidence |
| NEG-012 wrong constructor value | `tests/deployment/test_execution_plan.py::test_constructor_drift_changes_plan` | Mutated typed argument | New plan hash; old approval invalid | Fast / security |
| NEG-013 wrong artifact/runtime hash | `tests/deployment/test_post_deployment_assertions.py::test_runtime_hash_mismatch` | Mutated artifact/address | Later steps blocked; failed assertion | Integration / compiler |
| NEG-014 unverified bytecode | `tests/deployment/test_verifier_adapters.py::test_unverified_is_not_success` | Provider returns failed/pending | Truthful manifest status and launch gate | Fast / verifier |
| NEG-015 deployer retains authority | `tests/deployment/fork/test_role_handoff_rehearsal.py::test_deployer_authority_absent` | Completed mock handoff | Complete role diff; failure blocks release | Fork / security |
| NEG-016 omitted integration deployed | `tests/deployment/test_robinhood_omissions.py::test_omitted_component_has_no_surface` | Inject forbidden address/row/route | Negative assertion failure | Fast / protocol |
| NEG-017 zero-address call path | `tests/deployment/test_robinhood_omissions.py::test_zero_is_not_placeholder` | Missing required value or zero target | Plan refuses execution | Fast / security |
| NEG-018 PSM mint enabled | `tests/deployment/test_robinhood_omissions.py::test_psm_mint_disabled` | CM-048 scaffold | `canMint=false`; no HQ mint capability | Integration / risk |
| NEG-019 PSM redeem enabled | `tests/deployment/test_robinhood_omissions.py::test_psm_redeem_disabled` | CM-048 scaffold | `canRedeem=false` | Integration / risk |
| NEG-020 PSM auto-deposit/yield enabled | `tests/deployment/test_robinhood_omissions.py::test_psm_no_auto_deposit_or_yield` | CM-048 scaffold | false plus `(0, zero address)` | Integration / risk |
| NEG-021 Stock collateral premature | `tests/deployment/test_robinhood_omissions.py::test_stock_asset_not_enabled_before_track8` | Track 8 gate absent | No asset/vault/borrow route | Integration / risk |
| NEG-022 CreditRedeem premature | `tests/deployment/test_robinhood_omissions.py::test_stock_credit_redeem_false` | Candidate Stock config | `canRedeemCollateral=false` | Integration / risk |
| NEG-023 Stability Pool Stock swap | `tests/deployment/test_robinhood_omissions.py::test_stock_stability_swap_false` | Candidate Stock config | `shouldSwapInStabPools=false` | Integration / risk |
| NEG-024 unsupported price source | `tests/deployment/test_robinhood_omissions.py::test_unsupported_oracle_unreachable` | CM-017–020/039–041/050 absent | No registry/source route; base-rate fallback where specified | Integration / oracle |
| NEG-025 CCIP capability premature | `tests/deployment/test_robinhood_omissions.py::test_ccip_capability_withheld_until_complete` | CM-051–053 incomplete | No pool HQ capability | Integration / Track 1 |
| NEG-026 bad CCIP remote/token/pool | `tests/deployment/live/test_robinhood_ccip.py::test_remote_mapping_exact` | V-06 and approved test deployment | Mapping/selectors/code hashes and blocked mismatch | Live / Track 1/security |
| NEG-027 unapproved live-version drift | `tests/deployment/fork/test_live_version_policy.py::test_unapproved_drift_fails` | Base/RH code hashes | Policy failure | Fork / protocol |
| NEG-028 S1/S2 omitted | `tests/deployment/test_dependency_gate.py::test_integrated_s1_s2_required` | Missing gate result | Release gate fails | Fast / Track 6 |
| NEG-029 broad state retry | `tests/deployment/test_execution_plan.py::test_ambiguous_submission_requires_review` | Timeout after mocked submission | No duplicate retry; blocked state | Fast / security |
| NEG-030 positional resume | `tests/deployment/test_execution_plan.py::test_transaction_position_is_not_resume_identity` | Changed step source with same call count | Resume rejected | Fast / tooling |
| NEG-031 registry ID shift | `tests/deployment/test_registry_topology.py::test_hardcoded_ids_cannot_shift` | Omit an early HQ/VaultBook row | Plan failure before submission | Fast / protocol |
| NEG-032 cross-history write | `tests/deployment/test_network_profiles.py::test_profiles_cannot_share_history` | Test profile points to mainnet history | Schema/plan failure | Fast / evidence |
| NEG-033 Savings path premature | `tests/deployment/test_robinhood_omissions.py::test_savings_path_stays_inert_without_approval` | CM-003 scaffold, DR-007 open | No deposits/rewards/insurance/Stability route or capability | Integration / product-risk |
| NEG-034 inactive HR path enabled | `tests/deployment/test_robinhood_omissions.py::test_hr_scaffold_has_no_contributors_or_rewards` | CM-005/032 inactive scaffolds | No contributor instance, vesting, RIPE mint capability or payout | Integration / protocol |
| NEG-035 bond/reward path premature | `tests/deployment/test_robinhood_omissions.py::test_bond_and_reward_paths_stay_disabled` | CM-028/029/033/038, terms/tokenomics open | No Boardroom/bond/Lootbox reward enablement or RIPE mint capability | Integration / tokenomics-risk |
| NEG-036 disabled registry scaffold gains authority | `tests/deployment/test_robinhood_omissions.py::test_slot_scaffolds_have_exact_disabled_capabilities` | CM-003/029/032/033/043/046/048 | Exact registry IDs preserved while all unapproved flags/capabilities/routes remain absent | Integration / security |
| NEG-037 PriceDesk semantic slot reuse | `tests/deployment/test_registry_topology.py::test_pricedesk_reserved_ids_cannot_be_repurposed` | Chainlink at ID 1; attempt to add a non-Curve source next or to add Pyth/Stork without preserving earlier slots | Plan/registration rejected before submission; IDs 2–5 remain empty or contain only their canonical source identities | Fast + Integration / protocol-oracle owners |
| NEG-038 invalid temporary local governance | `tests/deployment/test_resume_reconciliation.py::test_zero_temporary_governance_is_rejected_before_execution` and `::test_final_governance_cannot_be_used_as_temporary_governance` | Zero or final DP-18 governance bound as temporary governance | Plan rejected before execution; no transaction receipt | Fast / deployment-security owners |
| NEG-039 deployment-sender mismatch | `tests/deployment/test_resume_reconciliation.py::test_temporary_governance_must_equal_executor_sender` | Distinct temporary binding does not equal backend deployment sender | Executor preflight rejection with empty backend sequence | Fast / deployment-security owners |
| NEG-040 partial authority relinquishment | `tests/deployment/test_resume_reconciliation.py::test_partial_relinquishment_history_resumes_only_remaining_contracts` | Failure before first, after an interior, or after final relinquishment | Exact per-contract receipts and retained set; no current promotion; fresh bound resume mutates only remaining contracts | Integration / evidence-security owners |
| NEG-041 premature final handoff | `tests/deployment/test_resume_reconciliation.py::test_final_handoff_refuses_incomplete_required_assertion` | Required setup/assertion action incomplete | Final handoff absent from backend sequence; no relinquishment or promotion | Integration / deployment-security owners |

## 11. Approved-path lifecycle matrices

These cases remain blocked until their owner gates close.

### 11.1 Core protocol lifecycle

| Scenario | Required assertion |
| --- | --- |
| Deposit | Requested/received/credited values and vault custody reconcile under the Track 8-approved artifact |
| Borrow | Price, collateral, debt and GREEN mint receipt reconcile; no unsupported source/route contributes |
| Repay | GREEN movement and debt reduction are atomic |
| Withdraw | Delivered asset and accounting reconcile; cooldown/clock profile is correct |
| Liquidation | Eligibility, auction state, payment, debt and collateral delivery are atomic |
| Bad debt | Liability transitions exactly once under the approved Track 8 design |

### 11.2 Governance lifecycle

- propose, wait and execute one parameter change;
- prove early execution fails;
- prove repeated and jumping numbers follow the approved Track 6 semantics;
- prove unauthorized caller, wrong chain/profile and stale proposal fail;
- prove final roles and deployer-authority loss.

### 11.3 PSM lifecycle

Default case proves disabled mint/redeem/auto-deposit/yield. Enabled lifecycle is
specified only after Track 4 approval and must cover caps, fees, interval reset,
reserve accounting, price/feed failure, governance disable and no unsupported
route.

### 11.4 CCIP lifecycle

Only after Track 1 approval:

- exact Base/RH token, pool, router and selector mappings;
- pool direct mint capability and no extra mint-adapter trust boundary;
- burn/mint supply reconciliation in both directions;
- rate limits, remote disable, RMN/pause and failed-message behavior;
- role transfer and emergency controls; and
- total GREEN/RIPE cross-chain reconciliation.

## 12. Diagnostics and failure reporting

Every failed case reports:

- stable case/step/assertion ID;
- profile and expected/observed chain ID;
- source, plan, dependency and artifact hashes;
- last immutable manifest hash;
- public transaction/receipt identifiers if any;
- expected versus observed typed state with secrets redacted;
- whether the state is pre-submission, ambiguous submission, finalized failure,
  governance-remediable or irreversible;
- safe next action and required approver; and
- local versus committable evidence disposition.

Tests must not dump environment variables, credentialed URLs, signatures, full
provider bodies or wallet transcripts.

## 13. CI and execution tiers

The starting commit has no `.github/workflows/`. No CI change is authorized in
this specification track.

| Tier | Intended trigger | Network/state |
| --- | --- | --- |
| Fast | Every implementation PR | No external network; mocked providers |
| Integration | Every implementation PR after deterministic isolation | Fresh local EVM/filesystem |
| Slow/reproducibility | Merge gate/nightly as approved | Two clean build environments |
| Fork | Manual protected job | Pinned read-only source, submission disabled |
| Testnet live | Owner-approved release candidate | State-changing nonproduction |
| Mainnet rehearsal | Owner-approved release gate | No production submission |
| Restricted release | Exact-plan owner authorization | Production |

Future CI must use environment references/scoped secrets, redact logs, forbid
fork/live jobs on untrusted changes and require protected approval. CI design is
a separate implementation slice.

## 14. Final validation checklist

- [ ] Every prerequisite gate has an owner, artifact and status.
- [ ] Every selected CM row maps to a stage and assertion.
- [ ] Every omitted/disabled/deferred CM row maps to a negative test.
- [ ] Reservations `0010`–`1000` have duplicate/order/progression tests.
- [ ] Every required negative case has a proposed file, prerequisite, fixture,
  evidence, tier and owner.
- [ ] Base behavior and known defects are separately dispositioned.
- [ ] Track 6 exact-version and clock gates are not weakened.
- [ ] Track 8 and Stock Token tests remain blocked until the exact minimum
  containment artifact and activation gates close; Stock Token omission is not
  treated as a passing initial-launch result.
- [ ] PSM/SavingsGreen/CCIP tests remain blocked until their individual gates.
- [ ] No test logs or persists secrets.
- [ ] Current manifest cannot promote from a failed or partial plan.
- [ ] Rebuilds reproduce all declared hashes.
- [ ] Testnet soak and mainnet release require separate owner approval.
- [ ] No future path is described as already implemented.

## 15. Clean-checkout and reproducibility procedure

This procedure is future validation, not a command authorization:

1. Name the full frozen source commit, reviewed dependency profile, canonical
   network profile, parameter/inventory manifest and semantic plan hash.
2. Create two independent disposable checkouts at that exact commit. Confirm
   `git rev-parse HEAD` equality and an empty `git status --porcelain` in each.
3. Recompute the Track 7 input hashes and fail if any frozen input differs.
4. Build two clean environments using the H-01-approved dependency command.
   Never inherit a repository virtualenv, compiler cache, ABI directory,
   dotenv file or provider environment.
5. Run Stage 1 in each checkout with external networking disabled. Compare test
   collection and pass/skip results.
6. Compile to new temporary output roots and export canonical source/compiler
   input/ABI/creation/runtime inventories. Compare every declared hash and
   reject extra, missing, stale or colliding outputs.
7. Run Stage 2 from an empty local EVM and empty temporary history. Compare
   canonical plans, immutable step chains and terminal current indexes, allowing
   only explicitly normalized ephemeral fields.
8. Run the Base profile regression and Track 6 ordinary/repeated/+1/jump clock
   profiles in both checkouts.
9. If Stage 3 is authorized, use the same source chain ID and exact pinned block
   in both checkouts; do not let a latest-block fork satisfy reproducibility.
10. Produce a sanitized comparison report with source/dependency/plan/artifact/
    assertion hashes. Review it before any testnet plan can be frozen.
11. Destroy disposable local environments through the owner-approved cleanup
    process. Never remove a worktree, history or evidence path by an unresolved
    variable or broad recursive target.

Reproduction fails on a dirty tree, different dependency resolution, undeclared
network use, mismatched artifact/plan hash, nondeterministic generated output,
manual manifest repair or a current index that cannot be regenerated solely
from its immutable chain.

## 16. Follow-on slice command map

All paths and commands are future interfaces. A row is runnable only after its
slice creates the named paths and closes its prerequisite gates.

| Slice | Expected targeted validation | Required broader validation |
| --- | --- | --- |
| H-01 | `python -m pytest -q tests/deployment/test_dependency_gate.py`; approved resolver/audit and release-note review | Track 6 S1 exact profile; `python -m pytest -q` |
| H-02 | `python -m pytest -q tests/deployment/test_network_profiles.py tests/deployment/test_secret_handling.py tests/deployment/test_base_profile_regression.py`; CLI help/import with env absent | Stage 1 subset; full suite |
| H-03 | `python -m pytest -q tests/deployment/test_robinhood_blueprint.py tests/deployment/test_robinhood_omissions.py`; prove H-03 registry-slot expectations in those owned tests | Base profile regression; full suite. `tests/deployment/test_registry_topology.py` remains H-08-owned and is run only after H-08 creates it |
| H-04 | `python -m pytest -q tests/config/test_defaults_robinhood.py tests/deployment/test_network_clock_profiles.py`; deterministic generator comparison | Track 6 S1/S2 and Base defaults regression; full suite |
| H-05 | `python -m pytest -q tests/deployment/test_migration_discovery.py tests/deployment/test_execution_plan.py tests/deployment/test_robinhood_migration_source.py`; dry plan for both RH profiles | Base runner/history regression; one complete serial suite on final bytes |
| H-06 | `python -m pytest -q tests/deployment/test_manifest_schema.py tests/deployment/test_current_manifest_promotion.py`; parse all historical JSON | Base history read compatibility; full suite |
| H-07 | `python -m pytest -q tests/deployment/test_verifier_adapters.py tests/deployment/test_abi_export.py`; two clean artifact builds | Base verifier/ABI consumer regression; full suite |
| H-08 | `python -m pytest -q tests/deployment/test_post_deployment_assertions.py tests/deployment/test_registry_topology.py tests/deployment/test_robinhood_omissions.py` | Golden Base/RH checker fixtures; full suite |
| H-09 | All Stage 1/2 and NEG-001–037 cases; two-checkout reproduction | Base full suite, Track 6 profiles and serial `python -m pytest -q` |
| H-10 | Stage 4 dry plan and exact plan/hash review; live command intentionally withheld until fresh authorization | Re-run Stages 1–3; post-run evidence/soak review if authorized |
| H-11 | Stage 5 rebuild, rehearsal and preflight; production command intentionally absent | Re-run Stages 1–4 and every selected launch gate |
| H-12 | Pinned Chainlink/Solidity build plus source/storage/method delta checks, inherited ABI/behavior tests, `test_ccip_artifact_index.py`, destination-gas measurement, verifier/ABI and two-chain tests | Exact-hash reference-review record plus production-package independent review/audit; full Solidity/Vyper/Base/RH suites; and cross-chain supply reconciliation |

Parallel execution remains prohibited until H-09 proves fixture, EVM, compiler
cache and filesystem isolation. A command returning zero is insufficient if
required evidence, negative assertions or selected gates are missing.

## 17. Launch-gate and checklist mapping

| Technical launch requirement | Validation evidence | Earliest satisfying stage / blocking gate |
| --- | --- | --- |
| Frozen commit, dependencies, inventory and parameter/address manifests | V-00/V-01 hashes, DR closure, two-checkout comparison | Stage 5; H-01 and V-08 |
| One canonical source; no Robinhood-only protocol branch | Component/source inventory and bytecode policy matrix | Stage 1/3; Track 6/8/1 shared-source review |
| Every block-number dependency tested on Base and RH semantics | Track 6 S1/S2 reports plus `tests/deployment/test_network_clock_profiles.py` | Stage 2; V-02/V-03 |
| Clean-checkout deployment and verification tooling | Sections 15/16 evidence, complete local manifest chain | Stage 2 then provider rehearsal Stage 3 |
| Minimal GREEN/RIPE pool permission and production registration | Exact artifact/role/remotes, negative capabilities and receipts | Stage 4/5; V-06 plus separate Base/RH action approvals |
| Bidirectional bridge and total-supply reconciliation | Source burn, in-flight, destination mint and aggregate supply report | Stage 4/5; CCIP activation gate |
| Robinhood mint → CCIP → Base PSM propagation | Bounded test amounts, message evidence, supply and PSM reserve reconciliation | Stage 4/5; Track 1/4 and risk approval |
| USDG/PSM valid or verifiably disabled | NEG-018–020, oracle/reserve/flag assertions and any approved lifecycle | Stage 2 disabled; Stage 4 enabled only after V-05/V-10 |
| Savings/Stability/insurance posture selected and tested | NEG-033/036 or complete owner-approved lifecycle | Stage 2 disabled; Stage 4 active only after DR-007 |
| Launch-mandatory Stock Token mapping/minimum-containment/risk posture selected and tested | NEG-021–023, Track 8 artifact tests and approved lifecycle; omission fails the initial-launch gate | Stage 4; V-04/V-10 |
| Unsupported Base integrations unreachable | NEG-003/016/017/024 and complete omission manifest | Stage 2, confirmed Stage 3 |
| Full-stack testnet/adversarial/Base regression/rehearsal | Stage exit records, soak report and full-suite evidence | Stage 4 plus Stage 5 rehearsal |
| Every live-version difference approved | Pinned code-hash matrix, policy classification and convergence evidence | Stage 3; DR-006/016 |
| Exact deployed code, roles, registries, flags and parameters match manifests | H-08 complete assertion bundle and immutable/current manifest equality | Stage 4 then Stage 5 |

### 17.1 Smoke and supply-reconciliation plan

Smoke actions are disabled by default and individually owner-approved. The
smallest approved sequence starts only after deployment assertions and role
handoff:

1. perform one bounded deposit, borrow and full repay/withdraw path for an
   approved reserve;
2. perform no Stock Token smoke until Track 8 and exact-token gates close, but
   block initial launch if the approved Stock Token lifecycle cannot then run;
3. perform a PSM mint/redeem only if Track 4 activation is approved; otherwise
   rerun disabled invariants;
4. perform one bounded liquidation/bad-debt path in the test environment;
5. bridge GREEN and RIPE in each direction only after both pools, remotes,
   capabilities and rate limits are approved; and
6. reconcile per-chain token supply, source burns, destination mints, in-flight
   messages, failed/manual executions and PSM reserve effects before and after
   each bridge action.

Any unexplained supply delta, duplicate message effect, enabled omitted route,
or mismatch between action receipt and manifest blocks the next action and
requires Track 1/security/risk review. Mainnet smoke uses separately approved
smaller limits and never inherits testnet authorization.
