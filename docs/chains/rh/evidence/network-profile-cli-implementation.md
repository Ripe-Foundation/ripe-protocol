# Track 7 H-02 network-profile and CLI evidence

## Status and checkpoint boundary

This record contains the H-02 Phase A read-only audit, approved design,
Phase B implementation, and Phase F validation. The owner approved the Phase A
checkpoint before implementation. The implementation is committed for
independent Gate 1 review; Gate 1 and Gate 2 are not yet approved.

Phase A used the isolated worktree and branch:

```text
worktree: /Users/wigglez/dev/ripe-protocol-track-7-h2-network-profiles-cli
branch: rh-track-7-h2-network-profiles-cli
HEAD: 26eb3a78668d623be40ed2b6e16f52c919906a12
local rh: 26eb3a78668d623be40ed2b6e16f52c919906a12
fetched origin/rh: 26eb3a78668d623be40ed2b6e16f52c919906a12
tree: c4750ce7e743ffd817659e5fb572b9058d01160c
parent: 575d47b82055b42da2bddf1535d8076cd7cf4c63
subject: Record H-01 post-integration K-02 evidence
author/committer: Mick Hagen, 2026-07-24T19:27:24-06:00
```

The worktree was clean before this record was added. Phase A did not read a
real RPC, explorer key, account key, `.env`, credential store, or raw process
environment. It made no RPC, explorer, verifier, signer, Safe, Ledger, browser,
or other external connection. It did not sign, submit, migrate, verify, deploy,
push, merge, or edit the integration worktree.

The only external package access occurred during the separately owner-approved
bootstrap: exact locked packages were downloaded from public PyPI into a
disposable environment. That access preceded Phase A and did not change the
repository or the active `ripe-lite` environment.

The exact implementation commit is:

```text
commit: 4aea35225ac13dc22f6f207b3425bcb7e96d6cec
tree: 0d5a8af0453f556b5c03b8e922c8af35e7737d28
parent: 26eb3a78668d623be40ed2b6e16f52c919906a12
subject: Implement H-02 network profiles and CLI safety
author/committer: Mick Hagen, 2026-07-24T21:24:01-06:00
```

## Frozen inputs and H-01 runtime

### Input hashes

| Path | SHA-256 |
|---|---|
| `docs/chains/rh/track-7-h2-network-profiles-cli.md` | `f37597f37d6cf785f50bac0954709e2f60dde7ab836ed2c699cab45e5d105b59` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `9a85d0a0307ce8fc6d268d6c48ab9a27bc60a75f8cbb655e88220020e7482698` |
| `docs/chains/rh/robinhood-deployment-validation-plan.md` | `ab39fd135c50f7d348788341a061511b50a854550234de9165554e5674ec2393` |
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `scripts/migrate.py` | `8b4df707383ed336ba36b4f288bc4037d1d4485decf7647bf9b670cdd1797f2a` |
| `scripts/console.py` | `048cfb39ec1d509c0c357bee2a811f522f0f28e4af86d53ec225b32176de358a` |
| `scripts/verify.py` | `752d29cd386b7a63b6b635cb842022a327368d669cc9457cb10099d3ac12861c` |
| `scripts/utils/migration_helpers.py` | `f369004a661478606f3b2764703e8fd54958def741c58f1aa9a14b7de179b1ec` |
| `tests/deployment/test_dependency_gate.py` | `d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa` |
| `docs/chains/rh/evidence/dependency-security-gate.md` | `5cb0d37aa50ab66b13d8389eecafd2bcd1f47dd7a3fd6fb6648e34470393fa87` |

H-01's reviewed branch commit
`3b46be0a3af3355661b4a9f55b6a4c2295a39da7` is the second parent of
integration commit `575d47b82055b42da2bddf1535d8076cd7cf4c63`, which is an
ancestor of the H-02 baseline.

### Disposable locked environment

```text
root: /private/tmp/rh-h02-cpython312.pQexIu
root mode: 0700
Python: 3.12.0
pip: 23.2.1
Vyper: 0.4.3
Titanoboa: 0.2.7
pytest: 8.4.2
locked distributions checked: 92
locked version mismatches: 0
pip check: No broken requirements found
```

The exact install command was:

```bash
/private/tmp/rh-h02-cpython312.pQexIu/venv/bin/python \
  -m pip --isolated install --no-cache-dir --no-deps \
  --index-url https://pypi.org/simple -r requirements.txt
```

`--isolated` ignored user and global pip configuration, `--no-deps` prevented
dependency re-resolution, the explicit index was public PyPI, and no cache or
extra/private index was used.

### Bootstrap validation

| Location / command | Result |
|---|---|
| Integration H-01 dependency gate | `16 passed in 1.45s` |
| Integration S1 clock profiles | `57 passed in 27.34s` |
| Integration S2 inventory | `60 passed in 25.18s` |
| Integration full suite | `2,738 passed, 142 deselected in 290.47s` |
| H-02 worktree H-01 dependency gate | `16 passed in 1.47s` |
| H-02 worktree S1 clock profiles | `57 passed in 26.99s` |
| H-02 worktree S2 inventory | `60 passed in 25.25s` |

The first H-02 full-suite attempt stopped during collection because the sandbox
denied a Titanoboa compiler-cache write under the user's normal cache
directory. It collected no complete suite and produced two
`PermissionError` collection errors. No repository assertion had failed.

The owner then authorized a fresh task-specific mode-`0700` compiler cache.
Titanoboa 0.2.7 exposes its compiler cache setter at
`boa.interpret.set_cache_dir`; it does not expose a supported cache environment
variable. The task-specific launcher used
`RH_H02_BOA_CACHE_DIR=/private/tmp/rh-h02-titanoboa-cache.gwHeaI`, removed that
variable from the process environment, and passed the path to the setter before
pytest collection.

The initial launcher incorrectly called `boa.set_cache_dir` and exited before
pytest collection with this sanitized error:

```bash
env -u BASESCAN_API_KEY -u WEB3_ALCHEMY_API_KEY -u TEST_PRIVATE_KEY \
  ETHERSCAN_API_KEY=local-placeholder \
  PYTHONPATH=. \
  RH_H02_BOA_CACHE_DIR=/private/tmp/rh-h02-titanoboa-cache.gwHeaI \
  /private/tmp/rh-h02-cpython312.pQexIu/venv/bin/python -c \
'import os; import boa; cache_dir = os.environ.pop("RH_H02_BOA_CACHE_DIR"); boa.set_cache_dir(cache_dir); import pytest; raise SystemExit(pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", "--basetemp=/private/tmp/rh-h02-bootstrap-wt-collect-cacheisolated"]))'
```

```text
AttributeError: module 'boa' has no attribute 'set_cache_dir'
```

The corrected collection command was:

```bash
env -u BASESCAN_API_KEY -u WEB3_ALCHEMY_API_KEY -u TEST_PRIVATE_KEY \
  ETHERSCAN_API_KEY=local-placeholder \
  PYTHONPATH=. \
  RH_H02_BOA_CACHE_DIR=/private/tmp/rh-h02-titanoboa-cache.gwHeaI \
  /private/tmp/rh-h02-cpython312.pQexIu/venv/bin/python -c \
'import os; from boa.interpret import set_cache_dir; cache_dir = os.environ.pop("RH_H02_BOA_CACHE_DIR"); set_cache_dir(cache_dir); import pytest; raise SystemExit(pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", "--basetemp=/private/tmp/rh-h02-bootstrap-wt-collect-cacheisolated"]))'
```

It collected `2,738/2,880` tests, with `142` deselected, in `1.55s`.

The corrected full-suite command was:

```bash
env -u BASESCAN_API_KEY -u WEB3_ALCHEMY_API_KEY -u TEST_PRIVATE_KEY \
  ETHERSCAN_API_KEY=local-placeholder \
  PYTHONPATH=. \
  RH_H02_BOA_CACHE_DIR=/private/tmp/rh-h02-titanoboa-cache.gwHeaI \
  /private/tmp/rh-h02-cpython312.pQexIu/venv/bin/python -c \
'import os; from boa.interpret import set_cache_dir; cache_dir = os.environ.pop("RH_H02_BOA_CACHE_DIR"); set_cache_dir(cache_dir); import pytest; raise SystemExit(pytest.main(["-q", "-p", "no:cacheprovider", "--basetemp=/private/tmp/rh-h02-bootstrap-wt-full-cacheisolated"]))'
```

