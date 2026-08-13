# Robinhood deployment-support specification

> **CCIP supersession note (2026-08-11):** this specification's CCIP rows are
> predeployment planning history. GREEN/RIPE CCIP is now live; current topology,
> unresolved exact live-creation source identity, and remaining operational gates are in
> [ccip-live-state.md](ccip-live-state.md). Non-CCIP content retains its stated
> scope and authority.

> **1 August 2026 currentness overlay:** Ready to continue bounded launch
> preparation from exact baseline `5f5d22b7ee78cbb904c4fe3c6e46599c330c4353`,
> tree `7454b5456ebb6cd02d716a64b408629ab501629e`. PR #61, Morpho V2 and
> BlueChipYield support, H-04 source authority, M4 proof, and the H-06 candidate
> operator/storage class are integrated. The former H-05 declarative runner,
> executor, and plan census are retired; the eight-file imperative migration
> candidate remains repository review input, not an executable plan.
> `DefaultsRobinhood.vy` exists and compiles; Blueprint and Defaults
> are the two editable value authorities, and the JSON ledger is synchronized
> derived evidence. The current check is `configuration_consistent=true`,
> `deployment_ready=false`, with 64 blockers. The current launch candidate
> selects unchanged CurvePrices at PriceDesk ID 2 for GREEN only, with ID 1
> Chainlink and priorities `[1,2]`. ID 3 BlueChipYield remains
> blueprint-selected but is not deployed or finalized by the current candidate;
> IDs 4/5 are empty.
> USDG remains Chainlink-only; no LP token or Curve higher power is admitted.
> Repository configuration is
> prepared and consistent; production/onchain configuration has not occurred.
> No launch-remediation-candidate migration, deployment, activation, RPC,
> account, key, signer, or release action has occurred. Separately observed
> live CCIP and monitoring-only Uniswap state grants no such authority. The sole current operational handoff is
> [`deployment-owner-quickstart.md`](deployment-owner-quickstart.md). The
> phase tables below preserve historical specification proposals and are not
> current source or lifecycle authority. In particular, their CM-017
> omitted/empty-ID-2 row is superseded by
> [`curve-launch-activation.md`](curve-launch-activation.md).

- Status: Phases A–H completion draft for owner/reviewer scrutiny
- Review status: independent checkpoint/completion findings incorporated; specification directions approved only where recorded
- Scope completed: Phases A–H and Deliverables A–B at specification level
- Scope not authorized: implementation, production values, push, merge, or live actions
- Starting commit: `68a76dcd5ea9b95b9148d3e6ebdd12107d5cc88e`
- Track branch: `rh-track-7-deployment-support`
- Worktree: `/Users/wigglez/dev/ripe-protocol-track-7-deployment-support`
- Evidence date: 2026-07-23, America/Denver
- Planning correction: on 2026-07-24, the proposed deployment clock-profile
  test was renamed to `tests/deployment/test_network_clock_profiles.py` and
  assigned to H-04, avoiding a pytest basename collision with the integrated
  Track 6 S1 file `tests/clock/test_clock_profiles.py`; no implementation is
  implied
- Minimum-change correction: on 2026-07-24, the owner required unchanged
  production source, configuration, omission, or explicit risk acceptance to
  be evaluated before any contract change. S3 is retained, S4 is closed
  no-code for the initial release with zero cooldown and omitted Underscore,
  and S5 now has an owner-selected portable action-block direction with the
  existing Base Ledger permanently retained. The S3/S4/S5 reservations remain
  assertion namespaces, not independent upgrade authorization. H-03 through
  H-09 must consume the selected minimal graph from
  `minimal-contract-change-reassessment.md`.

## 1. Checkpoint boundary

This document began as Deliverable A at the optional early checkpoint defined by
`track-7-robinhood-deployment-support.md`. Following the recorded owner
authorization, it now carries the specification through Phases C–H. It records:

- the Phase A audit of the existing deployment system;
- the dependency-security preflight;
- a proposed Phase B network-profile schema;
- a proposed Base/Robinhood network-profile table;
- the primary-source record;
- unresolved facts and owner gates;
- abstraction decisions that materially shape Phases C–H;
- the component graph, migration reservations, evidence and artifact contracts;
- the ordered follow-on implementation slices and full decision register; and
- the exact `rh-summary.md` Section 1 handoff.

It does **not** approve a Robinhood deployment, choose a production operator,
authorize dependency changes, or approve production values. On 2026-07-23, the
owner authorized this checkpoint commit, selected one shared Robinhood
migration-source directory with separate testnet/mainnet histories, approved
D-001, D-002, D-004, D-009, D-013, and D-014 as specification directions, and
authorized continuation through Phases C–H. The authorization did not permit
push, merge, or implementation. After completion review on the same date, the
owner also approved D-005 as a specification direction: explicit Blockscout and
Etherscan-v2 adapters with no provider fallback. That approval does not approve
credentials, rate limits, or live verification.

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
| Track 5, vault | Neither existing vault is approved unchanged for Stock Tokens. Track 5 defines the failure evidence; it does not preselect a broader Rebase/Shares redesign over the smallest sufficient containment patch. | Track 8 owner/security decision |
| Track 6, S1/S2 | The narrow kickoff directions are owner-approved at `ce3805d`; specifications exist, but neither fact proves implementation or validation has landed. | Reconcile exact implementation commits before H-09 or any rehearsal |
| Track 8, vault change | Brief-only post-kickoff input at `be6a759`; the owner now requires Stock Tokens at initial launch and directs Track 8 to specify the smallest demonstrably sufficient shared containment patch. Track 7 owns exact Robinhood migration IDs, namespaces, manifests, and deployment tooling. | Keep Phase C vault rows provisional; reconcile the reviewed minimum-containment outputs before H-03/H-05 implementation; launch blocks if the path cannot be approved |

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

### 2.7 Final parallel-worktree reconciliation

During completion validation, integration first remained at `be6a759` with two
uncommitted edits not made by Track 7. After Track 7's first completion commit,
the same byte-for-byte edits landed as clean integration commit
`ce3805d6079ee87d727486ea82b75cbddc12e46d`
(`docs: owner-approved checklist reconciliation at be6a759`):

| Integrated input | SHA-256 | Reconciliation |
| --- | --- | --- |
| `docs/chains/rh-summary.md` | `b60f5c516b531d2cea67dfce08032e2fcd4f2ed6a26bff8c688d9e2fecf67c22` | Section 0 checklist-status clarifications; Section 1 text consumed by the exact handoff is unchanged |
| `docs/chains/rh/shared-block-clock-specification.md` | `dd9e940aa03f065ad7ae9a0407074fe202dec7b563cf15972bad0fd3d6a154b0` | Narrow S1/S2 directions are owner-approved; implementation and remaining clock values stay open |

These post-kickoff inputs do not replace the Section 2.3 hashes used for the
frozen Phase A audit. Their content is compatible with this specification:
the selected existing USDG Chainlink-feed direction, shared-source posture,
assisted-registration preference and S1/S2 gates are already represented, while
deployment, activation, exact values and implementation remain blocked. No
owned Track 7 deliverable path or proposed migration ID collision was observed.
Track 7 did not edit, stage, clean, push or merge the integration worktree.

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

> [!NOTE]
> **Active-tree extraction, 2026-08-07.** The numeric step manifests described
> below were extracted from the active tree by the RH codebase simplification
> pass. Both directories, both current manifests, and every
> `config/network_profiles.py` declaration are unchanged. All 66 extracted step
> manifests remain recoverable from
> `610b43f4508e85628a1362532a79d68d71ea902c`, with per-file blob IDs and
> SHA-256 values in
> [`extracted-files.tsv`](../../simplification/extracted-files.tsv).
>
> **Current active-tree contents, and they are not symmetric:**
>
> ```text
> migration_history/base-mainnet/v1/       current-manifest.json
> migration_history/robinhood-mainnet/v1/  0008-manifest.json
>                                          current-manifest.json
> ```
>
> `0008-manifest.json` is **retained, not extracted**. It was produced after the
> extraction baseline, it is live Robinhood deployment history, and the
> extraction manifest is bound to `610b43f…` and makes no claim about material
> created after it. Operators should expect numeric step manifests produced from
> now on to accumulate here normally; nothing in this cleanup removes, rewrites,
> or suppresses them, and the runner's write path is unchanged.
>
> This changes no operator behavior. `--start-timestamp` defaults to the string
> `"0"`, so `MigrationRunner._migrations()` always takes the explicit-start
> branch and `_latest_manifest_timestamp()` stays unreachable from the CLI, as
> Section 2.4 of the simplification plan records. The counts below remain the
> historical observation made at the starting commit.

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

`pymdown-extensions` is a severable documentation-only sub-slice despite being
listed in Slice A for complete alert accounting. A Markdown compatibility
failure keeps that advisory and the documentation-build gate open, but must not
block review or landing of an otherwise compatible deployment-path refresh.
Conversely, clearing the docs alert cannot satisfy the deployment-security
gate.

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
  deployment_rate_policy_id: approved-policy-or-null
  public_read_rate_limit:
    requests: positive-integer-or-null
    interval_seconds: positive-integer-or-null
    burst: positive-integer-or-null
    source: documented_default | instance_confirmed | owner_policy | unknown
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
  block_policy: explicit_pin_required | latest_for_local_exploration
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
12. Public and deployment RPC throttling are separate policies. A live-capable
    provider requires an approved rate/quota policy; a public endpoint with an
    unknown limit remains read-only/fork-only and must fail conservatively.
13. A fork used as reproducible or committable evidence requires an exact source
    chain-ID match and pinned block. `latest` and dirty-state forks are
    exploration-only and their evidence remains local. The concrete source block
    number/hash belongs to the per-run evidence bundle, never the static profile.
14. Fork mode never signs or submits to its source RPC. A fork profile with
    `allow_submission: true` is invalid.
15. Live mode requires a frozen plan digest, explicit network/chain
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
| `robinhood-mainnet` | Mainnet | `4663`; ETH, 18 | `ROBINHOOD_MAINNET_RPC_URL` required for deployment. Official public RPC is rate-limited and read-only/facts/fork only; interval/burst are unknown and must fail conservatively. | `https://robinhoodchain.blockscout.com`; Blockscout API at `/api/`; keyless supported; documented default is 3 requests/minute without a key, but effective instance/key policy is pending; Vyper and Solidity standard JSON | Proposed `robinhood` blueprint / `DefaultsRobinhood`; shared proposed source `migrations/robinhood/`; isolated proposed history `migration_history/robinhood-mainnet/v1/`; paths not yet created | No backend approved; confirmation, reorg, fee-cap, and finality policies pending; live mode rejected |
| `robinhood-testnet` | Test | `46630`; ETH, 18 | `ROBINHOOD_TESTNET_RPC_URL` required for deployment. Official public RPC is rate-limited and read-only/facts/fork only; interval/burst are unknown and must fail conservatively. | `https://explorer.testnet.chain.robinhood.com`; Blockscout API at `/api/`; keyless supported; documented default is 3 requests/minute without a key, but effective instance/key policy is pending; Vyper and Solidity standard JSON | Same proposed Robinhood blueprint/default model and shared source `migrations/robinhood/`; isolated proposed history `migration_history/robinhood-testnet/v1/`; paths not yet created | No backend approved; confirmation, reorg, fee-cap, and finality policies pending; live mode rejected |

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

Testnet-only setup cannot fork that source tree:

- faucet funding and signer funding are operator prerequisites recorded in the
  testnet runbook/evidence bundle, never migration steps;
- mock or test-token deployment belongs to isolated test fixtures outside
  `migrations/robinhood/` and never appears in mainnet or canonical testnet
  migration history;
- the same migration step IDs consume profile-specific approved values, so a
  testnet parameter/address differs without a second source path; and
- if a production-intent step cannot be rehearsed through the shared graph, the
  testnet run records the limitation and stops for owner review rather than
  adding a conditional testnet-only migration.

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
| U-015 | The reviewed Track 8 vault-change specification, validation plan, and M0 evidence are integrated, but M0 remains open and the exact minimum-containment implementation is not yet approved | Cross-track product/security gate | H-03 must preserve unresolved Stock, sGREEN, PSM, reward, and route decisions as typed blockers; consume a reviewed M0 closure before any later slice turns those rows into executable deployment inputs |

## 9. Material abstraction decisions for owner review

Recommendations remain proposals unless the status explicitly records owner
approval.

