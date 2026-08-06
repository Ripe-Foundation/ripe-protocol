# H-06 macOS/APFS Manifest Operator Qualification Evidence

## Disposition

**Verdict: CONDITIONALLY READY**

The integrated H-06 implementation is a qualified candidate operator/storage
class for a macOS/APFS-only initial release. Native exclusive publication ran
without skip on two independently created private APFS roots, and the complete
current H-06 suite passed with no skip, xfail, xpass, error, or failure.

The verdict is conditional on one final owner confirmation binding this class
to the intended operator machine and selected state volume. This local task
cannot prove that the qualification host is the intended production operator.
It is also conditional on a future frozen release candidate satisfying both
historical-base ancestry and exact bound-input byte checks.

**Release gate: not authorized by this task.** Independent Gate 1/release
review, the final owner binding, and separate release authority remain
required. No real Robinhood history/current/attempt/temporary/lock state,
production publication, current promotion, migration, deployment,
configuration, signing, submission, account/key access, or release occurred.

## Authorized scope

The work was limited to:

1. local, non-production qualification using private mode-`0700` roots outside
   the repository; and
2. exactly these two new documentation files:
   - `docs/chains/rh/robinhood-manifest-operator-runbook.md`;
   - `docs/chains/rh/evidence/robinhood-manifest-macos-release-qualification.md`.

No H-06 implementation, schema, test, dependency, historical Phase A
evidence, `.gitignore`, or other repository file was modified.

Qualification worktree:

- branch `rh-track-7-h6-macos-operator-qualification`;
- isolated worktree path retained as `$REPO` to avoid storing a username or
  home-directory detail;
- historical controlling local/cached/live ref at qualification: `rh`.

## Historical qualification baseline

| Identity | Value |
|---|---|
| Commit | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Tree | `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381` |
| Subject | `merge(rh): add H-06 manifest publication to foundation train` |
| Parents | `f82bc7dbe6ec61682c3a3ca24dbe3f130b53b72c`, `6005805554bf1616aaf98aedca3a15a6167de558` |
| Local `rh` | exact commit match |
| Cached `origin/rh` | exact commit match |
| Live `origin/rh` | exact commit match |
| Initial isolated worktree | clean |

Local, cached, and live identities were checked before the worktree was
created. The created worktree's `HEAD` and tree were rechecked before
qualification. These rows record what was true when qualification ran; they do
not require future `HEAD` or `rh` to remain at this historical commit.

## Relevant implementation, schema, test, and runner hashes

All values are from the historical qualification baseline before
documentation edits.

| Path | SHA-256 | Git blob | Bytes | Lines |
|---|---|---|---:|---:|
| `docs/chains/rh/schemas/deployment-manifest-v2.schema.json` | `19ce1868e4fbff170ab0b8256dcb5634e2554ab1ba3f08be87ea43100227d41a` | `289a301148411a427f629ed9d6380649a5e8973a` | 29,490 | 1 |
| `scripts/utils/json_file.py` | `84c38a4975454ccec77607c3987f459917ce23794d355396cbdb01ee6c398c82` | `8463c510e4b1fa0b9a2690e62f9260af826e1751` | 2,326 | 89 |
| `scripts/utils/manifest_schema.py` | `386c0988481ca451e18b77c43ed106ef9466970cbde0c369c8bfbc2060609b5d` | `68aaf0763bfe607d4cd786e7245c9544ebdd7299` | 123,398 | 3,511 |
| `scripts/utils/migration.py` | `58733561aae7c0a599de86f64a1f20529c61a92943d7c29408fd7501e915d1ba` | `5d3448ec84ed4c5be1d67139586a18bb3d5b3f35` | 10,840 | 320 |
| `tests/deployment/test_manifest_schema.py` | `74380b7c786fe2cecf47eb3d8c18a1a009dcb9542a4a5f32650a1e0555739c0c` | `4898c47e78a29ba1fe1fca2b1b4aaebb590ae7a5` | 42,355 | 1,363 |
| `tests/deployment/test_current_manifest_promotion.py` | `63db4291df2d3193b24d6a30ec1b950d1f511c08be9bde1c35934e5270f564cb` | `7ae05f71fb85e6f64d77de2a203bcc4b6ce5f55f` | 43,578 | 1,414 |
| `requirements.txt` | `214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010` | `eaf12f774a108a100696a5c77d8a9dec9617ed1e` | 5,327 | 291 |
| `.python-version` | `7806297a8a9f8f0d0544d3ca7582c68fb19d6ed3e6dc3bc19a48545c73a45e52` | `3655f82abce9cfa0792853d53a5549be75a355a0` | 10 | 1 |

