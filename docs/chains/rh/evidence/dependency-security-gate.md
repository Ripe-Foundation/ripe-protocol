# Track 7 H-01 Stage A Dependency-Security Gate

**Status:** Stage A evidence complete; H-01 and every dependency change remain
blocked at the mandatory owner/security checkpoint

**Evidence date:** 24 July 2026

**Stage A branch:** `rh-track-7-h1-dependency-security`

**Starting commit:** `382eb7da82bc4ed54be945311a8ccd30fae87dec`

This is the sanitized, evidence-only Stage A record required by
`track-7-h1-dependency-security-preflight.md`. It is not a dependency
selection, alert acceptance, Stage B authorization, S3 approval, merge
approval, deployment approval, or claim that an authoritative alert is
closed. No requirement, lock, test, contract, script, production file, or
other documentation file was changed.

## Executive decision summary

The authenticated source reported 13 open Dependabot alerts in
`requirements.txt`: 6 high, 6 medium, and 1 low. All alerting packages are
transitive from the five current direct inputs. Repository and upstream
analysis divides the remediation into four independently reviewable choices:

1. Candidate A changes only `cbor2 5.7.0 -> 5.9.0`, `idna 3.10 -> 3.15`,
   `python-dotenv 1.2.1 -> 1.2.2`, `requests 2.32.5 -> 2.33.0`,
   `urllib3 2.5.0 -> 2.7.0`, and `wheel 0.45.1 -> 0.46.2`. It predicts
   remediation of ten high/medium deployment, HTTP, environment, compiler, or
   packaging alerts with no unrelated package-version churn. It leaves the
   pytest, Pymdown Extensions, and Pygments alerts open.
2. Candidate pytest changes Candidate A plus `pytest 8.4.2 -> 9.0.3`. It
   predicts remediation of the pytest alert, but crosses a major version,
   intentionally breaks S1's current exact expectation, and conflicts with
   Vyper 0.4.3's optional `test`/`dev` metadata constraint `pytest<9`.
   Resolution without those extras is not compatibility proof.
3. Candidate docs changes only `pymdown-extensions 10.16.1 -> 10.21.3`
   while explicitly holding Titanoboa and pytest. It predicts remediation of
   the documentation-only alert, but the repository has no Markdown build
   configuration that reaches the vulnerable snippets feature.
4. Candidate zero combines the preceding changes and adds
   `Pygments 2.19.2 -> 2.20.0`. It predicts removal of all 13 alerts from the
   candidate lock with no unrelated package-version churn. It is not an audit,
   candidate installation, runtime validation, or authoritative default-branch
   alert closure.

The proposed policy is zero unresolved high/medium alerts in any deployment,
compiler/build, environment, HTTP, or mandatory validation path, with a
separate explicit decision for documentation-only and low-severity alerts.
Because pytest is part of the mandatory validation path, that proposal still
requires either a validated exact pytest upgrade or a complete time-bounded
exception. This recommendation is not an approval.

S3-first remains mandatory and recommended. S3 is in flight, not integrated
into `rh`, and has produced production-contract, test, artifact, Gate 1, and
inventory-reconciliation/Gate 2 evidence against the old dependency profile.
Its independent reviewer Gate 2 remains open. Stage B must wait for that gate
and S3 integration, then reconcile under explicit owner direction and
reproduce S1/S2/S3/full-suite and artifact evidence.

### Independent review disposition

The first independent Stage A review reported no blocking defect and seven
evidence-quality observations. The first follow-up revision maps and addresses
them one-to-one:

1. **Destroyed artifacts:** the byte-identical K-02 raw preimage and a stricter
   canonical projection are retained outside the repository with restrictive
   permissions; candidate-lock comparability is restored through the embedded
   literal diffs, exact hashes, and mandatory fresh Stage B diff review.
2. **Literal lock diffs:** all four complete candidate diffs are embedded and
   were mechanically checked against exact hash reproductions.
3. **Placeholder authority:** the `local-placeholder` provenance is identified
   as unintegrated S3 authority.
4. **Compiler-cache side effect:** the shared Titanoboa compiler cache is
   acknowledged as a second non-repository side effect and a future-brief
   correction.
5. **Alert-number gaps:** provider gaps are explained without inventing closed
   states.
6. **First-patched versus latest:** candidates are compared with current PyPI
   latest releases.
7. **Freeze timestamp:** the initial bootstrap freeze has an exact UTC/local
   timestamp.

The follow-up also exposed and now records one important reproduction detail:
the frozen output lock must seed pip-compile. Without it, the mutable current
index produces broad unrelated churn. Stage B therefore requires a complete
fresh literal diff review even if a candidate hash happens to match.

A second independent rereview verified all seven corrections and raised five
minor follow-ups: retained-artifact lifecycle, exact lock-command/header form,
the grammar and one-to-one mapping above, the targeted replay's full-suite
rationale, and explicit local-versus-remote branch state. Those points are
addressed in place, including the new residual-risk rows and the additions to
checkpoint decisions 7 and 8.

A third independent rereview mechanically rechecked the evidence-only scope,
file and retained-artifact hashes, permissions, branch publication state, S3
state, and every second-round correction. It found no new defect and raised
only two cosmetic clarity points: multi-commit rollback wording and explicit
review-round provenance. This revision addresses both without changing any
candidate, risk judgment, checkpoint decision, or Stage A boundary.

## Authority, bootstrap, and frozen inputs

The task contract, merged Track 7 specification and validation plan, and the
integrated Track 6 S1/S2 records were read from the starting `rh` commit. The
initial freeze was captured at `2026-07-24T16:52:20Z`
(`2026-07-24T10:52:20-0600`, MDT). The integration worktree was clean at
bootstrap. The requested branch and worktree did not exist, and no active
branch diff owned `requirements.in`, `requirements.txt`,
`tests/clock/test_clock_profiles.py`, or the proposed evidence path. The exact
worktree-add command in the task contract initially failed in the managed
sandbox because Git could not create the new ref lock; the same command was
then approved for Git-metadata write access and succeeded. The isolated
worktree was clean at the same starting commit and the hashes below matched.

| Frozen input | SHA-256 |
| --- | --- |
| H-01 preflight brief | `ac31478d185571c9b804c84a0f78de60bf40eeb3a0aec80b839b66f62befef22` |
| Track 7 deployment-support specification | `a28db8424537d5f059a14a614265077fd4f64379f6596b6eaede9d2716d3269d` |
| Track 7 deployment-validation plan | `6b61a24b838d84d87d88f9d04f95521f2e351a4c75e9511a86e8ac0e13422add` |
| `requirements.in` | `2a6726cdc447cb71cc376ef14ee93cc645dbb43826893c5d2433586a89f26f63` |
| `requirements.txt` | `18df0aad224f2a10febc9e155e4a530e1000ec553916c8ef78dc9859c6c92ba0` |
| S1 test | `2b1bbd8c77f97e614c9db54fcb98b284d3db95a6bb47d1ee9ab020bf6d725cc4` |
| S1 clock utility | `69f3a616a78cb3a155962edb779533f56e362a68cc922c307dc7d40cbd4b34de` |

The compiled lock says it was generated with Python 3.12 by
`pip-compile requirements.in`. `pip-tools` is not a repository-declared
dependency; it is externally supplied. The ambient toolchain was:

| Surface | Observed value |
| --- | --- |
| Python executable | `~/.pyenv/versions/ripe-lite/bin/python` |
| Python | `3.12.0` |
| pip | `25.2` |
| pip-tools | `7.4.1` |
| Vyper | `0.4.3` |
| Titanoboa | `0.2.7` |
| pytest | `8.4.2` |
| platform | macOS `26.5.2`, arm64 |

`python -m pip check` reported no broken requirements. That is not exact-lock
or clean-resolution evidence: the ambient environment did not contain
IPython, and its installed `python-dotenv` was `1.1.0` while the lock pins
`1.2.1`.