| Decision | Options | Selected/recommended direction | Why it shapes Phases C–H | Status |
| --- | --- | --- | --- | --- |
| D-001: canonical network model | Continue parallel dictionaries/conditionals; introduce one validated profile registry | One immutable profile registry consumed everywhere | Determines CLI, config, migration, verification, test, and evidence interfaces | Owner-approved specification direction, 2026-07-23 |
| D-002: RPC secret interface | Vendor-token URL construction; full opaque URL env per profile | Full opaque URL env; optional explicit Base compatibility adapter | Prevents vendor assumptions and secret-bearing URL logs | Owner-approved specification direction, 2026-07-23 |
| D-003: public RPC use | Allow all modes; restrict to facts/read-only/fork | Restrict official public Robinhood RPCs to facts/read-only/fork | Robinhood labels public RPCs rate-limited and not production-grade | Proposed |
| D-004: network identity | Trust selected label; require runtime chain-ID equality | Require equality before account load/sign/submit/verify | Eliminates wrong-chain execution and explorer routing | Owner-approved specification direction, 2026-07-23 |
| D-005: verifier architecture | One Etherscan helper; provider/language capability adapters | Explicit Blockscout and Etherscan-v2 adapters with no fallback | Shapes artifact metadata, verification tests, and rate/error evidence | Owner-approved specification direction, 2026-07-23; credentials, rate limits, and live verification remain unapproved |
| D-006: migration namespaces | Share Base or Robinhood directories; split or share Robinhood test/main source | Resolved: never share Base. Use `migrations/robinhood/` for both Robinhood environments and isolate their history directories; see Section 14.1 and DR-004. | Determines graph reuse, ID ownership, and evidence isolation | Owner-approved specification direction, 2026-07-23 |
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
D-005, D-006, D-009, D-013, and D-014. D-005 was approved after completion
review and authorizes only the explicit adapter/no-fallback specification
direction; credentials, rate limits, and live verification remain unapproved.
These approvals permit specification work only. They do not approve a
dependency change, account, provider, address, role, finality count, fee value,
deployment inventory, implementation, push, merge, or live action.

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

## 13. Phase C — deployment inventory and graph

### 13.1 Inventory status and graph rule

This section specifies the deployable graph; it does not approve addresses,
parameters, roles, account backends, or live versions. `Selected` means the
component belongs in the provisional clean-deployment graph once every stated
gate closes. `Scaffolded disabled` means the component is deployed/registered
only to preserve a required shared registry topology, with every value path and
capability disabled. `Omitted` means no Robinhood address, registry entry,
permission, route, or manifest contract record. `Deferred` and `blocked` fail
closed.

The shared source hard-codes registry topology in several places:

- RipeHq IDs 1–22 are constants in `contracts/modules/Addys.vy:40-61`.
- VaultBook Stability Pool ID 1 is repeated in
  `contracts/core/CreditEngine.vy:184`,
  `contracts/core/CreditRedeem.vy:110`, and `contracts/core/Teller.vy:213`;
  RipeGov Vault ID 2 is repeated in `contracts/core/BondRoom.vy:102`,
  `contracts/core/HumanResources.vy:127`, `contracts/core/Lootbox.vy:192`,
  `contracts/core/Teller.vy:214`, and
  `contracts/vaults/modules/StabVault.vy:95`.
- PriceDesk ID 2 is hard-coded as `CURVE_PRICES_ID` in
  `contracts/core/CreditEngine.vy:185`, `contracts/core/Teller.vy:215`, and
  `contracts/core/Endaoment.vy:148`. Address registration is sequential in
  `contracts/registries/modules/AddressRegistry.vy:184-198`, so the next source
  after Chainlink would otherwise silently acquire Curve semantics.
- SwitchboardBravo mirrors RipeHq IDs 1, 2, 5, 6, and 8 at
  `contracts/config/SwitchboardBravo.vy:179-183`; SwitchboardDelta mirrors IDs
  4, 5, 12, 16, 17, and 18 at
  `contracts/config/SwitchboardDelta.vy:433-439`; and SwitchboardEcho mirrors
  IDs 5, 14, and 22 at `contracts/config/SwitchboardEcho.vy:439-441`. The
  adjacent Switchboard/Underscore registry constants are separate registry
  domains and do not relax the RipeHq assignments.

Those IDs are not merely Base deployment history. Therefore:

1. Robinhood cannot shift later registrations when an optional component is
   omitted.
2. A component required to occupy a hard-coded slot must either be deployed in
   an inert, reviewed posture or the canonical shared source must first gain an
   approved sparse/optional-registry design.
3. A zero address, unrelated placeholder, or deliberately wrong contract is not
   an acceptable slot reservation.
4. RipeHq IDs 23 and 24 are provisionally reserved for the GREEN and RIPE CCIP
   pools only if Track 1 proves the pools implement the required Department
   capability surface and the owner approves registration.
5. PriceDesk IDs 2–5 preserve their Base semantic assignments: Curve,
   BlueChipYield, Pyth, and Stork. While omitted, a slot remains empty and is
   permanently reserved to that semantic identity; a different source can never
   consume it. Adding a supported source at its canonical later ID requires an
   owner-approved sparse-registry design or legitimate occupation of every
   earlier canonical slot, plus a new migration and topology review.

### 13.2 Common row policies

The following codes expand the repeated fields in every inventory row:

| Code | Required behavior |
| --- | --- |
| `ARG-P` | Constructor shape comes from the canonical source ABI; every chain value comes from the frozen network profile, `DefaultsRobinhood`, or an approved parameter manifest. A missing value is `blocked`, never zero-filled. |
| `ARG-HQ` | Constructor receives the newly deployed Robinhood RipeHq address plus only the additional values declared by the canonical constructor ABI. |
| `ROLE-G` | Temporary deployment authority may perform setup only. Final governance/admin belongs to the owner-approved local timelock/Safe path; guardian/operations receives only explicitly enumerated pause/runbook powers; deployer authority must be absent after handoff. |
| `ASSERT-S` | Address is nonzero, chain ID/profile match, creation/runtime/ABI/source hashes match, constructor values match, expected registry name/ID and capabilities match, ownership is correct, and every post-deployment call result is recorded. |
| `ASSERT-O` | No address, registry row, capability, approval, route, feature flag, or callable configured path exists on Robinhood; manifest disposition is `omitted` or `deferred`, never a zero-valued deployed record. |
| `ASSERT-D` | Contract may exist, but all named enablement flags/caps/roles are false or zero by explicit legitimate parameter; it has no mint capability or unsupported approval/route. |
| `BASE-U` | Canonical source is unchanged. Base needs no bytecode action merely because Robinhood deploys a new address; configuration remains chain-local. |
| `BASE-M` | Canonical shared source is modified. Base requires an explicit per-component live-version decision: a separately approved, time-bounded convergence plan or a narrowly justified permanent exception for an immutable or unacceptably risky state-bearing/custody-bearing deployment. |
| `BASE-O` | Component remains Base-only; Robinhood omission does not alter Base. |
| `ABORT-A` | Before registry/capability confirmation, stop and leave any already-created address explicitly orphaned in local evidence. A transaction cannot be undone. |
| `ABORT-G` | After registry/capability/ownership confirmation, remediation requires governance cancellation, disablement, replacement, or a new migration. It is not rollback. |

Registry names and numeric IDs below preserve the canonical constants. Any
implementation that observes a different next ID must stop rather than accept a
shifted registration.

### 13.3 Components CM-001 through CM-020

| ID / component | Robinhood disposition and form | Canonical source; constructor/value source | Order, reservation, registry and capability | Controls, assertions, Base policy, abort and approval |
| --- | --- | --- | --- | --- |
| CM-001 `GreenToken` | Selected ordinary Vyper contract | `contracts/tokens/GreenToken.vy`; current ABI with `ARG-P`; initial supply/recipient are owner values | `0100_TokensAndRipeHq.py`; RipeHq ID 1 `Green Token`; no self capability | `ROLE-G`; `ASSERT-S`; `BASE-U`; `ABORT-G`; production values open |
| CM-002 `RipeToken` | Selected ordinary Vyper contract | `contracts/tokens/RipeToken.vy`; current ABI with `ARG-P`; supply/governance are owner values | `0100`; RipeHq ID 3 `Ripe Token`; no self capability | `ROLE-G`; `ASSERT-S`; `BASE-U`; `ABORT-G`; Track 1 token-admin contingency open |
| CM-003 `SavingsGreen` | Provisionally selected registry scaffold; user-facing path remains disabled pending owner product decision | `contracts/tokens/SavingsGreen.vy`; GREEN/HQ dependencies and `ARG-P` | `0100` because RipeHq requires the address; RipeHq ID 2 `Savings Green`; downstream enablement reserved at `0700` | `ROLE-G`; `ASSERT-D`; `BASE-U`; `ABORT-G`; owner inclusion/omission redesign decision open |
| CM-004 `RipeHq` | Selected authority/registry contract | `contracts/registries/RipeHq.vy`; GREEN/sGREEN/RIPE addresses, temporary deployer, and reviewed timelock bounds from `ARG-P` | `0100`, after CM-001–003 and before every Department | `ROLE-G`; verify minting globally disabled until handoff gates; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-005 `Contributor` | Blueprint selected only as inert HR scaffold; no contributor instances unless HR approved | `contracts/modules/Contributor.vy`; blueprint has no constructor; instances derive from approved HR config | `0100` blueprint; not an HQ registry row; CM-032 owns instances | No employee data/roles; `ASSERT-D`; `BASE-U`; `ABORT-A`; product/HR owner open |
| CM-006 `TrainingWheels` | Selected launch-control contract | `contracts/config/TrainingWheels.vy`; RipeHq plus owner-approved allowlist, never copied Base addresses | `0100`; referenced by `DefaultsRobinhood`, not an HQ row | `ROLE-G`; allowlist provenance/assertions; `BASE-U`; `ABORT-G`; role values open |
| CM-007 `DefaultsBase` | Omitted from Robinhood | `contracts/config/DefaultsBase.vy`; Base-only artifact | No RH migration or registry; replaced by CM-049 | `ASSERT-O`; `BASE-O`; no rollback; omission approved by architecture |
| CM-008 `Ledger` | Selected fresh deployment of the revised canonical Ledger with the same-execution-block guard enabled through the S5-approved action-block boundary | `contracts/data/Ledger.vy`; `ARG-HQ` plus the immutable provider/source input approved by S5 Stage A | `0200_DataAndConfigRegistries.py`; RipeHq ID 4 `Ledger`; no mint/RIPE/blacklist capability | `ROLE-G`; prove same-child rejection, next-child allowance under a repeated ancestor number, provider/source identity and fail-closed behavior; `BASE-M` with the owner-approved permanent exception that retains the live state-bearing Base Ledger and creates no migration/convergence deadline; `ABORT-G` |
| CM-009 `MissionControl` | Selected data contract | `contracts/data/MissionControl.vy`; RipeHq plus CM-049 defaults artifact | `0200`; RipeHq ID 5 `Mission Control`; no capability | `ROLE-G`; parameter hash/assertions; `BASE-U`; `ABORT-G`; all production parameters open |
| CM-010 `Switchboard` | Selected configuration registry | `contracts/registries/Switchboard.vy`; RipeHq and reviewed registry timelock bounds | `0300_Switchboards.py`; RipeHq ID 6 `Switchboard`; blacklist capability true only after reviewed handoff | `ROLE-G`; IDs 1–5 below; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-011 `SwitchboardAlpha` | Selected configuration Department | `contracts/config/SwitchboardAlpha.vy`; `ARG-HQ`, stale-time bounds, action timelocks | `0300`; Switchboard ID 1 `Switchboard Alpha` | `ROLE-G`; no unsupported addresses; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-012 `SwitchboardBravo` | Selected auction configuration Department | `contracts/config/SwitchboardBravo.vy`; `ARG-HQ` and action timelocks | `0300`; Switchboard ID 2 `Switchboard Bravo` | `ROLE-G`; RH auction values blocked pending approval; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-013 `SwitchboardCharlie` | Selected rewards/config Department | `contracts/config/SwitchboardCharlie.vy`; `ARG-HQ` and action timelocks | `0300`; Switchboard ID 3 `Switchboard Charlie` | `ROLE-G`; tokenomics values blocked; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-014 `SwitchboardDelta` | Selected unchanged with Deleverage cooldown zero unless S4 necessity approval requires a shared artifact | `contracts/config/SwitchboardDelta.vy`; `ARG-HQ`, timelocks, zero cooldown and other approved values | `0300`; Switchboard ID 4 `Switchboard Delta` | `ROLE-G`; zero/non-activation assertion; `BASE-U`; conditional `BASE-M` only after S4 security/protocol approval; S5 may consume the existing Boolean policy but must not change Delta without separate necessity proof; `ABORT-G` |
| CM-015 `PriceDesk` | Selected registry | `contracts/registries/PriceDesk.vy`; RipeHq, ETH sentinel/native metadata, registry timelocks | `0400_PriceSources.py`; RipeHq ID 7 `Price Desk`; no capability | `ROLE-G`; only approved sources registered; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-016 `ChainlinkPrices` | Selected adapter, but no asset feed registered without dated feed approval | `contracts/priceSources/ChainlinkPrices.vy`; RipeHq, native/BTC sentinels and primary-source feed addresses through `ARG-P` | `0400`; PriceDesk ID 1 `Chainlink`; feed registrations follow adapter confirmation | `ROLE-G`; feed decimals/quote/heartbeat assertions; `BASE-U`; `ABORT-G`; oracle owner approval open |
| CM-017 `CurvePrices` | Selected unchanged for bounded GREEN-only launch pricing; no LP admission or higher power | `contracts/priceSources/CurvePrices.vy`; RipeHq plus selected AddressProvider ID 7 MetaRegistry and deployment-produced GREEN/USDG pool through `ARG-P` | Exact registration order is Chainlink ID 1, Curve ID 2, BlueChipYield ID 3; GREEN alone receives the Curve feed; USDG has no Curve feed | `ROLE-G`; prove GREEN → Curve → USDG → Chainlink, priorities `[1,3]`, zero/revert/stale/paused/disabled behavior, and no recursive USDG lookup; `ASSERT-S`; `BASE-U`; deployment blocked by the 23 typed Curve inputs; `ABORT-G` |
| CM-018 `BlueChipYieldPrices` | Selected source-compatible launch adapter | `contracts/priceSources/BlueChipYieldPrices.vy`; RipeHq and approved market bindings through `ARG-P` | Registered after Curve at PriceDesk ID 3; retained as priority ID 3 | `ROLE-G`; source-specific market, decimals, and failure assertions; `ASSERT-S`; `BASE-U`; final external bindings remain open; `ABORT-G` |
| CM-019 `PythPrices` | Omitted and unregistered at launch | `contracts/priceSources/PythPrices.vy` | No migration; PriceDesk ID 4 remains empty and reserved for Pyth semantics | `ASSERT-O`; future use needs a new decision/migration that preserves the selected IDs 1–3 topology; `BASE-O` |
| CM-020 `StorkPrices` | Omitted and unregistered | `contracts/priceSources/StorkPrices.vy` | No migration; PriceDesk ID 5 remains empty and reserved for Stork semantics | `ASSERT-O`; no other source at ID 5; future use must preserve selected IDs 1–3 and the semantic ID 4 reservation; `BASE-O`; no rollback |

