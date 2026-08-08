# Track 7 H-01: Dependency-Security Preflight

**Status:** Draft for owner and security review; Stage A is evidence-only and
Stage B remains blocked on the mandatory checkpoint and S3 integration

**Prepared:** 24 July 2026

**Planning baseline:** `f0bfd0fd5ac2be1d27321463b77248c7cd91d829`

## Fresh-agent instruction

Treat this document as the task contract. Implement only Track 7 follow-on
slice H-01: produce a current, reviewable dependency-security decision and,
only after explicit owner/security approval and the S3 sequencing gate, apply
the smallest approved dependency refresh without weakening Track 6 S1 or
changing protocol behavior.

H-01 has two stages:

1. **Stage A — audit and decision checkpoint:** repository-read-only
   dependency, advisory, release-note, resolution, and compatibility analysis.
   The only repository deliverable is a sanitized evidence record; an
   owner-approved K-01 disposable resolver environment is the sole permitted
   non-repository side effect.
2. **Stage B — approved refresh and validation:** narrowly approved direct
   input/lock changes, an offline deterministic dependency-gate test, the
   minimum exact S1 version update if approved versions changed, and complete
   clean-environment validation.

Stage A may run while Track 6 S3 and Track 8 are in flight. Stage B must not
begin until the owner closes the mandatory checkpoint. No dependency-changing
commit may merge beneath an in-flight S3 production-contract review. The safe
default is to merge S3 first, then refresh H-01 from the integrated S3
baseline and rerun every required S3/S1/S2/full-suite gate.

On 24 July 2026, the owner approved the two narrow kickoff authorizations
below for the future fresh H-01 agent. That approval does not authorize this
brief's author to start H-01, does not approve a requirement edit or Stage B,
and does not extend beyond the exact K-01/K-02 boundaries.

Use branch `rh-track-7-h1-dependency-security`. Commit Stage A to that branch,
stop at the checkpoint, and wait for owner direction. Never push directly to
or merge into `rh` or `master`; the owner reviews and integrates the work.

This track authorizes no contract, default, migration, deployment, RPC,
verification, signer, secret, or live-chain change.

## Worktree bootstrap

The owner must first commit the reviewed brief to `rh`. The fresh agent is
responsible for creating its own worktree:

1. Start from `/Users/wigglez/dev/ripe-protocol`.
2. Verify that:
   - the integration worktree is clean;
   - `rh` resolves to the owner-approved integration commit;
   - this brief exists in that commit;
   - the merged Track 7 specification and validation plan exist;
   - S1 and S2 are integrated;
   - the current S1 exact-version assertions pass on the untouched baseline;
   - Track 6 S3's branch/worktree/integration state is recorded accurately; and
   - no other active branch owns `requirements.in`, `requirements.txt`,
     `tests/clock/test_clock_profiles.py`, or the proposed H-01 paths.
3. Record:
   - the full starting commit;
   - SHA-256 hashes of this brief, both Track 7 outputs, `requirements.in`,
     `requirements.txt`, `tests/clock/test_clock_profiles.py`, and
     `tests/utils/clock_profiles.py`;
   - the installed Python, pip, pip-tools if present, Vyper, Titanoboa, and
     pytest versions;
   - the current S1 and full-suite results; and
   - whether S3 is not started, in flight, at reviewer gate 1, at reviewer
     gate 2, or integrated.
4. Confirm that branch `rh-track-7-h1-dependency-security` and path
   `/Users/wigglez/dev/ripe-protocol-track-7-h1-dependency-security` do not
   already exist. If either exists, stop and ask the owner. Do not reuse,
   delete, reset, or overwrite it.
5. Create the isolated worktree:

   ```bash
   git -C /Users/wigglez/dev/ripe-protocol worktree add \
     -b rh-track-7-h1-dependency-security \
     /Users/wigglez/dev/ripe-protocol-track-7-h1-dependency-security \
     rh
   ```

6. Verify the new worktree's branch, commit, clean status, hashes, versions,
   S1 result, and S3 state.
7. Run every subsequent command and make every edit inside
   `/Users/wigglez/dev/ripe-protocol-track-7-h1-dependency-security`.

Do not modify or commit from the integration worktree. Do not create or mutate
a shared/global Python environment.

