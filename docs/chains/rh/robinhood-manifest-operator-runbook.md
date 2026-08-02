# Robinhood Manifest v2 macOS/APFS Operator Runbook

> **31 July 2026 currentness overlay:** Ready to begin deployment preparation
> from current configuration-source baseline `e4473ce6485888f1b747761a5ee8693443108877`,
> tree `33b705690007bda9b11900b5775bd9230e79f09e`. H-06 qualifies a candidate
> operator/storage class only. It is not final operator, machine, volume,
> migration, deployment, production publication, configuration, activation, or
> release authorization. The deployment owner must bind the frozen release
> candidate, intended operator machine, and selected volume before any future
> run. No Robinhood migration has been executed and no history has been
> promoted. Repository configuration is prepared and consistent;
> production/onchain configuration has not occurred. Begin from the canonical
> [`deployment-owner-quickstart.md`](deployment-owner-quickstart.md) and use
> this runbook only at the operator-binding phase.

> **1 August 2026 transaction-executor overlay:** The unstaged executor
> candidate on parent `25c0d58e1243449276e4ac4cae8d7abb8272f376`, tree
> `2dd9ddb30c1bc09cc82b8ed1ffd67949a20a4abf`, extends manifest-v2 execution
> evidence with typed action outputs, per-contract temporary-governance
> relinquishment receipts, and exact retained-governance sets. The generated
> candidate schema is 34,204 bytes with SHA-256
> `5579f3a505844ba0b83ccf9023e485b3c6f8524b2789ea2d32a0f8d227ed3483`.
> This extension is awaiting independent review and integration. The historical
> qualification hash block below is intentionally unchanged and therefore
> fails closed against these candidate bytes; do not operate the candidate
> until a new frozen commit/tree and reviewed H-06 byte binding replace it.

## Purpose and authority

This runbook qualifies and operates the H-06 manifest-v2 filesystem protocol
on its initially supported platform: a trusted macOS operator using a
mode-`0700` state root on local APFS.

This document is procedural guidance. It does not authorize Robinhood
history/current/attempt/lock creation, migration execution, production
publication, deployment, configuration, promotion, account or key access,
signing, transaction submission, or release. Obtain separate written authority
for the exact environment and action before using a real state root.

The historical qualification was performed against:

- implementation base commit
  `cca60bb85c772c977bb9fb62c1c6c5252c3a1438`;
- implementation base tree
  `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381`;
- branch `rh-track-7-h6-macos-operator-qualification` for the uncommitted
  documentation candidate.

Those are historical qualification identities, not perpetual required values
for future `HEAD` or `rh`. This runbook separately binds the qualified
implementation/schema/test/dependency bytes and requires an operator to supply
the exact frozen release-candidate commit and tree.

The companion qualification record is
[evidence/robinhood-manifest-macos-release-qualification.md](evidence/robinhood-manifest-macos-release-qualification.md).

## Supported claim

The supported operating class is deliberately narrow:

- macOS on local, journaled, internal, non-removable APFS;
- one trusted operator, with the state root owned by the effective user and
  mode `0700`;
- immutable publication only through
  `renameatx_np(..., RENAME_EXCL)`;
- canonical temporary bytes written to a held regular mode-`0600` inode,
  file `fsync`, `F_FULLFSYNC`, reread and validation, exclusive publication,
  directory `fsync`, final `F_FULLFSYNC`, and identity revalidation;
- generated `current-manifest.json` promotion only under the manifest lock,
  after complete-chain and stale-prior validation, using the one isolated
  `os.replace` call in the current-index path.

Durable success is strong best-effort durability on the qualified stack, not
a guarantee against power loss, lying firmware, defective hardware, or media
failure.

Unsupported and fail-closed:

- Linux and every non-macOS platform;
- non-APFS filesystems;
- synced folders, network filesystems, container overlays, tmpfs, and
  removable storage;
- paths under `/Volumes`, or with `Dropbox`, `iCloud Drive`,
  `Mobile Documents`, or `OneDrive` components;
