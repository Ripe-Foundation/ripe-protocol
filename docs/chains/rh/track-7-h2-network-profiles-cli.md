# Track 7 H-02: Network Profiles and CLI Safety

**Status:** Draft for owner, deployment-tooling, security, and Base-owner
review; implementation launch is blocked until H-01 is reviewed and integrated
into `rh`

**Prepared:** 24 July 2026

**Planning baseline:** `dd51c637f1462bede7529a53427bfb4327dbfb12`

## Fresh-agent instruction

Treat this document as the task contract. Implement only Track 7 follow-on
slice H-02: replace the deployment tools' scattered network labels and unsafe
fallbacks with one immutable, validated network-profile registry, then make the
existing migration, console, and verification entrypoints consume it safely.

This is deployment-tooling work, not a protocol-contract change. It must make
wrong-network, missing-secret, cross-history, and unsupported-provider states
fail closed without adding a new live deployment capability. No contract,
default, migration, manifest, generated ABI, production address, account
backend, RPC provider, fee policy, finality policy, or live operation is
authorized.

Use branch `rh-track-7-h2-network-profiles-cli`. Commit deliverables to that
branch with clear messages. Never push directly to or merge into `rh` or
`master`; the owner reviews and integrates the work.

## Worktree bootstrap

The owner must first commit this reviewed brief and its H-02 ownership
correction to `rh`. H-01 must then pass its mandatory reviewer gate and be
integrated into `rh`. The fresh H-02 agent creates its own worktree only after
both conditions are true:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - local `rh` and `origin/rh` resolve to the same owner-approved commit;
   - this brief exists in that commit;
   - the merged Track 7 support specification and validation plan exist;
   - the H-02 row names `scripts/utils/migration_helpers.py` and the sanitized
     implementation record;
   - the reviewed H-01 dependency gate and resulting requirement state are
     integrated into `rh`;
   - S1 and S2 remain integrated and their gates pass on the untouched
     baseline; and
   - no active branch owns an H-02 file.
3. Record:
   - the full starting commit;
   - SHA-256 hashes of this brief, both Track 7 authority documents,
     `requirements.in`, `requirements.txt`, and every H-02 existing file;
   - the integrated H-01 evidence commit and exact dependency versions;
   - the Python, pip, Vyper, Titanoboa, and pytest versions;
   - the S1/S2 and untouched full-suite results; and
   - local/remote branch parity.
4. Confirm that branch `rh-track-7-h2-network-profiles-cli` and path
   `/Users/wigglez/dev/ripe-protocol-track-7-h2-network-profiles-cli` do not
   exist. If either exists, stop and ask the owner. Do not reuse, delete,
   reset, or overwrite it.
5. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-7-h2-network-profiles-cli \
     /Users/wigglez/dev/ripe-protocol-track-7-h2-network-profiles-cli \
     rh
   ```

6. Verify the new worktree's branch, commit, clean status, file hashes,
   dependency versions, and baseline test results.
7. Run every subsequent command and make every edit inside
   `/Users/wigglez/dev/ripe-protocol-track-7-h2-network-profiles-cli`.

Do not modify or commit from the integration worktree.

## Hard sequencing rule: H-01 controls the runtime baseline

H-02 must consume the reviewed, integrated H-01 dependency state. It must not
read a floating H-01 worktree, cherry-pick an unintegrated H-01 commit, copy
H-01 files manually, or branch from a pre-H-01 `rh`.

Stop before editing if:

- H-01 is not integrated locally and remotely;
- H-01's reviewer gate is incomplete or conditional;
- the dependency evidence does not identify the exact installed profile;
- S1's exact-version assertions disagree with the integrated lock; or
- any requirement or lock change is pending after the H-02 worktree is
  created.

If dependencies change after bootstrap, stop, reconcile from the new reviewed
`rh` baseline, refresh all recorded hashes, and rerun the baseline before
continuing.

## Planning correction carried by this brief

The original H-02 slice row named the three CLI modules but omitted
`scripts/utils/migration_helpers.py`, even though A-001's silent public test-key
fallback is implemented by `get_account()` in that helper. It also lacked a
sanitized place to preserve implementation and review evidence. The reviewed
planning batch adds the helper and evidence record to H-02's exact ownership
boundary.

This is a correction to file ownership, not permission to redesign shared
migration helpers. H-02 may change only the account-loading behavior needed to:

- remove the implicit public test-key fallback;
- keep any test/local key use explicit, local-only, and impossible to select
  through a live-capable profile;
- ensure account loading cannot occur before runtime chain identity is proved;
  and
- provide deterministic, network-free tests for those properties.

If closing A-001 requires another file, a new account backend, or a wider
account abstraction, stop and amend the specification through owner and
security review.

## Exact file ownership

H-02 may modify only:

- `scripts/migrate.py`;
- `scripts/console.py`;
- `scripts/verify.py`;
- `scripts/utils/migration_helpers.py`;
- new `config/network_profiles.py`;
- new `tests/deployment/test_network_profiles.py`;
- new `tests/deployment/test_secret_handling.py`; and
- new `tests/deployment/test_base_profile_regression.py`.

H-02 may also add one sanitized implementation record:

- new `docs/chains/rh/evidence/network-profile-cli-implementation.md`.

The evidence record must contain hashes, commands, results, known limitations,
and reviewer/owner provenance. It must never contain a secret, credentialed
URL, raw environment dump, provider response, private key, or account address
that was not already public and expressly required.

The existing `tests/deployment/` directory is the shared offline deployment
tooling test surface established by H-01. H-02 owns only the three unique test
files named above.

## Prohibited files and scope

Do not modify:

- anything under `contracts/`, `interfaces/`, `migrations/`, or
  `migration_history/`;
- `config/BluePrint.py`, `contracts/config/DefaultsBase.vy`, or any future
  Robinhood blueprint/default;
- `scripts/utils/deploy_args.py`, `scripts/utils/migration.py`,
  `scripts/utils/migration_runner.py`, or verifier adapters;
- `scripts/utils/verify_etherscan.py` or any new Blockscout adapter;
- `requirements.in`, `requirements.txt`, S1, or S2;
- generated ABIs, bytecode, manifests, or parameter outputs;
- `.env`, shell profiles, credential stores, or external account state;
- the Track 7 authority documents other than the already reviewed ownership
  correction committed with this brief;
- `docs/chains/rh-summary.md`; or
- another track's files.

Do not create Robinhood migration/history directories. Do not implement H-03
blueprints, H-04 defaults, H-05 migration discovery/plans, H-06 evidence
writers, H-07 verifier adapters, H-08 assertions, or any H-10/H-11 runbook.

If an H-02 test exposes a defect owned by one of those slices, record it and
stop at the ownership boundary rather than fixing it here.

## Required reading

Read and verify the integrated versions of:

### Program authority

- `docs/chains/rh-summary.md`
- `docs/chains/rh/robinhood-deployment-support-specification.md`, especially
  Sections 3, 5, 7, 8, 18, and 19
- `docs/chains/rh/robinhood-deployment-validation-plan.md`, especially V-00,
  V-01, Stage 1, NEG-001, NEG-002, NEG-004, NEG-032, and H-02
- `docs/chains/rh/component-matrix.md`, especially CM-055 and CM-059
- `docs/chains/rh/track-7-h1-dependency-security-preflight.md`
- `docs/chains/rh/evidence/dependency-security-gate.md`
- `docs/chains/rh/minimal-contract-change-reassessment.md`

### Existing H-02 implementation surface

- `scripts/migrate.py`
- `scripts/console.py`
- `scripts/verify.py`
- `scripts/utils/migration_helpers.py`

### Adjacent code that must be understood but not changed

- `config/BluePrint.py`
- `scripts/utils/deploy_args.py`
- `scripts/utils/migration.py`
- `scripts/utils/migration_runner.py`
- `scripts/utils/verify_etherscan.py`
- `scripts/utils/mock_account.py`
- `scripts/utils/safe_account.py`
- `scripts/utils/json_file.py`
- `scripts/utils/log.py`

Read relevant current tests for migration CLI, console, verification, account
helpers, history selection, and environment isolation. Search the repository
for every import and use of `CLICK_PROMPTS`, `param_prompt`,
`ETHERSCAN_API_KEYS`, `ETHERSCAN_URLS`, `MIGRATION_HISTORY_DIR`,
`WEB3_ALCHEMY_API_KEY`, `BASESCAN_API_KEY`, `ETHERSCAN_API_KEY`,
`TEST_PRIVATE_KEY`, `get_account`, `--chain`, `--rpc`, and `--blueprint`.

Do not assume the reading list is exhaustive for analysis. It is exhaustive
for files H-02 may edit.

## Objective

Produce the smallest implementation that:

1. defines one immutable, typed, fail-closed registry for the five reviewed
   profiles:
   - `local`;
   - `base-mainnet`;
   - `base-sepolia`;
   - `robinhood-mainnet`; and
   - `robinhood-testnet`;
2. gives each profile an explicit identity, repository namespace, operation
   capability, RPC environment reference, fork policy, and verifier policy;
3. makes unknown profile/provider/operation identifiers fail before environment
   access, account loading, filesystem history access, network access, or
   verifier setup;
4. proves runtime `eth_chainId` equality before any account loading, signing,
   live-state simulation, verification, or submission path;
5. removes eager explorer-key reads and vendor-token URL construction;
6. removes implicit public test-key fallback;
7. redacts RPC values completely from logs, exceptions, object
   representations, plans, and tests;
8. prevents one profile from reading or writing another profile's history;
9. preserves intended Base labels and history selection without preserving
   unsafe fallback behavior; and
10. leaves unresolved live provider, signer, fee, finality, verifier-rate, and
    release-confirmation choices explicitly unsupported.

H-02 is complete only when the same code paths are proven for Base and
Robinhood profiles. Adding Robinhood strings to Click choices without enforcing
the profile invariants is not completion.

## Required outcome vocabulary

Every profile operation must resolve to exactly one of:

- `supported`: all static prerequisites for the offline or mocked operation are
  present;
- `unsupported`: the profile deliberately does not support the operation;
- `blocked_pending_policy`: the operation shape is known but a required owner
  policy, provider, account backend, finality rule, or verifier adapter is not
  approved; or
- `invalid`: the profile or configuration violates schema invariants.

Do not represent `unsupported`, `blocked_pending_policy`, or `invalid` as a
warning followed by fallback execution.

## Controlling constraints

### 1. One registry; no parallel authority

`config/network_profiles.py` is the sole H-02 authority for profile identity
and static network/repository policy. Do not add another chain dictionary to a
CLI or retain a hidden chain/provider fallback as a second authority.

Click choices, help text, repository namespaces, and verifier selection must be
derived from the registry or validated against it. Avoid import-time behavior
that resolves environment values.

### 2. Profiles store references, never secrets

An environment field stores only a variable name such as
`ROBINHOOD_MAINNET_RPC_URL`; it never stores or logs the value. RPC values are
resolved lazily only after profile and operation validation.

A command that does not require an RPC or verifier key—such as module import,
`--help`, schema validation, or offline tests—must work with every relevant
environment variable absent.

### 3. Identity precedes authority

For any operation that can reach a real network:

1. select and validate the canonical profile;
2. resolve the one required RPC reference lazily;
3. connect only through an injected/testable boundary;
4. read `eth_chainId`;
5. compare it exactly with the selected profile; and only then
6. initialize or load an account, signer, verifier, or state-changing runner.

Tests must spy on call order and prove that a mismatch performs no account,
signing, verification, history-write, or submission action.

H-02 does not approve any live account backend. A profile with an empty
`live_account_backend_ids` list must reject live mode before secret access.

### 4. Local test identity must be explicit

The current public Anvil key may be used only by an explicit local test path
whose profile and operation both prohibit live/fork submission. Absence of
`${ACCOUNT}_PRIVATE_KEY` must never select it.

Prefer requiring an explicit key argument or injected test account over a
module-level fallback. If the current helper signature cannot meet this rule
without breaking non-H-02 callers, stop at the checkpoint and propose the
smallest reviewed signature change; do not weaken the rule.

### 5. Full redaction, not partial masking

Never log a full or sliced RPC URL. Do not rely on truncation: credentials may
occur anywhere in a URL. User-supplied `--rpc` values are sensitive even when
they appear public.

Allowed diagnostics identify only the profile ID, operation, expected/observed
chain ID, environment-variable name, and a stable error code. Exception
messages and object representations must obey the same rule.

### 6. Base compatibility is semantic and bounded

Preserve:

- canonical `base-mainnet` selection;
- chain ID `8453`;
- the existing source path `migrations/base-mainnet`;
- the existing history path `migration_history/base-mainnet/v1`;
- `base-sepolia` identity `84532` while truthfully marking unsupported
  repository operations whose namespace does not exist; and
- existing Base manifests/history as read-only compatibility fixtures.

Do not preserve:

- implicit `base-mainnet` selection for unknown labels;
- `WEB3_ALCHEMY_API_KEY` URL interpolation unless a separately approved,
  time-bounded compatibility adapter is recorded;
- eager `BASESCAN_API_KEY` or `ETHERSCAN_API_KEY` reads;
- silent test-key fallback;
- raw or sliced RPC logging;
- non-Base `KeyError` behavior;
- history inference from arbitrary user strings; or
- unproved Safe/Ledger/private-key live support.

The Base regression test must distinguish intended compatibility from known
unsafe behavior. It must not fossilize a defect merely because it exists.

### 7. Repository namespaces cannot alias

Use the reviewed identities:

- Base mainnet source: `migrations/base-mainnet`;
- Base mainnet history: `migration_history/base-mainnet/v1`;
- Robinhood shared future source: `migrations/robinhood`;
- Robinhood mainnet future history:
  `migration_history/robinhood-mainnet/v1`;
- Robinhood testnet future history:
  `migration_history/robinhood-testnet/v1`.

H-02 records proposed Robinhood paths as profile values but does not create
them. Mainnet and testnet may share a future source path; they must never share
history. A missing path remains missing and cannot fall back to Base or another
profile.

### 8. Fork and live modes remain distinct

Fork profiles require exact source-chain identity. A pinned block is required
for reproducible/committable evidence; `latest` is allowed only for local
exploration. Fork mode must have `allow_submission = false`.

H-02 must remove the console's unconditional dirty-fork posture from any path
that could be presented as release evidence. If maintaining an exploratory
dirty fork is necessary, it must be explicitly selected, labeled local-only,
and excluded from evidence.

No public Robinhood RPC may become an implicit live deployment endpoint.

### 9. Verification selection stops before H-07

H-02 may make `scripts/verify.py` select and validate a profile, build the
correct manifest path, and fail truthfully when the profile's verifier
operation is unsupported or blocked.

H-02 must not implement the Blockscout adapter, modify Etherscan submission
logic, choose a Robinhood verification rate policy, read a production explorer
key, or submit a verification request. Those belong to H-07 and later
authorization.

### 10. Migration semantics stop before H-05

H-02 may supply validated source/history paths to existing entrypoints. It must
not change migration discovery, timestamp/resume behavior, manifest promotion,
execution-plan semantics, migration IDs, or create Robinhood skeletons. Record
those defects for H-05.

### 11. No comprehensive refactor

Apply the user's minimum-change directive to tooling too: prefer a small
immutable data model and narrow adapters in the three CLIs over a framework
rewrite. Every changed production-tooling line must map to an H-02 invariant or
test.

## Phase A — baseline audit and implementation design

Before editing code:

1. Reproduce and record, without printing secrets:
   - importing `scripts.migrate` with `BASESCAN_API_KEY` absent;
   - each CLI's `--help` with relevant environment variables absent;
   - the duplicate `base-mainnet` and `base-sepolia` entries in the migration
     CLI's current chain choices;
   - the migration CLI's current mismatch between help text claiming a `local`
     default and the actual `base-mainnet` default;
   - unknown-chain behavior;
   - non-Base explorer behavior;
   - missing private-key behavior through a safe injected/test boundary;
   - RPC log behavior with a synthetic credential-bearing URL;
   - Base mainnet source/history selection;
   - Base Sepolia's current advertised-but-incomplete namespace; and
   - console dirty/latest fork defaults.
2. Build a complete use/import map for every H-02 symbol named in Required
   Reading.
3. Record which current behaviors are intended compatibility, known defects,
   unsupported claims, and H-05/H-07-owned defects.
4. Specify the exact public API of `config/network_profiles.py`, including:
   - immutable profile type(s);
   - canonical IDs and any legacy aliases;
   - operation enum/outcome;
   - lookup and validation functions;
   - lazy environment resolution boundary;
   - chain-ID assertion boundary;
   - source/history path representation;
   - redacted diagnostic representation; and
   - deterministic test constructors or fixtures.
5. Trace every possible path from CLI parsing to:
   - environment access;
   - RPC connection;
   - account loading;
   - history access;
   - verifier selection; and
   - submission.
6. Propose the smallest code diff and identify every line that cannot be owned
   by H-02.

### Phase A mandatory checkpoint

Stop before editing implementation files and provide the owner/reviewers:

- the current-behavior audit;
- the proposed registry API;
- the call-order graph;
- the Base compatibility table;
- the exact file diff plan;
- the test matrix;
- the proposed location and ownership of any public local-test key literal,
  with proof that no live-capable path can import or reference it;
- an explicit owner decision on whether the migration CLI should require a
  profile or retain an accurately documented default, and which default;
- any unresolved question about explicit local test accounts;
- any discovered need to edit a prohibited file; and
- confirmation that no environment secret or external connection was used.

The safe default is no implementation until deployment-tooling, security, and
Base owners approve this checkpoint. Approval of the brief alone authorizes
Phase A only.

## Phase B — immutable profile registry

Only after checkpoint approval:

1. Add immutable, typed profile structures with no mutable nested dictionaries.
2. Add the five canonical profiles with the reviewed chain identities:
   - `local`: runtime-configured identity, local runtime only;
   - `base-mainnet`: `8453`;
   - `base-sepolia`: `84532`;
   - `robinhood-mainnet`: `4663`; and
   - `robinhood-testnet`: `46630`.
3. Store environment-variable names, never values.
4. Encode repository source/history identities exactly and reject cross-profile
   history aliasing.
5. Encode operation capabilities and unresolved-policy blocks explicitly.
6. Provide deterministic validation and stable, redacted error codes.
7. Keep import and schema validation free of environment access and network
   side effects.

Do not put account secrets, finality values, fee caps, production URLs,
production addresses, or mutable runtime state in the registry.

## Phase C — account and identity safety

1. Remove `get_account()`'s missing-secret fallback.
2. Make any explicit local test account path impossible for live-capable
   profiles and submission modes.
3. Introduce or expose a testable chain-ID assertion that runs before account
   loading.
4. Update `scripts/migrate.py` so unsupported Safe/Ledger paths fail
   deliberately instead of leaving `sender` undefined or implying support.
5. Ensure missing RPC/account policy fails before migrations, history writes,
   verifier setup, or deployment environment creation.
6. Prove through spies/mocks that wrong-chain and blocked-profile cases perform
   no authority-bearing action.

Do not implement a new signer backend.

## Phase D — CLI integration

### `scripts/migrate.py`

- remove eager explorer-key dictionaries;
- remove vendor-token URL construction;
- validate profile/operation before environment resolution;
- use only profile-owned source/history identities;
- assert chain identity before account loading;
- redact every RPC diagnostic;
- configure no verifier when unsupported or H-07-blocked;
- preserve Base-mainnet source/history selection; and
- leave migration execution/resume semantics unchanged.

### `scripts/console.py`

- derive choices and paths from canonical profiles;
- require a valid fork-capable profile and exact chain identity;
- remove raw/sliced RPC logging;
- distinguish local exploration from reproducible pinned evidence;
- prohibit source-RPC submission;
- preserve explicit Base-mainnet history lookup; and
- do not claim that an unpinned or dirty fork is release evidence.

### `scripts/verify.py`

- stop importing `scripts.migrate` for prompt reuse;
- select and validate a canonical profile without eager environment access;
- derive the manifest path only from that profile;
- stop truthfully on unsupported/blocked verifier operation; and
- preserve Base verification routing only to the extent possible without
  implementing H-07 or accessing a real key.

No H-02 test may submit verification.

## Phase E — required tests

### `test_network_profiles.py`

At minimum prove:

- all five canonical IDs and chain IDs;
- profile objects and nested data are immutable;
- unknown profile fails before environment/provider/account/history access;
- duplicate canonical IDs and invalid schemas fail;
- aliases cannot change chain ID or repository identity;
- mainnet/testnet histories cannot alias;
- Robinhood mainnet/testnet share only the proposed source namespace;
- missing directories do not fall back;
- unsupported and blocked operations are distinct;
- fork submission is always false;
- reproducible fork mode requires a block pin;
- dirty/latest fork remains local exploration only;
- chain-ID mismatch occurs before account load;
- correct chain ID permits only the next mocked step, not live execution; and
- error output contains no sensitive value.

Use the exact NEG-001, NEG-002, and NEG-032 names from the validation plan
where specified.

### `test_secret_handling.py`

At minimum prove:

- all H-02 modules import with relevant env vars absent;
- all CLI `--help` paths work with env vars absent;
- an RPC env is read only for an operation that requires it;
- a missing RPC env fails lazily and locally;
- missing `${ACCOUNT}_PRIVATE_KEY` never selects `TEST_PRIVATE_KEY`;
- any explicit local test account is rejected for live/fork submission;
- wrong-chain identity prevents private-key access;
- RPC URL, username, password, query, path token, and fragments never appear in
  logs, exceptions, reprs, or captured output;
- a user-supplied `--rpc` receives the same redaction;
- explorer keys are not read eagerly;
- unsupported verifier selection performs no key lookup; and
- the process environment is not dumped or persisted.

Use NEG-004's exact test name where specified.

### `test_base_profile_regression.py`

At minimum prove:

- `base-mainnet` resolves chain ID `8453`;
- its source/history remain `migrations/base-mainnet` and
  `migration_history/base-mainnet/v1`;
- generated/profile-derived chain choices contain no duplicates;
- CLI help and runtime behavior expose the same owner-approved default, or both
  require an explicit profile when no default is approved;
- legacy accepted Base CLI spelling resolves only to that canonical profile;
- unknown labels never resolve to Base;
- Base Sepolia is identity-valid but unsupported for missing repository
  operations rather than borrowing Base-mainnet paths;
- the advertised Ethereum labels are not silently mapped to a supported
  profile; Phase A must establish whether they are only stale CLI claims or a
  real supported workflow, and stop for owner review if removing them would
  break an evidenced workflow;
- intended Base manifest path construction remains compatible;
- module import/help needs no Base explorer key;
- unsafe Alchemy-token construction, test-key fallback, RPC logging, and
  provider `KeyError` are not preserved as regression expectations; and
- committed Base histories are not modified.

### Test isolation

All tests:

- run with external networking disabled;
- use synthetic URLs, keys, accounts, and chain-ID responses;
- isolate environment mappings per test;
- use temporary directories for any path fixture;
- do not read `.env`;
- restore monkeypatches and Boa/global state;
- do not depend on test order; and
- do not write under committed migration history.

## Phase F — validation

Run serially from the isolated H-02 worktree:

1. import/help checks with relevant environment variables absent;
2. `python -m pytest -q tests/deployment/test_network_profiles.py`;
3. `python -m pytest -q tests/deployment/test_secret_handling.py`;
4. `python -m pytest -q tests/deployment/test_base_profile_regression.py`;
5. the three H-02 files together;
6. the H-01 dependency gate;
7. the S1 clock profile suite;
8. the S2 checked-inventory guard;
9. existing migration, console, verification, and Base tests;
10. `python -m pytest --collect-only -q`;
11. `python -m pytest -q`; and
12. `git diff --check`.

Record exact commands, versions, collected counts, pass/fail/skip totals,
durations, and any environment exclusions. A green exit code does not waive a
missing negative assertion.

## Mandatory reviewer gates

### Gate 1 — implementation and security

Before the branch may be considered merge-ready, an independent reviewer must:

- inspect every changed line;
- verify the registry is the single authority;
- verify there is no import-time environment/network side effect;
- verify chain identity precedes account/key access;
- verify test-key fallback is impossible outside an explicit local-only path;
- inspect secret-redaction tests for path/query/fragment leakage;
- verify Base compatibility assertions do not preserve defects;
- verify H-03/H-05/H-07 boundaries remain intact;
- inspect the full test evidence; and
- confirm no secret, external connection, or live action occurred.

Any material finding returns the branch to implementation and requires a fresh
Gate 1 review.

### Gate 2 — integration readiness

After Gate 1 approval:

1. refresh the branch against current `rh`;
2. verify H-01 and every intervening reviewed change;
3. rerun targeted, H-01, S1, S2, Base regression, collection, and full-suite
   validation;
4. compare the exact diff with Gate 1;
5. confirm no active track owns an overlapping file;
6. record local and remote ahead/behind plus a virtual merge; and
7. obtain explicit owner approval before merge.

No push to `rh`, merge, worktree removal, or branch deletion is authorized by
either gate.

## Approval boundaries

Allowed without further owner approval after Phase A checkpoint approval:

- edits to the exact H-02 files;
- offline deterministic tests;
- local compilation/import/CLI help;
- temporary test directories inside the normal test process; and
- commits to the H-02 branch.

Require separate owner approval:

- any file outside exact ownership;
- any dependency change;
- any account backend or key-store integration;
- any network request, even read-only;
- any access to a real RPC/key/private account;
- any external write or verification submission;
- any production value or address;
- any migration/history creation or mutation;
- any push to or merge into `rh`/`master`; and
- any deployment or signing action.

## Stop conditions

Stop and return to the owner/reviewers if:

- H-01 or another prerequisite is not integrated and current;
- an H-02 file is concurrently owned;
- a prohibited file is required;
- Base intended behavior cannot be distinguished from a defect;
- chain identity cannot be checked before account loading;
- a real URL/key/account would be needed;
- a local test key could reach a live/fork submission path;
- any secret-like value reaches output or persisted evidence;
- a profile can fall back to another profile's source/history/provider;
- a Robinhood value would be guessed;
- H-03/H-05/H-07 work is required to make an H-02 test pass;
- tests need external networking;
- S1, S2, H-01, Base regression, or the full suite regresses; or
- branch baseline or authority documents change after approval.

## Required deliverables

### Deliverable A — implementation

- the reviewed H-02 code and tests within exact ownership.

### Deliverable B — sanitized implementation record

`docs/chains/rh/evidence/network-profile-cli-implementation.md` must record:

- baseline and final commits/hashes;
- H-01 dependency baseline;
- Phase A audit and approved checkpoint;
- exact registry API and operation vocabulary;
- Base compatibility disposition;
- old-to-new behavior map;
- call-order proof;
- negative-test mapping;
- exact validation commands/results;
- known unsupported/blocked operations;
- any deferred H-03/H-05/H-07 defect;
- Gate 1 and Gate 2 provenance; and
- an explicit statement that no secret, network access, external write,
  signing, deployment, or live verification occurred.

## Completion criteria

H-02 is complete only when:

- H-01 is integrated and recorded;
- the exact file boundary is respected;
- the five canonical profiles validate;
- unknown and unsupported states fail closed;
- runtime chain identity precedes account/key access;
- no implicit test key, vendor URL, eager key read, or RPC leakage remains;
- Base intended source/history behavior is preserved;
- Robinhood profiles remain blocked from live use while policy/backend fields
  are unresolved;
- all targeted, dependency, S1, S2, Base, collection, and full-suite checks
  pass;
- both reviewer gates close;
- deliverables are committed to the H-02 branch; and
- the owner decides whether to integrate.

The agent must report which checklist items become eligible for owner closure.
The agent must not tick `docs/chains/rh-summary.md`.

## Completion report

Report:

- branch, worktree, starting commit, and final commit;
- exact files changed;
- Phase A checkpoint approval provenance;
- H-01 baseline and file hashes;
- registry/profile/operation design;
- removed fallback and secret-leak paths;
- Base compatibility results;
- tests and exact outcomes;
- reviewer-gate status;
- remaining blockers and deferred slice ownership;
- local/remote ahead-behind and push status; and
- explicit confirmation of no contract/default/migration/manifest/generated
  artifact, secret access, network access, external write, signing, deployment,
  verification submission, `rh`/`master` merge, or checklist edit.