It passed `2,738` tests, deselected `142`, and emitted three non-fatal
`PytestAssertRewriteWarning` messages in `299.74s`. The warnings identified
`_hypothesis_globals`, `hypothesis`, and `boa` as already imported by the
cache-setting launcher. No warning was suppressed and no test was skipped,
xfail-marked, changed, or weakened.

The compiler cache was removed after validation and
`/private/tmp/rh-h02-titanoboa-cache.gwHeaI` was verified absent. The disposable
locked environment remains because H-02 still needs it; it must be removed and
that removal recorded when H-02 no longer needs it.

## Phase A current-behavior audit

All executable audit probes were offline. `.env` loading was disabled with
`PYTHON_DOTENV_DISABLED=1`; the worktree contained no `.env`. Relevant
environment mappings were absent or contained only a named synthetic
placeholder. Captured output was reduced to booleans, error classes, profile
IDs, and exit codes; no endpoint value, account address, key, or environment
dump was retained.

### Import and help behavior

With `BASESCAN_API_KEY` absent:

| Probe | Exit | Sanitized result |
|---|---:|---|
| `import scripts.migrate` | 1 | `KeyError(BASESCAN_API_KEY)` |
| `python -m scripts.migrate --help` | 1 | `KeyError(BASESCAN_API_KEY)` |
| `python -m scripts.console --help` | 0 | Help succeeds |
| `python -m scripts.verify --help` | 1 | It imports `scripts.migrate` and inherits the same key error |

`scripts/console.py` and `scripts/utils/migration_helpers.py` call
`dotenv.load_dotenv()` at import time. The audit disabled that behavior. H-02
must remove those import-time `.env` reads from its owned files.

### Migration CLI selection and defaults

| Current behavior | Observation | Classification |
|---|---|---|
| Chain default | Actual `base-mainnet`; help claims `local` | H-02 defect |
| Environment/history suffix default | Actual `v1`; help claims `dev` | H-02 defect |
| Chain choices | `local`, `base-mainnet`, `base-sepolia`, `eth-sepolia`, `eth-mainnet`, then duplicate `base-mainnet` and `base-sepolia` | H-02 defect |
| Click enforcement | The configured `click.Choice` is used only by the interactive prompt callback, not by `@click.option`; arbitrary command-line labels are accepted | H-02 defect |
| Unknown profile | An arbitrary label was accepted; account loading occurred; execution then raised `KeyError` | H-02 critical ordering defect |
| Non-Base advertised profile | `eth-mainnet` was accepted; account loading occurred; execution then raised `KeyError` because the explorer-key map contains only Base labels | Stale/unsupported claim plus H-02 ordering defect |
| Blueprint default | `base`, independent of selected chain | H-02 unsafe parallel authority |
| RPC default | A vendor URL is constructed from the chain label and `WEB3_ALCHEMY_API_KEY`; an absent token can become the literal string `None` | H-02 defect |
| Explorer setup | BaseScan key is read at import and explorer setup is unconditional | H-02 defect; adapter implementation remains H-07 |
| Chain identity | No `eth_chainId` assertion occurs before account loading or runner setup | H-02 critical defect |
| Safe selection | Non-fork Safe branch leaves `sender` undefined | H-02 must deliberately reject; backend implementation is out of scope |
| Ledger selection | Branch can reference `sender` before assignment | H-02 must deliberately reject; backend implementation is out of scope |
| Start/end defaults | String `"0"` defeats intended resume behavior | H-05 defect; do not change in H-02 |
| Retry/log semantics | Positional and ambiguous | H-05 defect; do not change in H-02 |

The Base and Ethereum labels were traced through current code and Git history.
There is no current `migrations/eth-mainnet`, `migrations/eth-sepolia`,
`migration_history/eth-mainnet`, or `migration_history/eth-sepolia` namespace.
The migration CLI cannot complete either advertised Ethereum path, and the
console finds no corresponding protocol manifest. Current tests use a separate
`--fork mainnet` harness, not these H-02 CLI labels. The Phase A disposition is
that `eth-mainnet` and `eth-sepolia` are stale CLI claims, not an evidenced
current deployment workflow. Removing them from H-02 profile choices does not
alter the separate test harness. The owner should still identify any
undocumented operator workflow before approving that removal.

### Secret and account behavior

With the requested account variable absent, a patched safe boundary proved
that `get_account()` calls `Account.from_key()` once with the module's public
test-key fallback. The key value was not printed or retained in this evidence.

The migration CLI was invoked offline with a synthetic credential-shaped RPC
value and forced to stop before any connector call. Captured output contained
the complete value and each of its username, password, path-token, query-token,
and fragment-token components. `scripts/console.py` logs a 50-character slice,
which is also unsafe because credentials may occur anywhere in a URL.

Current `DeployArgs` stores the RPC value and has no custom redacted
representation. H-02 must prevent the value from entering log arguments,
exceptions, representations, plans, or evidence.

### Repository and history behavior

| Profile | Current source | Current history | Disposition |
|---|---|---|---|
| `base-mainnet` | `migrations/base-mainnet` exists | `migration_history/base-mainnet/v1` exists | Intended compatibility |
| `base-sepolia` | Missing | Missing | Identity-valid, repository operations unsupported |
| `local` | Missing | Missing | Profile/runtime identity only; migration repository operation unsupported |
| `robinhood-mainnet` | Proposed `migrations/robinhood`, absent | Proposed isolated mainnet history, absent | `blocked_pending_policy` until H-05/H-06 |
| `robinhood-testnet` | Proposed shared source, absent | Proposed isolated testnet history, absent | `blocked_pending_policy` until H-05/H-06 |

Current migration, console, and verify paths concatenate arbitrary CLI strings
under `migration_history`. They do not validate namespace ownership or prevent
cross-profile history access. `MigrationRunner._latest_manifest_timestamp()`
also creates a selected history directory. H-02 must validate profile and
identity before constructing the runner, and must never instantiate it for a
missing/proposed repository operation. Discovery, directory creation, and
resume behavior remain H-05-owned.

### Console behavior

The console defaults to `base-mainnet`, constructs an Alchemy URL unless
`--rpc` is supplied, logs an unsafe slice, always passes `allow_dirty=True`,
and treats block `"0"` as an unpinned latest fork. The blueprint argument is
stored but does not configure the session. Manifest access occurs in
`Console.__init__` before the fork is opened and before any explicit chain-ID
proof.

Dirty/latest behavior is useful only as an explicitly selected local
exploration mode. It is a defect if presented as reproducible or committable
evidence. Source-RPC submission must remain impossible.

### Verification behavior

`scripts.verify` imports prompt data from `scripts.migrate`, inherits its eager
BaseScan-key failure, derives history from arbitrary chain/environment strings,
and reads `ETHERSCAN_API_KEY` before invoking the existing verifier helper.
It can iterate and submit every manifest record and sleeps between requests.

H-02 may select a profile, derive a manifest path, and return a truthful
operation outcome. It must not call `verify_from_manifest`, inspect a real key,
or submit. Provider adapters, timeouts, rate policies, response handling, and
the unsafe fallback behavior inside `scripts/utils/verify_etherscan.py` remain
H-07-owned.

## Complete H-02 symbol and import map

### Named-symbol map

| Symbol / interface | Definition | Current consumers and related occurrences | H-02 disposition |
|---|---|---|---|
| `CLICK_PROMPTS` | `scripts/migrate.py:20` | All migration Click options; imported by `scripts.verify.py:4` | Remove profile authority from this dictionary; verify must not import migrate |
| `param_prompt` | `scripts/migrate.py:98` | Migration callbacks; imported by verify | Keep only generic prompt behavior if still needed; profile choice/default comes from registry |
| `ETHERSCAN_API_KEYS` | `scripts/migrate.py:84` | Unconditional setup at `:298` | Delete; no eager key read |
| `ETHERSCAN_URLS` | `scripts/migrate.py:88` | Unconditional setup at `:298` | Delete; verifier policy comes from registry and H-02 does not submit |
| `MIGRATION_HISTORY_DIR` | migrate `:17`, console `:25`, verify `:8` | Each CLI concatenates chain/environment strings | Delete as a parallel authority; consume profile repository paths |
| `WEB3_ALCHEMY_API_KEY` | migrate `:259`, console `:279` | Also Base-only `scripts/params/params_utils.py:29` and `tests/conf_env.py` | Remove from H-02 CLIs; out-of-scope occurrences remain explicit residuals |
| `BASESCAN_API_KEY` | migrate `:85-86` | Import-time dictionary only | Remove from H-02 CLIs |
| `ETHERSCAN_API_KEY` | verify `:47-54` | Also params tooling and global test harness | No eager H-02 read; Base verifier reference may remain named in the profile while the operation is blocked |
| `TEST_PRIVATE_KEY` | migration helper `:17` | Fallback in `get_account()` | Remove from production helper; no production literal |
| `get_account` | migration helper `:45` | Only production caller is migrate `:274`; probe tests import only `load_vyper_files` | Change safely within H-02 ownership; require explicit verified context and no fallback |
| `--chain` | migration, console, verify | Migration option does not use its declared choice for normal parsing | Replace with canonical profile parameter; preserve `--chain` only as a deprecated option spelling if approved |
| `--rpc` | migration and console | Probe tooling has separate `--rpc-url`; test harness has unrelated `--rpc` | Treat as sensitive explicit override; validate profile/operation first and never log |
| `--blueprint` | migration and console | Independent Base default; console value unused | Derive from profile; an override can only assert exact equality |

