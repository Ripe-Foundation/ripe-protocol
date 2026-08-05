# RH hardening and release-support pass report

This report closes the locally authorized implementation pass against the
frozen `rh` baseline. It does not authorize a deployment, integration,
activation, release, monitoring rollout, or owner-gated decision.

The post-H-05 reconciliation amendment at the end of this report supersedes
all earlier current-state, count, baseline, aggregate-failure, and G1-decision
claims while preserving them as historical hardening-tip provenance.

The locally authorized implementation and reviewer-remediation work is
complete. A reviewer found that the original matrix named four support files
that the implementation did not need because the tests use functionally
complete embedded ephemeral doubles. Owner direction to address all reviewer
feedback authorized reconciling the matrix to the implemented design. The
same review also found cadence metadata hidden from the block-clock scanner;
the literal metadata is restored and explicitly inventoried below. Neither
remediation changes production contracts, interfaces, ABIs, or migrations.

## Historical hardening baseline echo

The controlling Phase 0 record is
[`BASELINE.md`](./BASELINE.md). Its required baseline contents are echoed here.
This table records the original hardening branch and is not the current
post-H-05 candidate baseline.

| Field | Captured value |
| --- | --- |
| Baseline commit | `a86650b187c523f27c92f05bfe959d06840025a6` |
| Reviewed implementation snapshot | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Branch | `rh-hardening` |
| Worktree | `/Users/wigglez/dev/ripe-protocol-rh-hardening` |
| Source branch captured once | `rh` |
| Interpreter | `/private/tmp/ripe-rh-final-gate2.uZCfBL/venv/bin/python` |
| Exact requirement pins | `90` |
| Requirement deviations | `0` |
| Vyper | `0.4.3+commit.bff19ea2` |
| Canonical environment manifest SHA-256 | `f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d` |

The initial main-worktree `git status --porcelain` capture was empty:

```text
```

The exact-lock verification printed `pins=90 deviations=0`. The canonical
manifest was the sorted, LF-terminated `importlib.metadata` listing recorded in
`BASELINE.md`; its SHA-256 was
`f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d`.
The compiler printed `0.4.3+commit.bff19ea2`.

The five frozen production-source identities were:

| Contract source | SHA-256 |
| --- | --- |
| `contracts/core/Teller.vy` | `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909` |
| `contracts/vaults/GuardedErc20.vy` | `0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed` |
| `contracts/core/CreditEngine.vy` | `7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d` |
| `contracts/data/Ledger.vy` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |

The record-stated committed ABI identities also matched:

| ABI | SHA-256 |
| --- | --- |
| `scripts/abis/GuardedErc20.json` | `1477d537e71863a7da8c727791cdbf3e745cc31b81889a00615296148d9dafb0` |
| `scripts/abis/Ledger.json` | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |
| `scripts/abis/Lootbox.json` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` |

The reviewed-snapshot-to-baseline `git log` and `git diff` inventories were
empty for all targeted Teller, GuardedErc20, comparison, CreditEngine, Ledger,
Lootbox, mock, and testing paths. There was no test/mock drift at baseline.

The compiler-settings line in `BASELINE.md` echoed the original prompt's
global `optimize=codesize` wording. Owner direction subsequently corrected
that prompt defect. The canonical rule used by S1 is source-governed:

- Teller, CreditEngine, and Lootbox contain `# pragma optimize codesize`;
- GuardedErc20 and Ledger contain no optimization pragma and use Vyper's
  default `gas` mode;
- compilation runs from the repository root as
  `vyper -p . -f bytecode,bytecode_runtime <file>` with no `-O` override;
- transitive input identity is `vyper -p . -f integrity <file>`;
- artifact SHA-256 strips `0x`, hex-decodes, and hashes raw bytes.

## Final recommendation traceability

The Phase 0 dispositions did not expand. The complete final traceability below
groups every record bullet by its controlling disposition.

### Teller

| Disposition | Record bullets |
| --- | --- |
| `live-gated` | Bind the deployed artifact to reviewed source/compiler; qualify each exact token implementation/configuration; complete deployment/configuration readback, monitoring, and owner release decision. |
| `T1`–`T7` | Recheck size, ABI/selectors/events/constructor and persistent/transient layout (`T6`); review supported vaults and composed routes (`T2`); mutex-sensitive authorized callback regression (`T1`); exercise adversarial callback mode 5 (`T2`); prove transient rollback (`T3`); add offsetting canonical-balance lie (`T4`); add post-clear liveness and name/remove opaque modes (`T5`); retain EIP-170/24,152-byte gates (`T6`); state exact-transfer and truthful-balance assumptions (`T7`). |
| `parked` | Separate Deleverage branch/PR; CCIP workflows; zero-backing settlement/loss allocation/bad debt. |
| `prohibited` | Typed `balanceOf` replacement; clearing/removing the dedicated mutex before `V == Q`; persistent mutex/checkpoint replacement; removing vault-result equality; accepting and crediting `R != Q`; vault-pull or prepare/finalize custody architecture; `C2` or per-asset mutex without its trigger; whitespace-only Teller changes. |

### GuardedErc20

| Disposition | Record bullets |
| --- | --- |
| `live-gated` | Bind exact artifact/constructor/VaultBook slot/asset/configuration; qualify the production token and control/liveness behavior; prove enabled Teller plus Guarded composition; preserve the one-AAPL guarded initial assignment without guessing. |
| `conditional` | Revalidate the exact configured Teller/AuctionHouse/CreditEngine/Guarded routes. |
| `G1`–`G6` | Guard-by-guard mutation evidence (`G1`); inherited recovery-path tests (`G2`); locked compiler artifact/test/inventory automation (`G3`); frozen consumer inventory and consumer-path proof (`G4`); monitoring and incident runbook (`G5`); SimpleErc20 unsuitable-by-default caveat (`G6`). |
| `parked` | Deficient settlement/auction completion; user/protocol/issuer loss allocation; surplus ownership/recapitalization allocation; bad-debt recognition/forgiveness/exactly-once accounting; permanent-versus-temporary backing-loss policy; automatic Base migration; CCIP; separate Deleverage branch/PR. |
| `prohibited` | Production GuardedErc20 change; global BasicVault change; replacing SimpleErc20 under the same name; mutable guarded mode; SharesVault without selected economics; weakening exact returndata/delivery; token-call gas caps; shared-module deduplication refactor; describing containment as settlement/bad-debt resolution. |

### CreditEngine

| Disposition | Record bullets |
| --- | --- |
| `C1`–`C4` | Exact release/artifact/compiler/runtime/configuration binding (`C3`); focused max-withdrawable regression (`C1`); marginal gas measurement (`C2`); change-triggered artifact/test automation without invented CI (`C3`); retain zero-skip and zero-price mutation detection (`C4`). |
| `conditional` | Rerun focused/composed tests at a future release snapshot. |
| `live-gated` | Prove enabled-vault `(empty,0)` versus `(asset,0)` posture. |
| `D2` | Monitor backing failures, deficits, health changes, liquidation, auctions, and settlement; document each transition separately. |
| `parked` | Cross-asset `lowestLtv`; post-loss interest; grace/recapitalization/settlement/restoration/loss/bad debt; Deleverage; CCIP. |
| `prohibited` | Restore `amount == 0` skip; price a zero amount; add a custody reader; revert debt-health evaluation solely for unsafe/unknown backing; present parked policy as planned work; blank-line restoration; describe integration as deployment/activation/settlement resolution. |

