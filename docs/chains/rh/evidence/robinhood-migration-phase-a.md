# Track 7 H-05 Phase A: Robinhood Migration Discovery and Plan Boundary

## Status and authority boundary

This is the documentation-only H-05 Phase A audit. It creates no migration
namespace, migration file, history, manifest, configuration, test, source code,
deployment artifact, address, parameter, account, role, transaction, or
activation decision. It does not authorize H-05 Phase B.

The proposed Robinhood namespace remains absent. Every reservation below
reconciles an identifier already present in the controlling specification; it
does not publish that identifier as an executable migration. A reservation is
not a migration, and an `assertion`, `omitted`, `blocked`, `deferred`,
`rejected`, or `tooling_only` disposition is not an executable placeholder.

The following were facts at sealed baseline
`c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` unless explicitly described as a
read-only observation:

- H-03 R5 is unapproved and non-controlling.
- S5 Stage B is uncommitted and non-controlling.
- Track 8 M1 Phase B is unauthorized.
- H-04 parameter/default implementation has not begun.
- No Base migration or history is Robinhood authority.
- No live endpoint, credential, account, signer, deployment, verification
  submission, or external write was accessed.

The mutable H-03 and S5 worktree statuses were read-only, non-controlling
observations at the seal; they are not durable claims about later status. Any
movement in H-03, H-04, S5, Track 8, H-01, H-05, H-06, or `rh` after the
sealed baseline requires explicit reconciliation before Phase B can be
authorized.

## Baseline and isolation seal

| Item | Exact value |
| --- | --- |
| Integration repository | `/Users/wigglez/dev/ripe-protocol` |
| Integration branch | `rh` |
| Local `rh` before work | `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` |
| Cached `origin/rh` before work | `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` |
| Live `origin/rh` before work | `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` |
| Baseline tree | `b2c2358f565e27ad6a5c787a9a0d1396af513076` |
| Integration status before work | Clean |
| Phase A branch | `rh-track-7-h5-migration-discovery-phase-a` |
| Isolated worktree | `/Users/wigglez/dev/ripe-protocol-track-7-h5-migration-discovery-phase-a` |
| Isolated worktree starting commit | `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` |
| Isolated worktree starting tree | `b2c2358f565e27ad6a5c787a9a0d1396af513076` |
| Isolated worktree starting status | Clean |

The live remote check used `git ls-remote origin refs/heads/rh` before the
branch and worktree were created. No fetch, pull, merge, rebase, push, or
integration-branch edit occurred.

## OD-01 through OD-12 approval provenance

The owner directly approved OD-01 through OD-12 exactly as presented in this
evidence at SHA-256
`a4dced33f48aa71246a5fa2a1018d12eb0b7b4b4c821838f7f52957fe09b8315`.
This section and the checked boxes below record that approval; they do not
retroactively alter the approved decision text.

| Approval item | Exact provenance or effect |
| --- | --- |
| Approval authority | Direct owner instruction in the H-05 task |
| Approved evidence bytes | SHA-256 `a4dced33f48aa71246a5fa2a1018d12eb0b7b4b4c821838f7f52957fe09b8315`, 994 lines |
| Approved decisions | OD-01 through OD-12 exactly as presented in those bytes |
| OD-01 through OD-12 approval recorded | `2026-07-26T21:52:37Z` |
| Current-state reconciliation observed | `2026-07-26T23:06:03Z` |
| Approval effect | Closes the Phase A owner-decision packet only |
| Explicit exclusions | No Phase B, implementation, dependency change, namespace, migration skeleton, history, manifest, execution, retry, transaction, filesystem write, RPC/environment access, signing, deployment, or production action |
| Next gate | Independent exact-hash review of this provenance revision; only after that review may Phase A be committed, pushed, and integrated |
| Later Phase B | Requires a separate, baseline-specific, file-exact owner authorization |

### Current-state reconciliation

Controlling authority is the committed `rh` state. The other worktrees below
were inspected read-only for drift and collision awareness. Their modified,
untracked, or unintegrated contents were not copied, interpreted as approval,
or imported as H-05 plan inputs.

The S5 recreation, Track 8 M1, H-01 implementation, and H-06 rows are
non-controlling observations captured once at
`2026-07-26T23:06:03Z`. Later movement does not change the durable blocker
conclusions below; it requires a fresh observation before any separately
authorized Phase B.

| Slice | Reconciled state | Authority effect | Blocker effect |
| --- | --- | --- | --- |
| `rh` | Local `rh`, cached `origin/rh`, and live `origin/rh` are `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`; tree `d0a6048d902a035bf69158359dc80e9786792f38`; integration worktree clean; merge commit `8e4a965f034dc3d11b60fbb674ebbb4095b57d98` integrates the H-03 R6 branch | Current controlling integration state advances from the sealed H-05 analysis baseline only through the two H-03 documentation paths; the sealed input ledger remains historical | Integrated H-03 authority is controlling; no non-H-03 blocker is cleared |
| H-03 | Final corrected R6 is feature commit `d65e4dbd6ab832cc65265b9bda443cd8031b20e4`; brief SHA-256 `f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`; evidence SHA-256 `ed81dad7aaad41150ee49d20134916c9660e283ac77f85a2b0e5fe757ab2036c`; local, tracking, and live feature refs agree; its worktree is clean; complete-file independent review and fresh owner approval preceded commit, push, and integration through `8e4a965f034dc3d11b60fbb674ebbb4095b57d98` | The integrated R6 documents are controlling H-03 authority; the R6 evidence records that exact-lock validation has not occurred, and neither document authorizes H-03 or H-05 Phase B | `B-H03-R5-UNAPPROVED` remains sealed-baseline historical code for rejected and superseded R5; the H-03 approval/integration dependency is satisfied, but exact-lock validation remains open and no downstream blocker or H-05 Phase B authority is cleared |
| H-04 / S6 | Brief commit `d7809b82f0e2adc660b1e40fe0e4e28d6056b35a` is an ancestor of `rh`; its worktree is clean; the integrated brief still authorizes neither H-04 Phase A nor Phase B implementation | Integrated documentation is controlling; no implementation input exists | `B-H04-NOT-STARTED` remains current |
| S5 | At the observation timestamp, the recreation worktree is clean at local commit `ed10d4d13fb22c2d00ad2dc06b4faece1e2629f3`, is not integrated into `rh`, and tracks remote commit `444b3c91711ab79fc0fa2c36063dd11701481f51` at `+13/-0` | The clean but unintegrated and unpublished-ahead recreation branch is a non-controlling observation and supplies no H-05 input | `B-S5-STAGE-B-NONCONTROLLING` remains current |
| Track 8 | At the observation timestamp, the M1 branch and remote agree at published, unintegrated commit `1805aabb9bcaf03ca411a75abb35743a7a4f266e`; one modified evidence file is the bounded post-commit correction under separate review | The published commit and mutable correction are non-controlling observations and supply no H-05 execution input | `B-T8-M1-PHASE-B-UNAUTHORIZED` remains current |
| H-01 | The implementation branch originated at prior `rh` tip `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` and, at the observation timestamp, is at unintegrated local merge commit `9aedbbbf13f8f60e0bd816d6493e310cacbfbbda` with parents `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d` and current `rh` `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`; its worktree has five modified dependency/evidence/test paths and no upstream | Integrated H-01 evidence remains controlling; the local merge and mutable implementation bytes are non-controlling observations | No H-05 blocker ID changes; any later H-01 integration requires fresh baseline and validation reconciliation |
| H-06 | At the observation timestamp, the Phase A worktree remains based at sealed baseline and prior `rh` tip `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d`, not current `rh` `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`, with one untracked evidence file; no H-06 implementation or Robinhood history exists | Mutable H-06 analysis is a non-controlling observation and is not H-05 authority | `B-H06-HISTORIES-ABSENT` remains current |
| H-05 namespace | `migrations/robinhood/` and both profile-specific Robinhood history roots remain absent | Approval records a future design only and creates no namespace | `B-H05-SOURCE-ABSENT` remains current |

The exact sorted six-blocker set remains unchanged for sealed-baseline reports.
R5 remains rejected and superseded, and `B-H03-R5-UNAPPROVED` is historical
baseline code rather than current shorthand for the H-03 gate. Corrected R6
feature commit `d65e4dbd6ab832cc65265b9bda443cd8031b20e4`, brief SHA-256
`f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`,
and evidence SHA-256
`ed81dad7aaad41150ee49d20134916c9660e283ac77f85a2b0e5fe757ab2036c`
received complete-file independent review and fresh owner approval, were
published, and are integrated into controlling `rh` by merge commit
`8e4a965f034dc3d11b60fbb674ebbb4095b57d98`. That closes only the H-03
approval/integration dependency. H-03 exact-lock validation and Phase B remain
open. The other five sealed-baseline blocker descriptions remain current, and
none of H-04, S5, Track 8, H-06, H-08, or H-09 is cleared or made H-05
authority. S5 recreation, H-01 implementation, Track 8 M1, and H-06 must be
reconciled again against the then-current integrated baseline before any
separate Phase B authorization.