### Module and reverse-import map

| Module | Direct dependencies relevant to H-02 | Reverse consumers |
|---|---|---|
| `scripts.migrate` | `boa`, Click, `os`, log, `get_account`, `load_vyper_files`, `MigrationRunner`, `DeployArgs`, `Env`, `MockAccount` | `scripts.verify` imports the full module for prompts |
| `scripts.console` | `os`, Click, Boa, dotenv, JSON/log helpers, `load_vyper_files`; imports `DeployArgs` and `MockAccount` but does not use them | No repository Python importer found |
| `scripts.verify` | Click, JSON, `os`, migrate prompts, `verify_from_manifest`, `time` | No repository Python importer found |
| `scripts.utils.migration_helpers` | JSON, `os`, time, log, `Account`, subprocess, ABI encode, dotenv | migrate and console; `scripts.utils.migration`; probe tooling imports `load_vyper_files` only |
| `scripts.utils.deploy_args` | `config.BluePrint` parallel dictionaries | migrate, migration, migration runner; console import is unused |
| `scripts.utils.migration_runner` | `os`, dynamic imports, `Migration`, `DeployArgs` | migrate |
| `scripts.utils.migration` | Boa, JSON/log helpers, `DeployArgs`, manifest and transaction helpers | migration runner |
| `scripts.utils.verify_etherscan` | requests, JSON, time, internal chain/browser maps | verify only |
| `scripts.utils.mock_account` | address-only object | migrate; console import is unused |
| `scripts.utils.safe_account` | Web3, requests, browser, signing/proposal helpers | Import in migrate is commented out |
| `tests/conf_env.py` | Eager explorer key reads and vendor URL construction | Registered globally by `tests/conftest.py` |

No current focused tests exercise migration CLI parsing, console selection,
verification routing, account fallback, history selection, or secret
redaction. The only current `tests/deployment` file is the H-01 dependency
gate. The new H-02 tests therefore establish this offline surface without
changing the global test harness.

## Intended behavior, H-02 defects, unsupported claims, and other-slice defects

| Behavior | Classification | H-02 action |
|---|---|---|
| Canonical Base mainnet identity `8453` | Intended | Preserve |
| Base source `migrations/base-mainnet` | Intended | Preserve read/selection semantics |
| Base history `migration_history/base-mainnet/v1` | Intended | Preserve; never modify fixtures |
| Base blueprint identity `base` | Intended Base compatibility | Derive from profile |
| Case-insensitive canonical `base-mainnet` spelling | Intended CLI compatibility | Preserve normalization to the same canonical profile |
| Unknown labels | H-02 defect | Fail before env, account, path, connector, or verifier |
| Duplicate Base choices and inaccurate help/defaults | H-02 defect | Generate choices/help from registry and owner-selected default policy |
| Eager BaseScan key read | H-02 defect | Remove |
| Alchemy token URL construction | H-02 defect | Remove unless a separate time-bounded Base compatibility decision is approved |
| Full/sliced RPC logging | H-02 security defect | Remove; use profile/env-name-only diagnostics |
| Account loading before chain identity | H-02 critical defect | Reverse order and prove by spies |
| Missing-key public test-key fallback | H-02 critical defect | Remove |
| Safe/Ledger labels implying support | H-02 unsupported claim | Reject deliberately; do not implement a backend |
| Arbitrary history concatenation | H-02 defect | Use profile-owned paths only |
| Cross-profile history alias | H-02 invalid schema | Reject |
| Base Sepolia chain ID `84532` | Intended identity | Preserve |
| Base Sepolia migration/history operation | Unsupported current claim | No Base-mainnet borrowing; repository operations return `unsupported` |
| Ethereum labels in H-02 CLIs | Stale/unsupported claims | Remove after owner confirms no undocumented workflow |
| Local profile identity | Intended profile | Runtime chain ID must be supplied explicitly |
| Local migration repository/blueprint | Unsupported in H-02 | Do not edit `config/BluePrint.py`; no fallback |
| Dirty/latest console fork | Intended only for explicitly labeled local exploration | Separate from pinned clean evidence mode |
| Fork submission | Invalid | Always false |
| Robinhood source/history paths | Reviewed future identity | Store as proposed values; return `blocked_pending_policy`; do not create |
| Robinhood live provider/backend/fee/finality | Unresolved owner policy | `blocked_pending_policy` before env/key access |
| Robinhood verifier adapter/rates | H-07 | H-02 records provider identity and blocks verification |
| Base verifier submission/rate behavior | H-07 | H-02 blocks before key/network while preserving provider identity |
| Start/end/resume and duplicate migration IDs | H-05 | Record; do not modify |
| Broad transaction retry and positional logs | H-05 | Record; do not modify |
| Manifest mutation/atomicity/schema | H-06 | Record; do not modify |
| Etherscan/Blockscout adapter implementation | H-07 | Record; do not modify |
| Local/Base/RH blueprint content | H-03 | Record; do not modify |
| Global pytest env/fork harness | H-09 or separate test-infrastructure slice | Use a synthetic parent placeholder and isolated child environments |

## Proposed immutable network-profile registry API

The registry is the sole H-02 authority for profile identity and static
network/repository policy. It remains pure Python: no Boa import, environment
lookup, filesystem access, or network access at module import.

### Immutable types

All types are `@dataclass(frozen=True, slots=True)`. Nested collections are
tuples or frozensets; repository paths are `PurePosixPath`; there are no mutable
nested dictionaries.

```text
ProfileEnvironment = LOCAL | TEST | MAINNET
PathState = ABSENT | EXISTING | PROPOSED
VerifierProvider = UNSUPPORTED | ETHERSCAN_V2 | BLOCKSCOUT

Operation =
  PROFILE_INSPECTION
  LOCAL_RUNTIME
  REPOSITORY_READ
  MIGRATION_FORK
  MIGRATION_LIVE
  CONSOLE_EXPLORATION
  CONSOLE_EVIDENCE
  VERIFICATION

OperationOutcome =
  supported
  unsupported
  blocked_pending_policy
  invalid
```

Proposed records:

```python
NetworkIdentity(profile_id, chain_id, environment)
RpcPolicy(env_name, allowed_operations, require_chain_id_match)
RepositoryPolicy(
    blueprint_id,
    migration_dir,
    migration_state,
    history_dir,
    history_state,
)
ForkPolicy(
    require_source_chain_id_match,
    pin_required_for_evidence,
    latest_allowed_for_exploration,
    dirty_allowed_for_exploration,
    allow_submission=False,
)
VerifierPolicy(provider, adapter_id, api_key_env_name, operation_outcome)
OperationPolicy(operation, outcome, requires_rpc, requires_identity,
                requires_repository, requires_account, requires_verifier)
NetworkProfile(identity, rpc, repository, fork, verifier, operations)
ProfileAlias(alias, canonical_profile_id)
VerifiedNetworkIdentity(profile_id, operation, expected_chain_id,
                        observed_chain_id)
NetworkProfileError(code, profile_id, operation, expected_chain_id=None,
                    observed_chain_id=None, env_name=None)
```

`NetworkProfileError` stores only safe fields. Its string and representation
must never contain an RPC value, provider exception, key, account, URL
component, or environment value. Provider exceptions are replaced with stable
errors using `raise ... from None`.

### Registry constants

```python
NETWORK_PROFILES: tuple[NetworkProfile, ...]
PROFILE_ALIASES: tuple[ProfileAlias, ...]
NETWORK_PROFILE_IDS: tuple[str, ...]
```

There is no public mutable map. Five entries are defined:

| Profile | Chain ID | RPC env reference | Source/history |
|---|---:|---|---|
| `local` | Runtime-configured | None | None/None |
| `base-mainnet` | `8453` | `BASE_MAINNET_RPC_URL` | Existing Base source/history |
| `base-sepolia` | `84532` | `BASE_SEPOLIA_RPC_URL` | None/None; repository operations unsupported |
| `robinhood-mainnet` | `4663` | `ROBINHOOD_MAINNET_RPC_URL` | Proposed shared source / proposed isolated mainnet history |
| `robinhood-testnet` | `46630` | `ROBINHOOD_TESTNET_RPC_URL` | Proposed shared source / proposed isolated testnet history |

Case-folding a canonical ID is normalization, not an alias. No `eth-*`, unknown,
or blueprint label is an alias. `--chain` may remain only as an option-name
alias for `--profile`; it does not create a second profile authority.

### Public functions

```python
canonical_profile_ids() -> tuple[str, ...]

get_profile(value: str) -> NetworkProfile

validate_registry(
    profiles: tuple[NetworkProfile, ...] = NETWORK_PROFILES,
    aliases: tuple[ProfileAlias, ...] = PROFILE_ALIASES,
) -> None

operation_decision(
    profile: NetworkProfile,
    operation: Operation,
) -> OperationPolicy

require_operation(
    profile: NetworkProfile,
    operation: Operation,
) -> OperationPolicy

resolve_rpc_reference(
    profile: NetworkProfile,
    operation: Operation,
    environ: Mapping[str, str],
    explicit_rpc: str | None = None,
) -> RedactedRpc

verify_chain_identity(
    profile: NetworkProfile,
    operation: Operation,
    rpc: RedactedRpc,
    chain_id_reader: Callable[[str], int | str],
    *,
    local_chain_id: int | None = None,
) -> VerifiedNetworkIdentity

validate_fork_request(
    profile: NetworkProfile,
    *,
    evidence_mode: bool,
    block_number: int | None,
    allow_dirty: bool,
) -> None

repository_paths(
    profile: NetworkProfile,
    operation: Operation,
    *,
    root: Path,
    identity: VerifiedNetworkIdentity | None,
) -> ResolvedRepositoryPaths

manifest_path(
    profile: NetworkProfile,
    manifest_name: str,
    *,
    root: Path,
    identity: VerifiedNetworkIdentity,
) -> Path
```

`RedactedRpc` retains an endpoint only for the injected connector boundary.
Its string/representation is a stable redacted label containing only profile,
operation, and environment-variable name. Tests may supply a spy mapping and a
fake chain-ID reader. Production CLI adapters may use Titanoboa's existing
`EthereumRPC.fetch("eth_chainId", [])`, but the registry does not import Boa.

`repository_paths()` never creates a directory and never falls back. It rejects
`ABSENT`, reports `PROPOSED` as `blocked_pending_policy`, and requires verified
identity for remote operations before filesystem access.

### Deterministic test constructors and fixtures

The frozen dataclass constructors are the deterministic construction API; the
production module does not add a mutable builder or a test-account factory.
`validate_registry(profiles=..., aliases=...)` accepts an injected tuple so
tests can construct duplicate IDs, aliased histories, invalid providers, and
invalid operation tables without mutating the canonical registry.

The three owned test modules will define only test-local helpers:

```python
profile_factory(**overrides) -> NetworkProfile
spy_environment(values: Mapping[str, str]) -> SpyEnvironment
chain_id_reader(return_value: int | str) -> ChainIdReaderSpy
call_order_spies() -> CallOrderSpies
isolated_cli_environment() -> Mapping[str, str]
```

`profile_factory` starts from literal, non-secret scalar values and rebuilds
every frozen nested record; it never copies or alters a canonical object.
`SpyEnvironment` records requested variable names, never values.
`ChainIdReaderSpy` records only its call count and returns a synthetic chain
ID. `CallOrderSpies` provides env, connector, account, history, verifier, and
submission sentinels so a test can assert the exact terminal step.
`isolated_cli_environment` is an allowlist created for a child process, not a
copy of the parent environment. None is exported from `config` or imported by
production code.

### Stable error codes

At minimum:

```text
H02_PROFILE_UNKNOWN
H02_PROFILE_INVALID
H02_OPERATION_UNSUPPORTED
H02_OPERATION_BLOCKED
H02_RPC_ENV_MISSING
H02_RPC_CONNECT_FAILED
H02_CHAIN_ID_INVALID
H02_CHAIN_ID_MISMATCH
H02_LOCAL_CHAIN_ID_REQUIRED
H02_REPOSITORY_UNAVAILABLE
H02_HISTORY_ALIAS
H02_FORK_PIN_REQUIRED
H02_DIRTY_EVIDENCE_FORBIDDEN
H02_FORK_SUBMISSION_FORBIDDEN
H02_ACCOUNT_BACKEND_UNAPPROVED
H02_PRIVATE_KEY_MISSING
H02_VERIFIER_UNSUPPORTED
H02_VERIFIER_BLOCKED
```

### Operation outcome table

| Operation | local | Base mainnet | Base Sepolia | RH mainnet | RH testnet |
|---|---|---|---|---|---|
| Profile inspection/help/schema | supported | supported | supported | supported | supported |
| Explicit local runtime | supported | unsupported | unsupported | unsupported | unsupported |
| Repository read/path selection | unsupported | supported | unsupported | blocked pending H-05/H-06 | blocked pending H-05/H-06 |
| Migration fork | unsupported | supported only with injected/mock account after identity | unsupported | blocked pending H-05/account policy | blocked pending H-05/account policy |
| Migration live | unsupported | blocked pending backend/fee/finality | unsupported | blocked pending backend/provider/fee/finality | blocked pending backend/provider/fee/finality |
| Console exploration | unsupported | supported after identity | supported after identity, without repository claims | supported after identity | supported after identity |
| Console evidence | unsupported | supported only pinned and clean | unsupported | blocked pending repository/retention | blocked pending repository/retention |
| Verification | unsupported | blocked pending H-07 policy | unsupported | blocked pending H-07 | blocked pending H-07 |

`supported` here means static prerequisites for an offline or mocked operation
are present. It does not authorize an external connection.

## CLI-to-authority call-order graph

### Import and help

```text
import CLI
  -> import immutable registry
  -> derive static choice/help text
  -> return
```

There is no environment, `.env`, account, filesystem, connector, verifier, or
submission step.

### Shared remote-operation prefix

```text
parse raw CLI values without logging them
  -> get_profile(profile_id)
     [unknown stops here]
  -> validate_registry()
  -> require_operation(profile, operation)
     [unsupported/blocked/invalid stops here]
  -> validate fork mode, pin, dirty state, and submission=false
  -> resolve named RPC reference or explicit override lazily
     [missing reference stops here]
  -> injected connector reads only eth_chainId
     [provider failure becomes sanitized stable error]
  -> compare exact expected/observed chain ID
     [mismatch stops here]
  -> VerifiedNetworkIdentity
```

No account/key, live-state simulation, manifest/history, verifier, or
submission action is reachable before `VerifiedNetworkIdentity`.

### Migration

```text
shared prefix
  -> reject live mode because no approved backend/policy
     OR continue only for supported local/mock/fork operation
  -> choose explicit injected/mock account or call guarded get_account()
  -> resolve profile-owned source/history after identity
  -> construct DeployArgs and MigrationRunner
  -> configure no verifier for blocked/unsupported verifier policy
  -> enter local/fork environment
  -> existing runner semantics
```

H-02 tests stop before the runner. H-02 does not execute migrations or change
runner discovery/resume/write behavior.

### Console

```text
shared prefix for CONSOLE_EXPLORATION or CONSOLE_EVIDENCE
  -> enforce latest/dirty only for explicit local exploration
  -> enforce exact pin and clean state for evidence
  -> enter a non-submitting fork
  -> only now read the profile-owned manifest when that repository operation
     is supported
  -> only now allow local impersonation/funding
  -> start the REPL with an explicit exploration/evidence banner
```

The source endpoint is never a submission target. A profile with fork
`allow_submission=True` is invalid.

### Verification

```text
parse -> get_profile -> validate -> operation_decision(VERIFICATION)
  -> blocked/unsupported result
  -> optionally report the profile-derived manifest path without reading it
  -> return non-success
```

No key lookup, connector, manifest iteration, verifier setup, HTTP request,
sleep/poll, or submission occurs in H-02. H-07 owns the later continuation.