### Ledger

| Disposition | Record bullets |
| --- | --- |
| `R1`, `R2` | Executable exact-`0x64` Robinhood profile (`R1`); reproducible local deployment bundle (`R2`). |
| `D3`, `D5`, `D6` | Native/historical replay policy (`D5`); monitoring and incident response (`D3`); `lastTouch` consumer semantics (`D6`). |
| `live-gated` | Real-network Nitro/ArbSys/topology qualification. |
| `L1`–`L6` | Trusted deposit non-arming/rollback (`L1`); dual `_mc` selectors (`L2`); source/profile mutations (`L3a`/`L3b`); source/artifact/layout/runtime checks (`L4`); snapshot-labeled counts (`L5`); monitoring thresholds/topology (`L6`). |
| `parked` | Deleverage; CCIP; zero-backing settlement/loss/bad debt. |
| `prohibited` | Generic-only Ledger refactor; `LedgerRh.vy`; mutable/arbitrary provider or selector; native fallback; `chain.id` dispatch; disabling equality guard; monotonicity enforcement without separate policy; editing historical Base migrations; Base migration for bytecode parity; removing `_mc`. |

### Lootbox

| Disposition | Record bullets |
| --- | --- |
| `R5`, `X1`–`X5` | Pin source/ABI/compiler/creation hash and ordered constructor manifest and encode RH floor `7_200`/interval zero (`R5`); future manifest/construction and historical incompatibility tests (`X1`); initially-disabled/later-enabled boundary (`X2`); max-minus-one/overflow coverage with separate cap decision (`X3`); EVM-number/wall-time monitoring (`X4`); snapshot-specific release counts (`X5`). |
| `live-gated` | Deployed getter/state/runtime/registry/capabilities; RH EVM-number/cadence revalidation; rewards/routes/minting gates. |
| `conditional` | Base convergence forward migration and operational plan. |
| `parked` | Deleverage, CCIP, zero-backing settlement/loss/bad debt. |
| `prohibited` | Rewrite historical Base migrations; `chain.id` branching or RH-only Lootbox; mutable floor; replay old call sites against current source; infer live address/signer/role/reward/runtime; treat source/tests as lifecycle approval; claim absent H-04/H-06/M4 integration. |

## Final approved path matrix

The matrix below includes the owner-authorized reviewer reconciliation.
“Changed” is the post-remediation observation before this report's final
commit.

| Work item | Exact approved path(s) | Pre-report observation |
| --- | --- | --- |
| Phase 0 | `docs/chains/rh/hardening/BASELINE.md` | changed |
| S1, T6, G3, C3, L4 | `scripts/check_contract_artifacts.py`; `config/contract-artifact-expectations.json`; `tests/inventory/test_contract_artifacts.py` | all changed |
| S2, S3 | `docs/chains/rh/hardening/mutation-evidence-protocol.md` | changed |
| T1, T2, T4, T5 | `tests/core/teller/test_teller_deposit.py` | changed |
| T3 | `tests/core/teller/test_teller_deposit.py` | changed; rollback probe is an embedded ephemeral double |
| T7, G6, D1 | `docs/chains/rh/hardening/asset-admission-assumptions.md` | changed |
| G1, G2 | `tests/vaults/test_guarded_erc20.py` | changed |
| G4 | `docs/chains/rh/hardening/guarded-consumer-inventory.md`; `tests/vaults/test_guarded_consumer_inventory.py` | both changed |
| G5, D2 | `docs/chains/rh/hardening/stock-backing-monitoring-runbook.md` | changed |
| C1, C2 | `tests/core/creditEngine/test_stock_backing.py`; `docs/chains/rh/hardening/creditengine-gas-measurements.md` | both changed |
| C4 | `docs/chains/rh/hardening/hardening-pass-report.md` | pending until this report commit |
| R1 | `scripts/proposals/__init__.py`; `scripts/proposals/ledger_robinhood_profile.py`; `scripts/proposals/ledger-robinhood-profile.json`; `tests/deployment_profiles/test_ledger_robinhood_profile.py` | all changed; profile doubles are embedded and complete |
| R2 | `scripts/proposals/build_ledger_artifact_bundle.py`; `tests/deployment_profiles/test_ledger_artifact_bundle.py`; `docs/chains/rh/hardening/ledger-local-artifact-bundle.json` | all changed |
| L1 | `tests/core/teller/test_teller_action_block.py` | changed |
| L2, L3a | `tests/data/test_ledger_action_block.py` | changed |
| L3b | `tests/deployment_profiles/test_ledger_robinhood_profile.py` | changed |
| L5 | `docs/chains/rh/hardening/release-packet-evidence-checklist.md`; `docs/chains/rh/hardening/hardening-pass-report.md` | checklist changed; report pending |
| L6, D3 | `docs/chains/rh/hardening/ledger-monitoring-runbook.md` | changed |
| R5 | `scripts/proposals/lootbox_deployment_profiles.py`; `scripts/proposals/lootbox-deployment-profiles.json`; `tests/deployment_profiles/test_lootbox_deployment_profiles.py` | all changed; profile double is embedded and complete |
| X1 | `tests/deployment_profiles/test_lootbox_deployment_profiles.py` | changed |
| X2, X3 | `tests/core/lootbox/test_underscore_rewards.py` | changed |
| X4, D4 | `docs/chains/rh/hardening/lootbox-distribution-monitoring.md` | changed |
| X5, D7 | `docs/chains/rh/hardening/release-packet-evidence-checklist.md` | changed |
| D5 | `docs/chains/rh/hardening/ledger-replay-policy.md` | changed |
| D6 | `docs/chains/rh/hardening/last-touch-consumer-semantics.md` | changed |
| Reviewer remediation | `config/block-clock-inventory.json`; `scripts/check_block_clock_inventory.py`; `tests/inventory/test_block_clock_inventory.py` | all changed |
| Phase 9 | `docs/chains/rh/hardening/hardening-pass-report.md` | pending until this report commit |

The original matrix's four unused file paths were removed only after the
reviewer confirmed the embedded doubles were functionally complete and the
owner directed that all feedback be fixed. The reviewer-remediation row
records the smallest required ceiling expansion. Artifact and profile cadence
names are now literal and have explicit `config` or `tooling`
classifications; no production clock classification changed.

## Deliverable status

“Done” means the locally authorized artifact or test exists and its focused
validation passed. It never means live approval or integration. A matrix
inverse-delta or unmet mutation criterion is explicitly partial.

