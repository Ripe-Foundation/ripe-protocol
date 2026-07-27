# Robinhood manifest v2 and immutable evidence chain — H-06 Phase A

Status: **PHASE A OWNER DECISIONS OD-01 THROUGH OD-12 APPROVED / PHASE B NOT AUTHORIZED**

This is the Track 7 H-06 Phase A static-analysis and architecture artifact. It
does not authorize implementation, evidence creation, migration execution,
signing, broadcasting, deployment, or promotion. The owner approved OD-01
through OD-12 exactly as presented at the pre-approval artifact SHA-256
`4458b90dc878c4e3ff2e2c0d6fc8b32e1baf7a7e33c1c8c15002b8524680ddc2`,
selecting each Recommended choice. Section 12 records that approval verbatim.
The external SHA-256 reported after this provenance-only amendment is its
review identity; embedding that post-amendment digest here would create a
self-reference.

## 1. Scope, baseline, and authority

The audit was performed from the following exact clean baseline:

| Item | Audited value |
| --- | --- |
| Integration branch | `rh` |
| Source commit | `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` |
| Source tree | `b2c2358f565e27ad6a5c787a9a0d1396af513076` |
| Phase A branch | `rh-track-7-h6-manifest-schema-phase-a` |
| Phase A worktree | `/Users/wigglez/dev/ripe-protocol-track-7-h6-manifest-schema-phase-a` |
| Permitted output | This document only, left untracked, unstaged, and uncommitted |

The controlling repository inputs are the
[Track 7 plan](../track-7-robinhood-deployment-support.md), the
[deployment-support specification](../robinhood-deployment-support-specification.md),
the [validation plan](../robinhood-deployment-validation-plan.md), and the
[integrated H-02 evidence](network-profile-cli-implementation.md). The current
implementation and tests were audited directly:

- [network profiles](../../../../config/network_profiles.py),
  [CLI](../../../../scripts/migrate.py), [migration object](../../../../scripts/utils/migration.py),
  [runner](../../../../scripts/utils/migration_runner.py),
  [helpers](../../../../scripts/utils/migration_helpers.py), and
  [JSON helper](../../../../scripts/utils/json_file.py);
- [Base regression](../../../../tests/deployment/test_base_profile_regression.py),
  [network profile](../../../../tests/deployment/test_network_profiles.py),
  [secret handling](../../../../tests/deployment/test_secret_handling.py), and
  [dependency gate](../../../../tests/deployment/test_dependency_gate.py) tests;
- every committed JSON file under
  [`migration_history/base-mainnet/v1`](../../../../migration_history/base-mainnet/v1).

### 1.1 H-05 version reconciliation

The complete integrated H-05 evidence was re-read at controlling `rh` commit
`7a3a36666f277277fa08b55081b3f58c7cd3ba64`. Its exact SHA-256 is
`28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c`,
1,092 lines, and 77,432 bytes. The committed blob is
`cc730d393daad01c7403c4305770d2b33209c752`. These integrated bytes are the
controlling H-05 Phase A authority for this reconciliation. Earlier versions
remain provenance only.

| H-05 SHA-256 | Observation | Authority result |
| --- | --- | --- |
| `702875b1775b02fb3ee124fa8d9995b92d93ecdc917cd5b4bb7b48f603e9dd79` | Directly observed and read during the initial H-06 pass; later replaced while still untracked. | Non-controlling: not reviewed, committed, or integrated. |
| `4c54a759d5e468fe55f2b53ce2157391e7c9f5e37547db502a40a16db9699fe1` | Directly observed and read after the first concurrent change; later replaced while still untracked. | Non-controlling: not reviewed, committed, or integrated. |
| `a4dced33f48aa71246a5fa2a1018d12eb0b7b4b4c821838f7f52957fe09b8315` | The integrated H-05 evidence records this as the 994-line byte set against which H-05 OD-01 through OD-12 received direct owner approval. | Approval-source provenance incorporated by the controlling H-05 evidence; not a substitute for the final integrated H-05 bytes. |
| `283e9fbed4b62efaec70e6ec44a78ddc7a7e53d1d5042b289162bd7412c4e77a` | Directly observed and read completely as the 1,051-line current artifact during this reconciliation; later replaced while still untracked. | Non-controlling: not independently reviewed, committed, or integrated. |
| `e90a584d758595c5084f6db30d871e7349df2ffa13cb77641b1f784163038c9d` | Then-current 1,056-line artifact read completely in the prior H-06 reconciliation and later replaced while still untracked. | Non-controlling: not independently reviewed, committed, or integrated. |
| `0643eb8c2c71821e864ed48d2a3939c618e43825dc96a0643c18d6e5c37281a8` | Historical starting candidate identified by full SHA-256 in the final reconciliation; the integrated H-05 evidence refers to this version by the `0643eb8c` prefix in its audit-diff provenance. | Non-controlling provenance only; the historical bytes are not substituted for integrated evidence. |
| `28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c` | Read completely in this reconciliation. Originally committed as `28d2dc9b2fb3b9e55d792b811ce5738555e1762a`, tree `e016bc121d5e1b8fb64b0e73b67981af0142e22e`; present unchanged at integration commit `7a3a36666f277277fa08b55081b3f58c7cd3ba64`, tree `515832eeb23bff94e6ef56e43d27434bbdcd7a81`. | Controlling H-05 Phase A evidence. Its approved design binds this H-06 reconciliation but does not authorize either Phase B. |

The controlling H-05 boundary is exact:

- its future Phase B ceiling is six files:
  `docs/chains/rh/evidence/robinhood-migration-phase-a.md`,
  `config/network_profiles.py`, `scripts/migrate.py`,
  `scripts/utils/migration_runner.py`,
  `tests/deployment/test_migration_discovery.py`, and
  `tests/deployment/test_execution_plan.py`;
- H-05 owns deterministic import-free discovery, the typed blocked plan/report,
  semantic ordering and refusal, RFC 8785/JCS report serialization, and
  `report_sha256`;
- the H-05-side semantic history protocol lives only in
  `scripts/utils/migration_runner.py`, with its Phase B synthetic only in
  `tests/deployment/test_execution_plan.py`;
- H-06 owns the real reader, schema, canonical serialization, plan digest,
  immutable writer/hash chain, and current promotion; and
- H-05 Phase B excludes `scripts/utils/migration.py`,
  `scripts/utils/migration_helpers.py`, all submission/retry/result
  classification, namespaces, histories, and execution.

The complete interface sources at controlling `rh` were also re-read:
`config/network_profiles.py`, `scripts/migrate.py`,
`scripts/utils/migration.py`, `scripts/utils/migration_runner.py`,
`scripts/utils/migration_helpers.py`, `scripts/utils/json_file.py`, and
`scripts/utils/deploy_args.py`. Their SHA-256 values exactly match the
integrated H-05 input ledger. H-05 integration therefore changed no
implementation byte and created no overlap in `migration.py`.

### 1.2 Current `rh` observation

At `2026-07-27T03:00:18Z`, local `rh`, cached `origin/rh`, and live
`origin/rh` all resolved read-only to
`7a3a36666f277277fa08b55081b3f58c7cd3ba64`, tree
`515832eeb23bff94e6ef56e43d27434bbdcd7a81`. The change from the H-06 audit
baseline `c0d0e708...` contains only four documentation paths:

- `docs/chains/rh/evidence/robinhood-blueprint-phase-a.md`; and
- `docs/chains/rh/evidence/robinhood-migration-phase-a.md`;
- `docs/chains/rh/evidence/stock-token-m1-exact-receipt.md`; and
- `docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md`.

The advance through H-03, H-05, and Track 8 evidence is therefore
documentation-only and did not alter the H-06 implementation inputs identified
in this document. The H-06 worktree remains based on `c0d0e708...`, tree
`b2c2358f...`; it was not rebased or merged. Any later `rh` or controlling
input movement requires a fresh input and interface reconciliation rather than
rewriting this timestamped observation.

### 1.3 Explicit exclusions

This Phase A does not implement or authorize:

- migration namespaces, files, or skeletons;
- Robinhood or Base history creation or modification;
- H-05 discovery, planning, namespace, reservation, or execution policy;
- H-07 verification adapters, H-08 topology checks, or H-09 fixtures;
- network-profile, dependency, CI, contract, ABI, deployment, or configuration
  changes;
- live manifests, RPC access, account access, chain actions, signing, or
  broadcasting.

## 2. Current behavior audit

### 2.1 Present write and resume flow