## Kickoff authorizations (owner-approved 24 July 2026)

These narrow authorizations prevent Stage A from predictably stopping before
it can produce a real candidate lock diff. They do not authorize any
requirement edit, Stage B work, alert acceptance, or dependency selection.

### K-01: disposable candidate-resolution tool

**Owner-approved on 24 July 2026 for the future fresh H-01 agent:** allow
`pip-tools==7.4.1` to be installed from the public Python Package Index into a
new disposable Python `3.12.0` virtual environment, solely to resolve
candidate copies of `requirements.in` to output files under a disposable
directory. This matches the `pip-compile 7.4.1` and Python `3.12.0` tools
observed at the planning baseline without treating the ambient pyenv
installation as reproducible provenance. The virtual environment necessarily
uses the approved installed Python `3.12.0` as its seed; that interpreter is
an explicit recorded platform input, not an independently provisioned tool.

Under this approval:

- use `--no-cache-dir` for installation and do not use a private index;
- record the actual Python executable path and binary hash used to seed the
  virtual environment;
- record the exact Python, pip, pip-tools, setuptools, wheel, build,
  pyproject-hooks, click, and resolver-tool environment;
- record the public index, commands, hashes, and complete installed tool
  inventory;
- copy `requirements.in` into the disposable directory and write candidate
  locks only there;
- do not install a candidate protocol lock, edit the worktree, run an auditor,
  or select a production dependency version under this authorization; and
- destroy the disposable environment after recording the sanitized evidence.

If the owner later revokes or narrows K-01, Stage A may still produce
release-note analysis and proposed direct-input edits, but it must label every
unresolved lock delta as blocked rather than claiming a complete prediction.

### K-02: read-only alert source

**Owner-approved on 24 July 2026 for the future fresh H-01 agent:** use the
authenticated GitHub Dependabot Alerts REST API through the installed GitHub
CLI, read-only, for repository `Ripe-Foundation/ripe-protocol`, limited to
listing current alerts. The prior Track 7 record proves an authenticated query
occurred but does not preserve which client performed it, so this authorization
must be explicit rather than inferred as precedent.

Under this approval:

- verify the remote repository identity before querying;
- request only Dependabot alert-list data with no mutation endpoint;
- never print authentication state, tokens, response headers, or unrelated
  repository/account data;
- keep the raw response outside the repository and commit only the sanitized
  ledger described below; and
- stop if the CLI is unauthenticated, lacks read access, or would require a
  new login, permission, or credential.

The owner may designate a different approved read-only GitHub connector
instead. Record the exact approved channel. K-02 does not authorize changing
Dependabot settings, dismissing alerts, or writing to GitHub.

## Hard sequencing rule: S3 controls the dependency baseline

S3 changes a live Base contract and records compiler/runtime/artifact evidence
against the dependency profile at its starting commit. H-01 must not make that
evidence stale silently.

The allowed sequence is:

1. H-01 Stage A runs and stops at its owner/security checkpoint.
2. S3 completes both reviewer gates and is integrated into `rh`.
3. The owner approves an exact H-01 refresh and explicitly instructs the H-01
   branch to reconcile with the integrated S3 commit.
4. H-01 Stage B recreates clean old/new environments, reruns S3's required
   tests and artifact checks, and completes its own reviewer gate.
5. Only then may H-01 merge.

An alternate order requires explicit approval from the owner, the S3
implementing/reviewing owners, Track 6, and security. If H-01 changes pytest,
Titanoboa, Vyper, compiler transitives, resolver output, or artifact hashes
before S3 integration, S3 must deliberately refresh its baseline and repeat
both reviewer gates. Do not infer that authorization.

Stage A must record the exact S3 branch/base commit and expected integration
consequence. Stage B must stop if S3 has changed since the approved checkpoint
or if the H-01 branch has not been reconciled with the reviewed S3 integration.

## Exact file ownership

### Stage A: evidence only

Stage A may add only:

- new `docs/chains/rh/evidence/dependency-security-gate.md`.

The new `docs/chains/rh/evidence/` directory is intentional: it contains
sanitized, reviewable release evidence rather than production configuration or
raw provider responses.