| Item | Status | Implementing commit | Evidence or residual |
| --- | --- | --- | --- |
| S1 | done | `dbe03ea`, `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` | Central parameterized checker, frozen expectations, direct test, independent ABI/layout expectation negatives, tampered-source negative, and pragma-conflict negative. |
| S2 | done within the approved evidence model | `dbe03ea`, `e418c05`, `995b596`, `a22fea8`, `16855fb`; this report commit | All accepted source-mutant claims have descriptions/digests and same-run baselines. The G1 post-solvency deletion is algebraically equivalent and therefore makes no S2-sensitive claim; the owner approved retaining that assertion as defense-in-depth. |
| S3 | done | `dbe03ea`, `db6149a`, `f4329499fe1139f3e8936ac5e09d80cfdd40bb59`; this report commit | Profile gates reject every named mutant, assert the intended two-field mutation, and pin each complete manifest/source digest in the test module and below. |
| T1 | done | `e418c05` | Mutex-sensitive trusted callback plus S2 mutant. |
| T2 | done | `e418c05` | Mode-5 callback held through receipt equality. |
| T3 | done | `e418c05`, matrix reconciliation in `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` | Same-transaction rollback/retry passes with a functionally complete embedded disposable caller. |
| T4 | done | `e418c05` | Offsetting truthful-looking balance lie pins the accepted trust boundary. |
| T5 | done | `e418c05` | Post-clear same-transaction liveness and descriptive fixture modes. |
| T6 | done | `dbe03ea` | Teller artifact, transient slots, EIP-170, and accepted 24,152-byte ceiling. |
| T7 | done | `ff2896a` | Teller assumptions in the asset-admission document. |
| G1 | done with owner-approved defense-in-depth disposition | `995b596`; post-H-05 owner decision recorded in this report | Six guards are mutation-sensitive. The explicit post-solvency deletion is equivalent under adjacent exact-outflow/accounting guards; the assertion is retained, and no adjacent containment requirement is weakened. |
| G2 | done | `995b596` | Inherited recovery behavior pinned. |
| G3 | done | `dbe03ea`, `995b596` | Guarded artifact and inventory test wiring; no-CI residual remains. |
| G4 | done | `995b596` | Frozen consumer inventory and test-to-consumer matrix. |
| G5 | done | `ff2896a` | Guarded/CreditEngine monitoring and incident runbook. |
| G6 | done | `ff2896a` | SimpleErc20 unsuitable-by-default caveat. |
| C1 | done | `a22fea8` | Numeric, null, and debt-terms failure surface pinned. |
| C2 | done | `d44ab68`, `a22fea8` | Protocol committed before local-Boa measurements. |
| C3 | done | `dbe03ea` | CreditEngine artifact gate and 444-byte headroom. |
| C4 | done | this report commit | Verify-first disposable mutants are detected by existing named tests; no new checked-in mechanism was needed. |
| R1 | done | `db6149a`, matrix reconciliation in `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` | Draft exact-`0x64` profile and local readbacks pass with functionally complete embedded ephemeral doubles. |
| R2 | done | `c34fccd`, `053d831`, `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` | Builder/tests committed first; clean generation repeated twice; the test now independently rebuilds in two fresh processes and exactly pins the immutable-bound runtime hash. |
| L1 | done | `16855fb` | Trusted deposit non-arming and enclosing rollback. |
| L2 | done | `16855fb` | Both `_mc` selectors reach the same Teller-gated body. |
| L3 | done | `16855fb`, `db6149a`, `f4329499fe1139f3e8936ac5e09d80cfdd40bb59`; this report commit | L3a satisfies S2; L3b asserts both source fields change and pins all four mutation digests before the intended gates reject them. |
| L4 | done | `dbe03ea`, `c34fccd`, `053d831` | Creation, runtime template, 37-entry persistent layout, immutable layout, and local immutable-bound runtime kept distinct. |
| L5 | done | `ff2896a`; this report commit | Historical and current counts are snapshot-labeled. |
| L6 | done | `ff2896a` | Ledger monitoring and expected topology. |
| R5 | done | `eb44809`, `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` | Three canonical draft postures and post-deploy assertions pass with a functionally complete embedded ephemeral double; cadence fields are literal and inventoried. |
| X1 | done for current repository paths | `ff5fc49`, `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` | R5 manifest/order/arity plus all four historical incompatibilities are tested, and a repository-wide migration/history sweep fails if another Lootbox deployment call site appears. |
| X2 | done | `ff5fc49` | Later enablement and strict first-send boundary pinned. |
| X3 | done | `ff5fc49`, `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` | Max-minus-one is settable; the test proves the reached checked-add exceeds `uint256` before asserting the reasonless Vyper arithmetic revert. A sane cap remains an owner decision. |
| X4 | done | `ff2896a` | EVM-number/wall-time monitoring document. |
| X5 | done | `ff2896a` | Snapshot-specific release evidence checklist. |
| D1 | done | `ff2896a` | Asset-admission assumptions. |
| D2 | done | `ff2896a` | Stock-backing monitoring and incident runbook. |
| D3 | done | `ff2896a` | Ledger monitoring with expected topology. |
| D4 | done | `ff2896a` | Lootbox distribution monitoring. |
| D5 | done | `ff2896a` | Historical/native replay policy. |
| D6 | done | `ff2896a` | `lastTouch` consumer semantics. |
| D7 | done | `ff2896a` | Standalone reusable release-packet checklist; adoption remains owner-gated. |

## Artifact and release-support evidence

S1 uses only the exact-lock Vyper binary, repository-root `-p .`, and no
optimization override. The final direct checker result was:

```text
CreditEngine: creation=24336 runtime_template=24132 optimize=codesize integrity=69ebcc99c48aef76e065f4d1c7d4b974997b2ebfdefbb1d39ff5c429308cf07a
GuardedErc20: creation=10691 runtime_template=10524 optimize=gas integrity=04662cb93e8195164442a4a6fea78993ca36f9788a8362fef61caaf20c0480f1
Ledger: creation=13730 runtime_template=13125 optimize=gas integrity=62cc9e492ee1b1a3e84ad104507d684dc81edecef969fc0ae0f7a1586dd0d830
Lootbox: creation=21911 runtime_template=21569 optimize=codesize integrity=65a3999e25cc33caf88ff839fddae3ab7601a8e72e4eb96f84fd854eab3c9718
Teller: creation=24387 runtime_template=24152 optimize=codesize integrity=1d734c3c0507c8508fa8d7fcfac8aa7dff850f9f0bd167b28d22129986f97fdd
```

The cheap settings-binding negative test passed: invoking `-O gas` on a
pragma-codesize contract failed with Vyper's settings-conflict error.
Tampered-source and tampered-expectation checker tests also failed closed.

The owner-approved one-value Lootbox reconciliation was independently
rechecked:

1. `Lootbox.vy` at implementation commit
   `f40dc25ff0352b6ce79944fb28c37499da7bf0f0` and at baseline produced the
   same CLI creation SHA-256
   `0222bd8f06f226cff079c5798df5fe7fd5d97d722bc2132c454865c7c8853e09`
   and the same CLI integrity
   `65a3999e25cc33caf88ff839fddae3ab7601a8e72e4eb96f84fd854eab3c9718`.
