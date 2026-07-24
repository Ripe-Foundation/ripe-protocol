# Robinhood deployment-support specification

- Status: working draft for the early owner-review checkpoint
- Review status: independent reviewer findings incorporated; early checkpoint approved
- Scope completed: Phase A and the proposed Phase B network-profile schema
- Scope not started: Phases C–H and Deliverable B
- Starting commit: `68a76dcd5ea9b95b9148d3e6ebdd12107d5cc88e`
- Track branch: `rh-track-7-deployment-support`
- Worktree: `/Users/wigglez/dev/ripe-protocol-track-7-deployment-support`
- Evidence date: 2026-07-23, America/Denver

## 1. Checkpoint boundary

This is Deliverable A in working-draft form at the optional early checkpoint
defined by `track-7-robinhood-deployment-support.md`. It records:

- the Phase A audit of the existing deployment system;
- the dependency-security preflight;
- a proposed Phase B network-profile schema;
- a proposed Base/Robinhood network-profile table;
- the primary-source record;
- unresolved facts and owner gates; and
- abstraction decisions that would materially shape Phases C–H.

It does **not** approve a Robinhood deployment, choose a production operator,
authorize dependency changes, or approve production values. On 2026-07-23, the
owner authorized this checkpoint commit, selected one shared Robinhood
migration-source directory with separate testnet/mainnet histories, approved
D-001, D-002, D-004, D-009, D-013, and D-014 as specification directions, and
authorized continuation through Phases C–H. The authorization did not permit
push, merge, or implementation.

No code, dependency, default, migration, manifest, ABI, test, or CI file was
modified. No secret value was read or stored. No transaction, deployment,
signature, verification submission, Safe proposal, or other state-changing
network action was performed.

## 2. Kickoff and frozen inputs

### 2.1 Worktree record

| Check | Result |
| --- | --- |
| Integration worktree | Clean at kickoff |
| `rh` integration commit | `68a76dcd5ea9b95b9148d3e6ebdd12107d5cc88e` |
| Brief present in integration commit | Yes |
| Track branch | `rh-track-7-deployment-support` |
| Track worktree | `/Users/wigglez/dev/ripe-protocol-track-7-deployment-support` |
| Track worktree initial state | Clean at the starting commit |
| Latest numeric migration identifier | `2026043000` |
| Latest numeric step-manifest identifier | `2026043000` |

### 2.2 Planning-baseline reconciliation

The brief names planning baseline
`758f45f5455fd7c05b25533d2d748769bcfc49c2`, while the required kickoff
occurred at `68a76dcd5ea9b95b9148d3e6ebdd12107d5cc88e`. The two intervening commits
were:

| Commit | Change |
| --- | --- |
| `e6c90d3` | Added the Track 6 S1, Track 6 S2, and Track 7 briefs |
| `68a76dc` | Added the dependency-security gate to the Track 6 S1 and Track 7 briefs |

`git diff --name-status 758f45f..68a76dc` contains only
`docs/chains/rh/track-6-s1-clock-harness.md`,
`docs/chains/rh/track-6-s2-checked-clock-inventory.md`, and
`docs/chains/rh/track-7-robinhood-deployment-support.md`. No audited contract,
configuration, deployment script, parameter script, migration, manifest, ABI,
dependency, test, or CI file changed between the planning baseline and kickoff.
The runtime audit therefore describes the same implementation at both commits,
while this specification uses the stricter brief at the required kickoff
commit.

### 2.3 Frozen input hashes

The SHA-256 digest is the portable evidence hash. The Git blob is included for
repository-local reconciliation.

| Input | SHA-256 | Git blob |
| --- | --- | --- |
| `docs/chains/rh-summary.md` | `a17820672b62b67935d06f88ad9d6fb5d6678f2aa23b85cc6b74bc4da994e182` | `be6a8a092710523aeafa527ddcbf8c8c8a2ea2f3` |
| `docs/chains/rh/component-matrix.md` | `9f4f33785d577461d17f89f0831e8e88b339e160509a4589e16bc5967364f2ec` | `1f5e947bcdd4033ec450926012c5143b1fcf48ba` |
| `docs/chains/rh/shared-block-clock-specification.md` | `98a8afb992cedb749543d986544504c42c7e9b0d57ec2eb72154ea5dad95fb8d` | `9ccd940fd6e40fb8b0bd697d446714cc31647a12` |
| `docs/chains/rh/block-clock-validation-plan.md` | `e3f5d73fa9588aba28ac8823b74c5d523d1e0e6451d29d47f352a87fe03371f2` | `0aa10e11023dca77bfaea97c1b2ab475e5544149` |
| `migration_history/base-mainnet/v1/current-manifest.json` | `06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00` | `ed2c72fb2444ac76c636a7107e53c1420567fedc` |
| `requirements.txt` | `18df0aad224f2a10febc9e155e4a530e1000ec553916c8ef78dc9859c6c92ba0` | `d5593e6634a43ea3a495534e4d871d11e04a1bef` |

### 2.4 Required integrated inputs

The starting commit contains the reviewed planning/evidence inputs named by the
brief, including:

- `docs/chains/rh-summary.md`;
- `docs/chains/rh/component-matrix.md`;
- `docs/chains/rh/block-number-inventory.md`;
- `docs/chains/rh/shared-block-clock-specification.md`;
- `docs/chains/rh/block-clock-validation-plan.md`;
- the Track 1 CCIP public/question/decision records;
- the Track 2 stock-transfer evidence;
- the Track 4 USDG evidence and decision record;
- the Track 5 vault comparison, decision, and fix records;
- all committed track briefs in `docs/chains/rh/`; and
- the Track 6 S1 and S2 specifications.

The presence of an input is not approval to implement it. The controlling
architecture remains a local Robinhood deployment of protocol, governance, and
positions with only GREEN and RIPE bridged. The superseded federated deployment
is not an implementation source.

### 2.5 Cross-track readiness at this checkpoint

| Input | Current implication for Track 7 | Gate |
| --- | --- | --- |
| Track 1, CCIP | Direct BurnMint topology; the pool is the direct mint caller. Exact supported release, inheritance, registration, roles, limits, and lifecycle remain pending. | External confirmation and owner approval before implementation or release freeze |
| Track 2, stock transfer | Evidence exists, but launch-asset and live-environment applicability must be frozen for the selected release. | Owner/release review |
| Track 4, USDG | Existing Chainlink-feed direction and disabled-by-default PSM posture are recorded. Implementation, parameters, risk gates, and SavingsGreen disposition are not complete. | Owner/risk approval |
| Track 5, vault | Rebase/Shares accounting is the preferred direction, but the vault is not approved for deployment unchanged and remediations remain. | Owner/security approval |
| Track 6, S1/S2 | Specifications exist but are still inputs, not proof that implementation or validation has landed. | Reconcile exact implementation commits before Phases C–H |
| Track 8, vault change | Brief-only post-kickoff input at `be6a759`; it assigns Track 7 exact Robinhood migration IDs, namespaces, manifests, and deployment tooling while reserving vault-specific sequencing for Track 8. | Reconcile reviewed Track 8 outputs before finalizing Phase C vault rows or migration reservations; route collisions to the owner |

### 2.6 Parallel-input reconciliation

During checkpoint revision, integration `rh` advanced from the frozen starting
commit to `be6a759e15e763b633feefdce91cf8f3ee31a10e` at
`2026-07-23T20:05:10-06:00`. The delta contains only the new
`docs/chains/rh/track-8-stock-token-vault-change.md` brief, with SHA-256
`c885c25f5a19f0531a15ce947534a4a054bf6e18ef7f198734d879dfd6a52637`.

No Track 8 implementation or owned output exists in that commit, and no audited
runtime, migration, manifest, ABI, dependency, test, or CI file changed. The
Phase A audit and Phase B facts therefore remain frozen to `68a76dc`; the Track
8 brief is recorded only as a pending input for Phases C–H. It does not collide
with this track's owned document path. This worktree was not rebased, merged, or
cherry-picked.