## Identity layers and qualification carry-forward

The package keeps five identities separate:

| Layer | Meaning | Current disposition |
|---|---|---|
| Historical qualification baseline | Commit/tree against which the native and complete H-06 tests actually ran | Fixed at `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` / `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381` |
| Qualified H-06 inputs | The eight implementation/schema/test/dependency paths and exact hashes above | Fixed; any byte change invalidates carry-forward |
| Documentation commit | Commit that will eventually contain this corrected two-file package | Not yet created; the files remain unstaged and uncommitted |
| Frozen release candidate | Exact commit/tree after Wave 1 and all other authorized source movement are complete | Not yet supplied; must be separately reviewed |
| Intended operator binding | Actual machine plus selected intended state volume | Later owner action after the release candidate is frozen |

A future documentation-only descendant may retain the bounded technical
qualification only if:

1. the historical qualification commit is an ancestor of the exact frozen
   release commit;
2. every one of the eight bound paths has both the exact qualified SHA-256 and
   Git blob in the release commit and clean worktree; and
3. independent review confirms no change to relevant platform policy,
   durability sequence, native adapter, fallback prohibition, test count,
   expected result, threat model, or supported storage class.

Ancestry alone is not sufficient. Exact input hashes without ancestry are not
sufficient. Any bound-byte or reviewed-semantic change requires fresh
qualification and independent review. The current candidate is not a
perpetual qualification of all descendants.

The corrected runbook names the historical commit
`QUALIFIED_IMPLEMENTATION_BASE` and requires the operator to supply
`EXPECTED_RELEASE_COMMIT` and `EXPECTED_RELEASE_TREE`. When run from
authoritative `rh`, it also binds local `rh`, cached `origin/rh`, and live
`origin/rh` to that supplied release commit.

## Sanitized environment tuple

No username, home-directory path, serial number, volume UUID, device
identifier, account, key, endpoint, secret, or unrelated mount entry is
retained here.

| Field | Qualified value |
|---|---|
| macOS | 26.5.2 |
| Build | 25F84 |
| Kernel class | Darwin 25.5.0 |
| Architecture | arm64 |
| Python | CPython 3.12.0 selected by the repository's pyenv environment; executable path omitted |
| pytest | 8.4.2 |
| uv | 0.11.4, Homebrew arm64 build |
| Apple clang | 21.0.0, target arm64-apple-darwin25.5.0 |
| Xcode | 26.6, build 17F113 |
| Filesystem | APFS; implementation `fstatfs` check returned `apfs` |
| Mount characteristics | local, journaled, writable, owner-enabled system data volume |
| Device class | internal, fixed/non-removable, solid-state |
| Protocol class | Apple Fabric |
| Root location | `/private/tmp` class; outside repository and known sync-root path components |
| Qualification root A | independently created; absolute directory; mode `0700`; owner matched effective user |
| Qualification root B | independently created; absolute directory; mode `0700`; owner matched effective user |
| Root relationship | same qualified local APFS volume; distinct directory identities |

The native implementation gate opened each root with no-follow directory
semantics, revalidated the root identity, loaded native macOS primitives, and
required filesystem type `apfs`.

## Command and result ledger

Commands use sanitized `$REPO`, `$QUAL_A`, `$QUAL_B`, and `$QUAL_DEVICE`
labels. The exact executable commands intended for reuse are in the companion
runbook.