The five direct inputs are unpinned `titanoboa`, exact `vyper==0.4.3`,
`rlp~=4.0.1`, unpinned `ipython`, and the deprecated `dotenv` wrapper.
The current lock alone pins Titanoboa to `0.2.7`. S1 asserts exact installed
versions `titanoboa==0.2.7` and `pytest==8.4.2`, plus the exact Vyper compiler
fingerprint. Candidate inputs therefore pin Titanoboa and pytest deliberately
to prevent silent float during a security regeneration.

### Reviewed source surface

The required program authority was read at the starting commit:
`docs/chains/rh-summary.md`, both Track 7 specification/validation outputs,
both shared Track 6 specification/validation outputs, the S1, S2, and S3
briefs, and the S1/S2 implementation records. S3's live branch record and
history were then re-read as that branch advanced during Stage A.

The dependency/runtime inspection covered `requirements.in`,
`requirements.txt`, both S1 files, `tests/conftest.py`, `tests/conf_env.py`,
the named migration/verification/console/ABI scripts, every repository match
for the alerting packages and their direct parents, repository
documentation/build configuration, `.gitignore`, and `README.md`. No direct
urllib3, cbor2, wheel, Pymdown Extensions, or Pygments production import was
found; their transitive paths are preserved below rather than being mislabeled
unused.

### Concurrent integration movement

At bootstrap, `rh` was the clean starting commit above. During Stage A, an
independent owner action advanced local `rh` to
`127b4bf287bf63c5ed662d82fbf3db8bf66d06a3` with only
`docs/chains/rh/track-6-s4-deleverage-cooldown.md`; none of the H-01-owned
paths differ. H-01 was not rebased or reconciled because that requires fresh
owner direction and is a Stage B precondition. This record and all tests are
therefore anchored to `382eb7d`.

At `2026-07-24T17:43:09Z` (`2026-07-24T11:43:09-0600`, MDT), a read-only
`git ls-remote` confirmed `origin/rh` remained at
`382eb7da82bc4ed54be945311a8ccd30fae87dec`; local `rh` remained at
`127b4bf287bf63c5ed662d82fbf3db8bf66d06a3`, one commit ahead. The local S4
brief was therefore not published through `rh`. The same remote read returned
no `rh-track-7-h1-dependency-security` branch, confirming H-01 remained
unpublished. This is an observation, not authorization to push, reconcile, or
integrate either branch.

## K-02 authoritative alert snapshot

K-02 was owner-approved in the brief on 24 July 2026. The sanitized remote
identity was verified as `Ripe-Foundation/ripe-protocol`; GitHub CLI version
`2.96.0` used the already-authenticated, read-only Dependabot alert-list REST
endpoint:

```text
gh api --method GET --paginate --slurp \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  '/repos/Ripe-Foundation/ripe-protocol/dependabot/alerts?state=open&per_page=100'
```

Retrieval succeeded at `2026-07-24T16:54:22Z`
(`2026-07-24T10:54:22-0600`, MDT). The raw response remained outside the
repository and had SHA-256
`52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a`.
The normalized outside-repository ledger had SHA-256
`db06f57169506b9cd01d44fd29fa4e9144d4963eb773296eee96e09813fe139a`.
Both original files were destroyed after the initial record was captured.

Reviewer follow-up re-ran the identical approved K-02 query at
`2026-07-24T17:26:39Z` (`2026-07-24T11:26:39-0600`, MDT). It returned the same
13 rows and a byte-identical raw response with the same SHA-256 above. That
recovered raw preimage and a stricter canonical projection are retained,
mode `0600`, outside the repository under
`~/dev/ripe-protocol-h1-private-evidence/`. The retained projection includes
alert number/state, severity, package/manifest/scope, GHSA/CVE, vulnerable
range, first patch, publication/update times, and advisory URL; its SHA-256 is
`d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06`.
This retention repairs the original reviewability weakness without committing
the authenticated response.

Interim custody is deliberately conservative while checkpoint decision 8 is
open: both files must remain byte-for-byte unchanged at the recorded paths,
mode `0600`, and must not be moved or deleted. Their committed hashes make
integrity re-checkable, but no accountable custodian, durable-copy
requirement, final retention period, or approved disposal trigger exists yet.
Decision 8 must supply those lifecycle controls. The untracked directory is
not durable repository storage and must not be treated as such.

No authentication state, token, header value, user identity, private URL, or
unrelated repository metadata is present here. No GitHub mutation endpoint,
login flow, alert dismissal, setting change, or other write was used.

The source is authoritative for the repository's current default-branch alert
state at retrieval time. It is not evidence about an unmerged candidate lock,
and the state can become stale after retrieval.

## Full sanitized alert ledger

All entries were open in `requirements.txt`; every alerting package is
transitive. “Disposition” below is a proposal for the checkpoint, not an
accepted risk or approved version. Alert numbers are provider-assigned and not
contiguous within a `state=open` filtered response. Numbers below 13 and gaps
#17 and #20 were absent from the authoritative open-alert result; this record
does not infer whether any absent number was fixed, dismissed, or otherwise
closed.