- symlinked roots, wrong-owner roots, and roots not exactly mode `0700`;
- rename, copy, link, unlink-before-rename, raw-syscall, Linux-adapter, or
  cross-filesystem publication fallbacks.

Same-UID or root malicious interference, loader interposition, lying firmware,
defective hardware, and media failure are outside the supported claim.

## Prerequisites

The operator must have:

1. A clean isolated worktree at the exact separately reviewed frozen release
   commit and tree.
2. macOS, arm64 or the independently reviewed target architecture, and a
   local APFS volume.
3. CPython with the locked repository requirements and pytest available.
4. Permission to create private temporary qualification roots under
   `/private/tmp`.
5. Local loopback socket permission for the repository pytest session fixture.
6. Network read access to verify live `origin/rh` when running from
   authoritative `rh`.
7. Independent confirmation that the release candidate descends from the
   historical qualification base and retains every bound input byte.
8. Separate action authority before selecting or touching a real state root.

Use a normal trusted login session. Do not run qualification through a synced
folder, network mount, container overlay, temporary RAM filesystem, removable
disk, injected loader, or untrusted wrapper.

## Hard stop conditions

Stop before any write if any of the following is true:

- the exact frozen release commit or tree has not been supplied;
- `HEAD` or its tree differs from the supplied release identity;
- when running from authoritative `rh`, local, cached, or live `rh` differs
  from the supplied release commit;
- the historical qualified implementation base is not an ancestor of the
  release commit;
- any bound implementation, schema, test, requirement, or Python-selection
  byte differs from the qualified hash;
- relevant platform policy, durability sequence, native adapter, fallback
  prohibition, test count, expected result, threat model, or supported storage
  class has changed since qualification;
- the worktree is not clean at the supplied release commit;
- a third repository path is needed;
- the platform is not macOS or the filesystem is not APFS;
- storage is not local, journaled, internal, fixed/non-removable, writable,
  and owner-enabled;
- the selected root is missing, relative, symlinked, wrong-owner, not exactly
  mode `0700`, or under a prohibited/synced/removable location;
- any qualification test skips, xfails, xpasses, errors, or fails;
- the native `renameatx_np` lane cannot run without skip;
- an unexpected file, lock identity, hash, prior pointer, current index, or
  temporary object is present;
- an outcome is ambiguous, corrupt, stale, or cannot be classified;
- the task would require credentials, RPC access, signing, submission,
  migration, deployment, production state, or release authority.

Do not change the implementation, tests, dependencies, schema, `.gitignore`,
or filesystem strategy to bypass a stop.

## Bind the historical base, qualified bytes, and release candidate

The eventual release-candidate commit and tree are not known by this
qualification document. They must be supplied after Wave 1 and all other
authorized source movement are complete and the exact release candidate is
frozen and separately reviewed.

Run from a clean worktree at that frozen release candidate. Set
`RUN_FROM_AUTHORITATIVE_RH=yes` only when local `rh`, cached `origin/rh`, and
live `origin/rh` are expected to be the authoritative frozen release tip. Set
it to `no` for a separately reviewed pre-integration release branch; that mode
does not make any claim about authoritative `rh`.