### 13.4 Components CM-021 through CM-040

| ID / component | Robinhood disposition and form | Canonical source; constructor/value source | Order, reservation, registry and capability | Controls, assertions, Base policy, abort and approval |
| --- | --- | --- | --- | --- |
| CM-021 `VaultBook` | Selected registry, but final vault artifact set is blocked by Track 8 | `contracts/registries/VaultBook.vy`; RipeHq and registry timelocks | `0500_VaultsAndAssets.py`; RipeHq ID 8 `Vault Book`; canMintRIPE true only if canonical behavior still requires it | `ROLE-G`; exact IDs 1–4 below; `ASSERT-S`; `BASE-U`; `ABORT-G`; Track 8 reconciliation required |
| CM-022 `StabilityPool` | Reward product values approved; enablement remains operationally gated with CM-003/SavingsGreen | `contracts/vaults/StabilityPool.vy`; `ARG-HQ` | `0500`, VaultBook ID 1 `Stability Pool`; enablement configuration in `0700_SavingsGreenPath.py` | `ROLE-G`; no Stock Token custody/swap; `ASSERT-D`; `BASE-U`; `ABORT-G` |
| CM-023 `RipeGov` | Selected governance vault; reward values approved and operational bindings open | `contracts/vaults/RipeGov.vy`; `ARG-HQ` | `0500`, VaultBook ID 2 `Ripe Gov Vault` | `ROLE-G`; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-024 `SimpleErc20` | Registry slot required; current artifact is blocked for Stock Tokens; deploy only the Track 8-approved minimum-containment canonical artifact | `contracts/vaults/SimpleErc20.vy`; `ARG-HQ` | `0500`, VaultBook ID 3 `Simple ERC20 Vault` | No Stock asset registration before Track 8 acceptance; initial launch is blocked if the approved Stock path cannot then be registered; live-backing tests required; `BASE-M` if changed; `ABORT-G`; Track 8 owner/security gate |
| CM-025 `RebaseErc20` / `SharesVault` | Blocked unchanged for Stock Tokens; deploy only if Track 8 selects this as part of the minimum-containment artifact set | `contracts/vaults/RebaseErc20.vy`, `contracts/vaults/modules/SharesVault.vy`; `ARG-HQ` | `0500`, VaultBook ID 4 `Rebase ERC20 Vault` | No Stock asset registration before Track 8 acceptance; initial launch cannot pass by silently omitting Stock Tokens; total-loss/post-zero assertions if selected; `BASE-M` if changed; `ABORT-G`; Track 8 owner/security gate |
| CM-026 `AuctionHouse` | Selected core Department; Stock settlement disabled until Track 8 acceptance, then enabled only through the approved minimum-containment path | `contracts/core/AuctionHouse.vy`; `ARG-HQ` | `0600_CoreDepartments.py`; RipeHq ID 9 `Auction House`; canMintGREEN true only after assertions | `ROLE-G`; pre-gate Stock path disabled; launch requires the approved external-delivery/settlement invariant; `ASSERT-S`; `BASE-M` if Track 8 changes source; `ABORT-G` |
| CM-027 `AuctionHouseNFT` | Selected ordinary Department | `contracts/core/AuctionHouseNFT.vy`; `ARG-HQ` | `0600`; RipeHq ID 10 `Auction House NFT`; no capability | `ROLE-G`; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-028 `Boardroom` | Selected rewards Department | `contracts/core/Boardroom.vy`; `ARG-HQ` | `0600`; RipeHq ID 11 `Boardroom`; no capability | `ROLE-G`; rewards remain disabled until tokenomics approval; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-029 `BondRoom` | Provisionally selected Department with derived BondBooster | `contracts/core/BondRoom.vy`, `contracts/config/BondBooster.vy`; `ARG-HQ` and booster address | `0600`; RipeHq ID 12 `Bond Room`; canMintRIPE true only after bond gates | `ROLE-G`; bond path disabled pending terms; `ASSERT-D`; `BASE-U`; `ABORT-G` |
| CM-030 `CreditEngine` | Selected core Department; Stock borrowing remains disabled until Track 8 acceptance and is required for the approved initial-launch lifecycle | `contracts/core/CreditEngine.vy`; `ARG-HQ` | `0600`; RipeHq ID 13 `Credit Engine`; canMintGREEN true only after assertions | `ROLE-G`; Curve danger and Stock deficit paths fail closed; initial launch blocks unless the approved Stock borrow path passes; `ASSERT-S`; `BASE-M` if Track 8 changes source; `ABORT-G` |
| CM-031 `Endaoment` | Selected reserve coordinator with Base routes absent | `contracts/core/Endaoment.vy`; `ARG-HQ` plus approved wrapped/native token metadata | `0600`; RipeHq ID 14 `Endaoment`; canMintGREEN true only after supported-action allowlist | `ROLE-G`; no Curve/yield/partner route; `ASSERT-S`; `BASE-U`; `ABORT-G`; reserve policy open |
| CM-032 `HumanResources` | Scaffolded inactive to preserve hard-coded RipeHq ID 15 unless owner approves active HR | `contracts/core/HumanResources.vy`; `ARG-HQ` and action timelocks | `0600`; RipeHq ID 15 `Human Resources`; canMintRIPE false while inactive | `ROLE-G`; no contributors/vesting; `ASSERT-D`; `BASE-U`; `ABORT-G`; HR owner decision open |
| CM-033 `Lootbox` | Selected with owner-retained S3 artifact; Underscore and rewards disabled until separate approvals | `contracts/core/Lootbox.vy`; `ARG-HQ`, floor `7,200`, interval zero, and approved reward values | `0600`; RipeHq ID 16 `Lootbox`; canMintRIPE false until enablement | `ROLE-G`; Underscore path absent; `ASSERT-D`; `BASE-M` with separately gated Base convergence; `ABORT-G` |
| CM-034 `Teller` | Selected user-entry Department | `contracts/core/Teller.vy`; `ARG-HQ` plus explicit Ledger-check policy | `0600`; RipeHq ID 17 `Teller`; no mint capability | `ROLE-G`; no Underscore wallet; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-035 `GreenPool` | Omitted Base Curve external address | Base migration/current-manifest evidence only | No RH migration/registry | `ASSERT-O`; forbidden-address list; `BASE-O`; no rollback |
| CM-036 `RipePoolCurve` | Omitted Base Curve external address | Base migration/current-manifest evidence only | No RH migration/registry | `ASSERT-O`; forbidden-address list; `BASE-O`; no rollback |
| CM-037 `RipePoolAero` | Omitted Base Aerodrome external address | Base migration/current-manifest evidence only | No RH migration/registry | `ASSERT-O`; forbidden-address list; `BASE-O`; no rollback |
| CM-038 `BondBooster` | Derived contract only if CM-029 is selected | `contracts/config/BondBooster.vy`; constructor values from approved bond terms | Created within `0600`, referenced by BondRoom; no HQ row | `ROLE-G`; disabled unless bond program approved; `ASSERT-D`; `BASE-U`; `ABORT-G` |
| CM-039 `wsuperOETHbPrices` | Omitted | `contracts/priceSources/wsuperOETHbPrices.vy` | No migration/PriceDesk row | `ASSERT-O`; `BASE-O`; no rollback |
| CM-040 `RedStone` | Omitted | `contracts/priceSources/RedStone.vy` | No migration/PriceDesk row | `ASSERT-O`; `BASE-O`; no rollback |

### 13.5 Components CM-041 through CM-060