## 3. Phase A audit

### 3.1 Current execution flow

The existing deployment path is:

`scripts/migrate.py` CLI and environment selection → `scripts/utils/deploy_args.py`
and `config/BluePrint.py` → account selection in `scripts/migrate.py` /
`migration_helpers.py` → `MigrationRunner` discovers and imports migration
modules → `Migration` executes or positionally skips transaction calls → current
and step manifests are rewritten during execution → `scripts/verify.py`
independently submits verification requests.

This is a Base-mainnet-oriented script stack, not a network-neutral deployment
system. The Base namespace itself contains legitimate Base-specific assumptions;
the defect would be silently copying those assumptions into Robinhood profiles.

### 3.2 CLI and network selection

| Finding | Exact source | Classification | Consequence |
| --- | --- | --- | --- |
| Environment defaults to `v1`, while help text describes a different default. | `scripts/migrate.py:31-35` | Defect | Operator instructions and actual history selection can diverge. |
| `--start` and `--end` default to string `"0"` despite help text describing resume/latest behavior. | `scripts/migrate.py:36-49` | Defect | The CLI defeats `MigrationRunner`'s intended resume behavior and starts from the first migration unless explicitly constrained. |
| Blueprint defaults to Base. | `scripts/migrate.py:54-57` | Design limitation / Robinhood blocker | An omitted flag silently selects Base assumptions. |
| Chain choices/default/help are internally inconsistent and Base-centric. | `scripts/migrate.py:59-64` | Defect / Robinhood blocker | Unsupported environments appear selectable and the default is not safely communicated. |
| Explorer setup unconditionally indexes `ETHERSCAN_API_KEYS[chain]` and `ETHERSCAN_URLS[chain]`, while the key map contains only `base-mainnet` and `base-sepolia`. | `scripts/migrate.py:84-95`, `scripts/migrate.py:297-298` | Defect / Robinhood blocker | `local`, `eth-mainnet`, and `eth-sepolia` all reach a `KeyError` if earlier requirements are satisfied. Local deployment through this CLI is currently unreachable even apart from the incomplete local blueprint. |
| A supplied RPC bypasses URL construction; otherwise the tool constructs an Alchemy URL from one token. | `scripts/migrate.py:258-259` | Design limitation / Robinhood blocker | Provider and network selection are coupled; a missing token can become a URL ending in literal `None`. |
| The RPC URL is logged in full. | `scripts/migrate.py:279` | Security defect | Embedded provider credentials can be written to terminals or logs. |
| No runtime chain-ID assertion exists before execution. | `scripts/migrate.py:258-318` | Robinhood blocker | A valid endpoint for the wrong chain can receive deployment transactions. |
| There is no explicit immutable plan, dry-run gate, irreversible-action confirmation, or configured finality policy before live execution. | `scripts/migrate.py:300-318` | Design limitation / Robinhood blocker | Operators cannot prove what is about to run or that it finalized under an approved policy. |
| Console choices cover Base/Ethereum only; blueprint input is stored but does not configure the session. | `scripts/console.py:239-255` | Design limitation | Console behavior does not share a canonical network abstraction. |
| Console logs the first 50 characters of the RPC endpoint. | `scripts/console.py:279-282` | Security defect | Credential-bearing endpoints may still be partially exposed. |
| Console fork mode permits dirty state. | `scripts/console.py:285-293` | Design limitation | Useful for exploration, but unsuitable as deployment evidence without an explicit evidence mode. |

Prompt and confirmation behavior is also not a safe live-deployment gate:

| Finding | Exact source | Classification | Consequence |
| --- | --- | --- | --- |
| `param_prompt` prompts only when the parsed value equals the configured default. Parameters with a non-`None` default are treated as optional and keep the default unless `--ask` is set. | `scripts/migrate.py:98-118`, `scripts/migrate.py:146-147` | Design limitation | Explicitly supplying the default is indistinguishable from omitting it, and normal noninteractive use silently accepts operational defaults. |
| Dependency-controlled prompts become enabled when any dependency matches rather than requiring all declared dependencies to match. The current `end_timestamp` prompt has only one dependency, so this is latent. | `scripts/migrate.py:120-132`; prompt declaration at `scripts/migrate.py:46-52` | Latent defect | Adding a multi-condition prompt later could expose it under the wrong conditions. |
| Input hiding is enabled only for a parameter literally named `password`, but no such CLI parameter exists. In particular, an RPC URL prompt is visible. | `scripts/migrate.py:26-30`, `scripts/migrate.py:134-141` | Security limitation | A credential-bearing RPC URL can be displayed during entry and is later logged in full. |
| `--ask` is only a default-value prompt switch; there is no reviewed plan digest, network/chain acknowledgment, irreversible-action confirmation, or post-signing confirmation boundary. | `scripts/migrate.py:98-147`, `scripts/migrate.py:300-318` | Robinhood blocker | Interactive prompting must not be mistaken for approval or live-deployment safety. |

### 3.3 Configuration and blueprint audit

| Finding | Exact source | Classification | Consequence |
| --- | --- | --- | --- |
| `ADDYS` and `PARAMS` define Base plus a partial local profile. | `config/BluePrint.py:1-96` | Design limitation | Configuration is a set of parallel dictionaries, not one validated profile. |
| `CORE_TOKENS`, `CURVE_PARAMS`, and `YIELD_TOKENS` are Base-only. | `config/BluePrint.py:99-245` | Design limitation / Robinhood blocker | Local and Robinhood configurations cannot satisfy the current constructor. |
| `BluePrint` unconditionally indexes every map. | `scripts/utils/deploy_args.py:4-11` | Defect | `blueprint="local"` fails even though local appears supported elsewhere. |
| `DeployArgs` carries loosely typed values but no canonical chain ID, verifier, fee, finality, account capability, or history identity. | `scripts/utils/deploy_args.py:14-20` | Design limitation / Robinhood blocker | Critical settings can disagree across scripts. |
| Parameter tooling hard-codes Base addresses, Base RPC construction, Base tokens, Base timing, and Base explorer configuration. | `scripts/params/params_utils.py:28-29`, `:76-83`, `:187-216`, `:275-280`, `:310` | Design limitation | Parameter reports are Base snapshots and must not be treated as Robinhood deployment inputs. |
| Default regeneration writes `contracts/config/DefaultsBase.vy`. | `scripts/params/regenerate_defaults.py:1120-1128` | Scope boundary | It is a state-changing repository operation and was not run in this specification track. |

### 3.4 Account, signing, and secret-handling audit

| Finding | Exact source | Classification | Severity / consequence |
| --- | --- | --- | --- |
| `BASESCAN_API_KEY` is read eagerly at import. | `scripts/migrate.py:84-87` | Defect | `python -m scripts.migrate --help` and `python -m scripts.verify --help` fail when the unrelated Base key is absent. |
| Safe and Ledger imports are commented out, but CLI branches remain. | `scripts/migrate.py:10-11`, `:261-275` | Defect | Safe and Ledger selections can leave `sender` undefined; fork paths may dereference it before assignment. |
| The private-key loader silently falls back to a public Anvil test key. | `scripts/utils/migration_helpers.py:17`, `:45-53` | Critical security defect | A missing production key can select a known public key instead of stopping. All live deployment must fail closed until removed and regression-tested. |
| RPC endpoints are logged in full by migration and by Ledger support. | `scripts/migrate.py:279`; `scripts/utils/ledger_account.py:77` | Security defect | Provider tokens embedded in URLs can leak. |
| Ledger fallback construction can default chain ID to 1 and use legacy gas price when fields are absent. | `scripts/utils/ledger_account.py:146-155` | Defect / Robinhood blocker | A transaction can be signed with the wrong chain identity or fee semantics. |
| Safe chain detection does not include Robinhood. | `scripts/utils/safe_account.py:34-49` | Robinhood blocker | Safe support cannot be inferred from current code. |
| Safe helper error paths can fall back to hash/nonce sentinel values. | `scripts/utils/safe_account.py:235-249` | Security defect | Proposal evidence can become ambiguous after provider/API failure. |