2. No Lootbox direct/import compiler input changed between that commit and
   `a86650b187c523f27c92f05bfe959d06840025a6`.
3. Creation size `21,911` and runtime-template SHA-256
   `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097`
   match the record.

The record's `9246a6d9…` creation hash and `83995dbf…` “compiler integrity”
row are production-pipeline recipe artifacts, not canonical CLI values. Only
the creation hash received owner authorization for reconciliation. No other
expectation was regenerated from a contradictory compile.

The Ledger builder head was
`c34fccd8b9b14f209f0597b49e4cf1e58e477d7d`. Two independent generations were
byte-identical with bundle SHA-256
`db3d2af13cb66655ba751194b5240fb07bee7438f140e54062796ab46cb492af`.
The locally deployed immutable-bound runtime was 13,253 bytes with SHA-256
`3be45215fc469302bd0893ccf57c10a8a274bb65ac76ad2fc88cf8958c4d0c59`.
These are local reproduction facts, not deployment evidence.

The C2 local-Boa median gas results, seven recorded top-level calls per point,
were:

| Positions | Priced median | Zero-amount-containment median |
| ---: | ---: | ---: |
| 1 | 37,637 | 21,950 |
| 2 | 56,681 | 25,411 |
| 4 | 94,769 | 32,333 |
| 8 | 170,945 | 46,177 |
| 16 | 325,068 | 75,636 |
| 50 | 977,877 | 198,623 |

Reviewer remediation re-ran the frozen measurement selection with `-s` and
the complete environment-unset protocol. It completed `1 passed, 3 warnings
in 116.24s`; all 84 raw observations, 12 medians, and PriceDesk call counts
exactly reproduced the committed result table.

The first C2 trace-count attempt was rejected because it counted broader trace
structure. The accepted run counted selector-specific child calls.

## Validation commands and results

All pytest selections ran serially in fresh processes. The original focused
rows each used a fresh private mode-0700 root. Reviewer-remediation focused
rows shared one private mode-0700 root but used separate pytest base
directories and fresh processes. Every run called
`boa.interpret.set_cache_dir()` before importing pytest, set
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=.`, and
`ETHERSCAN_API_KEY=local-placeholder`, and used `-q -p no:cacheprovider
--basetemp <private>/pytest`.

The focused selection arguments and observed results were:

| Exact selection/check | Result |
| --- | --- |
| `/private/tmp/ripe-rh-final-gate2.uZCfBL/venv/bin/python scripts/check_contract_artifacts.py` | green; five entries reproduced |
| `tests/inventory/test_contract_artifacts.py` | reviewer-remediation run: `5 passed`, `3 warnings` |
| `tests/core/teller/` | `149 passed` |
| `tests/vaults/test_guarded_erc20.py` | `76 passed` |
| `tests/vaults/test_stock_token_vault_comparison.py` | `92 passed`, `3 warnings` |
| `tests/core/creditEngine/` | `165 passed`, `3 warnings` |
| `tests/deployment_profiles/test_ledger_robinhood_profile.py` | `21 passed` |
| `tests/deployment_profiles/test_ledger_artifact_bundle.py` | `8 passed` |
| `tests/deployment_profiles/` | reviewer-remediation run: `41 passed`, `3 warnings` |
| Ledger action-block focused selection | `57 passed` |
| Ledger full focused selection | `101 passed` |
| `tests/deployment_profiles/test_lootbox_deployment_profiles.py` before reviewer remediation | `11 passed` |
| `tests/core/lootbox/` after X2/X3 | `178 passed` |
| `tests/core/lootbox/test_underscore_rewards.py::test_x3_max_minus_one_interval_is_settable_but_gate_addition_overflows` | reviewer-remediation run: `1 passed`, `3 warnings` |
| `tests/clock/test_clock_profiles.py` | reviewer-remediation run: `57 passed`, `3 warnings` |
| `tests/inventory/test_block_clock_inventory.py` | reviewer-remediation run: `95 passed`, `3 warnings` |
| `tests/config/test_switchboard_charlie.py::test_switchboard_three_set_underscore_send_interval_timelock` | reviewer-remediation run: `1 passed`, `3 warnings` |
| `python scripts/check_block_clock_inventory.py --check` | green |
| Static Guarded consumer inventory pytest module | green |

The Phase 8 prompt referred to two named SwitchboardCharlie interval tests.
Repository discovery found only the single exact test named above; no second
selection exists.

The historical hardening-tip clock-inventory output was:

```text
production_occurrences=99 production_lines=94 production_files=17
bn_ids=32 bn_records=99 indirect_ids=1 cadence_candidates=483
seconds_unit_candidates=58 timestamp_ids=11 timestamp_occurrences=37
mixed_clock_functions=4 vyper_paths=95 post_s5_production_records=59
post_s5_production_sha256=f29e30aef76e01f77a74a910b07ba16204aabb6a0860add4a072da7de76035bd
```

The accompanying non-production counts were testing `2/2/1`, test
`34/32/7`, cadence testing `1`, and test `172`.

These counts are superseded by the post-H-05 reconciliation amendment. The
nine additional cadence candidates are configuration/tooling metadata:
three literal artifact-layout keys, three canonical profile-manifest keys, and
three profile-rule keys. The earlier implementation encoded the artifact keys
with JSON Unicode escapes and renamed the profile field
`initial_send_spacing`, which concealed the scanner-visible vocabulary.
Reviewer remediation restored the literal source names and classified all nine
occurrences explicitly. Production inventory counts and the frozen post-S5
production hash are unchanged.

### Historical aggregate-failure protocol

One ad hoc focused aggregate selected 903 tests and completed:

```text
55 failed, 848 passed, 3 warnings in 381.66s
```

Of those failures, 28 stock-vault comparison cases matched the documented
reused-address Titanoboa trace-pollution signature exactly while formatting a
revert/storage trace:
`AttributeError: 'BoolT' object has no attribute 'key_type'`.

The other 27 CreditEngine cases lost expected event logs or revert strings at
reused fixture addresses. That behavior is adjacent to the trace-pollution
pattern, but it does not carry the exact documented signature. It therefore
remains an unexplained historical aggregate anomaly rather than a
conclusively classified harness artifact.

Fresh-process controls with fresh private state then completed:

```text
tests/vaults/test_stock_token_vault_comparison.py:
92 passed, 3 warnings in 115.06s