| ID / component | Robinhood disposition and form | Canonical source; constructor/value source | Order, reservation, registry and capability | Controls, assertions, Base policy, abort and approval |
| --- | --- | --- | --- | --- |
| CM-041 `UndyVaultPrices` | Omitted | `contracts/priceSources/UndyVaultPrices.vy` | No migration/PriceDesk row | `ASSERT-O`; `BASE-O`; no rollback |
| CM-042 `Underscore Vault` | Omitted external integration | Base migration/current-manifest evidence only | No migration/VaultBook row | `ASSERT-O`; no hooks, rewards, bypasses or registry dependencies; `BASE-O` |
| CM-043 `CreditRedeem` | Selected scaffold for hard-coded ID; Stock Token path disabled | `contracts/core/CreditRedeem.vy`; `ARG-HQ` | `0600`; RipeHq ID 19 `Credit Redeem`; no capability | `ROLE-G`; `canRedeemCollateral=false` for Stock assets; `ASSERT-D`; `BASE-U`; `ABORT-G` |
| CM-044 `Deleverage` | Selected unchanged with cooldown zero unless the owner approves an indispensable S4 artifact | `contracts/core/Deleverage.vy`; `ARG-HQ`; approved zero assertion or later cooldown/context policy | `0600`; RipeHq ID 18 `Deleverage`; no capability | `ROLE-G`; no Underscore path; zero/non-activation assertions; `BASE-U`; S4 artifact changes this to `BASE-M` only after security/necessity approval; `ABORT-G` |
| CM-045 `TellerUtils` | Selected helper Department | `contracts/core/TellerUtils.vy`; `ARG-HQ` | `0600`; RipeHq ID 20 `Teller Utils`; no capability | `ROLE-G`; Underscore getters/routes fail closed; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-046 `SwitchboardEcho` | Scaffolded disabled because CM-048 occupies hard-coded ID 22 and later activation needs governance | `contracts/config/SwitchboardEcho.vy`; `ARG-HQ` and action timelocks | `0300`; Switchboard ID 5 `Switchboard Echo`; PSM configuration in `0800_EndaomentPsmDisabled.py` | `ROLE-G`; only supported actions; `ASSERT-D`; `BASE-U`; `ABORT-G` |
| CM-047 `EndaomentFunds` | Selected local custody Department | `contracts/core/EndaomentFunds.vy`; `ARG-HQ` | `0600`; RipeHq ID 21 `Endaoment Funds`; no capability | `ROLE-G`; no external/yield destinations; `ASSERT-S`; `BASE-U`; `ABORT-G` |
| CM-048 `EndaomentPSM` | Scaffolded disabled to preserve ID 22; omission instead requires approved shared sparse-registry redesign | `contracts/core/EndaomentPSM.vy`; `ARG-HQ`; interval/fees/caps/reserve token from approved Track 4 manifest; yield `(0, zero address)` | `0600` deploy/register; `0800` proves disabled; RipeHq ID 22 `Endaoment PSM`; no GREEN capability | `canMint=false`, `canRedeem=false`, auto-deposit false, no approvals; `ASSERT-D`; `BASE-U`; `ABORT-G`; activation separately blocked |
| CM-049 `DefaultsRobinhood` | Selected chain-specific configuration artifact; not divergent protocol logic | Proposed `contracts/config/DefaultsRobinhood.vy`; generated only from approved parameter manifest | Built before `0100`; constructor mirrors canonical defaults interface; not registered | Hash/parity/field-denominator assertions; no Base addresses; `BASE-O`; replacement approved in architecture, values open |
| CM-050 `AeroRipePrices` | Omitted | `contracts/priceSources/AeroRipePrices.vy` | No migration/PriceDesk row | `ASSERT-O`; `BASE-O`; no rollback |
| CM-051 GREEN CCIP BurnMint pool | Live pool reporting `BurnMintTokenPool 1.5.1`; exact creation source identity unresolved | Ownership, routing and GREEN-only capability confirmed in the 2026-08-11 live snapshot; repository-source equivalence, rate policy and full destination-gas evidence remain open | Confirmed RipeHq ID 24 `GREEN CCIP Pool`; `canMintGreen=true`, `canMintRipe=false` | Preserve exact topology; owner disposition for disabled rate limits/zero rate admin; accepted full OffRamp gas evidence; no inferred source equivalence or transaction authority |
| CM-052 RIPE CCIP BurnMint pool | Live pool reporting `BurnMintTokenPool 1.5.1`; exact creation source identity unresolved | Same live evidence boundary as CM-051 with the RIPE-only capability | Confirmed RipeHq ID 23 `RIPE CCIP Pool`; `canMintRipe=true`, `canMintGreen=false` | Same operational and authority gates as CM-051 |
| CM-053 CCIP token-admin registration | Confirmed existing live external state | Current TokenAdminRegistry pool assignments and reciprocal remote wiring are bound by the dated snapshot; exact historical mutation hashes remain an evidence gap | Observed external state, not launch mutation `1000` | Preserve and revalidate; any further transaction requires owner/evidence gates, separate transaction authority, and post-readback assertions |
| CM-054 GREEN/RIPE local price adapter | Deferred; no fabricated peg | Source/artifact and constructor do not yet exist | No migration ID until separate oracle specification; dependent features disabled | `ASSERT-O`; `BASE-M` if new shared source; owner/oracle/security blocked |
| CM-055 deployment/migration/report tooling | Selected follow-on shared tooling, not onchain | `config/BluePrint.py`, deployment scripts and parameter scripts; profile/schema inputs from this specification | No onchain migration; implementation slices H-01–H-08 | Secret-safe, deterministic, chain-neutral assertions; `BASE-M` tooling regression; normal code revert is rollback |
| CM-056 manifests/history | Selected follow-on shared tooling and chain-local evidence | Migration utilities plus schema in Section 15 | No onchain migration; separate RH histories | Atomic/progression assertions; Base reader compatibility; normal code revert cannot erase already-published evidence |
| CM-057 ABI/export/verifier | Selected follow-on shared tooling | `scripts/export_abis.py`, `scripts/verify.py`, provider adapters | No onchain migration; verification follows deployed receipt | Deterministic clean build and truthful provider status; Base regression; code revert only |
| CM-058 CCIP Solidity inheritance/build/test boundary | Repository 1.5.1 candidate source and focused Foundry toolchain integrated; exact live creation binding unresolved | Repository candidate/build tests do not prove the source/compiler/settings/constructor identity of the four live pools | No launch mutation; required input for any future replacement or source-equivalence claim | Preserve pinned dependencies/compiler/EVM/optimizer/IR/metadata and license/notice inputs; source/storage/method delta and inherited behavior tests remain repository evidence only; live identity, full gas, review, and release gates remain open |
| CM-059 Base/RH test profiles | Selected future test tooling | `tests/**`, `tests/conf_core.py`, `tests/conf_utils.py` plus Track 6 inputs | No onchain migration; Deliverable B Stages 1–5 | Pinned/clean fork evidence; Base regression; no production effect |
| CM-060 `DefaultsLocal` | Omitted from RH artifacts; retained for generic local tests | `contracts/config/DefaultsLocal.vy` | No RH migration/manifest record | Assert CM-049 selected for RH; `BASE-U`; no rollback |

### 13.6 Topological deployment graph

The executable graph is:

1. freeze source, dependencies, network profile, approved parameter manifest,
   artifacts, proposed migration plan, and signer capability;
2. build CM-049 and canonical Vyper artifacts; reject dirty/stale output;
3. `0100`: deploy CM-001–006 and CM-004, finish token setup, and prove IDs 1–3;
4. `0200`: deploy/register CM-008 and CM-009 at IDs 4–5;
5. `0300`: deploy CM-010–014 and CM-046, prove Switchboard IDs 1–5, then register
   Switchboard at HQ ID 6 without finalizing timelocks;
6. `0400`: deploy CM-015/016, register Chainlink at PriceDesk ID 1 and PriceDesk
   at HQ ID 7; keep PriceDesk IDs 2–5 empty and semantically reserved, and
   reject any source that would acquire the wrong sequential ID;
7. `0500`: deploy CM-021–025 only after Track 8 artifacts close, prove VaultBook
   IDs 1–4, and register VaultBook at HQ ID 8;
8. `0600`: deploy/register HQ IDs 9–22 in exact canonical order, initially
   withholding optional mint capabilities and enablement;
9. `0700` and `0800`: apply only owner-approved optional configuration; otherwise
   produce explicit disabled assertions without enabling value paths;
10. `0900`: finalize registry/action timelocks, confirm only approved
    capabilities, transfer governance/admin, and prove deployer authority loss;
11. `1000`: remains absent until Track 1/CM-058 close; if later approved, deploy
    pools, complete external registration, verify remote mappings, then grant the
    pool itself—not an adapter—the direct mint capability; and
12. publish immutable step manifests only after each step's finality and
    assertions; promote `current-manifest.json` only after a terminal successful
    plan.

No later step may execute if an earlier registry ID, artifact hash, capability,
or omission assertion differs from the reviewed plan.

## 14. Phase D — migration namespace, reservations, and execution

### 14.1 Owner-approved namespace mapping

The brief originally illustrated separate
`migrations/robinhood-testnet/` and `migrations/robinhood-mainnet/` source
directories. At the early checkpoint, the owner instead selected one canonical
source:

```text
migrations/robinhood/
```

Both network profiles consume that same ordered source. Evidence is isolated:

```text
migration_history/robinhood-testnet/v1/
migration_history/robinhood-mainnet/v1/
```

Canonical profile IDs are `robinhood-testnet` and `robinhood-mainnet`. Marketing
aliases may resolve to these IDs at input validation, but aliases never create a
directory, defaults artifact, plan, or history. This mapping is the explicit
owner-approved replacement for the brief's separate-source examples.

### 14.2 Identifier convention

- Initial clean-deployment IDs are fixed-width four-digit decimal identifiers.
- `0010`–`0080` are pre-deployment Track 6 artifact/assertion gates.
- `0100`–`1000` are Track 7 clean-deployment steps in execution order.
- `1100`–`1999` remain unassigned integration space until the first mainnet
  freeze.
- Post-launch shared migrations begin at `2000` and increase monotonically.
- Before first mainnet execution, unused optional IDs receive an immutable
  `skipped` or `deferred` step record and are never reassigned.
- After first mainnet execution, insertion below the highest executed ID is
  forbidden. Reordering or renaming an executed ID is forbidden.
- Discovery rejects duplicate numeric IDs, duplicate semantic step IDs,
  noncanonical filenames, gaps without an explicit disposition, and a different
  source hash for an already-recorded ID.
- The integration owner is the sole reassigner. Concurrent tracks propose
  reservations; they do not take ownership by creating a colliding file.

### 14.3 Reservation table

All paths below are proposed. No migration file is created by this track.

| ID and intended filename | Purpose / CM IDs | Prerequisites and expected artifacts | Execution class / dependencies | Reassignment owner |
| --- | --- | --- | --- | --- |
| `0010_Track6S3LootboxFloor.py` | Retained S3 Lootbox floor; CM-033 | Integrated reviewed S3 source/tests and approved `7,200`/zero RH posture | Pre-deploy artifact assertion; no separate RH upgrade transaction | Integration owner with Track 6/7 owners |
| `0020_Track6S4DeleverageCooldown.py` | Conditional S4 cooldown/context; CM-014/044 | Zero-cooldown acceptance, or integrated S4 artifact plus wall-time/security approval | Omitted when zero cooldown is accepted; otherwise pre-deploy artifact assertion, upgradeable only through a later new ID | Integration owner |
| `0030_Track6S5LedgerGuard.py` | S5 portable action-block Ledger; CM-008/034 | Integrated reviewed S5 artifact, security-approved source/provider semantics, and explicit permanent Base live-version exception | Mandatory pre-deploy artifact/source/constructor assertion once S5 integrates; no independent RH upgrade transaction and no Base migration | Integration owner |
| `0040_Track6S6DefaultsAndParameters.py` | S6 CM-049/defaults and parameter manifest | Approved field inventory, generated artifact hashes, no Base/default leakage | Pre-deploy configuration-artifact assertion; no onchain action | Integration owner with parameter owners |
| `0050_Track6S7TimelockRegistryValidation.py` | S7 timelock/registry setup | Integrated validation requirements and approved bounds | Assertion step before `0100`; later onchain values are applied by owning deployment step | Integration owner |
| `0060_Track6S8LifecycleCapacity.py` | S8 lifecycle/capacity setup | Integrated capacity/lifecycle decisions | Assertion step; no independent transaction unless implementation proves a distinct governed action | Integration owner |
| `0070_Track6S9DisabledIntegrationAssertions.py` | S9 omitted/disabled graph | Approved negative allowlist covering CM-017–020/035–037/039–042/050/054/060 | Assertion step before plan approval and after deployment | Integration owner |
| `0080_Track6S10CadReportAssertion.py` | S10 CAD reporting correction; CM-055 | Integrated tooling fix and raw/formatted/runtime evidence | Tooling-only assertion, explicitly no onchain transaction or contract migration | Integration owner; a future onchain need receives a new ID |
| `0100_TokensAndRipeHq.py` | Tokens, HQ, contributor blueprint, TrainingWheels, CM-049 binding; CM-001–006/049 | `0010`–`0080`, SavingsGreen disposition, approved constructor manifest, canonical artifacts | Initial-deployment-only; first onchain step | Integration owner |
| `0200_DataAndConfigRegistries.py` | Ledger and MissionControl; CM-008/009 | Finalized `0100`, IDs 1–3, approved defaults hash, S5 provider/source input and artifact assertion | Initial fresh RH deploy; depends on RipeHq; never imports or migrates Base Ledger state | Integration owner |
| `0300_Switchboards.py` | Switchboard and Alpha–Echo; CM-010–014/046 | Finalized `0200`, approved timelocks and supported-action allowlist | Initial deploy; registry IDs 1–5 then HQ ID 6 | Integration owner |
| `0400_PriceSources.py` | PriceDesk and approved Chainlink adapter/feed records; CM-015–020/039–041/050/054 | Finalized `0300`, dated feed facts, external-address freeze | Initial deploy/config; unsupported sources receive negative assertions and PriceDesk IDs 2–5 remain empty/reserved to canonical semantics | Integration owner with oracle owner |
| `0500_VaultsAndAssets.py` | VaultBook and vault artifacts/assets; CM-021–025/042 | Finalized `0400`, reviewed Track 8 outputs, selected assets and exact vault artifacts | Initial deploy/config; VaultBook IDs 1–4 | Integration owner with Track 8 owner |
| `0600_CoreDepartments.py` | HQ IDs 9–22 and BondBooster; CM-026–034/038/043–048 | Finalized `0500`, complete registry/capability plan, all constructor values | Initial deploy; capabilities remain withheld unless separately enabled | Integration owner |
| `0700_SavingsGreenPath.py` | CM-003/022 dependent enablement or explicit disabled record | Owner SavingsGreen/Stability Pool decision and lifecycle tests | Optional configuration; initial-deployment-only disposition | Integration owner with product/risk owner |
| `0800_EndaomentPsmDisabled.py` | CM-046/048 disabled PSM posture | Track 4 parameter manifest; reserve asset/feed facts if deployed; no activation approval | Initial disabled configuration; upgrade-capable later only through a new ID | Integration owner with risk/oracle owner |
| `0900_CapabilitiesRolesAndHandoff.py` | Final capabilities, timelocks, roles and deployer-authority loss; all selected CM rows | Every earlier step finalized; owner-approved accounts/roles/finality; assertion report clean | Irreversible governance handoff; no execution while any role value is unresolved | Integration owner and security/operations owners |
| `1000_CcipPoolsAndRegistration.py` | CM-051–053 | Track 1 facts, CM-058 toolchain, Base/RH pool artifacts, selectors, remotes, limits, external permissions | Deferred upgrade-capable integration; never part of initial graph while pending | Integration owner with Track 1/security owners |