The current `Migration` constructor loads `current-manifest.json` and a
per-step transaction log. Both loads catch every exception and replace the
result with empty state
([migration.py L29-L40](../../../../scripts/utils/migration.py#L29-L40)).
Consequences include:

1. missing, malformed, truncated, wrong-type, permission-denied, and other
   failures are indistinguishable;
2. a corrupt current file is treated as an empty deployment state;
3. a corrupt retry log is treated as no completed transactions;
4. neither condition is fail-closed or surfaced with a typed result.

`execute()` calls `_run()` and saves only the positional transaction log; it
does not add a configuration record to either manifest
([migration.py L45-L53](../../../../scripts/utils/migration.py#L45-L53)).
Deployments register a contract and immediately call `_append_manifest()`
([migration.py L55-L61](../../../../scripts/utils/migration.py#L55-L61)).
The manifest therefore records contract deployment-shaped data but omits
configuration-only transactions, assertions, deliberate omissions, tooling
actions, and postconditions.

`_run()` uses the current length of `_transactions` as its resume identity and
reuses the string at that position
([migration.py L163-L210](../../../../scripts/utils/migration.py#L163-L210)).
The retry log contains only ordered string renderings
([migration.py L237-L249](../../../../scripts/utils/migration.py#L237-L249)).
Inserting, deleting, reordering, or conditionally skipping a transaction can
therefore associate an old log entry with a different semantic action.
Transaction position, not semantic identity, is the resume key.

The same `_run()` path can treat a `None` result as confirmed. The helper
returns `None` for one recognized error string and also falls through to
`None` after exhausting retries
([migration_helpers.py L129-L162](../../../../scripts/utils/migration_helpers.py#L129-L162)).
The caller appends the result and emits the confirmation message without
requiring a transaction hash or receipt. Integrated H-05 owns discovery and
deterministic plan construction, and explicitly excludes execution from its
six-file Phase B. A later file-exact execution-hardening authorization, whose
implementation owner remains unassigned by H-05, must own truthful typed
transaction-result construction, including exhausted-retry and false-success
refusal. H-06 accepts only that typed result and rejects incomplete,
false-success, exhausted-retry, `None`, or ambiguous outcomes; H-06 does not
implement transaction submission, retry, or result classification.

`_append_manifest()`:

- swallows all errors when reading the existing step manifest;
- builds a contract-only dictionary;
- merges it into the previously loaded current dictionary;
- directly rewrites the step manifest; and then
- directly rewrites `current-manifest.json`

([migration.py L218-L235](../../../../scripts/utils/migration.py#L218-L235)).
These writes happen during a step, before the remaining actions and
`Migration.end()` have completed. The mutable current file is consequently
both the resume input and independent deployment authority. A later failure
can leave both step and current files claiming partial progress.

`end()` only removes the retry log
([migration.py L108-L118](../../../../scripts/utils/migration.py#L108-L118)).
There is no durable terminal step or plan-completion marker.

The runner also creates the history directory while asking for the latest
manifest and derives progress from filenames
([migration_runner.py L136-L154](../../../../scripts/utils/migration_runner.py#L136-L154)).
That is not a read-only semantic history interface. The integrated CLI's Base
fork route passes the committed Base history directory to this runner and
warns that the run can write there
([migrate.py L338-L370](../../../../scripts/migrate.py#L338-L370)).
H-06 must preserve Base compatibility without copying this mutating-read
behavior into Robinhood.

### 2.2 Present JSON durability

The generic JSON writer creates parent directories and opens the canonical
target directly with mode `"w"`, then calls `json.dump(..., indent=2)`
([json_file.py L16-L27](../../../../scripts/utils/json_file.py#L16-L27)).
It provides none of the following:

- complete schema validation before a write;
- path-root validation or symlink rejection;
- a same-directory temporary file;
- restrictive explicit permissions;
- a complete-write loop, flush, or file `fsync`;
- a re-read, byte comparison, schema check, or digest check;
- atomic no-replace publication;
- directory `fsync`;
- interprocess locking, stale-writer detection, or collision handling;
- cleanup and typed outcomes at each failure boundary.

A crash, disk-full condition, process race, or write interruption can expose a
partial canonical file. Completed records can be silently overwritten.
`json.dump` also does not append a terminal newline and is not a specified
canonical hashing format.

### 2.3 Missing identity and state

Current manifests have no explicit identity for:

- schema name or version;
- canonical profile or expected chain ID;
- source commit, source tree, plan hash, or source-set digest;
- semantic migration, step, or action;
- a prior immutable record;
- requested transaction versus confirmed receipt;
- receipt block number/hash/status/gas;
- finality policy, finality observation, or reconciliation;
- expected or observed postconditions;
- terminal step or terminal plan completion.

An absent dictionary key is the only representation for many concepts.
Legitimate zero values, explicit null, absence, unknown, and not-applicable
cannot be distinguished. A contract address-only record is also structurally
different from a full record without an explicit discriminator.

### 2.4 Sensitive-material exposure surfaces

No H-06 evidence writer exists yet, so the risk is that a future writer could
serialize values already present in current execution or error paths:

| Surface | Present material | H-06 rule |
| --- | --- | --- |
| `Migration.rpc()` | Returns the raw resolved endpoint ([migration.py L42-L43](../../../../scripts/utils/migration.py#L42-L43)); a Base migration passes it to a provider ([2025071801 L6-L14](../../../../migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py#L6-L14)). | Never serialize, hash into committed evidence, or include in an error. |
| `_clean_message()` and logging | May render a transaction object, message, or argument ([migration.py L148-L173](../../../../scripts/utils/migration.py#L148-L173)). | Do not use log strings as evidence. Accept only schema allowlisted typed fields. |
| transaction helper | Receives provider exceptions and retries ([migration_helpers.py L129-L162](../../../../scripts/utils/migration_helpers.py#L129-L162)). | Store a stable sanitized code only; never the exception, cause, payload, or endpoint. |
| compiler helper | Raises text containing command output or an exception ([migration_helpers.py L164-L181](../../../../scripts/utils/migration_helpers.py#L164-L181)). | Never copy stderr, exception text, host paths, or process environment to evidence. |
| migration runner | Raises `MigrationError(timestamp) from exception` ([migration_runner.py L60-L69](../../../../scripts/utils/migration_runner.py#L60-L69)). The wrapper message contains fixed text and the failure timestamp; the original exception text remains reachable through the chained cause and traceback rather than being interpolated into the wrapper message. | Preserve only a typed code at the evidence boundary; never serialize the wrapper, chained cause, traceback, or message. |
| deployed-contract projection | Includes ABI, compiler JSON with embedded sources, encoded constructor arguments, and a file path ([migration_helpers.py L237-L257](../../../../scripts/utils/migration_helpers.py#L237-L257)). | Do not inherit this shape automatically. Admit only reviewed source digests and approved public semantic values. |
| generic JSON helper | Writes any supplied object without a sensitivity schema. | The v2 validator must reject unrecognized fields and sensitive patterns before any write. |

The integrated H-02 tests already require RPC redaction in logs and exceptions
([secret-handling test L489-L525](../../../../tests/deployment/test_secret_handling.py#L489-L525)).
That protection is necessary but not sufficient: H-06 evidence must be an
allowlist model, not a filtered dump of runtime objects.

## 3. Complete committed Base history audit

### 3.1 Corpus facts

All 58 committed JSON files parse as JSON. The corpus has:

| Measure | Exact result |
| --- | ---: |
| Numeric step files | 57 |
| Mutable `current-manifest.json` files | 1 |
| Total JSON files | 58 |
| Total bytes | 137,791,206 |
| Total LF-delimited lines (`wc -l`) | 2,817,358 |
| Total contract-record occurrences | 1,647 |
| Full records | 1,575 |
| Address-only records | 72 |
| Files ending in LF | 2 |
| Files without terminal LF | 56 |
| Filename-plus-SHA-256 inventory digest | `79267f031649ad08e314dc9f63645d4d09172120a1ab728161ea833ed2526a18` |

The inventory digest in the final row is SHA-256 over the ordinary
newline-delimited output of `shasum -a 256` for all 58 paths in bytewise
filename order. Every printed path is the repository-root-relative POSIX path,
for example
`migration_history/base-mainnet/v1/0000-manifest.json`, not a path relative
only to the history directory. Each line is
`<sha256-hex><two ASCII spaces><repository-root-relative POSIX path>\n`; the
final line also ends in LF. It is an audit inventory only, not a proposed v2
digest algorithm.

Every file has exactly one top-level key, `contracts`. Across all contract
occurrences there are exactly two shapes:

1. 1,575 full records with exactly `abi`, `address`, `args`, `file`, and
   `solc_json`; their types are array, string, string, string, and object,
   respectively.
2. 72 address-only records with exactly `address`, always a string.

Every full `solc_json` object has exactly `compiler_version`, `integrity`,
`language`, `settings`, and `sources`. There are no top-record nulls, empty
ABIs, zero addresses, or malformed address strings. Every referenced full
record `file` exists at the audited baseline. Every `args` value is an even
length hexadecimal string without an `0x` prefix; 50 are empty. The empty
arguments occur only for `Contributor` (48 occurrences) and `DefaultsBase`
(2 occurrences).

The 72 address-only occurrences are exactly:

| Contract name | Occurrences |
| --- | ---: |
| `GreenPool` | 33 |
| `RipePool` | 5 |
| `RipePoolAero` | 17 |
| `RipePoolCurve` | 17 |

The current manifest has 48 contracts: 45 full and 3 address-only
(`GreenPool`, `RipePoolAero`, and `RipePoolCurve`). It contains no `RipePool`.
Only `2025102000-manifest.json` and `2025120700-manifest.json` end in LF.

### 3.2 Exact file shapes

`Total = full + address-only` for every row:

| File | Total | Full | Address-only |
| --- | ---: | ---: | ---: |
| `0000-manifest.json` | 7 | 7 | 0 |
| `1004-manifest.json` | 8 | 8 | 0 |
| `1005-manifest.json` | 9 | 9 | 0 |
| `1006-manifest.json` | 14 | 14 | 0 |
| `1007-manifest.json` | 20 | 20 | 0 |
| `1008-manifest.json` | 25 | 25 | 0 |
| `1009-manifest.json` | 26 | 26 | 0 |
| `1010-manifest.json` | 27 | 27 | 0 |
| `1011-manifest.json` | 28 | 28 | 0 |
| `1012-manifest.json` | 29 | 29 | 0 |
| `1013-manifest.json` | 30 | 30 | 0 |
| `1014-manifest.json` | 31 | 31 | 0 |
| `1015-manifest.json` | 32 | 32 | 0 |
| `1016-manifest.json` | 33 | 33 | 0 |
| `1017-manifest.json` | 34 | 34 | 0 |
| `2001-manifest.json` | 35 | 34 | 1 |
| `3001-manifest.json` | 35 | 34 | 1 |
| `3002-manifest.json` | 35 | 34 | 1 |
| `2025071501-manifest.json` | 35 | 34 | 1 |
| `2025071502-manifest.json` | 35 | 34 | 1 |
| `2025071503-manifest.json` | 35 | 34 | 1 |
| `2025071504-manifest.json` | 35 | 34 | 1 |
| `2025071505-manifest.json` | 35 | 34 | 1 |
| `2025071506-manifest.json` | 36 | 35 | 1 |
| `2025071601-manifest.json` | 36 | 35 | 1 |
| `2025071602-manifest.json` | 36 | 35 | 1 |
| `2025071801-manifest.json` | 37 | 35 | 2 |
| `2025072001-manifest.json` | 37 | 35 | 2 |
| `2025072201-manifest.json` | 37 | 35 | 2 |
| `2025072301-manifest.json` | 37 | 35 | 2 |
| `2025072701-manifest.json` | 37 | 35 | 2 |
| `2025072901-manifest.json` | 38 | 35 | 3 |
| `2025080401-manifest.json` | 38 | 35 | 3 |
| `2025080800-manifest.json` | 38 | 35 | 3 |
| `2025080900-manifest.json` | 38 | 35 | 3 |
| `2025080901-manifest.json` | 38 | 35 | 3 |
| `2025081200-manifest.json` | 38 | 35 | 3 |
| `2025081800-manifest.json` | 38 | 35 | 3 |
| `2025082000-manifest.json` | 39 | 36 | 3 |
| `2025090300-manifest.json` | 39 | 36 | 3 |
| `2025090400-manifest.json` | 40 | 37 | 3 |
| `2025102000-manifest.json` | 1 | 1 | 0 |
| `2025102200-manifest.json` | 42 | 39 | 3 |
| `2025111100-manifest.json` | 45 | 42 | 3 |
| `2025112400-manifest.json` | 45 | 42 | 3 |
| `2025112500-manifest.json` | 48 | 45 | 3 |
| `2025120200-manifest.json` | 48 | 45 | 3 |
| `2025120400-manifest.json` | 48 | 45 | 3 |
| `2025120700-manifest.json` | 2 | 2 | 0 |
| `2025120900-manifest.json` | 1 | 1 | 0 |
| `2026010900-manifest.json` | 1 | 1 | 0 |
| `2026011400-manifest.json` | 1 | 1 | 0 |
| `2026021300-manifest.json` | 1 | 1 | 0 |
| `2026021900-manifest.json` | 3 | 3 | 0 |
| `2026022000-manifest.json` | 1 | 1 | 0 |
| `2026030500-manifest.json` | 1 | 1 | 0 |
| `2026043000-manifest.json` | 1 | 1 | 0 |
| `current-manifest.json` | 48 | 45 | 3 |

The runner's numeric ordering places `3001` and `3002` after `2001` and before
the 2025 date-like IDs. Of the 57 numeric files, 47 are snapshot-like by
record-count and continuity, while these 10 are delta-like:
`2025102000`, `2025120700`, `2025120900`, `2026010900`, `2026011400`,
`2026021300`, `2026021900`, `2026022000`, `2026030500`, and `2026043000`.
This is an observed shape classification, not a semantic reinterpretation.

The important discontinuities are:

- `2025072901` replaces the address-only `RipePool` shape with
  `RipePoolCurve` and `RipePoolAero`;
- `2025090300` removes `AeroRipePrices` and adds `wsuperOETHbPrices`;
- `2025102000` is a one-record delta, while `2025102200` returns to a
  42-record snapshot-like shape;
- after the 48-record `2025120400`, the remaining nine numeric files are
  small delta-like records, while `current-manifest.json` remains a
  48-record cumulative projection.

There are 62 Base migration source files and 61 unique numeric IDs. ID
`2025071506` occurs twice. Source IDs `2000`, `2003`, `2025071507`, and
`2025102700` have no same-ID history file. Every numeric history file has at
least one same-ID source file. These facts make filename presence, list
position, and contract-count growth invalid substitutes for semantic history.

### 3.3 Legacy compatibility contract

Base history is immutable legacy input. H-06 must:

- preserve every existing byte and path under `migration_history/base-mainnet/v1`;
- continue to read the `{"contracts": ...}` shape and both record variants;
- keep the Base current-manifest path used by the existing compatibility test
  ([Base regression L217-L234](../../../../tests/deployment/test_base_profile_regression.py#L217-L234));
- treat parse failure as a typed failure, never silently empty state
  ([Base regression L236-L250](../../../../tests/deployment/test_base_profile_regression.py#L236-L250));
- dispatch explicitly between legacy Base and Robinhood v2 readers;
- never normalize, rewrite, hash-chain, backfill, or reinterpret Base blobs as
  Robinhood evidence;
- never select a Base path, blob, `Ledger` deployment, or history as a
  Robinhood fallback.

The existing block-clock inventory test keeps Base history in its historical
exclusion while proving that a future Robinhood history namespace is scanned
([inventory test L721-L748](../../../../tests/inventory/test_block_clock_inventory.py#L721-L748)).
V2 must preserve that distinction; no inventory exception or change belongs
in H-06.

The Robinhood profiles already have isolated mainnet and testnet history roots
and distinct expected chain IDs
([network_profiles.py L416-L461](../../../../config/network_profiles.py#L416-L461)).
The proposed v2 format uses those profile-isolated roots. The existing `v1`
path segment is treated as a repository history namespace, not the record
schema version; changing those profile paths would exceed the proposed
eight-file ceiling and is an explicit owner decision.

## 4. Proposed manifest-v2 model

Normative keywords in this section describe the proposal only. They do not
indicate approval.

### 4.1 Artifact families and authority

The schema identity is proposed as
`ripe.robinhood.deployment-manifest`, with integer `schema_version: 2`.
The schema validates three explicit artifact kinds:

| `artifact_kind` | Retention | Authority |
| --- | --- | --- |
| `immutable_step_record` | Safe completed form is required to commit. | One immutable, self-hashed link in the completed semantic history chain. |
| `attempt_record` | Restricted local, never current authority. | Truthful partial, failed, blocked, ambiguous, or finality-pending execution state anchored to a completed head. |
| `current_index` | Generated and required to commit after successful promotion. | Pointer to and cache of a validated terminal immutable target; never independent evidence authority. |

Only `immutable_step_record` participates in the canonical prior-record chain.
An attempt record has its own self-hash and records the completed-chain head
from which the attempt began, but it cannot become that head. This prevents
partial or sensitive operational state from advancing canonical history.
Artifact-type separation is enforced by the three closed `artifact_kind`
values, closed per-kind schemas, and disjoint serialization/hash contracts.
No artifact is identified from a digest string alone. Section 4.5 additionally
gives the embedded raw-log evidence digest an external domain prefix so it
cannot be substituted for an artifact self-hash or plan digest.

`scripts/utils/manifest_schema.py` is proposed as the sole authoritative
in-code schema construction. Its standard-library-only builder returns the
complete closed schema object; the same constants and branch definitions drive
the validator. The committed
`docs/chains/rh/schemas/deployment-manifest-v2.schema.json` must equal the
builder's deterministic Section 5.2 JSON bytes byte-for-byte, including one
terminal LF. The schema file is a reviewable generated representation, not a
second hand-maintained authority. Tests must fail on drift in any required
key, conditional, enum, type branch, or `additionalProperties` behavior. No
`jsonschema` or other dependency is proposed.

An immutable file name is:

`<migration_id>-<semantic_step_id>-<record_sha256>.manifest-v2.json`

All components are schema validated. The controlling H-05 identifier contract
and its [owner-approved identifier convention](../robinhood-deployment-support-specification.md#L1163-L1178)
require a fixed-width four-digit ASCII-decimal `migration_id`, matching
`[0-9]{4}`. It remains a string, and leading zeroes are
identity-significant. The H-06 filename parser consumes exactly those four
digits, then the literal `-`; it never infers the boundary from an unrestricted
character set. H-05 separately owns its canonical source filename's semantic
name and underscore form. H-06 consumes the approved migration ID and semantic
step identity but does not parse or redefine the H-05 source filename.
`semantic_step_id` is lowercase ASCII
`[a-z0-9]+(?:-[a-z0-9]+)*`. The hash is 64 lowercase hexadecimal characters.
The target resides directly in the profile's configured history directory.
The file name is content addressed and cannot be reused for different bytes.
Any width, character-set, delimiter, or semantic-name change requires a joint
H-05/H-06 versioned schema decision; H-06 cannot widen this grammar silently.

### 4.2 Required immutable record envelope

Every `immutable_step_record` has exactly these top-level keys; additional
keys fail schema validation:

| Key | Required meaning |
| --- | --- |
| `schema` | Exact schema identity string. |
| `schema_version` | Integer `2`. |
| `artifact_kind` | Exact `immutable_step_record`. |
| `record_id` | `<profile_id>:<plan_sha256>:<migration_id>:<semantic_step_id>`. |
| `record_sha256` | Self-hash calculated by Section 5. |
| `profile` | Exact `profile_id` and positive integer `expected_chain_id`. |
| `source` | Exact source commit, source tree, plan SHA-256, source-set SHA-256, and ordered source members. |
| `step` | Semantic migration/step identity, prior record identity, ordered actions, and complete step state. |
| `plan_state` | Plan identity, completed step IDs, required remaining step IDs, and terminal plan status. |

Proposed semantic skeleton:

```json
{
  "schema": "ripe.robinhood.deployment-manifest",
  "schema_version": 2,
  "artifact_kind": "immutable_step_record",
  "record_id": "robinhood-mainnet:<plan_sha256>:0900:deploy-hq",
  "record_sha256": "<sha256>",
  "profile": {
    "profile_id": "robinhood-mainnet",
    "expected_chain_id": 4663
  },
  "source": {
    "commit": "<40-lowercase-hex>",
    "tree": "<40-lowercase-hex>",
    "plan_sha256": "<64-lowercase-hex>",
    "source_set_sha256": "<64-lowercase-hex>",
    "members": [
      {
        "path": "migrations/robinhood/0900_deploy_hq.py",
        "sha256": "<64-lowercase-hex>"
      }
    ]
  },
  "step": {
    "migration_id": "0900",
    "semantic_step_id": "deploy-hq",
    "ordinal": 0,
    "previous_record_id": null,
    "previous_record_sha256": null,
    "status": "complete",
    "actions": []
  },
  "plan_state": {
    "plan_sha256": "<64-lowercase-hex>",
    "predecessor_plan_sha256": null,
    "completed_step_ids": ["deploy-hq"],
    "remaining_required_step_ids": [],
    "status": "complete"
  }
}
```

The profile-chain genesis record requires both previous fields and
`predecessor_plan_sha256` to be null. Every later record requires both previous
record fields to be non-null and to identify the immediately preceding
validated immutable record in the same profile and chain.

Within a plan, source identity and plan SHA-256 are invariant and
`predecessor_plan_sha256` is constant. A plan transition is allowed only at
step ordinal zero, after a prior terminal-complete record, and only when the
new record's `predecessor_plan_sha256` equals the prior terminal record's plan
SHA-256. Later records in the new plan retain that predecessor value. This
permits forward remediation without a second head while making the plan
boundary explicit. Cross-profile, cross-chain, unmarked cross-plan,
skipped-link, duplicate-head, or self-referential links are invalid.

### 4.3 Action records

Actions are complete semantic records, not transaction-position entries. Each
has exactly:

- `action_id`: `<migration_id>:<six-digit-ordinal>:<semantic_action_id>`;
- `ordinal`: zero-based integer matching array position;
- `semantic_action_id`: stable lowercase ASCII slug from the approved plan;
- `kind`;
- `required`: Boolean;
- `status`;
- `expected_postconditions`;
- `observed_postconditions`;
- `transaction`;
- `events`;
- `supersedes`;
- `disposition`;
- `error`.

The allowed typed `kind` values are:

| Kind | Meaning |
| --- | --- |
| `deployment` | Creates code or a contract at an intended public address. |
| `configuration` | Changes protocol configuration or permissions. |
| `assertion` | Read-only invariant or postcondition check. |
| `omission` | Explicitly planned work that is intentionally not emitted or executed. |
| `blocked` | Cannot proceed until a named gate or prerequisite is resolved. |
| `deferred` | Owner-visible work assigned to a later approved plan or phase. |
| `rejected` | Proposed action explicitly excluded by an owner disposition. |
| `tooling-only` | Local preparation with no chain-state effect. |

The allowed action status values are `planned`, `submitted`, `confirmed`,
`finality-pending`, `reconciled`, `failed`, `blocked`, and `complete`.
Attempt records may use every status. An immutable step record requires every
required executable action to be `reconciled` or `complete`, and its step
status must be `complete`. Non-executable `omission`, `blocked`, `deferred`,
`rejected`, and `tooling-only` actions are still present, ordered, and
truthful; each needs a stable disposition code, an owner/gate reference, and
an expected effect of not-applicable. A `blocked` required action cannot
coexist with a complete step. A non-required reservation may be completely
disposed as blocked, deferred, rejected, or omitted without pretending it
executed.

For an executable action, the exact closed nested shape is:

```json
{
  "action_id": "0900:000000:deploy-hq",
  "ordinal": 0,
  "semantic_action_id": "deploy-hq",
  "kind": "deployment",
  "required": true,
  "status": "complete",
  "expected_postconditions": [
    {
      "postcondition_id": "hq-code-hash",
      "kind": "code-hash",
      "subject": "hq",
      "value": {
        "state": "known",
        "type": "bytes32",
        "value": "<32-byte-public-value>"
      }
    }
  ],
  "observed_postconditions": [
    {
      "postcondition_id": "hq-code-hash",
      "value": {
        "state": "known",
        "type": "bytes32",
        "value": "<32-byte-public-value>"
      },
      "observation": {
        "method_code": "eth-get-code-hash",
        "block_number": 1,
        "block_hash": "<32-byte-public-value>"
      },
      "status": "matched"
    }
  ],
  "transaction": {
    "required": true,
    "request_identity": {
      "state": "known",
      "semantic_request_id": "0900:000000:deploy-hq",
      "plan_action_sha256": "<64-lowercase-hex>"
    },
    "submission": {
      "status": "submitted",
      "transaction_hash": "<32-byte-public-value>"
    },
    "receipt": {
      "status": "confirmed",
      "transaction_hash": "<32-byte-public-value>",
      "block_number": 1,
      "block_hash": "<32-byte-public-value>",
      "success": true,
      "gas_used": 1,
      "cumulative_gas_used": {
        "state": "not-applicable",
        "type": "uint256",
        "value": null,
        "reason_code": "not-required-by-policy"
      }
    },
    "finality": {
      "status": "complete",
      "policy_id": "owner-approved-policy-id",
      "required_confirmations": 1,
      "required_finality_tag": {
        "state": "not-applicable",
        "type": "string",
        "value": null,
        "reason_code": "confirmation-depth-policy"
      },
      "observed_confirmations": 1,
      "observation_block_number": 1,
      "observation_block_hash": "<32-byte-public-value>"
    },
    "reconciliation": {
      "status": "reconciled",
      "observation_source_code": "owner-approved-observer",
      "check_ids": ["receipt-identity", "receipt-success", "postconditions"]
    }
  },
  "events": [
    {
      "event_id": "hq-created",
      "log_index": 0,
      "emitter": "<20-byte-public-address>",
      "signature_topic": "<32-byte-public-value>",
      "fields": [
        {
          "name": "hq",
          "value": {
            "state": "known",
            "type": "address",
            "value": "<20-byte-public-address>"
          }
        }
      ],
      "event_evidence_sha256": "<64-lowercase-hex>"
    }
  ],
  "supersedes": [],
  "disposition": null,
  "error": null
}
```

The placeholders illustrate types and are not valid evidence values. For a
non-transaction action, the same exact transaction keys remain present:
`required` is false; request state and every transaction sub-status are
`not-applicable`; identity/hash/number/Boolean fields are null; every such
null is paired with the applicable stable state or reason code. The JSON
Schema must express these alternatives with closed conditional branches, not
open optional objects.

`supersedes` is empty for ordinary actions. A forward remediation action uses
one or more closed records with exactly `record_sha256`, `action_id`,
`postcondition_id`, `reason_code`, and `authority_ref`. The referenced record
must be an ancestor in the same profile chain. `postcondition_id` uses the
typed-value wrapper: it is a known string when one prior postcondition is
superseded and not-applicable when the whole action is superseded. Entries are
ordered by record hash, action ID, then known postcondition ID. A remediation
gets a new plan and new action ID; it never changes, deletes, reuses, or
relabels the referenced transaction, receipt, event, or postcondition.

`disposition` is a closed object with `code`, `authority_ref`, and
`explanation_digest_sha256`. It never stores free-form owner communication.
`error` is either null or exactly:

```json
{
  "code": "H06_STABLE_SANITIZED_CODE",
  "phase": "write",
  "action_id": "0900:000000:deploy-hq"
}
```

No exception class, exception text, cause, traceback, endpoint, signer,
environment, provider request/response, or arbitrary message field is allowed.
An immutable complete record requires `error: null`.

### 4.4 Transaction request and receipt identity

Every action has a `transaction` object. Non-transaction actions use explicit
not-applicable state; the key is never silently absent.

For an executable transaction action, the object distinguishes:

| Field | Meaning |
| --- | --- |
| `required` | Whether policy requires a chain transaction. |
| `request_identity` | Deterministic semantic request ID and approved plan-action SHA-256. It contains no raw calldata, unsigned transaction, signed transaction, signature, private material, gas quote, endpoint, or provider payload. |
| `submission` | State plus the approved public transaction hash after submission. |
| `receipt` | State plus confirmed transaction hash, block number, block hash, Boolean success, gas used, and optional cumulative gas used. |
| `finality` | Policy ID, required confirmation depth/finality tag, observed block identity, observed confirmation count, and status. |
| `reconciliation` | Status, observation source code, and reconciliation check IDs. |

The semantic request ID is the action ID. The plan-action SHA-256 is supplied
by H-05's approved deterministic plan and is validated, not recomputed from a
runtime transaction by H-06. The only admitted public submission material is
the transaction hash. The confirmed receipt transaction hash must equal it.
A successful receipt requires Boolean `success: true`, nonnegative integer
block and gas values, and a 32-byte block hash. A reverted receipt records
`success: false` in a restricted attempt record and cannot enter a complete
immutable record.

`finality.status` is one of `not-applicable`, `pending`, `complete`, or
`failed`. `reconciliation.status` is one of `not-applicable`, `pending`,
`reconciled`, or `failed`. Policy decides the exact confirmation depth or
finality tag, but an immutable executable action requires both statuses to be
complete/reconciled. A receipt alone is not completion.

`request_identity.state` is `known` or `not-applicable`.
`submission.status` is `not-applicable`, `planned`, or `submitted`.
`receipt.status` is `not-applicable`, `pending`, or `confirmed`. The receipt
fields are non-null only when confirmed. The action status and nested states
must agree; for example, `submitted` requires a submission hash and forbids a
confirmed action status, while `finality-pending` requires a successful
confirmed receipt and pending finality.

#### 4.4.1 Bounded finality recommendation

The smallest proposed policy is
`robinhood-confirmations-64-v1`. It is a recommendation for owner review, not
a claim about Robinhood consensus finality and not live-action authority. An
executable action may reconcile only when:

1. the approved profile/chain identity agrees;
2. a receipt is confirmed with `success: true`;
3. the receipt transaction hash equals the submitted public transaction hash;
4. the receipt block hash is observed once with the receipt and again after at
   least 64 successor blocks;
5. the second observation returns the same transaction, receipt block, block
   hash, success status, and sanitized required events;
6. every required postcondition is re-read at the second observation block and
   matches; and
7. no provider, durability, chain, source, or result ambiguity remains.

The second observation records `observed_confirmations >= 64`, its block
number/hash, the approved observation-source code, and the postcondition
evidence. Endpoints and provider payloads remain prohibited. Because H-07 is
excluded and no chain-specific finality adapter is approved, mainnet current
promotion remains disabled until the chain/operations owner and security
reviewer either accept the residual reorganization/sequencer risk of this
bounded policy or approve a stronger finalized/L1 policy.

### 4.5 Events and postconditions

`events` contains only an approved allowlist projection: emitting public
address, event signature hash, receipt log index, schema-approved decoded
field-name/value records in ascending field-name order, and an event-evidence
SHA-256. It never contains the provider response, raw log object, RPC
metadata, or arbitrary decoded payload.

`event_evidence_sha256` commits to exactly one public receipt log through this
closed projection and no other keys:

```json
{
  "expected_chain_id": 4663,
  "transaction_hash": "<32-byte-public-value>",
  "block_number": 1,
  "block_hash": "<32-byte-public-value>",
  "log_index": 0,
  "emitter": "<20-byte-public-address>",
  "topics": ["<32-byte-public-value>"],
  "data": "0x"
}
```

The projection is constructed, validated, and then serialized with the exact
H-06 canonical algorithm in Section 5.2, including its terminal LF.
`event_evidence_sha256` is:

```text
SHA256(
  UTF8("ripe-manifest-v2-event-evidence") || 0x00 ||
  canonical_event_projection_bytes_including_terminal_LF
)
```

The `event_evidence_sha256` field is not a key in the projection and is never
part of its hash input. Transaction hash, block hash, and every topic are
`0x` plus exactly 64 lowercase hexadecimal characters; the emitter is `0x`
plus exactly 40 lowercase hexadecimal characters; data is `0x` followed by
an even number of lowercase hexadecimal characters and represents the exact
raw log data bytes, including leading zero bytes. Chain ID is a positive
integer; block number and log index are nonnegative integers. Topic order is
receipt order and is never sorted. For a named allowlisted event,
`signature_topic` must equal `topics[0]`; an empty topics array is valid only
for an explicitly schema-approved anonymous event without a signature-topic
claim.

Before hashing, the verifier requires the public log's transaction hash,
block number, and block hash to exist and equal the parent confirmed receipt;
its transaction hash must also equal the parent submission hash, and its chain
ID must equal the parent profile. The event record's log index and emitter
must equal the selected receipt log. Malformed lengths, uppercase or
non-normalized hex, missing receipt linkage, reordered or incomplete topics,
changed data bytes, duplicate/extra projection keys, or any mismatch with the
parent transaction/receipt fail validation.

An independent verifier obtains the public receipt identified by the parent
transaction hash, validates the parent receipt block identity, selects the
unique log at the recorded log index, copies its emitter, complete ordered
topics, and exact raw data bytes into the closed projection with the expected
chain ID and parent receipt identities, emits Section 5.2 bytes plus LF,
prepends the domain bytes and NUL above, and compares the lowercase SHA-256
using constant-time comparison. It does not hash a provider JSON object or a
decoded event representation.

Expected and observed postconditions are ordered records with:

- stable `postcondition_id`;
- a closed `kind` such as `code-hash`, `storage-value`, `role-membership`,
  `configuration-value`, `balance`, or `assertion`;
- public subject identity;
- typed expected and observed values;
- observation block number and hash when applicable;
- status `matched`, `mismatched`, `unknown`, or `not-applicable`;
- approved observation-method code.

Every required action must have at least one expected postcondition unless its
typed kind is expressly non-executable. Complete executable actions require
all required observed postconditions to be `matched` at the policy-required
finality point.

### 4.6 Zero, null, absent, unknown, and not-applicable

Values whose state can vary use this closed wrapper:

```json
{"state":"known","type":"uint256","value":0}
{"state":"explicit-null","type":"address","value":null}
{"state":"unknown","type":"uint256","value":null,"reason_code":"observation-unavailable"}
{"state":"not-applicable","type":"uint256","value":null,"reason_code":"non-transaction-action"}
```

Rules:

1. `known` requires a non-null schema-typed value; zero, false, and empty
   string are preserved and never treated as missing.
2. A legitimate known null is `explicit-null`, never `known`. Its `type` must
   name the field's actual non-null type; a generic `null` type tag is
   forbidden. Every explicit-null conditional branch pins that non-null type
   in the schema rather than accepting an unconstrained value family.
3. `unknown` means the value should exist but is not known; its value must be
   null and a stable reason code is required.
4. `not-applicable` means the concept does not apply; its value must be null
   and a stable reason code is required.
5. Absence means the key is omitted. It is permitted only where the schema
   explicitly declares a field optional and makes no semantic claim.
6. A required key that is absent is a schema error. A serializer never
   manufactures a missing value or converts a falsey value to null.

The closed `type` enum is `boolean`, `uint256`, `int256`, `address`,
`bytes`, `bytes32`, `string`, `address-array`, `uint256-array`, or
`bytes32-array`. Addresses are `0x` plus 40 lowercase hexadecimal characters.
Bytes are `0x` plus an even number of lowercase hexadecimal characters.
Bytes32, transaction hashes, and block hashes are `0x` plus 64 lowercase
hexadecimal characters. Array values retain approved semantic order; set-like
arrays must already be sorted by their canonical element bytes. Any required
type outside this enum is a schema/version owner decision, not an untyped
escape hatch.

### 4.7 Step and plan completion

An immutable record's `step.status` must be `complete`. A local attempt may
use `planned`, `submitted`, `confirmed`, `finality-pending`, `reconciled`,
`failed`, or `blocked`.

`plan_state.status` is `in-progress` or `complete` in immutable records and may
also be `failed`, `blocked`, or `ambiguous` in attempts. A terminal plan record
has:

- `status: complete`;
- every required semantic step ID exactly once in `completed_step_ids`;
- an empty `remaining_required_step_ids`;
- a complete current step;
- a chain whose source, profile, chain, plan, IDs, and hashes all validate.

The terminal marker is therefore inside the final immutable record and is
covered by its self-hash. Mere existence of a step file, receipt, deployment
address, or current index is not completion.

### 4.8 Restricted attempt envelope

An `attempt_record` uses exactly the immutable envelope's `schema`,
`schema_version`, `profile`, `source`, `step`, and `plan_state` objects, with
these top-level substitutions:

- `artifact_kind` is `attempt_record`;
- `attempt_id` is 32 lowercase random hexadecimal characters allocated before
  the attempt and used only for local identity;
- `attempt_sha256` replaces `record_id` and `record_sha256`;
- `base_record_id` and `base_record_sha256` identify the validated completed
  head from which execution began, or are both null only before chain genesis;
- `retention_class` is exactly `success-7d`, `failure-30d`, or
  `ambiguity-until-resolved-30d`.

The attempt's `step.previous_record_*` values must equal its base fields.
Attempt files are named
`.attempt-<profile_id>-<attempt_id>-<attempt_sha256>.json`, mode `0600`, and
are never accepted as immutable-chain members or current targets. Randomness
affects local attempt identity, not canonical serialization of a given
attempt object.

## 5. Deterministic canonicalization and hashes

### 5.1 Accepted data domain

Before serialization, validate the complete artifact against the v2 schema
and semantic invariants. Reject:

- duplicate object keys;
- floating-point values, exponent notation, NaN, infinity, and negative zero;
- integers outside `[-2^255, 2^256 - 1]`;
- invalid Unicode scalars, unpaired surrogates, or non-NFC strings;
- unrecognized keys, enum values, or sensitive-field names;
- unordered, duplicated, or discontinuous schema-ordered arrays.

All strings and object keys must already be Unicode NFC. The serializer
rejects rather than silently normalizing them.

### 5.2 Canonical JSON bytes

An independent implementation produces byte-identical bytes as follows:

1. Start from the validated in-memory JSON value. Emit UTF-8 without a byte
   order mark.
2. Sort every object's keys by the lexicographic order of their UTF-8 byte
   sequences. Sorting is recursive.
3. Preserve array order exactly. The schema separately requires actions by
   ascending contiguous `ordinal`, source members and string-ID collections by
   ascending normalized path/ID UTF-8 bytes, events by ascending log index,
   event fields by ascending name, and postconditions by ascending
   postcondition ID. No serializer may sort an array on the caller's behalf.
4. Emit integers as shortest base-10 ASCII: optional `-`, then digits, with no
   leading zero except `0`.
5. Emit Booleans as `true` or `false` and null as `null`.
6. For strings, emit `"` delimiters; escape quote as `\"`, reverse solidus as
   `\\`, and every U+0000 through U+001F control character as a six-byte
   lowercase `\u00xx` escape. Do not use short control escapes, escape `/`, or
   escape any other valid Unicode scalar.
7. Emit `,` and `:` without surrounding whitespace. Do not indent.
8. Append exactly one LF byte after the root value. There is no other leading
   or trailing whitespace.

### 5.3 Path normalization

Every persisted path is repository-relative POSIX text. It must be NFC, use
`/`, and preserve case. Reject:

- absolute, drive-letter, UNC, tilde, URI, or backslash forms;
- empty paths or empty components;
- `.` or `..` components;
- NUL, control characters, or a trailing slash;
- a path that lexically or after descriptor-based traversal escapes the
  approved repository/history root;
- any symlink in an existing component or at the target.

Host-absolute source, temporary, home, account, cache, and endpoint paths are
never evidence values.

### 5.4 Self-hash and chain

For `immutable_step_record`:

1. Require exactly one root `record_sha256` field.
2. Remove that key and value entirely; do not replace it with null.
3. Canonically serialize the remaining root object, including its terminal LF.
4. Compute SHA-256 over exactly those bytes.
5. Encode the 32 digest bytes as 64 lowercase hexadecimal characters.
6. Insert that string as `record_sha256`, revalidate, and canonically serialize
   the stored file with its terminal LF.

Verification removes the stored field, repeats the algorithm, and uses
constant-time digest comparison. Constant-time comparison is harmless defense
in depth for these public digests, not a claim that digest values are secret.
The hash input has no pathname, timestamp, process ID, random value, locale,
platform separator, or implicit prefix.
The previous record ID and SHA-256 are already inside the hashed object; there
is no second concatenation step. The current chain head SHA-256 is exactly the
terminal immutable record's `record_sha256`.

Attempt records use the same algorithm with root key
`attempt_sha256`. Current indexes use it with root key `index_sha256`.

### 5.5 Source-set and other digests

Each source member SHA-256 is computed over the exact Git blob bytes checked
out from the asserted source commit. Members are path-sorted as specified
above. `source_set_sha256` is:

```text
SHA256(
  UTF8("ripe-manifest-v2-source") || 0x00 ||
  for each member:
    UTF8(normalized_path) || 0x00 || raw_32_byte_member_sha256 || 0x00
)
```

An empty source set is invalid. The asserted Git commit and tree are exact
40-character lowercase object IDs and must resolve to one another during
authorized implementation validation.

H-05 supplies an owner-approved typed semantic plan object to H-06; it does
not serialize it. The closed plan projection has exactly `profile`, `source`,
and `steps`:

- `profile` is the same exact profile object used by the record;
- `source` is the record source object without `plan_sha256`;
- `steps` is ordered by contiguous `ordinal`, and each item has exactly
  `migration_id`, `semantic_step_id`, `ordinal`, `required`, and `actions`;
- each plan action is ordered by contiguous `ordinal` and has exactly
  `action_id`, `semantic_action_id`, `ordinal`, `kind`, `required`,
  `transaction_required`, `expected_postconditions`, `supersedes`, and
  `disposition`;
- expected postconditions and dispositions use the same closed definitions as
  the manifest; a disposition is null for work expected to execute.

There are no runtime statuses, observations, receipts, errors, transaction
objects, timestamps, or current identities in the plan projection. H-06
validates it against the `$defs.semanticPlan` definition in the v2 schema and
serializes it with Section 5.2.
`plan_sha256` is:

```text
SHA256(
  UTF8("ripe-manifest-v2-plan") || 0x00 ||
  canonical_plan_bytes_including_terminal_LF
)
```

For each action already committed by that plan,
`plan_action_sha256` is:

```text
SHA256(
  UTF8("ripe-manifest-v2-plan-action") || 0x00 ||
  raw_32_byte_plan_sha256 || 0x00 ||
  UTF8(action_id)
)
```

The plan hash commits to the complete approved typed plan; the action hash
binds an action ID to that plan without hashing a runtime transaction object.
H-06 owns these serialization and digest functions. H-05 owns discovery and
construction of the typed plan, and may only call the H-06 functions. Until
H-05's typed plan definition is reviewed alongside the v2 schema, neither hash
can be accepted.

### 5.6 H-05/H-06 serialization boundary

The integrated H-05 evidence at SHA-256
`28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c`,
controlling `rh` `7a3a36666f277277fa08b55081b3f58c7cd3ba64`, and this
H-06 proposal address different artifact types with different encodings.
H-05's RFC 8785/JCS report contract is approved H-05 Phase A authority; the
H-06 encoding is approved as the H-06 Phase A OD-02 design decision. Both
encodings remain, the boundary is typed, and substitution is prohibited. This
approval authorizes no Phase B work.

| Property | H-05 dry-plan report | H-06 semantic plan and manifest |
| --- | --- | --- |
| Artifact | Human/reviewer-facing deterministic blocked or later plan-ready report | Typed semantic plan input and immutable evidence/current artifacts |
| Constructor | H-05 planner/report component | H-06 `manifest_schema.py` |
| Canonicalizer owner | H-05, using RFC 8785 JCS | H-06, using Section 5.2 |
| Self-hash field | `report_sha256` | `record_sha256`, `attempt_sha256`, or `index_sha256`; semantic plan has no self-hash field |
| Hash-input field rule | Remove `report_sha256` entirely; null is invalid | Remove the applicable self-hash field entirely; null is invalid |
| Hash-input terminal LF | None | Exactly one LF for manifest/attempt/index canonical bytes |
| Stored/output terminal LF | Exactly one LF after inserting `report_sha256` | Exactly one LF after inserting the applicable self-hash |
| Digest domain | SHA-256 of the JCS hash-input bytes, with no added domain prefix | Manifest self-hash is SHA-256 of custom canonical bytes; `plan_sha256` and related digests use the explicit Section 5 domain prefixes |
| Plan hash field | `plan_hash` is null in a blocked report; once plan-ready it embeds the exact H-06-produced `plan_sha256` hexadecimal value | `plan_sha256` is constructed only by H-06 from the typed H-05 plan projection |

RFC 8785 JCS and Section 5.2 are not interchangeable. JCS uses its own
ECMAScript-compatible property ordering and string serialization and hashes
the H-05 report without a terminal LF. H-06 sorts object keys by UTF-8 bytes,
uses the explicit control-character escaping in Section 5.2, and includes a
terminal LF in each H-06 canonical hash input. Both final serialized artifacts
end in one LF, but that does not make their hash inputs equal.

H-05 constructs the typed semantic plan and its own report object. It computes
`report_sha256` using its RFC 8785 report function. H-05 does not compute,
recreate, or validate `plan_sha256` with a local serializer. Once H-06 exists
and the plan is eligible to become ready, H-05 passes the typed plan to the
H-06 pure plan-hash function and embeds the returned lowercase digest as
`plan_hash`; the subsequent H-05 `report_sha256` therefore commits to the
embedded H-06 digest. While an H-05 report is blocked, `plan_hash` remains
null and no H-06 digest is fabricated.

Required boundary tests are:

1. H-05 golden vectors prove `report_sha256` is absent, not null, during
   hashing; the JCS hash input has no LF; and the final report has exactly one
   LF.
2. H-06 golden vectors prove each self-hash key is absent, not null; the
   custom canonical hash input has exactly one LF; and the stored artifact has
   exactly one LF.
3. Plan vectors prove the H-06 domain prefix and LF are present and that H-05
   can embed only the returned digest, not recompute it.
4. A control-character vector and a non-ASCII key-order vector using U+E000
   and U+10000 produce and lock the intentionally different encoding behavior.
5. Closed-schema tests reject a dry-plan report as a semantic plan or manifest,
   reject a manifest as a report, reject `report_sha256` in the H-06 plan
   projection, and reject a report hash substituted for `plan_sha256`.
6. Cross-substitution vectors feed identical allowed scalar content to both
   canonicalizers and prove the encoded bytes/digest domains cannot be treated
   as the other artifact type, even if a particular ASCII-only subobject would
   serialize identically.
7. Two clean processes and checkouts reproduce each artifact independently,
   then verify that only the typed H-06 digest crosses into H-05 `plan_hash`.

Selecting one shared canonicalizer instead would change H-05's currently
recorded owner-approved report contract or H-06's proposed manifest contract,
their tests, and at least one file ceiling. No technical requirement found in
this pass forces that expansion. If an owner requires one shared
canonicalization, both phases must stop for a joint file-exact decision; H-06
must not select the winner silently.

## 6. Fail-closed local writer

The same write primitive publishes immutable step records and restricted
attempt snapshots; only the former receives a canonical non-hidden evidence
name. An attempt snapshot is also no-replace and never updated in place. The
proposed local writer has these ordered phases. Every outcome is a typed
result; no parse, schema, hash, I/O, lock, or durability failure is converted
to empty state.

1. **Bind root.** Open the configured profile history root through a trusted
   repository directory descriptor. Verify the exact profile and operation
   gate before permitting creation. If an authorized writer must create the
   final history directory, create that single descriptor-relative component
   with mode `0700`, then `fsync` its already-open parent directory. Reject a
   raced non-directory or symlink. Mainnet and testnet roots are never
   interchangeable.
2. **Validate path.** Apply Section 5.3. Walk existing parent components with
   directory descriptors and no-follow flags. Reject symlinks, non-directories,
   path escape, and unexpected files. Reading never creates a directory.
3. **Acquire lock.** Open a profile-local `.manifest-v2.lock` with create,
   read/write, no-follow, and mode `0600`; acquire an exclusive advisory lock.
   Fail closed on unsupported locking. Re-read the directory and current index
   only after holding the lock.
4. **Validate input.** Validate the entire schema, semantic invariants,
   canonical ordering, sensitivity allowlist, prior record, source identity,
   plan identity, and proposed target name before opening a temporary file.
5. **Check collision.** If the immutable target exists, reject symlinks. Exact
   existing canonical bytes with the same validated hash are an idempotent
   `already-present` result and are not rewritten. Any other target is a
   collision/corruption result.
6. **Create temp.** In the target directory, create
   `.<final-name>.tmp.<32-lowercase-random-hex>` using exclusive create,
   no-follow, and mode `0600`. Randomness names the temporary file only and
   never enters evidence. Retry a bounded number of name collisions.
7. **Write.** Write the already-built canonical byte string in a complete-write
   loop. Flush language buffers and call file `fsync`. Any short write or
   error fails.
8. **Re-read.** From the still-open file descriptor, seek to zero and read all
   bytes. Require exact byte equality, parse with duplicate-key rejection,
   revalidate schema and semantics, recompute the self-hash, and require EOF at
   the expected length.
9. **Publish immutable.** Atomically rename in the same directory with
   no-replace semantics. Linux `renameat2(RENAME_NOREPLACE)` and macOS
   `renameatx_np(RENAME_EXCL)` are acceptable platform adapters. If an
   equivalent atomic no-replace primitive is unavailable, fail closed; a
   check-then-rename sequence is not sufficient.
10. **Sync directory.** Open the target directory and call directory `fsync`
    before reporting durable success.
11. **Unlock.** Release the lock only after the typed result is fixed.

No partial file ever receives the canonical name. No completed immutable
record is overwritten, truncated, appended, repaired in place, or mutated.

On any failure before rename, close and unlink only the exact temporary file
created by this invocation, then directory-fsync that cleanup when possible.
Never glob, remove a caller-supplied path, or delete an existing canonical
file. A cleanup failure is separately reported.

If rename succeeds but directory `fsync` fails or has an indeterminate result,
the writer returns `H06_POST_RENAME_DURABILITY_AMBIGUOUS`. It must not delete,
rewrite, claim durable success, or promote current. On a later authorized
run, reconciliation under the lock may validate the exact final bytes and
hash, re-fsync the directory, and then report a durable `already-present`
result. The ambiguity itself stays in restricted local attempt evidence.

Concurrent writers serialize through the profile lock and revalidate the
prior head/current identity inside it. A process that began from a stale head
fails with `H06_STALE_PRIOR_IDENTITY`. An uncooperative writer is still
contained by atomic no-replace publication and content-addressed filenames.

The platform adapter is **not demonstrated**. Static inspection on the current
macOS host found:

- Python 3.12 `os.rename` and `os.replace` accept source/destination directory
  descriptors but no flags;
- `os` exposes no `renameat2`;
- the process C library exposes `renameatx_np` and `renamex_np`; and
- the installed macOS SDK declares `renameatx_np(..., RENAME_EXCL)`.

This proves symbol availability only. No no-replace call, filesystem
capability check, collision behavior, error mapping, crash boundary, or
directory durability was exercised. No Linux host was tested, and the Linux
`renameat2(RENAME_NOREPLACE)` standard-library/`ctypes` path was not
demonstrated.

Standard-library `os.link` is an additional OD-04 feasibility candidate, not
proven or approved behavior. A candidate would hard-link the fully written,
file-fsynced, re-read same-directory temporary inode to the final basename
using source/destination directory descriptors and `follow_symlinks=False`.
Existing-target refusal must be atomic. After link success it would
directory-fsync the new canonical name, unlink only the exact temporary
basename, and directory-fsync that unlink. Link-success/fsync ambiguity,
link-success/unlink failure, and second-fsync ambiguity each require distinct
non-success reconciliation states; none may promote current. Phase B
feasibility must prove inode identity, same-filesystem behavior, symlink and
race refusal, collision mapping, crash boundaries, exact unlink handling, and
both directory-fsync boundaries on macOS and Linux before selecting this
candidate over a platform rename adapter.

The eight-file ceiling therefore remains conditional, not established.
Before general Phase B work, a separately authorized feasibility gate must
prove macOS and Linux adapters inside `manifest_schema.py`, using only standard
library facilities and tests in `test_current_manifest_promotion.py`. Both
platforms must prove same-directory no-replace, existing-target refusal,
descriptor-relative operation, symlink refusal, stable error mapping, and
directory-fsync behavior without skips. The feasible adapter may be a proven
platform rename primitive or proven `os.link` protocol. Failure on either
platform is a Phase B stop and an explicit owner decision about a ninth file,
dependency, external restricted-state root, or reduced platform support;
scope must not widen silently.

## 7. Current-index promotion

`current-manifest.json` becomes a generated `current_index`, never independent
evidence authority. It has exactly this closed shape:

```json
{
  "schema": "ripe.robinhood.deployment-manifest",
  "schema_version": 2,
  "artifact_kind": "current_index",
  "index_sha256": "<64-lowercase-hex>",
  "profile": {
    "profile_id": "robinhood-mainnet",
    "expected_chain_id": 4663
  },
  "source": {
    "commit": "<40-lowercase-hex>",
    "tree": "<40-lowercase-hex>",
    "plan_sha256": "<64-lowercase-hex>"
  },
  "target": {
    "path": "<normalized-immutable-basename>",
    "record_id": "<terminal-record-id>",
    "record_sha256": "<64-lowercase-hex>"
  },
  "prior_index_sha256": null,
  "plan_status": "complete"
}
```

`prior_index_sha256` is null only for first promotion and otherwise equals the
exact index identity re-read under lock. The index source and plan fields must
equal the immutable target's active terminal-plan values.

A reader first validates the index and its self-hash, then loads the immutable
target and validates the entire chain. The index cannot supply a field missing
from the immutable record or override a disagreement.

Promotion is permitted only while holding the profile writer lock and only
after all of these checks pass:

1. every required semantic action and step is represented exactly once;
2. every executable required action is reconciled;
3. every required receipt, finality observation, event check, and
   postcondition is complete and matched;
4. all omission/deferred/rejected/tooling reservations have truthful typed
   dispositions;
5. the terminal immutable record has `plan_state.status: complete`;
6. the complete immutable chain validates profile, chain, every marked
   source/plan boundary, semantic IDs, prior IDs, and every self-hash;
7. the caller's prior current index identity equals the index re-read under
   lock;
8. the new immutable target has completed file and directory `fsync`;
9. the target path and target hash agree.

Promotion serializes and validates a new index, writes/fsyncs/re-reads it in a
same-directory unique `0600` temporary file, and atomically renames it over
`current-manifest.json` while holding the lock. It then directory-fsyncs.
The path walk and current target are rechecked with descriptor-relative
no-follow operations immediately before rename; a current symlink or
non-regular file fails closed. The old or new complete index may be visible,
never a partial index.

If index rename succeeds but directory `fsync` is ambiguous, return
`H06_CURRENT_PROMOTION_AMBIGUOUS` and do not claim promotion. A later reader
must determine whether the old or new complete index survived, validate its
target and prior identity, and reconcile under lock. It must never repeat the
promotion blindly.

A failed, partial, durability-ambiguous, finality-pending, unreconciled,
wrong-profile, wrong-chain, wrong-plan, stale, or corrupt step can never
promote current.

## 8. H-05 read-only semantic interface

H-06 proposes one narrow interface that H-05 may consume:

```text
read_history(
  configured_profile_id,
  configured_expected_chain_id,
  expected_plan_sha256,
  expected_source_commit,
  expected_source_tree,
  configured_history_root
) -> HistoryReadResult
```

The closed result variants are:

| Variant | Exact meaning |
| --- | --- |
| `valid` | Every immutable record, link, identity, hash, and any current index validates. Returns typed records, head, terminal state, and semantic action IDs. |
| `absent-clean` | The configured root is absent or has no index/record/temp/symlink. A recognized regular unlocked local lock file alone is ignored; a held, malformed, or symlink lock is not clean. |
| `incomplete` | A valid chain or valid anchored attempt exists but lacks required steps, a terminal complete record, or a promotable index. |
| `corrupt` | JSON parse, duplicate key, schema, canonical bytes, self-hash, prior-link, filename, path, or plan/source identity consistency validation fails. This includes a plan hash paired with source commit/tree values that do not belong to that plan, whether the disagreement is inside the chain/index or between a matching expected plan hash and the caller's expected source tuple. |
| `stale` | The internally consistent unique valid immutable head is newer than a valid current index, or the index's prior identity disagrees without creating multiple valid heads. It never covers a plan/source identity inconsistency. |
| `wrong-profile` | Valid evidence names a profile other than the configured profile. |
| `wrong-chain` | Valid evidence names a chain other than the configured expected chain. |
| `wrong-plan` | The unique active/current or terminal plan that is required to match `expected_plan_sha256` has a different plan SHA-256. Valid ancestor records may retain predecessor plan hashes at marked forward plan transitions and do not cause this result. |
| `ambiguous` | Multiple heads, conflicting duplicate IDs, an unresolved post-rename state, or more than one valid current candidate prevents a unique result. |

Classification first validates every record and marked plan transition,
identifies a unique immutable head, and distinguishes its active plan from
legitimate predecessor plans in ancestors. Precedence is: path
safety/parse/schema/canonical/hash/link failure or any inconsistent
plan/source identity as `corrupt`; profile mismatch; chain mismatch;
multiple-head/current/post-rename uncertainty as `ambiguous`; `wrong-plan`
only when the internally valid unique active/current or terminal comparison
target does not match `expected_plan_sha256`; then stale current identity;
then incomplete, absent-clean, or valid. The deterministic rule is:
**inconsistent plan/source identity is always `corrupt`, never `stale`.** A
valid current index that merely points to an older predecessor-plan terminal
while one unique newer head matches the expected plan is `stale`, not
`wrong-plan`. A chain is not wrong-plan merely because it contains more than
one plan hash across valid forward transitions. Results carry only stable
sanitized diagnostic codes and safe semantic IDs.

The reader:

- performs no writes, repairs, chmods, renames, directory creation, lock-file
  creation, or current promotion;
- may open an already-existing regular lock with no-follow and take/release a
  nonblocking shared advisory lock solely to obtain a stable snapshot; a held
  exclusive lock yields `ambiguous`, and no lock is ever created by a reader;
- does not swallow parse, schema, hash, permission, or I/O errors;
- does not infer action identity from transaction position;
- does not reduce records to an ordered list of transaction strings;
- does not fall back to Base history, source, blobs, or deployments;
- returns immutable typed values rather than mutable internal dictionaries.

H-05 may use the typed semantic action IDs and status to decide whether its
own approved planner sees completed work. H-05 must not implement v2
serialization, hashing, schema validation, atomic writing, chain repair, or
current promotion.

### 8.1 H-05/H-06 sequencing and ownership

The mandatory sequencing rule has now been satisfied for Phase A authority:
H-05 was independently reviewed, committed, and integrated first. The exact
binding is H-05 evidence SHA-256
`28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c`
at controlling integration commit
`7a3a36666f277277fa08b55081b3f58c7cd3ba64`. That integration changes no
implementation source. In particular, `scripts/utils/migration.py` remains
SHA-256 `c0bc3ff369d5664af3d96585c7870b8be723b54930664b5f1ce8870f8ace53e3`,
so the originally anticipated H-05/H-06 overlapping-byte condition is
currently vacuous.

The controlling interface contract is:

1. H-05's exact six-file future ceiling is the six paths in Section 1.1; it
   excludes `migration.py`, `migration_helpers.py`, H-06 files, namespaces,
   histories, and execution.
2. H-05 owns its typed deterministic blocked plan/report and RFC 8785/JCS
   `report_sha256`: remove `report_sha256` entirely, JCS-serialize without a
   terminal LF, hash those bytes, insert the lowercase digest, JCS-serialize
   again, and append exactly one LF to the final report.
3. H-05's semantic history protocol lives in `migration_runner.py`; its only
   Phase B synthetic lives in `test_execution_plan.py`. H-05 never implements
   the real reader, serializer, hash chain, writer, repair, or promotion.
4. Migration IDs are exact four-digit ASCII-decimal strings under the approved
   H-05 identifier convention. H-05 owns its canonical source filename;
   H-06 owns only the manifest filename grammar in Section 4.1.
5. H-06 owns the typed plan digest, `plan_sha256`, evidence
   schema/canonicalization, validation, immutable writing, history reading,
   hash-chain verification, and current promotion.
6. A later file-exact execution-hardening authorization with an explicitly
   assigned owner must create truthful typed transaction results and correct
   exhausted retry, ambiguous submission, false `None` success, and persisted
   `"None"`. H-05 Phase B and H-06 do not own submission, retry, or result
   classification.

Any later source change or overlapping byte still invalidates a proposed H-06
implementation patch and review ceiling without a byte-size threshold. H-06
Phase B, if separately authorized, must reconcile against the then-current
exact `migration.py`, not this Phase A baseline. The integration seam may pass
typed H-05 plan and later execution results into H-06, but neither workstream
may reimplement the other's canonicalizer or assume authority assigned only
to the future execution-hardening package.

## 9. Retention and sensitivity

### 9.1 Safe and required to commit

After policy completion and independent review:

- complete immutable step records and the generated current index;
- schema/profile/chain/source/plan/step/action IDs and hashes;
- approved public contract/configuration subject addresses;
- an approved public operator role address only when the typed plan names that
  address as a required postcondition subject; it is not a transaction-signer
  field;
- approved public transaction hash;
- sanitized receipt block number/hash, Boolean status, and gas used;
- allowlisted event projections and matched postcondition evidence;
- truthful omission, blocked, deferred, rejected, and tooling-only
  dispositions containing only stable codes and digests.

### 9.2 Local restricted evidence, not committed

- canonical attempt records for planned, submitted, confirmed,
  finality-pending, failed, blocked, or durability-ambiguous work;
- sanitized stable error codes and phase/action IDs;
- local writer lock and exact temporary files while an authorized write is in
  progress;
- reconciliation observations that have not reached policy finality.

Restricted evidence uses mode `0600`, profile isolation, and an explicit local
retention limit. It is never a source for current authority and must be
destroyed only by a separately authorized, exact-target cleanup.

The bounded retention recommendation is:

| Class | Maximum custody | Cleanup boundary |
| --- | --- | --- |
| `success-7d` | Seven calendar days after durable immutable write and successful current promotion | Exact attempt IDs may be deleted after owner-approved cleanup; no recursive path is permitted. |
| `failure-30d` | Thirty calendar days after the failed/blocked attempt is closed | Retain through incident review, then delete only the exact reviewed files. |
| `ambiguity-until-resolved-30d` | Until durability/submission/finality ambiguity is explicitly resolved, then at most 30 additional days | Never delete unresolved ambiguity; escalate at day 30 and retain in restricted quarantine until an owner disposition. |

Pre-rename temporary files are cleaned immediately by the writer's
exact-target failure path. The attempt contains only the retention-class code;
creation, closure, and deletion times are local custody metadata, not committed
evidence or hash authority. No automatic recursive cleanup is authorized.

The public-address recommendation is to omit transaction `from`/signer
identity entirely. If an operator address is an approved configuration fact,
store it only as a typed expected/observed role postcondition subject. Never
derive or copy it from a signer object, exception, environment value, or
provider payload. The public transaction hash remains sufficient for an
external chain observer to derive the sender, so residual privacy exposure
cannot be eliminated by omitting the duplicated field.

Restricted attempt, lock, and temporary names must not enter ordinary Git
scope. The bounded recommendation adds the repository-root `.gitignore` as
the eighth Phase B file with exactly these six anchored rules:

```gitignore
/migration_history/robinhood-mainnet/v1/.attempt-*
/migration_history/robinhood-mainnet/v1/.manifest-v2.lock
/migration_history/robinhood-mainnet/v1/.*.tmp.*
/migration_history/robinhood-testnet/v1/.attempt-*
/migration_history/robinhood-testnet/v1/.manifest-v2.lock
/migration_history/robinhood-testnet/v1/.*.tmp.*
```

These rules cover only direct H-06 operational artifacts under the exact two
configured Robinhood profile history roots. They do not ignore immutable
manifest records, `current-manifest.json`, Base namespaces, similarly named
files outside those roots, or malformed/near-match names. Ignore protection
is defense in depth, not evidence admission policy: exact-scope review must
still reject a force-added restricted artifact. This Phase A text proposes
the rules but does not approve or create `.gitignore`, either history root, an
operational file, or Phase B.

### 9.3 Never stored

- secrets, seed phrases, private keys, keystore contents, authentication
  tokens, cookies, or headers;
- RPC URLs, endpoint components, provider credentials, or account backends;
- environment variables, environment dumps, command history, home/cache/temp
  paths, or host identity;
- raw provider requests, responses, payloads, logs, debug traces, or
  correlation bodies;
- raw or unredacted exception text, class, cause, traceback, stderr, stdout,
  or arbitrary log messages;
- signer secrets, signer backend details, signature material, or an
  unapproved signer identity;
- unsigned transaction objects, raw calldata, nonces, gas-price bids, signed
  transaction bytes, signatures, or recovered signing material beyond the
  approved public transaction hash;
- compiler input/source blobs, ABI dumps, encoded constructor arguments, or
  filesystem paths copied wholesale from the legacy Base manifest shape.

The schema is closed and allowlisted. Rejection scans are defense in depth,
not permission to accept an unrecognized field after redaction.

## 10. Proposed smallest Phase B ceiling

The exact conditional eight-file ceiling is approved as the OD-07/OD-10 Phase
A design choice, but remains conditional on the OD-04 feasibility stop and
authorizes no Phase B work or file change:

| # | File | Why necessary |
| ---: | --- | --- |
| 1 | `docs/chains/rh/evidence/robinhood-manifest-phase-a.md` | Convert Phase A assumptions into reviewed Gate 1 implementation evidence, command output, and dispositions. |
| 2 | `scripts/utils/migration.py` | Replace contract-only pre-success mutation with the typed semantic record handoff and remove positional/current authority from the Robinhood v2 route while preserving Base behavior. This is the overlap file identified by the controlling task and must be re-evaluated against integrated H-05. |
| 3 | `scripts/utils/json_file.py` | Provide or route the low-level fail-closed atomic byte writer while preserving explicit legacy JSON reads. |
| 4 | `scripts/utils/manifest_schema.py` | New closed schema model, canonical serializer, hash-chain reader, sensitivity validation, immutable writer, lock handling, and current promotion. |
| 5 | `docs/chains/rh/schemas/deployment-manifest-v2.schema.json` | Reviewable machine-readable structural contract for v2 artifacts. |
| 6 | `tests/deployment/test_manifest_schema.py` | Schema, canonicalization, hashing, semantic reader, sensitivity, Base compatibility, and deterministic cross-process tests. |
| 7 | `tests/deployment/test_current_manifest_promotion.py` | Atomic-write fault injection, concurrency, stale identity, path safety, durability ambiguity, and promotion tests. |
| 8 | `.gitignore` | Add only the six exact anchored Section 9.2 patterns so restricted H-06 attempts, locks, and temporary files under the two Robinhood profile roots do not enter ordinary Git scope while immutable records/current indexes remain visible. |

No ninth file is presently proposed, but OD-04 feasibility has not proved that
the platform rename or `os.link` adapters fit this ceiling. Test fixtures can
otherwise be constructed inside the two test modules and temporary
directories. Phase B must not begin beyond the separately authorized adapter
feasibility gate. If that proof or later implementation requires a fixture
file, platform helper, dependency/lockfile change, profile path change,
external restricted-state-root design, or any other ninth file, work stops
for an exact owner decision; the ceiling must not widen silently.

The ceiling explicitly excludes every item in Section 1.3. In particular it
does not authorize a Robinhood history directory or record.

## 11. Required future tests

No implementation suite was run in Phase A. Gate 1 Phase B must include these
exact groups:

### 11.1 Schema and semantic identity

- one complete schema-valid record for each action kind;
- missing, unknown, extra, and wrong-type fields at every envelope boundary;
- zero versus absent, explicit-null, unknown, and not-applicable, with every
  explicit-null branch pinning its actual non-null type;
- wrong schema/version/artifact kind;
- wrong profile, chain, source commit/tree/set, plan, migration/step/action ID,
  and prior record hash;
- internally inconsistent plan/source identities and a matching expected plan
  paired with the wrong expected source tuple classify as `corrupt`, while an
  internally valid older current index classifies as `stale`;
- numeric-only migration IDs, leading-zero preservation, unambiguous immutable
  filename parsing, and rejection of nonnumeric/unapproved H-05 grammars;
- duplicate actions, ordinals, postconditions, source paths, and heads;
- partial action failure and a reverted receipt;
- finality-pending and reconciliation-pending attempts;
- configuration and assertion evidence with matched/mismatched postconditions;
- truthful omission, blocked, deferred, rejected, and tooling-only records;
- valid and invalid `supersedes` ancestry/order/action/postcondition references;
- all three retention classes and rejection of any other retention value;
- byte-for-byte equality between the committed schema JSON and the Section
  5.2 output of the authoritative in-code schema builder; mutation tests for
  every required key, conditional, enum, explicit-null type branch, other type
  branch, and `additionalProperties` rule must make either generated-byte or
  validation tests fail, using only the standard library.

### 11.2 Canonical bytes and tamper evidence

- deterministic key order, array order enforcement, integer/Boolean/null
  rendering, escaping, UTF-8, NFC rejection, whitespace, and terminal LF;
- duplicate-key and float rejection;
- path normalization and path-byte ordering;
- self-hash omission/reinsertion;
- source-set, plan, and plan-action concatenation with known vectors;
- artifact-type separation by closed `artifact_kind` and disjoint encodings,
  plus the separately prefixed event-evidence digest;
- every Section 5.6 H-05/H-06 boundary vector, including RFC 8785 no-LF hash
  input, H-06 LF hash input, control-character and U+E000/U+10000 ordering,
  typed digest embedding, and both cross-substitution directions;
- tampering with any action, receipt, finality, postcondition, prior ID/hash,
  source, or plan breaks validation;
- two clean processes in two independent checkouts construct byte-identical
  canonical records and hashes from the same approved typed input.

The exact event-evidence known vector uses prefix UTF-8
`ripe-manifest-v2-event-evidence`, one `00` byte, and the following canonical
projection text followed by exactly one `0a` byte:

```json
{"block_hash":"0x2222222222222222222222222222222222222222222222222222222222222222","block_number":123,"data":"0x0001ff","emitter":"0x3333333333333333333333333333333333333333","expected_chain_id":4663,"log_index":0,"topics":["0x4444444444444444444444444444444444444444444444444444444444444444","0x5555555555555555555555555555555555555555555555555555555555555555"],"transaction_hash":"0x1111111111111111111111111111111111111111111111111111111111111111"}
```

The expected lowercase digest is
`4008ce9d56daa4cfe33ebea06761a8508ca04933d7709670c81f944d7df4c79b`.
The vector's `event_evidence_sha256` is outside the projection. A verifier
must reproduce this digest from a synthetic public receipt log and must reject
each independent negative case: omitted or extra projection key; the digest
inserted into the projection; missing receipt transaction/block linkage;
wrong chain, transaction hash, block number, block hash, log index, or
emitter relative to the parent; uppercase or malformed-length transaction,
block, topic, emitter, or data hex; odd-length data; reordered, omitted,
duplicated, or changed topics; changed raw data including a removed leading
zero byte; absent or extra LF; changed prefix or missing NUL; and substitution
of this digest for a record, attempt, index, source-set, report, plan, or
plan-action digest.

### 11.3 Atomic writer faults

Inject and assert typed outcomes for:

- failure before temporary-file creation;
- temporary create and collision failure;
- short/error writes during the complete-write loop;
- failure before and during file `fsync`;
- corruption detected by re-read after file `fsync`;
- failure immediately before rename;
- no-replace collision at rename;
- failure/ambiguity immediately after rename;
- failure during directory open or directory `fsync`;
- cleanup failure before rename;
- reconciliation of an exact post-rename ambiguous target;
- refusal to mutate an existing completed record.

At every boundary, assert that no partial canonical file is visible and no
completed immutable record changes.

The same no-skip suite must run against the macOS `renameatx_np(RENAME_EXCL)`
adapter and Linux `renameat2(RENAME_NOREPLACE)` adapter. It must prove
descriptor-relative same-directory publication, existing-target refusal,
symlink refusal, stable collision/error classification, and directory fsync.
Missing platform evidence is a feasibility stop, not an xfail.

If OD-04 selects the `os.link` candidate, the same no-skip suite must also
prove exact temporary-inode identity, atomic existing-target refusal,
same-filesystem enforcement, first directory-fsync before exact-temp unlink,
second directory-fsync after unlink, and distinct truthful ambiguity handling
for link success, either fsync, and unlink failure on both platforms. Merely
exposing `os.link` is not proof.

### 11.4 Promotion, concurrency, and path safety

- incomplete, failed, ambiguous, finality-pending, unreconciled, or mismatched
  history never promotes current;
- stale prior current identity never promotes;
- promotion only after a durable immutable target and complete chain;
- exact `robinhood-confirmations-64-v1` thresholds, second-observation
  receipt/block equality, required event replay, and final postcondition match;
- current index self-hash and target disagreement fail closed;
- old-or-new complete current visibility during atomic replacement;
- post-index-rename directory-fsync ambiguity is not success;
- two concurrent writers from the same head yield one durable winner or one
  idempotent exact result plus one typed stale/collision result;
- concurrent writers from different heads reject the stale writer;
- target, parent, lock, temp, current, and immutable symlinks are rejected;
- absolute, traversal, backslash, URI, case-alias, and root-escape paths are
  rejected;
- reads never create a directory, lock, temp, repair, or index.

### 11.5 Sensitivity and legacy regression

- reject sensitive field names and synthetic secret, endpoint, environment,
  signer, provider-payload, raw exception, traceback, raw transaction,
  calldata, and signature values;
- omit transaction signer/from while allowing only an approved typed public
  operator role subject; reject signer-derived or unapproved addresses;
- prove `success-7d`, `failure-30d`, and
  `ambiguity-until-resolved-30d` classification and exact-target-only cleanup
  inputs without performing cleanup;
- prove failure diagnostics contain only stable codes and safe IDs;
- use `git check-ignore` and exact-scope review fixtures to prove all six
  anchored Section 9.2 patterns ignore every valid restricted attempt, lock,
  and temporary name directly under each exact Robinhood root; immutable
  manifest records and `current-manifest.json` are not ignored; Base and
  unrelated paths are unaffected; malformed and near-match filenames are not
  accidentally ignored; and a force-added restricted artifact is still
  rejected;
- parse every committed Base JSON file with the legacy reader;
- assert both exact Base record shapes remain readable without rewriting;
- hash every Base history and source file before/after tests and prove no
  mutation, normalization, directory creation, or fallback;
- preserve the current Base manifest compatibility path and behavior;
- prove Robinhood mainnet/testnet histories cannot cross-read and Robinhood
  cannot read Base history/source/`Ledger` as fallback.

## 12. Approved owner-decision packet

These decisions are ordered by potential blast radius. The owner selected
each Recommended choice against the exact pre-approval artifact SHA-256
`4458b90dc878c4e3ff2e2c0d6fc8b32e1baf7a7e33c1c8c15002b8524680ddc2`.
The following approval record is verbatim:

```text
I approve H‑06 Phase A owner decisions OD‑01 through OD‑12 exactly as presented in `docs/chains/rh/evidence/robinhood-manifest-phase-a.md` at SHA-256 `4458b90dc878c4e3ff2e2c0d6fc8b32e1baf7a7e33c1c8c15002b8524680ddc2`, selecting the Recommended choice for each:

- OD‑01: the closed `ripe.robinhood.deployment-manifest` v2 schema, `[0-9]{4}` IDs, authoritative in-code builder, byte-identical generated schema, and `/v1/` as the history namespace.
- OD‑02: separate H‑05 RFC 8785 `report_sha256`, H‑06 v2 `plan_sha256`/manifest hashes, and the separately domain-separated event-evidence digest.
- OD‑03: the immutable content-addressed single-head chain with explicit prior linkage, terminal completion, and non-authoritative anchored attempts.
- OD‑04: the fail-closed writer design with a mandatory pre-Phase-B macOS-and-Linux feasibility stop. No adapter, fallback, ninth file, dependency, or external state root is approved yet.
- OD‑05: `current-manifest.json` only as a generated, self-hashed compare-and-swap pointer to a durable validated terminal chain.
- OD‑06: `robinhood-confirmations-64-v1`, including the seven reconciliation conditions. I accept the stated residual reorganization, sequencer, L1-finality, and single-observation-source risk unless a stronger H‑07 or chain-owner policy is later approved.
- OD‑07: the conditional eight-file ceiling’s six narrowly scoped `.gitignore` patterns, the three retention classes, exact-target cleanup, no stored signer/from field, and operator addresses only as approved typed role postconditions.
- OD‑08: strict legacy/v2 dispatch, byte-identical Base compatibility, and no Robinhood fallback to Base paths, blobs, Ledger, source, or history.
- OD‑09: the nine-result H‑05/H‑06 read interface, H‑05 synthetic/H‑06 real-reader split, H‑06 ownership of `plan_sha256`, H‑05 ownership of `report_sha256`, bound to integrated H‑05 evidence SHA-256 `28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c` at `rh` commit `7a3a36666f277277fa08b55081b3f58c7cd3ba64`.
- OD‑10: the conditional exact eight-file Phase B ceiling, with no ninth file, dependency, external restricted-state root, or Phase B work until OD‑04 feasibility is demonstrated.
- OD‑11: at least three distinct independent Gate 1 reviewers for deployment/schema, filesystem/durability, and security/sensitivity, plus attributable H‑05-interface and Track 7 owner approvals.
- OD‑12: forward-only remediation through immutable sorted `supersedes` references, new plan/action identities, no evidence mutation, and no backward current promotion.

These approvals close only the H‑06 Phase A owner-decision packet. They do not authorize Phase B, implementation, `.gitignore` changes, schema/code/test edits, history or namespace creation, filesystem cleanup, RPC or account access, signing, transaction submission, deployment, commit, push, or merge.
```

### OD-01 — Schema identity and version

- [x] **Recommended choice:** Use
  `ripe.robinhood.deployment-manifest`, integer version `2`, the three artifact
  kinds, closed `$defs.semanticPlan`, typed values, `supersedes`, and the three
  restricted-retention classes. Use the controlling H-05 four-digit
  ASCII-decimal migration IDs, make the in-code builder authoritative, and
  require its generated schema bytes to equal the committed JSON. Treat the
  configured `v1` path component as a repository history namespace, not the
  record schema version.
- **No-change alternative:** Leave the schema/version and path meaning
  unresolved and keep Phase B stopped.
- **Smallest sufficient value/policy:** One closed v2 schema with no extension
  fields, `[0-9]{4}` migration IDs, no profile-path change, one
  standard-library validator/builder authority, and one byte-identical
  generated schema representation.
- **Risk of no change:** Implementations can produce mutually unreadable
  records or infer that `/v1/` requires the legacy Base shape.
- **Blast radius and residual risk:** All Robinhood evidence producers/readers
  and both profile histories. A future semantic type still requires schema
  version 3 rather than an open v2 escape hatch.
- **Required reviewer/owner:** Track 7 owner, H-06 schema reviewer, H-05 owner,
  and security reviewer.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-01 exactly:
  schema `ripe.robinhood.deployment-manifest`, version 2, the closed artifact
  and plan definitions in this evidence, the integrated H-05 `[0-9]{4}`
  migration-ID contract, the in-code authoritative schema and byte-identical
  generated JSON, and `/v1/` as the configured history namespace rather than
  the schema version. This does not authorize Phase B, a history directory, an
  implementation, commit, or deployment.”

### OD-02 — Canonicalization and digest ownership

- [x] **Recommended choice:** Retain both intentional encodings in Section
  5.6. H-05 constructs RFC 8785 report bytes and `report_sha256`; H-06
  constructs custom v2 manifest bytes, `plan_sha256`, and manifest self-hashes.
  A plan-ready H-05 report embeds only the H-06-returned digest as `plan_hash`;
  a blocked report keeps it null. Event-log evidence uses the separate
  `ripe-manifest-v2-event-evidence` prefix and closed projection.
- **No-change alternative:** Leave the two hash contracts adjacent but
  unbound; neither H-05 plan-ready reporting nor H-06 Phase B may proceed.
- **Smallest sufficient value/policy:** Preserve the exact absent-field and LF
  rules, H-06 domain prefixes, typed pure-function boundary, and seven
  boundary tests in Section 5.6.
- **Risk of no change:** A report digest may be mistaken for a plan digest, an
  LF may be hashed on the wrong side, or H-05 may reimplement H-06
  serialization.
- **Blast radius and residual risk:** H-05 report fixtures, H-06 schema/hash
  tests, history identity, and every future resume comparison. Residual risk
  is canonicalizer implementation error despite golden vectors.
- **Required reviewer/owner:** H-05 owner, H-06 owner, independent
  serialization/cryptographic reviewer, and Track 7 owner.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-02 exactly:
  H-05 RFC 8785 `report_sha256` and H-06 v2 canonicalization/`plan_sha256` are
  distinct non-interchangeable artifact contracts; H-05 may embed only the
  digest returned by H-06, with the exact absent-field, domain, and terminal-LF
  rules in Section 5.6. This does not authorize either Phase B,
  implementation, commit, history creation, or deployment.”

### OD-03 — Immutable-chain structure

- [x] **Recommended choice:** Use content-addressed immutable step records,
  one profile chain, explicit prior IDs/hashes, marked terminal-complete plan
  transitions, anchored non-authoritative attempts, and a single head.
- **No-change alternative:** Continue using mutable current and positional
  step files; Robinhood evidence and promotion remain prohibited.
- **Smallest sufficient value/policy:** Genesis nulls, exactly one prior link
  thereafter, no skipped link, and a terminal marker inside the hashed final
  record.
- **Risk of no change:** Partial, reordered, foreign, or rewritten state can
  appear complete.
- **Blast radius and residual risk:** All historical verification and future
  remediation. Residual risk is a valid but semantically wrong plan, which
  independent plan review must catch.
- **Required reviewer/owner:** H-06 owner, deployment-tooling reviewer, H-05
  semantic-plan owner, and protocol owner.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-03 exactly:
  the content-addressed single-head profile chain, explicit genesis/prior
  linkage, terminal-complete plan transitions, and non-authoritative anchored
  attempt model in this evidence. This does not authorize Phase B,
  implementation, history creation, commit, or deployment.”

### OD-04 — Atomic write and durability boundary

- [x] **Recommended choice:** Approve the fail-closed writer algorithm but
  keep the eight-file ceiling conditional on a macOS-and-Linux
  standard-library feasibility gate. Evaluate platform no-replace rename and
  the exact `os.link`/unlink/two-directory-fsync protocol as candidates; do
  not treat either as demonstrated.
- **No-change alternative:** Retain the current direct writer; H-06 Phase B
  and current promotion remain stopped.
- **Smallest sufficient value/policy:** One adapter implementation inside
  `manifest_schema.py` and tests inside
  `test_current_manifest_promotion.py`, proving no-replace and directory
  durability on both platforms without skips or dependencies.
- **Risk of no change:** A check-then-rename or overwrite-capable fallback can
  mutate immutable evidence; an unproved adapter can force a late ninth file
  or external-state design.
- **Blast radius and residual risk:** Local filesystems, concurrency, crash
  recovery, and every immutable record/current promotion. Residual risk
  remains for filesystems that claim but do not honor the required semantics;
  they must fail closed.
- **Required reviewer/owner:** Independent macOS filesystem reviewer,
  independent Linux filesystem reviewer, H-06 owner, and security reviewer.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-04 exactly:
  the fail-closed writer and a mandatory pre-Phase-B feasibility stop until
  macOS and Linux standard-library adapters, including any selected
  no-replace rename or exact `os.link`/unlink/fsync protocol, are demonstrated
  inside the proposed two files. Failure on either platform requires a new
  owner decision; no fallback, ninth file, dependency, or external state root
  is authorized.”

### OD-05 — Generated current index

- [x] **Recommended choice:** Make `current-manifest.json` only a generated,
  self-hashed pointer with prior-index compare-and-swap and complete target
  chain revalidation.
- **No-change alternative:** Keep mutable current as independent authority;
  Robinhood promotion remains prohibited.
- **Smallest sufficient value/policy:** The closed index object in Section 7,
  one expected prior index identity, one terminal target, atomic replacement,
  and directory `fsync`.
- **Risk of no change:** Partial or stale current state can override immutable
  evidence.
- **Blast radius and residual risk:** Resume, operator inspection, and all
  consumers of current. Post-rename directory-fsync ambiguity remains possible
  and must remain a non-success state.
- **Required reviewer/owner:** H-06 owner, deployment-tooling reviewer, and
  filesystem/durability reviewer.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-05 exactly:
  `current-manifest.json` is only the generated self-hashed compare-and-swap
  pointer in Section 7 and can promote only a durable terminal validated
  chain. This does not authorize Phase B, a current file, history creation,
  commit, or deployment.”

### OD-06 — Finality and reconciliation

- [x] **Recommended choice:** Adopt the bounded
  `robinhood-confirmations-64-v1` policy in Section 4.4.1: successful matching
  receipt, 64 successor blocks, identical second receipt/block observation,
  and all required events/postconditions rechecked and matched.
- **No-change alternative:** Leave policy unspecified and keep mainnet current
  promotion disabled. This is fail-closed but operationally unusable.
- **Smallest sufficient value/policy:** Exactly 64 confirmations and two
  consistent observations, with the second at or after the threshold; no
  endpoint/payload evidence.
- **Risk of no change:** No record can truthfully become promotable. Selecting
  a weaker implicit rule instead risks promoting reorganized or sequencer-only
  state.
- **Blast radius and residual risk:** Every executable action and current
  promotion. Residual chain/sequencer/L1-finality and single-observation-source
  risk remains explicit; H-07 or the chain owner may require a stronger policy.
- **Required reviewer/owner:** Robinhood chain/operations owner, protocol
  owner, security reviewer, and H-06 owner.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-06 exactly:
  policy `robinhood-confirmations-64-v1` with the seven reconciliation
  conditions in Section 4.4.1, and I accept its stated residual
  reorganization/sequencer risk unless a stronger H-07/chain-owner policy is
  approved. This approves design only and authorizes no RPC, Phase B,
  transaction, history promotion, or deployment.”

### OD-07 — Retention, redaction, and public operator addresses

- [x] **Recommended choice:** Adopt the conditional eight-file ceiling,
  including only the narrowly scoped repository-root `.gitignore` rules in
  Section 9.2; adopt `success-7d`, `failure-30d`, and
  `ambiguity-until-resolved-30d`; use exact-target owner-approved cleanup; omit
  transaction signer/from; admit an operator address only as an approved typed
  role postcondition.
- **No-change alternative:** Retain the seven-file ceiling and keep Phase B
  stopped until a reviewed external restricted-state-root design exists.
- **Smallest sufficient value/policy:** Seven days after successful promotion,
  30 days after closed failure, unresolved ambiguity retained through
  resolution plus no more than 30 days, no recursive deletion, and exactly the
  six anchored ignore patterns for the two configured Robinhood roots.
- **Risk of no change:** Sensitive operational evidence accumulates, while
  repository-local restricted names remain exposed to accidental Git scope;
  an undefined external state root can escape profile/path review; and
  inconsistent address handling leaks identity or makes role evidence
  unverifiable.
- **Blast radius and residual risk:** Local restricted custody and committed
  postconditions plus the repository-root ignore policy. Narrow patterns do
  not prevent force-add, so exact-scope review remains mandatory. Public
  transaction hashes still allow external derivation of sender identity.
- **Required reviewer/owner:** Security/privacy reviewer, operations evidence
  custodian, repository/Git policy owner, protocol role owner, and H-06 owner.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-07 exactly:
  the conditional eight-file ceiling's narrowly scoped `.gitignore`, the
  three retention classes and exact-target cleanup in Section 9, no stored
  transaction signer/from field, and operator addresses only as approved typed
  role postconditions. This authorizes no `.gitignore` edit, cleanup, Phase B,
  history root or write, account access, signing, or deployment.”

### OD-08 — Legacy Base compatibility

- [x] **Recommended choice:** Keep strict explicit legacy/v2 reader dispatch,
  both Base record shapes, the exact Base current path, byte immutability, and
  absolute prohibition on Robinhood fallback.
- **No-change alternative:** Reuse generic current/step parsing and accept
  fail-open empty state; H-06 cannot proceed.
- **Smallest sufficient value/policy:** Parse every committed Base JSON,
  preserve all hashes, and perform no Base write, normalization, schema
  backfill, or source/history fallback.
- **Risk of no change:** H-06 can break Base tooling or treat legacy Base
  evidence as Robinhood authority.
- **Blast radius and residual risk:** All Base migration inspection and
  regression behavior. Residual ambiguity inside legacy histories remains
  documented and must never be “repaired.”
- **Required reviewer/owner:** Base deployment owner, H-02 owner, H-06 owner,
  and regression reviewer.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-08 exactly:
  strict legacy/v2 dispatch, unchanged Base paths and bytes, both legacy record
  shapes, and no Robinhood Base path/blob/Ledger/history fallback. This does
  not authorize Phase B, a Base edit, history rewrite, commit, or deployment.”

### OD-09 — H-05/H-06 interface and digest handoff

- [x] **Recommended choice:** Use the nine typed history results, current
  classification precedence, H-05 synthetic-only Phase B protocol, H-06 real
  reader, and Section 5.6 digest handoff, bound to integrated H-05 evidence
  SHA-256 `28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c`
  at `rh` commit `7a3a36666f277277fa08b55081b3f58c7cd3ba64`.
- **No-change alternative:** Let H-05 and H-06 carry separate history and plan
  hash models; both phases remain stopped.
- **Smallest sufficient value/policy:** One typed `read_history` contract, one
  H-06 pure plan-hash function, and no H-05 manifest serializer, writer,
  repair, or promotion function.
- **Risk of no change:** Resume can fall back to transaction position, report
  hashes can be substituted for plan hashes, and file ownership can overlap.
- **Blast radius and residual risk:** H-05 planner, H-06 reader/schema, resume,
  and both workstream ceilings. Residual risk is later drift after this
  integration, handled by a new exact-hash reconciliation.
- **Required reviewer/owner:** H-05 owner, H-06 owner, deployment-tooling
  reviewer, and Track 7 owner.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-09 exactly:
  the nine-result read interface, H-05 synthetic/H-06 real-reader split, H-06
  ownership of `plan_sha256`, H-05 ownership of `report_sha256`, and mandatory
  binding to integrated H-05 evidence SHA-256
  `28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c`
  at `rh` commit `7a3a36666f277277fa08b55081b3f58c7cd3ba64`. This
  does not authorize either Phase B, implementation, commit, history, or
  deployment.”

### OD-10 — Exact Phase B file ceiling

- [x] **Recommended choice:** Retain exactly the conditional eight files in
  Section 10, including only the narrowly scoped `.gitignore`; stop on any
  ninth file, dependency, fixture, platform helper, external restricted-state
  root, or profile-path change.
- **No-change alternative:** Retain the seven-file ceiling and keep Phase B
  stopped until a reviewed external restricted-state-root design exists.
- **Smallest sufficient value/policy:** Eight files, the six exact anchored
  ignore patterns, generated in-test fixtures, and standard-library-only
  implementation after both platform proofs.
- **Risk of no change:** No implementation can begin. Silently widening
  instead would bypass ownership and security review.
- **Blast radius and residual risk:** H-06 production tooling, schema, tests,
  evidence, and the six root-anchored Git rules only. A failed adapter proof
  may make the ceiling infeasible; `.gitignore` cannot prevent force-add.
- **Required reviewer/owner:** Track 7 owner, H-06 owner, repository/Git policy
  owner, filesystem reviewer, and security reviewer.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-10 exactly:
  the conditional eight-file ceiling in Section 10, including only the six
  anchored `.gitignore` rules, with no ninth file, dependency, external
  restricted-state root, or Phase B work until OD-04 feasibility is
  demonstrated. This decision alone does not authorize `.gitignore`, Phase B,
  edits, commit, history creation, or deployment.”

### OD-11 — Gate 1 reviewers and validation

- [x] **Recommended choice:** Require at least three distinct independent
  reviewers: deployment/schema, filesystem/durability, and
  security/sensitivity. Also require attributable H-05 interface-owner and
  Track 7 owner approvals. The implementation author fills none of the three
  independent roles.
- **No-change alternative:** Leave roles unnamed and do not open Gate 1.
- **Smallest sufficient value/policy:** Three independent reviewers, two owner
  approvals, every Section 11 test, macOS and Linux adapter evidence, exact
  file/hash inventory, and full delta review after the last byte change.
- **Risk of no change:** Self-review can miss serialization substitution,
  filesystem crash behavior, or sensitive-data leakage.
- **Blast radius and residual risk:** All H-06 Phase B bytes and promotion
  safety. Human review cannot eliminate all implementation defects; required
  negative and fault-injection tests remain mandatory.
- **Required reviewer/owner:** Named deployment/schema reviewer, named
  macOS/Linux durability reviewer or two named platform specialists, named
  security reviewer, H-05 owner, and Track 7 owner.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-11 exactly:
  at least three distinct independent Gate 1 reviewers for
  deployment/schema, filesystem/durability, and security/sensitivity, plus
  attributable H-05-interface and Track 7 owner approvals, with the complete
  validation and exact-hash package after the final byte. This does not
  authorize Phase B, commit, history creation, or deployment.”

### OD-12 — Forward-only supersession and remediation

- [x] **Recommended choice:** Never mutate, delete, or point current backward.
  A new approved remediation plan/action uses the sorted `supersedes` records
  in Section 4.3 to reference the immutable prior action or postcondition, then
  becomes current only through ordinary terminal promotion.
- **No-change alternative:** Keep prior evidence immutable but provide no
  machine-readable supersession; affected current promotion remains blocked.
- **Smallest sufficient value/policy:** Prior record hash, action ID, typed
  postcondition ID/not-applicable marker, stable reason code, authority
  reference, new plan hash, and new action ID.
- **Risk of no change:** Operators may treat obsolete postconditions as current
  or rewrite old evidence to make remediation visible.
- **Blast radius and residual risk:** Chain interpretation, governance
  remediation, and audit consumers. The original public transaction remains
  irreversible and visible; supersession changes authority interpretation,
  not chain history.
- **Required reviewer/owner:** Protocol/governance owner, H-06 owner, security
  reviewer, and affected action/postcondition owner.
- **Exact approval wording:** “I approve H-06 Phase A decision OD-12 exactly:
  forward-only remediation with immutable sorted `supersedes` references, new
  plan/action identities, no evidence mutation or backward current promotion,
  and ordinary terminal promotion of the remediation record. This authorizes
  no remediation transaction, Phase B, history write, commit, or deployment.”

## 13. Gate 1 stop conditions

Phase B remains unauthorized. The approvals above close only the H-06 Phase A
owner-decision packet; a separate Phase B authorization may be considered only
after every applicable gate below, including the mandatory OD-04 feasibility
stop, is satisfied. Any of the following invalidates this ceiling and requires
renewed review:

- `rh` moves beyond the timestamped controlling
  `7a3a36666f277277fa08b55081b3f58c7cd3ba64` observation, or any controlling
  input changes;
- integrated H-05 evidence is not exactly
  `28c3e32b9732334c4904667eeb983d057d5d96391fb5fd8b13f37a9f5033af7c`,
  or its six-file ceiling, RFC 8785/JCS rules, synthetic-read boundary, or
  fixed-width four-digit migration-ID grammar changes;
- a later H-05 or execution-hardening implementation touches an overlapping
  `migration.py` byte without regenerating the H-06 patch and review ceiling;
- a ninth file, dependency, external restricted-state root, or broader
  `.gitignore` rule is needed;
- the configured Robinhood history roots or profile IDs change;
- the approved OD-02 dual-canonicalization boundary changes or a replacement
  is proposed;
- the macOS and Linux standard-library adapter feasibility proof is absent or
  either platform cannot provide lock, file-fsync, atomic no-replace, and
  directory-fsync semantics;
- the authoritative in-code schema and committed generated schema bytes differ
  or require a non-standard-library validator;
- an approved finality, retention, redaction, or forward-remediation policy
  changes or becomes unspecified.

Until a separate Phase B authorization after all gates, this document is the
only H-06 Phase A output. Its approved decisions are Phase A design authority,
not implementation authority.