```sh
set -eu
umask 077

REPO=$(git rev-parse --show-toplevel)
QUALIFIED_IMPLEMENTATION_BASE=cca60bb85c772c977bb9fb62c1c6c5252c3a1438
QUALIFIED_IMPLEMENTATION_BASE_TREE=161fb828f3bbf4cb12596a5dfaf6c9bf1e153381

: "${EXPECTED_RELEASE_COMMIT:?supply the frozen reviewed release commit}"
: "${EXPECTED_RELEASE_TREE:?supply the frozen reviewed release tree}"
: "${RUN_FROM_AUTHORITATIVE_RH:?set to yes or no}"

test "${#EXPECTED_RELEASE_COMMIT}" -eq 40
test -z "$(printf '%s' "$EXPECTED_RELEASE_COMMIT" | tr -d '0-9a-f')"
test "${#EXPECTED_RELEASE_TREE}" -eq 40
test -z "$(printf '%s' "$EXPECTED_RELEASE_TREE" | tr -d '0-9a-f')"

git cat-file -e "$QUALIFIED_IMPLEMENTATION_BASE^{commit}"
git cat-file -e "$EXPECTED_RELEASE_COMMIT^{commit}"
git cat-file -e "$EXPECTED_RELEASE_TREE^{tree}"

test "$(git rev-parse "$QUALIFIED_IMPLEMENTATION_BASE^{tree}")" = \
  "$QUALIFIED_IMPLEMENTATION_BASE_TREE"
test "$(git rev-parse HEAD^{commit})" = "$EXPECTED_RELEASE_COMMIT"
test "$(git rev-parse HEAD^{tree})" = "$EXPECTED_RELEASE_TREE"
test "$(git rev-parse "$EXPECTED_RELEASE_COMMIT^{tree}")" = \
  "$EXPECTED_RELEASE_TREE"
test -z "$(git status --porcelain=v1)"

git merge-base --is-ancestor \
  "$QUALIFIED_IMPLEMENTATION_BASE" \
  "$EXPECTED_RELEASE_COMMIT"

case "$RUN_FROM_AUTHORITATIVE_RH" in
  yes)
    test "$(git rev-parse --verify refs/heads/rh)" = \
      "$EXPECTED_RELEASE_COMMIT"
    test "$(git rev-parse --verify refs/remotes/origin/rh)" = \
      "$EXPECTED_RELEASE_COMMIT"
    LIVE_RH=$(git ls-remote --heads origin refs/heads/rh | awk '{print $1}')
    test "$LIVE_RH" = "$EXPECTED_RELEASE_COMMIT"
    ;;
  no)
    ;;
  *)
    printf '%s\n' "RUN_FROM_AUTHORITATIVE_RH must be yes or no" >&2
    exit 1
    ;;
esac

while IFS=' ' read -r expected_sha expected_blob file; do
  test -f "$file"
  actual_sha=$(shasum -a 256 "$file" | awk '{print $1}')
  actual_blob=$(git hash-object -- "$file")
  release_blob=$(git rev-parse "${EXPECTED_RELEASE_COMMIT}:$file")
  test "$actual_sha" = "$expected_sha"
  test "$actual_blob" = "$expected_blob"
  test "$release_blob" = "$expected_blob"
done <<'QUALIFIED_H06_INPUTS'
19ce1868e4fbff170ab0b8256dcb5634e2554ab1ba3f08be87ea43100227d41a 289a301148411a427f629ed9d6380649a5e8973a docs/chains/rh/schemas/deployment-manifest-v2.schema.json
84c38a4975454ccec77607c3987f459917ce23794d355396cbdb01ee6c398c82 8463c510e4b1fa0b9a2690e62f9260af826e1751 scripts/utils/json_file.py
386c0988481ca451e18b77c43ed106ef9466970cbde0c369c8bfbc2060609b5d 68aaf0763bfe607d4cd786e7245c9544ebdd7299 scripts/utils/manifest_schema.py
58733561aae7c0a599de86f64a1f20529c61a92943d7c29408fd7501e915d1ba 5d3448ec84ed4c5be1d67139586a18bb3d5b3f35 scripts/utils/migration.py
74380b7c786fe2cecf47eb3d8c18a1a009dcb9542a4a5f32650a1e0555739c0c 4898c47e78a29ba1fe1fca2b1b4aaebb590ae7a5 tests/deployment/test_manifest_schema.py
63db4291df2d3193b24d6a30ec1b950d1f511c08be9bde1c35934e5270f564cb 7ae05f71fb85e6f64d77de2a203bcc4b6ce5f55f tests/deployment/test_current_manifest_promotion.py
214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010 eaf12f774a108a100696a5c77d8a9dec9617ed1e requirements.txt
7806297a8a9f8f0d0544d3ca7582c68fb19d6ed3e6dc3bc19a48545c73a45e52 3655f82abce9cfa0792853d53a5549be75a355a0 .python-version
QUALIFIED_H06_INPUTS
```