| # | Severity; package/version | Advisory; affected; first patch | Path, repository reachability, and proposed disposition |
| --- | --- | --- | --- |
| 13 | high; `urllib3 2.5.0` | [GHSA-gm62-xv2j-4w53](https://github.com/advisories/GHSA-gm62-xv2j-4w53), CVE-2025-66418; `>=1.24,<2.6.0`; `2.6.0`; published/updated `2025-12-05T18:15:19Z`/`2025-12-05T18:33:00Z` | `titanoboa -> requests -> urllib3` and repository `requests` consumers. Automatic response decoding from external RPC/explorer/Safe/probe servers makes an unbounded encoding-chain DoS reachable. Upgrade to `2.7.0` in Candidate A; deployment-blocking until changed or explicitly excepted. |
| 14 | high; `urllib3 2.5.0` | [GHSA-2xpw-w6gg-jr37](https://github.com/advisories/GHSA-2xpw-w6gg-jr37), CVE-2025-66471; `>=1.0,<2.6.0`; `2.6.0`; `2025-12-05T18:15:54Z`/`2025-12-05T18:33:09Z` | Affects compressed streaming reads. Repository code does not directly call urllib3 streaming APIs, but the same transitive HTTP stack reaches external servers and the same minimal urllib3 upgrade patches it. Upgrade in Candidate A; deployment-blocking absent change/exception. |
| 15 | medium; `cbor2 5.7.0` | [GHSA-wcj4-jw5j-44wh](https://github.com/advisories/GHSA-wcj4-jw5j-44wh), CVE-2025-68131; `>=3,<5.8.0`; `5.8.0`; `2025-12-31T22:01:38Z`/`2026-06-05T14:17:48Z` | `vyper -> cbor2`; no direct repository import and no identified reused decoder across attacker-controlled trust boundaries. It remains a compiler dependency. Upgrade to `5.9.0` in Candidate A and require known-vector plus unchanged-artifact proof. |
| 16 | high; `urllib3 2.5.0` | [GHSA-38jv-5279-wg99](https://github.com/advisories/GHSA-38jv-5279-wg99), CVE-2026-21441; `>=1.22,<2.6.3`; `2.6.3`; `2026-01-07T19:18:14Z`/`2026-01-23T16:05:22Z` | Redirect-following can bypass compressed-stream safeguards. Requests follows redirects by default; external endpoints are reachable even though repository code does not directly stream. Upgrade to `2.7.0` in Candidate A; deployment-blocking absent change/exception. |
| 18 | high; `wheel 0.45.1` | [GHSA-8rrh-rw8j-w5fx](https://github.com/advisories/GHSA-8rrh-rw8j-w5fx), CVE-2026-24049; `>=0.40,<=0.46.1`; `0.46.2`; `2026-01-22T18:02:56Z`/`2026-01-23T17:44:38Z` | `vyper -> wheel`; no repository call to `wheel unpack`, but the package is in the deployment build/install toolchain. Upgrade to `0.46.2` in Candidate A and reproduce clean install metadata/artifacts; deployment-blocking absent change/exception. |
| 19 | high; `cbor2 5.7.0` | [GHSA-3c37-wwvx-h642](https://github.com/advisories/GHSA-3c37-wwvx-h642), CVE-2026-26209; `<=5.8.0`; `5.9.0`; `2026-03-23T20:23:57Z`/`2026-03-25T20:38:41Z` | Deeply nested untrusted CBOR can exhaust recursion. No repository path decodes network CBOR directly, but cbor2 is a compiler input. Upgrade to `5.9.0` in Candidate A and prove encoding/decoding and artifact equality. |
| 21 | medium; `requests 2.32.5` | [GHSA-gc5v-m9x4-r6x2](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2), CVE-2026-25645; `<2.33.0`; `2.33.0`; `2026-03-25T16:56:28Z`/`2026-03-27T22:07:43Z` | Repository imports Requests in Etherscan verification, Safe account operations, the stock-token probe, and local test environment checks, but never calls `requests.utils.extract_zipped_paths`, the sole affected API. Upgrade to `2.33.0` in Candidate A because it is the minimum patch and a core deployment HTTP dependency. |
| 22 | low; `Pygments 2.19.2` | [GHSA-5239-wwwm-4pmq](https://github.com/advisories/GHSA-5239-wwwm-4pmq), CVE-2026-4539; `<2.20.0`; `2.20.0`; `2026-03-22T06:30:15Z`/`2026-03-30T14:40:30Z` | Reached through IPython, pytest, Rich, and Titanoboa's MkDocs stack. The vulnerable Archetype lexer requires local crafted content and is not directly invoked by repository code. Upgrade to `2.20.0` only under a zero-alert/low-alert decision, or record a bounded acceptance. |
| 23 | medium; `pytest 8.4.2` | [GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g), CVE-2025-71176; `<9.0.3`; `9.0.3`; `2026-01-22T06:30:29Z`/`2026-04-13T16:38:47Z` | Titanoboa dependency and the repository-wide validation runner. On Unix, predictable per-user tmp directories expose local cross-user DoS/possible privilege effects. Candidate pytest resolves to `9.0.3`, but requires exact S1 reapproval and full compatibility proof; Vyper's optional test/dev metadata says `<9`. Upgrade or complete time-bounded exception is required before deployment rehearsal under the proposed policy. |
| 24 | medium; lock `python-dotenv 1.2.1` | [GHSA-mf9w-mj56-hr94](https://github.com/advisories/GHSA-mf9w-mj56-hr94), CVE-2026-28684; `<1.2.2`; `1.2.2`; `2026-04-21T14:38:57Z`/`2026-04-21T14:38:59Z` | `dotenv -> python-dotenv`. `scripts/console.py` and `scripts/utils/migration_helpers.py` call only `load_dotenv()`; neither `set_key()` nor `unset_key()` is used, so the advisory's symlink-following write path is not reached. Upgrade to `1.2.2` in Candidate A and test load/search/parsing/interpolation/precedence. |
| 25 | high; `urllib3 2.5.0` | [GHSA-qccp-gfcp-xxvc](https://github.com/advisories/GHSA-qccp-gfcp-xxvc), CVE-2026-44431; `>=1.23,<2.7.0`; `2.7.0`; `2026-05-11T14:51:20Z`/`2026-05-14T20:35:54Z` | Affects sensitive headers on cross-origin redirects from pools made with low-level `ProxyManager.connection_from_url`. Repository code has no direct urllib3/ProxyManager/adapter/Retry use, so that exact construction is not demonstrated; deployment HTTP does handle credentials and proxies transitively. Upgrade to `2.7.0` in Candidate A and validate redirects/proxies/headers. |
| 26 | medium; `idna 3.10` | [GHSA-65pc-fj4g-8rjx](https://github.com/advisories/GHSA-65pc-fj4g-8rjx), CVE-2026-45409; `<3.15`; `3.15`; `2026-05-19T14:34:32Z`/`2026-07-08T17:35:41Z` | `requests -> idna`; RPC/explorer hostnames reach encoding through Requests. Exploitation needs arbitrarily large crafted Unicode input; configured endpoints are expected to be owner-controlled, but the HTTP boundary is deployment-relevant. Upgrade to `3.15` in Candidate A and test normal/Unicode/oversized hostname acceptance and rejection. |
| 27 | medium; `pymdown-extensions 10.16.1` | [GHSA-62q4-447f-wv8h](https://github.com/advisories/GHSA-62q4-447f-wv8h), CVE-2026-46338; `>=10.0.1,<=10.21.2`; `10.21.3`; `2026-05-19T20:00:29Z`/`2026-05-19T20:00:30Z` | `titanoboa -> mkdocs-material -> pymdown-extensions`. No repository MkDocs/Pymdown build configuration or direct import was found; the vulnerable snippets traversal is not reached by a repository docs build. Candidate docs upgrades to `10.21.3`; land separately or leave explicitly open per owner policy. |

## Dependency and repository reachability map

| Direct input / package path | Alert packages and repository consumers |
| --- | --- |
| `titanoboa -> requests -> urllib3, idna` | Titanoboa runtime plus direct repository Requests imports in `scripts/utils/verify_etherscan.py`, `scripts/utils/safe_account.py`, `scripts/probes/stock_token_transfer_probe.py`, and `tests/conf_env.py`. Verifier and Safe calls omit explicit timeouts; the probe uses `timeout=30` and `raise_for_status`; the test path makes a local HEAD request. No direct urllib3, HTTPAdapter, Retry, proxy-manager, or pool call exists. |
| `dotenv -> python-dotenv` | `scripts/console.py` and `scripts/utils/migration_helpers.py` call `load_dotenv()` at import. No `set_key()`/`unset_key()` use exists. `.env` is ignored. |
| `vyper -> cbor2, wheel` | Compiler/build dependencies; no direct repository cbor2 or wheel import. Their behavior can still affect compilation, package installation, bytecode, and artifact evidence. |
| `titanoboa -> pytest` | S1 exact-version gate, repository collection/fixtures/plugins/assertions/warnings/teardown, and all mandatory validation. `tests/conftest.py` defines repository-wide plugin/fixture behavior. |
| `titanoboa -> mkdocs-material -> pymdown-extensions, Pygments` | No repository MkDocs/Pymdown configuration or build command was found. Pygments is also reached by IPython, pytest, and Rich, so it can affect console/test output even though the vulnerable lexer is not directly selected. |

## Primary upstream release and metadata review

The following findings cover the versions traversed by the realized
candidates. Primary references are included so the checkpoint reviewer can
verify the selection boundary.

### Requests and urllib3

- Requests 2.33.0 fixes only direct use of
  `requests.utils.extract_zipped_paths` for this alert; the advisory states
  ordinary Requests use is unaffected. The release also changes packaging,
  typing, netrc handling, and drops Python 3.9, none of which conflicts with
  Python 3.12 or a direct repository API found here. Primary:
  [Requests history](https://raw.githubusercontent.com/psf/requests/main/HISTORY.md)
  and [GHSA-gc5v-m9x4-r6x2](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2).
- urllib3 2.6.0 caps encoding chains, changes compressed streaming behavior,
  and temporarily removed `HTTPResponse.getheaders/getheader` before 2.6.1
  restored them. Version 2.6.3 fixes redirect bypass and caps long
  `Retry-After` values. Version 2.7.0 fixes the proxied cross-origin sensitive
  header issue, changes warnings, drops Python 3.9/PyPy 3.10, raises the
  pyOpenSSL floor, and fixes partial-read/cache/location behavior. The
  repository uses Requests, not those removed low-level APIs, but Stage B must
  compare redirects, retries, proxies, TLS/certificates, adapters, pooling,
  timeouts, response decoding, and exception behavior. Primary:
  [urllib3 changelog](https://raw.githubusercontent.com/urllib3/urllib3/main/CHANGES.rst).

### idna and python-dotenv

- idna 3.11 through 3.15 update Unicode/UTS-46 data and classification, add
  earlier long-input rejection, and extend the cap to alternate conversion
  functions. Those Unicode changes can alter hostname acceptance independent
  of the security fix. Primary:
  [idna 3.15 release](https://github.com/kjd/idna/releases/tag/v3.15) and
  [GHSA-65pc-fj4g-8rjx](https://github.com/advisories/GHSA-65pc-fj4g-8rjx).
- python-dotenv 1.2.2 adds Python 3.14 support, preserves file modes, and
  deliberately changes `set_key`/`unset_key` symlink behavior with a
  `follow_symlinks` option. The repository uses only the read/load path, but
  Stage B must prove search, parsing, interpolation, and precedence. Primary:
  [python-dotenv changelog](https://raw.githubusercontent.com/theskumar/python-dotenv/main/CHANGELOG.md)
  and [GHSA-mf9w-mj56-hr94](https://github.com/advisories/GHSA-mf9w-mj56-hr94).

### cbor2 and wheel

- cbor2 5.8.0 clears shareables on decoder reuse. Version 5.9.0 adds a default
  maximum decode depth of 400, changes decode read sizing for compatibility,
  disables the prior date-encoding default, renames `FrozenDict`, adds decoder
  controls, and drops Python 3.9. Those changes require known-vector,
  stream-position, compiler, ABI, creation/runtime-bytecode, and artifact
  comparisons rather than reliance on a resolver result. Primary:
  [cbor2 version history](https://cbor2.readthedocs.io/en/latest/versionhistory.html).
- wheel 0.46.x drops Python 3.8, removes old internals and vendored packaging,
  then 0.46.2 restores `bdist_wheel` compatibility for older setuptools and
  fixes unsafe chmod path construction while unpacking. Python 3.12 is
  supported, but clean installation and environment metadata must be
  reproduced. Primary:
  [wheel release notes](https://wheel.readthedocs.io/en/latest/news.html) and
  [GHSA-8rrh-rw8j-w5fx](https://github.com/advisories/GHSA-8rrh-rw8j-w5fx).

### pytest, Titanoboa, and Vyper

- pytest 9.0 adds native TOML configuration, strict-mode behavior, subtests,
  removals/deprecations, and collection/reporting/plugin changes; 9.0.1 and
  9.0.2 repair compatibility regressions, and 9.0.3 is the first advisory-fixed
  release. This repository has no pytest configuration file but makes broad
  use of fixtures, monkeypatching, warnings, assertions, exception matching,
  plugins, and collection behavior. Primary:
  [pytest 9 changelog](https://docs.pytest.org/en/9.0.x/changelog.html) and
  [GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g).
- Installed/public package metadata for Titanoboa 0.2.7 requires
  `vyper>=0.4.2` and pytest without an upper bound. Vyper 0.4.3 requires
  Python `>=3.10,<4`, `cbor2>=5.4.6,<6`, and wheel; its optional `test` and
  `dev` extras require `pytest>=8,<9`. Primary metadata:
  [Titanoboa 0.2.7](https://pypi.org/project/titanoboa/0.2.7/) and
  [Vyper 0.4.3](https://pypi.org/project/vyper/0.4.3/).
- The pytest 9 candidate resolves because neither optional Vyper extra is
  selected by the protocol lock. That does not establish compatibility with
  Vyper's own supported test profile. Stage B must first show the unchanged S1
  exact-version failure, then update the exact expectation only if approved,
  and re-prove collection, plugins, fixtures, warnings, assertions, teardown,
  S1 primitives, S2/S3, artifacts, and the full suite.

### Pymdown Extensions and Pygments

- Pymdown Extensions 10.17 through 10.21.3 add and alter Markdown block,
  caption, quote, emoji, critic, highlight, and regex behavior; 10.21.3 fixes
  the `restrict_base_path` snippets traversal. There is no repository docs
  build reaching it, so it is separable from the deployment gate. Primary:
  [Pymdown changelog](https://facelessuser.github.io/pymdown-extensions/about/changelog/)
  and [GHSA-62q4-447f-wv8h](https://github.com/advisories/GHSA-62q4-447f-wv8h).
- Pygments 2.20.0 changes multiple lexers and fixes catastrophic
  backtracking in the Archetype GUID/ID patterns. No direct repository path
  selects that lexer; this is low-severity console/docs/test tooling exposure.
  Primary:
  [Pygments changelog](https://pygments.org/docs/changelog/) and
  [GHSA-5239-wwwm-4pmq](https://github.com/advisories/GHSA-5239-wwwm-4pmq).

### First patched versus current latest

The candidate plans intentionally use the smallest supported patch for each
recorded advisory; they do not imply that the first patch is the newest
release. Public PyPI project metadata was re-queried at
`2026-07-24T17:26Z`:

| Package | Current lock | Candidate / first patch needed here | PyPI latest | Checkpoint consequence |
| --- | ---: | ---: | ---: | --- |
| urllib3 | 2.5.0 | 2.7.0 | 2.7.0 | Candidate is latest and is required by alert #25. |
| cbor2 | 5.7.0 | 5.9.0 | 6.1.3 | Latest is incompatible with Vyper 0.4.3's `cbor2<6`; do not substitute it without a separate Vyper decision. |
| wheel | 0.45.1 | 0.46.2 | 0.47.0 | Latest adds post-patch change surface; owner must choose minimal patch versus separately reviewed latest. |
| Requests | 2.32.5 | 2.33.0 | 2.34.2 | Later releases exist; Candidate A deliberately minimizes HTTP behavior churn. |
| Pygments | 2.19.2 | 2.20.0 | 2.20.0 | Candidate is latest. |
| pytest | 8.4.2 | 9.0.3 | 9.1.1 | Both cross the Vyper optional-extra `<9` boundary; later 9.x adds more unreviewed behavior. |
| python-dotenv | 1.2.1 | 1.2.2 | 1.2.2 | Candidate is latest. |
| idna | 3.10 | 3.15 | 3.18 | Later Unicode/normalization changes exist; Candidate A minimizes that behavior delta. |
| Pymdown Extensions | 10.16.1 | 10.21.3 | 11.0.1 | Latest crosses a major boundary; the docs-only candidate stays on patched 10.x. |
| Titanoboa | 0.2.7 | held 0.2.7 | 0.2.8 | A Titanoboa change is outside Candidate A and requires separate approval/S1 evidence. |
| Vyper | 0.4.3 | held 0.4.3 | 0.4.3 | Current compiler remains latest and exactly held. |

Primary metadata:
[urllib3](https://pypi.org/project/urllib3/),
[cbor2](https://pypi.org/project/cbor2/),
[wheel](https://pypi.org/project/wheel/),
[Requests](https://pypi.org/project/requests/),
[Pygments](https://pypi.org/project/Pygments/),
[pytest](https://pypi.org/project/pytest/),
[python-dotenv](https://pypi.org/project/python-dotenv/),
[idna](https://pypi.org/project/idna/),
[Pymdown Extensions](https://pypi.org/project/pymdown-extensions/),
[Titanoboa](https://pypi.org/project/titanoboa/), and
[Vyper](https://pypi.org/project/vyper/).

These latest-version observations expand checkpoint decision 2; they do not
select a later version. Any non-candidate version needs its own release-note,
resolver, compatibility, and artifact review.

## K-01 disposable resolver provenance

K-01 was owner-approved in the brief on 24 July 2026. The approved installed
seed was `~/.pyenv/versions/ripe-lite/bin/python`, resolving to
`~/.pyenv/versions/3.12.0/bin/python3.12`; the binary SHA-256 was
`d23fa2c326127c9590d097603f105d69e68774968f46246fc7a8a80103600765`.
It reported CPython 3.12.0 on macOS arm64.

The disposable venv was created outside the repository. The exact install
used only the public Python Package Index and no cache:

```text
DISPOSABLE_VENV/bin/python -m pip install \
  --no-cache-dir --index-url https://pypi.org/simple pip-tools==7.4.1
```

The first download attempt encountered a transient read timeout and retried;
installation then succeeded. The complete tool inventory was:

```text
build==1.5.0
click==8.4.2
packaging==26.2
pip==23.2.1
pip-tools==7.4.1
pyproject_hooks==1.2.0
setuptools==83.0.0
wheel==0.47.0
```

`pip check` reported no broken requirements. Each candidate directory received
both its proposed `requirements.in` and a byte-for-byte copy of the frozen
`requirements.txt` before compilation. That existing output is a material
resolver input: pip-compile preserves compatible frozen pins when it is not
given `--upgrade`, which is how the trials avoid an unrelated broad refresh.
The candidate resolver command was then run separately from inside each
candidate directory:

```text
env PIP_CONFIG_FILE=/dev/null \
  PIP_INDEX_URL=https://pypi.org/simple \
  PIP_EXTRA_INDEX_URL= \
  PIP_NO_CACHE_DIR=1 \
  DISPOSABLE_VENV/bin/pip-compile \
  --cache-dir=DISPOSABLE_PIP_TOOLS_CACHE \
  --index-url=https://pypi.org/simple \
  --no-emit-index-url \
  --output-file=requirements.txt requirements.in
```

That exact environment-wrapped invocation caused pip-tools 7.4.1 to emit this
command-header form in every candidate lock:

```text
pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in
```

The form truthfully reflects the completed candidate runs, but differs from
the frozen repository lock's clean `pip-compile requirements.in` header.
Neither header form is approved for Stage B. Checkpoint decision 7 must name
the exact generation invocation and its expected emitted header. Stage B must
not manually normalize the header or commit a header that differs from the
approved command; an unexpected header is a blocking lock diff.

An initial command without the explicit disposable `--cache-dir` stopped with
`PermissionError` when pip-tools tried to use the user cache. It did not
change the repository or install a candidate. The corrected command above
kept all resolver cache/output under the disposable root and succeeded.

Reviewer follow-up repeated K-01 from a new Python 3.12.0 venv and the same
public-index/tool inventory at `2026-07-24T17:29:31Z`. A deliberately observed
control run without seeding the frozen output produced broad current-index
churn, proving the frozen-output step above is essential rather than cosmetic.
After restoring the frozen output, all four candidate input and lock hashes
reproduced exactly. Each literal diff below was mechanically compared
byte-for-byte with its regenerated lock before disposal. The diffs are
committed below so future review does not depend on hash preimages or a
mutable package index.

No candidate lock was installed, no auditor was installed or run, no version
was selected for production, and the worktree remained unchanged. The original
venv, cache, copied inputs, and candidate locks were destroyed after the hashes
and results below were recorded. The follow-up K-01 venv, cache, copied inputs,
and candidate locks were likewise destroyed after the literal diffs were
recorded in this evidence. K-02's recovered raw response and canonical
projection are the deliberate outside-repository exception retained for
checkpoint review as described above.

## Realized candidate plans and complete lock deltas

Every listed direct-input addition is a semantic constraint change because
the corresponding package is currently transitive. The proposed safe initial
form is an exact pin for the checkpoint-selected profile. A transitive pin
should be removed only after the direct upstream dependency metadata
guarantees the same patched compatible floor and a fresh resolver/security
review proves its removal causes no float or alert regression.

All four trials explicitly pin `titanoboa==0.2.7`; every trial also pins the
selected exact pytest version. `vyper==0.4.3`, `rlp~=4.0.1`, `ipython`, and
`dotenv` are held. Apart from pip-compile's truthful command header and
“via -r requirements.in” annotations, the version deltas below are the entire
lock delta.

### Candidate A — non-pytest deployment-path refresh

Proposed direct-input additions/changes:

```text
titanoboa==0.2.7
pytest==8.4.2
requests==2.33.0
urllib3==2.7.0
idna==3.15
python-dotenv==1.2.2
cbor2==5.9.0
wheel==0.46.2
```

| Package | Old | Candidate |
| --- | --- | --- |
| cbor2 | 5.7.0 | 5.9.0 |
| idna | 3.10 | 3.15 |
| python-dotenv | 1.2.1 | 1.2.2 |
| requests | 2.32.5 | 2.33.0 |
| urllib3 | 2.5.0 | 2.7.0 |
| wheel | 0.45.1 | 0.46.2 |

Input SHA-256:
`2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d`.
Lock SHA-256:
`d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce`.
Residual alerts: #22 Pygments, #23 pytest, #27 Pymdown Extensions. Candidate A
can be reviewed independently but cannot by itself satisfy the proposed
deployment policy because mandatory validation still uses vulnerable pytest.

### Candidate pytest — Candidate A plus the pytest decision

The Candidate A inputs are retained and `pytest==8.4.2` becomes
`pytest==9.0.3`. The complete additional lock delta is only
`pytest 8.4.2 -> 9.0.3`; no other package version changes. Input SHA-256:
`2b19212edd68b20efba3d9e1a9d87f927dd9330635c2c55bc6d728fdb56182de`.
Lock SHA-256:
`e2af4c1452869aca5f63ffa22e2ac64397cdc929a6e7036a858d08890f0f5c07`.
Residual alerts: #22 and #27.

It cannot land without the Stage B exact S1 update/reapproval and complete
old/new validation. The known metadata conflict with Vyper's optional
`test`/`dev` extras must be explicitly accepted, paired with an approved
Vyper/Titanoboa path, or treated as an upstream blocker.

### Candidate docs — separable documentation-only sub-slice

The current direct inputs are retained; the trial explicitly pins
`titanoboa==0.2.7`, `pytest==8.4.2`, and
`pymdown-extensions==10.21.3`. The only package-version delta is
`pymdown-extensions 10.16.1 -> 10.21.3`. Input SHA-256:
`26dbc8c747adb0f91ca9ecb7da8db23a32d5bedc8dc36655f3be43825a66b7fb`.
Lock SHA-256:
`d064cd53a4c37a28fb9c561fe3eaae9126f99da3dc0b9f2ab5fc67a09642fb86`.
The other 12 alerts remain. This may land separately only after an owner
policy and Stage B validation; it does not close the deployment gate.

### Candidate zero — optional zero-open-alert profile

Candidate pytest is retained and exact direct pins
`pymdown-extensions==10.21.3` and `Pygments==2.20.0` are added. The complete
version delta from the current lock is:

| Package | Old | Candidate |
| --- | --- | --- |
| cbor2 | 5.7.0 | 5.9.0 |
| idna | 3.10 | 3.15 |
| Pygments | 2.19.2 | 2.20.0 |
| pymdown-extensions | 10.16.1 | 10.21.3 |
| pytest | 8.4.2 | 9.0.3 |
| python-dotenv | 1.2.1 | 1.2.2 |
| requests | 2.32.5 | 2.33.0 |
| urllib3 | 2.5.0 | 2.7.0 |
| wheel | 0.45.1 | 0.46.2 |

Input SHA-256:
`c5d2e05d395722f4acb5184748665e553ce1d2286a5474633f62224ebde613a4`.
Lock SHA-256:
`b74b693a52d5b0b0f525bf9aae502af7936a35c52145ea54b8843bb7ccd10622`.
The candidate lock contains no version in the 13 recorded vulnerable ranges.
That is a prediction from resolution, not an audit or authoritative alert
closure.

### Literal realized lock diffs

These are the complete `diff -u` outputs from the frozen lock to each
reproduced candidate lock. They include the command-header and dependency-path
annotation changes that the version tables summarize.

#### Candidate A

```diff
--- requirements.txt
+++ candidate-a/requirements.txt
@@ -2,7 +2,7 @@
 # This file is autogenerated by pip-compile with Python 3.12
 # by the following command:
 #
-#    pip-compile requirements.in
+#    pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in
 #
 annotated-types==0.7.0
     # via pydantic
@@ -18,8 +18,10 @@
     # via eth-account
 cached-property==2.0.1
     # via py-evm
-cbor2==5.7.0
-    # via vyper
+cbor2==5.9.0
+    # via
+    #   -r requirements.in
+    #   vyper
 certifi==2025.8.3
     # via requests
 charset-normalizer==3.4.3
@@ -94,8 +96,10 @@
     #   trie
 hypothesis==6.138.15
     # via titanoboa
-idna==3.10
-    # via requests
+idna==3.15
+    # via
+    #   -r requirements.in
+    #   requests
 immutables==0.21
     # via vyper
 iniconfig==2.1.0
@@ -147,6 +151,7 @@
     #   pytest
     #   vvm
     #   vyper
+    #   wheel
 paginate==0.5.7
     # via mkdocs-material
 parsimonious==0.10.0
@@ -196,14 +201,17 @@
     # via mkdocs-material
 pytest==8.4.2
     # via
+    #   -r requirements.in
     #   pytest-cov
     #   titanoboa
 pytest-cov==7.0.0
     # via titanoboa
 python-dateutil==2.9.0.post0
     # via ghp-import
-python-dotenv==1.2.1
-    # via dotenv
+python-dotenv==1.2.2
+    # via
+    #   -r requirements.in
+    #   dotenv
 pyyaml==6.0.2
     # via
     #   mkdocs
@@ -216,8 +224,9 @@
     # via
     #   mkdocs-material
     #   parsimonious
-requests==2.32.5
+requests==2.33.0
     # via
+    #   -r requirements.in
     #   mkdocs-material
     #   titanoboa
     #   vvm
@@ -257,8 +266,10 @@
     #   typing-inspection
 typing-inspection==0.4.1
     # via pydantic
-urllib3==2.5.0
-    # via requests
+urllib3==2.7.0
+    # via
+    #   -r requirements.in
+    #   requests
 vvm==0.3.2
     # via titanoboa
 vyper==0.4.3
@@ -269,5 +280,7 @@
     # via mkdocs
 wcwidth==0.2.14
     # via prompt-toolkit
-wheel==0.45.1
-    # via vyper
+wheel==0.46.2
+    # via
+    #   -r requirements.in
+    #   vyper
```

#### Candidate pytest

```diff
--- requirements.txt
+++ candidate-pytest/requirements.txt
@@ -2,7 +2,7 @@
 # This file is autogenerated by pip-compile with Python 3.12
 # by the following command:
 #
-#    pip-compile requirements.in
+#    pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in
 #
 annotated-types==0.7.0
     # via pydantic
@@ -18,8 +18,10 @@
     # via eth-account
 cached-property==2.0.1
     # via py-evm
-cbor2==5.7.0
-    # via vyper
+cbor2==5.9.0
+    # via
+    #   -r requirements.in
+    #   vyper
 certifi==2025.8.3
     # via requests
 charset-normalizer==3.4.3
@@ -94,8 +96,10 @@
     #   trie
 hypothesis==6.138.15
     # via titanoboa
-idna==3.10
-    # via requests
+idna==3.15
+    # via
+    #   -r requirements.in
+    #   requests
 immutables==0.21
     # via vyper
 iniconfig==2.1.0
@@ -147,6 +151,7 @@
     #   pytest
     #   vvm
     #   vyper
+    #   wheel
 paginate==0.5.7
     # via mkdocs-material
 parsimonious==0.10.0
@@ -194,16 +199,19 @@
     #   rich
 pymdown-extensions==10.16.1
     # via mkdocs-material
-pytest==8.4.2
+pytest==9.0.3
     # via
+    #   -r requirements.in
     #   pytest-cov
     #   titanoboa
 pytest-cov==7.0.0
     # via titanoboa
 python-dateutil==2.9.0.post0
     # via ghp-import
-python-dotenv==1.2.1
-    # via dotenv
+python-dotenv==1.2.2
+    # via
+    #   -r requirements.in
+    #   dotenv
 pyyaml==6.0.2
     # via
     #   mkdocs
@@ -216,8 +224,9 @@
     # via
     #   mkdocs-material
     #   parsimonious
-requests==2.32.5
+requests==2.33.0
     # via
+    #   -r requirements.in
     #   mkdocs-material
     #   titanoboa
     #   vvm
@@ -257,8 +266,10 @@
     #   typing-inspection
 typing-inspection==0.4.1
     # via pydantic
-urllib3==2.5.0
-    # via requests
+urllib3==2.7.0
+    # via
+    #   -r requirements.in
+    #   requests
 vvm==0.3.2
     # via titanoboa
 vyper==0.4.3
@@ -269,5 +280,7 @@
     # via mkdocs
 wcwidth==0.2.14
     # via prompt-toolkit
-wheel==0.45.1
-    # via vyper
+wheel==0.46.2
+    # via
+    #   -r requirements.in
+    #   vyper
```

#### Candidate docs

```diff
--- requirements.txt
+++ candidate-docs/requirements.txt
@@ -2,7 +2,7 @@
 # This file is autogenerated by pip-compile with Python 3.12
 # by the following command:
 #
-#    pip-compile requirements.in
+#    pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in
 #
 annotated-types==0.7.0
     # via pydantic
@@ -192,10 +192,13 @@
     #   mkdocs-material
     #   pytest
     #   rich
-pymdown-extensions==10.16.1
-    # via mkdocs-material
+pymdown-extensions==10.21.3
+    # via
+    #   -r requirements.in
+    #   mkdocs-material
 pytest==8.4.2
     # via
+    #   -r requirements.in
     #   pytest-cov
     #   titanoboa
 pytest-cov==7.0.0
```

#### Candidate zero

```diff
--- requirements.txt
+++ candidate-zero/requirements.txt
@@ -2,7 +2,7 @@
 # This file is autogenerated by pip-compile with Python 3.12
 # by the following command:
 #
-#    pip-compile requirements.in
+#    pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in
 #
 annotated-types==0.7.0
     # via pydantic
@@ -18,8 +18,10 @@
     # via eth-account
 cached-property==2.0.1
     # via py-evm
-cbor2==5.7.0
-    # via vyper
+cbor2==5.9.0
+    # via
+    #   -r requirements.in
+    #   vyper
 certifi==2025.8.3
     # via requests
 charset-normalizer==3.4.3
@@ -94,8 +96,10 @@
     #   trie
 hypothesis==6.138.15
     # via titanoboa
-idna==3.10
-    # via requests
+idna==3.15
+    # via
+    #   -r requirements.in
+    #   requests
 immutables==0.21
     # via vyper
 iniconfig==2.1.0
@@ -147,6 +151,7 @@
     #   pytest
     #   vvm
     #   vyper
+    #   wheel
 paginate==0.5.7
     # via mkdocs-material
 parsimonious==0.10.0
@@ -185,25 +190,31 @@
     #   eth-utils
 pydantic-core==2.33.2
     # via pydantic
-pygments==2.19.2
+pygments==2.20.0
     # via
+    #   -r requirements.in
     #   ipython
     #   ipython-pygments-lexers
     #   mkdocs-material
     #   pytest
     #   rich
-pymdown-extensions==10.16.1
-    # via mkdocs-material
-pytest==8.4.2
+pymdown-extensions==10.21.3
+    # via
+    #   -r requirements.in
+    #   mkdocs-material
+pytest==9.0.3
     # via
+    #   -r requirements.in
     #   pytest-cov
     #   titanoboa
 pytest-cov==7.0.0
     # via titanoboa
 python-dateutil==2.9.0.post0
     # via ghp-import
-python-dotenv==1.2.1
-    # via dotenv
+python-dotenv==1.2.2
+    # via
+    #   -r requirements.in
+    #   dotenv
 pyyaml==6.0.2
     # via
     #   mkdocs
@@ -216,8 +227,9 @@
     # via
     #   mkdocs-material
     #   parsimonious
-requests==2.32.5
+requests==2.33.0
     # via
+    #   -r requirements.in
     #   mkdocs-material
     #   titanoboa
     #   vvm
@@ -257,8 +269,10 @@
     #   typing-inspection
 typing-inspection==0.4.1
     # via pydantic
-urllib3==2.5.0
-    # via requests
+urllib3==2.7.0
+    # via
+    #   -r requirements.in
+    #   requests
 vvm==0.3.2
     # via titanoboa
 vyper==0.4.3
@@ -269,5 +283,7 @@
     # via mkdocs
 wcwidth==0.2.14
     # via prompt-toolkit
-wheel==0.45.1
-    # via vyper
+wheel==0.46.2
+    # via
+    #   -r requirements.in
+    #   vyper
```

## S3 sequencing and artifact consequence

At H-01 bootstrap, the S3 worktree was clean at
`23697faca5f522fd840be68f749a9237ab38c270`, based on
`f0bfd0fd5ac2be1d27321463b77248c7cd91d829`. It had production source and
test changes, artifact evidence, and a corrected Gate 1 record, but no
immutable owner Gate 1 approval or inventory reconciliation.

During Stage A, the S3 branch independently advanced through
`51e5c5a47ac74083affb16516cd07dd8321c0fbb` and then to
`22ece8f560b40f25e6ad2a651c9829fe2baf2120`. Commit `db7ae89` records owner
Gate 1 approval, `51e5c5a` reconciles the checked clock inventory, and
`22ece8f` records the green ordered Stage 2 evidence: 59 Lootbox reward tests,
91 Switchboard Charlie tests, 175 full Lootbox tests, 57 S1 tests, 60
inventory tests, a clean inventory checker, and 2,722 full-suite passes with
142 deselected.

Reviewer follow-up observed a later S3 documentation-only clarification,
`c823300c7af418a7b226093e3a9ddf1d970e1998`, at
`2026-07-24T17:32:56Z`. It changes only the S3 implementation record and does
not close Gate 2. The branch remains clean and is not an ancestor of `rh`. Its
mandatory independent reviewer Gate 2, production-contract security/audit
review, rollout decisions, owner merge/push, and integration remain open.

Every realized H-01 candidate changes at least cbor2 and wheel, which are
Vyper/compiler/build inputs. Candidate pytest and candidate zero also change
the mandatory test runner. H-01-first would stale S3's compiler/runtime,
artifact, validation, and reviewer evidence and require deliberate baseline
refresh plus repetition of both reviewer gates. No owner authorized that
expense.

After S3 integrates and the owner directs reconciliation, Stage B must repeat
at minimum:

- the exact S1 version/runtime/fingerprint gate;
- `tests/core/lootbox/test_underscore_rewards.py`;
- `tests/config/test_switchboard_charlie.py`;
- the checked clock-inventory script and inventory test;
- pytest collection and the full serial suite;
- deterministic ABI inventory/hash comparisons;
- representative creation/runtime bytecode fingerprints; and
- every S3 artifact/reviewer assertion affected by Python, pip, pip-tools,
  pytest, Titanoboa, Vyper, cbor2, wheel, or resolver output.

## Stage A validation record

The integration baseline and isolated worktree used the unchanged starting
commit and dependency environment. The exact initial S1 command without a
placeholder stopped during collection because `ETHERSCAN_API_KEY` was absent.
The S3 record already sanctions the non-secret value `local-placeholder` for
offline test collection, but that provenance is on the unintegrated,
reviewer-Gate-2-pending S3 branch rather than integrated `rh` authority. The
value is still manifestly non-secret and no live explorer call or secret access
occurred. The effective reruns set that value and this authority limitation is
not treated as checkpoint approval.

| Command | Result |
| --- | --- |
| `python --version` | `Python 3.12.0` |
| `python -m pip --version` | pip `25.2`, Python 3.12 |
| `python -m pip check` | `No broken requirements found.` |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py` | 57 passed in 28.57 s; 67.38 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. python scripts/check_block_clock_inventory.py --check` | `CLOCK_INVENTORY_OK`; 1.38 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py` | 56 passed in 25.02 s; 26.89 s wall |
| initial `... pytest --collect-only -q` in the managed sandbox | stopped with two collection errors because Titanoboa attempted to create missing compiler-cache entries under the non-writable user cache; 2,539/2,681 selected cases reached before interruption |
| cache-disabled equivalent collection | 2,699/2,841 collected, 142 deselected, in 1.52 s; this introduced only expected pre-import assertion-rewrite warnings |
| canonical `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest --collect-only -q` after the contract-approved baseline populated the missing compiler cache | 2,699/2,841 collected, 142 deselected, in 1.24 s; 2.64 s wall |
| canonical `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q` | 2,699 passed, 142 deselected in 310.03 s; 370.57 s wall |
| reviewer-correction replay: `python -m pip check` and `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py` | no broken requirements; 57 passed in 28.28 s; 67.13 s wall |

The reviewer-correction replay intentionally did not repeat collection,
inventory, or the full suite. That correction changed only this evidence
record and did not change dependencies, tests, configuration, source,
artifacts, or the baseline runtime, so the original complete baseline result
remains applicable; `pip check` plus exact S1 replay checked dependency
consistency and the exact S1 version/runtime/fingerprint assertions. Any
dependency, test, source, configuration, artifact, or runtime-profile change
would invalidate that rationale and require the complete ordered validation
again.

The canonical full suite initially required managed-filesystem approval solely
to create Titanoboa compiler-cache entries outside the worktree. It used the
unchanged dependency profile and no network or live service. It was an
environment-permission correction, not a test, source, dependency, or
assertion change, but it was also a second non-repository side effect beyond
the brief's statement that K-01 would be the sole such side effect. The
mandated baseline made compiler-cache population practically unavoidable in
this managed environment; the exception was not concealed or converted into a
broader authorization. Future briefs should explicitly permit or redirect the
baseline compiler cache to a disposable path. A pre-worktree run at the same
starting commit also passed 2,699 tests with 142 deselected.

### Operational command record

The following records all material command families used in Stage A. Repeated
`sed`/`rg`/`git show` reads differed only in file or search target and were
read-only.

```text
# Freeze/overlap checks
git status --short --branch
git rev-parse rh
git worktree list --porcelain
git branch --list rh-track-7-h1-dependency-security
git diff --name-only <active-branch>...rh -- <owned paths>
git merge-base --is-ancestor <S1-or-S2-head> rh
git ls-remote --heads origin rh
git ls-remote --heads origin rh-track-7-h1-dependency-security
shasum -a 256 <frozen inputs>

# Isolated worktree creation (first ref-lock attempt blocked by the
# managed sandbox; approved repeat succeeded)
git -C ~/dev/ripe-protocol worktree add \
  -b rh-track-7-h1-dependency-security \
  ~/dev/ripe-protocol-track-7-h1-dependency-security rh

# Local metadata/reachability reads
python --version
python -m pip --version
python -m pip check
python -m pip show <selected package>
python -c '<importlib.metadata version/Requires-Python/Requires-Dist read>'
rg -n '<package/import/API patterns>' <required source surfaces>

# K-02; raw output redirected outside the repository
gh api --method GET --paginate --slurp \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  '/repos/Ripe-Foundation/ripe-protocol/dependabot/alerts?state=open&per_page=100'
jq '<sanitized alert projection>' <outside-repository raw response>
shasum -a 256 <raw response> <sanitized projection>
install -m 600 <raw response and projection> \
  ~/dev/ripe-protocol-h1-private-evidence/

# Public latest-version comparison
curl -fsSL https://pypi.org/pypi/<package>/json

# K-01
python -m venv <disposable venv>
<disposable python> -m pip install --no-cache-dir \
  --index-url https://pypi.org/simple pip-tools==7.4.1
<disposable python> -m pip list --format=freeze
<disposable python> -m pip check
cp <frozen requirements.txt> <candidate directory>/requirements.txt
env PIP_CONFIG_FILE=/dev/null PIP_INDEX_URL=https://pypi.org/simple \
  PIP_EXTRA_INDEX_URL= PIP_NO_CACHE_DIR=1 \
  <disposable pip-compile> --cache-dir=<disposable cache> \
  --index-url=https://pypi.org/simple --no-emit-index-url \
  --output-file=requirements.txt requirements.in
diff -u <frozen lock> <candidate lock>
shasum -a 256 <candidate inputs and locks>

# Contract validation; ETHERSCAN_API_KEY is the documented non-secret
# collection placeholder
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  pytest -q tests/clock/test_clock_profiles.py
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  python scripts/check_block_clock_inventory.py --check
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  pytest -q tests/inventory/test_block_clock_inventory.py
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest --collect-only -q
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q
git diff --check

# Final scope/sanitization/disposal checks
git status --short --branch
git diff --no-index --check /dev/null \
  docs/chains/rh/evidence/dependency-security-gate.md
stat <retained raw response and projection>
shasum -a 256 <retained raw response and projection>
rg -n -i '<credential, token, private URL, username patterns>' \
  docs/chains/rh/evidence/dependency-security-gate.md
rm -rf <exact validated K-01 venv, cache, and candidate directories>
```

Final pre-stage checks found exactly one untracked file, this evidence record.
`git diff --check` was clean; `git diff --no-index --check /dev/null` against
this new file emitted no whitespace diagnostics (its exit 1 means the expected
content difference exists). No prohibited tracked venv/cache/wheel/raw-response
path and no high-confidence credential, authenticated URL, or unsanitized home
path pattern was found. The original exact K-01 disposable root was absent.
After reviewer correction, the repeated K-01 venv, cache, and candidate
directories were also absent; only the deliberately retained, mode-`0600`
K-02 raw/projection files exist outside the repository. The same scope and
sanitization checks must be repeated after staging and before commit.

## Residual-risk register and blockers

| Risk or blocker | Current state and required control |
| --- | --- |
| Authoritative default-branch alerts | All 13 remain open as of the snapshot. Candidate resolution cannot close them before an observed merged manifest. |
| Candidate evidence depth | No candidate was installed or audited under K-01. Resolver success proves neither runtime compatibility nor absence of newly surfaced vulnerabilities. Stage B tooling/commands need approval. |
| Resolver reproducibility | The candidate hashes reproduced only when the frozen output lock was supplied to pip-compile; a no-output control floated broad current-index packages. Literal Stage A diffs are now committed, but mutable index state still requires a fresh full Stage B diff review even when hashes match. Any mismatch blocks implementation until every changed line is explained and approved. |
| Lock command/header form | The isolated K-01 wrapper emitted expanded `--cert=None`/`--client-cert=None`/`--pip-args=None` header arguments rather than the frozen lock's clean header. Decision 7 must approve one exact invocation and truthful emitted header before Stage B. |
| Private-evidence lifecycle | The two retained K-02 files are integrity-checkable and mode `0600`, but the untracked directory has no approved custodian, durable-copy rule, retention deadline, or disposal trigger. Interim no-move/no-delete custody applies until decision 8 defines them. |
| pytest major boundary | `9.0.3` resolves without Vyper extras but conflicts with Vyper 0.4.3 optional test/dev metadata and intentionally invalidates S1's exact `8.4.2` expectation. Upgrade, exception, paired upstream change, or blocked disposition required. |
| cbor2/wheel artifact input | Candidate A changes compiler/build transitives. Old/new bytecode, ABI, known-vector, wheel/install, and S3 artifact equality are unproved until Stage B. |
| HTTP/environment behavior | Release notes were reviewed, but redirects/retries/proxies/TLS/certificates/adapters/pooling/timeouts/exceptions, hostname handling, and dotenv load behavior require clean candidate validation. |
| Documentation and low alerts | #27 and #22 require an explicit land/separate/accept decision; lack of repository reachability is not an automatic acceptance. |
| S3 sequencing | S3 is in flight and not integrated. Stage B and any dependency-changing merge remain blocked. |
| Branch freshness | Local `rh` advanced after bootstrap. Owner-directed reconciliation is required only after reviewed S3 integration and checkpoint closure. |
| Security policy/freshness | No alert policy, exception, freshness window/trigger, or stale-evidence blocking rule has been approved. |
| Ambient environment | `pip check` is green but ambient packages do not exactly equal the lock. Only Stage B old/new disposable installs can provide clean-environment proof. |

No residual risk is accepted by this record.

## Rollback and reproduction plan

Stage A changes no dependency, so repository rollback consists only of
reverting the H-01 evidence commits, which restores this evidence path to its
absence at the starting commit. The frozen dependency rollback anchor is
`382eb7d`, direct-input hash
`2a6726cdc447cb71cc376ef14ee93cc645dbb43826893c5d2433586a89f26f63`,
and lock hash
`18df0aad224f2a10febc9e155e4a530e1000ec553916c8ef78dc9859c6c92ba0`.

To reproduce a candidate after approval:

1. reconcile this branch with the reviewed, integrated S3 commit under owner
   direction and re-freeze all inputs;
2. create separate old and candidate Python 3.12.0 environments with the
   approved pip/pip-tools commands and public-index policy;
3. seed the candidate compile with the frozen reviewed output lock, regenerate
   from the exact candidate input above, and compare a complete literal diff
   with the Stage A appendix regardless of whether the recorded hash matches;
   any hash mismatch or extra diff line blocks implementation until a fresh
   full lock-diff review explains and approves it;
4. install old and candidate locks independently, run approved audit and
   `pip check`, record complete inventories, and exclude local/editable/private
   inputs;
5. run offline package compatibility, S1/S2/S3/full-suite, ABI, bytecode, and
   artifact comparisons; and
6. re-query authoritative alerts without claiming default-branch closure
   before the relevant manifest is merged and observed.

A failed candidate is abandoned by disposing its environment and restoring
the old lock/environment from the frozen hash; no in-place upgrade/downgrade
counts as rollback evidence.

## Mandatory owner/security checkpoint — open

No answer means no dependency edit. Recommendations above are not approvals.
The owner and security reviewer must record exact decisions for all eight
items:

1. **Alert policy:** choose zero open alerts; zero open deployment-path
   high/medium alerts with separate docs/low disposition; or another explicit
   policy. State whether mandatory test/validation tooling such as pytest is
   included in “deployment path.”
2. **Non-pytest selection:** approve exact package versions and the exact
   direct-input pins/constraints, including pin-versus-bounded-constraint
   form and removal conditions. Candidate A proposes cbor2 5.9.0, idna 3.15,
   python-dotenv 1.2.2, Requests 2.33.0, urllib3 2.7.0, wheel 0.46.2, and
   explicit holds for Titanoboa 0.2.7 and pytest 8.4.2. For each, explicitly
   choose the minimal patch versus the current-latest alternative in the table
   above; a different version reopens release-note and resolver review.
3. **pytest:** choose exact 9.0.3 with S1 reapproval; exact 8.4.2 under a
   time-bounded exception; a separately approved Vyper/Titanoboa change; or
   blocked pending a compatible upstream path. Explicitly resolve the Vyper
   optional-extra `<9` metadata.
4. **Docs/low:** decide whether Pymdown Extensions 10.21.3 and Pygments 2.20.0
   land now, land separately, or remain explicitly open.
5. **Residual acceptance:** for every accepted alert, name the owner,
   rationale, compensating controls, expiration, and mandatory re-review
   trigger. Otherwise state that none are accepted.
6. **Sequence:** confirm S3 completes both gates and merges first, or supply
   the explicit owner/S3/Track 6/security approval for the more expensive
   alternate sequence.
7. **Stage B toolchain:** approve exact Python, pip, pip-tools/resolver,
   indexes, frozen-output seeding, mandatory fresh literal lock-diff review,
   old/new clean-environment, and audit commands. Approve the exact
   pip-compile invocation and the truthful header it must emit: either the
   expanded K-01 wrapper form recorded above or a separately reproduced clean
   form. Manual header normalization is not approved. K-01 does not authorize
   Stage B installation or an auditor.
8. **Freshness:** define the exact time window or event trigger; what refreshes
   it; which alert classes, lock/environment/artifact evidence it covers; and
   which rehearsal/deployment actions stale evidence blocks. Keep ordinary
   offline unit tests independent of network and wall-clock state. Also define
   the retained K-02 artifacts' named custodian, authoritative/durable storage
   location, minimum retention event or deadline, hash/permission recheck
   trigger, approved disposal event and method, and required disposal record.
   Until then, the interim no-move/no-delete rule remains in force.

Until those decisions are explicit, H-01 is **evidence incomplete / checkpoint
blocked**. Stage B, dependency/test changes, branch reconciliation, merge,
push, and live/state-changing actions are prohibited.