The non-controlling temporary audit aids were rehashed during this correction:
`/private/tmp/rh-h05-approved-a4dced33.md` is
`a4dced33f48aa71246a5fa2a1018d12eb0b7b4b4c821838f7f52957fe09b8315`;
`/private/tmp/rh-h05-before-h03-correction-e90.md` is
`e90a584d758595c5084f6db30d871e7349df2ffa13cb77641b1f784163038c9d`;
and `/private/tmp/rh-h05-frozen-b0f3b2c5.md` is
`b0f3b2c52ac7e7fcd09259f935550aa5d8d94edced468319a3412d09e379a355`.
Exact no-index comparisons reproduce `a4dced33` to `e90a584d` as 87
insertions and 25 deletions, `e90a584d` to `b0f3b2c5` as 20 insertions and 12
deletions, and `b0f3b2c5` to starting candidate `0643eb8c` as 24 insertions
and 20 deletions. These temporary snapshots are audit aids, not authority or
repository artifacts; the eventual final committed H-05 evidence is the
durable authority.

## Complete input ledger

The following required inputs were read completely at the sealed baseline.
Hashes are SHA-256 over the exact committed bytes.

| Input | SHA-256 | Use |
| --- | --- | --- |
| [Track 7 deployment-support brief](../track-7-robinhood-deployment-support.md) | `d84e59bc79caf555fbb51e61fd78840f40be0c08f69be73cf1706da63e95e72b` | Phase boundaries and workstream ownership |
| [Deployment-support specification](../robinhood-deployment-support-specification.md) | `1e3fc931ecab674e3ec61640f5c649458d1d6793eecb30465614455090312906` | Namespace, reservations, plan semantics, H-05 ceiling |
| [Deployment validation plan](../robinhood-deployment-validation-plan.md) | `5ffbcfc14cb33e9a5cdc5f2c300cf3d1f9bae90fd90e14d04a408cbe274a94fb` | Tests, negative cases, staged validation |
| [H-02 profiles and CLI brief](../track-7-h2-network-profiles-cli.md) | `f37597f37d6cf785f50bac0954709e2f60dde7ab836ed2c699cab45e5d105b59` | Profile, identity, environment, and repository boundary |
| [H-03 blueprint and omissions brief](../track-7-h3-robinhood-blueprint-omissions.md) | `84055f1c1ad3505b38250bf2d2a4851fae8d3358642237ef37da76e59ab5ba4b` | Symbolic graph and registry-order boundary only |
| [H-04 defaults and parameters brief](../track-6-s6-track-7-h4-defaults-parameters.md) | `2d9a1e0777751265b4aacc1c65434349e19c7c91f2a1d796bf9ff0f4bb349010` | Typed-value ownership and current stop state |
| [Track 8 M0 owner packet](../track-8-m0-owner-decision-packet.md) | `9fc44e47ae98bfe8e99c6554580215150461f17182ec92094588b7e650186496` | Product boundary; M1 remains unauthorized |
| [Track 8 M1 exact-receipt brief](../track-8-m1-exact-receipt.md) | `34749b58c6bd3b0452cb2d73987ce86aa5ff7269a86429c466bd7b1cdae64270` | Unimplemented containment input and S5 coordination |
| [H-02 implementation evidence](network-profile-cli-implementation.md) | `79cf2f7e5c362b8880f2c460abac946126bf2f329425a82e3c8f5bd4da9a8de7` | Integrated call order and deferred H-05/H-06 defects |
| [Network profile registry](../../../../config/network_profiles.py) | `9c19d237eaa049a9d521fc3ab8ef868e6ee35ab6ba48c45e61180fa2daf8c42a` | Canonical profile and repository authority |
| [Migration CLI](../../../../scripts/migrate.py) | `6401e3fe35f29981378bb187a4070b1b0a75e6f7105204269e65aeef4aa6a12c` | Current selection and runner construction |
| [Migration execution object](../../../../scripts/utils/migration.py) | `c0bc3ff369d5664af3d96585c7870b8be723b54930664b5f1ce8870f8ace53e3` | Positional resume and write behavior |
| [Migration runner](../../../../scripts/utils/migration_runner.py) | `d38b8c79e7ced58cddd8c9654654d240d076574879ed4826eb80b25284a3c350` | Discovery, ordering, ranges, and latest-history scan |
| [Migration helpers](../../../../scripts/utils/migration_helpers.py) | `559c7648f871e6b71b7d13f306290fee7c0d3fbe6d13182996964ba5b79465db` | Retry and transaction-result behavior |

Two adjacent committed implementations were also required to reconstruct the
actual write and blueprint coupling:

| Input | SHA-256 | Use |
| --- | --- | --- |
| [JSON writer](../../../../scripts/utils/json_file.py) | `51658b8bea8af5680f069aaefccb7d492ca5d53a006dc96bf1b6955fed102bb2` | Direct, non-atomic history writes |
| [Deploy arguments](../../../../scripts/utils/deploy_args.py) | `3452d85cfa6cb7decb73a6f1812d99889f14bcae34ff47fc4320126c19201b22` | Unconditional legacy blueprint construction |

Every committed Base migration and history JSON was enumerated and parsed from
[the Base migration tree](../../../../migrations/base-mainnet/) and
[the Base history tree](../../../../migration_history/base-mainnet/v1/). Each
inventory digest was reproduced with this exact algorithm:

1. Enumerate only non-symlink regular files directly under the applicable root:
   top-level `*.py` for the Base migration inventory and top-level `*.json` for
   the Base history inventory; do not recurse.
2. Normalize each name to a repository-relative POSIX path.
3. Sort bytewise/ordinally by that normalized path, independent of locale.
4. Produce one UTF-8 line per file in this exact form:
   `<sha256-hex><two ASCII spaces><repo-relative POSIX path>\n`.
5. Include the terminal newline and SHA-256 the complete resulting byte
   sequence.

This is equivalent to hashing sorted, normalized `shasum -a 256` output. An
independent implementation of that algorithm reproduced both values:

| Inventory | Count | Aggregate SHA-256 |
| --- | ---: | --- |
| Base migration Python files | 62 | `583ecb4317ffae58c512d006840cea7ac63a5c7886e582de881fe764e73f094c` |
| Base history JSON files | 58 | `79267f031649ad08e314dc9f63645d4d09172120a1ab728161ea833ed2526a18` |

The relevant committed tests were read completely:

- [network-profile tests](../../../../tests/deployment/test_network_profiles.py),
  SHA-256
  `9178b2a13c7c6a6102c21d592d609ccd2ab1dea099450397f17ca9ddd81dd7c6`;
- [secret-boundary tests](../../../../tests/deployment/test_secret_handling.py),
  SHA-256
  `ac27dcb31f4c17459cb45847ec904237bf790225b53184d3d2e2e4e95cdee2f3`;
  and
- [Base profile regression tests](../../../../tests/deployment/test_base_profile_regression.py),
  SHA-256
  `6da51a700e7a8a914ee541b594fa4bb4cb45df6b2a62842695898f2e467f9ecb`.

The active H-03, S5, S5 recreation, and Track 8 M1 worktrees were inspected
read-only for path overlap and status at the seal. H-03 then had only mutable
documentation changes; the S5 recreation then had mutable Ledger, ABI, and test
changes; Track 8 M1 then had its own evidence path. None touched the H-05
implementation ceiling proposed below. These are non-controlling observations,
not current-status claims. Their mutable contents were not used as plan inputs,
reservations, values, or approval evidence.

## Current behavior reconstructed from source

### Profile and repository selection