Stage A must not edit requirements, tests, S1, source, scripts, generated
artifacts, or any other documentation.

### Stage B: only after checkpoint and S3 integration

After explicit owner/security approval, Stage B may change only:

- `requirements.in`;
- regenerated `requirements.txt`;
- new `tests/deployment/test_dependency_gate.py`;
- `tests/clock/test_clock_profiles.py`, only if an approved Titanoboa or pytest
  version changes and only to replace exact expected versions with new exact
  expected versions; and
- `docs/chains/rh/evidence/dependency-security-gate.md`.

The new `tests/deployment/` directory is intentional. It is the shared,
offline deployment-tooling test surface reserved by Track 7; the unique
`test_dependency_gate.py` basename avoids the repository's current pytest
collection ambiguity.

If a selected refresh requires another direct input, constraint file, test,
script, source file, or generated artifact, stop and obtain a reviewed brief
amendment before editing it.

Do not change:

- `tests/utils/clock_profiles.py` merely to loosen version behavior;
- any file under `contracts/`, `interfaces/`, `migrations/`, or
  `migration_history/`;
- deployment, verification, ABI, parameter, defaults, or manifest code;
- any generated ABI;
- Track 6 S3 implementation files;
- `.github` or another CI system;
- `docs/chains/rh-summary.md`; or
- another track's deliverables.

## Required reading

Read and verify the current integrated versions of:

### Program authority

- `docs/chains/rh-summary.md`
- `docs/chains/rh/robinhood-deployment-support-specification.md`, especially
  Sections 4 and 18
- `docs/chains/rh/robinhood-deployment-validation-plan.md`, especially V-01,
  Stage 1, H-01, and the clean-environment procedure
- `docs/chains/rh/shared-block-clock-specification.md`
- `docs/chains/rh/block-clock-validation-plan.md`
- `docs/chains/rh/track-6-s1-clock-harness.md`
- `docs/chains/rh/track-6-s2-checked-clock-inventory.md`
- `docs/chains/rh/track-6-s3-lootbox-floor.md`
- the integrated S1/S2 implementation and any integrated S3 output available
  at Stage B

### Dependency and runtime surfaces

- `requirements.in`
- `requirements.txt`
- `tests/utils/clock_profiles.py`
- `tests/clock/test_clock_profiles.py`
- `tests/conftest.py`
- `tests/conf_env.py`
- `scripts/migrate.py`
- `scripts/verify.py`
- `scripts/console.py`
- `scripts/export_abis.py`
- every direct import/use of `requests`, `urllib3`, `dotenv`,
  `python-dotenv`, `cbor2`, `wheel`, `pytest`, `titanoboa`, `vyper`,
  `pymdown-extensions`, and `Pygments`
- repository documentation/build configuration, if any
- current packaging, ignore, and environment instructions in `README.md`, if
  any

The Track 7 alert table is a dated starting point, not current authority. At
Stage A, re-query the authoritative alert source and primary upstream
advisories/release notes. If current authenticated alert access is unavailable,
record the access blocker and stop before recommending that the gate is closed.
Do not infer current alert state from the dated count or from a package index
alone.

## Objective

H-01 must produce a reviewable answer to five questions:

1. Which current open alerts affect the deployment, HTTP, environment,
   compiler/build, test, console, or documentation paths?
2. What is the smallest compatible refresh that closes every owner-selected
   deployment-path alert without unrelated resolver churn?
3. Can pytest cross the current major-version boundary while preserving Vyper,
   Titanoboa, repository plugin, fixture, and S1 behavior?
4. What remaining docs-only or low-severity alerts, if any, are explicitly
   deferred or accepted, by whom, and until when?
5. Does the approved dependency profile reproduce the same protocol artifacts,
   ABIs, tests, and Base behavior as the prior frozen profile?

The valid outcomes are:

- **refresh approved and validated**;
- **partial refresh approved**, with every residual alert explicitly blocking
  rehearsal unless separately accepted;
- **time-bounded security exception**, with owner, scope, compensating
  controls, expiry, and remediation trigger;
- **no compatible refresh**, leaving H-01 and deployment rehearsal blocked; or
- **evidence incomplete**, leaving H-01 blocked.

Silently retaining an alert or broadly upgrading the lock are not valid
outcomes.