Accepted result: every command exits `0`, and
`git status --porcelain=v1` prints nothing. In authoritative-`rh` mode, missing
live network proof is a stop, not permission to rely on a stale cached ref.

Ancestry alone is insufficient. Exact hashes without ancestry are also
insufficient. Carry-forward requires both:

1. the historical qualified implementation base is an ancestor of the exact
   frozen release commit; and
2. every bound input above has the exact qualified SHA-256 and Git blob in
   both the clean worktree and the release commit.

A documentation-only descendant may retain the technical qualification only
when those conditions hold and independent review confirms that the relevant
platform policy, durability sequence, native adapter, fallback prohibition,
test count and expected results, threat model, and supported storage class are
unchanged.

Any change to a bound byte or to one of those reviewed semantics invalidates
carry-forward and requires fresh qualification plus independent review. This
candidate is not a perpetual qualification of every descendant. A later
documentation commit is evidence identity, not the historical implementation
qualification base and not automatically the final release candidate.

## Create private qualification roots

These are disposable qualification roots, not Robinhood state roots:

```sh
QUAL_A=$(mktemp -d /private/tmp/h06-macos-qual-a.XXXXXX)
QUAL_B=$(mktemp -d /private/tmp/h06-macos-qual-b.XXXXXX)
chmod 0700 "$QUAL_A" "$QUAL_B"

test "$(stat -f '%Lp' "$QUAL_A")" = 700
test "$(stat -f '%Lp' "$QUAL_B")" = 700
test "$(stat -f '%u' "$QUAL_A")" = "$(id -u)"
test "$(stat -f '%u' "$QUAL_B")" = "$(id -u)"
test "$(stat -f '%d' "$QUAL_A")" = "$(stat -f '%d' "$QUAL_B")"
```

Do not place these roots inside the repository. Do not point them at any real
Robinhood history or current-index location.

## APFS and local-storage preflight

Exercise the implementation's actual root gate against both private roots:

```sh
PYTHONDONTWRITEBYTECODE=1 python - "$QUAL_A" "$QUAL_B" <<'PY'
import os
from pathlib import Path
import sys

from scripts.utils.manifest_schema import _validate_root_for_write

for value in sys.argv[1:]:
    directory_fd, _native = _validate_root_for_write(Path(value))
    os.close(directory_fd)
print("H06_ROOT_PREFLIGHT_OK count=2")
PY
```

Then resolve the mounted volume and inspect only the necessary storage
characteristics:

```sh
QUAL_DEVICE=$(df -P "$QUAL_A" | awk 'NR == 2 {print $1}')
QUAL_MOUNT=$(df -P "$QUAL_A" | awk 'NR == 2 {print $6}')

mount | awk -v mount_point="$QUAL_MOUNT" \
  '$2 == "on" && $3 == mount_point {print}'

diskutil info "$QUAL_DEVICE" | awk -F: '
  /File System Personality|Type \(Bundle\)|Owners|Protocol|Media Read-Only|Volume Read-Only|Device Location|Removable Media|Solid State/ {
    key=$1
    sub(/^[[:space:]]+/, "", key)
    value=substr($0, index($0, ":") + 1)
    sub(/^[[:space:]]+/, "", value)
    print key ": " value
  }'
```

Accept only all of the following:

- filesystem `APFS` / `apfs`;
- mount flags include `local` and `journaled`;
- owners enabled;
- device location internal;
- removable media fixed;
- media and volume read-only both no.

Record only these sanitized fields. Do not retain device identifiers, volume
UUIDs, serial numbers, capacity, usernames, home paths, or unrelated mounted
volumes.

## Exact qualification commands

The repository tests require a non-secret placeholder for test collection.
The placeholder is not a credential and must never be replaced by a real key
for this qualification.

The commands in this section preserve the exact procedure and historical
expected results. Do not rerun them merely to paper over a failed carry-forward
preflight. A carry-forward failure requires fresh qualification authority and
independent review.