1. `scripts/migrate.py` requires `--profile`; `--chain` is only a deprecated
   spelling for the same Click option. It does not create a second identity.
   Choices are generated from the five canonical profile IDs
   ([CLI options](../../../../scripts/migrate.py#L243-L255)).
2. `get_profile()` case-folds the input, checks canonical IDs, then checks
   `PROFILE_ALIASES`. The committed alias tuple is empty
   ([registry lookup](../../../../config/network_profiles.py#L466-L483)).
3. Registry validation rejects duplicate profile IDs, duplicate chain IDs,
   aliased history paths, absolute paths, and `..` path components
   ([registry validation](../../../../config/network_profiles.py#L485-L684)).
4. The Robinhood profiles share the literal source path
   `migrations/robinhood` and have distinct literal history paths. All three
   paths are `PROPOSED`, both blueprint IDs are `None`, and repository,
   migration-fork, and migration-live operations are blocked
   ([Robinhood profiles](../../../../config/network_profiles.py#L408-L464)).
5. Shared-source validation currently permits that exact two-profile sharing
   only while both migration states are `PROPOSED`. Changing both states to
   `EXISTING` without changing the validator would make the registry invalid
   ([shared-source rule](../../../../config/network_profiles.py#L755-L763)).
6. `repository_paths()` requires a supported repository operation, validates
   identity when the operation requires it, rejects any `PROPOSED` path, checks
   both directories with `is_dir()`, and returns the profile-owned pair
   ([path resolver](../../../../config/network_profiles.py#L1067-L1111)).
   It does not resolve symlinks, prove Git ownership, or prove that the returned
   pair belongs to one immutable plan.

### CLI order and environment boundary

The committed migration CLI executes this order
([CLI callback](../../../../scripts/migrate.py#L302-L395)):

```text
canonical profile
  -> operation selection
  -> require operation
  -> reject unapproved account backends
  -> require history suffix and nonempty blueprint
  -> validate fork policy
  -> resolve exactly one RPC reference
  -> read and compare chain ID
  -> load account
  -> resolve source/history paths
  -> construct legacy blueprint and runner
  -> enter fork
  -> execute and write history
```

For either Robinhood profile today, `require_operation()` fails before static
blueprint checks, environment access, chain reading, account access, path
resolution, runner creation, or filesystem writes. Existing tests prove a
blocked Robinhood RPC operation reads no environment value and a chain mismatch
prevents account/history access
([secret tests](../../../../tests/deployment/test_secret_handling.py#L204-L225),
[profile tests](../../../../tests/deployment/test_network_profiles.py#L397-L460)).

Runtime chain-ID validation necessarily reads the selected endpoint after
profile and operation validation; no accurate design can claim chain identity
is checked before obtaining that endpoint. The actual safe claim is:

- canonical profile and operation validation occur before all environment
  access;
- only the selected profile's RPC reference may then be read;
- exact runtime chain-ID equality occurs before account, repository, import,
  runner, or write access; and
- deterministic dry-plan mode must require no RPC and use only the statically
  validated expected chain ID.

The current CLI has no dry-plan mode. Its only supported repository migration
route is Base-mainnet fork exploration. That route loads an account before
repository paths and writes directly to the committed Base history namespace
([runner construction and warning](../../../../scripts/migrate.py#L344-L395)).

### Discovery and ordering

`MigrationRunner._filtered_migration_filenames()` currently:

1. calls `os.listdir()` on an arbitrary string directory;
2. accepts any filename matching `(\d+).*\.py`;
3. silently ignores every nonmatching entry;
4. extracts the full leading digit run as the timestamp;
5. sorts only on `int(timestamp)`;
6. preserves nondeterministic filesystem enumeration order for equal numeric
   IDs;
7. accepts duplicate IDs, semantic duplicates, variable widths, unexpected
   gaps, untracked files, symlinks, and empty results;
8. converts range strings to integers inside the loop;
9. stops after the first value greater than the end bound; and
10. returns filename, timestamp, and previous discovered timestamp
    ([discovery](../../../../scripts/utils/migration_runner.py#L93-L134)).

There is no canonical filename grammar, reservation ledger, profile binding,
source hash, commit check, tree-clean check, Base deny rule, or assertion that a
requested start/end ID exists. A reversed or nonmatching range can therefore
produce an empty successful run.

`_migrations()` imports each selected file dynamically under the same module
name and then yields `module.migrate`
([dynamic import](../../../../scripts/utils/migration_runner.py#L70-L91)).
Top-level module code executes before the runner can prove a plan. The
`previous_timestamp` value is passed into `Migration` but is never used to
select a previous manifest.

### History selection and resume

Automatic resume is entered only when `start_timestamp is None`. The CLI
always supplies its string default `"0"`, so ordinary CLI use explicitly
selects the full source sequence rather than automatic resume
([CLI default](../../../../scripts/migrate.py#L38-L49),
[resume branch](../../../../scripts/utils/migration_runner.py#L70-L86)).

When automatic resume is called directly, `_latest_manifest_timestamp()`:

- creates the history directory as a discovery side effect;
- accepts every `*-manifest.json` stem, including `current`;
- converts the selected stems to integers; and
- chooses the greatest numeric value without validating source, profile,
  chain, completeness, or hash linkage
  ([latest scan](../../../../scripts/utils/migration_runner.py#L136-L154)).

The canonical `current-manifest.json` therefore makes the intended numeric
scan capable of raising during integer conversion. If the scan did select a
numeric record, `_migrations()` would pass `inclusive=False`, but
`_filtered_migration_filenames()` never reads that argument and always compares
with `>=`. Automatic resume therefore reselects and can re-execute the
migration whose ID equals the latest recorded manifest
([dead inclusive argument](../../../../scripts/utils/migration_runner.py#L70-L82),
[unchanged comparison](../../../../scripts/utils/migration_runner.py#L93-L134)).
It would not prove that all prior steps exist or agree with current source.

`Migration` always attempts to load `current-manifest.json`, not the manifest
identified by `previous_timestamp`. Any exception is swallowed and converted
to an empty previous manifest. Any retry-log exception is also swallowed
([constructor](../../../../scripts/utils/migration.py#L15-L40)). Resume then
uses the number of stored transaction strings as positional identity. It does
not bind a stored item to a semantic action, code hash, arguments, receipt,
profile, chain, or observed state
([positional execution](../../../../scripts/utils/migration.py#L140-L210)).

### Execution and persistence

Each deploy or include operation immediately rewrites both its timestamp
manifest and `current-manifest.json`; configuration-only calls are absent from
those manifests
([manifest append](../../../../scripts/utils/migration.py#L218-L232)).
The JSON helper creates parent directories and writes the target file directly,
without a temporary file, lock, digest, validation, or atomic rename
([JSON writer](../../../../scripts/utils/json_file.py#L16-L27)).

`execute_transaction()` retries every exception up to 20 times with a fixed
delay, returns `None` immediately when exception text contains `NoneType`, and
also falls through with `None` after retry exhaustion
([retry helper](../../../../scripts/utils/migration_helpers.py#L131-L160)).
For a non-deployment action, `Migration._run()` appends that `None`, prints a
confirmation message, saves the log, and can continue toward history writes
([caller behavior](../../../../scripts/utils/migration.py#L175-L210)). This is
an unresolved execution-hardening boundary outside H-05 Phase B. H-06 owns
manifest rejection, atomic history, and promotion, not submission or retry
semantics.

The retry-log writer converts every stored result with `str(tx)`. A failed
`None` result is therefore persisted as the truthy string `"None"`. On reload,
`_curr_transaction()` returns that string, `if not tx` is false, and the action
is skipped as if it had already executed
([log serialization](../../../../scripts/utils/migration.py#L237-L249),
[truthy current result](../../../../scripts/utils/migration.py#L140-L146),
[skip branch](../../../../scripts/utils/migration.py#L175-L210)). This is
separate from positional identity, broad retry fallthrough, and the absence of
structured receipts.

Completion deletes the positional log and writes no terminal completion marker
([completion](../../../../scripts/utils/migration.py#L108-L118)). A resumed
blueprint deployment can also reach `kwargs["name"]` even though the blueprint
wrapper did not supply that key. The helper therefore has no safe semantic
resume contract for blueprint steps.

## Complete Base audit and non-authority result

The 62 committed Base files all define `migrate()`. Static parsing found:

- 61 unique numeric IDs across 62 files;
- one duplicate numeric ID, `2025071506`, shared by
  [BondRoom](../../../../migrations/base-mainnet/2025071506_BondRoom.py) and
  [Teller](../../../../migrations/base-mainnet/2025071506_Teller.py);
- 26 files containing 65 Python `assert` statements, including registry-order
  checks that disappear under optimized Python;
- one migration that constructs its own provider from raw `migration.rpc()`
  ([Lootbox refresh](../../../../migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py#L6-L13));
- no migration that reads `os.environ` directly; and
- Base-specific blueprint data, literal addresses, pool/oracle/token choices,
  and historical topology throughout the tree.

The 58 Base history files all parse as JSON and contain only a top-level
`contracts` object:

- 57 are numeric step manifests and one is `current-manifest.json`;
- all 57 numeric history IDs have at least one source file;
- source IDs `2000`, `2003`, `2025071507`, and `2025102700` have no same-ID
  numeric manifest;
- entry shapes are either full contract records or address-only records;
- no history record contains profile ID, chain ID, migration ID, source hash,
  plan hash, prior-step hash, receipt status, or completion marker; and
- step histories mix cumulative and delta-like content.

The absence of four same-ID manifests is not proof of failure: those sources
can perform configuration-only actions that the writer does not represent. The
single history for the duplicate source ID cannot identify which source or
ordering it authorizes. Base history is evidence of legacy behavior, not a
template for Robinhood resume.

The existing Base Ledger migration deploys a Base Ledger and confirms its
historical registry position
([Base Ledger migration](../../../../migrations/base-mainnet/1004_Ledger.py)).
It is prohibited from any Robinhood source list, plan, history, source-hash
set, resume record, or compatibility fallback. Robinhood's future Ledger is a
fresh deployment whose source inputs remain blocked on S5 and H-04.

## Base-specific assumptions, aliases, couplings, and fail-open paths

| ID | Current behavior | Robinhood consequence |
| --- | --- | --- |
| CF-01 | Base-mainnet is the only profile with an existing migration source, existing history, and nonempty blueprint. | A generic-looking stack is operationally Base-only. |
| CF-02 | `--chain` aliases the option spelling, while `PROFILE_ALIASES` is empty. | No network alias may select another root; future aliases must collapse to a canonical ID before planning. |
| CF-03 | The registry allows Robinhood source sharing only in `PROPOSED` state. | H-05 cannot publish the shared root by changing path state alone. |
| CF-04 | `_require_static_assertions()` requires a nonempty blueprint. | Both Robinhood profiles remain blocked until reviewed H-03 output and an H-02 registry amendment exist. |
| CF-05 | `DeployArgs` unconditionally constructs the legacy multi-map `BluePrint`. | A profile-only dry plan cannot instantiate `DeployArgs`; H-04/H-03 values must remain outside discovery. |
| CF-06 | Repository paths are checked after account loading in the execution CLI. | Plan generation must be a separate no-account route. |
| CF-07 | `MigrationRunner` receives untyped source/history strings. | Any source can be paired with any history unless H-05 binds the canonical profile-owned pair. |
| CF-08 | Base fork exploration writes to committed Base history. | H-05 must preserve Base behavior tests but prohibit Robinhood use and defer isolated writes to H-06. |
| CF-09 | Discovery uses filesystem enumeration and numeric-prefix regex matching. | Equal IDs are nondeterministic; malformed and extra files are ignored. |
| CF-10 | Duplicate numeric and semantic IDs are accepted. | One history ID cannot prove which code ran. |
| CF-11 | Gaps, missing expected IDs, unknown start/end IDs, and empty plans are accepted. | Omitted or blocked steps can disappear without evidence. |
| CF-12 | Discovery accepts untracked files, symlinks, and changed committed files. | Local mutable code can enter execution without changing a recorded identity. |
| CF-13 | Dynamic import executes top-level code before a plan exists. | Discovery is not side-effect free. |
| CF-14 | Source hashes and clean-tree identity are absent. | A recorded history cannot detect changed migration bytes. |
| CF-15 | CLI `"0"` defaults bypass intended automatic resume. | Help and actual replay behavior diverge. |
| CF-16 | Latest-history discovery creates a directory. | A read operation mutates the selected namespace. |
| CF-17 | The latest-history regex includes `current`. | Canonical history can crash automatic resume. |
| CF-18 | Latest numeric history is treated as progress without continuity checks. | Missing, stale, partial, or foreign records can advance resume. |
| CF-19 | Current-manifest and log parse failures become empty state. | Corruption fails open. |
| CF-20 | Resume identity is transaction position. | A source edit with the same call count can skip different actions. |
| CF-21 | The previous timestamp is not used to select history. | Starting in the middle still loads mutable `current`. |
| CF-22 | Step and current manifests are rewritten mid-step. | Partial execution can appear canonical. |
| CF-23 | Configuration actions are not in manifests. | Roles, registrations, parameters, and assertions are not evidenced. |
| CF-24 | Base step histories mix cumulative and delta forms. | Presence and completeness cannot be inferred from record size. |
| CF-25 | Four Base source IDs have no numeric history. | Missing history is ambiguous, not an implicit skip rule. |
| CF-26 | Broad retry can return `None`; the caller can call it confirmed. | Failed state changes can progress toward history mutation. |
| CF-27 | Retry logs contain string positions, not receipts or semantic IDs. | Reconciliation after ambiguity is impossible. |
| CF-28 | Completion deletes the log and adds no completion marker. | History cannot prove terminal success. |
| CF-29 | Python `assert` enforces many Base registry outcomes. | Optimized execution can remove correctness checks. |
| CF-30 | One Base migration creates a raw provider internally. | A copied Base file can bypass the profile boundary and secret-safe planner. |
| CF-31 | Global Vyper discovery keys files by stem without collision rejection. | Artifact selection can overwrite a same-name source before deployment. |
| CF-32 | No rule rejects a Base path or Base blob from a Robinhood runner. | A path mistake can make Base code executable on Robinhood. |
| CF-33 | `_filtered_migration_filenames()` accepts `inclusive=False` but never uses it; comparison remains `>=`. | Automatic resume silently reselects and can re-execute the latest recorded ID. |
| CF-34 | Retry logs serialize failed `None` results as the truthy string `"None"`. | Reloaded retry state can skip the failed action as if it had already executed. |

These 34 findings cover the current source/history couplings and all observed
fail-open routes relevant to H-05. H-06 remains responsible for the new history
schema, serialization, atomic writes, and current-index promotion. H-05 Phase B
must perform no execution. Exhausted retry, ambiguous `None`, false-success,
and truthy `"None"` retry-log behavior remain hard blockers for a later
file-exact execution-hardening authorization. H-06 may reject an ambiguous
typed result if one is presented, but it does not own transaction submission or
retry semantics.

## Proposed namespace and canonical profile model

The controlling namespace direction is retained exactly
([namespace specification](../robinhood-deployment-support-specification.md#L1144-L1165)):

| Canonical profile | Expected chain ID | Source root | History root |
| --- | ---: | --- | --- |
| `robinhood-testnet` | `46630` | `migrations/robinhood/` | `migration_history/robinhood-testnet/v1/` |
| `robinhood-mainnet` | `4663` | `migrations/robinhood/` | `migration_history/robinhood-mainnet/v1/` |

The source root is shared byte-for-byte. Histories never share a path, inode,
symlink target, current index, lock, staging path, or resume chain. A
profile-qualified plan hash differs between testnet and mainnet even when the
source digest and ordered semantic steps are identical.

No implicit fallback is allowed:

- missing Robinhood source does not fall back to Base;
- missing profile history does not create or select another history;
- a marketing alias, legacy option spelling, environment suffix, or blueprint
  label cannot alter a root;
- a source root cannot be inferred from the chain ID;
- a history root cannot be supplied as a free-form environment string; and
- `v1` is part of the profile-owned path, not an operator-selected namespace.

### Exact H-02 selection proof and required amendment

The committed registry already proves the literal source/history mapping and
history non-aliasing. It also proves blocked operations access no environment
([H-02 call-order evidence](network-profile-cli-implementation.md#L618-L669)).
It does not yet support H-05 publication:

1. shared Robinhood source is valid only while `PROPOSED`;
2. repository and migration operations are blocked;
3. both Robinhood blueprint IDs are `None`; and
4. the repository resolver rejects proposed paths.

Future H-05 therefore requires a file-exact amendment to
`config/network_profiles.py`. The minimum design is a distinct
`MIGRATION_PLAN` operation:

- supported for canonical Robinhood profiles without RPC, runtime identity,
  account, verifier, or write capability;
- authorized to read only static validated repository metadata while roots
  remain proposed;
- returns a deterministic blocked report while the namespace or any controlling
  input is absent;
- never calls `resolve_rpc_reference()`, `verify_chain_identity()`,
  `get_account()`, `repository_paths()` in write-capable mode, or
  `MigrationRunner.run()`; and
- cannot enable `MIGRATION_FORK` or `MIGRATION_LIVE`.

Adding an enum member is a total-policy change: `_operations()` builds a policy
for every enum member, so the derived policy tuple for each of the five
profiles receives an explicit outcome
([operation enum](../../../../config/network_profiles.py#L29-L37),
[policy totality](../../../../config/network_profiles.py#L238-L249),
[profile policies](../../../../config/network_profiles.py#L264-L357)). The
three unsupported profiles may inherit `_operations()`' default; their literal
profile blocks need not all be edited. The proposed outcomes are:

| Profile | Proposed `MIGRATION_PLAN` outcome | Required invariant |
| --- | --- | --- |
| `local` | `unsupported` | No new repository or runtime capability |
| `base-mainnet` | `unsupported` | Existing Base read/fork/live semantics unchanged |
| `base-sepolia` | `unsupported` | Existing console-only support unchanged |
| `robinhood-testnet` | `supported` | Static blocked planning only; no environment, RPC, identity, account, or write |
| `robinhood-mainnet` | `supported` | Static blocked planning only; no environment, RPC, identity, account, or write |

`config/network_profiles.py` is part of the sealed H-02 evidence surface. Any
byte change reopens exact H-02 evidence reconciliation and requires H-02-owner
and security review. Phase B must prove every non-Robinhood operation outcome
and all existing Base/local behavior unchanged except for the explicit,
unsupported `MIGRATION_PLAN` policy outcome.

Later promotion from `PROPOSED` to `EXISTING` must amend the shared-source
validator to allow exactly the two canonical Robinhood profiles in the same
state and must receive separate file-exact authorization. That promotion is not
part of the Phase B ceiling in this record.

## Reservation and blocker matrix

The canonical reservation sequence contains exactly 18 entries: eight
pre-deployment dispositions from `0010` through `0080`, followed by ten
clean-deployment graph reservations from `0100` through `1000`. This is a
reconciliation of the controlling table
([reservation source](../robinhood-deployment-support-specification.md#L1167-L1208)),
not migration publication. Blocker statuses in this matrix are sealed-baseline
facts and require reconciliation after any controlling workstream movement.

| ID | Phase A disposition | Executable now or in proposed Phase B | Controlling blocker or required input | Accountable owner boundary |
| --- | --- | --- | --- | --- |
| `0010` | `assertion` — retained S3 artifact | No | Reviewed integrated S3 artifact plus future H-04 hash binding | Track 6 S3, H-04, H-05 |
| `0020` | `omitted` — proof that S4 remains no-change | No | S4 no-change must remain controlling; H-08/H-09 negative proof | Track 6 S4, H-05, H-08, H-09 |
| `0030` | `assertion` — S5 artifact/source-input/constructor evidence before a fresh Ledger | No | Integrated reviewed S5 source, ABI, constructor input, and security proof; Stage B was uncommitted at the seal | S5, security, H-04, H-05 |
| `0040` | `assertion` — H-04 typed defaults/parameter artifact | No | H-04 Phase A and Phase B have not begun; no approved generated hashes | H-04/S6, parameter owners, H-05 |
| `0050` | `assertion` — timelock and registry lifecycle | No | Integrated S7 requirements and approved bounds | Track 6 S7, protocol, H-05 |
| `0060` | `assertion` — lifecycle and capacity | No | Integrated S8 lifecycle/capacity decisions | Track 6 S8, risk, H-05 |
| `0070` | `assertion` — disabled and omitted integrations | No | Approved H-03 artifact plus S9 negative allowlist; H-03 R5 is unapproved | H-03, S9, H-08, H-09 |
| `0080` | `tooling_only` — CAD report/tooling evidence | Never onchain | Integrated S10 tooling correction and raw/formatted/runtime proof | S10 tooling, H-05 |
| `0100` | `blocked` — future initial tokens and HQ graph step | No | All `0010`-`0080` dispositions, approved H-03 topology, H-04 manifest, exact artifacts | H-03, H-04, protocol, H-05 |
| `0200` | `blocked` — future data/config registries, including one fresh Robinhood Ledger | No | Final `0100`; integrated S5 and H-04 inputs; no Base state or Base Ledger migration | S5, H-04, protocol, H-05 |
| `0300` | `blocked` — future Switchboard graph | No | Final `0200`; approved H-03 order and H-04 timing inputs | H-03, H-04, protocol, H-05 |
| `0400` | `blocked` — future approved price-source graph | No | Final `0300`; approved oracle identities, feed facts, H-03 slots, H-04 inputs | Oracle, security, H-03, H-04, H-05 |
| `0500` | `blocked` — future vault and asset graph | No | Final `0400`; selected reviewed Track 8 artifact and lifecycle; M1 Phase B is unauthorized | Track 8, risk, H-03, H-04, H-05 |
| `0600` | `blocked` — future core departments and capability graph | No | Final `0500`; approved complete registry/capability plan and constructor inputs | H-03, H-04, Track 8, governance, H-05 |
| `0700` | `blocked` — future SavingsGreen disposition | No | Approved H-03 disposition and lifecycle tests; R5 is unapproved | Product, risk, H-03, H-09, H-05 |
| `0800` | `blocked` — future disabled PSM disposition or explicit omission | No | Track 4 posture, oracle/reserve facts if applicable, H-03/H-04 manifest; no activation | Track 4, oracle, risk, H-03, H-04, H-05 |
| `0900` | `blocked` — future capabilities, governance handoff, and authority-loss step | No | Every earlier step final; approved identities, policies, finality, H-06 evidence, H-08 checks | Governance, security, operations, H-06, H-08, H-05 |
| `1000` | `deferred` — CCIP pools and registration | No | Track 1 facts, supported toolchain/artifacts, remote identities, limits, external permissions | Track 1, H-12, security, H-05 |

Matrix count: 18 rows, 18 unique IDs, exact canonical order. None is eligible
for an executable file or live plan. In particular:

- `0010` remains the retained S3 assertion;
- `0020` remains `omitted` and records proof that S4 is no-change;
- `0030` cannot deploy or migrate a Ledger and only gates the later fresh
  `0200` Ledger;
- `0080` can never contain an onchain action; and
- no old reservation is evidence that a transaction is necessary.

The controlling specification uses the word `skipped`; the proposed report
schema normalizes that disposition to exactly `omitted`. `omitted` is a
non-executable disposition, is not accepted as a source-file alias, cannot be
reassigned after publication, and is distinct from `assertion`, `blocked`,
`deferred`, `rejected`, and `tooling_only`.

## Fail-closed discovery and planning contract

The future Robinhood planner must enforce all 24 rules before any migration
module import or execution:

| Rule | Required result |
| --- | --- |
| FD-01 canonical identity | Accept only a canonical profile object. Resolve any separately approved input alias once, retain only the canonical ID, and never use alias text in path selection. |
| FD-02 static, read-only plan operation | Validate profile and `MIGRATION_PLAN` capability before environment or filesystem access. All later filesystem access is read-only: no directory creation, lock, temporary/staging file, metadata update, or write. Plan mode never reads an RPC, account, signer, or secret and leaves repository bytes and paths unchanged. |
| FD-03 exact roots | Require the exact source and profile-specific history roots in this record. No caller override, suffix override, fallback, or inferred path. |
| FD-04 contained paths | Resolve under the repository root; reject escape, symlink, non-regular source file, shared history target, or source/history overlap. |
| FD-05 namespace ownership | Require every Robinhood source entry to originate under `migrations/robinhood/`. Reject every Base path, Base history path, Base source blob, or legacy blueprint fallback. |
| FD-06 committed source | For an executable plan, require every migration source to be tracked at the approved commit and byte-identical to its Git blob; reject dirty, untracked, staged-only, or changed source. |
| FD-07 canonical filename | Require one separately approved fixed-width ID plus one canonical semantic name. Reject any unmatched file instead of ignoring it. |
| FD-08 duplicate numeric ID | Reject two files or two ledger records with the same numeric ID before sorting or import. |
| FD-09 duplicate semantic ID | Reject repeated semantic identity even when numeric IDs differ. |
| FD-10 complete reservation ledger | Require exactly one disposition for every expected reservation. Missing IDs, extra IDs, or implicit omissions fail. |
| FD-11 expected gaps only | Compare the observed sequence with the approved sequence, not arithmetic adjacency. Any undeclared gap, insertion, reuse, or out-of-order ID fails. |
| FD-12 non-executable dispositions | Normalize the specification's `skipped` disposition to exactly `omitted`; represent `assertion`, `omitted`, `blocked`, `deferred`, `rejected`, and `tooling_only` as distinct typed plan records, never aliases or executable Python skeletons. |
| FD-13 executable-placeholder rejection | Reject a migration whose body is empty, `pass`, a placeholder exception, a no-op scaffold, or executable despite a non-executable disposition. |
| FD-14 import-free discovery | Parse metadata and hash bytes without importing the module. Import is an execution-stage action after an approved immutable plan. |
| FD-15 source digest | Bind plan ID, file path, numeric ID, semantic ID, byte hash, approved commit, and tree to each executable source. |
| FD-16 immutable recorded source | If history already records an ID, require the identical source and semantic hash. A changed committed migration requires a new later ID. |
| FD-17 exact history schema | Reject malformed JSON, unknown schema, wrong profile/chain, missing prior hash, duplicate ID, partial record, temporary record, or stale current index. H-06 defines serialization and atomic promotion. |
| FD-18 source/history collision | Reject a history whose plan/source identity points to another profile, another source root, Base, or a different approved commit. |
| FD-19 resume agreement | Require identical plan hash, profile, chain, source digest, prior immutable step chain, and observed postconditions. Positional transaction logs are never resume authority. |
| FD-20 ambiguous state | Stop at the first incomplete, failed, ambiguous, or finality-pending semantic action. Do not broad-retry or advance current history. |
| FD-21 explicit range | Require requested start/end semantic IDs to exist, be ordered, and agree with history. Empty selection is an error unless the complete plan is already satisfied and proved. |
| FD-22 topology constraints | Encode H-03 source-hard-coded IDs separately from Base-precedent registration-order constraints; failure of either blocks the plan. |
| FD-23 no Base Ledger | Reject the Base Ledger migration by path, source identity, blob, or semantic action. The future `0200` record may reference only a fresh Robinhood deployment with approved S5 inputs. |
| FD-24 sensitive-data absence | Reject any plan serialization containing an RPC value, environment dump, private-key material, account secret, signature, raw provider payload, or undisclosed production identity. |

FD-10 reconciles “missing IDs” and “unexpected gaps” without treating every
unused decimal number as missing. The canonical sequence is the approved
reservation ledger. An unused reserved step survives as a typed non-executable
record and can never be silently reassigned after publication
([identifier rules](../robinhood-deployment-support-specification.md#L1167-L1183)).

## Deterministic dry-plan boundary

### Pure call order

Dry-plan generation must use this no-network order:

```text
parse canonical profile ID
  -> validate immutable registry and MIGRATION_PLAN policy
  -> read static expected chain ID and exact repository metadata
  -> verify repository baseline commit and clean tree
  -> discover and hash source without importing it
  -> read history only through the H-06 read interface
  -> reconcile reservations, blockers, topology, and resume
  -> canonicalize report
  -> calculate report SHA-256
  -> return blocked or plan-ready report
```

No environment mapping is passed to this path. The forbidden call set is
`resolve_rpc_reference`, runtime chain reader, `get_account`, `boa.fork`,
`MigrationRunner.run`, transaction execution, history save/promotion, verifier,
connector access, directory creation, lock or temporary/staging file creation,
and every filesystem write. A dry-plan run must leave repository contents,
paths, and Git status byte-for-byte unchanged.

### Canonical report

The proposed report encoding is RFC 8785 JSON Canonicalization Scheme (JCS);
it is an owner-approved Phase A design bound to the approval provenance above,
not an implemented format or Phase B authorization. The value model allows
only strings, integers, booleans, arrays, objects, and null. Floats, `NaN`, and
infinities are rejected rather than coerced. Every path value is a
repository-relative POSIX string. Report construction must:

1. validate the complete typed value model and reject unsupported values;
2. build the hash-input object with `report_sha256` completely absent, not
   present as null;
3. JCS-canonicalize that object to UTF-8 bytes with no terminal newline;
4. hash those exact bytes with SHA-256;
5. insert the lowercase hexadecimal digest as `report_sha256`; and
6. JCS-canonicalize the final object and append exactly one terminal LF.

Array order is fixed by semantic plan order. Timestamps, absolute or host paths,
usernames, process IDs, directory enumeration order, and exception text are
forbidden. Tests must distinguish an absent hash field from a null hash field
and prove identical bytes across processes and clean checkouts.

Required top-level fields are:

| Field | Rule |
| --- | --- |
| `schema` | Fixed reviewed schema identifier |
| `mode` | Exactly `dry-plan` |
| `status` | Phase B emits exactly `blocked`; `plan_ready` is reserved for a later authorization; never `success` |
| `profile_id` | Canonical profile ID |
| `expected_chain_id` | Static profile value; not an observed RPC claim |
| `source_root` | Exact repository-relative shared root |
| `history_root` | Exact repository-relative profile-owned root |
| `source_commit` and `source_tree` | Approved immutable identities |
| `source_digest` | Null while source is absent; otherwise digest of the ordered file records |
| `reservation_digest` | Digest of all 18 typed reservation records |
| `prior_history_digest` | Null only for a proved clean history; otherwise H-06 chain digest |
| `steps` | All 18 records in canonical order; disposition is exactly one of `assertion`, `omitted`, `blocked`, `deferred`, `rejected`, or `tooling_only`; specification `skipped` is normalized to `omitted` before report construction |
| `blockers` | Sorted unique blocker IDs with accountable owner IDs |
| `plan_hash` | Null while any required input is blocked; otherwise profile-qualified immutable plan hash |
| `report_sha256` | Deterministic report hash |

The report must not include an RPC field, environment-variable value, account,
signer, signature, credential, endpoint, provider payload, or concrete
production identity. Diagnostic errors use stable codes and source-relative
paths only.

At the sealed Phase A baseline both profile reports are deterministically
`blocked`, `plan_hash` is null, and the blocker set is exactly:

| Blocker ID | Sealed-baseline fact | Accountable owner IDs |
| --- | --- | --- |
| `B-H03-R5-UNAPPROVED` | H-03 R5 is unapproved and non-controlling | `OWN-H03` |
| `B-H04-NOT-STARTED` | H-04 parameter/default implementation has not begun | `OWN-H04` |
| `B-H05-SOURCE-ABSENT` | `migrations/robinhood/` is absent and proposed | `OWN-H05`, `OWN-H02` |
| `B-H06-HISTORIES-ABSENT` | Both profile-specific histories are absent and proposed | `OWN-H06`, `OWN-H05` |
| `B-S5-STAGE-B-NONCONTROLLING` | S5 Stage B is uncommitted and non-controlling | `OWN-S5` |
| `B-T8-M1-PHASE-B-UNAUTHORIZED` | Track 8 M1 Phase B is unauthorized | `OWN-T8` |

These are baseline-qualified facts, not permanent labels. Any later movement of
H-03, H-04, S5, Track 8, H-01, H-05, H-06, or `rh` requires reconciliation
and a new exact blocker set. A blocked report is evidence of refusal, not a
deployment plan.

The expected testnet/mainnet difference set is exactly:

| Field | Testnet | Mainnet |
| --- | --- | --- |
| `profile_id` | `robinhood-testnet` | `robinhood-mainnet` |
| `expected_chain_id` | `46630` | `4663` |
| `history_root` | `migration_history/robinhood-testnet/v1` | `migration_history/robinhood-mainnet/v1` |
| `plan_hash` | Null while blocked; profile-qualified once ready | Null while blocked; different profile-qualified value once ready |
| `report_sha256` | Profile-qualified report value | Different profile-qualified report value |

The three semantic profile fields are `profile_id`, `expected_chain_id`, and
`history_root`. Their different values also make `report_sha256` differ and,
once ready, make `plan_hash` differ. The source root, source digest,
reservation digest, semantic order, source hashes, and non-profile blockers
must be identical. Any other unexplained difference fails plan determinism.

## Smallest future H-05 Phase B ceiling

Phase B remains unauthorized. The smallest credible file ceiling is exactly
six files:

| Path | State | Permitted future responsibility |
| --- | --- | --- |
| `docs/chains/rh/evidence/robinhood-migration-phase-a.md` | Existing after Phase A | Record approved decisions, exact implementation hashes, tests, and Gate 1 provenance |
| `config/network_profiles.py` | Existing | Add only the static no-RPC plan capability and all-five-profile policy outcomes; no path-state or shared-source promotion |
| `scripts/migrate.py` | Existing | Add a no-account, no-RPC blocked dry-plan entry path that cannot construct `DeployArgs` or invoke execution |
| `scripts/utils/migration_runner.py` | Existing | Add deterministic import-free discovery, ordering, blocked plan model, resume reconciliation, and the H-05-side H-06 read protocol only on the new plan path; legacy discovery used by Base fork exploration remains behaviorally identical |
| `tests/deployment/test_migration_discovery.py` | Proposed | Discovery, namespace, ordering, reservation, collision, and Base-exclusion tests |
| `tests/deployment/test_execution_plan.py` | Proposed | Canonical blocked plan, H-06 read-protocol synthetic, blocker, resume, profile, and sensitive-data tests |

Phase B performs no transaction submission or execution and does not change
Base fork-exploration runtime semantics.

This ceiling intentionally excludes:

- `scripts/utils/migration.py`, `scripts/utils/migration_helpers.py`, and all
  transaction execution, retry, submission, and Base runtime semantics;
- `migrations/robinhood/` and every migration file or skeleton;
- both Robinhood history directories and all JSON;
- a reservation manifest or configuration file;
- H-03/H-04/S5/Track 8 source, test, evidence, ABI, or generated files;
- Base migration/history changes;
- H-06 schema/writer files;
- H-08 checker files;
- H-09 integration/fork fixtures;
- dependency, CI, verifier, account-backend, and deployment files; and
- any live command, artifact, or output.

`config/network_profiles.py` is a necessary addition to the older H-05 slice
list because the integrated H-02 validator rejects an `EXISTING` shared source
and exposes no no-RPC plan operation. OD-01 and OD-03 approve this future design
inside the six-file ceiling; they do not authorize its implementation. Without
separate Phase B authorization, work stops and must not build a parallel path
map inside `scripts/migrate.py`.

The six-file ceiling can implement and test a deterministic blocked planner
against disposable source/history fixtures. Publishing the real namespace,
changing any Robinhood path state to `EXISTING`, attaching a blueprint, enabling
fork/live migration, or creating an identifier-bearing file requires a later
separate file-exact authorization after H-03, H-04, S5, and Track 8 gates close.

This is an explicit narrowing of the older specification allowance for a
namespace and inert skeletons. Phase B publishes no namespace, skeleton,
migration ID, history, or manifest; the 18 reservations exist only as typed
report records built from disposable fixtures. OD-02 and OD-05 now approve that
narrowing and representation, bound to the exact approval-source SHA above;
they do not publish a namespace or authorize Phase B.

The H-05-side H-06 read protocol must live in
`scripts/utils/migration_runner.py`. Its only Phase B implementation double
lives inside `tests/deployment/test_execution_plan.py`; the real schema reader,
serialization, atomic write, and promotion implementation remain H-06-owned.
If that boundary cannot fit these two files, Phase B stops for a new
file-exact decision. No seventh, eighth, ninth, or other implementation file is
permitted.

Exhausted retry, false `None` success, truthy persisted `"None"`, ambiguous
submission, and transaction-result typing are deferred to a later file-exact
execution-hardening authorization with an explicitly assigned owner. H-06 may
consume a typed execution result, and its writer must reject that result if it
is ambiguous, but H-06 does not own transaction submission, retry, or result
classification.

## Required future tests

The two proposed H-05 test files must cover these eleven required groups. Existing
H-02 and Base tests are validation dependencies, not Phase B edit targets.

| Test group | Required cases and result | Primary file |
| --- | --- | --- |
| T-01 migration discovery | Exact grammar; unmatched files fatal; regular tracked file requirement; duplicate numeric/semantic ID failure; missing/extra reservation failure | `test_migration_discovery.py` |
| T-02 ordering | Stable canonical order independent of `os.listdir`; approved-sequence gap rules; range endpoints must exist; no empty-success range | `test_migration_discovery.py` |
| T-03 plan determinism | RFC 8785 sequence; hash input omits `report_sha256`; absent differs from null; floats/non-finite numbers rejected; repository-relative POSIX paths; two processes and clean checkouts produce identical bytes/hash; cross-profile differences limited to approved fields and derived hashes | `test_execution_plan.py` |
| T-04 profile separation | Shared source, distinct histories, wrong-profile history and symlink alias rejected; all five `MIGRATION_PLAN` outcomes exact; existing operations unchanged; blocked operation reads no environment | Both |
| T-05 resume reconciliation | Source/plan/profile/chain/prior-chain/state disagreement rejected; positional logs ignored; partial/stale current records block; H-06 protocol synthetic is defined only in this test file | `test_execution_plan.py` |
| T-06 Base regression | Existing Base profile/source/history unchanged; 62/58 inventory unchanged; legacy reader compatibility; no new Base write during tests | Existing Base regression plus both new files |
| T-07 rejected and omitted steps | Specification `skipped` normalizes only to `omitted`; `omitted` is distinct from `assertion`/`blocked`/`deferred`/`rejected`/`tooling_only`, cannot alias or execute; `0020` proves S4 no-change; `0080` never onchain | Both |
| T-08 no Base Ledger migration | Base Ledger path/blob/semantic action and any Base source/history pair rejected from either Robinhood plan; `0030` cannot deploy; `0200` is fresh-only and blocked | Both |
| T-09 no executable skeleton | Empty/pass/placeholder/non-executable-disposition Python file rejected; no identifier-bearing file needed for test fixtures outside temporary paths | `test_migration_discovery.py` |
| T-10 sensitive-data absence | Environment/RPC/account/signer/provider spies remain untouched; canonical report and every stable error omit sensitive values | `test_execution_plan.py` |
| T-11 sealed-baseline blocked reports | Both Robinhood profiles report `blocked`, `plan_hash` null, exact profile/history roots, the exact sorted six-blocker set and owner IDs above, and no sensitive or host-derived fields; pre/post bytes and `git status` are identical, with no new directory, lock, temporary, staging, or other path | `test_execution_plan.py` |

Additional mandatory cases from the validation plan include changed external
fact invalidation, constructor/source drift changing the plan, transaction
position not being resume identity, and cross-history writes failing
([negative matrix](../robinhood-deployment-validation-plan.md#L331-L369)).
Ambiguous submission, exhausted retry, `None`/`"None"` handling, and false
success remain mandatory for the later execution-hardening package; they are
not Phase B execution tests. In particular, the hash-pinned validation plan
places NEG-029,
`test_ambiguous_submission_requires_review`, in
`tests/deployment/test_execution_plan.py`
([NEG-029 schedule](../robinhood-deployment-validation-plan.md#L361-L361)).
Option C deliberately defers that named case and its placement to the later
file-exact execution-hardening authorization. This is an explicit scheduling
reconciliation with the validation plan, not an omitted Phase B requirement.

## Cross-workstream ownership and overlap

| Workstream | Supplies to H-05 | H-05 may do | H-05 must not do | Sealed-baseline blocker |
| --- | --- | --- | --- | --- |
| H-02 | Canonical profiles, chain IDs, repository metadata, environment/identity call order | Under a separately authorized Phase B, minimally extend static plan capability with all five profile outcomes explicit | Create parallel profiles, aliases, roots, environment fallback, or silently change the sealed evidence surface | Shared source cannot become existing; no plan operation |
| H-03 | Symbolic graph, omissions, source-hard-coded IDs, registration-order constraints | Consume an integrated approved artifact read-only | Approve R5, reclassify components, choose addresses, or edit blueprint | R5 unapproved and non-controlling |
| H-04 / S6 | Typed approved values and artifact hashes | Bind approved hashes into a later plan | Invent values, create `0040`, or begin H-04 | Phase A and implementation have not begun |
| S5 | Reviewed Ledger source, ABI, constructor/source input, Base exception proof | Gate `0030`; later allow fresh `0200` input | Copy uncommitted Stage B, migrate Base Ledger, or infer source input | Stage B uncommitted and non-controlling |
| Track 8 | Reviewed selected Stock containment and lifecycle artifact | Gate future `0500` and keep routes blocked | Treat M1 as authorized, select a vault/ID, or activate Stock paths | M1 Phase B unauthorized; complete selected artifact absent |
| H-06 | History schema, immutable step chain, atomic writes/current promotion | Define the read protocol in `migration_runner.py`, test a synthetic only in `test_execution_plan.py`, and refuse unverifiable history | Implement the real reader/schema/writer, write history, promote current, or own submission/retry | H-06 not implemented |
| H-08 | Read-only topology and deployment assertions | Emit plan expectations for later checker consumption | Claim deployed state, create checker, or weaken mismatch to warning | H-03/H-04 graph inputs unresolved |
| H-09 | Clean deployment, resume integration, negative graph, reproducibility | Supply unit-tested planner and synthetic resume contract | Create integration/fork fixtures or claim clean deployment | H-03 through H-08 prerequisites incomplete |
| Later execution hardening | Typed transaction outcome, exhausted-retry refusal, and false-success prevention | Document the need and stop before execution | Assign it to H-06 or change `migration.py`/`migration_helpers.py` in Phase B | Owner and file-exact authorization unassigned |

Integrated H-03 R6 commit
`d65e4dbd6ab832cc65265b9bda443cd8031b20e4`, at brief SHA-256
`f528cc474c5abdf84fec68dbb6c3ec9a2ae92e5ab8dc0c3d2703388da676cce5`,
preserves the source-hard-coded versus registration-order distinction; H-05
must preserve both without relabeling them
([integrated R6 classification](../track-7-h3-robinhood-blueprint-omissions.md#L278-L295)).
H-06 owns atomic evidence, while H-05 owns semantic ordering and refusal
([slice boundaries](../robinhood-deployment-support-specification.md#L1652-L1656)).
If an ambiguous typed result reaches an H-06 writer, H-06 must reject it; H-06
does not create that type or own submission/retry. All blocker descriptions in
this table are facts at the sealed baseline. Movement in H-01, H-03, H-04, S5,
Track 8, H-05, H-06, or `rh` requires fresh reconciliation.

## Blast-radius-ordered owner-decision packet

The owner approved every decision below exactly as presented in evidence
SHA-256
`a4dced33f48aa71246a5fa2a1018d12eb0b7b4b4c821838f7f52957fe09b8315`.
Checked boxes record that approval only; Phase B remains separately
unauthorized.

- [x] **OD-01 - Phase B authority and exact six-file ceiling.** Authorize or
  reject the exact ceiling above, including `config/network_profiles.py` and
  the explicit deferral of all execution-hardening to a later file-exact
  authorization with assigned ownership. No broader file is implied.
- [x] **OD-02 - No namespace or skeleton publication in Phase B.** Confirm that
  Phase B implements only a deterministic blocked planner against disposable
  fixtures, deliberately narrows the older specification allowance, and keeps
  real namespace/ID publication behind a later gate.
- [x] **OD-03 - H-02 plan operation.** Approve a distinct no-RPC,
  no-runtime-identity, no-account `MIGRATION_PLAN` capability rather than
  overloading inspection, repository read, fork, or live execution; approve
  the exact five-profile outcomes and require H-02-owner/security review plus
  sealed-evidence reconciliation.
- [x] **OD-04 - Shared-source promotion rule.** Approve the exact future rule
  that only the two canonical Robinhood profiles may share the source and only
  when both declare the same path state; defer actual promotion to a later
  authorization.
- [x] **OD-05 - Reservation representation.** Approve typed non-executable plan
  records that normalize specification `skipped` to exactly `omitted`, keep it
  distinct from `assertion`/`blocked`/`deferred`/`rejected`/`tooling_only`, prohibit
  aliases or reassignment, and prohibit Python skeletons for those records.
- [x] **OD-06 - Canonical sequence and gap rule.** Confirm that the expected
  sequence is the 18-record reservation ledger rather than arithmetic decimal
  adjacency, every record requires an explicit canonical disposition, and
  omitted is not interchangeable with blocked, deferred, rejected, assertion,
  or `tooling_only`.
- [x] **OD-07 - H-03 dependency.** Require approved, integrated H-03 R5 or a
  later reviewed H-03 artifact before any graph-bearing plan can become ready.
- [x] **OD-08 - H-04 and S5 dependency.** Require approved integrated H-04
  hashes and S5 source/constructor proof before `0040`, `0030`, or `0200` can
  become plan-ready.
- [x] **OD-09 - Track 8 dependency.** Require the complete reviewed selected
  Track 8 artifact and lifecycle gates before `0500`; M1 alone cannot clear it.
- [x] **OD-10 - H-06 history interface.** Approve H-05's read-only semantic
  resume protocol in `scripts/utils/migration_runner.py`, its Phase B synthetic
  only in `tests/deployment/test_execution_plan.py`, and the real implementation,
  serialization, atomic write, and promotion behavior as H-06-owned. H-06 does
  not own transaction retry or submission.
- [x] **OD-11 - Base compatibility policy.** Require the existing Base
  source/history bytes and profile paths to remain unchanged, while explicitly
  rejecting all Base paths and blobs from Robinhood plans and preserving Base
  fork-exploration discovery and runtime semantics behaviorally unchanged.
- [x] **OD-12 - Gate 1 and validation package.** Approve the independent review,
  RFC 8785 report/hash contract, sealed-baseline blocked outputs, H-02 evidence
  reconciliation, exact commands, two-checkout determinism proof, full serial
  suite, and rollback rules below before any implementation commit.

All 12 Phase A owner decisions are answered. Phase B remains prohibited until
the owner separately authorizes its exact baseline and six-file implementation
scope.

## Phase B stop conditions

Stop before or during Phase B if:

- the baseline, controlling specification, or exact ceiling changes;
- any additional file is needed;
- the `config/network_profiles.py` byte change lacks H-02 evidence
  reconciliation, H-02-owner review, or security review;
- the integrated H-03 commit, brief hash, or evidence hash is absent or
  different, H-03 exact-lock validation or Phase B is represented as complete
  when it is not, or S5 Stage B, Track 8 M1 Phase B, or H-04 status is
  represented as approved when it is not;
- H-01, H-03, H-04, S5, Track 8, H-05, H-06, or `rh` moves without exact
  blocker and baseline reconciliation;
- a real migration namespace, identifier-bearing file, skeleton, history, or
  manifest would be created;
- any old reservation is used to justify an executable action;
- Base migration/history behavior would change or Base content could enter a
  Robinhood plan;
- discovery imports code, ignores an entry, accepts a duplicate/gap, or depends
  on filesystem order;
- dry-plan mode touches an environment mapping, endpoint, account, signer,
  secret, fork, verifier, or external connector;
- dry-plan mode creates a directory, lock, temporary/staging file, metadata
  update, or any other filesystem mutation, or changes repository bytes, paths,
  or Git status;
- history cannot be reconciled without implementing H-06;
- a transaction, retry, submission, result-classification, `DeployArgs`, or
  Base runtime path becomes reachable or requires modification;
- a test requires a live network, dependency change, skip, xfail, or
  environment installation;
- a concrete production identity, value, authority assignment, deployment, or
  activation would be selected; or
- an independent reviewer cannot reproduce every reported hash and result.

## Gate 1 review discipline

After an explicitly authorized Phase B produces an unstaged implementation:

1. Freeze the exact baseline commit/tree, dirty-state record, six-file list,
   file SHA-256 values, and complete diff.
2. Have an independent deployment-tooling reviewer inspect every changed line,
   every new test, and the complete updated evidence.
3. Have the H-02 owner reconcile the sealed H-02 evidence surface and verify
   all five profile outcomes plus every pre-existing operation outcome.
4. Have an independent security reviewer inspect environment non-access,
   import-free discovery, path containment, source/history separation,
   filesystem immutability, sensitive-data absence, execution unreachability,
   and Base exclusion.
5. Have protocol and Track 6/8 reviewers verify reservation dispositions,
   especially `0010`, `0020`, `0030`, `0080`, fresh `0200`, and the absence of
   any Base Ledger migration.
6. Compare the implementation with approved H-03/H-04/S5/Track 8 inputs without
   copying mutable worktree conclusions.
7. Resolve every finding and rerun the entire validation package after the last
   byte change.
8. Record attributable Gate 1 approval against exact hashes. The implementation
   author cannot self-approve.
9. Stop after Gate 1 for a separate owner decision. Gate 1 does not authorize
   commit, push, merge, namespace publication, execution, or deployment.

Any implementation or evidence byte change after approval reopens Gate 1.

## Required Phase B validation

The authorized implementation must pass, serially and with external networking
disabled:

1. `tests/deployment/test_migration_discovery.py`;
2. `tests/deployment/test_execution_plan.py`;
3. exact sealed-baseline blocked reports for both Robinhood profiles, including
   null `plan_hash`, exact roots, exact six-blocker set/owners, and absence of
   host or sensitive fields, with identical pre/post repository bytes, paths,
   and Git status and no created directories, locks, or temporary/staging files;
4. RFC 8785 absent-versus-null, rejected-number, and final-LF cases;
5. the three complete H-02 test files, explicit all-five-profile plan outcomes,
   and proof every pre-existing operation outcome is unchanged;
6. the unchanged Base profile regression file;
7. all then-applicable H-01, S1, and S2 gates;
8. the repository-authoritative full serial suite;
9. import/help checks with relevant environment variables absent;
10. two fresh-process and two-clean-checkout dry-plan comparisons for both
   Robinhood profiles;
11. parsing of every committed Base history JSON without rewriting it;
12. exact Base migration/history inventory comparison before and after;
13. negative scans for Base paths/blobs, executable placeholders, sensitive
    values, unexpected files, skips, and xfails;
14. proof no Phase B path constructs `DeployArgs`, calls execution, or changes
    transaction retry, result classification, or Base runtime semantics;
15. local Markdown links, balanced fences, conflict markers, tabs, trailing
    whitespace, and internal ID/count consistency;
16. exact six-file scope, `git diff --check`; and
17. the untracked-file `git diff --no-index --check` before either proposed
    test file is tracked.

No result is sufficient if a required negative assertion or evidence artifact
is missing. No dependency installation or environment refresh is implied by
this list.

## Rollback and remediation boundary

The proposed Phase B has no external state and publishes no migration ID,
source, or history. Before publication, rollback is an ordinary reviewed source
revert of exactly the six authorized implementation/evidence files to the
exact baseline, followed by sealed H-02 evidence reconciliation and the
complete Base/H-02 validation package. No shared execution runtime or history
is changed, so no history rewrite is involved.

If a later separately authorized phase publishes an identifier, that identifier
is not deleted, renamed, reordered, or repurposed. An unused record receives an
immutable non-executable disposition. A defect after publication is remediated
with a later owner-approved forward identifier. Confirmed onchain actions are
not rollback; the controlling specification permits only truthful governance
remediation or forward migration
([rollback truth](../robinhood-deployment-support-specification.md#L1253-L1264)).

## Phase A validation record

| Check | Result |
| --- | --- |
| Local `rh`, cached `origin/rh`, and live `origin/rh` | All equal current integration commit `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`; sealed analysis baseline remains historical |
| Integration worktree | Clean on `rh` |
| Isolated branch/worktree | Exact baseline commit and tree |
| Scope | Exactly this one untracked evidence file; staged set empty |
| Namespace/history absence | Shared source and both Robinhood history roots remain absent |
| Required citations | All required input links present |
| Local Markdown links | 64 links checked; 25 unique local targets resolve; line anchors in range |
| Markdown structure | Four fences balanced; 18 tables have consistent column counts |
| Inventory eligibility | 62/62 top-level Base migration entries are non-symlink regular `*.py`; 58/58 top-level Base history entries are non-symlink regular `*.json`; no strays |
| Reservation matrix | 18 rows, 18 unique IDs, canonical order |
| Owner approval | OD-01 through OD-12 approved exactly at source SHA `a4dced33f48aa71246a5fa2a1018d12eb0b7b4b4c821838f7f52957fe09b8315`; Phase B separately unauthorized |
| Internal registers | 34 CF findings, 24 FD rules, 11 test groups, 12 unique approved owner decisions, and zero unchecked owner decisions |
| Conflict/tab/trailing-whitespace scan | Clean |
| Sensitive literal scan | No endpoint URL, address literal, credential literal, or key material |
| `git diff --check` | Pass |
| Untracked `git diff --no-index --check` | Pass |

No runtime test was run: this phase changes no implementation or test file, and
the authorization prohibits dependency or environment installation. Validation
was static, local, read-only except for this evidence file, and network-free
except for the required read-only live Git remote identity check.

## Phase A conclusion

The correct minimum boundary is a profile-qualified, import-free, deterministic
planner that fails closed before environment or account access. It consumes one
shared Robinhood source and two isolated histories, but the current integrated
registry deliberately blocks those repositories and cannot yet promote their
shared source. Current Base discovery, resume, retry, and history behavior is
not safe to reuse for Robinhood.

The owner has approved OD-01 through OD-12 exactly as presented at the recorded
source SHA. Current-state reconciliation replaces the historical
sealed-baseline H-03 R5 blocker with approved, published, integrated R6
authority at the exact identities above. This satisfies only H-05's H-03
approval/integration dependency: H-03 exact-lock validation and Phase B remain
open, and none of H-04, S5, Track 8, H-06, H-08, or H-09 is cleared. The H-05
approval closes the Phase A decision packet but does not authorize Phase B.

All 18 reservations remain non-executable. The proposed Phase B can safely
implement only the blocked planning and discovery boundary in six files. It
cannot publish the namespace, create skeletons, enable migration execution, or
clear H-03, H-04, S5, Track 8, H-06, H-08, or H-09 blockers.