## Controlling constraints

- `requirements.txt` is generated from `requirements.in` using pip-compile
  under recorded Python/resolver provenance. Do not hand-edit only the compiled
  lock.
- Do not run an unconstrained broad upgrade and call all transitive churn
  security-required.
- Preserve `titanoboa==0.2.7` and `vyper==0.4.3` unless evidence proves a
  change is necessary and the owner separately approves it.
- The current S1 gate protects exact Titanoboa and pytest versions. A changed
  version must intentionally fail that gate before the exact expected value is
  updated and every runtime primitive is re-proved.
- Never replace an exact S1 version with a range, minimum, wildcard, skipped
  test, warning, xfail, or environment-dependent bypass.
- A security-fixed version number is not compatibility evidence. Review every
  selected package's primary upstream release notes and behavior changes.
- A clean resolver result is not runtime evidence. Validate HTTP, environment,
  compiler/build, test, ABI, and artifact behavior as applicable.
- Do not install into or mutate the shared developer environment. Use
  disposable virtual environments or other owner-approved isolated
  environments.
- Do not commit caches, virtual environments, downloaded wheels, raw
  authenticated responses, usernames, tokens, host credentials, private
  package indexes, or environment dumps.
- H-01 has no migration ID and authorizes no live action.
- At the planning baseline, `requirements.in` contains only five direct
  entries: unpinned `titanoboa`, `vyper==0.4.3`, `rlp~=4.0.1`, `ipython`, and
  `dotenv`. Every package in the dated alert set is transitive, and
  `titanoboa==0.2.7` exists only in the compiled lock. Therefore, an alert
  remediation may require adding a new direct pin or constraint; each proposal
  must identify that as a semantic direct-input change, choose pin versus
  bounded constraint deliberately, and state when the added constraint can be
  removed. A regeneration must also prove that unpinned Titanoboa did not
  float away from the approved exact version.
- Clearing a documentation-only alert cannot satisfy the deployment-security
  gate.

## Stage A — current alert and dependency audit

### Phase A1: freeze the starting state

Record:

- repository, branch, full commit, and clean status;
- UTC and local retrieval timestamps;
- hashes of direct inputs and the compiled lock;
- Python, pip, pip-tools, Vyper, Titanoboa, and pytest versions;
- the pip-compile command recorded in the lock header;
- whether pip-tools is declared by the repository or supplied externally;
- direct requirements versus transitive packages;
- installed environment consistency from `python -m pip check`;
- current S1 exact expectations and results;
- full baseline test result and collected-case count; and
- S3 branch/base/gate/integration state.

Do not treat the current installed environment as proof that the lock resolves
cleanly from scratch.

### Phase A2: obtain a sanitized authoritative alert snapshot

Use only the K-02 channel explicitly approved at kickoff. Do not substitute
another authenticated client, start a login flow, or print or store
authentication material.

For every open alert, record:

- alert number and state;
- severity;
- package and dependency manifest;
- vulnerable pinned version;
- GHSA/CVE identifiers;
- vulnerable range and first patched version;
- publication and update timestamps;
- direct or transitive dependency path;
- repository runtime/import consumers;
- deployment relevance;
- whether exploit conditions are reachable in Ripe's use;
- proposed disposition; and
- primary advisory URL.

Record aggregate counts only as a derived summary. The individual alert ledger
controls if counts disagree.

Do not commit the raw authenticated response. The sanitized evidence must omit
repository tokens, response headers, user identity, private URLs, and unrelated
metadata.

### Phase A3: map package reachability and release behavior

At minimum, assess:

| Package area | Mandatory review |
| --- | --- |
| `requests` / `urllib3` | Direct and transitive users; redirects, retries, proxies, TLS/certificates, adapters, pooling, timeouts, exceptions, and verifier/Safe/probe behavior |
| `idna` | Hostname normalization and rejection behavior used by RPC/explorer URLs |
| `python-dotenv` / `dotenv` | Search path, parsing, interpolation, precedence, and whether the advisory's write behavior is reachable |
| `cbor2` | Vyper/compiler dependency path, encoding/decoding compatibility, wheel availability, and artifact effect |
| `wheel` | Build/install behavior, supported Python versions, and reproducible environment metadata |
| `pytest` | 8-to-9 changes, collection, plugins, fixtures, warnings/errors, assertions, S1 anchors, and Vyper `test` extra constraints |
| `pymdown-extensions` | Actual repository docs/build reachability and Markdown behavior; no build is assumed if no config exists |
| `Pygments` | Console/docs reachability and low-severity policy if still alerted |
| Titanoboa / Vyper | Upstream metadata constraints, supported Python, compiler/runtime compatibility, and exact S1 profile |