### 14.4 Immutable plan and step model

Before account loading, the tool produces a deterministic plan containing:

- schema version, plan ID and plan hash;
- canonical profile ID and expected chain ID;
- source commit and clean-tree proof;
- dependency/compiler/artifact hashes;
- exact ordered migration/semantic step IDs and code hashes;
- constructor and configuration arguments with provenance;
- expected registry IDs, capabilities, roles, external permissions, and
  dispositions;
- expected transaction count only as diagnostic information, never resume
  identity;
- preconditions, postconditions, reversibility class, finality policy, and
  evidence disposition for every step; and
- prior immutable manifest hash for a resume or upgrade.

Plan mode performs no account loading, signing, provider mutation, or manifest
promotion. A plan changes if any source, dependency, artifact, argument, profile,
address, step, assertion, or prior-manifest hash changes.

### 14.5 Execution semantics

| Operation | Required semantics |
| --- | --- |
| Preflight | Reject dirty source, unresolved required values, open dependency gate, unknown profile, absent RPC, chain-ID mismatch, duplicate/out-of-order IDs, stale artifacts, unsupported verifier, insufficient balance, unapproved backend, and forbidden Base addresses before signing. |
| Dry run | Execute the immutable plan on a clean local environment or pinned clean fork with submission disabled. Produce local evidence linked to the same plan hash; never promote network history. |
| Clean deploy | Require an empty target history and prove expected registry/code absence. An unexpected existing address/state aborts; it is not silently adopted. |
| Checkpoint write | Write a local staged step record after receipt success, then add finality/assertions. Atomically rename it to an immutable step manifest only when complete. Never update `current-manifest.json` mid-step. |
| Idempotent rerun | Recompute the semantic step hash and compare code, constructor values, registry state, capabilities and configuration. If all postconditions already hold, record `already_satisfied`; any difference aborts. |
| Resume | Require the identical plan hash, source/profile/chain, prior immutable step chain and current onchain state. Resume at the first incomplete semantic action, not a positional transaction number. |
| Explicit skip | Require a declared `skipped`/`deferred` disposition, reason, approver, negative assertions and proof that no later dependency requires the step. An operator flag alone cannot skip. |
| Irreversible declaration | Deployment, registry confirmation, capability grant, ownership transfer, external CCIP registration and live-value enablement are individually labeled irreversible or governance-remediable before execution. |
| Receipt/finality | Record transaction hash, receipt success, block number/hash, effective fees and required confirmation/finality result. A receipt without the selected finality rule is not complete. |
| Manifest reconciliation | After every step, compare expected plan state, onchain reads, emitted events and staged evidence. Divergence blocks later steps and current-manifest promotion. |
| Abort | Stop on first failed/ambiguous action; do not broad-retry state-changing calls. Persist sanitized local failure evidence and the last finalized immutable step. |
| Retry | Retry transport reads under the profile policy. A state-changing submission is retried only when nonce, mempool/receipt state and idempotency prove no duplicate effect; otherwise require operator review. |
| Address adoption | A pre-existing address is adoptable only through a separately reviewed adoption step proving source, constructor, runtime hash, ownership, registry absence/state, provenance and external permissions. |
| Address retirement | Disable capabilities/value paths first, reconcile funds/debt/roles, update the registry through governance, and record the old address permanently. Deletion from history is forbidden. |
| Role transfer | Verify target role capability and chain, initiate/confirm through the required timelock or multisig, then prove the prior deployer has no authority. |
| Safe/multisig handoff | Record public Safe address, chain ID, threshold and proposal/transaction identifiers; never signatures, owner private data or complete wallet transcripts. Execution remains blocked until the backend is selected and approved. |

### 14.6 Rollback truth

Contract creation and confirmed external/registry actions are not reversible.
Before confirmation, a pending governed action may be cancelled if the canonical
contract supports cancellation. After confirmation, remediation may mean pause,
capability removal, registry replacement, ownership transfer, a compensating
migration, or abandoning an unused address. Redeployment is not rollback.

The last safe abort boundary for `0900` is before the first final governance
handoff transaction. The last safe abort boundary for `1000` is before external
token-admin/pool registration. Each actual plan must split those transitions
into separately acknowledged semantic actions.

## 15. Phase E — manifest and release-evidence contract

### 15.1 Artifact kinds and progression

Manifest schema version 1 defines:

| Artifact kind | Purpose | Mutability |
| --- | --- | --- |
| `deployment_plan` | Frozen expected graph, values, actions, assertions and reversibility | Immutable after approval; local until approved for retention |
| `step_manifest` | One finalized deployed, configured, skipped or deferred migration step | Immutable and committed under the selected history |
| `current_index` | Generated index of the terminal valid immutable step chain | Regenerated atomically; never the source of truth |
| `release_bundle` | Frozen source/artifact/profile/manifest/runbook/gate summary | Immutable after owner release approval |
| `failure_record` | Sanitized diagnostic linked to a plan/step | Local by default; committed only by separate owner approval |

Every immutable artifact includes its own canonical-content SHA-256 and the prior
artifact hash. A valid history is one linear hash chain. Replacing or deleting an
older step invalidates every later artifact.

### 15.2 Logical schema

The following is a logical schema, not a committed implementation:

```yaml
schema_version: 1
artifact_kind: deployment_plan | step_manifest | current_index | release_bundle
manifest_id: canonical-string
manifest_status: complete | already_satisfied | skipped | deferred
created_at_utc: rfc3339
content_sha256: hex
previous_manifest_sha256: hex-or-null

network:
  profile_id: canonical-profile-id
  display_name: string
  chain_id: integer
  environment: local | test | mainnet
  history_namespace: repo-relative-path
  fork_evidence:
    present: boolean
    source_chain_id: integer-or-null
    source_block_number: integer-or-null
    source_block_hash: hex-or-null
    source_endpoint_id: approved-nonsecret-reference-or-null
    observed_at_utc: rfc3339-or-null

source:
  repository: canonical-repository-id
  commit: full-git-oid
  dirty: false
  plan_sha256: hex

toolchain:
  python: exact-version
  titanoboa: exact-version
  vyper: exact-version
  pytest: exact-version
  solidity_toolchain: exact-version-or-null
  dependency_lock_sha256: hex
  compiler_binary_sha256: hex

migration:
  id: four-digit-string
  semantic_id: stable-string
  filename: repo-relative-path
  source_sha256: hex
  execution_class: assertion | deploy | configure | handoff | external_registration
  reversibility: reversible_pending | governance_remediable | irreversible

components:
  - component_id: CM-NNN
    name: canonical-name
    disposition: deployed | deployed_unregistered | registered_disabled |
      feature_disabled | omitted | deferred | blocked
    disposition_reason: string
    dependencies: [CM-NNN]
    contract:
      address: checksummed-address-or-null
      deployment_form: ordinary | blueprint | implementation | proxy |
        external | configuration_only | null
      canonical_source: repo-relative-path-or-null
      source_sha256: hex-or-null
      compiler_input_sha256: hex-or-null
      abi_path: repo-relative-path-or-null
      abi_sha256: hex-or-null
      creation_bytecode_sha256: hex-or-null
      deployed_bytecode_sha256: hex-or-null
      compiler_version: exact-string-or-null
      constructor:
        normalized_typed_values: []
        encoded_hex: hex-or-null
      immutables: []
    deployment:
      deployer_address: public-address-or-null
      transaction_hash: public-hash-or-null
      receipt_status: integer-or-null
      receipt_block_number: integer-or-null
      receipt_block_hash: hex-or-null
      confirmations_observed: integer-or-null
      finality_policy_id: string-or-null
      finality_result: passed | failed | pending | not_applicable
    verification:
      provider: blockscout | etherscan_v2 | unsupported | not_applicable
      status: verified | failed | pending | provider_unsupported | not_applicable
      browser_url: public-url-or-null
      evidence_timestamp_utc: rfc3339-or-null
      compiler_input_sha256: hex-or-null
    registry:
      registry_component_id: CM-NNN-or-null
      registry_id: integer-or-null
      description: string-or-null
      registered: boolean
    capabilities:
      can_mint_green: boolean
      can_mint_ripe: boolean
      can_set_token_blacklist: boolean
      other: []
    roles:
      governance: public-address-or-null
      admin: public-address-or-null
      guardian: public-address-or-null
      operations: public-address-or-null
      deployer_retains_authority: boolean
    feature_flags: []
    parameters:
      - name: canonical-field
        typed_value: explicit-value
        unit: string
        source: source-reference
    external_addresses:
      - purpose: string
        address: checksummed-address
        source_url: primary-url
        retrieved_at_utc: rfc3339
        source_sha256: hex-or-null
    assertions:
      - assertion_id: stable-string
        status: passed | failed | blocked | not_applicable
        expected: typed-value
        observed: typed-value-or-redacted
        evidence_sha256: hex-or-null

live_version_policy:
  base_source_commit: full-git-oid-or-null
  robinhood_source_commit: full-git-oid
  classification: strict_parity | bounded_temporary_drift | approved_exception
  convergence_deadline: rfc3339-or-null
  approval_reference: string-or-null

pending_decisions: []
launch_blockers: []
```

For a non-fork artifact, `fork_evidence.present` is false and every other
`fork_evidence` field is null. For pinned fork evidence it is true, every field
is populated, the block hash is checked against the recorded source chain, and
`source_endpoint_id` is a reviewed nonsecret reference rather than a URL or
credential. A latest-block observation cannot be converted into committable
evidence after the fact.

### 15.3 Disposition semantics

| State | Required representation |
| --- | --- |
| Contract not deployed | `disposition: omitted`, `deferred`, or `blocked`; `contract.address: null`; explicit reason and negative assertions |
| Deployed but not registered | `deployed_unregistered`; address/receipt/artifacts present; `registry.registered: false`; later plan dependency explicit |
| Registered with capability disabled | `registered_disabled`; registry ID/name present; all capability booleans explicit |
| Feature disabled | Contract/registry may be active, but the named flag is a typed false/zero value with source and assertion |
| Legitimate zero | Parameter entry exists with typed zero, unit, source and assertion; it is not `null` |
| Missing/unresolved value | No typed parameter value; related decision and launch blocker present; the plan cannot execute |

An omitted component never receives an all-zero contract record. A deferred
component may name a future source and reservation, but no address or verification
status may imply deployment.

### 15.4 Evidence storage policy

Committed under `migration_history/<profile>/v1/`:

- complete/already-satisfied/skipped/deferred immutable step manifests;
- their canonical plan hash and prior-manifest link;
- public addresses, public transaction/receipt/block evidence and sanitized
  verification result;
- source/dependency/compiler/artifact hashes;
- registry/capability/role/flag/parameter dispositions;
- sanitized primary-source provenance;
- post-deployment assertion results; and
- generated `current-manifest.json` only after terminal validation.

Local/operator evidence:

- staged/incomplete step records and failure diagnostics;
- provider latency/rate-limit samples and complete request/response bodies;
- gas estimates, balance checks, nonce/mempool diagnostics;
- unsigned or partially signed transaction payloads;
- full Safe proposal payloads and hardware-wallet interaction logs;
- credentialed RPC endpoints; and
- fork snapshots or dirty-state experiments.

Never written to any repository artifact:

- private keys, seed phrases, raw hardware-wallet data or signatures;
- API keys, auth headers, credential-bearing RPC URLs;
- complete wallet/Safe owner transcripts or personal data;
- unsanitized provider responses that contain operational metadata;
- dotenv contents or environment dumps; or
- secrets disguised as constructor/configuration provenance.

### 15.5 Atomic current-manifest generation

`current-manifest.json` is a generated index, not an execution scratchpad:

1. load and schema-validate the complete immutable step chain;
2. verify content hashes, prior links, profile/chain/source/plan consistency and
   the exact expected terminal step set;
3. reject any failed, pending, missing, duplicated, reordered or unknown step;
4. reduce component records by explicit semantic supersession rules, never a
   blind dictionary merge;
5. retain old/superseded addresses and progression references;
6. run every graph, registry, capability, role, omission and artifact assertion;
7. write to a same-directory temporary file, flush, and atomically rename; and
8. record the index hash in the release bundle.