## Base compatibility table

| Surface | Current | Phase A disposition |
|---|---|---|
| Canonical ID | `base-mainnet` | Preserve exactly |
| Chain ID | Not centrally asserted; verifier map says `8453` | Registry says `8453`; exact runtime equality |
| Source | `migrations/base-mainnet` | Preserve exact path |
| History | `migration_history/base-mainnet/v1` | Preserve exact path and existing fixtures |
| Blueprint | `base` default independent of chain | Profile-owned `base`; override only as exact assertion |
| CLI option spelling | `--chain base-mainnet` | May remain deprecated alias of required `--profile base-mainnet` |
| Case handling | Click choice is case-insensitive in some paths | Case-fold to the same canonical ID only |
| Unknown label | Accepted and later fails | Reject; never resolve to Base |
| RPC | Vendor token interpolation or raw `--rpc` | Full URL env reference or sensitive explicit override; never log |
| Alchemy token compatibility | Implicit | Recommend remove; retain only through separate explicit, time-bounded owner decision |
| Explorer key | Eager BaseScan read in migrate; Etherscan key in verify | No eager read; verifier operation blocked before key in H-02 |
| Verifier provider | Mixed BaseScan/Etherscan assumptions | Preserve provider identity as `etherscan_v2`; H-07 owns adapter |
| Live private key | Missing key falls back publicly | Do not preserve; live operation blocked |
| Safe/Ledger | Advertised but nonfunctional | Do not preserve claim; explicit unsupported/blocked outcome |
| Manifest path | Arbitrary chain/environment concatenation | Exact profile history plus validated manifest name |
| Base Sepolia | Chain ID advertised; no source/history | Preserve identity `84532`; repository operations unsupported |
| Ethereum labels | Advertised, no current repository workflow | Remove from H-02 registry after owner confirms no undocumented use |
| Existing histories | Committed compatibility fixtures | Read-only; H-02 tests hash/inventory and never modify |

## Smallest exact file-diff plan

No file outside the H-02 ownership list is needed.

| File | Smallest planned change |
|---|---|
| New `config/network_profiles.py` | Add the pure immutable types, five profiles, operation outcomes, registry validation, lazy RPC reference, redacted errors, chain-ID proof, fork validation, and non-creating repository path resolution |
| `scripts/migrate.py` | Remove eager explorer maps and vendor URL construction; derive profile choices; validate operation before env; exact chain ID before account; reject Safe/Ledger/live unsupported paths; derive source/history from profile; never log RPC; configure no blocked verifier; preserve runner semantics |
| `scripts/console.py` | Remove import-time dotenv; derive profiles/paths; validate identity before manifest/fork state; make exploration versus evidence explicit; require pin/clean evidence; never log RPC; prohibit submission |
| `scripts/verify.py` | Stop importing migrate; derive its own profile CLI from registry; derive manifest path; return truthful blocked/unsupported status before key, manifest iteration, verifier import/use, or network |
| `scripts/utils/migration_helpers.py` | Remove dotenv call, production public-key literal, and missing-key fallback; require an explicit verified context plus injected environment/key/account; preserve unrelated transaction/ABI/manifest helpers unchanged |
| New `tests/deployment/test_network_profiles.py` | Registry/schema/outcome/identity/history/fork negative tests |
| New `tests/deployment/test_secret_handling.py` | Import/help/lazy-env/account/redaction/no-key/no-network tests |
| New `tests/deployment/test_base_profile_regression.py` | Bounded intended Base compatibility and defect-removal tests |
| This evidence record | Add Phase A checkpoint, later approved implementation/results/reviewer provenance |

The change must not touch `DeployArgs`, `MigrationRunner`, `Migration`,
`verify_etherscan`, `BluePrint`, requirements, histories, migrations,
manifests, ABIs, contracts, defaults, summary checklists, or the global test
harness. If the implementation cannot enforce the stated order without one of
those edits, it must stop and return to the owner.

Exact baseline regions that H-02 has identified but cannot own are:

| Prohibited file / baseline region | Reason it is not an H-02 edit |
|---|---|
| `config/BluePrint.py:1-162` and its remaining network dictionaries | Blueprint address/parameter completeness is H-03 |
| `scripts/utils/migration_runner.py:70-154` | Discovery, positional resume, and history-directory creation are H-05/H-06 |
| `scripts/utils/migration.py:215-235` | Manifest naming, merge, and write/promotion behavior are H-06 |
| `scripts/utils/verify_etherscan.py:5-95` and its remaining polling branch | Provider dictionaries, fallback, request, response, retry, and submission policy are H-07 |
| `tests/conf_env.py:14-29,77-96` | Global fork environment and pytest option behavior are separate test infrastructure/H-09 |
| `scripts/params/params_utils.py:29,278` | Separate parameter entrypoint retains vendor/explorer assumptions outside H-02 |

H-02 can gate calls into these regions from its owned entrypoints. It cannot
repair, generalize, or preserve them as a second profile authority.

## Complete H-02 test matrix

All tests use the disposable locked interpreter, synthetic inputs, disabled
external networking, isolated child environments, temporary paths, and
injected connectors. No test reads `.env` or committed history for writing.

### `tests/deployment/test_network_profiles.py`

| Proposed test | Proof |
|---|---|
| `test_all_five_canonical_profiles_and_chain_ids` | Exact IDs; local runtime identity; `8453`, `84532`, `4663`, `46630` |
| `test_profile_and_nested_values_are_immutable` | Frozen records, tuples/frozensets, immutable paths |
| `test_operation_table_is_total_and_uses_required_vocabulary` | Every profile/operation has exactly one valid outcome |
| `test_unknown_profile_fails_closed` | NEG-001; no env/provider/account/history spy called |
| `test_duplicate_canonical_profile_id_is_invalid` | Duplicate ID rejected deterministically |
| `test_invalid_schema_fields_fail_closed` | Invalid chain/provider/path/outcome combinations rejected |
| `test_alias_cannot_change_identity_or_repository` | Alias cannot change chain, source, history, blueprint, or verifier |
| `test_casefolded_base_id_resolves_only_to_base_mainnet` | Accepted spelling remains one canonical identity |
| `test_profiles_cannot_share_history` | NEG-032; all non-null histories unique |
| `test_robinhood_profiles_share_only_proposed_source` | Shared RH source; isolated histories |
| `test_missing_repository_does_not_fallback_or_create` | Base Sepolia/local and proposed RH paths never borrow or appear |
| `test_unsupported_and_blocked_pending_policy_are_distinct` | Deliberate absence differs from future gated operation |
| `test_fork_submission_is_always_false` | Invalid profile if true |
| `test_reproducible_fork_requires_block_pin` | Evidence without pin rejected |
| `test_latest_and_dirty_are_exploration_only` | Never committable/release evidence |
| `test_chain_id_mismatch_before_account_load` | NEG-002; wrong ID calls no next/account/history/verifier step |
| `test_matching_chain_id_allows_only_next_mocked_step` | One next-step spy call; no live execution |
| `test_local_runtime_requires_explicit_chain_id` | No guessed local identity |
| `test_profile_errors_never_render_sensitive_rpc` | Logs, exception, repr, captured output are redacted |

### `tests/deployment/test_secret_handling.py`

| Proposed test | Proof |
|---|---|
| `test_h02_modules_import_without_relevant_env` | migrate, console, verify, helper import in isolated child env |
| `test_migrate_help_without_relevant_env` | Exit zero, no env access |
| `test_console_help_without_relevant_env` | Exit zero, no env access |
| `test_verify_help_without_relevant_env` | Exit zero, no env access |
| `test_rpc_env_read_only_for_required_operation` | Spy mapping untouched for help/unsupported/blocked |
| `test_missing_rpc_env_fails_lazily` | NEG-004 exact name; local failure after profile/operation validation |
| `test_missing_private_key_never_uses_public_fallback` | Stable missing-key error; `Account.from_key` not called |
| `test_public_local_key_is_test_only` | Literal absent from `scripts/` and `config/`; production imports no test module |
| `test_injected_local_test_account_rejected_for_fork_submission` | Explicit local fixture cannot authorize source submission |
| `test_injected_local_test_account_rejected_for_live_operation` | No live-capable profile can select it |
| `test_wrong_chain_prevents_private_key_mapping_access` | Mapping/key spy untouched before identity |
| `test_rpc_components_never_appear_in_logs_exceptions_or_repr` | Synthetic username/password/path/query/fragment all absent |
| `test_user_supplied_rpc_is_fully_redacted` | Same rule for `--rpc` |
| `test_explorer_key_is_not_read_at_import_or_help` | No eager key mapping access |
| `test_unsupported_verifier_does_not_read_key` | Unsupported/blocked result before key |
| `test_process_environment_is_not_dumped_or_persisted` | Output/files contain no mapping serialization |
| `test_dotenv_is_not_loaded_by_h02_modules` | Patched loader is not called |
| `test_safe_and_ledger_reject_before_secret_access` | Deliberate unsupported outcome; no undefined sender |