For each selected version, cite primary upstream release/changelog and package
metadata. Record relevant changes between the pinned version and candidate,
not only the final release.

If a package is not imported directly, trace why it is present and which direct
requirement brings it in. Do not label a transitive dependency unused merely
because repository search finds no import.

### Phase A4: construct minimal candidate resolution plans

Produce separately reviewable plans:

1. **Deployment-path non-pytest refresh:** HTTP, hostname, environment,
   compiler/build, packaging, and other high/medium deployment-relevant alerts.
2. **Pytest compatibility decision:** the advisory-fixed pytest version,
   Vyper/Titanoboa metadata, S1 expected version, plugin/fixture behavior, and
   full-suite implications.
3. **Docs-only sub-slice:** `pymdown-extensions` or another documentation-only
   alert that can be safely separated.
4. **Optional low-severity/zero-alert sub-slice:** only if the owner selects a
   zero-open-alert policy.

For each plan, record:

- exact direct-input edits, if any;
- exact selected package versions or bounded constraints;
- complete realized candidate lock delta when K-01 is approved and succeeds;
- otherwise, the best supported predicted dependency changes plus the explicit
  resolver blocker—never label an unexecuted prediction complete;
- resolver command and environment;
- packages deliberately held;
- packages expected to change only transitively;
- known metadata conflicts;
- tests and artifact comparisons;
- residual alerts;
- rollback lock/commit; and
- whether it can land independently.

Do not edit requirements during Stage A. Candidate resolutions may be tested
only under the exact K-01 authorization in disposable
directories/environments without changing the H-01 worktree. K-01 does not
authorize an auditor or another helper.

### Phase A5: assess S3 sequencing impact

Record:

- S3's starting dependency profile;
- whether S3 has produced source, ABI, artifact, or reviewer-gate evidence;
- which H-01 candidates change pytest, Titanoboa, Vyper, compiler transitives,
  packaging, or any artifact input;
- the exact S3 validations that must repeat after H-01;
- whether S3-first remains the recommended merge order; and
- the consequences of choosing H-01-first.

The recommendation must remain S3-first unless concrete evidence and explicit
owners approve another order.

## Deliverable and mandatory owner/security checkpoint

Create `docs/chains/rh/evidence/dependency-security-gate.md` during Stage A.

It must contain:

- starting commit and all input hashes;
- retrieval method, timestamps, source authority, and sanitization statement;
- full sanitized alert ledger;
- direct/transitive dependency map;
- package reachability and advisory applicability;
- primary release-note and metadata review;
- candidate resolution plans and complete realized lock diffs for every
  K-01-approved trial, or clearly blocked predictions where no approved
  resolver run exists;
- pytest/Vyper/Titanoboa compatibility analysis;
- S1 and S3 impact;
- selected or proposed security policy;
- exact owner decisions requested;
- residual-risk register;
- rollback/reproduction plan;
- Stage A command results;
- open blockers; and
- a clearly marked checkpoint record.

Then commit only the evidence file and stop.

The checkpoint must ask the owner/security reviewer to decide:

1. Which alert policy applies:
   - zero open alerts;
   - zero open deployment-path high/medium alerts, with separate docs/low
     disposition; or
   - another explicit risk policy.
2. Which exact non-pytest package versions and direct-input changes are
   approved.
3. Whether pytest is:
   - upgraded with exact S1 reapproval;
   - held under a time-bounded security exception;
   - paired with a separately approved Vyper/Titanoboa change; or
   - still blocked pending a compatible upstream path.
4. Whether docs-only and low-severity sub-slices land now, separately, or
   remain explicitly open.
5. Whether any residual alert is accepted, including owner, rationale,
   compensating control, expiration, and mandatory re-review trigger.