A failed or incomplete run leaves the prior valid current index unchanged. An
initial deployment has no current index until the terminal plan passes. The index
must state `complete: true`, terminal plan hash, step count/list and immutable
head hash; consumers must reject any index lacking them.

## 16. Phase F — verification, ABI, and Solidity boundary

### 16.1 Chain-neutral verifier interface

Every verifier adapter implements:

```text
capabilities(profile) -> provider, languages, formats, key mode, rate policy
is_verified(component_artifact, address) -> typed result
submit(component_artifact, address, constructor_evidence) -> request id
poll(request id, bounded policy) -> verified | failed | pending
browser_url(address) -> public URL
sanitize(evidence) -> committable result
```

Adapter selection occurs only from the validated network profile:

- Base uses an explicit `etherscan_v2` adapter.
- Robinhood uses an explicit `blockscout` adapter.
- Local uses `unsupported`/`not_applicable`.
- Unknown profile, provider, artifact language or format fails before a browser
  link or request is constructed.
- Browser availability is not verification capability.

The Blockscout adapter uses the instance-confirmed interval/burst policy. Until
that policy is known, production bulk verification is blocked; it does not assume
three requests per second or an available key.

### 16.2 Reproducible verification inputs

Each request is derived from the manifest record and must include:

- exact compiler and language;
- canonical compiler standard input and its hash;
- source paths/content hashes and settings;
- optimization, EVM version and metadata settings;
- contract/source name selected without filename guessing;
- normalized typed constructor arguments plus encoded bytes;
- immutable/library/link references;
- creation/runtime bytecode hashes; and
- target profile, chain ID and address.

The adapter records provider response classification and timestamp, but never an
API key or unsanitized request. A mismatch between rebuilt and deployed runtime
hash is `failed`, not `pending`.

### 16.3 Deployment-form behavior

| Form | Verification behavior |
| --- | --- |
| Ordinary contract | Verify the exact source/compiler input and constructor evidence against the deployed address. |
| Vyper blueprint | Record deployment form `blueprint`, blueprint creation/runtime hashes and blueprint address. Submit only if the provider explicitly supports that bytecode form; otherwise `provider_unsupported`. |
| Inherited module | No independent address or verification record. Its source/hash is part of the parent's compiler input and source inventory. |
| Implementation/proxy-like pair | Separate component records for implementation and proxy address, explicit linkage, proxy constructor/init call, storage/implementation slot assertion, and provider-specific verification of each supported address. |
| External address | No source-verification claim by this repository. Record `not_applicable`, provenance, chain code-presence/type assertions and external owner/admin facts where approved. |
| Configuration-only | No address verification; record governed call receipts and post-state assertions. |

If Robinhood's provider cannot verify a deployment form, the truthful manifest
state is `provider_unsupported`. Launch then requires an explicit owner decision;
the tool cannot convert browser visibility or matching local bytecode into
provider verification success.

### 16.4 Deterministic ABI export

The future exporter must:

1. build from a clean temporary output directory;
2. consume the frozen Vyper compiler inputs and, later, a declared Solidity
   artifact index;
3. emit deterministic JSON formatting and sort order;
4. name outputs by language plus source-relative path and contract name, not
   source stem alone;
5. reject duplicate output identities and source/contract collisions;
6. fail the whole run on any compile/export error;
7. compare the complete expected set, rejecting missing and stale files;
8. produce an artifact inventory with ABI/source/compiler hashes; and
9. replace committed output only after the complete build passes.

Proposed collision-safe identity:

```text
scripts/abis/vyper/<source-relative-path-without-extension>/<Contract>.json
```

Changing the existing flat ABI layout requires a compatibility/migration plan for
all consumers. The exact path is a Phase H implementation decision, not permission
to move current files now. Every changed ABI receives semantic review for
functions, events, errors, structs, mutability and selector compatibility; a JSON
diff alone is insufficient.

### 16.5 Thin-Solidity CCIP boundary

Track 1 selects thin Solidity subclasses of Chainlink's concrete
`BurnMintTokenPool`. CM-051–053 remain outside the executable graph until
Chainlink subclass support/version, the production dependency/build path,
production-package review/audit, destination-gas margin, runtime compatibility,
and owner/security decisions close. The exact-hash Round-3 reference review is
evidence for the source shape and Ripe compatibility only.

The approved workflow must produce a declared artifact index containing:

- source/contract identity and source hash;
- exact Chainlink package/source revisions and package integrity;
- exact Solidity version, EVM target, optimizer/via-IR/metadata settings;
- ABI, storage layout, method identifiers, creation/runtime bytecode, and
  hashes;
- proof that the subclasses add only the two capability selectors and no
  storage or bridge override;
- inherited-behavior, unit/invariant/fork/gas result references;
  and
- verification format/provider capability.

Python deployment tooling consumes that index through a versioned interface; it
does not search arbitrary output directories, infer a "latest" artifact, or
become a second compiler/package manager. One path-scoped Solidity build feeds
the existing Python manifest/deployment authority. The same declared pool
artifact must be used for Base and Robinhood counterpart deployment unless a
separately approved source/version policy says otherwise.

The dated Phase-A evidence snapshot still records the pre-decision Solidity
toolchain blocker. Preserve that record as historical evidence. The owner has
now accepted the bounded language boundary, but production integration remains
gated by this section.

## 17. Phase G — clean-deployment validation plan

Deliverable B is
`docs/chains/rh/robinhood-deployment-validation-plan.md`. It is specification
only and defines:

- Stage 1 static/unit and dependency-security gates;
- Stage 2 clean local deployment, semantic resume, manifest promotion and
  reproducible artifact cases;
- Stage 3 pinned, read-only fork/rehearsal behavior;
- Stage 4 Robinhood test-environment validation behind a fresh state-changing
  authorization;
- Stage 5 mainnet rehearsal and restricted release behind a distinct exact-plan
  authorization;
- thirty-seven named negative cases with proposed paths, fixtures, evidence,
  tiers and owners;
- lifecycle, governance, PSM, Stock Token, SavingsGreen and CCIP gates;
- clean-checkout reproduction, diagnostics, evidence retention and launch-gate
  mapping; and
- the expected validation command progression for H-01 through H-12.

No proposed test or runbook exists merely because it appears in that plan. The
validation document is authoritative for future test scope; this document is
authoritative for architecture, ownership and slice ordering.

## 18. Phase H — ordered follow-on implementation slices

### 18.1 File-path and ordering rule

All paths in this section are **proposed future paths** unless they already
exist at the starting commit. The exact file list is part of the review
boundary: a slice that discovers materially different ownership must stop and
update the specification before broadening its PR. Each slice begins from the
previous accepted slice; H-10 through H-12 are not permission for live action.

`Targeted` commands below are future commands that become required when their
files exist. `Full` means the repository-authoritative full suite selected after
H-01; the current candidate is `python -m pytest -q`, executed serially until
isolation is proven.

### 18.2 Slice register