No existing account backend is approved for a Robinhood live deployment. Phase B
therefore models required account capabilities and leaves Robinhood live account
backends empty until owner approval.

### 3.5 Migration discovery, progression, and failure behavior

| Finding | Exact source | Classification | Consequence |
| --- | --- | --- | --- |
| Discovery uses `os.listdir`, accepts numeric prefixes, and sorts only by numeric prefix. | `scripts/utils/migration_runner.py:104-118` | Defect | Duplicate IDs retain filesystem enumeration order and are not rejected. |
| Base contains duplicate migration ID `2025071506`. | `migrations/base-mainnet/2025071506_BondRoom.py`; `migrations/base-mainnet/2025071506_Teller.py` | Defect | Ordering is not uniquely identified and cannot be reproduced safely. |
| Intended resume logic runs only when `start` is `None`; the CLI supplies `"0"`. | `scripts/utils/migration_runner.py:77-85`; `scripts/migrate.py:36-39` | Defect | Default CLI behavior replays from the start rather than resuming. |
| Latest-manifest scanning accepts `current-manifest.json` in its regex and then attempts integer conversion. | `scripts/utils/migration_runner.py:136-153` | Defect | A helper intended to find the latest numeric manifest can fail on the canonical current filename. |
| Migration modules are dynamically imported and their `migrate` callable executed. | `scripts/utils/migration_runner.py:87-91` | Design characteristic | Source commit and module identity must be frozen before planning. |
| Current manifest and retry log parse errors are broadly swallowed. | `scripts/utils/migration.py:29-40` | Defect | Corruption is treated like an empty deployment. |
| Contract registration writes manifests immediately, before the whole migration is complete. | `scripts/utils/migration.py:55-61`, `:218-234` | Critical evidence defect | A partial deployment can overwrite `current-manifest.json` and look canonical. |
| Retry decisions use transaction position and string logs, not semantic step identity or observed chain state. | `scripts/utils/migration.py:163-210`, `:237-249` | Design limitation / Robinhood blocker | Resume/recovery is unsafe after source changes, partial execution, or reorgs. |
| Configuration-only `execute` steps are not represented in the manifest. | `scripts/utils/migration.py:163-210`, `:218-234` | Evidence limitation | Deployment evidence omits roles, registrations, and parameter changes. |
| Completion deletes the log and writes no terminal completion marker. | `scripts/utils/migration.py:108-118` | Evidence limitation | There is no durable proof that the migration completed. |
| `ignore_logs` / `is_retry` semantics and help text are inverted or ambiguous. | Prompt definition at `scripts/migrate.py:71-75`, option at `scripts/migrate.py:210-216`, inversion at `scripts/migrate.py:276`, and behavior at `scripts/utils/migration.py:237-242` | Defect | An operator can misunderstand whether prior steps will be skipped. |
| Transaction execution retries broad exceptions up to 20 times, returns `None` on exhaustion, and special-cases a `"NoneType"` substring. | `scripts/utils/migration_helpers.py:56-89` | Critical execution defect | Failure can be masked and a non-idempotent action can be retried without a receipt-aware policy. |
| Prior addresses are trusted without bytecode or state reconciliation. | `scripts/utils/migration.py:100-106` | Design limitation | Resume does not establish that a recorded address is the intended deployment. |

### 3.6 Existing migration and history conventions

At the starting commit:

- `migrations/base-mainnet/` contains 62 migration files.
- `migration_history/base-mainnet/v1/` contains 57 numeric step manifests.
- `current-manifest.json` contains 48 named contract records.
- Migration IDs without same-ID step manifests are `2000`, `2003`,
  `2025071507`, and `2025102700`.
- No numeric step-manifest ID lacks a corresponding migration file.
- The duplicate migration ID is `2025071506`.
- Early step manifests are cumulative, while later step manifests can contain
  only changed contracts. The repository therefore does not have one consistent
  snapshot-versus-delta convention.
- The current manifest includes three address-only external records:
  `GreenPool`, `RipePoolCurve`, and `RipePoolAero`.
- The Base migration tree intentionally contains Base token, pool, oracle,
  protocol, and operator addresses. A Robinhood namespace must not inherit them
  by default.
- `migrations/base-mainnet/2026011400_EndaomentPSM.py` encodes Base USDC,
  yield-vault, and time assumptions. Track 4 decisions must be applied through a
  Robinhood-specific, reviewed path instead of copying this migration.

There is no evidence that missing numeric manifests necessarily mean failed
deployments; the current format cannot distinguish skipped, non-contract-only,
failed, superseded, or deliberately uncommitted steps. Phases C–H must not infer
their disposition without repository/chain reconciliation.

### 3.7 Manifest evidence audit

Current contract entries may contain address, ABI, compiler standard input under
the misleading key `solc_json`, encoded constructor arguments, and source path.
External entries may contain only an address
(`scripts/utils/migration_helpers.py:137-184`).

The current manifest does not record:

- a schema version or artifact kind;
- network-profile ID, chain ID, or genesis identity;
- canonical source commit and dirty-worktree status;
- dependency or compiler artifact hashes;
- migration and semantic step identity;
- transaction hash, receipt status, block, confirmations, or finality result;
- deployer, signer backend, Safe proposal identity, or approved role;
- bytecode/runtime-code hash and constructor arguments in a normalized schema;
- configuration calls, roles, capabilities, ownership, or pause state;
- verification provider, request/result evidence, or browser link;
- supersession/progression links or a terminal completion state; or
- explicit local-only versus committable evidence disposition.

`JsonFile.save()` is a normal direct JSON write with no atomic rename, schema
validation, lock, or content digest (`scripts/utils/json_file.py:1-27`).

### 3.8 Verification and ABI export audit

| Finding | Exact source | Classification | Consequence |
| --- | --- | --- | --- |
| Verification imports `migrate.py`, inheriting its eager BaseScan-key requirement. | `scripts/verify.py:4` | Defect | Help and non-Base verification fail before network selection. |
| Both verification branches use `ETHERSCAN_API_KEY`, while migration expects `BASESCAN_API_KEY`. | `scripts/verify.py:45-55`; `scripts/migrate.py:84-87` | Defect | Credential names and ownership are inconsistent. |
| Verification iterates every current-manifest contract without schema/capability filtering and stores no durable result. | `scripts/verify.py:57-72` | Design limitation | Address-only or unsupported-language entries can fail; success cannot be audited later. |
| Verifier handling of an unknown chain is inconsistent rather than safely rejected. The full `verify_from_manifest` path first raises a `KeyError` while building the browser URL; independently, `is_contract_verified` and later chain-ID selection silently default to Ethereum mainnet. | `scripts/utils/verify_etherscan.py:27-30`, `:45-57` | Defect / latent critical routing hazard | The current end-to-end path crashes, but direct helper use or future divergence between the browser and chain-ID maps can query or submit with chain ID 1. One explicit supported-profile check must replace both behaviors. |
| `base-goerli` is assigned chain ID `84532`, the Base Sepolia ID. | `scripts/utils/verify_etherscan.py:7-14` | Defect | Legacy network identity is incorrect. |
| Requests have no explicit timeout, retry classification, or HTTP-status handling. | `scripts/utils/verify_etherscan.py:39-42`, `:75-76`, `:97-98` | Reliability defect | Network failures can hang or be misclassified. |
| Verification hard-codes Vyper `0.4.3`, standard JSON, optimization, and Etherscan-style behavior. | `scripts/utils/verify_etherscan.py:54-70` | Design limitation / Robinhood blocker | Solidity artifacts and Blockscout capabilities are not modeled. |
| Polling is fixed at ten attempts with five-second sleeps. | `scripts/utils/verify_etherscan.py:94-110` | Design limitation | Provider rate/finality behavior is not configurable or recorded. |
| ABI export scans Vyper only, names outputs by source stem, catches compile failures, and exits successfully. | `scripts/export_abis.py:16-49` | Evidence defect | Missing ABIs or stem collisions can be mistaken for a complete rebuild. |
| ABI export does not remove stale output. | `scripts/export_abis.py:16-49` | Evidence defect | Old artifacts can survive a rebuild. |