| ID | Command or action | Result |
|---|---|---|
| Q-01 | `git status --short --branch`; resolve local `rh`, cached `origin/rh`, and `rh^{tree}` | Primary worktree clean; commit/tree exact |
| Q-02 | `git ls-remote --heads origin refs/heads/rh` | Initial restricted-network attempt could not resolve the host; the identical read-only command was rerun in the approved host network context and returned exact commit `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Q-03 | Create exact isolated branch/worktree at the controlling commit | Success; `HEAD` and tree exact; no third repository path used |
| Q-04 | Collect `sw_vers`, architecture, Python, pytest, uv, clang, and Xcode identities | Success; sanitized tuple above |
| Q-05 | Create `$QUAL_A` and `$QUAL_B` with `mktemp -d` under `/private/tmp`, then `chmod 0700` | Success; distinct roots; owner matched effective user |
| Q-06 | Inspect mount and storage class; call implementation APFS root gate | `apfs`, local, journaled, internal, fixed, writable, owner-enabled; raw device/UUID fields discarded |
| Q-07 | First restricted-harness native pytest attempt for A and B | Both reached collection but errored before the test because the repository-wide session fixture could not bind a loopback socket: `PermissionError: [Errno 1] Operation not permitted`; no H-06 assertion ran |
| Q-08 | Rerun native no-skip test on `$QUAL_A` in the approved host harness | Exit `0`; `1 passed in 28.53s`; no skip |
| Q-09 | Rerun native no-skip test on `$QUAL_B` in the approved host harness | Exit `0`; `1 passed in 28.45s`; no skip |
| Q-10 | Run both current H-06 test modules with repository cache disabled and basetemp under `$QUAL_A` | Exit `0`; `148 passed in 37.26s`; no skip, xfail, xpass, error, or failure |
| Q-11 | Mock only `fstatfs` filesystem name as `not-apfs`, then call `_NativeMacOS.require_apfs` | Exit `0`; exact code `H06_FILESYSTEM_UNSUPPORTED` |
| Q-12 | Hash relevant source/test/runner inputs | First shell loop used zsh's special lowercase `path` variable and consequently lost command lookup after the mock had succeeded; corrected loop used `file` and produced the exact table above |
| Q-13 | Recheck repository status and untracked files after qualification, before documentation | Clean; no repository history/current/attempt/lock/temp state |
| Q-14 | Check relative links, table shapes, fence balance, tabs/trailing whitespace, sensitive host identifiers, real-index `git diff --check`, untracked-file no-index whitespace, exact scope, and Robinhood operational-state absence | PASS; exactly the two authorized untracked files |
| Q-15 | Pre-correction candidate binding | Exact branch, historical `HEAD`/tree, two SHA-256 values, two Git blobs, combined patch hash, empty real index, and exact two untracked paths all matched the authorized correction input |
| Q-16 | Bounded source-binding correction | Documentation only; H-06 implementation/schema/tests/dependencies and operational state untouched; qualification suite intentionally not rerun |
| Q-17 | Correction-only validation | Old-to-new semantic diff reviewed; exact two-file scope and empty real index; links/tables/fences; all 10 runbook shell blocks parsed by both `sh -n` and `zsh -n`; eight embedded bindings matched evidence and current bytes; whitespace, `git diff --check`, sensitivity, and operational-state checks passed |

The loopback-fixture error in Q-07 was a harness permission boundary, not an
H-06 result. No repository content was changed to bypass it. The approved host
reruns Q-08 through Q-10 exercised the original tests unchanged.

The `diskutil` framework was unavailable in the restricted harness. The
read-only inspection was rerun in the approved host context against the
resolved mounted volume. Only the sanitized fields above were retained.

## Repeatability proof

Two independent `mktemp -d` roots were created, explicitly set to mode `0700`,
and owner-checked.

The exact native test:

`tests/deployment/test_current_manifest_promotion.py::test_native_renameatx_np_no_replace_on_local_apfs_without_skip`

ran once under each root with separate pytest base directories. Each run:

1. opened a private APFS directory with no-follow semantics;
2. loaded `_NativeMacOS`;
3. required `apfs` through native `fstatfs`;
4. wrote and synchronized two separate regular files;
5. published the first through
   `renameatx_np(..., RENAME_EXCL)`;
6. received `FileExistsError` when publishing the second to the occupied
   target;
7. verified the first bytes remained and the published inode matched the held
   first-file descriptor.

Both returned `1 passed` with no skip. The two roots were on the same
qualified APFS storage class but had independent directory identities.

## Required behavior crosswalk

| Required behavior | Proof at exact test/source |
|---|---|
| Native APFS no-skip and collision refusal | `test_native_renameatx_np_no_replace_on_local_apfs_without_skip`; repeated on A and B |
| Exact durability sequence and final identity | `test_immutable_writer_exact_durability_order_and_identity` |
| Pre-publication fault cleanup | `test_prepublication_faults_never_expose_partial_canonical_file`; direct write/read/fsync/full-fsync failure tests |
| Collision never overwrites | `test_direct_mismatching_native_collision_never_overwrites` |
| Symlink and non-regular refusal | source-swap test for FIFO/symlink/regular replacement; simulated device/socket test; root/lock/immutable-target symlink and hardlink tests |
| Unsupported filesystem | safe Q-11 mock returned `H06_FILESYSTEM_UNSUPPORTED` |
| Linux fail-closed | `test_linux_and_non_macos_platforms_fail_closed` returned the expected exception in Q-10 |
| No Linux adapter or publication fallback | `test_immutable_writer_has_no_fallback_and_current_replace_is_isolated` asserts no immutable `os.rename`, `os.link`, `os.replace`, `renameat2`, or raw syscall; only one `os.replace`, after current promotion begins |
| Publication ambiguity | `test_post_publish_fault_is_truthful_publication_ambiguity` |
| Durability ambiguity | direct directory-fsync fault and post-rename sync-fault tests |
| Cleanup ambiguity and exact object preservation | direct unlink-failure, prepublication-cleanup-failure, and source-identity replacement tests |
| Lock behavior | acquisition failure, unlock failure, symlink/hardlink identity, held-lock reader ambiguity, and concurrent-writer tests |
| Immutable idempotency | exact-existing-record test retains inode, timestamp, and bytes |
| Current promotion boundary | complete-chain success; incomplete, failed, pending, and unreconciled refusal; stale-current refusal |
| Concurrent current promotion | exactly one durable winner and one stale-prior result |
| Current ambiguity | post-replace and directory-sync fault tests return `H06_CURRENT_PROMOTION_AMBIGUOUS` |

Q-10 executed every test in both modules, including all parametrized fault and
mutation cases, and reported 148 passes.

## Immutable and current-index findings

The qualified immutable path is:

1. schema, canonical-byte, semantic-plan, self-hash, and source Git identity
   validation;
2. absolute same-owner mode-`0700` root validation;
3. macOS native primitive load and APFS `fstatfs` validation;
4. valid mode-`0600` regular lock plus exclusive `flock`;
5. full-chain, prior, attempt, current, and operational-state validation;
6. same-directory exclusive temporary creation;
7. complete write, file `fsync`, `F_FULLFSYNC`, reread, canonical parse, and
   held-inode identity checks;
8. native `renameatx_np(..., RENAME_EXCL)` only;
9. directory `fsync`, final `F_FULLFSYNC` on the held published inode, and
   final path/inode/link-count/bytes/hash validation.

There is no rename/copy/link/unlink-before-rename/raw-syscall/Linux
publication fallback.

The generated current index is distinct. Its sole `os.replace` is reachable
only after lock, expected-prior, complete chain, target-head, action,
postcondition, attempt, profile, source, plan, and exact target checks. It is
non-authoritative and cannot hide incomplete or ambiguous immutable history.

## Cleanup, lock, and ambiguity findings

- The internal cleanup helper unlinks only the exact temporary basename and,
  when identity is available, only after regular-file, link-count, device, and
  inode equality checks. It then synchronizes the directory.
- If cleanup identity or unlink/sync cannot be proved, the writer returns
  `H06_CLEANUP_AMBIGUOUS`; it does not broaden deletion.
- The regular mode-`0600` `.manifest-v2.lock` is retained. Readers never create
  it. A held lock is classified as `ambiguous` /
  `H06_HISTORY_LOCKED`.
- Publication after a native return ambiguity, a fault after publish, or a
  post-rename sync failure never returns false durable success.
- Current post-replace or directory-sync uncertainty returns
  `H06_CURRENT_PROMOTION_AMBIGUOUS`.
- Exact existing immutable bytes are idempotent; mismatching bytes are a
  collision and are never overwritten.

## Threat model and limitations

Supported:

- trusted operator and process on the qualified macOS/APFS class;
- accidental collisions, concurrent trusted writers, expected I/O faults,
  unexpected symlink/hardlink/non-regular objects, stale prior state, partial
  cleanup, and restart classification;
- native same-directory no-replace semantics and reviewed best-effort
  durability ordering.

Outside the supported claim:

- same-UID or root malicious interference;
- loader or libc interposition;
- a malicious kernel or hardware/firmware that lies about completion;
- defective hardware, media corruption/failure, and catastrophic power loss;
- assurance that acknowledged bytes survive every power-loss mode;
- network filesystems, synced folders, removable media, container overlays,
  tmpfs, and non-APFS filesystems;
- Linux and all non-macOS platforms;
- unauthorized operator behavior, credential compromise, transaction
  correctness, chain finality, deployment safety, and release approval.

The fsync/`F_FULLFSYNC`/directory-sync sequence is strong best-effort. It is
not a power-loss guarantee. Ambiguous results require freeze, restart, and
read-only reconciliation; they must never be converted to durable success
from path existence alone.

## Final operator binding

Local evidence proves only a qualified candidate operator/storage class. One
owner confirmation remains:

> The intended operator machine and selected state volume satisfy this exact
> qualified macOS/APFS class and are approved for the separately authorized
> action.

The confirmation must be made on the actual intended operator machine, against
the selected intended state volume, after the exact release-candidate
commit/tree is frozen. The corrected companion-runbook preflight must first
prove historical-base ancestry and exact bound-input bytes, then perform the
sanitized storage/root checks on that machine and volume. The binding must not
be inferred from this candidate qualification, and it does not itself
authorize deployment or release.

## Remaining independent reviewer classes

1. **Filesystem/security reviewer:** independently verify native FFI,
   `RENAME_EXCL` collision semantics, held-inode checks, lock model, exact
   cleanup, absence of fallback, and the limits of the durability claim.
2. **Operator/runbook reviewer:** execute the runbook from a clean exact
   baseline on an equivalent private APFS root and assess stop, restart,
   retention, sanitization, and escalation procedures.
3. **Gate 1/release reviewer:** bind the exact two-file patch, historical base,
   future exact release commit/tree, source/test hashes, test ledger, scope,
   and verdict; verify ancestry plus exact bound inputs; confirm that no
   implementation or operational state entered the candidate; issue any later
   release decision under separate authority.

These reviewer classes are independent of the single owner machine/volume
binding.

## Release-gate disposition

| Gate | Disposition |
|---|---|
| Historical qualification baseline | PASS |
| Historical local/cached/live `rh` identity at qualification | PASS |
| Future frozen release commit/tree after Wave 1 and authorized source movement | OPEN; must be supplied |
| Historical-base ancestry plus exact bound-input bytes | OPEN for the future frozen release candidate |
| Clean isolated worktree before original qualification writing | PASS |
| macOS/APFS candidate environment | PASS |
| Mode-`0700` private-root preflight | PASS on two roots |
| Native no-skip exclusive rename | PASS twice |
| Complete current H-06 suite | PASS, 148 tests |
| Unsupported filesystem fail-closed | PASS, safe mock |
| No Linux/fallback reachability | PASS |
| Exact two-file documentation scope | PASS; exactly two authorized untracked files |
| Markdown/link/table/fence/whitespace and `git diff --check` | PASS |
| Corrected preflight static syntax and eight-input binding | PASS |
| Final intended operator machine/volume binding | OPEN after the release candidate is frozen and corrected preflight passes |
| Independent reviewer classes | OPEN |
| Production/release authorization | NOT GRANTED |

Accordingly, the bounded technical qualification verdict is
**CONDITIONALLY READY**, while release remains unauthorized.

The native APFS runs and complete 148-test result remain historical facts and
were not rerun for this documentation-only correction. No real operational
state was created, and the two temporary qualification roots remain removed.

## Finalization and rollback

Final file SHA-256 values, Git blobs, full-index patch SHA-256, exact diff
scope, and final checks are emitted in the handoff after this document reaches
its final bytes. They cannot be embedded in this file without changing its own
hash.

Both documentation files must remain unstaged and uncommitted for independent
Gate 1/release qualification review.

Rollback is exact and non-destructive to the baseline:

1. verify that the only untracked paths are the two authorized documentation
   files;
2. remove only those two exact untracked files if the owner rejects the
   package;
3. do not reset, checkout, clean, or modify any tracked path;
4. separately remove the isolated worktree/branch only under explicit Git
   cleanup authority.

No operational Robinhood state requires rollback because none was created.