| Slice / purpose and exact expected files | Inputs, dependencies, CM / migration IDs | Allowed outputs and Base impact | Targeted / full validation | Boundary, review, abort/remediation and downstream |
| --- | --- | --- | --- | --- |
| **H-01 dependency-security preflight.** Existing `requirements.in`, `requirements.txt`; proposed `tests/deployment/test_dependency_gate.py` and sanitized gate record `docs/chains/rh/evidence/dependency-security-gate.md`. | Section 4; Track 6 S1 exact profile; CM-055/059; no migration ID. | Only narrowly reviewed pins and test/evidence changes. No contract, default or migration output. `pymdown-extensions` is a separately reviewable docs-only sub-slice and cannot block a compatible deployment-path refresh. Base deployment/test environment can change, so all Base tests are mandatory. | Targeted: `python -m pytest -q tests/deployment/test_dependency_gate.py`; dependency resolution/audit command selected by security reviewer. Full: `python -m pytest -q`. | No dependency install/selection without fresh approval. Security and Track 6 owners review. Abort on unresolved deployment-path high/medium alert, incompatible Vyper/Boa/pytest metadata, or weakened S1 assertion. A docs-only alert remains visible but is not a deployment-path abort by itself. Remediation is pin rollback/new reviewed slice. Downstream H-02–H-09 and every rehearsal. |
| **H-02 network profiles and CLI.** Existing `scripts/migrate.py`, `scripts/console.py`, `scripts/verify.py`, `scripts/utils/migration_helpers.py`; proposed `config/network_profiles.py`, `tests/deployment/test_network_profiles.py`, `tests/deployment/test_secret_handling.py`, `tests/deployment/test_base_profile_regression.py`, and sanitized implementation record `docs/chains/rh/evidence/network-profile-cli-implementation.md`. The helper and record were added to this boundary on 2026-07-24: A-001's silent public test-key fallback is implemented in the helper and cannot be truthfully closed from the three CLI modules alone, while the record preserves reviewed hashes/results without credentials or network evidence. | D-001/002/004/013/014; U-001–008; CM-055/059; no migration. | Code/tests and sanitized local evidence only; no credentials or network evidence. Preserve intended Base selection/history behavior while deleting unsafe fallbacks, eager key reads and non-Base `KeyError` paths. | Targeted: the three proposed test files. Full: `python -m pytest -q`. CLI help/import checks run with relevant env vars absent. | No secret access or live connection. Deployment-tooling plus security and Base owners review. Abort on label fallback, pre-identity account load, unredacted URL, history aliasing or unclear Base behavior. Revert code before use; downstream H-03/H-05/H-07. |
| **H-03 Robinhood blueprint and omissions.** Existing `config/BluePrint.py`; proposed `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`, `config/robinhood_blueprint.py`, `tests/deployment/test_robinhood_blueprint.py`, `tests/deployment/test_robinhood_omissions.py`. | Approved H-02 profile interface; component rows CM-001–060; U-009–011/015; integrated Track 8 specification, validation plan, and M0 evidence; no migration. | Durable Phase A analysis plus schema/code/tests with symbolic required fields and explicit `omitted`, `disabled`, `deferred`, `blocked`; never production addresses. Base blueprint remains value compatible unless separately reviewed. Open M0 and cross-track decisions remain typed blockers rather than guessed selections. Source-hard-coded IDs are distinguished from Base-precedent registration-order constraints that H-05 must satisfy. Clearing a blocker requires a reviewed H-03 amendment; downstream slices consume the blueprint read-only. | Targeted: the two proposed H-03 test files plus `tests/deployment/test_base_profile_regression.py`. H-03 proves registry-slot expectations within its owned tests; the separate `tests/deployment/test_registry_topology.py` remains H-08-owned. Full suite. | No production value acceptance. Protocol, security and cross-track owners review. Abort if a required field can default to Base/zero, source-hard-coded slots shift, a registration-order constraint is mislabeled or cannot be preserved, or unresolved Track inputs are flattened. Code revert is remediation; downstream H-04/H-05/H-09. |
| **H-04 `DefaultsRobinhood` and parameter manifest.** Proposed `contracts/config/DefaultsRobinhood.vy`, `config/robinhood-parameters.json`, `tests/config/test_defaults_robinhood.py`, `tests/deployment/test_network_clock_profiles.py`; existing `scripts/params/regenerate_defaults.py`, `scripts/params/run_all.py`. | CM-049; selected minimal Track 6 dispositions through S6; approved inventory/parameters still required; predeployment reservations `0010`–`0060`. | Shared interface-compatible contract source, generator and tests; generated parameter artifact only from approved typed input. No production values in the PR unless separately approved. `DefaultsBase.vy` must not change; S3's approved floor input is included; S4 fields remain absent unless its necessity gate closes; S5 provider/source inputs come only from the reviewed Stage A/implementation artifact and must not be guessed here. | Targeted defaults/generator tests, Track 6 S1 profile, deterministic regeneration/diff. Full suite. | No further parameter or contract-change approval implied. Protocol, risk, Track 6 and security owners review. Abort on protocol logic, denominator/unit ambiguity, Base address, unapproved value, presumed S4 field, guessed S5 input, or non-deterministic generation. Remediation is source revert/new approved parameter artifact; downstream H-05/H-09. |
| **H-05 migration namespace, discovery and skeletons.** Existing `scripts/migrate.py`, `scripts/utils/migration.py`, `scripts/utils/migration_runner.py`, `scripts/utils/migration_helpers.py`; proposed `tests/deployment/test_migration_discovery.py`, `tests/deployment/test_execution_plan.py` and the reserved `migrations/robinhood/` namespace. | D-006/009/014; CM-001–060; selected Track 6/8 dispositions; reservations `0010`–`1000`. | Discovery/plan code, inert skeletons and tests only. `0010` is the retained S3 assertion; `0020` is omitted/assertion-only if S4 stays unchanged; `0030` asserts the integrated S5 artifact/source inputs before the fresh `0200` Ledger deployment and never migrates Base. A reservation cannot force an independent contract migration. Skeletons cannot transact or contain values until later reviewed slices; `0080` remains tooling-only. Base migrations/histories are never rewritten. | Targeted migration discovery/execution-plan tests plus dry plan generation for both RH profiles; full suite; negative proof that rejected contract-change steps cannot execute and no Base Ledger migration can enter the plan. | No state-changing execution. Tooling, protocol, Track 6/8 and security reviewers. Abort on a migration implied only by an old reservation, duplicate/order collision, source split, executable placeholder, or Base history write. Remove unused skeleton before publication; after an ID is published, remediate forward. Downstream H-06/H-08/H-09. |
| **H-06 manifest schema and evidence writer.** Existing `scripts/utils/migration.py`, `scripts/utils/json_file.py`; proposed `scripts/utils/manifest_schema.py`, `docs/chains/rh/schemas/deployment-manifest-v2.schema.json`, `tests/deployment/test_manifest_schema.py`, `tests/deployment/test_current_manifest_promotion.py`. | Section 15; D-009; CM-056; all migration IDs. | Schema/writer/tests and local fixtures. No live manifest. Preserve read compatibility for existing Base history; never rewrite it in place. | Targeted proposed files; parse every committed historical JSON; fault-inject partial writes; full suite. | No secrets/raw provider payloads. Release-evidence and security owners review. Abort if incomplete history can promote, legitimate zero equals missing, prior evidence mutates, or Base reader breaks. Code rollback cannot retract published evidence; remediate with new schema/version. Downstream H-07–H-11. |
| **H-07 verification, ABI and artifact handling.** Existing `scripts/verify.py`, `scripts/export_abis.py`, `scripts/utils/verify_etherscan.py`; proposed `scripts/utils/verifier.py`, `scripts/utils/verify_blockscout.py`, `tests/deployment/test_verifier_adapters.py`, `tests/deployment/test_abi_export.py`; generated `scripts/abis/vyper/**` and a separate declared Solidity namespace only after path compatibility approval. | Owner-approved D-005 direction; U-005; CM-057/058; Section 16; Track 1 interface only, no production CCIP artifacts yet. | Adapter/export code, tests, deterministic ABI inventory. Base Etherscan-v2 behavior and ABI consumers require regression/migration review. No verification submission in PR validation. | Targeted verifier/ABI tests; clean two-build hash comparison; Base verifier mocks; full suite. | No credential/key use, rate-limit selection, public submission, or live verification is authorized. Compiler, verifier, security and Base owners review. Abort on provider fallback, guessed artifact, unsupported-success claim, rate-policy assumption, stale/colliding ABI or consumer break. Revert code/restore last reviewed generated set before publication. Downstream H-08–H-12. |
| **H-08 post-deployment checker.** Proposed `scripts/check_deployment.py`, `scripts/utils/deployment_assertions.py`, `tests/deployment/test_post_deployment_assertions.py`, `tests/deployment/test_registry_topology.py`. | CM-001–060, Sections 13/15, Track 6 S9; migrations `0010`–`1000`. | Read-only checker code/tests and sanitized assertion fixtures. Must support Base via explicit profile expectations, not RH assumptions. | Targeted proposed tests; run checker against local golden Base/RH fixtures; full suite. | No live RPC unless separately approved read-only rehearsal. Protocol, security and evidence owners review. Abort if omitted state cannot be proved, any mismatch is warning-only, registry IDs can shift, or checker mutates state. Code revert/new assertion version is remediation. Downstream H-09–H-11. |
| **H-09 clean-deployment and negative suite.** Proposed `tests/deployment/test_clean_deployment.py`, `test_resume_reconciliation.py`, `test_reproducible_artifacts.py`, and `tests/deployment/fork/**` fixtures with network disabled by default; consumes all Stage 1 files, including H-04's `tests/deployment/test_network_clock_profiles.py`. | H-01–H-08; Track 6 S1/S2 and selected configuration/no-change/implemented dispositions for S3–S10; Track 8 launch decision; CM-001–060; selected migration IDs. | Tests/fixtures only; local generated histories remain temporary. Base full suite and ordinary/repeated/jumping-number profiles mandatory. S5 must prove the fresh RH action-block source while treating live Base as retained regression evidence, not a migration target. | Every selected Stage 1/2 target; two clean builds; `python -m pytest -q` serially. Prove omitted contract changes and disabled features as negative invariants. | No secret or public state change. QA, protocol, security and all cross-track owners review. Abort on nondeterminism, manual repair, unproved omission, accidental changed artifact, flaky shared state or Base regression. Fix owning slice; downstream H-10/H-11. |
| **H-10 test-environment deployment/runbook.** Proposed `docs/chains/rh/runbooks/robinhood-testnet-deployment.md`, `tests/deployment/live/test_robinhood_testnet_deployment.py`, `test_robinhood_testnet_lifecycle.py`, `test_robinhood_governance.py`, `test_robinhood_psm.py`, `test_robinhood_ccip.py`; authorized outputs only under `migration_history/robinhood-testnet/v1/`. | V-00–V-10; H-01–H-09; selected CM graph; `0010`–`1000`; exact approved test values/roles. | Runbook/live harness before action; public sanitized manifests only after a separately authorized run and review. No Base production change; Base Sepolia CCIP action is separately gated. | Stage 4 dry run, exact plan digest, then only separately authorized live commands; rerun full static/local suite before and after evidence review. | Requires fresh owner authorization, signer/provider/funds and external-action approvals. Operations, protocol, security, risk, Track owners approve. Abort on any stale fact/hash/gate, ambiguous receipt, assertion failure or unexpected authority. No chain rollback; pause/disable/orphan/adopt/forward migration only. Downstream H-11 and release decision. |
| **H-11 production rehearsal/restricted-release runbook.** Proposed `docs/chains/rh/runbooks/robinhood-mainnet-rehearsal.md`, `docs/chains/rh/runbooks/robinhood-mainnet-restricted-release.md`, `tests/deployment/live/test_robinhood_mainnet_preflight.py`; authorized outputs only under `migration_history/robinhood-mainnet/v1/`. | Accepted H-10 evidence; every DR row closed for selected graph; exact production source/plan/roles/values; `0010`–`1000`. | Documentation, read-only/preflight harness and reviewed release bundle template. No production manifest until separately authorized transactions finalize. Base effects only through separately approved Base migrations/CCIP registration. | Stage 5 two-environment rebuild, full suite, exact-plan rehearsal and preflight. Production command is deliberately absent until separate authorization names plan hash/backend. | No production authority from this spec. Owner, operations, governance, security and risk approve. Abort on any unresolved required field, changed fact/hash, insufficient balance, verifier/finality mismatch or authority gap. Onchain remediation is pause/disable/forward migration; never claim rollback. Downstream restricted-release decision. |
| **H-12 CCIP thin-Solidity inheritance/artifact integration.** Proposed production path `contracts/ccip/RipeCcipBurnMintTokenPools.sol`, `scripts/artifacts/ccip-artifact-index.json`, `tests/deployment/test_ccip_artifact_index.py`; the exact-hash Round-3-reviewed reference remains under `docs/chains/rh/examples/` and is not deployable source. | Track 1 subclass support and supported pool/API reference; CM-051–053/058; migration `1000`; Base/RH mappings, gas, lifecycle and role decisions; fresh owner/security authority for the Solidity build package. | Only pinned Chainlink dependencies plus the two-view subclasses, retained license/notice/grant files, declared artifact index, delta/review evidence, tests and exact compiler/EVM metadata. Generated artifacts follow Section 16. Same token-specific pool artifact on both chains unless separately approved. | Solidity build plus storage/method/source delta, exact inherited ABI/behavior, artifact-index/ABI/verifier, fork destination-gas, cross-chain integration and full Base/RH suites. | Fresh production-implementation and external-action approvals required. Track 1, compiler, protocol and security owners review. Abort if the subclass is unsupported, exact dependency/settings cannot be named, any storage/bridge override appears, the pool is not direct mint caller, artifacts or license inputs are guessed, gas margin/review is absent, versions unsupported, or remote/role facts remain open. Remediation before deployment is code revert; after registration use revoke/chain removal/token or RipeHq stops/forward migration and supply reconciliation. Downstream separate CCIP activation release. |

The proposed one-file production shape for H-12 reflects the selected reference
but remains unapproved until Track 1 confirms subclass support and the exact
reference, and owner/security review accepts the dependency, lifecycle, role,
gas, and review gates. The stable interface/output paths above reserve
ownership; inability to name exact dependency/compiler/EVM/test inputs is a
pre-PR abort condition rather than permission to fabricate them.

## 19. Required decision register

Recommendations in this table are not approvals. `Owner-approved specification
direction` records only the user's 2026-07-23 authorization; it does not approve
a provider, address, role, dependency, toolchain, parameter, inventory or live
action.

| ID / decision area | Options and evidence | Recommendation | Owner / prerequisite / deadline-slice | Status |
| --- | --- | --- | --- | --- |
| DR-001 Robinhood mainnet facts | Chain ID `4663`, official RPC/explorer facts and dated probes in Sections 6/12; production provider, gas and finality remain unknown. Options: official public RPC for operations or approved production provider. | Use verified identity/explorer facts; prohibit public RPC for production operations unless Robinhood explicitly approves it; freeze provider/fees/finality at H-11. | Operations + security; U-001–005; before H-10 rehearsal and H-11 freeze. | Facts verified; production values open. |
| DR-002 Robinhood test environment | Official testnet chain ID `46630` and explorer are documented; adequacy/funding/soak/support are unconfirmed. Options: official testnet or owner-approved production-like alternative with stated limitations. | Prefer official testnet after provider/operational qualification; otherwise document the alternative's missing guarantees. | Owner + operations; V-07/V-09; before H-10. | Open; no environment approved. |
| DR-003 network-profile API | Parallel dictionaries versus immutable registry; Sections 5/7 and A-001–A-017 evidence. | One immutable typed registry, opaque URL envs, exact chain-ID equality, pinned fork evidence and plan-bound acknowledgments. | Deployment tooling + security; D-001/002/004/013/014; H-02. | Owner-approved specification direction; implementation pending. |
| DR-004 migration namespace/version | Split RH sources versus shared source; separate histories; current duplicate/history defects in Section 3. | Shared `migrations/robinhood/`; histories `migration_history/robinhood-{testnet,mainnet}/v1/`; IDs `0010`–`1000`, postlaunch from `2000`, duplicates fatal. | Deployment owner; D-006/009; H-05. Reassignment only by owner before publication. | Owner-approved specification direction; files not created. |
| DR-005 manifest/release evidence | Mutable current manifest versus immutable hash-linked steps plus generated index; Section 15. | Use the Section 15 schema and committed/local/never-stored split; approve retention before H-10. | Release-evidence + security; H-06 then H-10. | Semantic plan/atomic-promotion direction approved via D-009; schema/retention still reviewable. |
| DR-006 live-version policy | Strict parity, bounded temporary drift, or narrow permanent exception per component; component rows mark `BASE-U/M/O`. | Default strict parity; temporary drift needs owner-approved convergence commit/deadline. CM-008 is the approved permanent exception: the live Base Ledger remains untouched because migrating its state is unacceptably risky, while RH receives the revised canonical source fresh. Other permanent exceptions remain gated. | Protocol + security + governance; Track 6/8/1 outputs; freeze before H-10/H-11 for selected components. | CM-008 permanent live-bytecode divergence owner-approved; all other component decisions remain open unless separately recorded. |
| DR-007 SavingsGreen/sGREEN | Active deployment; inert slot-preserving scaffold; or canonical sparse-registry redesign/omission. Hard-coded HQ ID 2 evidence in Section 13. | Keep CM-003 scaffolded and downstream paths disabled for implementation planning; owner must choose active versus reviewed inert posture before H-05 executable steps. | Product + protocol + risk; graph/lifecycle decision; H-03/H-05 deadline. | Open; no deployment/inventory approval. |
| DR-008 Stock Token vault | Existing vault with accepted risk, smallest demonstrably sufficient shared containment patch, or broader corrected-share design; Track 8 and Track 5 evidence. Omitting Stock Tokens is no longer an initial-launch option. | Stock Tokens are mandatory for initial launch. Use only the reviewed Track 8-selected minimum sufficient artifact; keep registration/borrowing/CreditRedeem/Stability swap disabled until its invariant, tests, exact token facts, and owner/security/risk acceptance close. | Track 8 + security + risk + owner; before H-04/H-05 values and H-09 lifecycle. | Product direction owner-approved; exact containment artifact and activation remain open. |
| DR-009 USDG/PSM | Omit, or deploy ID-22 scaffold disabled, or activate after Track 4. Hard-coded topology and Track 4 evidence. | Preserve disabled scaffold only if shared topology requires it: `canMint=false`, `canRedeem=false`, no GREEN capability, auto-deposit/yield disabled. Activation is a separate release. | Track 4 + oracle + risk + owner; before H-05 `0800`, activation after separate gates. | Existing Chainlink price-path direction recorded; no reserve/address/parameter, deployment posture or activation approved. |
| DR-010 CCIP | Supported release/toolchain/assisted registration versus shared token revision; Track 1 record. | Keep CM-051–053 and `1000` deferred; use direct pool mint capability, same pool artifact on both chains and declared artifact index after Track 1. | Track 1 + Chainlink channel + compiler/security/owner; before H-12. | Assisted registration is the recorded preference; supported path/release/toolchain/address/capability remain open. |
| DR-011 governance/admin roles | EOA, Safe/multisig, timelock and scoped guardian/operations combinations. Current tooling exposes unsafe account assumptions. | Capability-based signer backend; local timelock/Safe governance; explicitly scoped guardian/operations; prove deployer authority absent. | Governance + security + operations; U-004 and final graph; before H-10. | Open; no address/backend/role approved. |
| DR-012 external addresses | Copy research snapshot versus primary-source freeze and recheck. | Require checksum, code/type/decimals/interface, primary URL/retrieval date/hash and final pre-sign re-query; changed fact invalidates plan. | Component owner + security; relevant track gates; H-03 candidate data and H-10/H-11 freeze. | Open; no production address approved. |
| DR-013 gas/finality/retries | Guessed confirmations/static fee/retry versus provider evidence, caps and semantic ambiguity handling. | Dynamic RPC estimation within approved caps; instance-tested confirmation/finality; no broad state retry; ambiguous submission stops for reconciliation. | Operations + security; U-002/003 and testnet evidence; before H-10/H-11. | Open; all production values unresolved. |
| DR-014 CI | Local-only; fast/integration PR tiers plus protected fork/live jobs; no existing workflows. | Add fast/integration only after isolation; protected manual fork/live jobs with environment approvals and no untrusted secret access. | CI + security + QA; H-09 evidence; separate CI slice after H-09. | Proposed; no CI change authorized. |
| DR-015 dependency supply chain | Accept alerts, non-pytest refresh plus separate pytest decision, or broader upgrade; Section 4 alert/metadata evidence. | Release-block deployment-path high/medium alerts until fixed or explicitly accepted; split mechanical pins from pytest; review upstream behavior per package and intentionally reapprove S1. | Security + Track 6 + dependency owner; before H-01 acceptance and any rehearsal. | Open; no pin refresh approved. |
| DR-016 Base upgrades | No Base action; simultaneous convergence; bounded later migration; or approved permanent exception. Component `BASE-*` rows and current immutable/state-bearing deployments are evidence. | Preserve intended Base behavior in every slice; assign Base migration IDs only after a concrete shared-bytecode change and explicit owner approval. CM-008 has the selected no-Base-action/permanent live-bytecode exception; no migration ID or convergence deadline may be created for it. | Base deployment + protocol + governance; each other `BASE-M` slice before merge, final freeze H-11. | CM-008 exception owner-approved; every other Base migration/divergence remains open. |