6. Confirmation that S3 merges first, or explicit approval of the more
   expensive alternate sequence.
7. The approved Python, pip, pip-tools/resolver, clean-environment, and audit
   commands for Stage B.
8. The evidence-freshness policy: its exact window or event trigger, what
   refreshes it, which evidence and alert classes it covers, and which
   rehearsal/deployment actions stale evidence blocks. Ordinary offline unit
   tests must not become network- or wall-clock-dependent merely to enforce
   rehearsal freshness.

No answer means no dependency edit. Recommendations in the evidence file are
not approvals.

## Stage B — approved refresh implementation

Do not continue into Stage B until:

- every selected version and direct-input edit is explicitly approved;
- any security exception is explicit and time-bounded;
- the resolver/audit tooling and commands are approved;
- S3 is integrated into `rh`, unless the alternate sequence is explicitly
  approved;
- the H-01 branch is reconciled with that reviewed S3 integration under owner
  direction; and
- baseline tests pass again after reconciliation.

### Phase B1: create old and candidate clean environments

Use two disposable environments:

- **old:** the integrated pre-H-01 lock; and
- **candidate:** the approved regenerated lock.

Record for both:

- OS/architecture;
- Python implementation and exact version;
- pip and pip-tools versions;
- resolver command and indexes with credentials redacted;
- lock SHA-256;
- install success/failure;
- `python -m pip check`;
- installed package/version inventory;
- selected package metadata;
- no undeclared local/editable dependency; and
- environment disposal/rollback procedure.

Do not upgrade an environment in place and call downgrade/reinstall a rollback.

### Phase B2: edit direct inputs and regenerate deterministically

- Edit `requirements.in` only for approved direct pins/constraints.
- Preserve Titanoboa and Vyper unless separately approved.
- Regenerate `requirements.txt`; do not hand-edit the compiled lock.
- Use the approved Python and pip-tools versions and record the exact command.
- Prefer selected-package upgrades or explicit constraints over a broad
  resolver upgrade.
- Review every changed lock line, including packages not named in an alert.
- Explain every transitive addition, removal, upgrade, or downgrade.
- Fail if the same approved inputs/environment produce a different lock.
- Verify the lock header truthfully records the generation command and Python
  provenance.

If the resolver cannot produce the approved profile without unrelated or
incompatible changes, stop and return to the checkpoint.

### Phase B3: implement the offline dependency gate

Create `tests/deployment/test_dependency_gate.py`.

It must run with external network disabled and test at least:

- the committed direct-input and lock hashes match the approved evidence;
- the lock is marked generated from the expected direct input;
- selected packages are exactly the approved versions;
- held packages remain at approved versions;
- forbidden vulnerable versions/ranges from the approved snapshot are absent;
- no unapproved URL, editable, local-path, or private-index dependency exists;
- the committed evidence names every selected package and residual alert;
- unresolved deployment-path alerts cause a failed gate unless a current,
  explicit, nonexpired exception is recorded;
- S1's exact Titanoboa and pytest expectations match the approved lock;
- Vyper/Titanoboa/pytest compatibility assumptions are explicit;
- the gate never performs a live advisory query during pytest; and
- stale evidence is visible and blocks rehearsal according to the approved
  freshness policy, without making ordinary offline unit tests depend on wall
  clock or network.

Do not encode the dated aggregate alert count as a permanent invariant.
Stable advisory IDs, approved dispositions, lock/evidence hashes, and refresh
policy are the durable assertions.

### Phase B4: update and reapprove S1 if required

If the approved profile changes pytest or Titanoboa:

1. run the existing S1 test unchanged and record the intentional exact-version
   failure;
2. update every exact expected version in
   `tests/clock/test_clock_profiles.py`;
3. keep equality assertions exact;
4. rerun every S1 runtime primitive and profile;
5. reproduce artifact fingerprints;
6. obtain Track 6 owner/reviewer approval of the new exact profile; and
7. record that approval in the evidence file.

Do not change the clock profiles, patch mechanism, fixture isolation, artifact
definition, or error handling in H-01.

If pytest changes collection, fixture teardown, warnings, exception groups,
assertion behavior, plugin loading, or test ordering, record and review the
behavioral delta rather than normalizing it away.