### `tests/deployment/test_base_profile_regression.py`

| Proposed test | Proof |
|---|---|
| `test_base_mainnet_chain_id_is_8453` | Intended identity |
| `test_base_mainnet_source_and_history_are_preserved` | Exact two paths |
| `test_generated_profile_choices_have_no_duplicates` | Registry-derived choices |
| `test_cli_default_policy_matches_help_and_runtime` | Required profile or exact owner-approved default, consistently |
| `test_legacy_chain_option_resolves_only_to_canonical_base` | Option-name compatibility, no identity alias |
| `test_unknown_label_never_resolves_to_base` | No fallback |
| `test_base_sepolia_identity_valid_repository_unsupported` | `84532`, no Base-mainnet borrowing |
| `test_ethereum_labels_are_not_supported_profiles` | Stale CLI claims rejected |
| `test_base_manifest_path_remains_compatible` | Existing `current-manifest.json` construction |
| `test_import_and_help_need_no_base_explorer_key` | Eager read removed |
| `test_no_alchemy_token_url_construction` | No vendor interpolation |
| `test_no_test_key_fallback_regression` | Unsafe behavior not fossilized |
| `test_no_rpc_logging_regression` | Unsafe full/sliced logging not fossilized |
| `test_unknown_provider_returns_typed_outcome_not_keyerror` | Stable fail-closed result |
| `test_base_verification_route_is_truthfully_blocked` | Provider identity retained, no key/request |
| `test_committed_base_history_inventory_is_unchanged` | Hash/file inventory before and after tests |

The root pytest harness currently reads an explorer key at plugin import. H-02
tests will run the parent pytest process with the same non-secret
`local-placeholder` used by reviewed H-01 evidence, while all H-02 module/help
assertions run in child processes whose relevant environment is empty. This
does not prove the global harness secret-safe; it isolates H-02 without editing
the prohibited `tests/conf_env.py`. If reviewers require the parent process
itself to have no placeholder, a separately owned test-infrastructure change is
required and H-02 must stop.

## Public local-test key location and non-reachability proof

Recommendation: remove the current public Anvil key entirely from production
code. If a deterministic public local-test key remains useful, its only
authorized literal location is a private test fixture in
`tests/deployment/test_secret_handling.py`, for example
`_PUBLIC_ANVIL_TEST_KEY`. This evidence intentionally does not reproduce the
key value.

No CLI imports a test module. `scripts/utils/migration_helpers.py` will contain
no test-key constant and no fallback. Production account loading requires a
`VerifiedNetworkIdentity` and explicit injected key/environment input.
`MIGRATION_LIVE` is blocked for every live-capable profile; fork submission is
invalid for every profile; the test fixture is rejected for both.

Static and runtime proof:

1. scan `scripts/` and `config/` for the literal and test fixture import;
2. scan production AST imports for `tests.deployment.test_secret_handling`;
3. assert the only literal occurrence is the owned test file;
4. spy on key/environment access during wrong-chain, unsupported, blocked, and
   fork-submission cases;
5. prove only an explicit injected local-runtime test path can consume it; and
6. prove the resulting account cannot reach a live or source-submission
   operation.

There is no current production caller of `get_account()` other than
`scripts.migrate.py`; probe tests import only `load_vyper_files`. The helper
signature can therefore be narrowed inside H-02 ownership without another
production-file edit.

## Migration CLI profile/default decision

### Recommendation: explicit required profile

Require `--profile` for `scripts.migrate`. Preserve `--chain` only as a
deprecated spelling for the same required parameter if the Base owner needs
command-line compatibility. Choices and help come from
`canonical_profile_ids()`. There is no implicit Base, local, or unknown-label
fallback.

Reasons:

- the command can reach authority-bearing paths;
- the current help and runtime already disagree;
- `local` is not a complete migration repository/blueprint;
- defaulting to Base makes omission choose a production network identity; and
- a default would not solve the separately blocked account, fee, finality, or
  verifier policies.

### Owner options

1. **Required profile — recommended.** Missing profile fails before any
   environment read. `--chain base-mainnet` may remain a deprecated option
   spelling.
2. **Accurately documented `base-mainnet` default.** Preserves current runtime
   selection but retains omission risk. Unknown labels still fail, live mode
   remains blocked, and this default grants no deployment authority.
3. **`local` default — not recommended and not implementable in H-02.** The
   local repository and complete blueprint do not exist; selecting it would
   misrepresent support or require prohibited H-03/H-05 work.

The owner, deployment-tooling reviewer, security reviewer, and Base owner must
record option 1 or 2 before Phase B.

Separate Base compatibility decision: recommend removing implicit
`WEB3_ALCHEMY_API_KEY` URL construction and requiring
`BASE_MAINNET_RPC_URL`/`BASE_SEPOLIA_RPC_URL`. Retaining the legacy token form
requires an explicit time-bounded compatibility adapter, deprecation owner,
tests, and expiry. No such adapter is proposed by default.

## Local-test-account and prohibited-file issues

No public test key is needed by production H-02 code. Tests should inject an
account or key only after constructing a verified explicit local-runtime
context. There is therefore no unresolved local-test-account blocker unless
the owner requests a built-in CLI test account. Such a request must return to
security review because a production-importable literal is not acceptable.

Known prohibited-file boundaries:

- `config/BluePrint.py` is incomplete for local and has no Robinhood profile.
  H-02 marks those repository operations unsupported/blocked; H-03 owns
  blueprint content.
- `scripts/utils/migration_runner.py` and `scripts/utils/migration.py` own
  discovery, resume, directory creation, retries, and writes. H-02 gates them
  but does not change them; H-05/H-06 own fixes.
- `scripts/utils/verify_etherscan.py` contains unsafe provider/chain fallback
  and submission behavior. H-02 prevents entry; H-07 owns the adapter.
- `tests/conf_env.py` eagerly reads an explorer key and constructs vendor URLs.
  H-02 isolates child tests but does not edit the global harness.
- `scripts/params/params_utils.py` retains Base/vendor assumptions. It is not
  an H-02 entrypoint and remains an explicit later tooling residual.

The minimum H-02 implementation does not require a prohibited file. If review
requires a working local migration, a Base Sepolia migration namespace, a
Robinhood migration/history directory, a verifier request, a live account
backend, or global pytest harness repair, Phase B must not start until ownership
is amended and separately approved.

## Phase A package validation

- `HEAD`, local `rh`, and the fetched `origin/rh` reference all resolve to
  `26eb3a78668d623be40ed2b6e16f52c919906a12`.
- `git status --porcelain=v1 --branch --untracked-files=all` reports only this
  untracked evidence file on `rh-track-7-h2-network-profiles-cli`.
- `git diff --check` is clean. The required untracked-file check,
  `git diff --no-index --check /dev/null
  docs/chains/rh/evidence/network-profile-cli-implementation.md`, emits no
  whitespace diagnostic; its status is `1` because the new file differs from
  `/dev/null`.
- A sanitized literal scan found no private-key-shaped value, 40- or
  64-hex-character address/key literal, credentialed URL, or synthetic
  credential component value in this evidence.
- All 36 Markdown fence delimiters are balanced.
- The disposable environment remains mode `0700` with CPython `3.12.0` and pip
  `23.2.1`; the temporary Titanoboa cache remains absent.

## Phase A checkpoint decisions and review gate

Required before Phase B:

1. Owner selects required profile versus an accurately documented
   `base-mainnet` migration default.
2. Base owner approves removal of implicit Alchemy-token URL construction, or
   separately specifies a bounded compatibility adapter.
3. Deployment-tooling owner approves the immutable API, operation table,
   call-order graph, and exact diff plan.
4. Security reviewer approves redaction, the verified-identity-before-account
   order, removal of the production test key, test-only literal containment,
   and explicit rejection of Safe/Ledger/live paths.
5. Base owner approves the compatibility table and confirms no undocumented
   `eth-mainnet`/`eth-sepolia` CLI workflow must be retained.