tests/core/creditEngine/:
165 passed, 3 warnings in 120.59s
```

The fresh-process controls bound the practical risk: both affected selections
passed completely. They do not justify overstating the 27-failure root cause.
The 28 exact-signature failures are classified as harness artifacts; the 27
adjacent failures remain unresolved aggregate evidence and are not used to
claim a product defect or a clean aggregate run.

An attempted convenience command,
`/private/tmp/ripe-rh-final-gate2.uZCfBL/venv/bin/python
scripts/check_guarded_consumer_inventory.py`, failed because that script does
not exist. The authoritative inventory checker is the committed pytest module,
and it passed. The invalid convenience invocation is retained as a command
deviation.

### Full repository suite

The original run completed with `1 failed, 3538 passed, 142 deselected, 3
warnings in 473.72s`, but its command omitted ten required `env -u` names.
Before reviewer remediation, a direct ambient inspection found each omitted
name absent:

```text
RPC_URL=absent
WEB3_PROVIDER_URI=absent
ETHERSCAN_TOKEN=absent
BASESCAN_API_KEY=absent
TEST_PRIVATE_KEY=absent
BASE_MAINNET_RPC_URL=absent
BASE_SEPOLIA_RPC_URL=absent
ROBINHOOD_MAINNET_RPC_URL=absent
ROBINHOOD_TESTNET_RPC_URL=absent
ROBINHOOD_TESTNET_PRIVATE_KEY=absent
```

Owner direction to fix the review findings authorized this corrective run,
which used the exact-lock interpreter, private mode-0700 cache/temp
directories, and the complete unset list:

```sh
env -u PYTHON_DOTENV_DISABLED -u MAINNET_RPC_URL -u BASE_RPC_URL -u ARBITRUM_RPC_URL -u WEB3_ALCHEMY_API_KEY -u ALCHEMY_API_KEY -u PRIVATE_KEY -u DEPLOYER_PRIVATE_KEY -u RPC_URL -u WEB3_PROVIDER_URI -u ETHERSCAN_TOKEN -u BASESCAN_API_KEY -u TEST_PRIVATE_KEY -u BASE_MAINNET_RPC_URL -u BASE_SEPOLIA_RPC_URL -u ROBINHOOD_MAINNET_RPC_URL -u ROBINHOOD_TESTNET_RPC_URL -u ROBINHOOD_TESTNET_PRIVATE_KEY XDG_CACHE_HOME=/private/tmp/ripe-rh-review-full.uOwuMN/xdg HYPOTHESIS_STORAGE_DIRECTORY=/private/tmp/ripe-rh-review-full.uOwuMN/hyp RUN_BOA_CACHE=/private/tmp/ripe-rh-review-full.uOwuMN/boa PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ETHERSCAN_API_KEY=local-placeholder /private/tmp/ripe-rh-final-gate2.uZCfBL/venv/bin/python -c 'import os, sys; from boa.interpret import set_cache_dir; set_cache_dir(os.environ["RUN_BOA_CACHE"]); import pytest; raise SystemExit(pytest.main(sys.argv[1:]))' -q -p no:cacheprovider --basetemp /private/tmp/ripe-rh-review-full.uOwuMN/pytest
```

It completed collection/execution with:

```text
1 failed, 3540 passed, 142 deselected, 3 warnings in 558.43s
```

The only failure was again
`tests/registries/test_ripe_hq.py::test_mint_circuit_breaker_with_actual_minting`.
At reused aggregate fixture addresses, Boa lost the expected `"cannot mint"`
revert string and produced `<exception str() failed>`. A fresh-process control
using the same complete environment-unset protocol completed:

```text
1 passed, 3 warnings in 107.74s
```

The exact repeated aggregate-only signature plus the green fresh-process
control satisfy the prompt's harness-artifact classification protocol for
this one failure. The repository result is still reported as one failed, not
as a green full suite.

The 142 deselections match the repository's default local hook in
`tests/conf_env.py` for nonlocal fork markers. Pytest emitted no skips or
xfails. The two additional passes relative to the original run are the new S1
layout-negative and X1 call-site-completeness tests. The corrective wrapper
exited with pytest status 1 and did not require interruption.

## Mutation evidence

Every digest below is SHA-256 of the complete mutated source or canonical
mutated profile. “Met” means the baseline passed/rejected safely in the same
fresh process, the replacement count was checked, the mutant compiled/deployed
or profile loaded, and the named path exposed the intended missing invariant.

| Subject | Mutation and digest | Detecting test/gate | S2/S3 |
| --- | --- | --- | --- |
| Teller T1 | Delete the four dedicated receipt-measurement mutex constructs; `fdb1e2de2fb0617ba0d250e6380ce62a88107dcded80d718ffd994206270a6fd` | `test_t1_mutex_removal_mutant_exposes_offsetting_nested_receipt`; baseline rejects, while the mutant accepts an offsetting `Q-1` outer plus one-unit nested receipt against a deliberately permissive disposable vault | S2 met |
| Guarded G1 | Remove shared mutex; `71905639a3544e8bd896a49509292865ac5b1ab72050f09ed0f4cbe8f509c1bb` | `test_g1_shared_mutex_mutant_allows_authorized_nested_movement` | S2 met |
| Guarded G1 | Remove exact 32-byte returndata guard; `eb779f2d67150dc493cedeb8f63efb634a64bcdc831d83f05769c19671714ac7` | `test_g1_exact_returndata_length_mutant_accepts_33_byte_sentinel` | S2 met |
| Guarded G1 | Remove recipient delta; `71e386853c134126f4fe85dbeb17fddef060cea5e6887f54de6ecb36bd51cf53` | `test_g1_recipient_delta_mutant_accepts_short_delivery` | S2 met |
| Guarded G1 | Remove vault outflow delta; `72b909ec6369f6b6d06660d11706d8269c52460e430f699c232fa7adb99b3e29` | `test_g1_vault_outflow_mutant_spends_donated_surplus` | S2 met |
| Guarded G1 | Remove explicit post-withdraw solvency assertion; `6b4eb0ac18b9320c4db6454587d23b69dd832b2344bfd179642b105e4c8ecc29` | `test_g1_post_solvency_deletion_is_equivalent_under_adjacent_guards` proves baseline and mutant both preserve backing | S2 **not met**; guard is algebraically implied |
| Guarded G1 | Remove custody-neutrality equality; `c8ef54c3552479746da40006238b87db6c425473150284bb96d778162320149e` | `test_g1_internal_custody_neutrality_mutant_accepts_changed_observation` | S2 met |
| Guarded G1 | Replace backing-aware predicate with true; `ce56a23a5cea32a9e0a4a7cf702128daff3376500a5d05630832ba7477f3f530` | `test_g1_backing_aware_view_mutant_restores_phantom_value` | S2 met |
| CreditEngine C4 | Restore `(asset, 0)` skip; `620052b74c233e2dacdfcb3190c67b5b4364df2c581392985ea553ca3f7273b6` | Existing `test_unsafe_backing_failures_keep_terms_with_zero_capacity` fails; baseline passes in same experiment | S2 verify-first met |
| CreditEngine C4 | Route zero amount to PriceDesk; `f3191996b8c9e0b32a566e63c27a9e67a30df8448936150635e6805e863e8fbc` | Existing `test_mixed_safe_collateral_remains_exact_and_liquidatable` fails; baseline passes in same experiment | S2 verify-first met |
| Ledger L3a | Typed ArbSys call; `0357682c8018c9cec062179f1d2020109000d890950590b2b5d2f8c590f9e6b4` | `test_l3a_typed_call_mutant_fails_oversized_constructor_case` | S2 met |
| Ledger L3a | `max_outsize=32` truncation; `3012fdbc09bf750980dae1e08da48b014c846345b16dd3ca0e8ee8eaf8043865` | `test_l3a_truncation_mutant_fails_oversized_constructor_case` | S2 met |
| Ledger L3a | Remove constructor probe; `d847811d29fb7eede2c6be62938703cd508d4196ab47e543fb206d42d3a6c073` | `test_l3a_removed_probe_mutant_fails_missing_constructor_case` | S2 met |
| Ledger L3a | Native fallback after ArbSys failure; `1379dd6a5e67703db3e1a3c00fa0063be4e993540117ebc624657ca4510ac25d` | `test_l3a_native_fallback_mutant_fails_runtime_source_failure_case` | S2 met |
| Ledger L3a | Monotonic comparison; `94bc87b5d2549444b3ed3fe9f01d90275643e92697716899ea3f99307780abdb` | `test_l3a_monotonic_mutant_fails_equality_only_regression_case` | S2 met |
| Ledger L3b | Set both canonical profile source fields to zero; canonical manifest `ece7fa2b42d892e7e46b199e75f9050a397b8a89dd6d1ed2328fbb1715ca81e0` | `test_l3b_zero_or_wrong_source_mutant_fails_the_profile_gate` | S3 met; digest pinned in test |
| Ledger L3b | Set both canonical profile source fields to `0x65`; canonical manifest `259a192a718e82f6866ea3c4807b7c0add05208ef051ab1a3407cc22fe66cbb4` | `test_l3b_zero_or_wrong_source_mutant_fails_the_profile_gate` | S3 met; digest pinned in test |
| Ledger L3b | Delete immutable readback evidence; profile source `03c63ca6744e62024fe7ffaa573110554fc68f08513cf505afd4dd05cea48785` | `test_l3b_omitted_immutable_readback_mutant_fails_evidence_completeness` | S3 met; digest pinned in test |
| Ledger L3b | Delete post-deploy assertion call; profile source `9fd01fe6ee51b2f15162670761516e227f6b5fcfce38b837366e6c0e87e6dd6d` | `test_l3b_omitted_post_deploy_assertions_mutant_fails_evidence_completeness` | S3 met; digest pinned in test |

The canonical unmodified Ledger profile source used for the final digest
calculation was
`1a26ccd9b833c4c691dca979bc052e2d27476ef2785448dbaeea8595e2c559b4`.
As part of reviewer remediation, the two C4 digests above were independently
re-derived from exact-count-checked single replacements against the current
CreditEngine source; both reproduced the recorded values.

## Deviations

1. **Corrected prompt compiler line.** The global
   `optimize=codesize throughout` statement was defective. Owner direction
   authorized source-governed optimization and prohibited `-O`. This is the
   only settings recipe used by S1.
2. **Lootbox one-value reconciliation.** The record's creation hash and
   “compiler integrity” row came from a divergent production-pipeline recipe.
   The owner authorized freezing only the independently reconciled CLI
   creation hash; all other compile/record contradictions remained hard stops.
3. **G1 post-solvency mutation.** Exact vault outflow, exact nominal reduction,
   and prior backing imply the explicit post-solvency assertion. Its deletion
   did not create a failing scenario, so no S2 claim is made for that guard.
   The owner approved retaining the assertion as defense-in-depth with that
   algebraic redundancy understood. The approval does not weaken any adjacent
   solvency, custody, receipt, transfer, or accounting invariant and does not
   authorize deployment.
4. **Closed matrix inverse delta.** The original matrix listed four unused
   support-contract files. Reviewer confirmation established that the embedded
   ephemeral doubles were functionally complete, and owner direction to
   address the feedback authorized removing the unused paths from the matrix.
   No placeholder files were added.
5. **Closed scanner-evasion defect.** Artifact keys encoded with JSON Unicode
   escapes and the profile-only alias `initial_send_spacing` hid nine cadence
   metadata occurrences from the inventory scanner. Commit
   `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` restored
   literal source names, classified the nine `config`/`tooling` occurrences,
   and left production clock classifications unchanged.
6. **Closed L3b digest placement.** Commit
   `f4329499fe1139f3e8936ac5e09d80cfdd40bb59` moved all four complete
   mutation digests into the test module and proved that both canonical
   profile source fields change in each manifest mutant.
7. **Invalid inventory convenience command.** A nonexistent
   `scripts/check_guarded_consumer_inventory.py` was invoked once. The actual
   committed inventory pytest module passed.
8. **C2 rejected attempt.** A broad trace-count measurement was discarded;
   only the selector-counted, seven-call medians are reported.
9. **Aggregate-only failures.** Twenty-eight of the 903-test aggregate
   failures exactly matched known reused-address trace/repr pollution. The
   other 27 had adjacent lost-log/revert behavior but remain under-explained;
   their green fresh-process controls bound risk without proving root cause.
10. **Closed full-suite environment command gap.** The original invocation
   omitted ten required `env -u` names. A current ambient inspection found all
   ten absent, and reviewer remediation ran the suite again with the complete
   required unset list.
11. **Post-summary wrapper hang.** The original full-suite wrapper/PTY was interrupted
    only after pytest emitted its completed result summary.
12. **C4 verify-first outcome.** Existing named tests detected both required
    disposable mutants. No additional checked-in test mechanism was added.
13. **Historical commit prefixes.** Several earlier implementation commits use
    `feat(rh):`, which was not one of the prompt's examples but is established
    repository history. They were not rewritten: changing already-recorded
    commits would invalidate the evidence chain and was not authorized.
14. **Report-only evidence review.** The reusable release checklist now
    requires an independent reviewer to existence-check commit objects and
    reproduce sampled narrative-only counts, medians, and digests.

## Residuals register

| Residual | State |
| --- | --- |
| Automatic S1 trigger | No CI platform wiring exists; owner process item. |
| X1 future deployment paths | Only R5 exists as a current canonical future path; later paths require their own dry-run. |
| X3 sane upper interval bound | UNRESOLVED — owner decision; no source cap authorized. |
| D7 process adoption | Checklist exists; adoption into an actual release process is owner-gated. |
| Runbook authority fields | UNRESOLVED where the owner has not assigned pause/escalation/recovery authority. |
| G1 explicit post-solvency mutation | **CLOSED by owner decision.** The algebraically equivalent assertion is retained as defense-in-depth; no S2-sensitive claim is made, and every adjacent invariant remains controlling. |
| Historical 903-test aggregate | Twenty-seven CreditEngine failures remain under-explained despite fully green fresh-process controls; no exact harness signature was captured for them. |
| Live qualification/deployment/configuration | Not attempted; all remain live-gated. |
| `rh` drift | None observed: `rh` remained `a86650b187c523f27c92f05bfe959d06840025a6` at the pre-report check. |
| Main-worktree drift | Initial capture empty; pre-report read-only recheck also empty. |
| Test/mock drift from reviewed snapshot to baseline | None; both log and name-status inventories empty. |
| Production source/ABI/migration changes | None. |

## Historical Step 1 pre-review audit

The following audit is preserved as the exact observation that exposed the
original matrix defect. It is superseded by the owner-authorized reviewer
reconciliation and current audit that follow it.

`BASELINE.md` supplied the 40-hex literal
`a86650b187c523f27c92f05bfe959d06840025a6`.

The ancestry command succeeded:

```text
git merge-base --is-ancestor a86650b187c523f27c92f05bfe959d06840025a6 HEAD
exit 0
```

Both cleanliness commands were empty:

```text
git status --short