### Phase B5: behavior and artifact validation

Validate the selected package areas without live external services:

- HTTP redirect, retry, proxy, timeout, TLS/certificate configuration, adapter,
  and exception behavior used by repository tooling;
- URL/hostname normalization and rejection;
- dotenv load/search/interpolation/precedence behavior used by the repository;
- cbor2 deterministic known-vector round trips relevant to the compiler path;
- wheel/install metadata and clean resolution;
- pytest collection, fixtures, warnings, assertions, plugins, and teardown;
- S1 repeated/jumping-number behavior and anchor restoration;
- S2 inventory guard;
- S3 targeted tests and artifact record reproduction;
- deterministic ABI export to disposable directories;
- representative creation/runtime bytecode fingerprints under unchanged
  compiler/source inputs; and
- the entire Base suite serially.

Do not add production behavior tests to H-01. Where existing tests do not cover
a package behavior, the dependency-gate test may add a minimal isolated
compatibility case without importing secrets or external network state.

### Phase B6: re-query and finalize the security record

After the candidate lock is committed on the branch:

- re-query authoritative alerts against the branch/manifest if the source
  supports it, or record why repository default-branch alerts cannot yet
  reflect an unmerged branch;
- run the approved audit command against the candidate environment;
- reconcile every Stage A alert;
- record newly surfaced alerts;
- record remaining accepted/deferred items;
- update exact lock, environment, test, ABI, and artifact hashes;
- record all approval provenance; and
- state whether H-01 is closed, partially closed, blocked, or exception-gated.

Never claim a GitHub alert is closed before the authoritative service observes
the relevant manifest state. Distinguish candidate-lock remediation from
default-branch alert closure.

## Mandatory Stage B reviewer gate

Before merge, an independent security/Track 6 reviewer must inspect:

- Stage A evidence and owner decisions;
- exact direct-input and full lock diff;
- primary release-note review;
- resolver and clean-environment provenance;
- residual alerts and exceptions;
- `test_dependency_gate.py`;
- intentional S1 failure and exact-profile update, if any;
- S1/S2/S3 and full-suite results;
- ABI and artifact comparisons;
- S3 merge-base and repeated evidence;
- rollback reproduction;
- changed-file scope; and
- branch freshness against `rh`.

Any dependency, lock, expected-version, test-policy, evidence, or artifact
change after review reopens the relevant reviewer scope. Only the owner merges
and pushes.

## Approval and safety boundaries

The Stage A agent may:

- inspect repository code, history, metadata, and installed versions;
- query current Dependabot alerts read-only through the exact K-02 channel
  without exposing credentials;
- read public primary advisories, package metadata, and upstream release notes;
- create the exact K-01 disposable candidate-resolution environment without
  changing the worktree or shared environment, if K-01 is approved;
- draft and commit the sanitized evidence file; and
- recommend exact options at the checkpoint.

Fresh owner approval is required before:

- installing or selecting pip-tools, pip-audit, an auditor, resolver, or other
  tool, except for the exact K-01 trial authorization if approved at kickoff;
- changing any requirement, lock, test, or exact S1 expectation;
- accepting or deferring an alert;
- selecting a package version or resolver behavior;
- beginning Stage B;
- reconciling the branch with a newer `rh` commit;
- accessing a secret or private package index;
- using an authenticated alert channel other than the exact approved K-02
  path;
- committing raw authenticated responses;
- using a live RPC, explorer, verifier, Safe, or signer;
- changing production code, configuration, migrations, manifests, ABIs,
  defaults, or CI;
- merging ahead of S3;
- publishing the branch; or
- ticking `docs/chains/rh-summary.md`.

## Stop conditions

Stop and report evidence if:

- current alert access is unavailable or incomplete;
- a primary advisory or upstream release history cannot be verified;
- the repository's lock-generation provenance cannot be reproduced;
- candidate resolution requires an unapproved tool;
- a broad resolver refresh changes unrelated packages without justification;
- Titanoboa, Vyper, pytest, compiler transitives, or artifact hashes change
  outside an approved plan;
- S1 can pass only by weakening its exact-version or runtime gate;
- S3 is still in flight when Stage B would begin;
- the branch is not reconciled with reviewed S3 integration before Stage B;
- S3 tests or artifacts differ under the candidate profile without an approved
  explanation;