## 20. Operator and release-evidence workflow

This is an implementation-ready control sequence, not a production runbook or
authorization:

1. freeze the full source commit and clean tree;
2. close H-01 and record the reviewed dependency profile;
3. select a canonical profile and resolve only its required environment
   references;
4. prove the RPC chain ID before account backend initialization;
5. build from declared inputs and compare source/compiler/ABI/bytecode hashes;
6. generate the semantic plan, graph, omissions, irreversible boundaries and
   typed values; record its digest;
7. obtain the approvals required for that exact plan, profile and action tier;
8. preflight balance/nonce/fees/finality/provider/verifier/roles without
   exposing credentials;
9. execute one semantic step at a time, stopping on ambiguity or failed
   receipt/finality/postcondition;
10. write immutable sanitized step evidence atomically;
11. reconcile code, constructors, registry IDs, capabilities, roles, flags,
    parameters, omissions and external facts;
12. transfer roles and prove deployer authority loss;
13. promote `current-manifest.json` only from the complete validated chain;
14. archive the release bundle and separately retained local diagnostics; and
15. enable no optional value path without its own owner gate and new plan.

Any failed transaction or already-created address is historical fact. The
operator may stop, leave it unadopted, disable it where authority permits, or
propose a forward migration. The operator must never edit history or call a new
deployment/role transfer a rollback.

## 21. Cross-track reconciliation and exact summary handoff

### 21.1 Collision and ownership record

| Interface | Track 7 reservation | Other-track boundary | Current collision status |
| --- | --- | --- | --- |
| Clock changes | `0010`–`0080` predeployment gates and assertions | Track 6 owns contract/tooling implementation and S1/S2 evidence | No file collision found; IDs are provisional until integrated outputs reconcile |
| Vault/Stock | `0500_VaultsAndAssets.py`, manifest/assertion surfaces | Track 8 owns vault semantics, shared fixes and selected artifact; it explicitly delegates exact RH migration IDs/tooling to Track 7 | No collision in brief-only input; Track 8 must not create a second RH migration ID/history |
| USDG/PSM | `0800_EndaomentPsmDisabled.py` | Track 4 owns price/reserve/activation decisions and implementation | No collision found; `0800` may assert omission instead if owner selects an approved sparse redesign |
| CCIP | `1000_CcipPoolsAndRegistration.py`, CM-051–053/058 artifact interface | Track 1 owns supported release, questions, registration facts and Chainlink channel | No file collision found; source/build files remain blocked |
| Component identities | CM-001–060 are consumed without renumbering | Track 3/component matrix owns stable identity/disposition reconciliation | No renumbering; provisional graph dispositions remain owner-review items |
| Summary checklist | This section reports eligibility only | Owner alone edits/checks `docs/chains/rh-summary.md` | File intentionally unchanged |

The integration branch advanced after kickoff in two documentation commits:
the Track 8 brief at `be6a759e15e763b633feefdce91cf8f3ee31a10e`
(SHA-256
`c885c25f5a19f0531a15ce947534a4a054bf6e18ef7f198734d879dfd6a52637`)
and the owner-approved checklist reconciliation at `ce3805d`. Track 7 did not
merge, cherry-pick, push or edit that branch. The Track 8 brief remains a
pending interface input, not reviewed Track 8 output; the two `ce3805d` input
dispositions are recorded in Section 2.7.

### 21.2 Exact `rh-summary.md` Section 1 checklist handoff

The table quotes the Section 1 checklist item lead text exactly enough to
identify the owner-controlled checkbox. `Eligible for owner review` means this
specification supplies an implementation-ready direction; it does **not** mean
the checkbox is complete.

| `rh-summary.md` Section 1 item | Track 7 specification / implementation handoff | Eligibility |
| --- | --- | --- |
| “Add explicit Robinhood mainnet and testnet targets to the migration CLI and network configuration.” | Sections 5, 18 H-02; implement and pass Stages 1–3. | Eligible for owner review as a specification; implementation unchecked |
| “Add Robinhood chain IDs, RPC selection, explorer/verification support, gas settings, confirmation policy, and environment-variable handling without inheriting Base/Alchemy/Basescan assumptions.” | Sections 5–8, 16, DR-001/002/003/013, H-02/H-07; production settings remain open. | Eligible for owner review with production-value blockers |
| “Add a dedicated Robinhood blueprint containing only verified Robinhood addresses:” | Sections 13, 18 H-03, DR-012; exact addresses remain unapproved. | Eligible for owner review; implementation/value freeze unchecked |
| “Add `DefaultsRobinhood` or an equivalent generated defaults artifact rather than modifying `DefaultsBase` in place.” | CM-049, H-04, DR-016. | Eligible for owner review; implementation/parameters unchecked |
| “Treat `DefaultsRobinhood` as the intended chain-specific contract exception: it supplies Robinhood values and inventory but must not contain divergent protocol logic.” | CM-049 and H-04 abort conditions. | Eligible for owner review; implementation unchecked |
| “Create separate Robinhood testnet and mainnet migration trees and manifest histories.” | Owner-approved variance in Section 14: one shared source tree, separate testnet/mainnet histories; H-05/H-06. | Eligible only with the recorded owner variance; implementation unchecked |
| “Establish the Robinhood release-artifact convention: define the `migration_history/` paths, which manifests and verification outputs are committed, and where any evidence too large or sensitive for Git is retained.” | Sections 14–16 and 20; H-06/H-07. | Eligible for owner review; implementation/retention approval unchecked |
| “Make the Robinhood migration sequence deploy the same canonical contract implementations selected for Base, plus only the explicitly approved shared additions such as CCIP pools, and configure all registries, Departments, Switchboards, assets, price sources, and governance roles.” | Sections 13–14; H-04/H-05/H-12. Inventory and production values remain owner gates. | Eligible for graph/reservation review; executable deployment unchecked |
| “Make every omitted integration explicit in the deployment manifest; do not silently substitute zero addresses where downstream code expects a live contract.” | Sections 13/15; H-03/H-06/H-08/H-09; NEG-016/017/024. | Eligible for owner review; implementation unchecked |
| “Add post-deployment verification that checks deployed bytecode, constructor arguments, registry IDs, Department mint permissions, governance ownership, token/feed mappings, feature flags, and parameter values.” | Sections 15/20; H-08; validation Stages 2–5. | Eligible for owner review; checker/tests unchecked |
| “Ensure contract export/ABI and explorer-verification tooling supports every new Robinhood and CCIP contract.” | Section 16; H-07/H-12; CCIP remains Track 1/toolchain blocked. | Eligible for Vyper/Solidity adapter review; CCIP portion blocked |
| “Prevent Robinhood manifests from containing accidental Base token, oracle, DEX, yield, treasury, or Underscore addresses.” | CM omission rows; H-03/H-08/H-09; NEG-003/016/024. | Eligible for owner review; implementation/test evidence unchecked |

### 21.3 Completion status and open stop conditions

Phases A–H and both owned deliverables are complete at specification level and
eligible for owner/reviewer scrutiny. Track 7 is **not implementation-complete**
and no `rh-summary.md` checkbox is eligible to be marked complete yet.

The launch-critical open items are DR-001/002/006–016 and U-001–015 as
applicable. In particular, dependencies, Track 6/8/4/1 outputs, component
inventory, live versions, addresses, parameters, provider, finality/fees,
signing backend, roles, test environment, toolchain and optional Savings/Stock/
PSM/CCIP paths remain unapproved. Those open items do not prevent the two
specification documents from review; they intentionally prevent implementation
or live release from masquerading as approved.

## 22. Final specification-validation record

Validation was run in the isolated Track 7 worktree on 2026-07-23:

| Check | Result |
| --- | --- |
| Frozen input SHA-256 recomputation | All six Section 2.3 values match |
| Component inventory | Exactly one contiguous row for CM-001–060 |
| Migration reservations | 18 unique ordered IDs: `0010`–`0080` by tens and `0100`–`1000` by hundreds |
| Follow-on slices / decisions | H-01–H-12 and DR-001–DR-016 are contiguous and unique |
| Negative validation | NEG-001–NEG-037 are contiguous and unique |
| Section 1 handoff | 12 owner-controlled checklist rows; source text unchanged by observed parallel edits |
| Historical JSON | All 58 committed `migration_history/**/*.json` files parse |
| Existing numeric migration audit | 62 numeric files; only the recorded duplicate `2025071506` appears twice |
| Markdown structure | Fenced blocks balanced; every table has a consistent column count |
| Paths | Starting-commit source/runtime paths exist; absent paths are marked proposed/future, abstract schema paths, or the separately recorded Track 8 integration input |
| Corrected facts | Mainnet chain ID consistently `4663`; interval-based verifier limit schema; documented default represented as 3 requests/minute with instance confirmation required |
| Whitespace | `git diff --check` and the untracked-file `git diff --no-index --check` pass |
| Repository-native Markdown command | None found; no documentation dependency added |
| Changed-file scope | Only the two Track 7-owned Markdown deliverables |
| Prohibited actions | No code/test/dependency/default/migration/manifest/ABI/CI edit; no secret access; no external state change; no push/merge |

The searches for RPC, explorer, chain, environment, migration and manifest
assumptions were rerun over `scripts/migrate.py`, `scripts/verify.py`,
`scripts/console.py`, `scripts/utils/**` and `config/BluePrint.py`; the Phase A
findings remain applicable. No implementation test suite was run because this
track changes specifications only. The completion commit is recorded in the
owner handoff because a commit cannot contain its own final object ID.