First, run the native APFS no-replace test independently in each root:

```sh
PYTHONDONTWRITEBYTECODE=1 \
ETHERSCAN_API_KEY=local-placeholder \
python -m pytest -p no:cacheprovider \
  --basetemp="$QUAL_A/pytest-native-a" \
  -q -ra \
  tests/deployment/test_current_manifest_promotion.py::test_native_renameatx_np_no_replace_on_local_apfs_without_skip

PYTHONDONTWRITEBYTECODE=1 \
ETHERSCAN_API_KEY=local-placeholder \
python -m pytest -p no:cacheprovider \
  --basetemp="$QUAL_B/pytest-native-b" \
  -q -ra \
  tests/deployment/test_current_manifest_promotion.py::test_native_renameatx_np_no_replace_on_local_apfs_without_skip
```

Accepted result for each command: exit `0`, `1 passed`, and no skip, xfail,
xpass, warning that changes semantics, error, or failure.

Run the complete current H-06 schema/writer/reader/promotion suite:

```sh
PYTHONDONTWRITEBYTECODE=1 \
ETHERSCAN_API_KEY=local-placeholder \
python -m pytest -p no:cacheprovider \
  --basetemp="$QUAL_A/pytest-h06-complete" \
  -q -ra \
  tests/deployment/test_manifest_schema.py \
  tests/deployment/test_current_manifest_promotion.py
```

At the qualified baseline the accepted result is exit `0`, `148 passed`, and
no skips, xfails, xpasses, errors, or failures. A different collection count
requires an independent baseline review.

Safely exercise the non-APFS fail-closed branch without mounting unsupported
storage:

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
from scripts.utils.manifest_schema import ManifestError, _NativeMacOS

native = object.__new__(_NativeMacOS)

def fake_fstatfs(_fd, pointer):
    pointer._obj.f_fstypename = b"not-apfs"
    return 0

native.fstatfs = fake_fstatfs
try:
    native.require_apfs(-1)
except ManifestError as error:
    assert error.code == "H06_FILESYSTEM_UNSUPPORTED"
    print(error.code)
else:
    raise SystemExit("non-APFS mock was accepted")