6. Reviewers accept the synthetic parent pytest placeholder boundary or assign
   the prohibited global harness change to another slice.

At this checkpoint:

- no environment secret or real account was accessed;
- no external network or verifier was contacted during Phase A;
- no contract, interface, default, migration, history, manifest, ABI,
  requirement, dependency, CI, or summary checklist changed;
- no implementation or H-02 test file was created;
- no integration-worktree file was touched; and
- Phase B remains blocked pending the decisions and approvals above.

## Phase A approval provenance

On 24 July 2026, the owner approved the complete Phase A checkpoint and
authorized the exact H-02 implementation and offline validation. The recorded
decisions were:

1. require explicit `--profile`, with `--chain` only as a deprecated equivalent
   option spelling and no network default;
2. remove implicit `WEB3_ALCHEMY_API_KEY` construction and require a full RPC
   URL from the profile's named environment reference or explicit `--rpc`;
3. remove `eth-mainnet` and `eth-sepolia` as stale, unsupported CLI claims;
4. approve the immutable registry, outcome vocabulary, identity-before-
   authority order, owned-file boundary, and test matrix;
5. approve complete RPC redaction, chain-ID-before-account/history/verifier
   access, production test-key removal, test-only containment, and explicit
   Safe/Ledger/live rejection;
6. approve the Base compatibility table while leaving live migration and
   verification blocked for later slices; and
7. accept the synthetic parent-pytest placeholder without changing the
   prohibited global harness.

The approval did not authorize a live RPC, account load, signing, migration,
verification submission, deployment, governance action, push, merge, or
prohibited-file edit.

## Phase B implementation record

### Commit and exact file hashes

Implementation commit:
`4aea35225ac13dc22f6f207b3425bcb7e96d6cec`.

| File | Final SHA-256 |
|---|---|
| `config/network_profiles.py` | `1b15c1ae6f744b5ead389e6e274dbbbb2655bb3dda9bb94e6c01da517847b2eb` |
| `scripts/migrate.py` | `b711789b6efdfb85bb2b2f40ca7c5da83792ab85031a694b10fea1a1271248cc` |
| `scripts/console.py` | `e9901c58e7dd95c1ca345e52cc1cd61224bca0f23653dc4bb9bf577f918b9030` |
| `scripts/verify.py` | `334b8cee749f5716ef1b771c22b1454919778d7c2a085d9cfede327cb0794027` |
| `scripts/utils/migration_helpers.py` | `abe944556bc581b21bb162d77ce311b2d8f64c4ea5a1e1d461847f3d5f641319` |
| `tests/deployment/test_network_profiles.py` | `020ff8e5026c6baef7c015140105651593d1b76d330e4d9ff8954c21cbefe738` |
| `tests/deployment/test_secret_handling.py` | `a6d90f3744e5086c5756f8ed99d11b9bfdbe8b15bff5fb6a32318d36993addac` |
| `tests/deployment/test_base_profile_regression.py` | `6013096e8292798a289dc0d3d3ca5d51830f2a90944e88d54b3261b69688aa65` |

The commit changes exactly those eight implementation/test files: four
existing owned files and four new owned files. It contains `2,778` insertions
and `370` deletions. The implementation evidence record is a separate
follow-up deliverable.

### Implemented registry and API

`config/network_profiles.py` is the single static authority. It performs
`validate_registry()` at import, but that validation is pure: no environment,
filesystem, Boa, provider, or network access.

The implementation provides the approved frozen records and enums plus the
brief-required `live_account_backend_ids` tuple. Every canonical profile has an
empty live-backend tuple. The public constants and functions are:

```text
NETWORK_PROFILES
PROFILE_ALIASES
NETWORK_PROFILE_IDS
canonical_profile_ids
get_profile
validate_registry
operation_decision
require_operation
resolve_rpc_reference
verify_chain_identity
validate_fork_request
repository_paths
manifest_path
```

There are no value aliases. Case-folding a canonical ID is the only label
normalization. `--chain` is only an option-name alias.

The registry stores only these RPC references:

```text
BASE_MAINNET_RPC_URL
BASE_SEPOLIA_RPC_URL
ROBINHOOD_MAINNET_RPC_URL
ROBINHOOD_TESTNET_RPC_URL
```

It stores no RPC value, token, URL, account, address, fee, finality value, or
mutable runtime state. Full URL syntax is validated only after the selected
operation is supported. `RedactedRpc.__str__` and `__repr__` expose only
profile, operation, and reference name.

### Old-to-new behavior map

| Old behavior | Implemented behavior |
|---|---|
| Implicit `base-mainnet`; help claimed local | All three CLIs require `--profile`; help/runtime agree |
| Duplicate Base and advertised Ethereum choices | Five registry-derived canonical choices, no duplicates or `eth-*` values |
| Vendor token interpolated into a URL | Full URL from named `*_RPC_URL` reference or sensitive `--rpc` |
| Eager BaseScan/Etherscan key reads | No owned module reads an explorer key at import/help; H-02 verification stops before key access |
| Unknown label reached account and `KeyError` | Click/registry rejection before environment, account, path, provider, or verifier |
| No runtime chain proof | Injected reader obtains `eth_chainId`; exact equality precedes account/history/fork state |
| Public production test-key fallback | Literal and fallback removed; missing account key returns `H02_PRIVATE_KEY_MISSING` |
| Safe/Ledger implied support | `H02_ACCOUNT_BACKEND_UNAPPROVED` before RPC or secret access |
| Live migration path existed | Every live migration outcome is unsupported or blocked; no live Boa environment branch remains |
| Arbitrary history concatenation | Profile-owned `PurePosixPath` values; optional environment is equality-only |
| Full/sliced RPC logs and provider exceptions | Stable redacted messages; raw URL never enters logs/errors/reprs |
| Console always dirty/latest | Exploration is explicitly labeled; evidence requires a positive pin and clean fork |
| Console could read manifest before identity | Exact chain proof precedes repository resolution and manifest parsing |
| Verify imported migrate and submission adapter | Independent registry selection; truthful blocked/unsupported error before adapter/key/request |
| Base missing manifest could become empty console | Expected Base manifest read/parse failure is fail-closed |

The migration runner's discovery/resume/write behavior remains unchanged and
is reachable only for the supported Base-mainnet exploration fork after
profile, operation, RPC, chain identity, and account checks. The CLI labels
that output non-pinned fork results as exploration-only, not release evidence.

### Implemented operation disposition

The approved Phase A operation table is implemented. Important terminal
states:

- `local` supports explicit `LOCAL_RUNTIME` identity only; H-02 CLIs do not
  infer a migration repository for it;
- Base mainnet preserves chain `8453`, blueprint `base`, source
  `migrations/base-mainnet`, and history
  `migration_history/base-mainnet/v1`;
- Base Sepolia preserves chain `84532`, supports identity-checked console
  exploration without a repository claim, and rejects repository operations;
- both Robinhood profiles preserve reviewed identities and proposed,
  non-aliasing histories while repository/live/evidence/verification actions
  remain blocked pending policy; and
- verification submission is unreachable for every profile.

### Account and call-order proof

`get_account()` now requires a `VerifiedNetworkIdentity` and operation. The
ordinary path reads exactly `${ACCOUNT}_PRIVATE_KEY` only for
`MIGRATION_FORK`; missing or invalid material produces a sanitized typed error
and no fallback. Its explicit-key path additionally requires
`local_test_only=True`, profile `local`, and `LOCAL_RUNTIME`.

Spies prove both migration and console wrong-chain cases terminate after the
chain-ID reader. They do not call account, repository/manifest, fork,
verifier, or submission sentinels. Matching identity permits only the next
mocked step in the unit proof.

### Public local-test-key correction

The implementation removed the public Anvil key from
`scripts/utils/migration_helpers.py`. During the first containment test, the
same already-public literal was discovered in the pre-existing, prohibited,
test-only fixture `tests/tokens/test_signatures.py:49`.

H-02 did not edit that file. The H-02 test constructs the public value from
separate source fragments, uses it only with an explicit verified `local` /
`LOCAL_RUNTIME` context, and proves rejection for both Base fork and Base live
contexts. Repository-wide static proof shows:

- the one contiguous literal remains only in
  `tests/tokens/test_signatures.py`;
- no literal occurs under `config/` or `scripts/`; and
- no production AST imports either that test module or the H-02 secret test.

This is a corrected test-only location record, not a production blocker or a
request to modify another owner's test.

## Negative-test mapping