A read-only export to a temporary directory produced 49 ABI files and printed
compilation failures for nine source files: `DeptBasics`, `TimeLock`,
`PriceSourceData`, `AddressRegistry`, `Erc4626Token`, `BasicVault`,
`SharesVault`, `StabVault`, and `VaultData`. The repository contains 50 ABI
files, including stale-looking `scripts/abis/DefaultsBaseSepolia.json`, which
was not generated by that run. This is evidence of incompleteness, not a request
to update committed ABIs in this track.

### 3.9 Test and CI inventory

- There is no repository-level `pyproject.toml`, `pytest.ini`, `setup.cfg`, or
  `tox.ini`; pytest plugins are registered in `tests/conftest.py`.
- `tests/conf_env.py:14-28` eagerly reads explorer keys and constructs Base and
  Ethereum RPC URLs, so unrelated local test collection depends on external
  credentials.
- Fork selection covers local, Ethereum mainnet, and Base
  (`tests/conf_env.py:77-84`), not Robinhood.
- RPC override handling can use an uninitialized `block_number` for an
  unrecognized fork (`tests/conf_env.py:181-187`).
- No focused suite covers migration discovery, duplicate IDs, resume/recovery,
  manifest atomicity/schema, verifier routing, secret-safe logging, account
  capability gates, or chain-ID mismatch.
- Existing probe tooling tests cover Vyper file loading/export exclusions, not
  deployment evidence.
- The starting commit has no `.github/workflows/` directory. Track 7 must define
  validations without assuming a current CI execution environment.

### 3.10 Consolidated release-blocking findings

| ID | Finding | Type | Gate |
| --- | --- | --- | --- |
| A-001 | Missing private key silently selects a public test key. | Critical defect | Block every live deployment until removed and regression-tested. |
| A-002 | RPC credentials can be logged. | Security defect | Block rehearsal/live execution until secret-safe logging is proven. |
| A-003 | No strict chain-ID assertion exists. | Robinhood blocker | Require exact runtime chain ID before signing or submitting. |
| A-004 | Safe and Ledger CLI paths are nonfunctional/unapproved. | Defect / owner gate | Select and validate an account backend; do not infer support. |
| A-005 | Duplicate migration IDs are accepted. | Determinism defect | Reject duplicates before planning. |
| A-006 | Default CLI progression can replay from the first migration. | Execution defect | Replace positional/default ambiguity with explicit reviewed plan. |
| A-007 | Broad transaction retries can mask final failure. | Critical defect | Require receipt-aware, idempotency-aware failure behavior. |
| A-008 | Partial execution rewrites the canonical current manifest. | Evidence defect | Use staged/atomic evidence and terminal status before promotion. |
| A-009 | Manifest lacks network, source, transaction, finality, configuration, and progression evidence. | Design limitation | Define and validate a versioned manifest schema. |
| A-010 | Unknown verifier handling is inconsistent: full verification crashes on the browser map, while independent chain-ID lookups default to Ethereum mainnet. | Defect / latent critical routing hazard | Validate one supported profile/provider pair and fail closed before constructing links or requests. |
| A-011 | Verification is Etherscan/Vyper-only and results are not persisted. | Robinhood blocker | Introduce explicit provider/language adapters and evidence records. |
| A-012 | ABI export can succeed with failures and retain stale files. | Reproducibility defect | Require clean deterministic rebuild and completeness checks. |
| A-013 | Base-specific dictionaries and scripts are the effective network model. | Design limitation | Introduce one validated profile registry without changing Base defaults implicitly. |
| A-014 | No explicit plan, confirmation, finality, or rollback evidence gate exists. | Operational blocker | Define fail-closed policies before any live rehearsal. |
| A-015 | Deployment tooling has no focused regression suite. | Validation blocker | Phase G must specify tests before implementation approval. |
| A-016 | Open dependency alerts affect HTTP, environment, compiler/build, and test paths. | Security blocker | Resolve or explicitly accept through the dependency-security gate below. |
| A-017 | Migration unconditionally indexes Base-only explorer dictionaries for every selected chain. | Execution defect / Robinhood blocker | Local, Ethereum, and any future Robinhood profile remain unreachable until explorer setup is capability-gated. |

## 4. Dependency-security preflight

### 4.1 Source and result

At `2026-07-24T01:39:28Z` (`2026-07-23T19:39:28-06:00`), a read-only,
authenticated query of the repository Dependabot alerts returned 13 open alerts,
all against `requirements.txt`: six high, six medium, and one low. No secret
content was read or stored.

