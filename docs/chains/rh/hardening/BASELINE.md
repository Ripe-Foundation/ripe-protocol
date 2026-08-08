# RH hardening pass baseline, traceability, and path matrix

> **Path note (8 August 2026):** some paths cited below no longer exist in the
> active tree — the block-clock inventory, the `contracts/testing/` probes, and
> the extracted deploy manifests and review records were removed. The citations
> were accurate when written and are left intact. See
> [`REMOVED.md`](../../../simplification/REMOVED.md) for the full index; everything is
> recoverable from git history. No production contract was modified.

This originated as the sole Phase 0 repository artifact for the
owner-authorized RH hardening and offline release-support pass. The historical
hardening baseline remains immutable provenance. The post-H-05 reconciliation
amendment below binds the current candidate to authoritative `rh` while
preserving the same fail-closed 35-path ceiling.

## Post-H-05 reconciliation baseline

| Field | Literal value |
| --- | --- |
| Authoritative source commit | `a8ec21f78e8b7c791952c6d01d8cf73f43ee2d48` |
| Authoritative source tree | `be5d2dc78842550fda2c8c1fd4cb72bb6fbefadb` |
| Source branch | `rh` |
| Candidate branch | `rh-hardening-post-h05-reconciliation` |
| Candidate worktree | `/Users/wigglez/dev/ripe-protocol-rh-hardening-post-h05-reconciliation` |
| Historical hardening tip | `2c7f09381888beb54322628fec44d284bcec5063` |
| Historical hardening tree | `8d100da5cdf40181c411afb8c0d28f7cc4e867bf` |
| Merge base | `a86650b187c523f27c92f05bfe959d06840025a6` |
| Reconciliation scope | exactly 35 paths; no production contract, interface, ABI, dependency, or migration execution path |
| Compiler settings | Source-governed optimization: Teller, CreditEngine, and Lootbox `codesize`; GuardedErc20 and Ledger Vyper-default `gas`; no `-O` override; `experimental_codegen=false` |
| Interpreter | `/Users/wigglez/dev/ripe-protocol-validation-envs/rh-wave2-py312/bin/python` |
| Python executable SHA-256 | `d23fa2c326127c9590d097603f105d69e68774968f46246fc7a8a80103600765` |
| Exact requirement pins | `92` |
| Requirement deviations | `0` |
| Requirements SHA-256 | `214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010` |
| Normalized installed-inventory SHA-256 | `9d1b066c4d8c96bff1c97cdcd243905b8c02324b434c962553a1f1b58886df92` |
| Vyper | `0.4.3+commit.bff19ea2` |
| Titanoboa | `0.2.7` |

Local `rh`, cached `origin/rh`, and credential-free live `origin/rh` matched
the source commit before mutation. The existing `rh-hardening` worktree and
index were clean at the historical tip and remain unchanged. The candidate is
an unstaged, uncommitted working-tree contribution based directly on the
authoritative source commit; it does not import the hardening branch's commit
history.

## Historical hardening provenance baseline

| Field | Literal value |
| --- | --- |
| Baseline commit | `a86650b187c523f27c92f05bfe959d06840025a6` |
| Reviewed implementation snapshot | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Branch | `rh-hardening` |
| Worktree | `/Users/wigglez/dev/ripe-protocol-rh-hardening` |
| Source branch captured once | `rh` |
| Compiler settings | Source-governed optimization: Teller, CreditEngine, and Lootbox `codesize`; GuardedErc20 and Ledger Vyper-default `gas`; no `-O` override; `experimental_codegen=false` |
| Interpreter | `/private/tmp/ripe-rh-final-gate2.uZCfBL/venv/bin/python` |
| Exact requirement pins | `90` |
| Requirement deviations | `0` |
| Vyper | `0.4.3+commit.bff19ea2` |
| Canonical environment manifest SHA-256 | `f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d` |

The exact main-worktree `git status --porcelain` capture was empty:

```text
```

The branch collision check failed as required:

```text
fatal: 'refs/heads/rh-hardening' - not a valid ref
```

The worktree path was absent from both `git worktree list` and the filesystem
before creation.

## Baseline identity verification

The five production sources match both the directory README and their
component records:

| Path | SHA-256 |
| --- | --- |
| `contracts/core/Teller.vy` | `4afc6ce1ccf21cb65e04ce3c56fedcf60bb79cba8e7dc51fd855a1f1f82bd909` |
| `contracts/vaults/GuardedErc20.vy` | `0fcdb02a0b3adf56ef0fd04397c57ac40325a37c87a32f29979dadc5eaf353ed` |
| `contracts/core/CreditEngine.vy` | `7de649cece6e076b75775bb4ff5f397bf5ffa0a50ccdc462a061ca047b888e3d` |
| `contracts/data/Ledger.vy` | `6bd731a6ce9084de213494ebad09f8e52c782153842708b78f90fa178c06e9e3` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |

The record-stated committed ABI identities also match:

| Path | SHA-256 |
| --- | --- |
| `scripts/abis/GuardedErc20.json` | `1477d537e71863a7da8c727791cdbf3e745cc31b81889a00615296148d9dafb0` |
| `scripts/abis/Ledger.json` | `c6fc1c410e13f144ae9e9d1853378d476fa578211b08f67b23f80c2075bc415f` |
| `scripts/abis/Lootbox.json` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` |

The reviewed-snapshot-to-baseline inventory command covered:

```text
tests/core/teller/
tests/vaults/test_guarded_erc20.py
tests/vaults/test_stock_token_vault_comparison.py
tests/core/creditEngine/
tests/data/test_ledger_action_block.py
tests/core/teller/test_teller_action_block.py
tests/core/lootbox/
contracts/mock/
contracts/testing/
```

Both `git log --oneline
cca60bb85c772c977bb9fb62c1c6c5252c3a1438..a86650b187c523f27c92f05bfe959d06840025a6
-- <paths>` and the corresponding `git diff --name-status` were empty. There
is no recommendation-sensitive test, mock, or support drift to adjudicate.

## Environment manifest

The canonical, sorted `importlib.metadata` manifest was:

```text
annotated-types==0.7.0
asttokens==3.0.0
attrs==25.3.0
babel==2.17.0
bitarray==3.7.1
cached-property==2.0.1
cbor2==5.9.0
certifi==2025.8.3
charset-normalizer==3.4.3
ckzg==2.1.2
click==8.3.3
colorama==0.4.6
coverage==7.10.6
cytoolz==1.0.1
decorator==5.2.1
dotenv==0.9.9
eth-account==0.13.7
eth-bloom==3.1.0
eth-hash==0.7.1
eth-keyfile==0.8.1
eth-keys==0.7.0
eth-rlp==2.2.0
eth-stdlib==0.2.8
eth-typing==5.2.1
eth-utils==5.3.1
eth_abi==5.2.0
executing==2.2.1
ghp-import==2.1.0
hexbytes==1.3.1
hypothesis==6.138.15
idna==3.15
immutables==0.21
iniconfig==2.1.0
ipython==9.8.0
ipython_pygments_lexers==1.1.1
jedi==0.19.2
jinja2==3.1.6
lark==1.2.2
lru-dict==1.3.0
markdown-it-py==4.0.0
markdown==3.9
markupsafe==3.0.2
matplotlib-inline==0.2.1
mdurl==0.1.2
mergedeep==1.3.4
mkdocs-get-deps==0.2.0
mkdocs-material-extensions==1.3.1
mkdocs-material==9.5.41
mkdocs==1.6.1
packaging==24.2
paginate==0.5.7
parsimonious==0.10.0
parso==0.8.5
pathspec==0.12.1
pexpect==4.9.0
pip==23.2.1
platformdirs==4.4.0
pluggy==1.6.0
prompt_toolkit==3.0.52
ptyprocess==0.7.0
pure_eval==0.2.3
py-ecc==8.0.0
py-evm==0.12.1b1
pycryptodome==3.23.0
pydantic==2.11.7
pydantic_core==2.33.2
pygments==2.20.0
pymdown-extensions==10.21.3
pytest-cov==7.0.0
pytest==8.4.2
python-dateutil==2.9.0.post0
python-dotenv==1.2.2
pyyaml==6.0.2
pyyaml_env_tag==1.1
regex==2025.9.1
requests==2.33.0
rich==14.1.0
rlp==4.0.1
six==1.17.0
sortedcontainers==2.4.0
stack-data==0.6.3
titanoboa==0.2.7
toolz==1.0.0
traitlets==5.14.3
trie==3.1.0
typing-inspection==0.4.1
typing_extensions==4.15.0
urllib3==2.7.0
vvm==0.3.2
vyper==0.4.3
watchdog==6.0.0
wcwidth==0.2.14
wheel==0.46.2
```

Manifest SHA-256:
`f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d`.

## Recommendation traceability

Every bullet in each component record's `Currently required`, `Recommended
hardening`/`Recommended changes`, `Parked by owner`, and `Explicitly not
recommended` sections has exactly one disposition below. `prohibited` means
prohibited in this task absent later explicit owner authorization.

### Teller

| Record bullet | Disposition |
| --- | --- |
| Bind the deployed artifact to reviewed source/compiler | `live-gated` |
| Recheck size, ABI/selectors/events/constructor, persistent and transient layout | `T6` |
| Qualify each exact token implementation/configuration | `live-gated` |
| Review supported vaults and composed routes | `T2` |
| Complete deployment/configuration readback, monitoring, and owner release decision | `live-gated` |
| Mutex-sensitive authorized callback regression | `T1` |
| Exercise adversarial vault callback mode 5 | `T2` |
| Prove transient rollback without manual clearing | `T3` |
| Add offsetting canonical-balance lie | `T4` |
| Add post-clear liveness and name/remove opaque modes | `T5` |
| Retain EIP-170/24,152-byte gates in central artifact checking | `T6` |
| State exact-transfer and truthful-balance assumptions | `T7` |
| Separate Deleverage branch/PR | `parked` |
| CCIP workflows | `parked` |
| Zero-backing settlement/loss allocation/bad debt | `parked` |
| Replace `_exactBalance` with typed `balanceOf` | `prohibited` |
| Remove/clear the dedicated mutex before `V == Q` | `prohibited` |
| Replace transient state with persistent mutex/checkpoint | `prohibited` |
| Remove vault-result equality | `prohibited` |
| Accept and credit `R != Q` | `prohibited` |
| Move custody into vault-pull or prepare/finalize architecture | `prohibited` |
| Add `C2` or a per-asset mutex without its documented trigger | `prohibited` |
| Change Teller source to undo whitespace churn | `prohibited` |

### GuardedErc20

| Record bullet | Disposition |
| --- | --- |
| Bind exact artifact, constructor, VaultBook slot, asset, and configuration | `live-gated` |
| Qualify the exact production token and control/liveness behavior | `live-gated` |
| Prove the enabled Teller plus Guarded deposit composition | `live-gated` |
| Revalidate exact configured Teller/AuctionHouse/CreditEngine/Guarded routes | `conditional` |
| Preserve the one-AAPL guarded initial assignment without guessed slot/adoption | `live-gated` |
| Guard-by-guard S2 mutation evidence | `G1` |
| Focused inherited recovery-path tests | `G2` |
| Locked-compiler artifact/test/inventory automation | `G3` |
| Frozen consumer inventory and consumer-path proof | `G4` |
| Monitoring and incident runbook | `G5` |
| SimpleErc20 unsuitable-by-default admission caveat | `G6` |
| Deficient settlement and auction completion | `parked` |
| User/protocol/issuer loss allocation | `parked` |
| Surplus ownership and recapitalization allocation | `parked` |
| Bad-debt recognition/forgiveness/exactly-once accounting | `parked` |
| Permanent-versus-temporary backing-loss policy | `parked` |
| Automatic Base migration | `parked` |
| CCIP workflows | `parked` |
| Separate Deleverage branch/PR | `parked` |
| Change reviewed GuardedErc20 source | `prohibited` |
| Modify BasicVault globally | `prohibited` |
| Replace SimpleErc20 under the same name | `prohibited` |
| Add mutable guarded mode | `prohibited` |
| Adopt SharesVault without owner-selected share economics | `prohibited` |
| Weaken exact returndata/delivery for an incompatible token | `prohibited` |
| Add token-call gas caps | `prohibited` |
| Shared-module refactor solely for deduplication | `prohibited` |
| Describe containment as settlement/bad-debt resolution | `prohibited` |

### CreditEngine

| Record bullet | Disposition |
| --- | --- |
| Bind exact release identity, artifacts, compiler/settings, runtime and configuration | `C3` |
| Rerun focused/composed tests at a future release snapshot | `conditional` |
| Prove enabled vault `(empty,0)` versus `(asset,0)` and approved posture | `live-gated` |
| Monitor backing failures, deficits, health transitions, liquidation, auctions, settlement | `D2` |
| Document each liquidation/loss transition separately | `D2` |
| Focused `getMaxWithdrawableForAsset` numeric/failure regression | `C1` |
| Measured marginal gas over realistic position counts | `C2` |
| Change-triggered artifact/test automation without inventing CI | `C3` |
| Retain zero-skip and zero-price mutation detection | `C4` |
| Cross-asset `lowestLtv` policy | `parked` |
| Post-loss interest policy | `parked` |
| Grace/recapitalization/settlement/restoration/loss/bad debt | `parked` |
| Separate Deleverage branch/PR | `parked` |
| CCIP workflows | `parked` |
| Restore `amount == 0` skip | `prohibited` |
| Price a zero amount | `prohibited` |
| Add a second raw custody reader | `prohibited` |
| Revert debt-health evaluation solely for unsafe/unknown backing | `prohibited` |
| Present parked policy as planned work | `prohibited` |
| Restore deleted blank lines | `prohibited` |
| Describe integration as deployment/activation/settlement resolution | `prohibited` |

### Ledger

| Record bullet | Disposition |
| --- | --- |
| Executable exact-`0x64` Robinhood profile | `R1` |
| Reproducible deployment bundle | `R2` |
| Native and historical replay policy | `D5` |
| Real-network Nitro/ArbSys/topology qualification | `live-gated` |
| Monitoring and incident response | `D3` |
| Confirm `lastTouch` consumer semantics | `D6` |
| `depositFromTrusted` non-arming/rollback test | `L1` |
| Dual `_mc` selector test | `L2` |
| Source/profile mutation coverage | `L3a` |
| Automated source/artifact/layout/runtime checks | `L4` |
| Snapshot-label all counts | `L5` |
| Monitoring thresholds and expected topology | `L6` |
| Separate Deleverage branch/PR | `parked` |
| CCIP workflows | `parked` |
| Zero-backing settlement/loss/bad debt | `parked` |
| Refactor Ledger solely for generic appearance | `prohibited` |
| Create `LedgerRh.vy` | `prohibited` |
| Add mutable/arbitrary provider or selector | `prohibited` |
| Add native fallback | `prohibited` |
| Add `chain.id` dispatch | `prohibited` |
| Disable equality guard | `prohibited` |
| Add monotonicity enforcement without a separate policy | `prohibited` |
| Edit historical Base migration as replay | `prohibited` |
| Migrate existing Base Ledger for bytecode parity | `prohibited` |
| Remove `_mc` in this release | `prohibited` |

### Lootbox

| Record bullet | Disposition |
| --- | --- |
| Pin source/ABI/compiler/creation hash and ordered constructor manifest | `R5` |
| Encode RH floor `7_200` and interval zero in reviewed draft path | `R5` |
| Verify deployed getter/state/runtime/registry/capabilities | `live-gated` |
| Revalidate RH EVM-number model/cadence at release | `live-gated` |
| Keep rewards/routes/minting disabled pending gates | `live-gated` |
| Base convergence forward migration and operational plan | `conditional` |
| Add future deployment/manifest tests | `X1` |
| Constructor arity/order/manifest dry-run tests | `X1` |
| Initially-disabled/later-enabled first-send boundary | `X2` |
| Max-minus-one/overflow coverage and separate sane-cap decision | `X3` |
| EVM-number and wall-time monitoring | `X4` |
| Regenerate snapshot-specific release evidence counts | `X5` |
| Deleverage, CCIP, zero-backing settlement/loss/bad debt | `parked` |
| Rewrite historical Base migrations | `prohibited` |
| Add `chain.id` branching or Robinhood-only Lootbox | `prohibited` |
| Make the floor governance-mutable | `prohibited` |
| Replay old call sites against current source | `prohibited` |
| Infer a live address/signer/role/reward amount/runtime | `prohibited` |
| Treat green source/tests as lifecycle approval | `prohibited` |
| Claim absent H-04/H-06/M4 work is integrated | `prohibited` |

## Approved work-item path matrix

Only the paths below may differ from the frozen baseline. Rows containing an
existing file are the complete Phase 0 enumeration of permitted existing-file
edits. New files inside the prompt's pre-authorized locations may be appended
later with a one-line justification in the same commit that first uses them.

| Work item | Exact path(s) |
| --- | --- |
| Phase 0 | `docs/chains/rh/hardening/BASELINE.md` |
| S1, T6, G3, C3, L4 | `scripts/check_contract_artifacts.py`; `config/contract-artifact-expectations.json`; `tests/inventory/test_contract_artifacts.py` |
| S2, S3 | `docs/chains/rh/hardening/mutation-evidence-protocol.md` |
| T1, T2, T4, T5 | `tests/core/teller/test_teller_deposit.py` |
| T3 | `tests/core/teller/test_teller_deposit.py` |
| T7, G6, D1 | `docs/chains/rh/hardening/asset-admission-assumptions.md` |
| G1, G2 | `tests/vaults/test_guarded_erc20.py` |
| G4 | `docs/chains/rh/hardening/guarded-consumer-inventory.md`; `tests/vaults/test_guarded_consumer_inventory.py` |
| G5, D2 | `docs/chains/rh/hardening/stock-backing-monitoring-runbook.md` |
| C1, C2 | `tests/core/creditEngine/test_stock_backing.py`; `docs/chains/rh/hardening/creditengine-gas-measurements.md` |
| C4 | `docs/chains/rh/hardening/hardening-pass-report.md` |
| R1 | `scripts/proposals/__init__.py`; `scripts/proposals/ledger_robinhood_profile.py`; `scripts/proposals/ledger-robinhood-profile.json`; `tests/deployment_profiles/test_ledger_robinhood_profile.py` |
| R2 | `scripts/proposals/build_ledger_artifact_bundle.py`; `tests/deployment_profiles/test_ledger_artifact_bundle.py`; `docs/chains/rh/hardening/ledger-local-artifact-bundle.json` |
| L1 | `tests/core/teller/test_teller_action_block.py` |
| L2, L3a | `tests/data/test_ledger_action_block.py` |
| L3b | `tests/deployment_profiles/test_ledger_robinhood_profile.py` |
| L5 | `docs/chains/rh/hardening/release-packet-evidence-checklist.md`; `docs/chains/rh/hardening/hardening-pass-report.md` |
| L6, D3 | `docs/chains/rh/hardening/ledger-monitoring-runbook.md` |
| R5 | `scripts/proposals/lootbox_deployment_profiles.py`; `scripts/proposals/lootbox-deployment-profiles.json`; `tests/deployment_profiles/test_lootbox_deployment_profiles.py` |
| X1 | `tests/deployment_profiles/test_lootbox_deployment_profiles.py` |
| X2, X3 | `tests/core/lootbox/test_underscore_rewards.py` |
| X4, D4 | `docs/chains/rh/hardening/lootbox-distribution-monitoring.md` |
| X5, D7 | `docs/chains/rh/hardening/release-packet-evidence-checklist.md` |
| D5 | `docs/chains/rh/hardening/ledger-replay-policy.md` |
| D6 | `docs/chains/rh/hardening/last-touch-consumer-semantics.md` |
| Phase 9 | `docs/chains/rh/hardening/hardening-pass-report.md` |
| Reviewer remediation | `config/block-clock-inventory.json`; `scripts/check_block_clock_inventory.py`; `tests/inventory/test_block_clock_inventory.py` |

The reviewer-remediation row supersedes the original Phase 0 expectation that
`config/block-clock-inventory.json` would remain absent. Owner-directed review
found scanner-visible cadence metadata in files created by this pass. Those
metadata echoes are inventoried explicitly; they do not add a production
clock dependency or change any production semantic classification.