PY
```

Accepted result: exit `0` and exactly
`H06_FILESYSTEM_UNSUPPORTED`.

The complete suite also proves:

- collision refusal and no overwrite;
- Linux/non-macOS rejection;
- symlink, FIFO, simulated device/socket, hardlink, and wrong-root refusal;
- exact temporary cleanup and distinct cleanup ambiguity;
- typed lock acquisition/identity/release behavior;
- publication and post-rename durability ambiguity;
- idempotent immutable replay and concurrent-writer serialization;
- complete-chain-only current promotion, stale-prior refusal, and a single
  concurrent promotion winner;
- no immutable `os.rename`, `os.link`, `os.replace`, `renameat2`, or raw
  syscall fallback; the sole `os.replace` is after
  `promote_current_index`.

## Exit status and result-code handling

For qualification commands, only shell exit `0` with the exact expected
summary is acceptable. Treat pytest exit `1` (failed tests), `2` (interrupted
or usage error), `3` (internal error), `4` (usage error), or `5` (no tests
collected) as a stop. A skip or xfail is also a stop even if pytest exits `0`.

The writer returns a `WriteResult` with a state and stable code, or raises a
sanitized `ManifestError`. Handle the principal results as follows:

| State | Stable code | Meaning | Required action |
|---|---|---|---|
| `durable` | `H06_IMMUTABLE_DURABLE` | Immutable bytes passed the reviewed publication and durability sequence | Retain; continue only under separate action authority |
| `already-present` | `H06_IMMUTABLE_ALREADY_PRESENT` | Exact immutable bytes already exist and were not rewritten | Treat as idempotent success; retain |
| `durable` | `H06_CURRENT_PROMOTED` | Generated current index passed promotion checks | Retain; verify history before any next step |
| `stale-prior` | `H06_STALE_PRIOR_IDENTITY` | Expected prior no longer matches | Stop; do not retry with a changed prior |
| `collision` | `H06_IMMUTABLE_COLLISION` | Target name exists with different bytes or won a race | Stop; never overwrite or delete the target |
| `pre-publication-failure` | `H06_TEMP_WRITE_FAILURE`, `H06_NATIVE_PUBLICATION_FAILURE`, or typed `H06_LOCK_*` | No durable success was established before publication | Stop; verify exact cleanup and read history |
| `publication-ambiguity` | `H06_PUBLICATION_AMBIGUOUS` | Publication may have occurred | Freeze the root and reconcile read-only |
| `cleanup-ambiguity` | `H06_CLEANUP_AMBIGUOUS` | Exact temporary cleanup could not be proved | Freeze the root; do not delete by pattern |
| `durability-ambiguity` | `H06_POST_RENAME_DURABILITY_AMBIGUOUS` | Immutable target exists but reviewed sync completion was not proved | Freeze the root and reconcile after restart |
| `publication-ambiguity` or `durability-ambiguity` | `H06_CURRENT_PROMOTION_AMBIGUOUS` | Generated current index may have been replaced without proved durable completion | Freeze the root and reconcile after restart |
| `final-identity-mismatch` | `H06_FINAL_IDENTITY_MISMATCH` | Final path/held-inode/byte identity did not revalidate | Incident stop; preserve evidence |

Any raised `ManifestError`, unclassified exception, or I/O error is a stop.
Never convert it to success, broaden cleanup, or substitute a fallback.

## Immutable publication and current-promotion boundaries

Immutable records and attempt records are authority-bearing history. Their
final names are content- and semantic-identity-bound. Publication never
replaces an existing final name.

`current-manifest.json` is a generated, mutable, non-authoritative index. It
may be promoted only when:

- the lock is valid and exclusively held;
- the actual current hash and both prior-index fields equal the caller's
  expected prior;
- the complete immutable chain and semantic-plan bindings validate;
- no unresolved attempt or operational temporary state exists;
- the target is the chain head;
- required actions are reconciled or complete;
- target path, record identity, profile, source commit/tree, and plan hash
  match.

Never treat current-index promotion as immutable publication, transaction
finality, migration success, deployment authority, or release authority.

### Execution failure records and bound resume

Executor action evidence records the accepted typed inputs and exact typed
outputs. Final `0900` handoff evidence additionally records, in canonical
contract order, each temporary-governance relinquishment transaction and the
exact contracts that still retain temporary governance.

If execution stops before the final handoff is complete:

1. publish only the validated failure attempt; never promote
   `current-manifest.json`;
2. preserve all earlier immutable successful-action records and every
   successful per-contract relinquishment receipt;
3. report the retained set exactly, including a valid empty set when failure
   occurs after the eleventh relinquishment but before terminal completion;
4. keep release, handoff, and authority removal incomplete; and
5. resume only with the identical profile, plan hash, source commit/tree,
   execution envelope, deployment sender, and history root.

On a bound resume, the executor restores outputs and completed relinquishments
from immutable evidence, reattaches deployed contracts by their recorded
addresses, and performs only remaining setup or relinquishment work. Any
missing, extra, conflicting, or untyped output/receipt is a stop. Never infer a
temporary-governance value or completed relinquishment from an owner, guardian,
Safe, signer, final-governance role, transaction position, or observed zero
alone.

## Durable, failed, and ambiguous outcomes

On a durable immutable result, record only the state, stable code, expected
basename, expected digest, source commit/tree, and operator-approved evidence
fields. Do not edit the record.

On a pre-publication failure:

1. Stop the writer.
2. Do not infer that no path was touched.
3. Run the read-only reconciliation below.
4. Confirm that no exact final target or `.tmp.` object remains before an
   authorized retry.
5. Retain the regular mode-`0600` `.manifest-v2.lock`; its existence is
   expected and it must not be deleted as cleanup.

On collision, stale prior, cleanup ambiguity, publication ambiguity,
durability ambiguity, final identity mismatch, or an unclassified error:

1. Freeze all writers and current promotion for the root.
2. Preserve the root, logs, stable code, expected target, and process status.
3. Do not overwrite, unlink, rename, copy into, chmod, chown, or repair any
   state-root entry.
4. Reconcile read-only after a normal restart or confirmed process exit.
5. Escalate to the owner plus independent filesystem/security and release
   reviewers.

## Restart and read-only reconciliation

After a restart or confirmed writer exit, re-run platform, storage, owner, and
mode preflight. Then supply the exact reviewed identities:

```sh
: "${STATE_ROOT:?set the exact authorized state root}"
: "${PROFILE_ID:?set robinhood-mainnet or robinhood-testnet}"
: "${CHAIN_ID:?set the reviewed expected chain ID}"
: "${PLAN_SHA256:?set the reviewed semantic-plan SHA-256}"
: "${SOURCE_COMMIT:?set the reviewed source commit}"
: "${SOURCE_TREE:?set the reviewed source tree}"