git ls-files --others --exclude-standard
```

The complete pre-report change list was:

```text
A	config/contract-artifact-expectations.json
A	docs/chains/rh/hardening/BASELINE.md
A	docs/chains/rh/hardening/asset-admission-assumptions.md
A	docs/chains/rh/hardening/creditengine-gas-measurements.md
A	docs/chains/rh/hardening/guarded-consumer-inventory.md
A	docs/chains/rh/hardening/last-touch-consumer-semantics.md
A	docs/chains/rh/hardening/ledger-local-artifact-bundle.json
A	docs/chains/rh/hardening/ledger-monitoring-runbook.md
A	docs/chains/rh/hardening/ledger-replay-policy.md
A	docs/chains/rh/hardening/lootbox-distribution-monitoring.md
A	docs/chains/rh/hardening/mutation-evidence-protocol.md
A	docs/chains/rh/hardening/release-packet-evidence-checklist.md
A	docs/chains/rh/hardening/stock-backing-monitoring-runbook.md
A	scripts/check_contract_artifacts.py
A	scripts/proposals/__init__.py
A	scripts/proposals/build_ledger_artifact_bundle.py
A	scripts/proposals/ledger-robinhood-profile.json
A	scripts/proposals/ledger_robinhood_profile.py
A	scripts/proposals/lootbox-deployment-profiles.json
A	scripts/proposals/lootbox_deployment_profiles.py
M	tests/core/creditEngine/test_stock_backing.py
M	tests/core/lootbox/test_underscore_rewards.py
M	tests/core/teller/test_teller_action_block.py
M	tests/core/teller/test_teller_deposit.py
M	tests/data/test_ledger_action_block.py
A	tests/deployment_profiles/test_ledger_artifact_bundle.py
A	tests/deployment_profiles/test_ledger_robinhood_profile.py
A	tests/deployment_profiles/test_lootbox_deployment_profiles.py
A	tests/inventory/test_contract_artifacts.py
A	tests/vaults/test_guarded_consumer_inventory.py
M	tests/vaults/test_guarded_erc20.py
```

The additions-only protection audit for the pre-existing
`docs/chains/rh/` tree was empty:

```text
git diff --name-status --diff-filter=MDRTUXB a86650b187c523f27c92f05bfe959d06840025a6 HEAD -- docs/chains/rh/
```

The protected production/interface/ABI/migration audit was empty:

```text
git diff --name-status a86650b187c523f27c92f05bfe959d06840025a6 HEAD -- contracts/ ':(exclude)contracts/mock' ':(exclude)contracts/testing' interfaces/ scripts/abis/ migrations/
```

The mechanical pre-report comparison printed:

```text
approved_unique_paths=36
changed_unique_paths=31
changed_not_in_matrix:
matrix_not_changed:
contracts/testing/MockArbSys.vy
contracts/testing/MockLedgerDefaults.vy
contracts/testing/MockProfileRipeHq.vy
contracts/testing/TellerDepositRollbackProbe.vy
docs/chains/rh/hardening/hardening-pass-report.md
```

At that historical point the report was the sole permitted Step 1 inverse
delta and the other four paths violated the then-current matrix. There were no
changed paths outside it.

## Current post-remediation pre-report audit

The owner-authorized final matrix and current baseline diff now match exactly:

```text
approved_unique_paths=35
changed_unique_paths=35
changed_not_in_matrix:
<empty>
matrix_not_changed:
<empty>
```

Commit-object verification resolved every full hash represented as a commit
in this report, including the corrected Ledger builder hash
`c34fccd8b9b14f209f0597b49e4cf1e58e477d7d` and reviewer-remediation commit
`f4329499fe1139f3e8936ac5e09d80cfdd40bb59`.

The current protected production/interface/ABI/migration diff remains empty.
The local hardening-document link audit reports zero missing targets and zero
bad Markdown-section anchors. The final clean-tree audit runs after this
report's commit; its outputs and final commit SHA are delivered in the closing
response, not invented in this file.

## Post-H-05 hardening reconciliation amendment

This amendment is the current controlling status for the unstaged,
uncommitted reconciliation candidate. It preserves all earlier text as
historical `rh-hardening` provenance.

### Current baseline and provenance

The candidate starts directly from authoritative `rh`:

| Identity | Value |
| --- | --- |
| `rh` commit | `a8ec21f78e8b7c791952c6d01d8cf73f43ee2d48` |
| `rh` tree | `be5d2dc78842550fda2c8c1fd4cb72bb6fbefadb` |
| candidate branch | `rh-hardening-post-h05-reconciliation` |
| candidate worktree | `/Users/wigglez/dev/ripe-protocol-rh-hardening-post-h05-reconciliation` |
| historical hardening tip | `2c7f09381888beb54322628fec44d284bcec5063` |
| historical hardening tree | `8d100da5cdf40181c411afb8c0d28f7cc4e867bf` |
| merge base | `a86650b187c523f27c92f05bfe959d06840025a6` |

Before mutation, local `rh`, cached `origin/rh`, and credential-free live
`origin/rh` matched the stated commit. The historical hardening worktree and
index were clean, the branch was local-only, and its 16-commit / 35-path net
scope matched the expected topology.

The mode-0700 provenance source directory is
`/Users/wigglez/dev/ripe-protocol-hardening-provenance.WLGBoc`; the mode-0600
archive is
`/Users/wigglez/dev/ripe-protocol-hardening-provenance.WLGBoc.tar.gz`.
The archive SHA-256 is
`d7e0cb91bf3c3719332f02fe3335dd143fe24dad8d6ac82fd0e65141970b52eb`;
its member-manifest SHA-256 is
`d8052f55d279d6ff8c50d62772f195e6b65aa4f2d665e1d29fc257560c380bbf`.
It contains the canonical original full-index patch at SHA-256
`0abdad23629b1f8b98c9eef22cc07e3b8e7280654e4c89b0abe66adebf6fefec`,
337,406 bytes and 57 hunks, plus the complete path, per-file, blob, ancestry,
commit-metadata, and signature records. All 16 recorded commit signatures
have status `G`.

### Scope and preservation proof

The candidate contribution relative to current `rh` is exactly the same
35-path set as the historical hardening net contribution. The Git-visible set
comparison has no missing or extra path.

- 28 non-overlap paths are byte-identical to the historical hardening tip.
- Four non-overlap paths contain demonstrated and bounded reconciliation
  corrections:
  `docs/chains/rh/hardening/BASELINE.md`,
  `docs/chains/rh/hardening/hardening-pass-report.md`,
  `tests/core/creditEngine/test_stock_backing.py`, and
  `tests/core/teller/test_teller_action_block.py`.
- The three expected overlap paths were merged semantically as described
  below.
- All 11 current H-04/H-05 paths outside the overlap are byte-identical to
  authoritative `rh`.
- Production contracts, interfaces, checked-in ABIs, dependencies, and
  migration execution/configuration are unchanged.

The first compatibility correction updates the C2 gas protocol's retired
temporary-interpreter and 90-distribution assertions to the owner-mandated
persistent exact-lock interpreter, its executable SHA-256, the requirements
SHA-256, and the tuple-sorted 93-distribution normalized inventory SHA-256.
It changes no gas path, position count, repetition, price-call, or semantic
assertion.

The second correction root-causes the historical aggregate-only Boa failure.
The L1 action-block test temporarily deployed a producer with
`override_address=credit_engine.address` inside `boa.env.anchor()`. Titanoboa
reverted EVM code and storage but did not snapshot its separate address-to-
debug-contract registry, leaving the producer's source map at the real
CreditEngine address. Later nested reverts could therefore lose their reason
and render `<exception str() failed>`. The test now restores the original
CreditEngine registration in a `finally` block and asserts the registry
identity. Its trusted-deposit, explicit-touch, enclosing-revert, and rollback
assertions are unchanged.

### Three-path semantic merge

1. `config/block-clock-inventory.json` retains the complete current H-04
   schema-v2 inventory, exact-path admission records, stable semantic IDs,
   review authorities, provenance, and fingerprints. It adds the nine
   hardening-tip cadence metadata records unchanged as explicit
   `config`/`tooling` candidates.
2. `scripts/check_block_clock_inventory.py` retains H-04's exact-record and
   site fingerprint validation, future-path fail-closed behavior, and current
   production admissions. It adds the exact nine-key
   `REVIEWER_REMEDIATION_CADENCE_KEYS` set to the historical-fingerprint
   reconciliation exclusion without adding any scan exclusion, glob
   exemption, renamed identifier, or escaped literal.
3. `tests/inventory/test_block_clock_inventory.py` retains all 130 current
   H-04 tests and updates only the combined candidate expectation from 590 to
   599. The hardening negative cases and current exact-path/fail-closed cases
   all pass.

### Final inventory identities

The reconciled checker reports:

```text
production_occurrences=99 production_lines=94 production_files=17
bn_ids=32 bn_records=99 indirect_ids=1 cadence_candidates=599
seconds_unit_candidates=58 timestamp_ids=11 timestamp_occurrences=37
mixed_clock_functions=4 vyper_paths=95 post_s5_production_records=59
post_s5_production_sha256=f29e30aef76e01f77a74a910b07ba16204aabb6a0860add4a072da7de76035bd
```

The historical S5 fingerprint remains exactly
`924a559075d5b96bcac3f73d28390deee3b436fe5500adc4fb6bf769282217b4`.
Non-production direct counts remain testing `2/2/1` and test `34/32/7`;
non-production cadence counts are testing `1` and test `177`. The complete
inventory module remains 130 tests.

### G1 owner disposition

The owner approved retaining the G1 post-solvency assertion as
defense-in-depth. Its deletion is algebraically equivalent under the adjacent
exact-outflow, exact-accounting, and prior-backing guards, so mutation survival
does not demonstrate missing behavior and no S2-sensitive claim is made for
that assertion. The assertion remains in production source. This disposition
does not relax any solvency, custody, receipt, transfer, recipient-delivery,
outflow, accounting, backing, or atomicity invariant and does not authorize
deployment.

### Reconciliation validation

All pytest runs used the persistent exact-lock Python 3.12.0 environment,
Vyper 0.4.3, Titanoboa 0.2.7, private mode-0700 caches and basetemps,
`PYTHONDONTWRITEBYTECODE=1`, pytest's cache provider disabled, and the
non-secret `ETHERSCAN_API_KEY=local-placeholder`. Every RPC/key/signer
environment variable was explicitly unset for collection and complete-suite
runs. The harness used local loopback only; no RPC, fork, account, signer,
transaction, migration, simulation, deployment, or external state was used.

| Gate | Current result |
| --- | --- |
| direct S1 artifact checker | green; all five exact expectations reproduced |
| S1 artifact negative module | 5 passed |
| complete Teller hardening selection | 150 passed |
| GuardedErc20 hardening module | 74 passed |
| stock-vault composed comparison | 92 passed |
| complete CreditEngine selection, including C2 | 165 passed |
| Ledger and Lootbox deployment profiles | 41 passed |
| complete Ledger module | 101 passed |
| Ledger action-block module | 44 passed |
| complete Lootbox directory | 178 passed |
| static Guarded consumer inventory | 2 passed |
| current block-clock checker | green with the exact identities above |
| complete inventory module | 130 passed |
| H-04 manifest/generator and clock-profile gate | 111 passed |
| H-05 discovery and execution-plan gate | 98 passed |
| combined H-01/H-02/S1/H-03/H-06 gate | 453 passed |
| S5 Ledger/Teller action-block gate | 57 passed |
| Track 8 M4 four-file gate | 74 passed |
| Track 8 M1/M2/M3 eight-file union | 469 passed |
| targeted Boa-registry regression | 14 passed; the 13 action-block tests followed by the formerly failing RipeHq test in one process |
| complete collection | 3,785 selected; 3,927 total; 142 policy-controlled deselections; zero collection errors |
| corrected complete serial suite | 3,785 passed; 142 deselected; zero failures, selected skips, or xfails; 539.62 seconds |
| Python compilation | all 18 candidate Python paths compiled to an external bytecode cache |
| JSON parsing | all 120 repository-visible JSON files parsed |
| `pip check` | no broken requirements |

The first complete serial attempt accurately reported one failure and 3,784
passes: the historical aggregate-only `RipeHq` symptom. It was not waived.
The isolated control passed; a five-module same-process prefix reproduced it;
binary narrowing isolated the L1 action-block test; the registry mechanism was
confirmed from Titanoboa's distinct EVM snapshot and debug-contract maps; and
the 14-test same-process regression passed after the bounded fix. A second
full serial run from a new cache then passed all 3,785 selected tests.

The three observed warnings are the established `PytestAssertRewriteWarning`
notices for `_hypothesis_globals`, `hypothesis`, and `boa`. They are caused by
calling `boa.interpret.set_cache_dir()` before importing pytest so that all
compiler cache writes stay in the private external directory. They are
explained harness import-order notices, not product warnings, suppressions,
skips, or relaxed assertions.

### Residuals and lifecycle boundary

Automatic S1 CI triggering, live artifact/configuration qualification,
runbook authority assignments, D7 process adoption, a future X1 deployment
path, and the X3 sane upper interval bound remain owner-gated or unresolved as
recorded above. The G1 defense-in-depth decision and the prior aggregate Boa
anomaly are closed in this candidate.

This candidate grants no commit, staging, push, PR, merge, `rh` integration,
deployment, migration execution, activation, release, signer/account/key
access, broadcasting, RPC/fork access, governance action, H-06 successor,
H-07/H-08/H-09 implementation, CCIP work, Deleverage work, or zero-backing
settlement/loss-allocation/bad-debt-policy authority.