| Alert | Severity | Package / pinned version | Advisory | Affected / first fixed | Deployment relevance |
| --- | --- | --- | --- | --- | --- |
| `#27` | Medium | `pymdown-extensions 10.16.1` | [GHSA-62q4-447f-wv8h](https://github.com/advisories/GHSA-62q4-447f-wv8h), CVE-2026-46338 | `<=10.21.2` / `10.21.3` | Documentation build; not a transaction-path gate by itself |
| `#26` | Medium | `idna 3.10` | [GHSA-65pc-fj4g-8rjx](https://github.com/advisories/GHSA-65pc-fj4g-8rjx), CVE-2026-45409 | `<3.15` / `3.15` | HTTP/RPC hostname handling |
| `#25` | High | `urllib3 2.5.0` | [GHSA-qccp-gfcp-xxvc](https://github.com/advisories/GHSA-qccp-gfcp-xxvc), CVE-2026-44431 | `<2.7.0` / `2.7.0` | HTTP stack used by deployment/verifier tooling |
| `#24` | Medium | `python-dotenv 1.2.1` | [GHSA-mf9w-mj56-hr94](https://github.com/advisories/GHSA-mf9w-mj56-hr94), CVE-2026-28684 | `<1.2.2` / `1.2.2` | Deployment environment handling; current code uses load behavior, not the advisory's write path |
| `#23` | Medium | `pytest 8.4.2` | [GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g), CVE-2025-71176 | `<9.0.3` / `9.0.3` | Required validation harness; major-version transition |
| `#22` | Low | `Pygments 2.19.2` | [GHSA-5239-wwwm-4pmq](https://github.com/advisories/GHSA-5239-wwwm-4pmq), CVE-2026-4539 | `<2.20.0` / `2.20.0` | Console/docs; not a live-deployment gate by itself |
| `#21` | Medium | `requests 2.32.5` | [GHSA-gc5v-m9x4-r6x2](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2), CVE-2026-25645 | `<2.33.0` / `2.33.0` | Direct verifier/Safe/probe HTTP client |
| `#19` | High | `cbor2 5.7.0` | [GHSA-3c37-wwvx-h642](https://github.com/advisories/GHSA-3c37-wwvx-h642), CVE-2026-26209 | `<=5.8.0` / `5.9.0` | Vyper compiler/build dependency |
| `#18` | High | `wheel 0.45.1` | [GHSA-8rrh-rw8j-w5fx](https://github.com/advisories/GHSA-8rrh-rw8j-w5fx), CVE-2026-24049 | `<=0.46.1` / `0.46.2` | Compiler/build environment |
| `#16` | High | `urllib3 2.5.0` | [GHSA-38jv-5279-wg99](https://github.com/advisories/GHSA-38jv-5279-wg99), CVE-2026-21441 | `<2.6.3` / `2.6.3` | HTTP stack |
| `#15` | Medium | `cbor2 5.7.0` | [GHSA-wcj4-jw5j-44wh](https://github.com/advisories/GHSA-wcj4-jw5j-44wh), CVE-2025-68131 | `<5.8.0` / `5.8.0` | Vyper compiler/build dependency |
| `#14` | High | `urllib3 2.5.0` | [GHSA-2xpw-w6gg-jr37](https://github.com/advisories/GHSA-2xpw-w6gg-jr37), CVE-2025-66471 | `<2.6.0` / `2.6.0` | HTTP stack |
| `#13` | High | `urllib3 2.5.0` | [GHSA-gm62-xv2j-4w53](https://github.com/advisories/GHSA-gm62-xv2j-4w53), CVE-2025-66418 | `<2.6.0` / `2.6.0` | HTTP stack |

Pin locations in the frozen lock include `cbor2` at
`requirements.txt:21-22`, `idna` at `requirements.txt:97-98`, Pygments at
`requirements.txt:188-193`, pymdown-extensions at
`requirements.txt:195-196`, pytest at `requirements.txt:197-200`,
python-dotenv at `requirements.txt:203-206`, requests at
`requirements.txt:219-223`, titanoboa at `requirements.txt:241-242`, urllib3
at `requirements.txt:260-261`, Vyper at `requirements.txt:264-267`, and wheel
at `requirements.txt:272-273`.

### 4.2 Smallest credible refresh slice

The smallest candidate refresh that clears all high and medium alerts is:

| Package | Candidate minimum |
| --- | --- |
| `requests` | `2.33.0` |
| `urllib3` | `2.7.0` |
| `idna` | `3.15` |
| `python-dotenv` | `1.2.2` |
| `pytest` | `9.0.3` |
| `cbor2` | `5.9.0` |
| `wheel` | `0.46.2` |
| `pymdown-extensions` | `10.21.3` |

`Pygments 2.20.0` is required only if the owner selects a zero-open-alert
policy; the low alert is not independently a deployment blocker.

The implementation review should treat this as two approval slices:

| Slice | Packages | Gate |
| --- | --- | --- |
| A: non-pytest alert-clearing candidate | `requests`, `urllib3`, `idna`, `python-dotenv`, `cbor2`, `wheel`, and `pymdown-extensions` | Complete upstream release-note/behavior review, resolve in a clean environment, prove compiler/artifact and HTTP behavior, and obtain security approval |
| B: pytest compatibility decision | `pytest 8.4.2` → at least `9.0.3` | Decide how to reconcile the Vyper `test` extra's `pytest<9` constraint, then deliberately update and reapprove the Track 6 S1 exact-version profile |
| Optional zero-alert slice | `Pygments 2.19.2` → at least `2.20.0` | Required only if the owner/security policy demands zero open alerts |

Slice A is intentionally **not** called mechanical. Its packages touch network,
environment, serialization/compiler, packaging, and documentation behavior and
still require compatibility evidence.

The checkpoint has not completed the required upstream release-note and
behavior-change review. That review is an explicit input to the separate pin
implementation slice:

| Package | Release-note / behavior review status | Mandatory review focus |
| --- | --- | --- |
| `requests` | Pending | Redirect, proxy, certificate, adapter, exception, and urllib3-integration behavior |
| `urllib3` | Pending | Connection pooling, retries, redirects, proxy/TLS behavior, and every change between `2.5.0` and `2.7.0` |
| `idna` | Pending | Hostname validation and normalization behavior |
| `python-dotenv` | Pending | Load, parse, interpolation, search-path, and environment-precedence behavior even though the advisory concerns write helpers |
| `cbor2` | Pending | Encoding/decoding compatibility, build wheels, and any effect on Vyper compiler artifacts |
| `wheel` | Pending | Build/installation behavior and reproducible environment metadata |
| `pymdown-extensions` | Pending | Markdown output and documentation-build compatibility |
| `pytest` | Pending beyond the known major-version constraint | Collection, plugin, fixture, warning/error, assertion, and Track 6 harness behavior across the 8→9 boundary |
| `Pygments` | Pending if selected | Console/docs rendering behavior |

At implementation kickoff, the reviewer must attach dated primary upstream
release/changelog sources and record the accepted behavior delta for every
selected package. A security-fixed version number alone is not sufficient.

This table is a security target, not authorization to edit pins. The refresh
must occur in a separate reviewed implementation slice by editing direct inputs
as needed and regenerating `requirements.txt` with the repository's recorded
Python and resolver provenance. Hand-editing only the compiled lock is not an
acceptable resolution.

### 4.3 Compatibility and rollback gate

- Keep `titanoboa 0.2.7` and `vyper 0.4.3` unless resolution or compatibility
  evidence requires changing them.
- `titanoboa 0.2.7` accepts Vyper `>=0.4.2` and does not declare an upper pytest
  bound. Vyper `0.4.3` package metadata constrains its `test` extra to
  `pytest<9`. Therefore the advisory-fixed pytest `9.0.3` is not a mechanical
  pin bump: it crosses a major version and conflicts with that optional test
  environment.
- Any change to titanoboa, Vyper, pytest, compiler transitive dependencies, or
  the resolver output must deliberately trip the Track 6 S1 exact-version gate.
  The gate must never be weakened to make a refresh pass.
- Required revalidation includes clean-environment resolution and audit, full
  local tests, compiler-version and artifact-hash comparison, deterministic ABI
  export, deployment-tooling unit tests, read-only fork subsets, and migration
  plan/dry-run tests once those facilities exist.
- Rollback is by reverting the isolated dependency commit/lock and recreating
  the environment from the prior frozen lock. Reusing an environment that has
  been upgraded in place is not rollback evidence.

**Checkpoint disposition:** dependency security is release-blocking. Owner and
security review must choose the pin-refresh/compatibility path before a
Robinhood deployment rehearsal. No dependency was changed in this track.

## 5. Phase B proposed network-profile abstraction

### 5.1 Design goals

One immutable, validated profile must be the sole source for CLI, migration,
console, verifier, parameter, test/fork, and evidence tooling. Network identity
must be explicit and must fail closed. A profile may describe a currently
unsupported operation, but it must not invent a fallback.

The profile must distinguish:

- network facts from operator policy;
- public read-only endpoints from credentialed deployment endpoints;
- browser URLs from verifier APIs;
- verifier provider type from chain identity;
- migration source namespace from evidence/history namespace;
- account capabilities from specific secret material; and
- configured confirmations from observed finality evidence.

### 5.2 Proposed schema

The following is a logical schema, not implementation syntax:

```yaml
schema_version: 1
id: unique-kebab-case-profile-id
display_name: human-readable-name
environment: local | test | mainnet

chain:
  chain_id: positive-integer
  native_token:
    symbol: string
    decimals: integer

rpc:
  deployment_url_env: env-var-name-or-null
  public_read_url: literal-public-url-or-null
  public_url_allowed_modes: [facts, read_only, fork]
  timeout_seconds: positive-integer
  read_retry_policy_id: policy-name
  require_chain_id_match: true

fees:
  transaction_type: rpc_dynamic | eip1559 | legacy
  estimator: rpc
  max_fee_policy_id: approved-policy-or-null
  priority_fee_policy_id: approved-policy-or-null

finality:
  required_confirmations: approved-positive-integer-or-null
  reorg_policy_id: approved-policy-or-null
  finalized_tag_supported: true | false | unknown

explorer:
  browser_url: url-or-null
  verifier:
    provider: blockscout | etherscan_v2 | unsupported
    api_url: url-or-null
    api_key_env: env-var-name-or-null
    keyless_allowed: true | false
    supported_languages: [vyper_standard_json, solidity_standard_json]
    rate_limit:
      requests: positive-integer-or-null
      interval_seconds: positive-integer-or-null
      burst: positive-integer-or-null
      source: documented_default | instance_confirmed | owner_policy | unknown

fork:
  source_url_env: env-var-name-or-null
  require_source_chain_id_match: true
  block_policy: explicit_pin | latest_for_local_exploration
  pinned_block_number: positive-integer-or-null
  allow_dirty_state: false
  allow_submission: false
  evidence_disposition: local_only | sanitized_committable

repository:
  blueprint_id: identifier-or-null
  defaults_id: identifier-or-null
  migration_dir: existing-or-proposed-path-or-null
  history_dir: existing-or-proposed-path-or-null
  legacy_aliases: []

operations:
  allowed_modes: [read_only, fork, plan, dry_run, live]
  live_account_backend_ids: []
  required_account_capabilities: []
  allow_dirty_source: false
  require_dependency_gate: true
  require_finality_policy: true
  confirmation:
    require_plan_digest: true
    require_network_and_chain_ack: true
    require_irreversible_action_ack: true
    allow_unattended_live_mode: false
```

Validation rules:

1. `id`, `chain.chain_id`, environment, repository namespace, and verifier
   provider are immutable within a release evidence bundle.
2. A live operation requires `deployment_url_env`; a public URL is never an
   implicit live fallback.
3. The runtime `eth_chainId` must exactly equal the configured integer before
   account loading, signing, simulation against live state, verification, or
   submission.
4. Missing RPC, finality, fee-cap, account-backend, dependency, or verifier
   policy fails closed for the operation that needs it.
5. Unknown chain, provider, language, or profile IDs fail closed; there is no
   Ethereum-mainnet fallback.
6. Environment-variable fields store names only. Profiles, logs, plans, and
   manifests never store secret values or credential-bearing URLs.
7. `migration_dir` and `history_dir` are separate identities. A profile cannot
   silently read or write another profile's history.
8. A proposed path is not created until its implementation slice is approved.
9. Legacy aliases may preserve an existing CLI spelling, but must resolve to one
   canonical profile with an explicit deprecation test. They cannot alias chain
   IDs, histories, or defaults.
10. A verifier adapter must declare the provider, API form, language capability,
    key mode, rate limit, and evidence fields; browser URL inference is forbidden.
11. Rate limits are interval-denominated. A documented default is not an
    instance guarantee; the effective explorer limit must be confirmed or an
    owner-approved conservative policy must apply.
12. A fork used as reproducible or committable evidence requires an exact source
    chain-ID match and pinned block. `latest` and dirty-state forks are
    exploration-only and their evidence remains local.
13. Fork mode never signs or submits to its source RPC. A fork profile with
    `allow_submission: true` is invalid.
14. Live mode requires a frozen plan digest, explicit network/chain
    acknowledgment, and irreversible-action acknowledgment. Generic `--ask`
    prompting does not satisfy those gates.

### 5.3 Proposed profile table

`Pending` means the profile must reject the affected operation until the owner
approves and implementation proves the value.

| Profile | Env | Chain ID / gas | RPC posture | Explorer / verifier | Repository identity | Live account / finality |
| --- | --- | --- | --- | --- | --- | --- |
| `local` | Local | Runtime-configured; ETH-like 18 decimals | Local runtime only; no public fallback | Unsupported; current CLI crashes at unconditional Base-only explorer setup | Current local blueprint is incomplete; migration/history paths are not established | Live forbidden; local test account only; finality immediate by local-runtime policy |
| `base-mainnet` | Mainnet | `8453`; ETH, 18 | Proposed `BASE_MAINNET_RPC_URL`; preserve current behavior only through an explicit compatibility path | BaseScan browser; Etherscan-v2 adapter; one normalized key-env policy pending | Existing `base` blueprint / `DefaultsBase`; `migrations/base-mainnet`; `migration_history/base-mainnet/v1` | Existing private-key path is not safe enough for release; approved backend and confirmation policy pending |
| `base-sepolia` | Test | `84532`; ETH, 18 | Proposed `BASE_SEPOLIA_RPC_URL` | BaseScan browser; Etherscan-v2 adapter | CLI advertises the chain, but no matching migration/history namespace exists; no implicit Base-mainnet reuse | Live deployment unsupported until paths, backend, and finality are approved |
| `robinhood-mainnet` | Mainnet | `4663`; ETH, 18 | `ROBINHOOD_MAINNET_RPC_URL` required for deployment. Official public RPC is read-only/facts/fork only. | `https://robinhoodchain.blockscout.com`; Blockscout API at `/api/`; keyless supported; documented default is 3 requests/minute without a key, but effective instance/key policy is pending; Vyper and Solidity standard JSON | Proposed `robinhood` blueprint / `DefaultsRobinhood`; shared proposed source `migrations/robinhood/`; isolated proposed history `migration_history/robinhood-mainnet/v1/`; paths not yet created | No backend approved; confirmation, reorg, fee-cap, and finality policies pending; live mode rejected |
| `robinhood-testnet` | Test | `46630`; ETH, 18 | `ROBINHOOD_TESTNET_RPC_URL` required for deployment. Official public RPC is read-only/facts/fork only. | `https://explorer.testnet.chain.robinhood.com`; Blockscout API at `/api/`; keyless supported; documented default is 3 requests/minute without a key, but effective instance/key policy is pending; Vyper and Solidity standard JSON | Same proposed Robinhood blueprint/default model and shared source `migrations/robinhood/`; isolated proposed history `migration_history/robinhood-testnet/v1/`; paths not yet created | No backend approved; confirmation, reorg, fee-cap, and finality policies pending; live mode rejected |

Fork-mode values are profile-specific:

| Profile | Fork source | Identity and block policy | Evidence disposition |
| --- | --- | --- | --- |
| `local` | None; this is already the local runtime | Not applicable | Dirty/local state is never release evidence |
| `base-mainnet` | `BASE_MAINNET_RPC_URL` | Require chain ID `8453`; exact block for reproducible evidence; `latest` only for local exploration | Pinned, clean, sanitized evidence may be committable under the later evidence policy |
| `base-sepolia` | `BASE_SEPOLIA_RPC_URL` | Require chain ID `84532`; same pinning rule | Same, once the profile has approved repository paths |
| `robinhood-mainnet` | `ROBINHOOD_MAINNET_RPC_URL`; official public RPC may be used only for local exploration | Require chain ID `4663`; exact block for reproducible evidence | Pinned, clean, sanitized evidence may be committable only with owner-approved retention |
| `robinhood-testnet` | `ROBINHOOD_TESTNET_RPC_URL`; official public RPC may be used only for local exploration | Require chain ID `46630`; exact block for reproducible evidence | Same |

Every fork profile sets `allow_submission: false`. Fork funding, impersonation,
and dirty-state mutations may support local experiments, but their outputs
remain local and cannot satisfy release evidence.

The owner selected one shared future migration source,
`migrations/robinhood/`, with distinct
`migration_history/robinhood-mainnet/v1/` and
`migration_history/robinhood-testnet/v1/` histories. This is a specification
decision, not permission to create the directories. Phase C must define the
shared graph and isolated evidence behavior before an implementation slice can
create them.

### 5.4 Current-to-proposed compatibility map

| Current behavior | Proposed handling |
| --- | --- |
| `base-mainnet` string spread across CLI, config, migrations, history, verifier, tests, and parameter scripts | One canonical `base-mainnet` profile consumed by all tools |
| `WEB3_ALCHEMY_API_KEY` interpolated into vendor URLs | Opaque full URL env var per profile; a time-bounded Base compatibility adapter only if owner requires it |
| `BASESCAN_API_KEY` in migration and `ETHERSCAN_API_KEY` in verifier | Verifier-specific `api_key_env` in the profile; no unrelated eager lookup |
| Unknown verifier chain crashes in the full path while independent chain-ID lookups default to Ethereum | One supported-profile/provider validation before any browser-link construction or request |
| Public RPC can be passed as live RPC | Profile-enforced operation modes; public Robinhood endpoints excluded from live mode |
| Safe/Ledger/private-key branches selected by CLI labels | Capability-based approved backend registry; an empty list means live deployment is unavailable |
| Current manifest path is inferred from chain/env strings | History path comes only from the selected profile and is embedded in evidence |

## 6. Primary-source and live read-only record

### 6.1 Robinhood network facts

Sources were retrieved on 2026-07-23 (America/Denver).

| Fact | Result | Authority |
| --- | --- | --- |
| Mainnet connection | Robinhood Chain, chain ID `4663`, ETH native gas, public RPC `https://rpc.mainnet.chain.robinhood.com`, explorer `https://robinhoodchain.blockscout.com` | [Robinhood: Connecting to Robinhood Chain](https://docs.robinhood.com/chain/connecting/), [Add network to wallet](https://docs.robinhood.com/chain/add-network-to-wallet/) |
| Testnet connection | Robinhood Chain Testnet, chain ID `46630`, ETH native gas, public RPC `https://rpc.testnet.chain.robinhood.com`, explorer `https://explorer.testnet.chain.robinhood.com` | [Robinhood: Connecting to Robinhood Chain](https://docs.robinhood.com/chain/connecting/), [Add network to wallet](https://docs.robinhood.com/chain/add-network-to-wallet/) |
| RPC production posture | Public endpoints are rate-limited; provider-specific RPC is recommended for production use. | [Robinhood: Connecting to Robinhood Chain](https://docs.robinhood.com/chain/connecting/), [Run a full node](https://docs.robinhood.com/chain/run-a-full-node/) |
| Platform | Robinhood Chain is based on Arbitrum Nitro/ArbOS and uses ETH for gas. | [Robinhood Chain documentation](https://docs.robinhood.com/chain/) |
| Test environment stability | Testnet availability and continuity are not a production guarantee. | [Robinhood Chain Terms of Service](https://docs.robinhood.com/chain/terms-of-service/) |
| Deployment/verification example | Robinhood documents explorer verification and a keyless Blockscout-style configuration. | [Robinhood: Deploy smart contracts](https://docs.robinhood.com/chain/deploy-smart-contracts/) |

Both official environments exist, so this checkpoint does not propose an
alternative testnet.

### 6.2 Explorer/verifier capability record

Provider documentation:

- [Blockscout contract-verification API](https://docs.blockscout.com/devs/verification/blockscout-smart-contract-verification-api)
- [Blockscout API requests and limits](https://docs.blockscout.com/devs/apis/requests-and-limits)

Read-only calls to the exact configuration endpoints below returned HTTP 200 on
2026-07-23:

- `https://robinhoodchain.blockscout.com/api/v2/smart-contracts/verification/config`
- `https://explorer.testnet.chain.robinhood.com/api/v2/smart-contracts/verification/config`

Both reported the verifier microservice enabled and offered Vyper
standard-input/multipart/code and Solidity standard-input/multipart methods.
Vyper compiler `v0.4.3+commit.bff19ea2` appeared in both compiler lists. The
mainnet response advertised Sourcify while the testnet response did not;
therefore Sourcify is not part of the proposed common profile.

Blockscout documents a default no-key, per-IP limit of **three requests per
minute**, not per second. The documentation also says instance operators can
change limits and describes higher-capacity key and whitelist modes. The
effective limit on each Robinhood explorer must therefore be confirmed rather
than inferred from Blockscout's default. At the documented default, verifying
roughly 48 contracts with the current ten-poll loop is operationally
impractical and would violate the intended request budget. Production
verification needs an instance-confirmed key/whitelist policy or an explicitly
approved low-rate queue.

### 6.3 Empirical RPC observations

Read-only JSON-RPC probes against the official public endpoints observed:

| Probe | Mainnet | Testnet | Interpretation |
| --- | --- | --- | --- |
| `eth_chainId` | `0x1237` (`4663`) | `0xb626` (`46630`) | Matches official documentation |
| Latest block | Included `baseFeePerGas` | Included `baseFeePerGas` | Supports dynamic-fee client handling |
| `eth_feeHistory` | Supported | Supported | RPC estimation is available |
| `eth_maxPriorityFeePerGas` | Returned zero at sample time | Returned zero at sample time | Observation only; never a hard-coded policy |
| `eth_gasPrice` | Supported | Supported | Observation only |

These observations justify an RPC-estimated dynamic-fee proposal, not a claim
about guaranteed production fee or finality behavior. A release freeze must
repeat the probes against the selected deployment provider and record sanitized
results locally.

## 7. Environment-variable inventory and proposed disposition

| Name / form | Current use | Proposed disposition |
| --- | --- | --- |
| `BASESCAN_API_KEY` | Eager migration import and Base explorer construction | Remove eager lookup; normalize under profile verifier settings or a reviewed Base compatibility layer |
| `ETHERSCAN_API_KEY` | Verification, test environment, and parameter helpers | Lazy-load only when a selected Etherscan profile requires it |
| `WEB3_ALCHEMY_API_KEY` | Base/Ethereum RPC URL interpolation | Replace for new profiles with opaque full RPC URL env vars; do not log |
| `${ACCOUNT}_PRIVATE_KEY` | Direct account loading | No silent fallback; allowed only if owner approves that backend and capability policy |
| `--rpc` value | Direct RPC override | Treat as sensitive; redact completely; exact chain-ID match still required |
| `ROBINHOOD_MAINNET_RPC_URL` | Proposed | Required full credentialed/provider URL for mainnet live modes; value never persisted |
| `ROBINHOOD_TESTNET_RPC_URL` | Proposed | Required full credentialed/provider URL for testnet live modes; value never persisted |

The names above contain no secret values. The owner may choose different
Robinhood env-var names, but the full-URL, lazy-load, redact, and exact-chain-ID
semantics are material.

## 8. Unresolved facts and owner gates

| ID | Unresolved item | Type | Required resolution |
| --- | --- | --- | --- |
| U-001 | Exact production RPC provider, endpoint policy, quotas, archival/state capability, and operational ownership | External fact / owner choice | Provider evidence and owner approval before rehearsal |
| U-002 | Required confirmations, reorg handling, `finalized`-tag semantics, and release finality threshold on Robinhood | External fact / owner policy | Primary/provider confirmation plus explicit operations policy |
| U-003 | Fee caps, priority-fee behavior, stuck/replacement policy, and balance floor | Owner policy | Approved per-environment policy validated on testnet |
| U-004 | Production signing backend and accountable operator roles | Owner/security choice | Capability matrix and security approval; no backend is currently approved |
| U-005 | Whether Blockscout verification remains keyless in production and the effective rate interval/burst on each Robinhood explorer | Owner/operations choice | Confirm instance settings before verifier implementation; do not assume the documented three-requests-per-minute no-key default or keyed limits are the deployed settings |
| U-007 | Whether Base retains legacy Alchemy-token and explorer-key compatibility aliases | Compatibility choice | Explicit deprecation/retention decision and regression scope |
| U-008 | Exact local profile chain-ID policy and repository paths | Test design choice | Track 6 reconciliation before implementation |
| U-009 | Track 1 supported Chainlink CCIP release, inheritance, registration, roles, limits, and lifecycle | Cross-track external/owner gate | Track 1 confirmation and owner approval |
| U-010 | Track 4 final USDG implementation, parameters, PSM controls, and SavingsGreen disposition | Cross-track owner/risk gate | Approved Track 4 implementation input |
| U-011 | Track 5 vault remediations and deployment-ready accounting implementation | Cross-track security gate | Approved, validated Track 5 input |
| U-012 | Track 6 S1/S2 implementation commits and exact version profiles | Cross-track implementation gate | Reconcile before Phase G validation design |
| U-013 | Dependency refresh compatible with pytest/Vyper/titanoboa and all open alerts | Security gate | Separate pin-refresh slice and complete revalidation |
| U-014 | Disposition of four migrations without numeric manifests and the duplicate ID | Historical fact | Repository/chain reconciliation; do not infer success/failure |
| U-015 | Reviewed Track 8 vault-change specification and validation plan do not yet exist | Parallel-track input | Keep vault-specific sequencing and requirements pending; reconcile before Phase C finalizes vault inventory/IDs and route any collision to the owner |

## 9. Material abstraction decisions for owner review

Recommendations remain proposals unless the status explicitly records owner
approval.

| Decision | Options | Selected/recommended direction | Why it shapes Phases C–H | Status |
| --- | --- | --- | --- | --- |
| D-001: canonical network model | Continue parallel dictionaries/conditionals; introduce one validated profile registry | One immutable profile registry consumed everywhere | Determines CLI, config, migration, verification, test, and evidence interfaces | Owner-approved specification direction, 2026-07-23 |
| D-002: RPC secret interface | Vendor-token URL construction; full opaque URL env per profile | Full opaque URL env; optional explicit Base compatibility adapter | Prevents vendor assumptions and secret-bearing URL logs | Owner-approved specification direction, 2026-07-23 |
| D-003: public RPC use | Allow all modes; restrict to facts/read-only/fork | Restrict official public Robinhood RPCs to facts/read-only/fork | Robinhood labels public RPCs rate-limited and not production-grade | Proposed |
| D-004: network identity | Trust selected label; require runtime chain-ID equality | Require equality before account load/sign/submit/verify | Eliminates wrong-chain execution and explorer routing | Owner-approved specification direction, 2026-07-23 |
| D-005: verifier architecture | One Etherscan helper; provider/language capability adapters | Explicit Blockscout and Etherscan-v2 adapters with no fallback | Shapes artifact metadata, verification tests, and rate/error evidence | Proposed |
| D-006: migration namespaces | Share Base or Robinhood directories; split or share Robinhood test/main source | Never share Base. Use `migrations/robinhood/` for both Robinhood environments and isolate their history directories. | Determines graph reuse, ID ownership, and evidence isolation | Owner-approved specification direction, 2026-07-23 |
| D-007: finality defaults | Choose a guessed confirmation count; leave null and fail closed | Leave null until owner/provider evidence; reject live modes | Finality affects progression, manifests, rollback, and release evidence | Proposed; production value unresolved |
| D-008: account abstraction | CLI labels tied to implementations; capability-based approved backends | Capability-based registry with no Robinhood live backend initially | Separates network profile from secret/signing implementation and enforces approval | Proposed; production backend unresolved |
| D-009: execution progression | Positional transaction logs; semantic immutable plan plus observed receipts/state | Semantic plan with step IDs, pre/postconditions, receipts, and atomic promotion | Determines resume, partial failure, rollback, and manifest schema | Owner-approved specification direction, 2026-07-23 |
| D-010: dependency gate | Treat alert scan as advisory; release-block high/medium deployment-relevant alerts | Release-block until fixed or explicitly accepted by owner/security | Directly affects frozen environment and all reproduction evidence | Proposed; owner/security approval pending |
| D-011: Base compatibility | Refactor Base implicitly; freeze all behavior; explicit compatibility contract | Preserve intended Base behavior through profiled regression tests, while rejecting unsafe defects | Avoids accidental defaults or history changes while removing unsafe fallbacks | Proposed |
| D-012: fee model | Hard-code sampled priority fee; use RPC estimation under approved caps | RPC dynamic estimation with owner-approved caps and replacement rules | Sampled zero priority fee is not durable policy | Proposed; production values unresolved |
| D-013: fork evidence | Allow latest/dirty forks as release evidence; require pinned clean forks for reproducible evidence | Exact source chain ID and block for committable evidence; latest/dirty forks remain local exploration only | Shapes test fixtures, evidence retention, and release reproducibility | Owner-approved specification direction, 2026-07-23 |
| D-014: operator confirmation | Reuse generic `--ask`; require plan/network/irreversible-action acknowledgments | Bind explicit acknowledgments to the frozen plan digest and canonical profile | Separates input prompting from accountable deployment approval | Owner-approved specification direction, 2026-07-23 |

## 10. Checkpoint disposition

The owner approved the early checkpoint and authorized continuation through
Phases C–H on 2026-07-23. The approved directions are D-001, D-002, D-004,
D-006, D-009, D-013, and D-014. This approval permits specification work only.
It does not approve a dependency change, account, provider, address, role,
finality count, fee value, deployment inventory, implementation, push, merge,
or live action.

At this checkpoint, Phases C–H and Deliverable B had not started. Their results
must preserve every unresolved production field and later owner/security gate.

## 11. Checkpoint validation record

The following read-only checks were used or are required immediately before
handoff:

- verify branch, worktree, starting commit, and changed-file scope;
- enumerate migration and step-manifest IDs and detect duplicates/missing pairs;
- parse every committed JSON manifest;
- verify recorded manifest source paths exist;
- inspect CLI help/import behavior without credentials;
- export ABIs only to a temporary directory;
- query repository dependency alerts read-only;
- retrieve official Robinhood and Blockscout documentation;
- use read-only `eth_chainId`, block, and fee RPC methods only;
- run Markdown whitespace validation against this untracked file; and
- re-run every frozen input hash.

No release, deployment, verification submission, or state-changing validation
is part of this checkpoint.

## 12. Reproducible sanitized public probes

These commands contain only public endpoints and read-only methods. The
JSON-RPC requests use HTTP `POST` as transport but do not sign, submit, or
simulate a transaction. They are suitable for reproducing the dated checkpoint
observations. Raw responses are intentionally not committed.

### 12.1 Explorer configuration

```bash
for robinhood_explorer_config in \
  'https://robinhoodchain.blockscout.com/api/v2/smart-contracts/verification/config' \
  'https://explorer.testnet.chain.robinhood.com/api/v2/smart-contracts/verification/config'
do
  curl --silent --show-error --fail --max-time 20 \
    --header 'Accept: application/json' \
    "$robinhood_explorer_config" |
    jq '{
      verification_enabled: .is_rust_verifier_microservice_enabled,
      verification_options,
      vyper_0_4_3: [
        .vyper_compiler_versions[]? |
        select(contains("v0.4.3"))
      ]
    }'
done
```

Expected checkpoint facts:

- both endpoints return HTTP 200 with the verifier microservice enabled;
- both include `vyper-standard-input`, `standard-input`, and
  `v0.4.3+commit.bff19ea2`;
- mainnet includes `sourcify`; testnet does not.

### 12.2 Chain identity

```bash
for robinhood_public_rpc in \
  'https://rpc.mainnet.chain.robinhood.com' \
  'https://rpc.testnet.chain.robinhood.com'
do
  curl --silent --show-error --fail --max-time 20 \
    --header 'Content-Type: application/json' \
    --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
    "$robinhood_public_rpc" |
    jq '{jsonrpc, id, result}'
done
```

Expected results are `0x1237` for mainnet and `0xb626` for testnet. The decimal
values are `4663` and `46630`.

### 12.3 Fee-market observations

```bash
for robinhood_public_rpc in \
  'https://rpc.mainnet.chain.robinhood.com' \
  'https://rpc.testnet.chain.robinhood.com'
do
  curl --silent --show-error --fail --max-time 20 \
    --header 'Content-Type: application/json' \
    --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest",false],"id":1}' \
    "$robinhood_public_rpc" |
    jq '{
      number: .result.number,
      baseFeePerGas: .result.baseFeePerGas
    }'

  curl --silent --show-error --fail --max-time 20 \
    --header 'Content-Type: application/json' \
    --data '{"jsonrpc":"2.0","method":"eth_feeHistory","params":["0x1","latest",[]],"id":1}' \
    "$robinhood_public_rpc" |
    jq '{
      oldestBlock: .result.oldestBlock,
      baseFeePerGas: .result.baseFeePerGas
    }'

  curl --silent --show-error --fail --max-time 20 \
    --header 'Content-Type: application/json' \
    --data '{"jsonrpc":"2.0","method":"eth_maxPriorityFeePerGas","params":[],"id":1}' \
    "$robinhood_public_rpc" |
    jq '{jsonrpc, id, result}'

  curl --silent --show-error --fail --max-time 20 \
    --header 'Content-Type: application/json' \
    --data '{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}' \
    "$robinhood_public_rpc" |
    jq '{jsonrpc, id, result}'
done
```

The changing block and fee values are observations, not approved defaults.
Release freeze must repeat these methods against the selected provider without
printing, storing, or committing a credential-bearing endpoint.