PYTHONDONTWRITEBYTECODE=1 python - \
  "$STATE_ROOT" "$PROFILE_ID" "$CHAIN_ID" "$PLAN_SHA256" \
  "$SOURCE_COMMIT" "$SOURCE_TREE" <<'PY'
import sys

from scripts.utils.manifest_schema import read_history

root, profile, chain, plan, commit, tree = sys.argv[1:]
result = read_history(profile, int(chain), plan, commit, tree, root)
print("state=" + result.state.value)
print("code=" + result.code)
print("records=" + str(len(result.records)))
print("current=" + ("present" if result.current_index is not None else "absent"))
PY
```

`read_history` does not create a lock or repair state.

- `valid` / `H06_HISTORY_VALID`: the chain and current index are internally
  consistent. This does not retroactively prove power-loss durability or
  authorize a next action.
- `absent-clean` / `H06_HISTORY_ABSENT_CLEAN`: no history is present. Retry
  only when the prior result was conclusively pre-publication and separate
  authority permits it.
- `incomplete`: stop. Do not promote current or resubmit.
- `stale`: stop. Do not rewrite current.
- `ambiguous`, including `H06_HISTORY_LOCKED`: confirm process status and
  escalate. Never delete a possibly active lock.
- `corrupt`, wrong profile, wrong chain, or wrong plan: incident stop.

An immutable target observed after an ambiguous result must be validated as
part of the full chain. Its mere existence is not permission to return success
or promote current. A current index observed after ambiguous promotion must be
validated through `read_history`; never replace it based only on timestamps.

## Exact-target-only cleanup and retention

Retain every immutable record, attempt record needed for reconciliation,
current index, and `.manifest-v2.lock` according to the approved evidence
retention policy. Do not prune content-addressed history.

The implementation may clean only the exact temporary basename it created,
and only after its regular-file and held-inode identity match. If that check
fails, it returns cleanup ambiguity and leaves the object for incident review.
No wildcard or age-based state-root cleanup is allowed.

After qualification evidence is captured and only for the disposable roots,
remove the two exact paths with prefix, ownership, and mode guards:

```sh
for qual_root in "$QUAL_A" "$QUAL_B"; do
  case "$qual_root" in
    /private/tmp/h06-macos-qual-a.*|/private/tmp/h06-macos-qual-b.*) ;;
    *) printf '%s\n' "refusing unexpected cleanup target" >&2; exit 1 ;;
  esac
  test -d "$qual_root"
  test "$(stat -f '%Lp' "$qual_root")" = 700
  test "$(stat -f '%u' "$qual_root")" = "$(id -u)"
done