| Validation case | Exact implemented test |
|---|---|
| NEG-001 unknown profile | `test_unknown_profile_fails_closed` |
| NEG-002 wrong chain | `test_chain_id_mismatch_before_account_load` |
| NEG-004 missing RPC | `test_missing_rpc_env_fails_lazily` |
| NEG-032 cross-history | `test_profiles_cannot_share_history` |
| Cross-profile identity | `test_verified_identity_cannot_select_another_profile_history` |
| Migration order | `test_wrong_chain_prevents_private_key_mapping_access` |
| Console order | `test_console_wrong_chain_prevents_manifest_and_fork` |
| Test-key containment | `test_public_local_key_is_test_only` and the explicit local/rejection cases |
| RPC component leakage | `test_rpc_components_never_appear_in_logs_exceptions_or_repr` |
| User RPC leakage | `test_user_supplied_rpc_is_fully_redacted` |
| Import/help keylessness | module/help and Base explorer-key subprocess cases |
| Base compatibility | all 22 cases in `test_base_profile_regression.py` |

The three owned modules contain 68 selected cases: 21 registry, 25 secret and
call-order, and 22 Base regression cases.

## Phase F validation

### Isolated runtime and launcher

All Python validation used:

```text
/private/tmp/rh-h02-cpython312.pQexIu/venv/bin/python
Python 3.12.0
pip 23.2.1
```

The Phase B compiler cache was:

```text
variable: RH_H02_BOA_CACHE_DIR
path: /private/tmp/rh-h02-phaseb-titanoboa.i5QcMX
mode: 0700
```

The cache was removed after final validation and verified absent. It is
regenerable and contained compiler artifacts only. The disposable locked
environment remains because Gate 1/Gate 2 may require the exact runtime; it
must be removed and its absence recorded when H-02 no longer needs it.

The exact H-02 launcher was:

```bash
env -u BASESCAN_API_KEY -u WEB3_ALCHEMY_API_KEY -u TEST_PRIVATE_KEY \
  -u BASE_MAINNET_RPC_URL -u BASE_SEPOLIA_RPC_URL \
  -u ROBINHOOD_MAINNET_RPC_URL -u ROBINHOOD_TESTNET_RPC_URL \
  -u DEPLOYER_PRIVATE_KEY \
  ETHERSCAN_API_KEY=local-placeholder \
  PYTHON_DOTENV_DISABLED=1 PYTHONPATH=. \
  RH_H02_BOA_CACHE_DIR=/private/tmp/rh-h02-phaseb-titanoboa.i5QcMX \
  /private/tmp/rh-h02-cpython312.pQexIu/venv/bin/python -c \
'import os; from boa.interpret import set_cache_dir; cache_dir = os.environ.pop("RH_H02_BOA_CACHE_DIR"); set_cache_dir(cache_dir); import pytest; raise SystemExit(pytest.main(<ARGUMENTS>))'
```

For H-01, S1, S2, collection, and the full suite, the same command explicitly
added `-u PYTHON_DOTENV_DISABLED` and omitted
`PYTHON_DOTENV_DISABLED=1`, because H-01 itself tests dotenv behavior.

### Exact final results

Every pytest argument list below also included `-q`, `-p`, and
`no:cacheprovider`.

| Command-specific arguments | Result |
|---|---|
| `--basetemp=/private/tmp/rh-h02-final-network tests/deployment/test_network_profiles.py` | `21 passed, 3 warnings in 0.04s` |
| `--basetemp=/private/tmp/rh-h02-final-secret tests/deployment/test_secret_handling.py` | `25 passed, 3 warnings in 4.61s` |
| `--basetemp=/private/tmp/rh-h02-final-base tests/deployment/test_base_profile_regression.py` | `22 passed, 3 warnings in 5.19s` |
| `--basetemp=/private/tmp/rh-h02-final-combined` plus all three H-02 file paths | `68 passed, 3 warnings in 9.56s` |
| `--basetemp=/private/tmp/rh-h02-final-h01 tests/deployment/test_dependency_gate.py` | `16 passed, 3 warnings in 1.44s` |
| `--basetemp=/private/tmp/rh-h02-final-s1 tests/clock/test_clock_profiles.py` | `57 passed, 3 warnings in 26.49s` |
| `--basetemp=/private/tmp/rh-h02-final-s2 tests/inventory/test_block_clock_inventory.py` | `60 passed, 3 warnings in 25.17s` |
| `--collect-only --basetemp=/private/tmp/rh-h02-final-collect` | `2,806/2,948 collected, 142 deselected in 1.23s` |
| `--basetemp=/private/tmp/rh-h02-final-full` | `2,806 passed, 142 deselected, 3 warnings in 304.11s` |

The three warnings in every cache-launched run were the same non-fatal
`PytestAssertRewriteWarning` notices for `_hypothesis_globals`, `hypothesis`,
and `boa`, which the cache-setting launcher imports before pytest. No warning
was suppressed. There were no skips or xfails.

Final direct import/help checks used the disposable interpreter with all
explorer, vendor-token, profile RPC, deployer key, and test-key variables
absent plus `PYTHON_DOTENV_DISABLED=1`. All five H-02 modules imported and all
three `--help` commands exited zero without a network or key read.

The repository contains no pre-existing focused migration, console, or
verification CLI tests beyond the new H-02 modules. Existing `pytest.base`
tests require external fork configuration and were not separately invoked;
they remained deselected by the unchanged local full-suite harness, as in the
accepted baseline. The 22 offline Base regression tests are the authorized
Base compatibility gate.

### Corrected non-final diagnostics

Two non-final failures were caused by validation assumptions, not implementation
regressions:

1. The first secret suite reported `1 failed, 23 passed in 4.52s` because its
   containment assertion assumed the public key did not already occur in
   `tests/tokens/test_signatures.py`. The test was corrected without editing
   that prohibited file; the final suite is 25/25.
2. The first H-01 rerun reported `1 failed, 15 passed in 1.51s` because the
   launcher incorrectly set `PYTHON_DOTENV_DISABLED=1` while H-01 was testing
   `load_dotenv`. Explicitly unsetting that H-02-only variable restored the
   untouched H-01 gate to 16/16.

An earlier pre-hardening full run passed `2,802` tests with `142` deselected in
`306.21s`. After adding malformed-chain-ID and fail-closed-manifest checks plus
cross-profile and console-order proofs, the definitive result is the
`2,806`-test run above.

## Ownership and residual risk after implementation

No prohibited file changed. In particular, H-02 did not edit contracts,
interfaces, migrations, histories, manifests, generated artifacts,
`config/BluePrint.py`, runner/migration/verifier helpers, requirements, S1,
S2, `tests/conf_env.py`, parameter tooling, authority documents, or
`docs/chains/rh-summary.md`.

Remaining risk is deliberately fail-closed:

- H-03 owns complete local and Robinhood blueprints;
- H-05 owns discovery, migration IDs, resume, execution plans, and ambiguous
  retry behavior;
- H-06 owns manifest schema, atomic writes, and promotion;
- H-07 owns provider adapters, explorer keys, rates, responses, and
  verification submission;
- the global pytest harness still eagerly reads its synthetic parent
  placeholder and remains separate test-infrastructure/H-09 work;
- `scripts/params/params_utils.py` retains out-of-scope Base/vendor assumptions;
- no live account backend, provider, fee, finality, or release confirmation is
  approved; and
- Base fork migration remains explicitly exploration-only and must not be
  presented as release evidence.

## Reviewer-gate status

Gate 1 is open. An independent deployment-tooling/security/Base reviewer must
inspect every changed line and the full evidence, then record approval or
findings. This implementation agent's audit is not independent Gate 1
provenance.

Gate 2 has not begun. There has been no refresh onto a later `rh`, remote
ahead/behind check, virtual merge, push, or integration-readiness approval.
Neither gate authorizes merge.

The following completion items are eligible for independent owner/reviewer
closure:

- exact H-02 ownership boundary;
- five canonical immutable profiles;
- fail-closed unknown/unsupported/blocked states;
- runtime identity before account/history/fork access;
- removal of implicit test key, vendor URL, eager explorer read, and RPC
  leakage;
- intended Base path compatibility;
- blocked Robinhood live/verifier operations; and
- targeted, H-01, S1, S2, collection, and full-suite validation.

H-02 is not merge-ready until Gate 1 and Gate 2 close. No secret, live RPC,
real account, external connection, external write, signing, migration,
verification submission, deployment, governance action, push, merge, or
integration-worktree edit occurred.