- a deployment-path high/medium alert remains without explicit disposition;
- a security exception lacks owner, scope, control, expiry, or re-review
  trigger;
- an authenticated response or environment output contains a secret;
- the full suite requires skipping, xfail, warning suppression, or unrelated
  source changes;
- another active track overlaps an owned file; or
- a live/state-changing action would be required.

The valid blocked outcome is preferable to an unproved "clean" dependency
profile.

## Validation

### Stage A baseline

Run without changing dependencies:

```bash
python --version
python -m pip --version
python -m pip check
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest --collect-only -q
PYTHONPATH=. pytest -q
git diff --check
```

Also:

- [ ] Confirm only the evidence file changed.
- [ ] Confirm no virtual environment, cache, wheel, raw response, or secret is
  present.
- [ ] Confirm every alert has an individual disposition.
- [ ] Confirm every selected candidate has primary release-note evidence.
- [ ] Confirm resolver churn is complete and explained, or explicitly blocked
  under the recorded K-01 disposition.
- [ ] Confirm S3 state and merge-order impact are explicit.
- [ ] Record commands, durations, counts, versions, hashes, and failures.

If the baseline full suite has a pre-existing failure, reproduce it from the
untouched starting commit and separate it from H-01.

### Stage B candidate

Use only the owner-approved resolver and audit commands. At minimum run:

```bash
python -m pip check
PYTHONPATH=. pytest -q tests/deployment/test_dependency_gate.py
PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py
PYTHONPATH=. python scripts/check_block_clock_inventory.py --check
PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py
PYTHONPATH=. pytest -q tests/core/lootbox/test_underscore_rewards.py
PYTHONPATH=. pytest -q tests/config/test_switchboard_charlie.py
PYTHONPATH=. pytest --collect-only -q
PYTHONPATH=. pytest -q
git diff --check
```

Repeat the approved clean resolution and compare lock hashes. Generate ABIs
into two separate disposable directories and compare inventories/hashes.
Reproduce the S1/S3 artifact fingerprints under the old and candidate
environments.

Also:

- [ ] Confirm the changed-file set matches Stage B ownership.
- [ ] Confirm `requirements.txt` is generated, not hand-edited.
- [ ] Confirm every lock delta is approved and explained.
- [ ] Confirm S1 exact assertions match the selected profile.
- [ ] Confirm no Track 6 profile or production source changed.
- [ ] Confirm historical migrations, manifests, and generated ABIs are
  byte-identical.
- [ ] Confirm no secret or raw authenticated response is committed.
- [ ] Confirm S3's reviewed tests/artifacts were repeated after integration.
- [ ] Confirm authoritative alert closure is not claimed prematurely.
- [ ] Record both clean environments and rollback recreation.

## Completion report

### Stage A handoff

Report:

- starting commit and exact changed file;
- input/evidence hashes;
- retrieval time, source, sanitization, and alert totals;
- complete alert/disposition table;
- direct/transitive dependency map;
- release-note findings;
- candidate resolution plans and predicted lock deltas;
- pytest/Vyper/Titanoboa decision analysis;
- S3 sequencing consequence;
- Stage A command results;
- checkpoint decisions requested;
- K-01/K-02 approval provenance; and
- all resulting or other blockers.

Then stop. Do not state that H-01 is complete.

### Final H-01 handoff

After Stage B and reviewer approval, report:

- starting, reconciled-S3, Stage A, implementation, approval, and final commits;
- exact changed files;
- owner/security decisions and provenance;
- old/new direct inputs and complete lock diff;
- resolver/auditor/environment provenance;
- selected and residual alerts;
- security exceptions and expiry, if any;
- S1 exact-profile before/after evidence;
- S2 and S3 reconciliation evidence;
- ABI/artifact comparisons;
- all validation commands and results;
- rollback recreation;
- authoritative default-branch alert status versus candidate-lock status;
- reviewer sign-off;
- downstream H-02–H-09 readiness; and
- which Track 7 dependency-security/checklist items are eligible for owner
  review.

Do not edit or tick `docs/chains/rh-summary.md`. H-01 implementation does not
authorize deployment rehearsal or live activity.