rm -rf -- "$QUAL_A"
rm -rf -- "$QUAL_B"
```

Never apply this cleanup procedure to a real state root.

## Evidence sanitization

Record:

- macOS product version and build;
- architecture and tool versions;
- sanitized APFS/local/journaled/internal/fixed/read-write/owners-enabled
  characteristics;
- root mode and whether owner equals the effective user;
- historical implementation-base commit/tree, frozen release commit/tree, and
  bound file hashes;
- exact commands, exit status, counts, stable codes, and limitations.

Do not record:

- usernames, home-directory paths, numeric device identifiers, UUIDs, serial
  numbers, or unrelated mount entries;
- secrets, real API keys, accounts, addresses tied to an operator, endpoints,
  private keys, mnemonics, signatures, transactions, or provider output;
- raw environment dumps, full `diskutil` output, or unfiltered process lists.

Use labels such as `$REPO`, `$QUAL_A`, `$QUAL_B`, `$STATE_ROOT`, and
`$QUAL_DEVICE` in retained evidence.

## Abort and escalation

Abort and preserve evidence for any release-identity drift, base-ancestry
failure, bound-byte mismatch, reviewed-policy change, unsupported storage,
permission mismatch, unexpected object, collision, stale prior, lock
ambiguity, cleanup ambiguity, publication ambiguity, durability ambiguity,
final identity mismatch, corruption, skipped test, or changed test count.

Escalation must include the stable code, expected basename/digest, source
commit/tree, sanitized storage tuple, exact command and exit status, and a
statement of what was not done. It must not include credentials or unnecessary
host identity.

After the exact release candidate is frozen and the corrected source-binding
preflight above passes, run the storage/root preflight on the actual intended
operator machine against the selected intended state volume. The final binding
from the qualified candidate operator/storage class is then one explicit owner
confirmation:

The intended state root must already exist under separate authority. This
read-only binding preflight opens it through the implementation's exact gate
and displays only the storage fields required for owner confirmation:

```sh
: "${STATE_ROOT:?set the exact authorized intended state root}"

PYTHONDONTWRITEBYTECODE=1 python - "$STATE_ROOT" <<'PY'
import os
from pathlib import Path
import sys

from scripts.utils.manifest_schema import _validate_root_for_write

directory_fd, _native = _validate_root_for_write(Path(sys.argv[1]))
os.close(directory_fd)
print("H06_INTENDED_STATE_ROOT_PREFLIGHT_OK")
PY

STATE_DEVICE=$(df -P "$STATE_ROOT" | awk 'NR == 2 {print $1}')
STATE_MOUNT=$(df -P "$STATE_ROOT" | awk 'NR == 2 {print $6}')

mount | awk -v mount_point="$STATE_MOUNT" \
  '$2 == "on" && $3 == mount_point {print}'

diskutil info "$STATE_DEVICE" | awk -F: '
  /File System Personality|Type \(Bundle\)|Owners|Protocol|Media Read-Only|Volume Read-Only|Device Location|Removable Media|Solid State/ {
    key=$1
    sub(/^[[:space:]]+/, "", key)
    value=substr($0, index($0, ":") + 1)
    sub(/^[[:space:]]+/, "", value)
    print key ": " value
  }'
```

Apply the same acceptance rules as the earlier APFS/local-storage preflight.
Do not retain the device value, raw `diskutil` output, or unrelated mount
entries.

> The intended operator machine and selected state volume satisfy the
> qualified macOS/APFS class and are approved for the separately authorized
> action.

The confirmation is invalid if made on a substitute machine or volume, before
the release commit/tree is frozen, or without the corrected preflight. It does
not itself grant deployment or release authority.

## Explicit non-authorizations

This runbook and its qualification evidence do not authorize:

- creating real Robinhood history, attempt, current, temporary, or lock state;
- publication or current promotion in production;
- migration, configuration, deployment, release, or rollback;
- signing, submission, account/key access, RPC/provider access, or transaction
  activity;
- changing the H-06 implementation, schema, tests, dependencies, historical
  evidence, `.gitignore`, or fallback policy;
- Linux support or qualification;
- treating ancestry, byte hashes, a documentation commit, or a later
  descendant alone as qualification carry-forward;
- treating this candidate machine as the final production operator without
  the single owner binding above.
