# Track 7 H-01 Stage A Dependency-Security Gate

> **Path note (8 August 2026):** some paths cited below no longer exist in the
> active tree — the block-clock inventory, the `contracts/testing/` probes, and
> the extracted deploy manifests and review records were removed. The citations
> were accurate when written and are left intact. See
> [`REMOVED.md`](../../../simplification/REMOVED.md) for the full index; everything is
> recoverable from git history. No production contract was modified.

**Historical post-Candidate-A status (recorded 25 July 2026 UTC):** The
independently approved four-file H-01 Candidate A payload was
integrated and pushed on authoritative `rh` at exact merge commit
`575d47b82055b42da2bddf1535d8076cd7cf4c63`. Its parents are the reviewed
baseline `03c07f01dda03a5529c602aafbfe5545ae86df69` and final H-01 commit
`3b46be0a3af3355661b4a9f55b6a4c2295a39da7`; the integration delta is
exactly the four authorized H-01 files. The authorized post-integration
K-02/default-branch refresh at `2026-07-25T01:20:02Z` found that GitHub still
observes all 13 alerts open: 6 high, 6 medium, and 1 low, numbers
`13,14,15,16,18,19,21,22,23,24,25,26,27`. GitHub's observed alert state is
recorded exactly and controls this closeout: no alert is claimed resolved,
closed, or remediated merely because Candidate A is integrated. The static
integrated-lock range comparison remains separate evidence only. All five
bounded exceptions remain in force with their 15 August 2026 review,
`2026-08-31T23:59:59Z` hard expiry, compensating controls, invalidation
triggers, custody requirements, retention, and separately authorized disposal
obligations. This post-integration amendment changes only this evidence file
and awaits final review; no dependency, lock, test, exception, policy, or
validation conclusion changed. No Dependabot mutation, deployment, signing,
verification submission, private-evidence deletion/relocation, or other
production action is authorized or performed.

**Current transition status (updated 27 July 2026 UTC):** The exact
three-package remediation is integrated and pushed on authoritative `rh` at
commit `d62777646cba1ae448fb9e26519c6fa295f437df`, tree
`01b1d7c8fc7bdf5163e20efe1f61b53db2b01a61`. The integrated pins are Click
`8.3.3`, Pygments `2.20.0`, and Pymdown Extensions `10.21.3`; pytest `8.4.2`,
Titanoboa `0.2.7`, Vyper `0.4.3`, and every other dependency remain held. The
final corrected validation interval is recorded at the end of this evidence.
The owner-authorized three-file exception-status transition is also recorded
in the latest controlling section. Its target split becomes effective only
when the exact independently approved transition commit is integrated into
authoritative `rh`; a feature branch or uncommitted candidate does not itself
retire an exception. Package remediation, repository exception retirement,
and GitHub/Dependabot alert closure remain separate determinations.

**Evidence date:** 24 July 2026

**Stage A branch:** `rh-track-7-h1-dependency-security`

**Starting commit:** `382eb7da82bc4ed54be945311a8ccd30fae87dec`

This record began as the sanitized, evidence-only Stage A record required by
`track-7-h1-dependency-security-preflight.md`. Its historical Stage A sections
remain evidence of the state and decisions at those gates; the later dated
sections record the owner-authorized Stage B attempt, replacement
authorization, Candidate A implementation, and validation. Nothing in this
record is merge, push, deployment, signing, or other live-action approval, and
it never claims an authoritative default-branch alert is closed merely because
the unmerged candidate lock remediates its affected range.

Statements below that say H-01 was `stopped`, `pending`, `blocked`, or awaiting
the Stage B reviewer gate are preserved as contemporaneous checkpoint
evidence. They do not describe the final current state. For current status,
the top-level status above and the latest dated review/reconciliation section
at the end of this record control.

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

## Mandatory owner/security checkpoint — closed 24 July 2026

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

### Owner/security approval record

On 24 July 2026, the owner first authorized “the eight-item H-01 Stage B
authorization as recommended,” explicitly directed reconciliation with
integrated `rh` commit
`3e6e6f230169fc445d0b29454457480c62efd89a`, and directed Stage B to proceed
exactly under the brief. Because decisions 4, 7, and 8 contained choices rather
than one recommendation, the implementing agent stopped without changing the
branch and proposed a concrete bundle. After independent review and the
reviewer's hardening riders, the owner stated: “I approve both and the revised
bundle.” The owner also confirmed that they act as the Track 6 owner for this
conditional exact-profile authorization.

The closed decisions are:

1. **Alert policy:** the final target is zero open alerts in the approved
   candidate lock. Candidate Zero will be implemented incrementally—Candidate
   A first, then pytest, then the documentation/low packages—to isolate any
   failure. No partial candidate may merge or be described as H-01 closure.
   Any candidate drift, unresolved alert, compatibility failure, S3 artifact
   difference, or scope expansion stops Stage B.
2. **Exact package selection and constraint form:** use exact direct pins
   `titanoboa==0.2.7`, `pytest==9.0.3`, `requests==2.33.0`,
   `urllib3==2.7.0`, `idna==3.15`, `python-dotenv==1.2.2`,
   `cbor2==5.9.0`, `wheel==0.46.2`,
   `pymdown-extensions==10.21.3`, and `Pygments==2.20.0`; retain
   `vyper==0.4.3`, `rlp~=4.0.1`, `ipython`, and `dotenv`. These are the
   recorded Candidate Zero minimal patched versions, not later PyPI releases.
   An added transitive pin may be removed only when its direct parent's
   upstream metadata guarantees at least the patched floor and a fresh
   resolver plus security review approves the resulting complete lock diff.
3. **pytest and S1:** use exact pytest `9.0.3`. The Vyper 0.4.3 optional
   `test`/`dev` metadata conflict (`pytest<9`) is conditionally accepted only
   because those extras are not installed; resolver success is not
   compatibility proof. Run S1 unchanged first and record its intentional
   exact-version failure, update only the exact pytest expectation, and
   re-prove the complete S1/S2/S3/full-suite and artifact surface. The
   approving owner is also the Track 6 owner. Final exact-profile acceptance
   remains subject to the designated independent reviewer gate.
4. **Documentation and low severity:** land exact Pymdown Extensions `10.21.3`
   and Pygments `2.20.0` in the same final Candidate Zero profile, after the
   separable Candidate A and pytest validations.
5. **Residual acceptance:** no Stage A alert is accepted, deferred, ignored,
   or suppressed. The approved final candidate must audit without a known
   vulnerability; any residual or newly surfaced alert stops Stage B.
6. **Sequence:** S3 must merge first. The owner explicitly directed the H-01
   branch to reconcile with reviewed integration commit
   `3e6e6f230169fc445d0b29454457480c62efd89a`. No alternate sequence is
   approved.
7. **Stage B toolchain and audit:** use CPython `3.12.0` from the recorded
   K-01 seed, pip `23.2.1`, and pip-tools `7.4.1`. Do not upgrade pip in
   place. Use only `https://pypi.org/simple`, no extra/private index,
   `--no-cache-dir` for tool installation, a disposable pip-tools cache,
   frozen-output seeding, a mandatory complete fresh literal lock-diff review,
   and repeated resolution. The approved compile command and truthful emitted
   header are the expanded K-01 wrapper form recorded above; manual header
   normalization is prohibited. Build independent old and candidate clean
   environments rather than upgrading in place. In a third disposable audit
   tool environment, install exact `pip-audit==2.10.1` from public PyPI using:

   ```text
   python -m pip install --no-cache-dir \
     --index-url https://pypi.org/simple pip-audit==2.10.1
   ```

   Audit both old and candidate locks, without dependency resolution, fixing,
   ignores, or suppression:

   ```text
   PIP_CONFIG_FILE=/dev/null python -m pip_audit \
     --no-deps --disable-pip -r requirements.txt --format=json
   ```

   The audit is an approved read-only live advisory-network query. It must
   never run inside pytest; the committed dependency gate remains offline.
   Sanitized audit results may be committed in this evidence record, but raw
   output remains outside the repository.
8. **Freshness and retained evidence:** there is no wall-clock window. The
   sole staleness triggers are a change to direct inputs, the compiled lock,
   any selected version, Python/pip/pip-tools/auditor provenance, the
   integrated S3 source or artifact baseline, the authoritative alert ledger,
   or another branch reconciliation. Refresh K-02 and both candidate audit
   evidence after final lock generation and again immediately before the
   Stage B reviewer gate. Stale evidence blocks Stage B acceptance and every
   rehearsal/deployment action, but never makes ordinary offline tests depend
   on network or wall-clock state.

   The approving owner is custodian of the two retained K-02 files at
   `~/dev/ripe-protocol-h1-private-evidence/`. They remain the sole
   authoritative copies, mode `0600`; the owner explicitly accepts the
   single-copy risk. Loss is detectable through the committed hashes but the
   original bytes would not be recoverable without a new K-02 retrieval.
   Retain them through the later of Stage B reviewer acceptance and a
   post-merge authoritative default-branch alert refresh. Recheck path, hash,
   and permissions at every K-02 refresh and immediately before the reviewer
   gate. Move or delete them only under a separate owner instruction, and
   record the paths, hashes, method, and timestamp of disposal.

The owner designated the same independent reviewer agent that performed the
Stage A reviews as the mandatory Stage B security/Track 6 reviewer. That
reviewer must inspect the complete brief-defined reviewer surface after
implementation. Until that review occurs, H-01 is **Stage B authorized but not
accepted**. Merge, push, deployment, signing, verification submission, and
every other live/state-changing action remain prohibited.

## Stage B execution record — blocked 24 July 2026

Stage B stopped during pre-implementation audit. No dependency, lock, S1
expectation, dependency-gate test, contract, script, production file, or
generated artifact was changed. The only worktree change after the stop is
this sanitized evidence update. Candidate Zero is abandoned and must not be
committed, merged, or described as an alert-free candidate.

### Reconciliation and re-frozen baseline

Before any Stage B candidate action, the integration worktree was clean and
local `rh` and `origin/rh` both resolved to the owner-approved reviewed S3
integration commit
`3e6e6f230169fc445d0b29454457480c62efd89a`. That commit contains S3 reviewer
approval commit `6f42645` in its ancestry. The H-01 branch recorded approval
at `73914a5fd6588695369b1d54cae494ed163f961e`, then merged the exact approved
S3 integration commit without conflict:

```text
cc0fd9977b854756114e2c3fda2185f2a81f0ce2
parent 73914a5fd6588695369b1d54cae494ed163f961e
parent 3e6e6f230169fc445d0b29454457480c62efd89a
```

The commits introduced on `rh` touched none of H-01's owned requirements,
S1, new dependency-gate-test, or evidence paths. The re-freeze occurred at
`2026-07-24T18:16:32Z` (`2026-07-24T12:16:32-0600`, MDT) from reconciled H-01
commit `cc0fd9977b854756114e2c3fda2185f2a81f0ce2`.

| Re-frozen input | SHA-256 |
|---|---|
| `docs/chains/rh/track-7-h1-dependency-security-preflight.md` | `ac31478d185571c9b804c84a0f78de60bf40eeb3a0aec80b839b66f62befef22` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `a28db8424537d5f059a14a614265077fd4f64379f6596b6eaede9d2716d3269d` |
| `docs/chains/rh/robinhood-deployment-validation-plan.md` | `6b61a24b838d84d87d88f9d04f95521f2e351a4c75e9511a86e8ac0e13422add` |
| `requirements.in` | `2a6726cdc447cb71cc376ef14ee93cc645dbb43826893c5d2433586a89f26f63` |
| `requirements.txt` | `18df0aad224f2a10febc9e155e4a530e1000ec553916c8ef78dc9859c6c92ba0` |
| `tests/clock/test_clock_profiles.py` | `2b1bbd8c77f97e614c9db54fcb98b284d3db95a6bb47d1ee9ab020bf6d725cc4` |
| `tests/utils/clock_profiles.py` | `69f3a616a78cb3a155962edb779533f56e362a68cc922c307dc7d40cbd4b34de` |
| `docs/chains/rh/lootbox-floor-implementation-record.md` | `d577f44507954ee3d1eee3efc4e940833557287d1fdb2890c863070cfee9be7c` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |
| `scripts/abis/Lootbox.json` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` |
| `config/block-clock-inventory.json` | `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb` |
| `scripts/check_block_clock_inventory.py` | `cc86f73629589c6a2ee0c9b60e480761d88e1e033e452c1f0843c18db9e28642` |
| `tests/conf_core.py` | `2ee8fa9222c99345fbc43ecbbf1641c185688724cc36e6a910f43069e4c06f0f` |
| `tests/inventory/test_block_clock_inventory.py` | `d9007158565979f7e5027a012a0cf6efdc6be354f0a96b16b7d35c87ba58a39c` |
| `tests/core/lootbox/test_underscore_rewards.py` | `20b86c2d5466863dc2afceaa580d8ae19c5beb363fb937090aabc1eca6bf7e7b` |
| `tests/config/test_switchboard_charlie.py` | `a444c5fc64439ccb28f5634248cb9459e579336452d59fb741e1d076d7e1fd44` |

Commit `09a17747b9c6bb985993dd18967daf06955007fe` originally recorded
incorrect values and three nonexistent paths in this table. Several values
were not even 64 hexadecimal characters and therefore could not be SHA-256
outputs. That was an evidence-integrity defect, not candidate drift. The table
above replaces every row with output recomputed directly from the reconciled
commit, using each real repository path:

```text
git show cc0fd9977b854756114e2c3fda2185f2a81f0ce2:"$path" |
  shasum -a 256
```

The seven H-01 input hashes are identical to their Stage A values, as expected
because the S3 reconciliation did not change those files. The nine integrated
S3 hashes now identify the exact paths added or changed between S3's first
parent and integration commit. Every value above was also checked for the
required 64-hex-character shape; path existence was checked at `cc0fd99`.
Follow-up rereview caught that the first correction still omitted
`tests/conf_core.py`; this revision adds its directly recomputed hash, making
the integrated-S3 set complete and the full table 16 rows.

The relevant read-only reconciliation commands and results were:

```text
git status --short --branch
  clean integration worktree; clean H-01 worktree
git rev-parse rh
git rev-parse origin/rh
  both 3e6e6f230169fc445d0b29454457480c62efd89a
git merge-base --is-ancestor \
  3e6e6f230169fc445d0b29454457480c62efd89a HEAD
  exit 0 after reconciliation
git diff --name-only 382eb7d..3e6e6f2 -- \
  requirements.in requirements.txt \
  tests/clock/test_clock_profiles.py \
  tests/deployment/test_dependency_gate.py \
  docs/chains/rh/evidence/dependency-security-gate.md
  no H-01-owned overlap from integrated rh work
```

### Reconciled old-profile validation

The old profile remained Python `3.12.0`, Titanoboa `0.2.7`, Vyper `0.4.3`,
pytest `8.4.2`, and pip check-clean. The required serial baseline was repeated
after reconciliation and before candidate implementation:

| Command | Result |
|---|---|
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q tests/clock/test_clock_profiles.py` | 57 passed in 28.12 s; 67.28 s wall |
| `PYTHONPATH=. python scripts/check_block_clock_inventory.py --check` | clean; production `100/95/17`, BN `32/100`, indirect `1`, cadence candidates `455`, seconds-unit candidates `58`, timestamp `11/37`, mixed-clock functions `4`, Vyper paths `92`; non-production test `31/29/5`, cadence test `159`; 1.45 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q tests/inventory/test_block_clock_inventory.py` | 60 passed in 26.42 s; 28.38 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q tests/core/lootbox/test_underscore_rewards.py` | 59 passed in 30.74 s; 70.70 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q tests/config/test_switchboard_charlie.py` | 91 passed in 35.43 s; 75.54 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest --collect-only -q` | 2,722 collected, 142 deselected in 1.27 s; 2.64 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. pytest -q` | 2,722 passed, 142 deselected in 305.16 s; 365.29 s wall |

The placeholder value supplied only the repository's collection-time
environment guard; no explorer or other live service was called.

### Fresh K-02 and retained candidate evidence

At approximately `2026-07-24T18:27:45Z`, the byte-for-byte approved K-02
read-only query and canonical sanitization were repeated. The fresh response
remained 13 open alerts: 6 high, 6 medium, and 1 low, alert numbers
`13, 14, 15, 16, 18, 19, 21, 22, 23, 24, 25, 26, 27`. It was byte-identical
to Stage A:

| Retained fresh K-02 record | SHA-256 | Mode |
|---|---|---|
| `~/dev/ripe-protocol-h1-private-evidence/dependabot-open-2026-07-24T182745Z-raw.json` | `52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a` | `0600` |
| `~/dev/ripe-protocol-h1-private-evidence/dependabot-open-2026-07-24T182745Z-sanitized.json` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `0600` |

The original Stage A retained records also remained at their recorded paths,
hashes, and mode `0600`.

The approved resolver was rebuilt from
`/Users/wigglez/.pyenv/versions/3.12.0/bin/python3.12` with pip `23.2.1` and
pip-tools `7.4.1`, using only public PyPI, no cache for tool installation, and
a disposable compile cache. Transient command output reported the Stage A
tool inventory (`build==1.5.0`, `click==8.4.2`, `packaging==26.2`,
`pip==23.2.1`, `pip-tools==7.4.1`, `pyproject_hooks==1.2.0`,
`setuptools==83.0.0`, `wheel==0.47.0`) and a passing `pip check`, but that
inventory output was not retained outside the repository.

Commit `09a1774` also asserted that all four candidates reproduced
byte-for-byte after reconciliation and followed that assertion with seven
incorrect input/lock hashes. The disposable resolver root and generated
candidate files had already been destroyed, and the resolver tool-environment
inventory was not retained. This correction therefore withdraws the entire
post-reconciliation four-candidate reproduction claim instead of replacing it
with values that cannot now be checked against retained preimages.

The durable candidate evidence is narrower:

- Stage A records the four exact candidate inputs, input and lock hashes, and
  complete literal lock diffs; independent Stage A review mechanically
  verified those embedded diffs before the preimages were disposed.
- The retained old and Candidate Zero environment inventories below prove
  that the two installed environments differed by exactly the nine approved
  package versions.
- The retained Candidate Zero audit JSON proves that the audited candidate
  requirements specified the expected selected versions for the packages it
  assessed.
- None of those facts proves a fresh post-reconciliation resolution was
  byte-for-byte identical across all four candidates.

A resumed Stage B must create a new resolver environment after the required
owner decisions and branch reconciliation, retain its complete tool inventory
at mode `0600`, retain or otherwise hash-anchor mechanically generated
candidate preimages before disposal, and record command-generated values
without manual transcription. Fresh resolution, complete literal diff review,
and candidate-drift determination remain unperformed for the next baseline.

Independent old and Candidate Zero environments used CPython `3.12.0` and
pip `23.2.1`; neither was upgraded in place. Both locks installed from public
PyPI with `--no-cache-dir`, and `python -m pip check` passed. Their complete
inventories differed only in these nine approved lock changes:

```text
cbor2                 5.7.0   -> 5.9.0
idna                  3.10    -> 3.15
Pygments              2.19.2  -> 2.20.0
pymdown-extensions    10.16.1 -> 10.21.3
pytest                8.4.2   -> 9.0.3
python-dotenv         1.2.1   -> 1.2.2
requests              2.32.5  -> 2.33.0
urllib3               2.5.0   -> 2.7.0
wheel                 0.45.1  -> 0.46.2
```

The complete retained inventories are:

| File | SHA-256 | Mode |
|---|---|---|
| `~/dev/ripe-protocol-h1-private-evidence/old-environment-inventory-2026-07-24T182745Z.txt` | `10a17ea189dfdf2ccd0e70eed88e1f9b274e080e6fce7c8dac2d214844180eeb` | `0600` |
| `~/dev/ripe-protocol-h1-private-evidence/candidate-zero-environment-inventory-2026-07-24T182745Z.txt` | `e9ec0c1bcc7954a5dbce5c98d8111935b3f32236960468db959aa447e1d37ca1` | `0600` |

### Approved auditor and blocking result

A third independent CPython `3.12.0` / pip `23.2.1` environment installed
exact `pip-audit==2.10.1` from public PyPI with `--no-cache-dir`. Its complete
inventory SHA-256 was
`e1284aaefc7051673541ec1bb24b6a215169a78865375896314ba48b17c02d8e`;
`python -m pip check` passed. The inventory is retained at
`~/dev/ripe-protocol-h1-private-evidence/audit-tool-environment-inventory-2026-07-24T182745Z.txt`
with mode `0600`.

The first sandboxed audit attempt stopped before any query because pip-audit
could not create its standard macOS cache under
`~/Library/Caches/pip-audit` (`PermissionError: [Errno 1] Operation not
permitted`). The exact approved command was then rerun with permission to use
that standard cache and its advisory network service; no flag, dependency,
lock, or audit policy changed:

```text
PIP_CONFIG_FILE=/dev/null \
  /private/tmp/ripe-h01-stageb-clean-20260724T182745Z/audit/bin/python \
  -m pip_audit --no-deps --disable-pip \
  -r requirements.txt --format=json \
  --output /private/tmp/ripe-h01-stageb-clean-20260724T182745Z/old-audit.json

PIP_CONFIG_FILE=/dev/null \
  /private/tmp/ripe-h01-stageb-clean-20260724T182745Z/audit/bin/python \
  -m pip_audit --no-deps --disable-pip \
  -r /private/tmp/ripe-h01-stageb-resolver-20260724T182745Z/candidate-zero/requirements.txt \
  --format=json \
  --output /private/tmp/ripe-h01-stageb-clean-20260724T182745Z/candidate-audit.json
```

At `2026-07-24T18:33:46Z`, the old lock returned exit `1` and “Found 20
known vulnerabilities in 11 packages.” The JSON contains 20 vulnerability
entries representing 18 unique audit IDs because the service returned
duplicate `PYSEC-2025-90` and `PYSEC-2026-215` entries. At
`2026-07-24T18:33:54Z`, Candidate Zero returned exit `1` and “Found 4 known
vulnerabilities in 3 packages.”

The old-lock unique IDs were
`CVE-2026-24049`, `CVE-2026-61632`, `PYSEC-2023-142`,
`PYSEC-2025-238`, `PYSEC-2025-33`, `PYSEC-2025-90`,
`PYSEC-2026-141`, `PYSEC-2026-1845`, `PYSEC-2026-1994`,
`PYSEC-2026-1996`, `PYSEC-2026-1998`, `PYSEC-2026-2123`,
`PYSEC-2026-2132`, `PYSEC-2026-215`, `PYSEC-2026-2270`,
`PYSEC-2026-2275`, `PYSEC-2026-2987`, and `PYSEC-2026-2999`.

Candidate Zero remediates all 13 alerts in the authoritative Stage A GitHub
ledger but fails the broader approved auditor:

| Package/version | Audit ID | Aliases | Auditor fix versions | Disposition |
|---|---|---|---|---|
| `click==8.2.1` | `PYSEC-2026-2132` | `GHSA-47fr-3ffg-hgmw`, `CVE-2026-7246` | `8.3.3` | unresolved; not in approved candidate |
| `pymdown-extensions==10.21.3` | `CVE-2026-61632` | `GHSA-9xwg-3r6f-jcx2` | `11.0.0` | unresolved; approved version is still vulnerable |
| `vyper==0.4.3` | `PYSEC-2023-142` | `GHSA-5824-cm3x-3c38`, `CVE-2023-39363` | none reported | unresolved; approved held package |
| `vyper==0.4.3` | `PYSEC-2025-33` | `GHSA-vgf2-gvx8-xwc3`, `CVE-2025-21607` | none reported | unresolved; approved held package |

These are newly surfaced relative to the Stage A GitHub alert ledger, not a
claim that the advisories themselves are newly published. No ignore,
suppression, exception, or residual acceptance was applied.

Raw audit JSON remains outside the repository:

| Retained raw audit | SHA-256 | Mode |
|---|---|---|
| `~/dev/ripe-protocol-h1-private-evidence/pip-audit-old-2026-07-24T182745Z-raw.json` | `5bb47d3f69669aae51bf3007532ba156de40c1da0d5e3c50e005eebd75c3f8d2` | `0600` |
| `~/dev/ripe-protocol-h1-private-evidence/pip-audit-candidate-zero-2026-07-24T182745Z-raw.json` | `9ae967aadec370959f356929ed229928c48caffcd4b656c3f81ceaa1f80a7db9` | `0600` |

### Stop boundary and decisions required

Owner decision 5 required an audit with no known vulnerability and stated
that any residual or newly surfaced alert stops Stage B. The user separately
directed a stop on any unresolved alert. Both conditions fired. Accordingly:

- no candidate was copied into the worktree;
- the unchanged S1 intentional-failure step did not begin;
- no S1 expectation or dependency-gate test was edited;
- candidate compatibility, artifact, and full-suite validation did not begin;
- B6 final re-query and the mandatory Stage B reviewer gate were not reached;
- no merge, push, deployment, signing, verification submission, or other
  live/state-changing action occurred; and
- H-01 is **blocked during Stage B**, not complete and not reviewer-ready.

At `2026-07-24T18:36:40Z`, the abandoned resolver, old-profile,
Candidate Zero, and auditor environments were removed by deleting only
`/private/tmp/ripe-h01-stageb-resolver-20260724T182745Z` and
`/private/tmp/ripe-h01-stageb-clean-20260724T182745Z`; both paths were
confirmed absent. The task-created standard pip-audit cache
`~/Library/Caches/pip-audit` (creation time
`2026-07-24T12:33:42-0600`) was also removed and confirmed absent. The
worktree's old direct input and lock were never changed and remain reproducible
at the re-frozen hashes above. The retained mode-`0600` evidence files were
not moved or deleted.

During independent blocker rereview, local `rh` had advanced from the
approved reconciliation target to
`27765d29094256fa9619dd44a0bfd145863de8b7`
(`docs: record owner-approved Track 6 S5 plan`), while `origin/rh` remained
`3e6e6f230169fc445d0b29454457480c62efd89a`. The only local-`rh` delta was
new documentation file `docs/chains/rh/track-6-s5-ledger-guard.md`; the prior
S3 integration remains its ancestor. This blocked H-01 branch was not
reconciled again because the prior authorization named exact commit `3e6e6f2`
and any later reconciliation requires fresh owner direction. Under decision
8, the local baseline movement is independently sufficient to require a new
freeze and fresh security evidence before any resumption.

Independent blocker rereview also supplied the following decision guidance.
It is recorded as reviewer analysis, not owner/security approval:

- Retain a zero-vulnerability policy for applicable findings, with an explicit
  applicability determination for every auditor result rather than treating
  an advisory-database metadata defect as an automatically applicable
  vulnerability. Each determination must cite the primary reviewed
  advisory's affected range and carry its own explicit re-review trigger.
- Trial `click==8.3.3` in a refreshed candidate. The current lock records the
  dependency path `titanoboa -> mkdocs-material -> mkdocs -> click`; OSV/PyPA
  advisory
  [`PYSEC-2026-2132`](https://osv.dev/vulnerability/PYSEC-2026-2132)
  reports every Click version before `8.3.3` as affected.
- Do not select Pymdown Extensions `10.21.3` again. GitHub's reviewed
  [`CVE-2026-61632`](https://github.com/advisories/GHSA-9xwg-3r6f-jcx2)
  record reports `<=10.21.3` affected and `11.0.0` as the first patched
  version. A refreshed candidate must either trial `11.0.0` as an explicitly
  reviewed major crossing or retain `10.16.1` with an explicit open
  disposition. Review primary Click `8.3.x` and Pymdown Extensions `11.x`
  release notes and breaking changes before selection; do not infer
  compatibility merely from their documentation-tooling reachability.
  Preserve the approved incremental Candidate A, then pytest, then
  documentation/low sequence so each failure remains isolated.
- Treat the two Vyper findings as applicability candidates, not silently as
  accepted risk or as an automatic Vyper-upgrade instruction. GitHub's
  reviewed records limit
  [`CVE-2023-39363`](https://github.com/advisories/GHSA-5824-cm3x-3c38)
  to `>=0.2.15,<0.3.1` with `0.3.1` patched, and
  [`CVE-2025-21607`](https://github.com/advisories/GHSA-vgf2-gvx8-xwc3)
  to `<0.4.1`. Both ranges exclude the held `vyper==0.4.3`. If the
  owner/security reviewer adopts that determination, the refreshed audit
  command must explicitly authorize and record the exact two ignore flags
  because the current command forbids ignores:

  ```text
  --ignore-vuln PYSEC-2023-142
  --ignore-vuln PYSEC-2025-33
  ```

  Recheck the primary affected ranges and OSV/PyPA metadata at every K-02 and
  candidate-audit refresh, and remove either ignore flag immediately when the
  metadata no longer incorrectly flags `0.4.3`. The reviewer recommends
  filing an upstream PyPA advisory-database report, but that external write
  needs separate owner authorization. No ignore flag was used and no upstream
  report was submitted in this blocked run.
- Refresh the complete eight-item authorization bundle only after these
  choices and the new `rh` reconciliation decision are explicit. Resolve and
  record the exact current `rh` commit at approval time; `27765d2` is only the
  latest observation, not a pre-approved future reconciliation target. Carry
  retained resolver inventory, retained-or-hash-anchored candidate preimages,
  and command-generated numeric transcription into the refreshed bundle as
  binding evidence conditions.

Fresh owner/security decisions are required before any resumption:

1. whether to adopt the reviewer's recommended zero-applicable-vulnerability
   policy and per-finding applicability rule, including a primary affected
   range citation and explicit re-review trigger for each determination, or to
   define another precise residual policy;
2. whether scope may expand to trial and review exact `click==8.3.3` and
   either exact `pymdown-extensions==11.0.0` or an explicit hold at the current
   `10.16.1`, including primary release-note and breaking-change review, the
   unchanged Candidate A -> pytest -> documentation/low sequence, a fresh
   complete resolver diff, clean environments, compatibility tests, and a new
   candidate approval;
3. whether to approve the primary-range determination that both Vyper
   findings do not apply to `vyper==0.4.3`, and if so, the exact two audit
   ignore flags, recheck-and-remove trigger at every K-02/audit refresh, and
   whether to separately authorize filing an upstream metadata report;
   otherwise, whether to exception-gate them or authorize a separately
   reviewed Vyper profile change and its Track 6/S1/S3/artifact consequences;
   and
4. whether, after resolving the exact current local `rh` commit at approval
   time, to reconcile H-01 to that commit, re-freeze every baseline, retain
   resolver inventory and candidate preimages under the new hygiene rules,
   refresh the complete eight-item authorization bundle, and only then resume
   Stage B.

### Evidence-integrity correction verification

The correction parsed every row in the re-frozen table, read the file directly
from `cc0fd99`, recomputed its hash, compared it to the recorded value, and
checked the 64-hex-character shape:

```text
sed -n '/^| Re-frozen input | SHA-256 |$/,/^$/p' \
  docs/chains/rh/evidence/dependency-security-gate.md |
  rg '^\| `' |
  while IFS='|' read -r _ file_path_field hash_field _; do
    # trim Markdown delimiters into file_path and recorded
    actual=$(git show cc0fd99:"$file_path" | shasum -a 256 |
      awk '{print $1}')
    test "$recorded" = "$actual"
    printf '%s' "$recorded" | rg -q '^[0-9a-f]{64}$'
  done
```

Result: all 16 rows passed. A first read-only draft of this verification loop
used zsh's special `path` variable, which cleared the executable search path
after the first row and produced `command not found` for subsequent commands.
It made no file or Git change. Renaming the variable to `file_path` produced
the all-green result above. The final nine table paths, sorted and compared
against `git diff --name-only 127b4bf..3e6e6f2`, matched exactly, including
`tests/conf_core.py`.

An independent shape scan of every 50–70-character lowercase hexadecimal
value in this Stage B record produced no non-64-character result. Searches for
the three former nonexistent paths, the stale resolver-build value, all
withdrawn post-reconciliation candidate-hash fragments, and the former
reproduction sentence returned no match. `git diff --check` passed, and
`git diff --name-only` listed only this evidence file. All seven retained
K-02, audit, and environment files were rehashed and rechecked at mode `0600`;
they still match the tables above. No dependency or runtime test was repeated:
this correction changes only evidence text, and it deliberately withdraws an
unsupported resolver claim rather than making a new runtime claim.

Approval of the previous Candidate Zero bundle does not answer these new
questions. Until they are explicit, dependency/test implementation and the
Stage B reviewer gate remain blocked.

## Refreshed minimum-candidate authorization packet — pending

**Packet date:** 24 July 2026

**Packet status:** proposed for owner/security approval; not dependency-change
authorization

### Authority and supersession

The owner directed H-01 to continue because dependency, deployment-tooling,
and test-environment changes do not change production smart-contract behavior.
That direction authorized reconciliation and preparation of this packet only.
It explicitly did not authorize a requirement, lock, dependency, test, or
tooling change.

If and only if the owner and designated independent security/Track 6 reviewer
approve this complete packet, it **supersedes in full** the previous
eight-item H-01 Stage B owner authorization dated 24 July 2026, recorded under
“Mandatory owner/security checkpoint — closed 24 July 2026” in commit
`73914a5fd6588695369b1d54cae494ed163f961e`. The former Candidate Zero
authorization will then be historical and non-operative. The two policies
must never be combined, selectively inherited, or treated as simultaneously
live.

Until that approval is explicit, the prior authorization remains stopped by
the recorded audit blocker and this replacement packet grants no
implementation authority.

### Reconciled reviewed baseline and fresh freeze

At the reconciliation check, committed local `rh` resolved to reviewed
commit `27765d29094256fa9619dd44a0bfd145863de8b7`; `origin/rh` remained
`3e6e6f230169fc445d0b29454457480c62efd89a`. The committed delta was solely
new Track 6 S5 brief
`docs/chains/rh/track-6-s5-ledger-guard.md`. It touched no H-01-owned
requirement, lock, S1 expectation, dependency-gate-test, or evidence path.

The main `rh` worktree contained unrelated uncommitted documentation changes.
They were preserved and excluded because they are not a reviewed commit.
H-01 merged only exact commit `27765d2`, producing:

```text
a2b6f225b46f6b95271e86cf102e31b6285476a4
parent 22eb097e86a123c01a7117d5166b87ed11ae30c9
parent 27765d29094256fa9619dd44a0bfd145863de8b7
```

The fresh freeze was captured at `2026-07-24T20:14:05Z`
(`2026-07-24T14:14:05-0600`, MDT) directly from merge commit `a2b6f225`.

| Refrozen path | SHA-256 |
|---|---|
| `docs/chains/rh/track-7-h1-dependency-security-preflight.md` | `ac31478d185571c9b804c84a0f78de60bf40eeb3a0aec80b839b66f62befef22` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `a28db8424537d5f059a14a614265077fd4f64379f6596b6eaede9d2716d3269d` |
| `docs/chains/rh/robinhood-deployment-validation-plan.md` | `6b61a24b838d84d87d88f9d04f95521f2e351a4c75e9511a86e8ac0e13422add` |
| `docs/chains/rh/track-6-s5-ledger-guard.md` | `37332bb560ba5591da10b08f1e2e8aca28d4d21142c6a61ef8ac210566b564e1` |
| `requirements.in` | `2a6726cdc447cb71cc376ef14ee93cc645dbb43826893c5d2433586a89f26f63` |
| `requirements.txt` | `18df0aad224f2a10febc9e155e4a530e1000ec553916c8ef78dc9859c6c92ba0` |
| `tests/clock/test_clock_profiles.py` | `2b1bbd8c77f97e614c9db54fcb98b284d3db95a6bb47d1ee9ab020bf6d725cc4` |
| `tests/utils/clock_profiles.py` | `69f3a616a78cb3a155962edb779533f56e362a68cc922c307dc7d40cbd4b34de` |
| `docs/chains/rh/lootbox-floor-implementation-record.md` | `d577f44507954ee3d1eee3efc4e940833557287d1fdb2890c863070cfee9be7c` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |
| `scripts/abis/Lootbox.json` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` |
| `config/block-clock-inventory.json` | `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb` |
| `scripts/check_block_clock_inventory.py` | `cc86f73629589c6a2ee0c9b60e480761d88e1e033e452c1f0843c18db9e28642` |
| `tests/conf_core.py` | `2ee8fa9222c99345fbc43ecbbf1641c185688724cc36e6a910f43069e4c06f0f` |
| `tests/inventory/test_block_clock_inventory.py` | `d9007158565979f7e5027a012a0cf6efdc6be354f0a96b16b7d35c87ba58a39c` |
| `tests/core/lootbox/test_underscore_rewards.py` | `20b86c2d5466863dc2afceaa580d8ae19c5beb363fb937090aabc1eca6bf7e7b` |
| `tests/config/test_switchboard_charlie.py` | `a444c5fc64439ccb28f5634248cb9459e579336452d59fb741e1d076d7e1fd44` |

The existing old-profile validation remains applicable because the sole
integrated delta is a new documentation brief and no dependency, runtime,
test, source, artifact, or validation configuration changed. No test was
rerun for packet preparation. Any later committed `rh` movement, any
H-01-owned-file movement, or any integration of the currently uncommitted
documentation work invalidates this freeze and requires another explicit
reconciliation decision.

### Fresh authoritative alert observation

The exact approved K-02 read-only query was repeated at
`2026-07-24T20:13:11Z` with GitHub CLI `2.96.0`. Before the query, a
precheck invoked `gh auth status`. That command displayed authentication-state
metadata and a fully masked token representation in the local command
transcript. It exposed no literal credential value, and no authentication
output was written to a file or the repository, but invoking it was contrary
to K-02's stricter “never print authentication state” output-minimization
rule. This is a recorded process deviation, not an assertion of compliance or
an expansion of K-02. It performed no mutation. Future K-02 refreshes must not
invoke `gh auth status`; they must use the approved API call's success or
failure without printing separate authentication state. The query itself
remained:

```text
gh api --method GET --paginate --slurp \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  '/repos/Ripe-Foundation/ripe-protocol/dependabot/alerts?state=open&per_page=100'
```

The response is byte-identical to both earlier retained snapshots: 13 open
alerts, 6 high, 6 medium, and 1 low, alert numbers
`13, 14, 15, 16, 18, 19, 21, 22, 23, 24, 25, 26, 27`. The new Pymdown
Extensions `CVE-2026-61632` finding is in GitHub's reviewed advisory database
but is not a separate default-branch Dependabot alert in this response.

| Fresh retained K-02 file | SHA-256 | Mode |
|---|---|---|
| `~/dev/ripe-protocol-h1-private-evidence/dependabot-open-2026-07-24T201311Z-raw.json` | `52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a` | `0600` |
| `~/dev/ripe-protocol-h1-private-evidence/dependabot-open-2026-07-24T201311Z-sanitized.json` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `0600` |

Default-branch alert state still cannot prove an unmerged candidate. Candidate
remediation and authoritative closure remain separate facts.

### Recommended minimum candidate

The recommendation is the historical Candidate A selection, refreshed from a
new resolver only after packet approval. It changes exactly six
deployment-path packages and keeps every other package version fixed:

```text
titanoboa==0.2.7
vyper==0.4.3
rlp~=4.0.1
ipython
dotenv
pytest==8.4.2
requests==2.33.0
urllib3==2.7.0
idna==3.15
python-dotenv==1.2.2
cbor2==5.9.0
wheel==0.46.2
```

| Package | Current | Proposed | Deployment-path purpose |
|---|---:|---:|---|
| `cbor2` | `5.7.0` | `5.9.0` | Resolve both compiler-transitive CBOR alerts; re-prove deterministic compiler artifacts. |
| `idna` | `3.10` | `3.15` | Resolve oversized-Unicode hostname processing in the Requests path. |
| `python-dotenv` | `1.2.1` | `1.2.2` | Resolve the dotenv write-helper alert while retaining tested load/interpolation behavior. |
| `requests` | `2.32.5` | `2.33.0` | Resolve the Requests alert at the minimum patch in deployment HTTP tooling. |
| `urllib3` | `2.5.0` | `2.7.0` | Resolve all four HTTP response/redirect/proxy alert ranges. |
| `wheel` | `0.45.1` | `0.46.2` | Resolve build/install extraction risk at the minimum patch. |

The historical Candidate A input/lock hashes and embedded literal diff remain
Stage A evidence only. Post-reconciliation byte-for-byte reproduction was
withdrawn and is not reasserted. Approval would authorize a new clean
resolution, not reuse of those hashes. The new run must retain the complete
resolver inventory and retain or hash-anchor every candidate preimage before
disposal.

The selected candidate is expected to remove 10 of the 13 current Dependabot
vulnerable ranges from the candidate lock while leaving #22 Pygments, #23
pytest, and #27 Pymdown Extensions visible and explicitly dispositioned.
GitHub will still report all default-branch alerts until it observes a merged
manifest.

### Finding-by-finding applicability and residual ledger

The retained Candidate Zero audit produced four findings. Candidate A keeps
Click and Vyper at the same versions and returns Pymdown Extensions from
Candidate Zero's `10.21.3` to the unchanged baseline `10.16.1`; both Pymdown
versions remain within the new b64 finding's affected range. Every finding
therefore needs an individual disposition:

| Current audit finding | Affected range and source | Repository reachability | Proposed disposition |
|---|---|---|---|
| [`PYSEC-2026-2132`](https://raw.githubusercontent.com/pypa/advisory-database/main/vulns/click/PYSEC-2026-2132.yaml); Click `8.2.1`; command injection in `click.edit()` | PyPA records `<8.3.3`; upstream Click `8.3.3` [removes `shell=True` from editor/pager launch](https://github.com/pallets/click/releases/tag/8.3.3). | `scripts/migrate.py`, `scripts/verify.py`, and `scripts/console.py` directly use Click commands, options, choices, and prompts. No repository call to `click.edit()` exists. | Version is affected, but the vulnerable function is absent from the current deployment-tooling path. Proposed bounded exception `EX-H01-CLICK-01`; do not mislabel it documentation-only. |
| [`CVE-2026-61632`](https://github.com/advisories/GHSA-9xwg-3r6f-jcx2); Pymdown Extensions; `pymdownx.b64` path traversal | GitHub-reviewed `<=10.21.3`; first patch `11.0.0`. | No repository MkDocs config, Pymdown import, `pymdownx.b64`, or documentation build exists. No untrusted Markdown is rendered. | Applicable version but unreachable extension. Proposed bounded exception `EX-H01-PYMDOWN-B64-01`. Candidate Zero's `10.21.3` remains vulnerable and must not be selected. |
| [`PYSEC-2023-142`](https://github.com/advisories/GHSA-5824-cm3x-3c38); Vyper named reentrancy-lock allocation | Authoritative GitHub-reviewed `>=0.2.15,<0.3.1`; first patch `0.3.1`. | Exact compiler hold is `vyper==0.4.3`, outside the authoritative affected range. | Not applicable to `0.4.3`. [PyPA scanner metadata](https://raw.githubusercontent.com/pypa/advisory-database/main/vulns/vyper/PYSEC-2023-142.yaml) incorrectly records `introduced: 0` without a fixed boundary. Scanner-metadata defect, not accepted security risk. No ignore flag proposed. |
| [`PYSEC-2025-33`](https://github.com/advisories/GHSA-vgf2-gvx8-xwc3); Vyper precompile-call success checks | Authoritative GitHub-reviewed `<0.4.1`; `0.4.3` is outside the range. | Exact compiler hold is `vyper==0.4.3`; the authoritative range and [current PyPA metadata](https://raw.githubusercontent.com/pypa/advisory-database/main/vulns/vyper/PYSEC-2025-33.yaml) `fixed: 0.4.1` both exclude it. | Not applicable to `0.4.3`. The earlier pip-audit PyPI service result was stale/inconsistent scanner metadata. No ignore flag proposed. |

Candidate A also retains three previously visible alert packages and restores
three findings that Candidate Zero had removed. The complete expected
residual set, to be confirmed by a fresh no-ignore audit after approval, is:

| Residual finding | Candidate A version | Proposed disposition |
|---|---:|---|
| [`PYSEC-2026-2132`](https://raw.githubusercontent.com/pypa/advisory-database/main/vulns/click/PYSEC-2026-2132.yaml) / `GHSA-47fr-3ffg-hgmw` Click command injection | `8.2.1` | `EX-H01-CLICK-01` |
| [`PYSEC-2026-1845`](https://github.com/advisories/GHSA-6w46-j5rx-g56g) pytest tmpdir handling | `8.4.2` | `EX-H01-PYTEST-01` |
| [`PYSEC-2026-2987`](https://github.com/advisories/GHSA-5239-wwwm-4pmq) Pygments Archetype lexer ReDoS | `2.19.2` | `EX-H01-PYGMENTS-01` |
| [`PYSEC-2026-2999`](https://github.com/advisories/GHSA-62q4-447f-wv8h) Pymdown snippets traversal | `10.16.1` | `EX-H01-PYMDOWN-SNIPPETS-01` |
| [`CVE-2026-61632`](https://github.com/advisories/GHSA-9xwg-3r6f-jcx2) Pymdown b64 traversal | `10.16.1` | `EX-H01-PYMDOWN-B64-01` |
| [`PYSEC-2023-142`](https://github.com/advisories/GHSA-5824-cm3x-3c38) | `vyper==0.4.3` | not applicable; authoritative range exclusion |
| [`PYSEC-2025-33`](https://github.com/advisories/GHSA-vgf2-gvx8-xwc3) | `vyper==0.4.3` | not applicable; authoritative range exclusion |

This is a prediction from the retained old/Candidate Zero audits and unchanged
versions, not a fresh Candidate A audit result. Any additional finding, range
change, or disappearance must be reconciled rather than normalized.

### Proposed bounded exceptions

All exceptions are pending. The proposed exception owner is **Mick Hagen,
acting H-01 and Track 6 owner**. Each exception has a scheduled security review
on **15 August 2026** and hard expiry at **2026-08-31T23:59:59Z**. The earlier
of hard expiry or a finding-specific invalidation trigger ends authorization.
An expired exception blocks deployment rehearsal and merge; it never converts
into permanent acceptance.

#### `EX-H01-PYTEST-01` — retain pytest `8.4.2`

- **Threat model:** pytest before `9.0.3` uses predictable
  `/tmp/pytest-of-{user}` directories on Unix. Another local user can cause
  denial of service and may be able to gain privileges. The exposure exists
  while pytest runs; pytest is not part of deployed contract runtime.
- **Scope:** exact pytest `8.4.2` under CPython `3.12.0` for H-01/S1/S2/S3 and
  full-suite validation on owner-controlled local or ephemeral single-tenant
  runners. No untrusted test, plugin, or pull-request code may run.
- **Reason to accept temporarily:** pytest `8.4.2` is the exact S1-reviewed
  runtime and matches Vyper `0.4.3`'s optional test/dev metadata. Moving to
  pytest 9 crosses a major boundary, invalidates S1's fail-closed version gate,
  and expands collection/plugin/fixture/warning/teardown proof without being
  necessary to remediate the six deployment-path packages.
- **Compensating controls:** create a fresh task-specific mode-`0700`
  temporary directory for every pytest invocation; pass a dedicated explicit
  child via `--basetemp`; delete only that task directory after the command;
  run only trusted repository tests/plugins; prohibit shared multi-user
  runners; preserve exact S1 assertions and run the entire required serial
  suite without skip, xfail, or warning suppression.
- **Re-review/invalidation triggers:** shared or multi-user runner use;
  untrusted tests/plugins; inability to provide a private basetemp; pytest,
  Vyper, Titanoboa, Python, plugin, or S1-profile change; advisory range or
  exploit update; demonstrated pytest 9 compatibility; every K-02/audit
  refresh; scheduled review or hard expiry.

#### `EX-H01-CLICK-01` — retain Click `8.2.1`

- **Threat model:** versions through `8.3.2` have command injection in
  `click.edit()`, allowing an unprivileged local attacker to influence editor
  command execution.
- **Scope:** exact Click `8.2.1` only for the current direct repository CLI
  uses in `scripts/migrate.py`, `scripts/verify.py`, and `scripts/console.py`.
  Those uses are limited to commands, options, choices, and prompts.
- **Compensating controls:** no `click.edit()` or equivalent editor launch;
  no untrusted Click plugins; no untrusted `EDITOR`/`VISUAL` command source;
  dependency gate asserts the absence of `click.edit` in repository code; only
  owner-controlled deployment hosts may run these scripts.
- **Re-review/invalidation triggers:** any editor helper or plugin use; any
  new Click import/call surface; untrusted environment-variable control;
  advisory or exploit change; selected package change; every K-02/audit
  refresh; scheduled review or hard expiry.

#### `EX-H01-PYGMENTS-01` — retain Pygments `2.19.2`

- **Threat model:** crafted local content passed to the Archetype `AdlLexer`
  can cause catastrophic regular-expression backtracking and local denial of
  service.
- **Scope:** exact Pygments `2.19.2` as transitive console, test, and
  documentation tooling. No direct repository import or Archetype lexer
  selection exists.
- **Compensating controls:** prohibit `AdlLexer`/Archetype selection and
  untrusted content highlighting; no repository documentation build; gate
  scans for new direct imports/lexer selection; owner-controlled tooling only.
- **Re-review/invalidation triggers:** any docs build, new Pygments import,
  Archetype lexer use, untrusted highlighted content, advisory/exploit change,
  every K-02/audit refresh, scheduled review, or hard expiry.

#### `EX-H01-PYMDOWN-SNIPPETS-01` — retain Pymdown Extensions `10.16.1`

- **Threat model:** `pymdownx.snippets` with `restrict_base_path=True` can
  read sibling-prefix paths outside `base_path`; untrusted Markdown in a docs
  build could exfiltrate readable files or CI secrets into rendered output.
- **Scope:** exact transitive Pymdown Extensions `10.16.1`. The repository has
  no MkDocs configuration, Pymdown import, snippets extension, or docs build.
- **Compensating controls:** do not enable `pymdownx.snippets`; do not process
  untrusted Markdown; do not run a docs build with repository or CI secrets;
  gate scans for config/import/extension activation.
- **Re-review/invalidation triggers:** any Markdown/docs pipeline, Pymdown
  config/import, snippets activation, untrusted Markdown, advisory change,
  every K-02/audit refresh, scheduled review, or hard expiry.

#### `EX-H01-PYMDOWN-B64-01` — retain Pymdown Extensions `10.16.1`

- **Threat model:** `pymdownx.b64` accepts relative traversal or absolute image
  paths and embeds readable image-extension files outside `base_path` into
  output.
- **Scope:** exact transitive Pymdown Extensions `10.16.1`; no repository b64
  extension, docs configuration, or Markdown-rendering path exists.
- **Compensating controls:** do not enable `pymdownx.b64`; do not render
  untrusted Markdown; gate scans for extension/config/import activation; no
  docs build may run with readable secrets.
- **Re-review/invalidation triggers:** any b64 extension or docs-build use,
  untrusted Markdown, new Pymdown import/config, advisory change, every
  K-02/audit refresh, scheduled review, or hard expiry.

The two Vyper determinations are not exceptions: the selected compiler version
is outside both primary affected ranges. This packet proposes **no
`--ignore-vuln` flags**. The canonical audit remains a raw, no-ignore result;
the evidence ledger performs the finding-specific applicability and exception
reconciliation. If the owner later wants machine-level ignores, each exact ID
requires a separate approval naming its authoritative range, scanner defect,
owner, and removal trigger.

### Candidate A versus previously approved Candidate Zero

| Surface | Refreshed Candidate A | Previous Candidate Zero | Avoided or accepted consequence |
|---|---|---|---|
| Lock version changes | Six: cbor2, idna, python-dotenv, Requests, urllib3, wheel | Nine: the same six plus pytest, Pygments, Pymdown Extensions | Avoid three unrelated runtime/docs changes. |
| pytest/S1 | Keep pytest `8.4.2`; S1 exact profile remains unchanged | Move to pytest `9.0.3`; intentionally fail and edit S1 exact expectation | Avoid pytest major-version compatibility work and an S1 profile change; accept bounded local-runner risk under `EX-H01-PYTEST-01`. |
| Documentation/low packages | Keep Pygments `2.19.2` and Pymdown `10.16.1` | Pygments `2.20.0`, Pymdown `10.21.3` | Avoid lexer/Markdown churn. Pymdown `10.21.3` is now known vulnerable to `CVE-2026-61632`, so its former “zero” benefit is invalid. Accept two Pymdown and one Pygments bounded exceptions. |
| Click | Keep `8.2.1`; no Candidate Zero change | Keep `8.2.1` | Same finding in both; bounded function-specific exception because deployment scripts do not use `click.edit()`. |
| Vyper | Keep exact `0.4.3` | Keep exact `0.4.3` | Same scanner results; primary ranges exclude `0.4.3`, so no compiler change or security exception is warranted. |
| Candidate alert outcome | Candidate lock is expected to remediate 10/13 current Dependabot ranges; three remain visibly excepted | Predicted remediation of 13/13 old Dependabot ranges, but broad audit still found four and new Pymdown advisory defeats the count | Prefer deployment-path risk reduction over a cosmetically perfect count. |
| Required changed-package validation | HTTP, hostname, dotenv load, cbor2 vectors, wheel/install, S1/S2/S3/full suite, ABI and bytecode equality | Same plus pytest 9 behavior/S1 reapproval and docs/lexer behavior | Avoid pytest/docs change-specific proof; do not avoid the full serial suite or compiler/artifact proof. |

Candidate A still changes cbor2 and wheel, so all old/new compiler, ABI,
creation/runtime bytecode, S1/S2/S3, and full-suite evidence remains
mandatory. Minimum churn reduces proof surface; it does not lower artifact or
test standards.

### Proposed Stage B toolchain, audit, and evidence controls

If approved, retain the previously reviewed CPython `3.12.0`, pip `23.2.1`,
pip-tools `7.4.1`, public PyPI-only, no-private-index, no-cache installation,
frozen-output seeding, and truthful expanded pip-compile-header policy. Do not
upgrade an environment in place. Create independent old, candidate, resolver,
and `pip-audit==2.10.1` environments.

The resolver inventory must be retained at mode `0600`. Candidate inputs,
generated locks, literal diffs, and hashes must be generated mechanically;
candidate preimages must be retained or hash-anchored before disposal. Manual
numeric/hash transcription and manual lock-header normalization are
prohibited. Any fresh resolver delta outside the six selected package versions
plus expected direct-input annotations/header changes stops Stage B.

Run the canonical audit against both old and candidate locks with no fix,
ignore, suppression, or dependency resolution:

```text
PIP_CONFIG_FILE=/dev/null python -m pip_audit \
  --no-deps --disable-pip -r requirements.txt --format=json
```

The audit is expected to exit nonzero for approved exceptions and scanner
artifacts. Acceptance is based on exact JSON reconciliation against the
approved finding ledger, not exit code or aggregate count. Every unexpected
finding, changed range/version, expired exception, or lost compensating
control is a stop. The raw no-ignore output must be retained outside the
repository; ordinary pytest remains offline.

Run the existing S1 test unchanged. pytest and Titanoboa expectations must
remain exact at `8.4.2` and `0.2.7`; any S1 version failure is unexpected and
stops Stage B. Use a new private `--basetemp` for every pytest command. Repeat
the dependency gate, complete S1/S2/S3 surfaces, inventory checker, collection,
full serial suite, clean resolution, ABI inventory/hashes, and representative
creation/runtime bytecode fingerprints. No skip, xfail, warning suppression,
unrelated source change, production-contract change, or artifact difference
is authorized.

### Refreshed evidence-freshness policy

There is no general wall-clock freshness window. Evidence becomes stale on
any of these events:

- any change to direct inputs, compiled lock bytes, selected package version,
  resolver/auditor command, index policy, Python/pip/pip-tools/pip-audit
  provenance, or installed old/candidate inventory;
- any change to the H-01 owned files, reconciled `rh` commit, integrated S3
  source, S1/S2/S3 test surface, compiler input, ABI, or artifact baseline;
- any change to the authoritative Dependabot ledger or fresh no-ignore audit
  result, including a new finding, changed range/alias/fix version, or removed
  finding;
- any change to a primary advisory's affected range, exploit analysis, or
  patch status for an exception or Vyper applicability determination;
- loss of an exception's stated reachability assumption or compensating
  control; scheduled review or hard expiry of an exception; or
- any private-evidence custody event, integrity mismatch, or permission
  change.

After final Candidate A lock generation, refresh K-02 and run fresh raw
no-ignore audits against both old and candidate locks. Recheck every primary
range and exception assumption, then repeat K-02, the candidate audit,
path/hash/mode custody checks, and branch-freshness check immediately before
the Stage B reviewer gate. A lock, toolchain, selected-version, S1/S2/S3
surface, compiler/source, or reconciled-baseline change additionally requires
fresh deterministic resolution, environment inventories, the complete
brief-defined validation suite, and ABI/creation/runtime-artifact comparison.

This policy covers every alert severity, every auditor finding, the complete
lock and environment, all bounded exceptions and applicability
determinations, S1/S2/S3/full-suite results, and ABI/artifact evidence. Stale
evidence blocks submission to the Stage B reviewer gate, Stage B acceptance,
merge eligibility, and every rehearsal or deployment action. It does not make
ordinary offline unit tests depend on the network, current advisory state, or
wall clock; freshness is checked and recorded at the gated workflow events.

### Refreshed private-evidence custody plan

The pause extends custody beyond the originally anticipated Stage B gate.
The proposed continuing custodian is **Mick Hagen, H-01 owner**. The
authoritative local location remains:

```text
/Users/wigglez/dev/ripe-protocol-h1-private-evidence/
```

At packet preparation the directory was owned by local UID/GID `501:20` and
mode `0755`; every retained file was owned by the same UID/GID and mode
`0600`. Approval must require an owner-only directory mode of `0700` before
any further H-01 evidence access or Stage B work, followed by a recorded
owner/mode recheck. This packet does not itself authorize or perform that
permission change.

There are now three K-02 raw/sanitized pairs:

| Snapshot | Raw SHA-256 | Sanitized SHA-256 | Mode |
|---|---|---|---|
| `2026-07-24T172639Z` | `52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `0600` |
| `2026-07-24T182745Z` | `52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `0600` |
| `2026-07-24T201311Z` | `52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `0600` |

Five ancillary audit/environment records in the same directory remain at
their recorded hashes and mode `0600`:

| Ancillary private record | SHA-256 | Mode |
|---|---|---|
| `audit-tool-environment-inventory-2026-07-24T182745Z.txt` | `e1284aaefc7051673541ec1bb24b6a215169a78865375896314ba48b17c02d8e` | `0600` |
| `candidate-zero-environment-inventory-2026-07-24T182745Z.txt` | `e9ec0c1bcc7954a5dbce5c98d8111935b3f32236960468db959aa447e1d37ca1` | `0600` |
| `old-environment-inventory-2026-07-24T182745Z.txt` | `10a17ea189dfdf2ccd0e70eed88e1f9b274e080e6fce7c8dac2d214844180eeb` | `0600` |
| `pip-audit-candidate-zero-2026-07-24T182745Z-raw.json` | `9ae967aadec370959f356929ed229928c48caffcd4b656c3f81ceaa1f80a7db9` | `0600` |
| `pip-audit-old-2026-07-24T182745Z-raw.json` | `5bb47d3f69669aae51bf3007532ba156de40c1da0d5e3c50e005eebd75c3f8d2` | `0600` |

The following controls apply to all private evidence:

- **Permitted use:** local integrity verification, sanitized projection, and
  direct owner/security/reviewer inspection for H-01 only. Raw authenticated
  responses may not be committed, uploaded, emailed, pasted into review
  systems, used to mutate alert state, or disclosed outside the named review
  group. Only sanitized fields and hashes may enter the repository.
- **Copy/storage rule:** these remain the sole authoritative copies in the
  private directory. The owner continues to accept single-copy loss risk.
  No move, rename, duplicate, cloud sync, or backup is authorized without a
  separate custody decision.
- **Integrity triggers:** recheck the directory path/owner/mode and every file
  path, filename, hash, owner, and mode after every K-02/audit refresh, branch
  reconciliation, access by a reviewer, custody event, staging operation, and
  immediately before the Stage B reviewer gate.
- **Retention:** retain through the latest of refreshed Stage B reviewer
  acceptance, post-merge authoritative default-branch K-02 refresh, and final
  disposition or expiry of every exception in this packet. Conduct a custody
  review on 15 August 2026; that review does not authorize automatic disposal.
- **Disposal:** only a separate explicit owner instruction after every
  retention condition is satisfied may authorize deletion. Use exact-file
  unlinking, not a broad directory target; record each path, pre-disposal
  hash/mode, UTC time, operator, command/method, result, and any known
  filesystem snapshot/backup limitation. Do not claim cryptographic secure
  erasure on APFS. The disposal record must be committed as sanitized
  evidence.

### Packet-preparation verification

| Read-only command or check | Result |
|---|---|
| `git rev-parse rh`; `git rev-parse origin/rh` | committed local `rh` `27765d2`; local remote-tracking ref `3e6e6f2` |
| `git diff --name-status 3e6e6f2..27765d2` | one addition only: `docs/chains/rh/track-6-s5-ledger-guard.md`; 1,283 lines |
| `git show -s --format=%P a2b6f225` | exact parents `22eb097e86a123c01a7117d5166b87ed11ae30c9` and `27765d29094256fa9619dd44a0bfd145863de8b7` |
| Parse all “Refrozen path” rows; hash `git show a2b6f225:<path>` | 17/17 exact matches; all recorded values are 64 lowercase hexadecimal characters |
| Fresh exact K-02 command above; canonical projection/count query | 13/13 retained alert records; 6 high, 6 medium, 1 low; exact alert-number set; raw and sanitized bytes unchanged |
| `jq` over retained old and Candidate Zero raw audits | old: 20 entries / 18 unique IDs; Candidate Zero: 4 entries / 4 unique IDs; the four-item blocker ledger matches |
| Repository search for `click.edit`, Pymdown config/import/extensions, and Pygments `AdlLexer`/Archetype use | direct Click CLI use confirmed; no `click.edit`; no repository Pymdown or affected lexer activation found |
| `stat` and `shasum -a 256` over the private directory | 11/11 files present at the recorded hashes, owner `501:20`, mode `0600`; directory owner `501:20`, current mode `0755` |
| `git diff --name-only a2b6f225`; `git ls-files --others --exclude-standard`; `git diff --check` | only this evidence file changed; zero untracked files; whitespace check passed |

The only non-evidence repository delta was the owner-directed merge of the
reviewed S5 documentation brief; the only new outside-repository records were
the fresh retained K-02 pair. No requirement, lock, dependency environment,
test, tool, production-contract source, script, artifact, or other production
file was changed. No dependency or runtime test was run because reconciliation
added only that documentation brief and this packet remains
pre-implementation. No merge to `rh`, push, deployment, signature,
verification submission, alert mutation, ignore flag, upstream report, or
external state-changing action occurred.

### Proposed replacement eight-item authorization

Owner/security approval must answer all eight items as one replacement policy:

1. **Supersession and policy:** approve this packet as the sole operative
   H-01 Stage B authorization, superseding the prior eight-item Candidate Zero
   authorization dated 24 July 2026; require zero unresolved applicable
   deployment-path high/medium findings while permitting only the exact
   bounded exceptions below.
2. **Exact candidate:** approve fresh resolution and trial of Candidate A only:
   exact `titanoboa==0.2.7`, `pytest==8.4.2`, `requests==2.33.0`,
   `urllib3==2.7.0`, `idna==3.15`, `python-dotenv==1.2.2`,
   `cbor2==5.9.0`, `wheel==0.46.2`, with Vyper/RLP/IPython/dotenv held as
   above and no Click, Pygments, or Pymdown version change.
3. **pytest/S1 exception:** approve `EX-H01-PYTEST-01`, its named owner,
   private-basetemp/single-tenant controls, 15 August review, 31 August hard
   expiry, and unchanged exact S1 profile.
4. **Documentation/low exceptions:** approve
   `EX-H01-PYGMENTS-01`, `EX-H01-PYMDOWN-SNIPPETS-01`, and
   `EX-H01-PYMDOWN-B64-01` with their exact scopes, controls, triggers, review,
   and expiry; explicitly reject docs/lexer churn solely to improve the alert
   count.
5. **Four audit-blocker findings:** approve `EX-H01-CLICK-01`; approve both
   Vyper findings as not applicable to `vyper==0.4.3` based on their primary
   reviewed ranges; approve raw no-ignore auditing and ledger reconciliation;
   authorize no ignore flag and no upstream report.
6. **Baseline and sequence:** approve reconciled baseline merge `a2b6f225`
   over exact reviewed `rh` commit `27765d2`; require a new stop and owner
   direction on any later `rh`/owned-file movement; preserve S3-first and run
   Candidate A as a single six-package slice with no partial landing.
7. **Toolchain, validation, and evidence hygiene:** approve the exact
   resolver/auditor provenance and commands above, private pytest basetemps,
   retained resolver inventory and candidate preimages, mechanically generated
   hashes/diffs, complete old/new validation, artifact equality, and every
   existing stop condition.
8. **Freshness, custody, and reviewer gate:** approve the event-driven
   evidence-freshness policy and covered evidence above; approve Mick Hagen as
   custodian, changing only the exact private evidence directory from current
   mode `0755` to `0700` before further access, the
   permitted-use/copy/retention/integrity/disposal rules, continuing
   single-copy risk, and the same independent security/Track 6 reviewer as the
   mandatory Stage B reviewer. Explicitly accept the recorded non-secret K-02
   process deviation as not invalidating this packet, while prohibiting
   `gh auth status` in every future refresh; otherwise reject the packet and
   provide a remediation decision. No merge, push, deployment, signing,
   verification submission, alert mutation, or other live action is
   authorized.

Approval must be explicit. Until all eight decisions are approved, H-01
remains **Stage B blocked / packet pending** and no implementation may begin.

## Replacement Stage B authorization record — closed 24 July 2026

The designated independent security/Track 6 reviewer reviewed commit
`3b8cf72f16ba8297ee6968d2d5b5d877e00b5cba` end to end and approved the
packet subject to custody hardening, a full pre-edit serial baseline,
deliberate treatment of in-flight authority-document changes, and a separately
authorized upstream metadata report. The owner then explicitly approved all
eight replacement items, Candidate A, all five bounded exceptions, both Vyper
dispositions, the K-02 deviation, freshness, and custody controls.

The owner accepted the first three operational conditions as follows:

- change only the exact private-evidence directory from `0755` to `0700`
  before any further private-evidence access, verify ownership/mode, and
  preserve every retained file hash;
- run the complete serial old-profile baseline immediately after custody
  hardening and before any requirement, lock, dependency, or runtime-test
  edit; and
- treat uncommitted planning corrections as non-authoritative, but stop,
  reconcile, refreeze, and rerun every affected validation if those
  corrections or another relevant authority change integrates into `rh`
  before the Stage B reviewer gate.

The owner did **not** authorize a public PyPA report within H-01. The
`PYSEC-2023-142` machine-readable metadata discrepancy remains recorded; any
upstream report requires a separate, narrowly scoped owner approval. H-01 does
not wait for upstream action. This owner decision replaces, rather than
partially satisfying, the reviewer's proposed fourth condition.

This approval supersedes in full the previous eight-item Candidate Zero
authorization dated 24 July 2026. It authorizes Stage B implementation and
evidence collection only. It does not authorize merge, push, deployment,
signing, alert mutation, verification submission, or any other live action.
H-01 must stop at the mandatory Stage B reviewer gate.

### Custody hardening and retained-integrity proof

The first post-approval action was exactly:

```text
chmod 0700 /Users/wigglez/dev/ripe-protocol-h1-private-evidence
stat -f 'mode=%Lp owner=%u:%g path=%N' \
  /Users/wigglez/dev/ripe-protocol-h1-private-evidence
```

The change completed at filesystem ctime `2026-07-24T20:54:37Z`, before any
further private-evidence access. The resulting directory mode is `0700` and
owner is `501:20`. A subsequent hash/mode/owner pass verified all 11 retained
files are still present, owned by `501:20`, mode `0600`, and byte-identical to
the hashes in the refreshed custody tables above. No file was moved, renamed,
copied, or modified.

### Freshness stop, reconciliation, and refreeze

The first approved baseline run began on merge `a2b6f225`. Before completion,
the owner reported that `rh` had advanced to
`4966969265c6056bc7f3f139dc1a2437ef553c9f`. The freshness stop fired
immediately. The in-progress full suite was interrupted at 1,726 passed and
142 deselected after 197.58 seconds; this was an intentional stale-baseline
interruption, not a test failure and not baseline-completion evidence. Its
exact private basetemp was removed.

The integration worktree was clean. The committed delta from `27765d2` to
`4966969` was ten planning/authority documents only: 1,255 insertions and 453
deletions. It changed both frozen Track 7 outputs but no H-01 requirement,
lock, S1 file, dependency-gate path, evidence path, production source, script,
ABI, or artifact. H-01 merged exact `4966969`, producing:

```text
789a8df27cea479e477ff1323b0a7d83b554d441
parent 3b8cf72f16ba8297ee6968d2d5b5d877e00b5cba
parent 4966969265c6056bc7f3f139dc1a2437ef553c9f
```

The refreeze was captured at `2026-07-24T21:03:14Z`
(`2026-07-24T15:03:14-0600`, MDT).

| Reconciled refrozen path | SHA-256 |
|---|---|
| `docs/chains/rh/track-7-h1-dependency-security-preflight.md` | `ac31478d185571c9b804c84a0f78de60bf40eeb3a0aec80b839b66f62befef22` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `ffd3f6a5d17d2c61b58ecbbe86d39230b38508b54ae44fb018bfa551f9cfd1e2` |
| `docs/chains/rh/robinhood-deployment-validation-plan.md` | `ab39fd135c50f7d348788341a061511b50a854550234de9165554e5674ec2393` |
| `docs/chains/rh/minimal-contract-change-reassessment.md` | `72c2d1fe13b6f551712935ff78eba0f801f56d80965f3f449a726c74e4a40186` |
| `docs/chains/rh-summary.md` | `bb1190bcc9bb26201ffdfdea8ede91ef7a3ea384c7d60a2285405a03e66184c2` |
| `docs/chains/rh/block-clock-validation-plan.md` | `b6891973cea3cb72dade1975f443b49b7ef5c210c481ac62472d07f15ed8e5bc` |
| `docs/chains/rh/block-number-inventory.md` | `d6f5e89a673bf74f6ebd68033348e48ba295cd2c5c0c903869a8b339a10699d4` |
| `docs/chains/rh/component-matrix.md` | `bea64119069943534d6b877c04f453f82f8560540099593841c4c770706764c7` |
| `docs/chains/rh/shared-block-clock-specification.md` | `9c501491c8a96a08ef5136f836baea04ea041eb525a703862d3925e19c7afec4` |
| `docs/chains/rh/track-6-s4-deleverage-cooldown.md` | `865b459e6d630cb89feebc69edc6f058d72093ccaa81c00e6fb889f87e582962` |
| `docs/chains/rh/track-6-s5-ledger-guard.md` | `266112d5ee1cb0f261d4d3b833ea6c5911d4b62c5646718063e6808a2c1a4dd5` |
| `requirements.in` | `2a6726cdc447cb71cc376ef14ee93cc645dbb43826893c5d2433586a89f26f63` |
| `requirements.txt` | `18df0aad224f2a10febc9e155e4a530e1000ec553916c8ef78dc9859c6c92ba0` |
| `tests/clock/test_clock_profiles.py` | `2b1bbd8c77f97e614c9db54fcb98b284d3db95a6bb47d1ee9ab020bf6d725cc4` |
| `tests/utils/clock_profiles.py` | `69f3a616a78cb3a155962edb779533f56e362a68cc922c307dc7d40cbd4b34de` |
| `docs/chains/rh/lootbox-floor-implementation-record.md` | `d577f44507954ee3d1eee3efc4e940833557287d1fdb2890c863070cfee9be7c` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |
| `scripts/abis/Lootbox.json` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` |
| `config/block-clock-inventory.json` | `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb` |
| `scripts/check_block_clock_inventory.py` | `cc86f73629589c6a2ee0c9b60e480761d88e1e033e452c1f0843c18db9e28642` |
| `tests/conf_core.py` | `2ee8fa9222c99345fbc43ecbbf1641c185688724cc36e6a910f43069e4c06f0f` |
| `tests/inventory/test_block_clock_inventory.py` | `d9007158565979f7e5027a012a0cf6efdc6be354f0a96b16b7d35c87ba58a39c` |
| `tests/core/lootbox/test_underscore_rewards.py` | `20b86c2d5466863dc2afceaa580d8ae19c5beb363fb937090aabc1eca6bf7e7b` |
| `tests/config/test_switchboard_charlie.py` | `a444c5fc64439ccb28f5634248cb9459e579336452d59fb741e1d076d7e1fd44` |

A first read-only draft of the refreeze loop mistakenly named
`docs/chains/rh/rh-summary.md`. `git show` rejected that nonexistent path, but
the draft pipeline still hashed empty input because it lacked `pipefail`.
That value was rejected immediately, never entered a file, and the correct
`docs/chains/rh-summary.md` value above was recomputed. A second loop used the
correct path, `pipefail`, and an existence check; all 24 paths passed.

### Complete reconciled old-profile baseline

Every pytest invocation used a fresh mode-`0700` task parent and an explicit
private `--basetemp`; every task parent was removed after the command. The
complete serial baseline finished before any requirement, lock, dependency,
or test edit:

| Command | Result |
|---|---|
| `python -m pip check` | no broken requirements; 0.34 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. python -m pytest --basetemp=PRIVATE -q tests/clock/test_clock_profiles.py` | 57 passed in 27.45 s; 65.09 s wall |
| `PYTHONPATH=. python scripts/check_block_clock_inventory.py --check` | clean; production `100/95/17`, BN `32/100`, indirect `1`, cadence candidates `455`, seconds-unit candidates `58`, timestamp `11/37`, mixed-clock functions `4`, Vyper paths `92`; non-production test `31/29/5`, cadence test `159`; 1.40 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. python -m pytest --basetemp=PRIVATE -q tests/inventory/test_block_clock_inventory.py` | 60 passed in 25.78 s; 26.80 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. python -m pytest --basetemp=PRIVATE -q tests/core/lootbox/test_underscore_rewards.py` | 59 passed in 29.80 s; 68.70 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. python -m pytest --basetemp=PRIVATE -q tests/config/test_switchboard_charlie.py` | 91 passed in 35.53 s; 75.40 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. python -m pytest --basetemp=PRIVATE --collect-only -q` | 2,722 collected, 142 deselected in 1.23 s; 2.58 s wall |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. python -m pytest --basetemp=PRIVATE -q` | 2,722 passed, 142 deselected in 301.94 s; 362.03 s wall |

The placeholder satisfies only the repository's collection-time environment
guard. No explorer or external service was called. The worktree remained
clean after the baseline. Candidate resolution and every dependency/test edit
were still unstarted.

## Candidate A Stage B implementation — reviewer gate 24 July 2026

Candidate A was implemented only after the replacement authorization,
custody hardening, `4966969` reconciliation/refreeze, and complete pre-edit
serial baseline above. The resulting state is **exception-gated and pending
the mandatory independent Stage B review**. It is not merged, pushed,
deployed, signed, submitted for verification, or reflected in authoritative
default-branch alert state.

### Exact candidate and deterministic resolution

The owner-approved CPython `3.12.0` / pip `23.2.1` resolver environment
installed exact `pip-tools==7.4.1` from public PyPI with no installation
cache. It was seeded with the frozen old lock and used:

```text
PIP_CONFIG_FILE=/dev/null
PIP_INDEX_URL=https://pypi.org/simple
PIP_EXTRA_INDEX_URL=
PIP_NO_CACHE_DIR=1
pip-compile \
  --cache-dir=PRIVATE_DISPOSABLE_CACHE \
  --index-url=https://pypi.org/simple \
  --no-emit-index-url \
  --output-file=requirements.txt requirements.in
```

The truthful emitted lock header is:

```text
#    pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in
```

The fresh result reproduced the historically approved Candidate A preimages
byte-for-byte. A second clean compile from the same approved input and frozen
old-lock seed also reproduced both hashes exactly:

| Candidate A artifact | SHA-256 |
|---|---|
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| generated `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `c95340364a92f3bf07b4c0bb9ff44da941d7029c4b727167289e03f0001e040e` |

The full lock review found exactly six version changes:

```text
cbor2              5.7.0  -> 5.9.0
idna               3.10   -> 3.15
python-dotenv      1.2.1  -> 1.2.2
requests           2.32.5 -> 2.33.0
urllib3            2.5.0  -> 2.7.0
wheel              0.45.1 -> 0.46.2
```

All other lock versions are unchanged. The remaining diff is limited to the
approved direct-input pins, truthful resolver header, direct-input
annotations for the six selected packages and pytest, and wheel's new direct
annotation under packaging. Titanoboa `0.2.7`, Vyper `0.4.3`, pytest `8.4.2`,
Click `8.2.1`, Pygments `2.19.2`, and Pymdown Extensions `10.16.1` remain
exactly held.

One initial repeat command named the nonexistent resolver path
`.../venv/bin/pip-compile` and exited `127` before executing any resolver.
The corrected command used the retained `.../resolver/bin/pip-compile` path
and reproduced the exact lock above. During the manual direct-input edit, an
initial patch briefly replaced the first line with the literal `...`; it was
noticed on the immediate line-number inspection, corrected before lock copy,
resolution, installation, or testing, and the corrected file was then
byte-compared with the retained approved preimage. No candidate was generated
from the transient invalid input.

### Clean environments and rollback reproduction

Independent old and Candidate A environments were created, never upgraded in
place, from the frozen and candidate locks. Both used Darwin `25.5.0`,
macOS `26.5.2`, arm64, CPython `3.12.0`, and pip `23.2.1`; both installed
from public PyPI with `--no-cache-dir`; both contain 93 packages; and both
passed `python -m pip check`. A mechanical inventory comparison found only
the six version changes above. Selected-package metadata matched the lock and
no `direct_url.json`, local, editable, URL, or private-index installation was
present.

Rollback is recreation from reconciled parent `789a8df`:

```text
git show 789a8df:requirements.in
git show 789a8df:requirements.txt
python3.12 -m venv PRIVATE_OLD_ENV
PIP_CONFIG_FILE=/dev/null PRIVATE_OLD_ENV/bin/python -m pip install \
  --no-cache-dir --index-url https://pypi.org/simple \
  -r OLD_REQUIREMENTS_TXT
PRIVATE_OLD_ENV/bin/python -m pip check
```

That exact old lock was installed successfully and is the hash-anchored old
inventory below. This is rollback reproduction evidence, not authorization to
reset, revert, merge, or alter another branch.

| Retained private environment record | SHA-256 | Mode |
|---|---|---|
| `stageb-resolver-environment-inventory-2026-07-24T211519Z.txt` | `df6d690ab688349177fbc2ffbe46e1c43765d9ef62c3ca0318dc31eba9b545f4` | `0600` |
| `candidate-a-requirements-in-2026-07-24T211609Z.txt` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` | `0600` |
| `candidate-a-requirements-lock-2026-07-24T211609Z.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` | `0600` |
| `stageb-old-environment-inventory-2026-07-24T211741Z.txt` | `10a17ea189dfdf2ccd0e70eed88e1f9b274e080e6fce7c8dac2d214844180eeb` | `0600` |
| `stageb-candidate-a-environment-inventory-2026-07-24T211741Z.txt` | `e15eb92a788af8fa0ad18b11c5a719f258e6e7428187ffeefe765c6998abdff1` | `0600` |
| `stageb-audit-environment-inventory-2026-07-24T211948Z.txt` | `e1284aaefc7051673541ec1bb24b6a215169a78865375896314ba48b17c02d8e` | `0600` |

### Fresh no-ignore audit reconciliation

An independent CPython `3.12.0` / pip `23.2.1` environment installed exact
`pip-audit==2.10.1` from public PyPI with no installation cache and passed
`pip check`. Both audit commands used the approved canonical policy:

```text
PIP_CONFIG_FILE=/dev/null python -m pip_audit \
  --no-deps --disable-pip -r REQUIREMENTS --format=json \
  --output PRIVATE_RAW_JSON
```

The first sandboxed attempts stopped before a query because pip-audit could
not create `~/Library/Caches/pip-audit`. The identical commands were repeated
with permission to use that standard cache; no flag, lock, dependency, or
audit policy changed. The frozen lock reported 20 entries in 11 packages
(18 unique IDs, including the previously observed duplicated cbor2 and idna
rows). Candidate A reported exactly seven entries in five packages. Every
Candidate A row matches the authorized ledger; there is no new, disappeared,
or range/fix-version-drifted finding:

| Candidate package | Audit ID | Aliases | Fix version | Operative disposition |
|---|---|---|---|---|
| Click `8.2.1` | `PYSEC-2026-2132` | `GHSA-47fr-3ffg-hgmw`, `CVE-2026-7246` | `8.3.3` | `EX-H01-CLICK-01` |
| pytest `8.4.2` | `PYSEC-2026-1845` | `GHSA-6w46-j5rx-g56g`, `CVE-2025-71176` | `9.0.3` | `EX-H01-PYTEST-01` |
| Pygments `2.19.2` | `PYSEC-2026-2987` | `GHSA-5239-wwwm-4pmq`, `CVE-2026-4539` | `2.20.0` | `EX-H01-PYGMENTS-01` |
| Pymdown Extensions `10.16.1` | `PYSEC-2026-2999` | `GHSA-62q4-447f-wv8h`, `CVE-2026-46338` | `10.21.3` | `EX-H01-PYMDOWN-SNIPPETS-01` |
| Pymdown Extensions `10.16.1` | `CVE-2026-61632` | `GHSA-9xwg-3r6f-jcx2` | `11.0.0` | `EX-H01-PYMDOWN-B64-01` |
| Vyper `0.4.3` | `PYSEC-2023-142` | `GHSA-5824-cm3x-3c38`, `CVE-2023-39363` | none | not applicable; primary range excludes `0.4.3` |
| Vyper `0.4.3` | `PYSEC-2025-33` | `GHSA-vgf2-gvx8-xwc3`, `CVE-2025-21607` | none | not applicable; primary range and fixed boundary exclude `0.4.3` |

The two Vyper results remain scanner-metadata dispositions, not ignored
findings or accepted compiler vulnerabilities. No `--ignore-vuln` flag was
used. Per owner direction, no PyPA or other upstream report was filed; that
would require separate narrowly scoped approval.

| Retained private raw audit | SHA-256 | Mode |
|---|---|---|
| `stageb-old-lock-raw-audit-2026-07-24T212056Z.json` | `b9e17c0f64df49d9e5127892a42063b7490a49e21aeb82a5ed1f8e1c176dd19d` | `0600` |
| `stageb-candidate-a-raw-audit-2026-07-24T212056Z.json` | `039bdc746c8b1f59088bf21ddbbd22128ba5822863404cf24bf7ac051e6a0d4f` | `0600` |

### Post-generation K-02 observation

After final Candidate A lock generation, the exact approved read-only K-02
query was repeated at `2026-07-24T21:21:49Z` without `gh auth status`. The
raw bytes and canonical projection remain identical to the earlier retained
snapshots: 13 current default-branch open alerts, 6 high, 6 medium, 1 low,
alert numbers `13, 14, 15, 16, 18, 19, 21, 22, 23, 24, 25, 26, 27`.

| Retained post-generation K-02 record | SHA-256 | Mode |
|---|---|---|
| `dependabot-open-2026-07-24T212149Z-raw.json` | `52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a` | `0600` |
| `dependabot-open-2026-07-24T212149Z-sanitized.json` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `0600` |

These alerts describe the repository default branch, not this unmerged
candidate. Candidate remediation is proven only against the generated lock
and fresh audit; no GitHub alert is claimed fixed or closed.

### Offline dependency gate and package behavior

`tests/deployment/test_dependency_gate.py` contains 12 offline tests. It
asserts the exact approved input/lock hashes and generated header; selected,
held, and forbidden versions; public-PyPI-only/no-local-source policy; all
seven residual findings and dispositions; the five complete exception
schemas and event-driven freshness controls; absence of the approved
Click/Pygments/Pymdown reachability triggers; unchanged S1 exact versions;
and the absence of subprocess, socket, advisory-query, or GitHub-query logic.

Isolated no-network cases additionally exercise Requests adapter, redirect,
retry, proxy, timeout, TLS-setting, and exception behavior; Unicode IDNA
normalization and rejection; dotenv search, interpolation, and environment
precedence; canonical cbor2 vectors; and wheel metadata. The gate passed all
12 tests under Candidate A with a private `--basetemp`.

The first test-development replay reported three assertion failures because
three required evidence phrases crossed Markdown line breaks. The package,
runtime, and compatibility cases passed. The assertions were corrected to
normalize only whitespace in the committed evidence text; no dependency,
exception, policy, source, or production behavior was weakened. The complete
gate then passed.

### Candidate validation

Every pytest invocation used a fresh mode-`0700` task parent and explicit
private `--basetemp`, and every task parent was removed after completion.
No skip, xfail, warning, or plugin suppression was used.

| Command | Candidate A result |
|---|---|
| `python -m pip check` | no broken requirements |
| `pytest -q tests/deployment/test_dependency_gate.py` | 12 passed |
| `pytest -q tests/clock/test_clock_profiles.py` | 57 passed in 27.75 s; 65.19 s wall |
| `python scripts/check_block_clock_inventory.py --check` | clean; production `100/95/17`, BN `32/100`, indirect `1`, cadence `455`, seconds-unit `58`, timestamp `11/37`, mixed-clock `4`, Vyper paths `92`; non-production test `31/29/5`, cadence test `159`; 1.30 s wall |
| `pytest -q tests/inventory/test_block_clock_inventory.py` | 60 passed in 25.39 s; 26.29 s wall |
| `pytest -q tests/core/lootbox` | all 175 reviewed Lootbox tests passed in 40.69 s; 79.45 s wall |
| `pytest -q tests/core/lootbox/test_underscore_rewards.py` | exact brief minimum: 59 passed in 30.11 s; 69.22 s wall |
| `pytest -q tests/config/test_switchboard_charlie.py` | 91 passed in 34.70 s; 73.06 s wall |
| `pytest --collect-only -q` | 2,734 selected / 2,876 total collected; 142 deselected in 1.33 s; 2.57 s wall |
| `pytest -q` | 2,734 passed, 142 deselected in 293.97 s; 351.62 s wall |
| second seeded `pip-compile`; candidate hash comparison | byte-identical input and lock; no resolver drift |
| `git diff --check` | passed |

The collection/full-suite increase from 2,722 to 2,734 is exactly the 12 new
dependency-gate tests. pytest and Titanoboa did not change, so the existing S1
test ran unchanged and no intentional version failure or S1 edit was needed.
The placeholder `ETHERSCAN_API_KEY=local-placeholder` satisfied only the
repository collection-time guard; no explorer or live external service was
called.

### ABI and compiler-artifact equality

S1 and S3 representative artifacts were compiled independently in the old and
Candidate A environments. Each old/candidate pair was byte-identical:

| Artifact | Source SHA-256 | ABI SHA-256 | Creation SHA-256 | Runtime SHA-256 | Combined fingerprint |
|---|---|---|---|---|---|
| S1 `ClockObserver` | `238b2198a0217158db3f93000da47e4af5535883807e7b39cc3864f8d5b432f7` | `55fd4609d43321ded86224d044944b9a1955be174ca91fd55b75fb179f5090c8` | `b5f9615f2267ede387f99c77873aded9a241d30d0269a6f1df336ed93e454ecd` | `6842b313171e51a6b1b4f99143074e263de3f72d943838a3ec887ad3b1dd16d6` | `9ac4b78267b62fe4a645212b3b2bc83498afcedb7b75804d9449ea2056ce791d` |
| S3 `Lootbox` | `ebb4dcca8fa95bafe8e38ddc1d01886bfaceaf06302fe195f63db0bb7b3ef1da` | `e752a206ba5c78cb573c734c7bfd1c407f1cb98898d3d8e9d3513836c56f5fb2` | `9246a6d9dbee596750dc3a50d27d4418f318a62b7b4826a13f76aee37621e6ce` | `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097` | `263f6e5a75b85763dfed0656b194109512fad6856bc2acf8cccef660586aea0d` |

Both use `vyper==0.4.3+commit.bff19ea2`; compiler settings are identical
within each pair. The first S3 fingerprint attempt supplied an unsupported
`name=` argument to `boa.load_partial` and stopped with `TypeError`; the
corrected read-only compile omitted that argument. The first S1 fingerprint
attempt omitted `tests` from `PYTHONPATH` and stopped at import with
`ModuleNotFoundError`; the corrected command used `PYTHONPATH=.:tests`.
Neither failed attempt produced or changed an artifact.

The old and Candidate A environments separately ran
`scripts/export_abis.py` to disposable directories. Each exported the same 49
ABIs, skipped the same 28 mock/testing paths, and reported the same nine known
standalone module-initializer failures. Relative inventories and every output
byte matched; both canonical 49-file hash inventories have SHA-256
`47942174d74fc35e33ee8ae44c0cdea57ebb29685d747f90c932c4c8fd828d9a`.
Both generated `Lootbox.json` files are byte-identical to committed
`scripts/abis/Lootbox.json`, SHA-256
`33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c`.

As already recorded by S3, full exporter output has five pre-existing
committed-output differences (`Deleverage.json`, `EndaomentPSM.json`,
`SwitchboardAlpha.json`, `SwitchboardDelta.json`, and
`wsuperOETHbPrices.json`) plus committed-only `DefaultsBaseSepolia.json`.
Those are identical old-versus-candidate conditions, not Candidate A drift,
and were not modified. An initial parallel exporter orchestration returned
before presenting its subprocess output; clean synchronized old and candidate
runs were then performed from empty disposable directories and are the results
recorded here.

### Scope, rollback, and reviewer stop

The exact Stage B repository scope is:

```text
docs/chains/rh/evidence/dependency-security-gate.md
requirements.in
requirements.txt
tests/deployment/test_dependency_gate.py
```

There is no change to S1, S2, S3, any production contract, deployment script,
historical migration, manifest, committed ABI, cache, virtual environment, or
other repository file. No secret, raw authenticated response, private path
contents, or dependency environment is committed. The raw K-02/audit data and
complete environment inventories remain outside Git under the approved
custody policy.

No Candidate A drift, unexpected audit finding, applicable unresolved
deployment-path alert, compatibility failure, S3 artifact difference, or
scope expansion remains. The five bounded exceptions remain current under the
approved 15 August 2026 review / 31 August 2026 hard-expiry policy; the two
Vyper findings remain approved not-applicable determinations. H-01 is therefore
**exception-gated and stopped at the mandatory Stage B reviewer gate**. It is
not closed, merge-ready, pushed, deployed, signed, or authorized for any live
action until the named independent security/Track 6 reviewer approves the
complete Stage B bundle and the owner separately acts within the brief.

### Final `rh` freshness stop, reconciliation, and refreeze

After implementation commit
`8459104d8917fe3b501870e24b1aaac1cb29f06c` and before the immediate
pre-review K-02/audit sequence, the required branch-freshness check found that
local and remote-tracking `rh` had advanced from `4966969` to:

```text
dd51c637f1462bede7529a53427bfb4327dbfb12
docs(rh): close S4 no-code checkpoint
```

The freshness stop fired before any further K-02 or audit access. The committed
delta is one new, independently reviewed 1,178-line authority record:
`docs/chains/rh/deleverage-cooldown-security-decision.md`. The integration
worktree also contained five modified planning documents and one untracked
H-02 brief; those remain uncommitted, were treated as non-authoritative, and
were not included in the reconciliation.

The S4 record selects unchanged source, constructor-default Robinhood
cooldown `0`, no initial Underscore deployment, and no S4 Stage B or Stage C.
It explicitly makes no dependency, compiler-input, source, ABI, test,
migration, manifest, or live-state change. It preserves H-01-first sequencing
if S4 is ever reopened. It therefore changes review authority and branch
freshness, but not Candidate A selection, the H-01 exception policy, or any
technical validation input.

H-01 merged only exact committed `dd51c637`, producing:

```text
079ab239f3d2aecc11e16a9b178c6da2d2033e3a
parent 8459104d8917fe3b501870e24b1aaac1cb29f06c
parent dd51c637f1462bede7529a53427bfb4327dbfb12
```

The refreeze was captured at `2026-07-24T21:52:30Z`
(`2026-07-24T15:52:30-0600`, MDT):

| Final reconciled/refrozen path | SHA-256 |
|---|---|
| `docs/chains/rh/track-7-h1-dependency-security-preflight.md` | `ac31478d185571c9b804c84a0f78de60bf40eeb3a0aec80b839b66f62befef22` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `ffd3f6a5d17d2c61b58ecbbe86d39230b38508b54ae44fb018bfa551f9cfd1e2` |
| `docs/chains/rh/robinhood-deployment-validation-plan.md` | `ab39fd135c50f7d348788341a061511b50a854550234de9165554e5674ec2393` |
| `docs/chains/rh/minimal-contract-change-reassessment.md` | `72c2d1fe13b6f551712935ff78eba0f801f56d80965f3f449a726c74e4a40186` |
| `docs/chains/rh/deleverage-cooldown-security-decision.md` | `98cbe896e502ad280f4b3de74e45181937b5085988dd9c6d45d2ce0e167a755b` |
| `docs/chains/rh-summary.md` | `bb1190bcc9bb26201ffdfdea8ede91ef7a3ea384c7d60a2285405a03e66184c2` |
| `docs/chains/rh/block-clock-validation-plan.md` | `b6891973cea3cb72dade1975f443b49b7ef5c210c481ac62472d07f15ed8e5bc` |
| `docs/chains/rh/block-number-inventory.md` | `d6f5e89a673bf74f6ebd68033348e48ba295cd2c5c0c903869a8b339a10699d4` |
| `docs/chains/rh/component-matrix.md` | `bea64119069943534d6b877c04f453f82f8560540099593841c4c770706764c7` |
| `docs/chains/rh/shared-block-clock-specification.md` | `9c501491c8a96a08ef5136f836baea04ea041eb525a703862d3925e19c7afec4` |
| `docs/chains/rh/track-6-s4-deleverage-cooldown.md` | `865b459e6d630cb89feebc69edc6f058d72093ccaa81c00e6fb889f87e582962` |
| `docs/chains/rh/track-6-s5-ledger-guard.md` | `266112d5ee1cb0f261d4d3b833ea6c5911d4b62c5646718063e6808a2c1a4dd5` |
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `c95340364a92f3bf07b4c0bb9ff44da941d7029c4b727167289e03f0001e040e` |
| `tests/clock/test_clock_profiles.py` | `2b1bbd8c77f97e614c9db54fcb98b284d3db95a6bb47d1ee9ab020bf6d725cc4` |
| `tests/utils/clock_profiles.py` | `69f3a616a78cb3a155962edb779533f56e362a68cc922c307dc7d40cbd4b34de` |
| `docs/chains/rh/lootbox-floor-implementation-record.md` | `d577f44507954ee3d1eee3efc4e940833557287d1fdb2890c863070cfee9be7c` |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |
| `scripts/abis/Lootbox.json` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` |
| `config/block-clock-inventory.json` | `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb` |
| `scripts/check_block_clock_inventory.py` | `cc86f73629589c6a2ee0c9b60e480761d88e1e033e452c1f0843c18db9e28642` |
| `tests/conf_core.py` | `2ee8fa9222c99345fbc43ecbbf1641c185688724cc36e6a910f43069e4c06f0f` |
| `tests/inventory/test_block_clock_inventory.py` | `d9007158565979f7e5027a012a0cf6efdc6be354f0a96b16b7d35c87ba58a39c` |
| `tests/core/lootbox/test_underscore_rewards.py` | `20b86c2d5466863dc2afceaa580d8ae19c5beb363fb937090aabc1eca6bf7e7b` |
| `tests/config/test_switchboard_charlie.py` | `a444c5fc64439ccb28f5634248cb9459e579336452d59fb741e1d076d7e1fd44` |

All 25 pre-existing refrozen paths retain their previously validated bytes;
only the S4 decision record is new. Consequently no package environment,
resolver, audit input, S1/S2/S3 source, test collection, ABI, migration, or
compiler artifact was affected. The complete 2,734-test run and old/new
artifact comparisons remain applicable. The evidence-dependent offline gate,
branch freshness, candidate audit, K-02, and custody checks must be repeated
against the final reconciled reviewer bundle.

## Independent Stage B approval, superseding `rh` movement, and reopened review

### Formal review received for `dc3ef1d`

On 24 July 2026, the owner supplied the formal decision of the designated
independent security/Track 6 reviewer:

> The Stage B bundle at `dc3ef1d` is approved by the independent
> security/Track 6 reviewer.

That reviewer reported inspecting the complete brief-defined surface and
independently creating a clean CPython 3.12.0 environment from the committed
lock. In that environment, `pip check` passed, the 12 selected/held packages
matched, the dependency gate passed 12/12, and S1 passed 57/57 against the
bytes at `dc3ef1d`. This independent execution closed the prior record's gap
between the last agent-run gate and the final evidence-only commit.

The approval retained all five bounded exceptions and their 15 August 2026
review / 31 August 2026 hard-expiry controls. It also retained K-02 custody
until the later of the post-merge alert refresh and final exception
disposition, and required the post-merge default-branch refresh to distinguish
candidate remediation from authoritative GitHub alert closure. No merge,
push, alert mutation, deployment, signing, verification submission, or other
live action was authorized.

The reviewer expressly stated that a dependency, lock, expected-version,
test-policy, evidence, or artifact change after review reopens the relevant
reviewer scope. The approval therefore remains an immutable approval of
`dc3ef1d`; it is not silently transferred to later bytes.

### Freshness discrepancy and required stop

The formal review record was received at 16:10 MDT. It reported that the H-01
branch was 15 commits ahead and zero behind `rh`. Repository metadata instead
showed that `rh` and `origin/rh` had already advanced at 16:01:54 MDT to:

```text
063d9459c4c0acf29a4d4e59251ad32bf2d71184
docs: reconcile S4 and add Track 7 H-02 brief
parent dd51c637f1462bede7529a53427bfb4327dbfb12
```

At `dc3ef1d`, the correct relationship was one commit behind and 15 commits
ahead. The review's branch-freshness statement was therefore stale even
though its independently checked H-01 files, lock, environment, tests,
audits, K-02 records, and artifacts were accurate.

This movement integrated the exact planning corrections that the replacement
authorization had required H-01 to treat as non-authoritative while they were
uncommitted. It occurred before the Stage B reviewer record. The owner's
standing instruction therefore required H-01 to stop, reconcile/refreeze,
and rerun every affected validation rather than relying on the stale
zero-behind statement.

The committed `dd51c637..063d945` delta contains only:

```text
docs/chains/rh-summary.md
docs/chains/rh/component-matrix.md
docs/chains/rh/minimal-contract-change-reassessment.md
docs/chains/rh/robinhood-deployment-support-specification.md
docs/chains/rh/shared-block-clock-specification.md
docs/chains/rh/track-7-h2-network-profiles-cli.md
```

The first five files reconcile the approved S4 no-code posture and the
reviewed H-02 ownership correction. The new H-02 brief explicitly blocks
H-02 until reviewed H-01 requirements and evidence are integrated into `rh`;
it prohibits H-02 from changing H-01 dependencies and makes the H-01 gate,
S1, S2, and the full suite downstream validation inputs. The delta does not
change the H-01 brief, requirements, lock, dependency gate, S1/S2/S3 source
or tests, contract/compiler input, migration, ABI, artifact, exception,
audit, K-02, or custody policy.

Only exact committed `063d945` was merged into the H-01 track, producing:

```text
7cbaaf01fca73ae260a50a32f272ef7fec6ace26
parent dc3ef1da98d51431659f9ad306b17d5312096fb9
parent 063d9459c4c0acf29a4d4e59251ad32bf2d71184
```

Immediately after that reconciliation, the branch was zero behind and 16
commits ahead of local and remote-tracking `rh`. The H-01 four-file diff
against `rh` remained unchanged.

### Refrozen authority and technical anchors

The newly authoritative documentation bytes are:

| Reconciled authority path | SHA-256 |
|---|---|
| `docs/chains/rh-summary.md` | `8a44754bccfbc7698e71421b57fb2c591808a838fa91c7005223bfdff2ae97ea` |
| `docs/chains/rh/component-matrix.md` | `33747982b11a1f9430619710b8b2007113dfb5961a90162def4c852c1b6b18e6` |
| `docs/chains/rh/minimal-contract-change-reassessment.md` | `e29a1163b4cb1b4837ed8857775e9d1ea557bd3dc56213a594fa3fde0267987f` |
| `docs/chains/rh/robinhood-deployment-support-specification.md` | `9a85d0a0307ce8fc6d268d6c48ab9a27bc60a75f8cbb655e88220020e7482698` |
| `docs/chains/rh/shared-block-clock-specification.md` | `7afcd89fe4b07c597ae1670f453010c66bbceaa7659cd7411ad2eb01b342a4cf` |
| `docs/chains/rh/track-7-h2-network-profiles-cli.md` | `f37597f37d6cf785f50bac0954709e2f60dde7ab836ed2c699cab45e5d105b59` |

The affected-scope analysis rechecked these H-01 and compiler/artifact
anchors:

| Refrozen H-01 path | SHA-256 | Disposition |
|---|---|---|
| `docs/chains/rh/track-7-h1-dependency-security-preflight.md` | `ac31478d185571c9b804c84a0f78de60bf40eeb3a0aec80b839b66f62befef22` | unchanged |
| `docs/chains/rh/robinhood-deployment-validation-plan.md` | `ab39fd135c50f7d348788341a061511b50a854550234de9165554e5674ec2393` | unchanged |
| `docs/chains/rh/deleverage-cooldown-security-decision.md` | `98cbe896e502ad280f4b3de74e45181937b5085988dd9c6d45d2ce0e167a755b` | unchanged |
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` | unchanged |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` | unchanged |
| `tests/clock/test_clock_profiles.py` | `2b1bbd8c77f97e614c9db54fcb98b284d3db95a6bb47d1ee9ab020bf6d725cc4` | unchanged |
| `tests/utils/clock_profiles.py` | `69f3a616a78cb3a155962edb779533f56e362a68cc922c307dc7d40cbd4b34de` | unchanged |
| `contracts/core/Lootbox.vy` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` | unchanged |
| `scripts/abis/Lootbox.json` | `33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c` | unchanged |

No clean dependency environment, resolver, audit, alert, ABI export, compiler
fingerprint, S1/S2/S3 test, or full-suite input changed. Their validated
results remain applicable. The authority refreeze, H-01 gate, fixture
isolation, branch topology, scope, and whitespace checks are the validations
affected by this reconciliation and evidence/test correction.

### Strict-sandbox fixture isolation correction

The independent reviewer noted that, at `dc3ef1d`, collection of the
dependency-only gate inherited the repository-wide autouse `ripe_hq` fixture.
That fixture resolved through `env`, `anvil`, and `free_port`; `free_port`
bound an ephemeral local socket even though the 12 H-01 tests made no external
query. This was not an external network request and did not invalidate the
reviewer's results, but it could fail during setup on a CI runner that blocks
all socket creation.

The H-01-owned gate now defines a module-local, session-scoped no-op
`ripe_hq` fixture. It deliberately overrides only the irrelevant protocol
autouse setup for this dependency-only module; it does not alter repository
fixture policy or any production/runtime test. The 12 test bodies and every
dependency, exception, hash, audit, freshness, and S1 assertion remain
unchanged. The corrected gate SHA-256 is
`a0d3dcc22d0754229c8226fb55a99c2f17cfb004766285ed67a3c5075a39d948`.

A fresh CPython 3.12.0 environment was created from the unchanged committed
lock under a new mode-`0700` disposable directory using
`python -m venv`, followed by
`python -m pip install --no-cache-dir -r requirements.txt`. Installation
completed from public PyPI and `python -m pip check` reported no broken
requirements. `pytest --fixtures-per-test` then showed the local `ripe_hq`
override for all 12 tests, plus only `monkeypatch`, `tmp_path`, and
`tmp_path_factory` where explicitly requested. It showed no `env`, `anvil`,
`free_port`, or other protocol fixture in this module's resolved setup graph.

This fixture isolation is a test-policy change after `dc3ef1d`; together with
this evidence addition and the corrected branch baseline, it reopens the
corresponding scope. H-01 remains exception-gated and stopped for renewed
independent security/Track 6 review. The prior review is preserved as valid
evidence for the immutable `dc3ef1d` bundle, not represented as approval of
this corrected bundle.

Final affected validation in the fresh Candidate A environment produced:

| Command | Result |
|---|---|
| `python -m pip check` | no broken requirements |
| `pytest --fixtures-per-test -q tests/deployment/test_dependency_gate.py` | all 12 cases resolve to the local `ripe_hq` override; no `env`, `anvil`, or `free_port`; collection-only fixture report completed cleanly |
| `pytest -q tests/deployment/test_dependency_gate.py` | 12 passed in 0.05 s |
| `pytest -q tests/clock/test_clock_profiles.py` | 57 passed in 27.10 s |
| `pytest --collect-only -q` | 2,734 selected / 2,876 total collected; 142 deselected in 1.24 s |
| `pytest -q -p no:cacheprovider` | 2,734 passed, 142 deselected in 293.40 s |
| `git diff --check` | passed |

S1 and collection were replayed even though their inputs were unchanged, to
confirm the module-local fixture override neither escaped its H-01 test module
nor altered the approved runtime profile or suite inventory. Although the
reconciled commit changes documentation only and the fixture correction only
removes irrelevant setup from the 12-test module, the complete serial suite
was also replayed after all test-body changes. It passed exactly, so renewed
review need not rely on an applicability argument for the final test bytes.

## Independent Candidate A payload review — technically approved 24 July 2026

**Current integration-baseline review:** Pending.

The designated independent security/Track 6 reviewer technically approved
the exact H-01 Candidate A dependency/test payload at:

```text
001ccaccdf473223ba33e3eeb37509a01990a60e
```

That reviewed payload was reconciled against the then-current, now-previous
reviewed `rh` integration baseline
`063d9459c4c0acf29a4d4e59251ad32bf2d71184`. The technical payload approval
superseded the current-state effect of earlier stopped, pending, blocked, or
reviewer-gate-waiting statements while that baseline remained current, and
those statements remain historical checkpoint evidence. It does not approve
the uncommitted evidence-amendment bytes or establish merge readiness against
the newer integration baseline
`2517eeb0013cdb277dc4815db4b524d7a090d682`.

### Exact reviewed scope and installation

At the payload review, the approved committed bundle differed from the
then-current `rh` by exactly these four permitted H-01 files:

| Reviewed path | SHA-256 at `001ccac` |
|---|---|
| `docs/chains/rh/evidence/dependency-security-gate.md` | `a3fb8c90171ca24d93e1ab748ab7f1df2cd5a1c3dc0fd96b599c91fdb452306c` |
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `a0d3dcc22d0754229c8226fb55a99c2f17cfb004766285ed67a3c5075a39d948` |

The reviewer independently created a clean CPython 3.12.0 environment from
the committed Candidate A lock using public PyPI. Installation completed
cleanly, every selected and held package matched the approved exact version,
and `python -m pip check` reported no broken requirements.

### Final no-ignore audit disposition

The fresh approved no-ignore audit reported exactly seven findings in five
packages, matching the committed ledger without any `--ignore-vuln` flag:

| Package | Finding | Final disposition |
|---|---|---|
| Click `8.2.1` | `PYSEC-2026-2132` | bounded exception `EX-H01-CLICK-01` |
| pytest `8.4.2` | `PYSEC-2026-1845` | bounded exception `EX-H01-PYTEST-01` |
| Pygments `2.19.2` | `PYSEC-2026-2987` | bounded exception `EX-H01-PYGMENTS-01` |
| Pymdown Extensions `10.16.1` | `PYSEC-2026-2999` | bounded exception `EX-H01-PYMDOWN-SNIPPETS-01` |
| Pymdown Extensions `10.16.1` | `CVE-2026-61632` | bounded exception `EX-H01-PYMDOWN-B64-01` |
| Vyper `0.4.3` | `PYSEC-2023-142` | not applicable; authoritative affected range is `>=0.2.15,<0.3.1` |
| Vyper `0.4.3` | `PYSEC-2025-33` | not applicable; authoritative affected range is `<0.4.1` |

Both Vyper findings are outside Vyper `0.4.3`'s authoritative affected
ranges. They remain scanner-metadata dispositions, not ignored findings,
bounded exceptions, or accepted compiler vulnerabilities.

### Reviewed payload validation and prior topology

The approved evidence includes the following final validation:

| Validation | Result |
|---|---|
| Clean Candidate A installation | completed from the exact committed lock |
| `python -m pip check` | no broken requirements |
| Fresh no-ignore audit | seven findings in five packages; exact ledger match |
| `pytest -q tests/deployment/test_dependency_gate.py` | 12 passed; the reviewer also reproduced 12/12 inside a restricted sandbox without protocol/socket setup |
| `pytest -q tests/clock/test_clock_profiles.py` | 57 passed |
| `python scripts/check_block_clock_inventory.py --check` | clean |
| `pytest -q tests/inventory/test_block_clock_inventory.py` | 60 passed |
| `pytest --collect-only -q` | 2,734 selected / 2,876 total; 142 deselected |
| Complete serial `pytest -q` | **2,734 passed, 142 deselected** |
| `git diff --check` | passed |

At the payload review, local `rh` and `origin/rh` both resolved to
`063d9459c4c0acf29a4d4e59251ad32bf2d71184`; the candidate was 17 commits
ahead and zero behind with a clean worktree and no published track ref.
`git merge-base rh 001ccac` returned exact `063d945`, and `rh` is an ancestor
of the candidate. The virtual merge was therefore a conflict-free
fast-forward at that reviewed baseline. This is historical payload-review
evidence, not a claim about current merge readiness and not permission for the
agent to merge or push.

### Reconciliation to the new integration baseline

After payload approval, local `rh` and `origin/rh` advanced to:

```text
2517eeb0013cdb277dc4815db4b524d7a090d682
merge: integrate Track 8 stock token vault specification
parents:
  063d9459c4c0acf29a4d4e59251ad32bf2d71184
  4b4cb6021dda8bcc054970c03175077184f1311a
```

The complete tree delta from the previous reviewed integration baseline
`063d9459c4c0acf29a4d4e59251ad32bf2d71184` to the new integration baseline
`2517eeb0013cdb277dc4815db4b524d7a090d682` consists only of these two Track 8
Markdown documents:

| New Track 8 document | SHA-256 | Delta |
|---|---|---:|
| `docs/chains/rh/stock-token-vault-change-specification.md` | `71099e629734e7f001a8cbfa40792dfc2ab9fbc5490cd8b9c80a8431a994705c` | 6,659 insertions |
| `docs/chains/rh/stock-token-vault-change-validation-plan.md` | `88edaf44fa375a7310cb73bec254d5801478e89479d51ded0c439f33a9a81bb1` | 2,460 insertions |

There is no deletion or modification in that tree delta and no dependency,
requirement, lock, test, compiler input, artifact, ABI, contract, migration,
script, or H-01-owned file change. The two documents introduce Track 8
planning/evidence authority only.

Before reconciliation, H-01 HEAD remained exact reviewed payload commit
`001ccaccdf473223ba33e3eeb37509a01990a60e`, its merge base with current `rh`
remained `063d9459c4c0acf29a4d4e59251ad32bf2d71184`, and the branch was 35
commits behind and 17 ahead of current `rh`.

The independent reviewer then approved the complete evidence file at exact
SHA-256
`9a8438109c046bab789ec5ba9048e1b35c955632dd5d160a0fe53020dfe39854`.
Those exact bytes were committed without amendment:

```text
579def4b22240cfc8e2a5e95d97cf40014b83f9e
parent 001ccaccdf473223ba33e3eeb37509a01990a60e
docs(rh): record final H-01 review provenance
```

Exact current `rh` baseline
`2517eeb0013cdb277dc4815db4b524d7a090d682` was then merged into the H-01
branch using a merge, not a rebase:

```text
c9ce0f501824305f74e84e1c8f1c1b3d4a20477f
parents:
  579def4b22240cfc8e2a5e95d97cf40014b83f9e
  2517eeb0013cdb277dc4815db4b524d7a090d682
```

The merge completed without conflict and preserved the already reviewed
Candidate A history. Immediately after reconciliation, `rh` and `origin/rh`
both remained exact `2517eeb`; the merge base was exact `2517eeb`; H-01 was
zero behind and 19 commits ahead; and the net delta remained exactly the four
authorized H-01 files. No dependency, requirement, lock, test, compiler,
artifact, ABI, contract, migration, or script byte changed during
reconciliation.

At reconciliation, current-baseline audit and validation still had to complete
against the reconciled tree before final independent merge-readiness review.
The completed results are recorded in the next dated section; reconciliation
alone did not establish merge readiness or authorize merge into `rh`.

### Surviving exceptions and post-merge obligations

All five bounded exceptions remain in force without amendment:

- `EX-H01-CLICK-01`
- `EX-H01-PYTEST-01`
- `EX-H01-PYGMENTS-01`
- `EX-H01-PYMDOWN-SNIPPETS-01`
- `EX-H01-PYMDOWN-B64-01`

Each requires security review on **15 August 2026** and has a hard expiry at
`2026-08-31T23:59:59Z`; expiry blocks deployment rehearsal and merge until a
fresh disposition is approved.

After owner integration, the authorized read-only K-02/default-branch refresh
must record what GitHub actually observes without claiming closure early.
All 13 alerts may persist until GitHub re-observes the merged manifest; the
expected steady residual set is alert #22 Pygments, #23 pytest, and #27
Pymdown Extensions, each still governed by its recorded exception. Any
different count, finding, severity, range, or package disposition requires
reconciliation rather than normalization.

Exception review and private-evidence custody also survive approval. Retention
continues until the later of the post-merge K-02 refresh and final disposition
of all five exceptions. The recorded custodian, mode/hash rechecks, permitted
security-evidence use, retention events, and no-move/no-delete controls remain
binding. Disposal requires the recorded event, method, and disposal record
and may occur only on separate explicit owner instruction.

The existing approval authorizes technical acceptance of the exact four-file
Candidate A payload at `001ccac` only. It does not by itself approve the
current post-reconciliation evidence update, the subsequent `2517eeb`
baseline merge, or the final branch merge-readiness state. It does not
authorize deployment, signing, verification submission, alert mutation,
production configuration, or any other live or production action. Merge and
push remain gated by the required review sequence and owner direction.

## Current-baseline audit and validation — complete 24 July 2026; final review pending

Required validation ran against the actual reconciled tree at
`c9ce0f501824305f74e84e1c8f1c1b3d4a20477f`, with current local and
remote-tracking `rh` fixed at
`2517eeb0013cdb277dc4815db4b524d7a090d682`. The run began at
`2026-07-24T23:23:25Z` and completed at `2026-07-24T23:32:43Z`.

### Clean environments and fresh no-ignore audit

A new mode-`0700` disposable directory held two isolated CPython 3.12.0
environments:

- the Candidate A environment was installed from the exact committed lock
  using `python -m pip install --no-cache-dir -r requirements.txt`; it used
  pip 23.2.1, contained 93 installed packages, and `python -m pip check`
  reported no broken requirements; and
- the separate audit environment installed exact `pip-audit==2.10.1` from
  public PyPI with `--no-cache-dir`, so the audit tool and its dependencies
  could not alter the Candidate A environment.

The audit used the approved no-ignore policy:

```text
PIP_CONFIG_FILE=/dev/null python -m pip_audit \
  --no-deps --disable-pip -r requirements.txt --format=json \
  --output PRIVATE_RAW_JSON --cache-dir PRIVATE_CACHE
```

It reported exactly seven findings in five packages. The IDs, package
versions, aliases, fix versions, and dispositions match the committed ledger
exactly:

```text
click               8.2.1   PYSEC-2026-2132
pygments             2.19.2  PYSEC-2026-2987
pymdown-extensions   10.16.1 CVE-2026-61632
pymdown-extensions   10.16.1 PYSEC-2026-2999
pytest               8.4.2   PYSEC-2026-1845
vyper                0.4.3   PYSEC-2023-142
vyper                0.4.3   PYSEC-2025-33
```

There is no changed, added, disappeared, severity-drifted, range-drifted, or
fix-version-drifted finding. No `--ignore-vuln` flag was used. The Vyper
findings remain outside Vyper `0.4.3`'s authoritative affected ranges and
remain not-applicable scanner-metadata dispositions.

The fresh raw result is retained under the approved private-evidence controls:

| Retained current-baseline audit | SHA-256 | Owner/group | Mode |
|---|---|---|---|
| `stageb-post-2517eeb-candidate-a-raw-audit-2026-07-24T232325Z.json` | `1cec5232704458776de962c4116fcdf353c4e0d449392c0b4dd7b6305e9a49ce` | `wigglez:staff` | `0600` |

The custody directory remained `wigglez:staff` mode `0700`. Existing private
evidence was not moved, deleted, or rewritten. This new raw audit inherits
the same permitted-use, retention, recheck, and disposal obligations.

### Reconciled validation results

Every pytest command used the exact environment prefix
`ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=.`. The prefix is repeated
verbatim below so that no row depends on an implied environment.

The first current-baseline validation sequence did use explicit private
basetemps beneath the mode-`0700` parent
`/private/tmp/h01-2517eeb.JFtqCn`, but that shared parent was removed only
after the sequence rather than after each command. These commands and results
are retained as historical provenance, not as the final
`EX-H01-PYTEST-01`-compliant results:

| Exact historical current-baseline pytest command | Historical result |
|---|---|
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-2517eeb.JFtqCn/candidate/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-2517eeb.JFtqCn/pytest-gate` | 12 passed in 0.05 s |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-2517eeb.JFtqCn/candidate/bin/python -m pytest -q tests/clock/test_clock_profiles.py --basetemp=/private/tmp/h01-2517eeb.JFtqCn/pytest-clock` | 57 passed in 26.93 s |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-2517eeb.JFtqCn/candidate/bin/python -m pytest -q tests/inventory/test_block_clock_inventory.py --basetemp=/private/tmp/h01-2517eeb.JFtqCn/pytest-inventory` | 60 passed in 25.52 s |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-2517eeb.JFtqCn/candidate/bin/python -m pytest --collect-only -q --basetemp=/private/tmp/h01-2517eeb.JFtqCn/pytest-collect` | 2,734 selected / 2,876 total; 142 deselected in 1.30 s |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-2517eeb.JFtqCn/candidate/bin/python -m pytest -q -p no:cacheprovider --basetemp=/private/tmp/h01-2517eeb.JFtqCn/pytest-full` | 2,734 passed, 142 deselected in 298.71 s |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-2517eeb.JFtqCn/candidate/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-2517eeb.JFtqCn/pytest-final-evidence` | 12 passed in 0.06 s |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-2517eeb.JFtqCn/candidate/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-2517eeb.JFtqCn/pytest-handoff` | 12 passed in 0.05 s |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-final-gate.iC21aP/venv/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-final-gate.iC21aP/pytest` | 12 passed in 0.06 s; this separate parent was mode `0700` and removed after the command |

Because the shared-parent cleanup timing did not establish the strict
one-command/one-parent control, all five required current-baseline results
were replaced on 24 July 2026 from a newly installed clean Candidate A
environment at
`/private/tmp/h01-current-baseline-env.xk2AE2/candidate`. Its enclosing
disposable directory was mode `0700`; installation from the committed lock
again completed cleanly and `python -m pip check` again reported no broken
requirements.

For every replacement command, a distinct task-specific parent was created,
changed to mode `0700`, and verified as `drwx------ 700 wigglez:wheel` before
pytest started. The exact parent was recursively removed immediately after
its one command, and nonexistence was verified before the next command:

| Exact authoritative replacement pytest command | Result and parent disposal |
|---|---|
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-pytest-gate.oA11Lb/basetemp` | 12 passed in 0.05 s; `/private/tmp/h01-pytest-gate.oA11Lb` was mode `0700` and removed after the command |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python -m pytest -q tests/clock/test_clock_profiles.py --basetemp=/private/tmp/h01-pytest-clock.TBpBBS/basetemp` | 57 passed in 28.75 s; `/private/tmp/h01-pytest-clock.TBpBBS` was mode `0700` and removed after the command |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python -m pytest -q tests/inventory/test_block_clock_inventory.py --basetemp=/private/tmp/h01-pytest-inventory.g51Z0P/basetemp` | 60 passed in 26.35 s; `/private/tmp/h01-pytest-inventory.g51Z0P` was mode `0700` and removed after the command |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python -m pytest --collect-only -q --basetemp=/private/tmp/h01-pytest-collect.TWCbRY/basetemp` | 2,734 selected / 2,876 total; 142 deselected in 1.29 s; `/private/tmp/h01-pytest-collect.TWCbRY` was mode `0700` and removed after the command |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python -m pytest -q -p no:cacheprovider --basetemp=/private/tmp/h01-pytest-full.4CFNDY/basetemp` | **2,734 passed, 142 deselected in 295.79 s**; `/private/tmp/h01-pytest-full.4CFNDY` was mode `0700` and removed after the command |

The non-pytest current-baseline results are unchanged:

| Command | Result |
|---|---|
| `/private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python -m pip check` | no broken requirements |
| fresh no-ignore `pip-audit` | seven findings in five packages; exact exception-ledger match |
| `/private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python scripts/check_block_clock_inventory.py --check` | clean; production `100/95/17`, BN `32/100`, indirect `1`, cadence `455`, seconds-unit `58`, timestamp `11/37`, mixed-clock `4`, Vyper paths `92`; non-production test `31/29/5`, cadence test `159` |

After this corrected result section was written, the evidence-dependent gate
was repeated against the complete current evidence bytes with:

```text
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  /private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python \
  -m pytest -q tests/deployment/test_dependency_gate.py \
  --basetemp=/private/tmp/h01-pytest-final-evidence.EpYXs6/basetemp
```

It passed all 12 tests in 0.07 s. Its task-specific parent
`/private/tmp/h01-pytest-final-evidence.EpYXs6` was verified mode `0700`
before the command and removed immediately afterward.

The final byte-level gate then used the exact complete evidence file returned
for review:

```text
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  /private/tmp/h01-current-baseline-env.xk2AE2/candidate/bin/python \
  -m pytest -q tests/deployment/test_dependency_gate.py \
  --basetemp=/private/tmp/h01-pytest-final-bytes.kN1wEt/basetemp
```

It passed all 12 tests. Its distinct task-specific parent
`/private/tmp/h01-pytest-final-bytes.kN1wEt` was verified mode `0700` before
the command and removed immediately afterward.

The first clean-environment replay attempt stopped during package download on
a transient TLS record-layer failure, before any validation ran; that partial
environment was deleted without use. A second empty setup attempt referenced
a nonexistent fixed interpreter path and was likewise deleted without use.
Neither attempt supplied or replaced any validation result.

No failure, skip, warning, compatibility change, collection change, candidate
drift, inventory drift, or scope expansion occurred in the completed
replacement validations.

### Prior reconciled topology and scope — superseded by reachability correction

At the prior validation handoff, repository metadata was:

```text
H-01 reconciled HEAD:
  c9ce0f501824305f74e84e1c8f1c1b3d4a20477f
current rh and origin/rh:
  2517eeb0013cdb277dc4815db4b524d7a090d682
merge base:
  2517eeb0013cdb277dc4815db4b524d7a090d682
ahead / behind:
  19 / 0
```

The exact net delta from current `rh` was:

```text
docs/chains/rh/evidence/dependency-security-gate.md
requirements.in
requirements.txt
tests/deployment/test_dependency_gate.py
```

The three self-hashable payload paths at that checkpoint were byte-identical
to the approved Candidate A payload:

| Prior payload path | SHA-256 |
|---|---|
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `a0d3dcc22d0754229c8226fb55a99c2f17cfb004766285ed67a3c5075a39d948` |

The evidence-file hash for that prior handoff was supplied out of band because
the file cannot contain its own stable hash. The later reachability correction
changes the dependency-gate test and evidence bytes; the section below
supersedes this prior current-state description.

All five bounded exceptions, their 15 August 2026 review, the
`2026-08-31T23:59:59Z` hard expiry, the authorized post-merge
K-02/default-branch refresh, and all custody, retention, and disposal
obligations remain unchanged. No post-merge K-02 refresh was attempted because
H-01 has not been merged into `rh`. No merge into `rh`, push, deployment,
signing, verification submission, alert mutation, private-evidence deletion,
or other production/live action occurred.

At that checkpoint H-01 was reconciled and validation-complete, but not yet
merge-ready. The subsequent reviewer finding reopened the test-policy and
evidence scope.

## Reviewer-gate reachability correction — 24 July 2026; final review pending

The final independent review found that
`test_exception_reachability_controls_remain_true` did not mechanically
enforce the full approved invalidation surface for
`EX-H01-CLICK-01`, `EX-H01-PYGMENTS-01`,
`EX-H01-PYMDOWN-SNIPPETS-01`, and `EX-H01-PYMDOWN-B64-01`. The old check
looked for literal `click.edit()` only in three existing scripts and looked
for Pymdown/Pygments tokens only under `scripts/`, `config/`, and
`contracts/`. It could therefore miss an aliased Click import, a new Click
surface, a root or nested MkDocs configuration, or a Pygments
Archetype/`AdlLexer` activation elsewhere.

### Smallest sufficient gate correction

Only `tests/deployment/test_dependency_gate.py` and this evidence record were
changed. The correction:

- walks all repository Python and activation-capable configuration suffixes
  (`.py`, `.cfg`, `.ini`, `.json`, `.toml`, `.yaml`, and `.yml`) from the
  repository root;
- prunes version-control, cache, generated-output, private, dependency-vendor,
  and virtual-environment directories, and skips symlinks;
- AST-parses Python files, resolves ordinary import aliases, fails on
  `click.edit` references/imports, and permits Click imports only in the three
  already approved files `scripts/console.py`, `scripts/migrate.py`, and
  `scripts/verify.py`;
- detects direct or aliased Pygments Archetype/`AdlLexer` imports and
  references, plus `get_lexer_by_name("adl")` or
  `get_lexer_by_name("archetype")`; and
- detects `pymdownx.snippets` and `pymdownx.b64` in root or nested
  configuration files and direct Pygments Archetype/`AdlLexer` configuration
  selection.

This is a local helper inside the existing dependency-gate module, not a new
repository-wide lint framework. No dependency, exception term, production
code, policy, CI, script, compiler input, contract, ABI, or artifact changed.

Four mutation cases prove that the same assertion used by the live gate fails
for:

1. root `mkdocs.yml` enabling `pymdownx.snippets`;
2. root `mkdocs.yml` enabling `pymdownx.b64`;
3. `from click import edit as launch_editor` in a new tooling path; and
4. a direct aliased `AdlLexer` import in a new tooling path.

The corrected gate contains 16 cases and has SHA-256:

```text
d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa
```

An initial corrected-gate replay passed 16 cases before the explicit
three-file Click allowlist was added. The final implementation with that
additional fail-closed control was then replayed and is the result below.

### Clean Candidate A environment and fresh security reconciliation

A new mode-`0700` disposable root,
`/private/tmp/h01-reachability-validation.xHpsMn`, held separate Candidate A
and audit environments. CPython `3.12.0` / pip `23.2.1` installed the exact
unchanged committed lock from public PyPI with:

```text
PIP_CONFIG_FILE=/dev/null
PIP_INDEX_URL=https://pypi.org/simple
PIP_EXTRA_INDEX_URL=
PIP_NO_CACHE_DIR=1
/private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python \
  -m pip install --no-cache-dir -r requirements.txt
```

Installation completed cleanly and
`/private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pip check`
reported no broken requirements.

The separate audit environment installed exact `pip-audit==2.10.1` from
public PyPI without cache. The approved no-ignore command was:

```text
PIP_CONFIG_FILE=/dev/null \
  /private/tmp/h01-reachability-validation.xHpsMn/audit/bin/python \
  -m pip_audit --no-deps --disable-pip -r requirements.txt --format=json \
  --output /Users/wigglez/dev/ripe-protocol-h1-private-evidence/stageb-reachability-correction-candidate-a-raw-audit-2026-07-25T001306Z.json \
  --cache-dir=/private/tmp/h01-reachability-validation.xHpsMn/audit-cache
```

Its expected nonzero finding exit reported exactly seven findings in five
packages, with no added, removed, version-drifted, range-drifted, or
disposition-drifted row:

```text
click               8.2.1   PYSEC-2026-2132
pygments             2.19.2  PYSEC-2026-2987
pymdown-extensions   10.16.1 CVE-2026-61632
pymdown-extensions   10.16.1 PYSEC-2026-2999
pytest               8.4.2   PYSEC-2026-1845
vyper                0.4.3   PYSEC-2023-142
vyper                0.4.3   PYSEC-2025-33
```

The raw audit is retained mode `0600`, owner/group `wigglez:staff`, SHA-256:

```text
2f655db221ffed938627e3da5d150ecc873ea0acde7b76a00e84ec670b120268
```

The two Vyper findings remain outside Vyper `0.4.3`'s authoritative affected
ranges. No ignore, fix, suppression, alert mutation, or upstream report was
used.

The exact approved K-02 read-only query ran at
`2026-07-25T00:12:49Z` without `gh auth status`:

```text
gh api --method GET --paginate --slurp \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  '/repos/Ripe-Foundation/ripe-protocol/dependabot/alerts?state=open&per_page=100'
```

It returned the unchanged default-branch ledger: 13 open alerts, 6 high, 6
medium, 1 low, numbers
`13,14,15,16,18,19,21,22,23,24,25,26,27`. The raw response and approved
sanitized projection are byte-identical to the prior retained snapshots:

| Fresh K-02 record | SHA-256 | Owner/group | Mode |
|---|---|---|---|
| `dependabot-open-2026-07-25T001249Z-raw.json` | `52eccab5e38769070f5310b753f018030587b673cc2637105983ba670bfe2f0a` | `wigglez:staff` | `0600` |
| `dependabot-open-2026-07-25T001249Z-sanitized.json` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `wigglez:staff` | `0600` |

The first refreshed sanitized projection used a broader nested schema. Before
handoff it was regenerated from the retained raw bytes with the existing
approved minimized projection, yielding the exact prior hash above. The
replacement temporarily inherited group `wheel` from its private temporary
file; the immediate custody check corrected it to `wigglez:staff` while mode
remained `0600`. No pre-existing retained file changed.

After the refresh, the H-01 private directory remained
`wigglez:staff` mode `0700`. All 28 retained files were rehashed and verified
`wigglez:staff` mode `0600`; the sorted private path/hash inventory contained
28 rows and had SHA-256
`1737af25d7c7c8fa7de810af5f7a1e525f9f5feb4c0d8d709d8c82b899373a6b`.
The inventory itself remained outside the repository and was used only for
this custody integrity check.

### Fresh validation commands and results

Every pytest command used exact prefix
`ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=.` and a distinct
task-specific mode-`0700` parent with an explicit private `--basetemp`.
Every named parent was removed immediately after its command and verified
absent:

| Exact command | Result and parent disposal |
|---|---|
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-reachability-gate2.kprpCe/basetemp` | corrected gate 16 passed in 1.46 s; parent removed |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pytest -q tests/clock/test_clock_profiles.py --basetemp=/private/tmp/h01-reachability-clock.tafqQr/basetemp` | S1 57 passed in 27.35 s; parent removed |
| `PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python scripts/check_block_clock_inventory.py --check` | clean; production `100/95/17`, BN `32/100`, indirect `1`, cadence `455`, seconds-unit `58`, timestamp `11/37`, mixed-clock `4`, Vyper paths `92`; non-production test `31/29/5`, cadence test `159` |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pytest -q tests/inventory/test_block_clock_inventory.py --basetemp=/private/tmp/h01-reachability-inventory.uvJK9G/basetemp` | S2 60 passed in 25.22 s; parent removed |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pytest -q tests/core/lootbox/test_underscore_rewards.py --basetemp=/private/tmp/h01-reachability-lootbox.7ijAth/basetemp` | S3-targeted 59 passed in 29.29 s; parent removed |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pytest -q tests/config/test_switchboard_charlie.py --basetemp=/private/tmp/h01-reachability-switchboard.ImcEWi/basetemp` | S3-targeted 91 passed in 35.66 s; parent removed |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pytest --collect-only -q --basetemp=/private/tmp/h01-reachability-collect.RQLlzk/basetemp` | 2,738 selected / 2,880 total; 142 deselected in 1.28 s; parent removed |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python -m pytest -q -p no:cacheprovider --basetemp=/private/tmp/h01-reachability-full.bMHpGC/basetemp` | **2,738 passed, 142 deselected in 298.10 s**; parent removed |

The four-case increase from 2,734 to 2,738 is exactly the two parameterized
Pymdown mutation cases, the aliased Click import case, and the direct
`AdlLexer` import case. There was no skip, xfail, warning suppression,
compatibility failure, unrelated collection change, inventory change, or
artifact-relevant source/input change.

The final byte-level dependency-gate command against the complete corrected
evidence returned for review was:

```text
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  /private/tmp/h01-reachability-validation.xHpsMn/candidate/bin/python \
  -m pytest -q tests/deployment/test_dependency_gate.py \
  --basetemp=/private/tmp/h01-reachability-final-evidence.mPr5Tk/basetemp
```

It passed all 16 tests. The distinct task-specific parent
`/private/tmp/h01-reachability-final-evidence.mPr5Tk` was verified mode
`0700` before the command and removed immediately afterward.

### Corrected hashes, scope, and review stop

The corrected self-hashable H-01 files are:

| Current H-01 path | SHA-256 |
|---|---|
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa` |

The requirement and lock hashes are unchanged. The test hash changed only for
the reviewed reachability correction and four mutation cases. The evidence
hash is supplied out of band because the file cannot contain its own stable
hash.

The repository remains based on reconciliation commit
`c9ce0f501824305f74e84e1c8f1c1b3d4a20477f`, whose second parent is exact
reviewed baseline `2517eeb0013cdb277dc4815db4b524d7a090d682`.

### Post-validation remote-baseline freshness stop

The final scope check discovered that the remote had advanced after the
reviewed `2517eeb` baseline. Read-only `git ls-remote` confirmed authoritative
remote `rh` at:

```text
03c07f01dda03a5529c602aafbfe5545ae86df69
merge: integrate Track 8 M0 evidence
```

The complete `2517eeb..03c07f0` remote delta is four commits and adds only:

```text
docs/chains/rh/stock-token-m0-evidence.md
docs/chains/rh/stock-token-m0-raw-evidence.json
```

The delta is 12,492 inserted lines of Track 8 M0 evidence and changes no H-01
owned path, requirement, lock, dependency, Python test, compiler input,
contract, ABI, artifact, deployment script, or configuration. Nevertheless,
the approved freshness policy treats a reconciled-`rh` commit change as a
freshness event. No non-overlap inference can silently carry merge readiness
to new baseline bytes.

Current authoritative topology is:

```text
H-01 HEAD:
  c9ce0f501824305f74e84e1c8f1c1b3d4a20477f
authoritative remote/origin rh:
  03c07f01dda03a5529c602aafbfe5545ae86df69
merge base:
  2517eeb0013cdb277dc4815db4b524d7a090d682
ahead / behind relative to origin/rh:
  19 / 4
local rh:
  706975bec0e608d2d9705a8331f03aad3ef7bf7f
```

Local `rh` and `origin/rh` are themselves one commit ahead of and one commit
behind each other; local `rh` is therefore not substituted for the
authoritative remote baseline. The H-01 branch remains unpublished.

The merge-base-only H-01 change set remains the four authorized files:

```text
docs/chains/rh/evidence/dependency-security-gate.md
requirements.in
requirements.txt
tests/deployment/test_dependency_gate.py
```

The actual net tree delta against current `origin/rh` additionally shows the
two Track 8 files as absent because H-01 has not reconciled their integration.
Therefore the required exact-four-file net-scope condition is not currently
satisfied.

The worktree has exactly two unstaged changes: the gate correction and this
evidence update. No commit, merge, push, deployment, signing, verification
submission, alert mutation, private-evidence deletion, or other
production/live action occurred.

All five bounded exceptions remain unchanged, including the 15 August 2026
review, `2026-08-31T23:59:59Z` hard expiry, post-merge K-02/default-branch
refresh, exception review, custody, retention, and separately authorized
disposal obligations. The prior reviewer approval does not cover these new
test/evidence bytes. The just-completed clean install, gate, S1/S2/S3,
collection, full suite, no-ignore audit, K-02, and custody checks remain exact
evidence for `2517eeb`, but became stale for merge readiness when the remote
baseline advancement was detected. H-01 is stopped before reconciliation.
Owner direction is required to merge exact current `origin/rh` into the H-01
branch and rerun the freshness-required checks; this record does not authorize
that merge.

After recording this freshness stop, a new clean environment installed the
unchanged Candidate A lock and passed `pip check`. The final offline
dependency gate against the exact stopped-state evidence bytes returned for
review used:

```text
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  /private/tmp/h01-reachability-stop-final.Ba2K76/candidate/bin/python \
  -m pytest -q tests/deployment/test_dependency_gate.py \
  --basetemp=/private/tmp/h01-reachability-stop-gate.IC0ALt/basetemp
```

It passed all 16 cases. The task-specific parent
`/private/tmp/h01-reachability-stop-gate.IC0ALt` was verified mode `0700`
before the command and removed immediately afterward. This byte-level offline
gate confirms the corrected scanner and stopped-state evidence; it does not
clear the new-baseline freshness stop.

## 24 July 2026: exact `origin/rh` `03c07f0` reconciliation and validation

This section records the final current state. The immediately preceding
`03c07f0` freshness stop is retained as historical checkpoint evidence only:
the owner subsequently authorized reconciliation with that exact remote
commit, and the stop was cleared by the merge and complete replay below.
Earlier stopped, pending, or approved statements remain accurate only for the
specific historical bytes and baseline they name.

### Authority, preflight, and merge

Read-only `git ls-remote origin rh` confirmed exact authority:

```text
03c07f01dda03a5529c602aafbfe5545ae86df69	refs/heads/rh
```

The complete `2517eeb0013cdb277dc4815db4b524d7a090d682..03c07f0`
incoming delta was inspected before the merge and contained exactly:

```text
docs/chains/rh/stock-token-m0-evidence.md
docs/chains/rh/stock-token-m0-raw-evidence.json
```

It contained 12,492 inserted lines and no other path. It did not overlap the
two then-unstaged H-01 paths or any H-01-owned file. It changed no requirement,
lock, dependency, Python test, compiler input, artifact, ABI, contract,
deployment script, or configuration. A conflict-checking virtual merge
completed and produced tree
`898a37126905446665896baf86d8bafc27ee7ce8`. The authorized exact merge was:

```text
git merge --no-ff --no-edit 03c07f01dda03a5529c602aafbfe5545ae86df69
```

It completed without conflict at:

```text
merge commit:
  678034e4a8ba469f65485748bb7e612dc343a91a
first parent:
  c9ce0f501824305f74e84e1c8f1c1b3d4a20477f
second parent:
  03c07f01dda03a5529c602aafbfe5545ae86df69
commit time:
  2026-07-24T18:39:07-06:00
```

The two merged Track 8 worktree blobs exactly matched the authoritative
remote commit:

```text
docs/chains/rh/stock-token-m0-evidence.md
  b680e03d6b1ed687491f55fbec41d7eb270e613d
docs/chains/rh/stock-token-m0-raw-evidence.json
  c55e5c25c15ef15190161193ea6f04212e8ff605
```

An initial post-merge verification loop mistakenly assigned zsh's reserved
`path` array, which made its child `git` commands unavailable and its printed
comparison unusable. That output was discarded. The loop made no repository
or private-evidence change; independent commands with a non-reserved variable
then established all hashes, topology, and scope values recorded here.

Actual reconciled topology is:

```text
H-01 reconciled HEAD:
  678034e4a8ba469f65485748bb7e612dc343a91a
authoritative baseline and merge base:
  03c07f01dda03a5529c602aafbfe5545ae86df69
ahead / behind relative to that exact baseline:
  20 / 0
```

The exact net worktree delta against `03c07f0`, including the two uncommitted
review corrections, is:

```text
A  docs/chains/rh/evidence/dependency-security-gate.md
M  requirements.in
M  requirements.txt
A  tests/deployment/test_dependency_gate.py
```

No other net path exists.

### Clean Candidate A and audit environments

A new disposable root
`/private/tmp/h01-03c07f0-validation.l1mMSg` was created mode `0700`,
owner/group `wigglez:wheel`, using CPython `3.12.0` and pip `23.2.1`.
Candidate A was installed from the unchanged committed lock with the complete
prefix and command:

```text
PIP_CONFIG_FILE=/dev/null \
PIP_INDEX_URL=https://pypi.org/simple \
PIP_EXTRA_INDEX_URL= \
PIP_NO_CACHE_DIR=1 \
  /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python \
  -m pip install --no-cache-dir -r requirements.txt
```

Installation completed successfully from public PyPI with 93 packages. The
exact post-install check:

```text
/private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pip check
```

reported `No broken requirements found`.

The same root held a separate mode-`0700` audit environment and
mode-`0700` audit cache. Exact `pip-audit==2.10.1` was installed from public
PyPI without cache using:

```text
PIP_CONFIG_FILE=/dev/null \
PIP_INDEX_URL=https://pypi.org/simple \
PIP_EXTRA_INDEX_URL= \
PIP_NO_CACHE_DIR=1 \
  /private/tmp/h01-03c07f0-validation.l1mMSg/audit/bin/python \
  -m pip install --no-cache-dir --index-url https://pypi.org/simple \
  pip-audit==2.10.1
```

The audit environment passed `pip check` and reported
`pip-audit 2.10.1`. The approved raw no-ignore audit command was:

```text
PIP_CONFIG_FILE=/dev/null \
  /private/tmp/h01-03c07f0-validation.l1mMSg/audit/bin/python \
  -m pip_audit --no-deps --disable-pip -r requirements.txt --format=json \
  --output /Users/wigglez/dev/ripe-protocol-h1-private-evidence/stageb-post-03c07f0-reachability-candidate-a-raw-audit-2026-07-25T005409Z.json \
  --cache-dir=/private/tmp/h01-03c07f0-validation.l1mMSg/audit-cache
```

Its expected finding exit was `1`: seven findings in five packages. A shell
wrapper then attempted to store that exit in zsh's reserved read-only
`status` variable and stopped before its postprocessing commands. The audit
itself had completed and written the full result. Separate read-only checks
confirmed the retained file, its mode, hash, and exact ledger:

```text
click               8.2.1   PYSEC-2026-2132
pygments             2.19.2  PYSEC-2026-2987
pymdown-extensions   10.16.1 CVE-2026-61632
pymdown-extensions   10.16.1 PYSEC-2026-2999
pytest               8.4.2   PYSEC-2026-1845
vyper                0.4.3   PYSEC-2023-142
vyper                0.4.3   PYSEC-2025-33
```

Compared with the preceding no-ignore audit, only the order of the Pygments
and pytest advisory-alias arrays changed. Finding IDs, packages, versions,
aliases as sets, fix versions, applicability, and all five exception
dispositions remained exact. Both Vyper findings remain outside Vyper
`0.4.3`'s authoritative affected-version ranges. No ignore flag, suppression,
alert mutation, or upstream report was used.

The retained raw audit file is owner/group `wigglez:staff`, mode `0600`,
SHA-256:

```text
28733404ee019ff13813df7be6b323374925a057e1428b9d839592c481acb6d4
```

### Fresh K-02 and custody reconciliation

Before access, the approved private directory was verified
`wigglez:staff`, mode `0700`. No authentication state was printed. At
approximately `2026-07-25T00:52:48Z`, the exact approved read-only K-02 query
was:

```text
gh api --method GET --paginate --slurp \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  '/repos/Ripe-Foundation/ripe-protocol/dependabot/alerts?state=open&per_page=100'
```

The approved minimized projection was regenerated directly in the private
directory with mode `0600`:

```text
jq '[.[][] | {number, state, severity: .security_advisory.severity,
package: .dependency.package.name, manifest: .dependency.manifest_path,
scope: .dependency.scope, ghsa: .security_advisory.ghsa_id,
cve: .security_advisory.cve_id,
vulnerable_range: .security_vulnerability.vulnerable_version_range,
first_patched_version:
.security_vulnerability.first_patched_version.identifier,
published_at: .security_advisory.published_at,
updated_at: .security_advisory.updated_at, advisory_url: null}]
| sort_by(.number)'
```

The result remained 13 open alerts, 6 high, 6 medium, and 1 low, numbers
`13,14,15,16,18,19,21,22,23,24,25,26,27`. The sanitized projection was
byte-identical to every prior approved projection. The raw response changed
only in time-varying EPSS `percentage`/`percentile` fields for alerts
`13,15,16,26,27`; a path-and-value-hash comparison found no other scalar
change. Thus no alert identity, package, state, severity, affected range,
first patched version, publication/update time, or disposition changed.

| Fresh K-02 record | SHA-256 | Owner/group | Mode |
|---|---|---|---|
| `dependabot-open-2026-07-25T005248Z-raw.json` | `a5d870192e7c2688bd81c4f5de24ef35f93fc2a7d86039169ded1025148ddbd0` | `wigglez:staff` | `0600` |
| `dependabot-open-2026-07-25T005248Z-sanitized.json` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `wigglez:staff` | `0600` |

After the K-02 and audit refresh, the private directory remained
`wigglez:staff`, mode `0700`. All 31 retained files were rehashed and verified
owner/group `wigglez:staff`, mode `0600`; there were zero custody mismatches.
The sorted private path/hash inventory contained 31 rows and had SHA-256:

```text
8700cf1125742f35202cf9575cf89cab83e30555298cda471edb8a56c205cacf
```

That inventory was retained only at
`/private/tmp/h01-03c07f0-custody-inventory.D7xl6D` during reconciliation and
removed after this record was updated. No retained private evidence was moved,
renamed, deleted, or printed. Retention continues through the later of the
authorized post-merge default-branch K-02 refresh and final disposition of all
five exceptions; disposal still requires separate explicit owner instruction
and a recorded hash/mode/custody recheck.

### Current-baseline validation commands and results

Every pytest invocation used the exact complete prefix
`ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=.` and an explicit private
`--basetemp` under a distinct task-specific parent. Each parent was verified
mode `0700` before its command and removed immediately afterward:

| Exact command | Result |
|---|---|
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-03c07f0-gate.63FEkH/basetemp` | corrected dependency gate: 16 passed in 1.43 s; parent removed and absent |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest -q tests/clock/test_clock_profiles.py --basetemp=/private/tmp/h01-03c07f0-s1.56VZ5R/basetemp` | S1 clock profiles: 57 passed in 26.97 s; parent removed and absent |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest -q tests/inventory/test_block_clock_inventory.py --basetemp=/private/tmp/h01-03c07f0-s2-inventory.cNgDAS/basetemp` | S2 inventory tests: 60 passed in 25.26 s; parent removed and absent |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest -q tests/core/lootbox/test_underscore_rewards.py --basetemp=/private/tmp/h01-03c07f0-s3-lootbox.No9N5Z/basetemp` | S3 Lootbox target: 59 passed in 29.17 s; parent removed and absent |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest -q tests/config/test_switchboard_charlie.py --basetemp=/private/tmp/h01-03c07f0-s3-switchboard.RuiyxM/basetemp` | S3 Switchboard target: 91 passed in 35.89 s; parent removed and absent |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest --collect-only -q --basetemp=/private/tmp/h01-03c07f0-collection.SgvzHt/basetemp` | 2,738/2,880 collected, 142 deselected in 1.31 s; parent removed and absent |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest -q -p no:cacheprovider --basetemp=/private/tmp/h01-03c07f0-full.uE7R9H/basetemp` | complete serial suite: 2,738 passed, 142 deselected in 302.35 s; parent removed and absent |
| `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=/private/tmp/h01-03c07f0-final-gate.kx59HD/basetemp` | final byte-level dependency gate after this complete evidence update: 16 passed; parent removed and absent |

The checked S2 inventory command was:

```text
PYTHONPATH=. \
  /private/tmp/h01-03c07f0-validation.l1mMSg/candidate/bin/python \
  scripts/check_block_clock_inventory.py --check
```

It returned:

```text
CLOCK_INVENTORY_OK schema=1 production_occurrences=100 production_lines=95 production_files=17 bn_ids=32 bn_records=100 indirect_ids=1 cadence_candidates=455 seconds_unit_candidates=58 timestamp_ids=11 timestamp_occurrences=37 mixed_clock_functions=4 vyper_paths=92
CLOCK_INVENTORY_NONPROD mock=0/0/0 testing=0/0/0 test=31/29/5
CLOCK_INVENTORY_NONPROD_CADENCE mock=0 testing=0 test=159
```

The validation root, Candidate A environment, separate audit environment,
audit cache, and final-gate parent were removed after the final dependency
gate and verified absent. The `ETHERSCAN_API_KEY` value was a documented
non-secret collection placeholder only; no explorer or other production
service was called by pytest.

### Current hashes, obligations, and reviewer stop

The current self-hashable H-01 payload files are:

| Current H-01 path | SHA-256 |
|---|---|
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa` |

The evidence hash is intentionally supplied out of band because this file
cannot contain its own stable hash. `git diff --check` passes. The worktree
contains exactly two unstaged changes: the corrected dependency gate and this
complete evidence amendment. Requirements and lock bytes are unchanged from
the reviewed Candidate A payload.

All five bounded exceptions remain exactly as approved. Their scheduled review
is 15 August 2026 and their hard expiry is
`2026-08-31T23:59:59Z`; expiry blocks rehearsal. After owner integration, the
authorized default-branch K-02 refresh must distinguish candidate remediation
from authoritative alert closure and reconcile the expected post-observation
residual alerts with the exception ledger. Exception review and the recorded
custody, retention, hash/mode recheck, and separately authorized disposal
obligations remain mandatory.

At the completion of this pre-approval section, the reconciled branch and
complete evidence were stopped at the mandatory final independent
merge-readiness review. No final reviewer approval was claimed here. The next
section records the later exact-byte approval and the owner's narrow
authorization to commit and publish the H-01 branch. Neither approval
authorizes merge into `rh`, Dependabot mutation, deployment, signing,
verification submission, private-evidence deletion, or another
production/live action.

## 24 July 2026: final independent merge-readiness approval

The independent security/Track 6 reviewer approved H-01 Candidate A merge
readiness against this exact identity:

```text
authoritative baseline:
  03c07f01dda03a5529c602aafbfe5545ae86df69
reconciled HEAD:
  678034e4a8ba469f65485748bb7e612dc343a91a
complete pre-approval evidence SHA-256:
  8217348b2e0309597a33684ecba445334da0344109dae19e826624b5b387ac79
requirements.in SHA-256:
  2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d
requirements.txt SHA-256:
  d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce
tests/deployment/test_dependency_gate.py SHA-256:
  d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa
```

The approval covers the exact four-file Candidate A payload and all five
previously owner-approved bounded exceptions. It expressly retains the
15 August 2026 review, `2026-08-31T23:59:59Z` hard expiry, compensating
controls, invalidation triggers, custody requirements, and post-merge
obligations. No dependency, exception, policy, test logic, validation
conclusion, requirement, or lock byte changed to record this approval. The
addition necessarily changes only this evidence file's out-of-band hash.

After this approval record was added, `git diff --check` passed. A newly
created mode-`0700` disposable Candidate A root,
`/private/tmp/h01-final-approval-validation.CzGWIx`, installed the exact
committed lock from public PyPI with:

```text
PIP_CONFIG_FILE=/dev/null \
PIP_INDEX_URL=https://pypi.org/simple \
PIP_EXTRA_INDEX_URL= \
PIP_NO_CACHE_DIR=1 \
  /private/tmp/h01-final-approval-validation.CzGWIx/candidate/bin/python \
  -m pip install --no-cache-dir -r requirements.txt
```

The environment used CPython `3.12.0` and pip `23.2.1`; installation
completed cleanly and `python -m pip check` reported no broken requirements.
The exact approval-record gate replay used the documented non-secret
collection placeholder and a fresh task-specific mode-`0700` parent:

```text
ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=. \
  /private/tmp/h01-final-approval-validation.CzGWIx/candidate/bin/python \
  -m pytest -q tests/deployment/test_dependency_gate.py \
  --basetemp=/private/tmp/h01-final-approval-gate.usiaky/basetemp
```

It passed all 16 cases. The basetemp parent and complete disposable Candidate A
root were removed immediately afterward and verified absent. No private
evidence was accessed or deleted.

The owner authorized committing exactly this evidence file and
`tests/deployment/test_dependency_gate.py`, then publishing only
`rh-track-7-h1-dependency-security`. The owner/integration agent retains the
merge. This final approval does not authorize merge into `rh`, Dependabot
mutation, deployment, signing, verification submission, private-evidence
deletion, or any other production action.

## 24 July 2026: authorized post-integration K-02/default-branch refresh

### Integrated identity and scope

Read-only local and remote checks confirmed both the `rh` worktree and
`origin/rh` at:

```text
575d47b82055b42da2bddf1535d8076cd7cf4c63
merge: integrate Track 7 H-01 dependency security
```

The merge parents are:

```text
first parent / authoritative reviewed baseline:
  03c07f01dda03a5529c602aafbfe5545ae86df69
second parent / final published H-01 commit:
  3b46be0a3af3355661b4a9f55b6a4c2295a39da7
```

The final H-01 commit is an ancestor of integrated `rh`. The first-parent
integration delta is exactly:

```text
A  docs/chains/rh/evidence/dependency-security-gate.md
M  requirements.in
M  requirements.txt
A  tests/deployment/test_dependency_gate.py
```

The integrated evidence file matched its reviewed final pre-refresh SHA-256
`d8e33871b2676ebdf39da1b6176fe9ecb009a46c6d35730f68ef103343d26c2c`
before this amendment. The `rh` worktree already contained unrelated,
pre-existing Track 6 S5 planning changes at
`docs/chains/rh/track-6-s5-ledger-guard.md` and
`docs/chains/rh/track-6-s5-checkpoint-0-owner-decision-packet.md`; they were
not read, modified, staged, or otherwise included in H-01 work. A concurrent
untracked `contracts/data/test.md` appeared during the final scope check; it
was likewise not read, modified, staged, or attributed to H-01.

### Exact GitHub-observed default-branch state

Before the query, the remote repository identity was verified as
`Ripe-Foundation/ripe-protocol`, and read-only `git ls-remote` confirmed
`origin/rh` remained exact `575d47b`. Authentication state, tokens, response
headers, and unrelated repository/account data were not printed. At
`2026-07-25T01:20:02Z`, the approved K-02 channel ran only this alert-list
request:

```text
gh api --method GET --paginate --slurp \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  '/repos/Ripe-Foundation/ripe-protocol/dependabot/alerts?state=open&per_page=100'
```

GitHub returned 13 alerts, all with `state=open`: 6 high, 6 medium, and 1 low.
The complete sanitized observed ledger is:

| Alert | State | Severity | Package | GitHub vulnerable range | First patched version |
|---:|---|---|---|---|---|
| 13 | open | high | `urllib3` | `>= 1.24, < 2.6.0` | `2.6.0` |
| 14 | open | high | `urllib3` | `>= 1.0, < 2.6.0` | `2.6.0` |
| 15 | open | medium | `cbor2` | `>= 3.0.0, < 5.8.0` | `5.8.0` |
| 16 | open | high | `urllib3` | `>= 1.22, < 2.6.3` | `2.6.3` |
| 18 | open | high | `wheel` | `>= 0.40.0, <= 0.46.1` | `0.46.2` |
| 19 | open | high | `cbor2` | `<= 5.8.0` | `5.9.0` |
| 21 | open | medium | `requests` | `< 2.33.0` | `2.33.0` |
| 22 | open | low | `Pygments` | `< 2.20.0` | `2.20.0` |
| 23 | open | medium | `pytest` | `< 9.0.3` | `9.0.3` |
| 24 | open | medium | `python-dotenv` | `< 1.2.2` | `1.2.2` |
| 25 | open | high | `urllib3` | `>= 1.23, < 2.7.0` | `2.7.0` |
| 26 | open | medium | `idna` | `< 3.15` | `3.15` |
| 27 | open | medium | `pymdown-extensions` | `>= 10.0.1, <= 10.21.2` | `10.21.3` |

The alert-number set, count, severity split, package identities, ranges, and
first-patched versions are unchanged from the immediately preceding K-02
refresh. The raw and approved minimized sanitized bytes are also byte-identical
to that refresh:

| Retained post-integration K-02 file | SHA-256 | Owner/group | Mode |
|---|---|---|---|
| `dependabot-open-post-integration-2026-07-25T012002Z-raw.json` | `a5d870192e7c2688bd81c4f5de24ef35f93fc2a7d86039169ded1025148ddbd0` | `wigglez:staff` | `0600` |
| `dependabot-open-post-integration-2026-07-25T012002Z-sanitized.json` | `d2dd2d89acb63de901e164c3c7d69f402c04bc38da9a803fe9674734ab404b06` | `wigglez:staff` | `0600` |

This is the authoritative state observed from GitHub at the query time. No
alert is reported as resolved, closed, dismissed, fixed, or remediated in this
record. Candidate A's integrated pins are outside the recorded vulnerable
ranges for alerts `13,14,15,16,18,19,21,24,25,26`, but that static
candidate-lock comparison is not GitHub closure and does not change the 13
observed `open` states. Alerts `22,23,27` remain within the integrated pins and
remain exception-governed. GitHub may re-observe the manifest later; any later
state requires a new authorized observation and may not be inferred here.

### Exceptions and custody after the refresh

All five bounded exceptions survive unchanged:

- `EX-H01-CLICK-01`
- `EX-H01-PYTEST-01`
- `EX-H01-PYGMENTS-01`
- `EX-H01-PYMDOWN-SNIPPETS-01`
- `EX-H01-PYMDOWN-B64-01`

Alert `22` maps to the Pygments exception, alert `23` maps to the pytest
exception, and alert `27` remains governed by both bounded Pymdown reachability
exceptions. The Click exception has no separate alert in this K-02 response.
Every exception retains its exact threat model, owner, scope, compensating
controls, invalidation/recheck triggers, 15 August 2026 review, and
`2026-08-31T23:59:59Z` hard expiry. Expiry continues to block rehearsal.

Before K-02 access, the private-evidence directory was verified
`wigglez:staff`, mode `0700`, with 31 retained files, all
`wigglez:staff` mode `0600` and zero custody mismatches. The query and approved
projection added only the two retained files named above. Afterward, all 33
retained files were rehashed and rechecked with zero owner/group/mode
mismatches; the directory remained `wigglez:staff` mode `0700`. The sorted
33-row private path/hash inventory had SHA-256:

```text
1a192540fbaff78f7579a8db1fabe73b3cef4eb999a32fea927c969100703b5f
```

The temporary inventory at
`/private/tmp/h01-post-integration-custody-inventory.nYE4lf` was removed after
this sanitized record was updated. No retained private evidence was printed,
moved, renamed, deleted, or copied elsewhere.

Completion of the post-integration refresh satisfies that retention event but
does not authorize disposal: retention continues until final disposition of
all five exceptions, which is later than this refresh. Permitted use remains
limited to H-01 security evidence and independent review. Disposal remains
blocked absent separate explicit owner instruction, exact pre-disposal
path/hash/mode verification, the approved per-file method, and a committed
sanitized disposal record.

### Evidence-only review handoff

This refresh changed only
`docs/chains/rh/evidence/dependency-security-gate.md`. It did not change
requirements, the compiled lock, the dependency gate, any exception or policy,
tests, scripts, contracts, artifacts, ABIs, or another repository file.
`git diff --check` passes. No audit beyond the authorized K-02 alert-list
refresh was run, and no alert endpoint was mutated.

The current integrated payload hashes remain:

| Integrated H-01 path | SHA-256 |
|---|---|
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa` |

The updated evidence hash is supplied out of band because this file cannot
contain its own stable hash. This evidence-only amendment remains uncommitted
for final review. No commit, push, merge, Dependabot mutation, deployment,
signing, verification submission, private-evidence deletion/relocation, or
other production action was performed.

## 26 July 2026: three-package exception-retirement implementation — Gate 1 validation

This section is the current implementation record. Historical Candidate A,
review, integration, K-02, and exception records above remain unchanged.

### Authority, baseline, isolation, and scope

The owner authorized exactly:

```text
click==8.3.3
Pygments==2.20.0
pymdown-extensions==10.21.3
```

Exact pytest `8.4.2`, Titanoboa `0.2.7`, Vyper `0.4.3`, and every other
direct and transitive dependency are held. The implementation identities are:

```text
baseline commit:
  c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d
baseline tree:
  b2c2358f565e27ad6a5c787a9a0d1396af513076
branch:
  rh-track-7-h1-exception-retirement-implementation
worktree:
  /Users/wigglez/dev/ripe-protocol-track-7-h1-exception-retirement-implementation
```

Before worktree creation, the integration worktree was clean and local `rh`,
cached `origin/rh`, and live `origin/rh` all equaled the exact baseline. The
distinct implementation branch and worktree did not exist locally or
remotely. The preserved feasibility and preflight evidence branches and
worktrees were not reused, modified, moved, deleted, pruned, or treated as
implementation candidates.

The immutable feasibility report remains byte-identical at SHA-256:

```text
9b9ad56d73d8a7418dcc0e452b3affb927979ce53fd90fcd5f84f9b9dfcfbfec
```

### Deterministic resolver and exact lock delta

Two independent mode-`0700` resolver environments used the same exact
CPython `3.12.0` seed, SHA-256
`d23fa2c326127c9590d097603f105d69e68774968f46246fc7a8a80103600765`,
with pip `23.2.1`, pip-tools `7.4.1`, build `1.5.0`, Click `8.4.2`,
packaging `26.2`, pyproject-hooks `1.2.0`, setuptools `83.0.0`, and wheel
`0.47.0`. Each used its own frozen-lock seed and private resolver cache, public
`https://pypi.org/simple` only, no extra/private index, and the approved
truthful command-header form.

Both candidate inputs are byte-identical at:

```text
1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9
```

Both generated locks are byte-identical at:

```text
214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010
```

The final-path compile reproduced the same bytes. Mechanical normalized-pin
comparison found 90 pins in both control and candidate and exactly:

```text
click                 8.2.1  -> 8.3.3
pygments              2.19.2 -> 2.20.0
pymdown-extensions    10.16.1 -> 10.21.3
```

No fourth package or transitive version changed. The only other literal lock
changes are the three corresponding `-r requirements.in` annotations.

### Fresh clean installations and audit

Separate fresh mode-`0700` control and candidate CPython `3.12.0` environments
installed their respective locks from public PyPI with `--no-cache-dir`.
Both passed `python -m pip check`, contained exactly 93 distributions, and
contained no `direct_url.json`. Their canonical inventory SHA-256 identities
are:

```text
control:
  dd7409860ff2f014fc607c77c57ce56df4d1da3175f381fa54eed9644fe50e59
candidate:
  1f60250c51822ad4e033ed729563ff8f2625a05e93730116c55477e97dae3688
```

The inventories differ only in the three authorized packages above.

A separate CPython `3.12.0` / pip `23.2.1` environment installed exact
`pip-audit==2.10.1`. Fresh raw no-ignore audits used `--no-deps`,
`--disable-pip`, no fix, no suppression, and no `--ignore-vuln` flags.
Control reported seven rows in five packages; candidate reported four rows in
three packages:

| Candidate package | Finding | Disposition before final review |
|---|---|---|
| Pymdown Extensions `10.21.3` | `CVE-2026-61632` | retained `EX-H01-PYMDOWN-B64-01`; first patch remains `11.0.0` |
| pytest `8.4.2` | `PYSEC-2026-1845` | retained `EX-H01-PYTEST-01`; first patch remains `9.0.3` |
| Vyper `0.4.3` | `PYSEC-2023-142` | authoritative range exclusion; not an exception |
| Vyper `0.4.3` | `PYSEC-2025-33` | authoritative range exclusion; not an exception |

The Click `PYSEC-2026-2132`, Pygments `PYSEC-2026-2987`, and Pymdown
Snippets `PYSEC-2026-2999` rows are absent from the candidate result. The b64
row remains at Pymdown `10.21.3`. The two Vyper determinations are not
exceptions and both Vyper dispositions remain unchanged.

Raw audit SHA-256 identities inside the private disposable task root are:

```text
control:
  6652eda4acae57de587d01799946f2e417e875c81d38e047a1d10b43a212d80c
candidate:
  88e5243eac8236c8eae64b7890708aa913d7cadf3d408303c2f0a5512bfe0a84
```

This audit proves candidate-lock remediation only. It is not GitHub or
Dependabot alert closure, no alert state was queried, and no exception is
claimed retired.

### Click, Pygments, and Pymdown behavior

Control Click `8.2.1` and candidate Click `8.3.3` were invoked independently
through migrate, console, and verify. Fourteen offline cases covered all three
help routes, missing-required-option failures, invalid choices,
case-insensitive accepted choices, and migrate/console sensitive-RPC
redaction. Every `(return code, stdout, stderr)` tuple was byte-identical
between environments, and the synthetic sensitive RPC never appeared in
output. The dependency gate additionally verifies the installed Click editor
patch uses a parsed argument vector and does not use `shell=True`.

Control and candidate Pygments produced the same exact normal Python token,
HTML, terminal, IPython, pytest terminal-writer, and Rich terminal outputs:

| Surface | SHA-256 |
|---|---|
| Token rows | `48953b4016ec793c0e8e23c9baaa7afe2ef8cc40b9605187666490c0071e5f35` |
| HTML | `c3e57a4263eb74006e0988b6dea2d398bbcabeb4e1b0119bd4fd8dbac899f48c` |
| Terminal and IPython terminal | `37ebe32a865ffdd7ecd4a5d097375ac299210fc8c16eeb6b9866682e0e0cb401` |
| pytest terminal writer | `b1c489802e2e3adbbf152619aee2bf48c29798c933a67066cdb53f9d478cf6f4` |
| Rich terminal | `14793d92ce8bc074a7d3ae21e04ab478339a33e81fc0382bfcbcaecc6255c317` |

Direct, aliased, and literal-folded affected-lexer selections remain rejected
by the repository reachability gate.

Fresh synthetic Snippets fixtures showed that Pymdown `10.16.1` leaked both a
shared-prefix sibling and an absolute outside-base file, while `10.21.3`
blocked shared-prefix, parent, and absolute traversal shapes and preserved an
inside-base include. The separate b64 fixture still encoded an image outside
the configured base under both versions. That result is residual evidence for
`EX-H01-PYMDOWN-B64-01`, not a b64 remediation claim.

### Candidate validation results

Every pytest command used `ETHERSCAN_API_KEY=local-placeholder`, an external
single-use mode-`0700` parent, an explicit external basetemp, and a distinct
private Boa cache installed with `from boa.interpret import set_cache_dir`.
Every parent was removed and verified absent after its command.

| Gate | Result |
|---|---|
| Complete H-01 dependency gate | 24 passed in 1.77 s |
| Current H-02 combined suite | 99 passed in 13.88 s |
| S1 clock profiles | 57 passed in 105.33 s |
| S2 checked inventory | `CLOCK_INVENTORY_OK`; production `100/95/17`, BN `32/100`, indirect `1`, cadence `455`, seconds-unit `58`, timestamp `11/37`, mixed-clock `4`, Vyper paths `92`; non-production test `31/29/5`, cadence `159` |
| S2 inventory tests | 60 passed in 25.56 s |
| Complete Lootbox directory | 175 passed in 120.66 s |
| S3 Switchboard Charlie target | 91 passed in 114.63 s |
| Collection | 2,845/2,987 selected; 142 pre-existing deselected in 5.91 s |
| Complete serial suite | 2,845 passed, 142 deselected in 316.46 s |

The candidate adds exactly eight selected H-01 dependency-gate cases over the
2,837-case baseline. It adds no skip, xfail, deselection, warning suppression,
or test relaxation.

### Compiler, artifact, and ABI identity

Control and candidate independently compiled both representative artifacts
with separate private Boa caches and exact
`vyper==0.4.3+commit.bff19ea2`:

| Artifact | Optimize | Source SHA-256 | ABI SHA-256 | Creation SHA-256 | Runtime SHA-256 | Combined fingerprint |
|---|---|---|---|---|---|---|
| `ClockObserver` | GAS | `238b2198a0217158db3f93000da47e4af5535883807e7b39cc3864f8d5b432f7` | `55fd4609d43321ded86224d044944b9a1955be174ca91fd55b75fb179f5090c8` | `b5f9615f2267ede387f99c77873aded9a241d30d0269a6f1df336ed93e454ecd` | `6842b313171e51a6b1b4f99143074e263de3f72d943838a3ec887ad3b1dd16d6` | `9ac4b78267b62fe4a645212b3b2bc83498afcedb7b75804d9449ea2056ce791d` |
| `Lootbox` | CODESIZE | `ebb4dcca8fa95bafe8e38ddc1d01886bfaceaf06302fe195f63db0bb7b3ef1da` | `e752a206ba5c78cb573c734c7bfd1c407f1cb98898d3d8e9d3513836c56f5fb2` | `9246a6d9dbee596750dc3a50d27d4418f318a62b7b4826a13f76aee37621e6ce` | `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097` | `263f6e5a75b85763dfed0656b194109512fad6856bc2acf8cccef660586aea0d` |

Separate empty ABI roots each exported 49 byte-identical files, skipped the
same 28 mock/testing paths, and reproduced the same nine pre-existing
standalone initializer failures. The canonical 49-file mapping SHA-256 is
`c49c61ad006d223a1bf13e2d26c5862eda82128f3cc640501c278c28f69b1dde`.
Generated and committed `Lootbox.json` are byte-identical at
`33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c`.

### Rollback reproduction

Rollback used the separate fresh control environment installed directly from
the old lock and the untouched exact-baseline integration worktree. It was
not an in-place downgrade. `pip check` passed, the baseline H-01 gate passed
16 cases, H-02 passed 99, S1 passed 57, collection was exactly 2,837/2,979
selected with 142 deselected, and the complete serial baseline suite passed
2,837 with the same 142 deselected in 322.85 seconds.

Before merge, rollback is to discard only the validated candidate environment
and restore the five authorized repository files to the frozen baseline
bytes. After any later merge, rollback requires a separately reviewed revert
and regenerated old lock; destructive reset is not authorized.

### Proposed exception disposition and Gate 1 stop

Subject to final exact-byte independent review and later owner approval, the
proposed disposition is:

- proposed retirement only: `EX-H01-CLICK-01`,
  `EX-H01-PYGMENTS-01`, and `EX-H01-PYMDOWN-SNIPPETS-01`;
- retain: `EX-H01-PYTEST-01` and `EX-H01-PYMDOWN-B64-01`.

All five bounded exceptions remain operative during implementation and review.
Final byte-level dependency-gate, exact-scope, whitespace, and local/cached/live
`rh` freshness results are recorded only after these evidence bytes are
complete. The package stops at Gate 1 unstaged and uncommitted. No staging,
commit, push, merge, deployment, signing, verification submission, alert
query/mutation, live-chain action, or private retained-evidence access was
performed.

### Final Gate 1 scope and freshness

After the complete evidence bytes were written, the dependency gate passed
again with 24 cases and the complete serial suite passed again with 2,845
selected cases and the same 142 deselected. `git diff --check` is clean.
The exact changed-path set is only:

```text
docs/chains/rh/evidence/dependency-exception-exit-preflight.md
docs/chains/rh/evidence/dependency-security-gate.md
requirements.in
requirements.txt
tests/deployment/test_dependency_gate.py
```

There is no staged or untracked path. The diff adds no skip, xfail,
deselection, warning suppression, or relaxation. The final non-self-referential
implementation file hashes are:

```text
requirements.in
  1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9
requirements.txt
  214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010
tests/deployment/test_dependency_gate.py
  c2aacf206d159bc74968496ced55f7eb7978f74249b7b5af7634172db8bd903b
```

The feasibility report remains byte-identical at
`9b9ad56d73d8a7418dcc0e452b3affb927979ce53fd90fcd5f84f9b9dfcfbfec`,
and its preserved branch still resolves to
`2b6920c2fc9044cbfb6f715c03674e96027084e3`. The integration worktree is
clean. Local `rh`, cached `origin/rh`, and a final live `origin/rh` read all
remain exact
`c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d`.

Gate 1 therefore stops with these five authorized files unstaged and
uncommitted. The proposed dispositions remain pending independent review and
owner approval; all five exceptions remain operative.

## 26 July 2026: bounded F1/F3 correction and current-`rh` reconciliation

This latest section supersedes the first implementation Gate 1 verdict above.
It does not rewrite the historical test results; it marks them
non-authoritative and records the fresh corrected interval.

### Reconciliation identity and byte preservation

Before reconciliation, the complete unstaged full-index patch had SHA-256
`22e4fa540a8f27aff68ad5a906bad9533138a88f2c91c5a2e853e4ddcd0fcaae`
and contained 815 lines / 34,322 bytes. Its exact five file hashes were:

```text
requirements.in
  1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9
requirements.txt
  214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010
tests/deployment/test_dependency_gate.py
  c2aacf206d159bc74968496ced55f7eb7978f74249b7b5af7634172db8bd903b
docs/chains/rh/evidence/dependency-security-gate.md
  a2266346b0255df63e3291eef8e106c6ac39ec9269e1a531dc06201a3b45bacd
docs/chains/rh/evidence/dependency-exception-exit-preflight.md
  15a9dfebb3415f0204a73123180780bb2c720547612624c78bd8c1183def369e
```

At the authorized pre-merge observation on 26 July 2026, local `rh`, cached
`origin/rh`, live `origin/rh`, and the clean integration worktree all resolved
to `8e4a965f034dc3d11b60fbb674ebbb4095b57d98`. This is historical
reconciliation provenance, not a current-ref claim. The incoming range
contained only H-03 documentation commits `2c8468a` and `d65e4db`, adding or
changing only:

```text
docs/chains/rh/evidence/robinhood-blueprint-phase-a.md
docs/chains/rh/track-7-h3-robinhood-blueprint-omissions.md
```

A normal conflict-free `--no-ff` merge created
`9aedbbbf13f8f60e0bd816d6493e310cacbfbbda` with parents:

```text
parent 1: c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d
parent 2: 8e4a965f034dc3d11b60fbb674ebbb4095b57d98
```

Immediately after the merge, all five file hashes and the complete full-index
patch hash remained byte-identical. There was no conflict, staged H-01 path,
or candidate-byte movement.

### Fresh resolver, installation, and audit evidence

Two independent mode-`0700` CPython `3.12.0` resolver environments used seed
interpreter SHA-256
`d23fa2c326127c9590d097603f105d69e68774968f46246fc7a8a80103600765`,
pip `23.2.1`, pip-tools `7.4.1`, build `1.5.0`, Click `8.4.2`,
packaging `26.2`, pyproject-hooks `1.2.0`, setuptools `83.0.0`, and wheel
`0.47.0`. Each authoritative run started with the approved frozen lock at the
output path, a separate private cache, and public PyPI only.

Both input hashes were
`1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9`;
both generated locks were byte-identical to the repository lock at
`214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010`.
The exact normalized delta remains only:

```text
click                 8.2.1  -> 8.3.3
pygments              2.19.2 -> 2.20.0
pymdown-extensions    10.16.1 -> 10.21.3
```

Separate fresh old-lock and candidate environments each contained 93
distributions, passed `pip check`, contained no `direct_url.json`, and differed
only in those three rows. For a sorted lowercase `name==version` newline
inventory, their SHA-256 values were:

```text
control:
  d27107b4ef813977aa270e8e4d363a455c18e009e0336db8c4b803416bc8f234
candidate:
  06200ff43c346a61da7ded7e11a8c5b973e0167080f8f1764b417bda183a6a36
```

Fresh exact `pip-audit==2.10.1` no-ignore audits reported seven control rows
and four candidate rows. Raw JSON SHA-256 values were:

```text
control:
  9738ae73d02ab0a403a7aed7d0608a700d99929f8ad7234b384ad7ac4fc9c587
candidate:
  5d098257bf6a21d9903c0b3af99fa8b63c8e417cef8501dc1a058465b1996c4f
```

The candidate rows remain Pymdown b64 `CVE-2026-61632`, pytest
`PYSEC-2026-1845`, and the two range-excluded Vyper rows. No GitHub or
Dependabot state was queried, and candidate audit remediation is not alert
closure.

### F1: explicit Rich color mode

The Rich behavior case now constructs `Console` with `no_color=False` together
with the existing `force_terminal=True`, `color_system="standard"`, and fixed
width. It asserts the rendered transcript contains `\x1b[` before accepting
the exact colored-output SHA-256:

```text
4a98e8fea362182468a3d6c34cc22bdbc6efb5c4a293833960a382bdaf9afdd5
```

The complete corrected H-01 gate passed 30 cases with `NO_COLOR` absent and
passed the same 30 cases with ambient `NO_COLOR=1`. Therefore ambient
no-color state cannot satisfy or alter this colored rendering check. The
earlier 24-case result is not authoritative.

### F3: bounded string-activation reachability

The AST reachability scanner now rejects direct and imported/aliased
`markdown.markdown(..., extensions=...)` activation of `pymdownx.b64` and
`pymdownx.snippets` without requiring a Pymdown import. It resolves:

- direct string literals;
- list, tuple, and set literals;
- bounded name assignments;
- statically resolvable string `+` concatenations; and
- bounded sequence `+` concatenations.

The existing allowlist remains exact only for
`tests/deployment/test_dependency_gate.py`. Four focused positive cases cover
both extensions, direct literals, aliases, assignments, string
concatenations, and sequence concatenation. Two focused negative cases cover
ordinary safe extensions and a deliberately unresolved runtime selection.
The focused run passed 6 cases. This is intentionally bounded static analysis,
not unrestricted runtime dataflow.

### F4, F5, and F6 residual dispositions

- **F4 — Pygments:** The scanner still does not claim exhaustive coverage of
  runtime-computed lexer names, plugin registry selection, `getattr`, or other
  dynamic indirection. It covers direct/aliased affected-lexer imports and
  bounded literal/concatenated `get_lexer_by_name` calls. A current
  repository-wide scan finds no dynamic affected-lexer path. This limitation
  remains disclosed, and `EX-H01-PYGMENTS-01` remains operative until the
  separately reviewed retirement transition.
- **F5 — Click:** The procedural Click reachability trigger is not a control
  relied upon after any separately reviewed Click retirement transition.
  Current evidence also includes installed patch-source and migrate/console/
  verify behavior checks, but `EX-H01-CLICK-01` remains operative here.
- **F6 — scanner boundary:** Repository traversal is rooted at the supplied
  tree, excludes the enumerated generated/vendor/environment directories,
  does not follow directory symlinks, and skips symlinked files. It does not
  claim coverage outside that root or through symlink targets. The Pygments
  pytest-rendering assertion imports pinned pytest `8.4.2`'s private
  `_pytest._io.terminalwriter.TerminalWriter`; any pytest movement or private
  API change reopens this evidence. Filesystem traversal is not widened and
  pytest is not upgraded.

### Corrected validation results

Every pytest invocation used a new mode-`0700` external parent, an explicit
external basetemp, and a private Boa cache.

| Gate | Fresh corrected result |
|---|---|
| Focused F3 scanner cases | 6 passed; 24 deselected |
| Complete H-01, `NO_COLOR` absent | 30 passed in 1.75 s |
| Complete H-01, ambient `NO_COLOR=1` | 30 passed in 1.77 s |
| Current H-02 | 99 passed in 13.34 s |
| S1 | 57 passed in 104.11 s |
| S2 checker/tests | `CLOCK_INVENTORY_OK`; 60 passed in 25.45 s |
| Complete Lootbox directory | 175 passed in 121.24 s |
| Switchboard Charlie | 91 passed in 114.43 s |
| Collection | 2,851/2,993 selected; 142 pre-existing deselected |
| Complete serial candidate suite | 2,851 passed; 142 deselected in 313.39 s |

The count increase from the superseded 2,845 result is exactly six selected
F3 cases: four fail-closed positives and two bounded negatives. No skip,
xfail, warning suppression, relaxation, or unexplained deselection was added.

### Compiler and ABI canonicalization

Fresh control and candidate compilations with separate Boa caches reproduced
byte-identical ClockObserver and Lootbox source, compiler settings, ABI,
creation bytecode, runtime bytecode, and combined fingerprints listed in the
preceding artifact table. The raw Lootbox file hash remains
`669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65`.

The reviewed compiler-data source and creation sub-hashes are reproducible
with this exact canonicalization procedure:

```text
H01_BOA_CACHE_DIR=<new-mode-0700-cache> PYTHONPATH=. <exact-python> -c '
from pathlib import Path
import os
import boa
from boa.interpret import set_cache_dir
from tests.utils.clock_profiles import artifact_fingerprint
cache = Path(os.environ["H01_BOA_CACHE_DIR"])
cache.mkdir(mode=0o700)
set_cache_dir(cache)
artifact = boa.load_partial("contracts/core/Lootbox.vy")
fingerprint = artifact_fingerprint(artifact)
print(fingerprint.source_sha256)
print(fingerprint.creation_bytecode_sha256)
'
```

It prints, in order:

```text
ebb4dcca8fa95bafe8e38ddc1d01886bfaceaf06302fe195f63db0bb7b3ef1da
9246a6d9dbee596750dc3a50d27d4418f318a62b7b4826a13f76aee37621e6ce
```

These are hashes of Boa/Vyper compiler-data source and creation bytes, not the
raw source-file hash. Old/candidate byte equality and the combined fingerprint
are the controlling artifact result. No private retained evidence was read.

Separate ABI exports again produced 49 byte-identical files, the same 28
mock/testing skips, and the same nine known standalone initializer failures.
The canonical mapping hash remains
`c49c61ad006d223a1bf13e2d26c5862eda82128f3cc640501c278c28f69b1dde`;
generated and committed `Lootbox.json` remain byte-identical at
`33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c`.

### Fresh rollback and exception status

The separate fresh old-lock environment and untouched current-`rh` integration
worktree passed `pip check`, baseline H-01 16, H-02 99, S1 57, collection
2,837/2,979 with 142 deselected, and the complete serial rollback suite with
2,837 passed / 142 deselected in 279.78 seconds.

No exception is retired. `PROPOSED_RETIREMENTS` remains proposed only. All
five bounded exceptions remain operative. Any split into retired historical
records and the two retained operative exceptions requires another fresh
exact-hash review, independent approval, and separate owner authorization.
This corrected package stops unstaged and uncommitted at Gate 1. The
reconciliation merge exists only on the local feature branch; nothing was
pushed or merged into `rh`.

## 27 July 2026 final bounded Gate 1 correction

This section supersedes the preceding 30-case / 2,851-case result only where
the new scanner cases, reproducible aggregate serialization, rollback
boundary, or ref wording differ. It does not change the lock, compiler,
exception, or owner disposition.

### Exact starting bytes, cleanup, and ref observations

Before editing, the five approved files still had the Gate 1 hashes:

```text
requirements.in
  1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9
requirements.txt
  214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010
tests/deployment/test_dependency_gate.py
  9e9b1091d764a47a5f209a30b40cdefdaa38fd245b1d648cf2a62b361d2102d8
docs/chains/rh/evidence/dependency-security-gate.md
  a08ede99983ac73386faabc33e6fd6c35d31890c943e712bcbcfce19587a1daf
docs/chains/rh/evidence/dependency-exception-exit-preflight.md
  d7ab7b0d63a2ce2674360e2d8c09e48a1948af7c05847614d7c2c6030ce8341e
```

The complete unstaged full-index patch SHA-256 was exact
`9c075c4f6f2a69bd5a56eab79fee44fb53669b83a0df69b4fcc9cffa6ade93cf`.

The ignored generated Python cache/bytecode inventory was resolved before
cleanup and contained only these exact paths:

```text
.hypothesis/constants/0236a436f2a29278
.hypothesis/constants/06b5d4da03c0dbc5
.hypothesis/constants/090671e773896788
.hypothesis/constants/0e9ef9ec119ea428
.hypothesis/constants/47246ce20fa5c099
.hypothesis/constants/59ce3bf3e4616a90
.hypothesis/constants/6a23e09f813b6a5c
.hypothesis/constants/8a6e0e1115a36284
.hypothesis/constants/8b1a8fbd01a24982
.hypothesis/constants/8c7cee9e0d794ba9
.hypothesis/constants/cd5041e2a0414bb9
.hypothesis/constants/ce6fdaf779cc0a92
.hypothesis/constants/e422491e1f6ea729
.hypothesis/constants/f2d64de826b91460
.hypothesis/constants/f32d0f9860fc926e
.hypothesis/constants/f53330046d3946ef
config/__pycache__/BluePrint.cpython-312.pyc
config/__pycache__/network_profiles.cpython-312.pyc
scripts/__pycache__/console.cpython-312.pyc
scripts/__pycache__/migrate.cpython-312.pyc
scripts/__pycache__/verify.cpython-312.pyc
scripts/utils/__pycache__/deploy_args.cpython-312.pyc
scripts/utils/__pycache__/json_file.cpython-312.pyc
scripts/utils/__pycache__/log.cpython-312.pyc
scripts/utils/__pycache__/migration.cpython-312.pyc
scripts/utils/__pycache__/migration_helpers.cpython-312.pyc
scripts/utils/__pycache__/migration_runner.cpython-312.pyc
tests/__pycache__/conf_core.cpython-312-pytest-8.4.2.pyc
tests/__pycache__/conf_env.cpython-312-pytest-8.4.2.pyc
tests/__pycache__/conf_mock.cpython-312-pytest-8.4.2.pyc
tests/__pycache__/conf_utils.cpython-312-pytest-8.4.2.pyc
tests/__pycache__/conftest.cpython-312-pytest-8.4.2.pyc
tests/__pycache__/constants.cpython-312.pyc
tests/utils/__pycache__/clock_profiles.cpython-312-pytest-8.4.2.pyc
tests/utils/__pycache__/clock_profiles.cpython-312.pyc
```

Only those ignored cache roots were removed. No tracked file, other worktree,
or stash was touched.

At `2026-07-27T03:02:59Z`, an initial read observed local `rh` and cached
`origin/rh` at `7a3a36666f277277fa08b55081b3f58c7cd3ba64`; a separate live
`git ls-remote` immediately confirmed the same live ref. At
`2026-07-27T03:30:58Z`, the final validation-freeze recomputation again
observed local, cached, and live `rh` at exact `7a3a3666`, with a clean
integration worktree. These are timestamped observations only. They do not
make later documentation movement candidate authority, and this correction
does not reconcile `rh`. Immediately before any later commit-time
reconciliation, all three refs and integration cleanliness must be recomputed,
the incoming delta must be reviewed, and new authority obtained where the
approved target differs.

### Per-element and expanded Markdown activation scanning

The scanner no longer treats a sequence as all-or-nothing. It independently
collects every statically resolvable string element in list, tuple, set,
bounded name, string-`+`, and sequence-`+` forms. An unresolved sibling
contributes no inferred value but cannot hide a direct banned value. Both:

```text
extensions=["pymdownx.b64", pick_extra()]
extensions=[pick_extra(), "pymdownx.snippets"]
```

therefore fail closed. Safe literals alongside unresolved runtime values
remain allowed because this is bounded static resolution, not speculative
runtime dataflow.

The same extension check now covers:

- `markdown.markdown(...)`;
- `markdown.Markdown(...)`; and
- `markdown.markdownFromFile(...)`.

Direct imports, module aliases, imported function/class aliases, direct static
function/class alias assignments, bounded extension assignments and
concatenations, and direct or bounded named `**` keyword mappings are covered.
The allowlist remains exactly
`tests/deployment/test_dependency_gate.py`. Sixteen positive cases exercise
both banned extensions across the three call surfaces and alias shapes; five
negative cases preserve safe literal and unresolved-runtime behavior. The
focused matrix is therefore 21 cases, 24 other H-01 cases deselected.

### Reproducible installed-inventory identities

Each fresh interpreter generated its 93-row inventory twice using this exact
command and byte serialization:

```text
<exact-python> -c 'from importlib.metadata import distributions; import sys; rows=sorted("{}=={}".format(d.metadata["Name"].lower(), d.version) for d in distributions()); sys.stdout.buffer.write(("\n".join(rows)+"\n").encode("utf-8"))' > inventory.txt
shasum -a 256 inventory.txt
```

The serialization is UTF-8, package metadata `Name` lowercased without other
normalization, Python-codepoint sorted complete `name==version` rows, one LF
after every row including the last, and no other bytes. Independent reruns
reproduced:

```text
control:   9e30800bec2f4d9a784314b6a3d3d25a37ee7c994a022366a577966a698abfa2
candidate: f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d
```

Both contain exactly 93 rows. Their textual diff contains only Click
`8.2.1 -> 8.3.3`, Pygments `2.19.2 -> 2.20.0`, and Pymdown Extensions
`10.16.1 -> 10.21.3`. The earlier `d27107b4...` and `06200ff4...` aggregate
digests lacked a retained exact generating serialization and did not reproduce
under the command above. They are historical, non-load-bearing observations
and are not assigned invented provenance. The complete inventories, exact
three-row diff, lock equality, and the newly reproducible digests are the
controlling installed-state evidence.

### Reproducible 49-file ABI mapping identity

Control and candidate independently ran `scripts/export_abis.py` into separate
empty private output roots. Each produced 49 files, skipped the same 28
mock/testing paths, and reported the same nine known standalone initializer
failures. Every corresponding output byte was identical. Each root then used:

```text
<exact-python> -c 'from pathlib import Path; import hashlib,json,sys; root=Path(sys.argv[1]); mapping={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}; sys.stdout.buffer.write(json.dumps(mapping,sort_keys=True,separators=(",",":")).encode("utf-8"))' <abi-root> > abi-map.json
shasum -a 256 abi-map.json
```

The mapping is a JSON object from POSIX relative filename to lowercase
hexadecimal file SHA-256, with lexicographically sorted keys, compact `,` and
`:` separators, UTF-8 encoding, and no trailing newline. Both independently
generated 4,240-byte mappings reproduced:

```text
c49c61ad006d223a1bf13e2d26c5862eda82128f3cc640501c278c28f69b1dde
```

Control, candidate, and committed `scripts/abis/Lootbox.json` also remained
byte-identical at
`33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c`.
Separate private-cache compilation again reproduced byte-identical
ClockObserver and Lootbox source, settings, ABI, creation/runtime bytecode,
and combined fingerprints `9ac4b782...` and `263f6e5a...`.

### Real-worktree rollback boundary and fresh validation

The authoritative rollback replay used the fresh old-lock environment from the
clean real Git integration worktree observed at `2026-07-27T03:22:10Z`, not an
export. The
`test_committed_base_history_inventory_is_unchanged` Base-profile regression
explicitly calls `git rev-parse --is-inside-work-tree` and self-skips outside
a Git worktree. A `git archive` lacks `.git`; its
`2,836 passed + 1 skip` shape is therefore not equivalent to the authoritative
result and is non-load-bearing because it does not execute the committed
Base-history assertion.

The real-worktree rollback environment passed `pip check`, H-01 16, H-02 99,
S1 57, collection 2,837/2,979 with 142 deselected, and the complete serial
suite at 2,837 passed / 142 deselected in 278.02 seconds, with no skip or
xfail.

Every corrected candidate pytest command used an external mode-`0700`
basetemp parent, a private Boa cache, and the exact candidate interpreter.

| Gate | Final bounded-correction result |
|---|---|
| Focused expanded scanner matrix | 21 passed; 24 deselected |
| Complete H-01, `NO_COLOR` absent | 45 passed |
| Complete H-01, ambient `NO_COLOR=1` | 45 passed |
| H-02 | 99 passed in 11.60 s |
| S1 | 57 passed in 96.53 s |
| S2 checker/tests | `CLOCK_INVENTORY_OK`; 60 passed in 24.00 s |
| Complete Lootbox directory | 175 passed in 108.09 s |
| Switchboard Charlie | 91 passed in 102.83 s |
| Collection | 2,866/3,008 selected; 142 pre-existing deselected |
| Complete serial candidate suite | 2,866 passed; 142 deselected in 276.58 s |

The exact increase over the superseded 2,851 selected cases is 15: twelve new
positive scanner parameters and three new negative parameters. No skip,
xfail, warning suppression, relaxation, or new deselection was introduced.
The two independent resolvers still produced byte-identical lock SHA-256
`214f6c32...`, with exactly the authorized three-package delta and no
transitive drift.

No exception is retired. `PROPOSED_RETIREMENTS` remains proposed only, and all
five bounded exceptions remain operative. This package remains unstaged and
uncommitted pending narrow delta re-review. No reconciliation, commit, push,
alert mutation, deployment, signing, or live-chain action is authorized or
performed here.

## H-01 three-exception retirement transition

**Authorization status:** The owner adopted the exact
`H-01 THREE-EXCEPTION RETIREMENT TRANSITION AUTHORIZATION` against integrated
baseline commit `d62777646cba1ae448fb9e26519c6fa295f437df`, tree
`01b1d7c8fc7bdf5163e20efe1f61b53db2b01a61`.

**Effectivity boundary:** This section defines the final target repository
policy. It becomes operative only when the exact independently approved
transition commit containing these bytes is integrated into authoritative
`rh`. Until that integration, the historical all-five operative state remains
the authoritative policy. A feature branch, working-tree change, Gate 1
candidate, review approval, or commit that is not integrated into `rh` does
not itself retire an exception.

**New-advisory authorization boundary:** The retirement authorization above
predates `PYSEC-2026-3654`. Mick Hagen, H-01 owner, explicitly adopted this
exact bounded exception on 11 August 2026 after the containment candidate and
independent review were complete. The new exception becomes operative only
when the exact authorized bytes are integrated into authoritative `rh`; the
authorization alone does not make a feature branch authoritative. A green test
result proves only that the bounded fail-closed controls are represented
consistently; it is not release, deployment, or alert-state authority.

The transition changes no dependency byte. Its immutable integrated inputs
remain:

```text
requirements.in
  1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9
requirements.txt
  214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010
```

The exact integrated versions remain Click `8.3.3`, Pygments `2.20.0`,
Pymdown Extensions `10.21.3`, pytest `8.4.2`, Titanoboa `0.2.7`, and Vyper
`0.4.3`. The three-package lock delta and every transitive hold remain
unchanged.

### Final target exception register

| Exception | Final target status | Basis and boundary |
|---|---|---|
| `EX-H01-CLICK-01` | **Retired—historical and non-operative.** | Exact `click==8.3.3` is outside the `PYSEC-2026-2132` affected range and contains the reviewed editor-launch remediation. The former exception remains retained as historical evidence only. |
| `EX-H01-PYGMENTS-01` | **Retired—historical and non-operative.** | Exact `Pygments==2.20.0` remediates `PYSEC-2026-2987`. Dynamic/plugin lexer-selection limitations remain disclosed defense-in-depth boundaries, not a continuing exception basis. |
| `EX-H01-PYMDOWN-SNIPPETS-01` | **Retired—historical and non-operative.** | Exact `pymdown-extensions==10.21.3` remediates the reviewed `PYSEC-2026-2999` Snippets traversal finding. This disposition does not apply to `pymdownx.b64`. |
| `EX-H01-PYTEST-01` | **Retained—operative.** | Exact `pytest==8.4.2` remains governed by the controls, triggers, review, and expiry below. Pytest 9 remains a separate S1/Vyper/Track 6 decision. |
| `EX-H01-PYMDOWN-B64-01` | **Retained—operative.** | Exact `pymdown-extensions==10.21.3` remains affected by `CVE-2026-61632`; first patch remains `11.0.0`, outside the current resolver-valid Titanoboa/docs graph. |
| `EX-H01-PYMDOWN-REDOS-01` | **Retained—operative.** | Exact `pymdown-extensions==10.21.3` is affected by `PYSEC-2026-3654` / `GHSA-gm37-52c6-37mw` / `CVE-2026-67422`; first patch is `11.0.1`, outside the current resolver-valid Titanoboa/docs graph. The owner-authorized controls below contain the currently unreachable surface. |

The historical `PROPOSED_RETIREMENTS` state is superseded only when the
effectivity boundary above is satisfied. The three retired records remain
preserved for audit chronology, evidence retention, and separately authorized
disposal; they are not operative authorization after effective integration.

### Operative retained exception terms

The retained-exception owner is **Mick Hagen, H-01 owner**. All three retained
exceptions keep the scheduled security review on **15 August 2026** and hard
expiry at **2026-08-31T23:59:59Z**. The earlier of a finding-specific
invalidation trigger or hard expiry ends authorization. An expired exception
blocks deployment rehearsal and merge; it never converts into permanent
acceptance.

#### `EX-H01-PYTEST-01` — retain pytest `8.4.2`

- **Status:** Retained—operative.
- **Threat model:** pytest before `9.0.3` uses predictable
  `/tmp/pytest-of-{user}` directories on Unix. Another local user can cause
  denial of service and may be able to gain privileges while pytest runs.
- **Scope:** Exact pytest `8.4.2` under CPython `3.12.0` for trusted repository
  validation on owner-controlled local or ephemeral single-tenant runners.
  Pytest is not part of deployed contract runtime.
- **Compensating controls:** Use a fresh task-specific mode-`0700` parent and
  explicit private `--basetemp` for every invocation; run only trusted
  repository tests/plugins; prohibit shared multi-user runners; preserve the
  exact S1 runtime assertions; add no skip, xfail, warning suppression, or test
  relaxation.
- **Re-review/invalidation triggers:** Shared or multi-user runner use;
  untrusted tests/plugins; inability to provide a private basetemp; pytest,
  Vyper, Titanoboa, Python, plugin, private pytest API, or S1-profile change;
  advisory/exploit change; demonstrated pytest 9 compatibility; scheduled
  review; or hard expiry.

#### `EX-H01-PYMDOWN-B64-01` — retain Pymdown Extensions `10.21.3`

- **Status:** Retained—operative.
- **Threat model:** `pymdownx.b64` accepts relative traversal or absolute image
  paths and embeds readable image-extension files outside `base_path` into
  rendered output.
- **Scope:** Exact transitive Pymdown Extensions `10.21.3`. The repository has
  no b64 extension, MkDocs configuration, documentation build, or untrusted
  Markdown-rendering path. The first patch is `11.0.0`, which is not
  resolver-valid under unchanged `titanoboa==0.2.7` and
  `mkdocs-material==9.5.41`.
- **Compensating controls:** Do not enable `pymdownx.b64`; do not render
  untrusted Markdown; preserve fail-closed source/configuration scanning; do
  not run a docs build with repository, CI, or readable host secrets.
- **Re-review/invalidation triggers:** Any b64 activation, Pymdown import or
  configuration, Markdown/docs pipeline, untrusted Markdown, advisory/exploit
  change, Titanoboa/docs-graph movement, scanner-boundary change, scheduled
  review, or hard expiry.

### Owner-authorized Pymdown ReDoS exception

The reviewed [PyPA record](https://github.com/pypa/advisory-database/blob/main/vulns/pymdown-extensions/PYSEC-2026-3654.yaml),
[GitHub advisory](https://github.com/advisories/GHSA-gm37-52c6-37mw),
[upstream fix](https://github.com/facelessuser/pymdown-extensions/commit/c68498598d7b13011bb4571350b6e3612a4ce44b),
and [PyPI release](https://pypi.org/project/pymdown-extensions/11.0.1/)
identify one finding under `PYSEC-2026-3654`, `GHSA-gm37-52c6-37mw`, and
`CVE-2026-67422`. Affected versions are `<=11.0`; the first fixed release is
`11.0.1`. GitHub rates the upstream finding High at CVSS 3.1 score `7.5`
(`AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H`). It is distinct from the older Caption
ReDoS fixed in `10.16.1`.

The affected processors are `pymdownx.caret`, `pymdownx.tilde`,
`pymdownx.betterem`, and `pymdownx.magiclink`; `pymdownx.extra` also exposes
the default BetterEm processor. When an affected extension is enabled, a
crafted sub-50-byte untrusted Markdown line can cause exponential regular-
expression backtracking and pin the rendering thread at full CPU. This is an
availability threat, not a confidentiality or integrity finding.

The exact `origin/rh` tree at
`02468586d710e2cce2360c2bc07e94de6ebdab29` has no MkDocs configuration or
documentation-build command and no Pymdown import or Markdown-rendering call
outside `tests/deployment/test_dependency_gate.py`. That explicit dependency
test activates only `pymdownx.snippets` and `pymdownx.b64`, not an extension
affected by this ReDoS. No repository path accepts or renders untrusted
Markdown. Installation of the affected package alone does not activate an
extension, so the reviewed current exploit path is absent.

A clean patch upgrade is not resolver-valid. Exact `titanoboa==0.2.7`
requires `mkdocs-material==9.5.41`, which requires
`pymdown-extensions~=10.2` and therefore excludes version 11. Pymdown
Extensions `11.0.1` itself requires Python `>=3.10` and Markdown `>=3.6`, so it
is otherwise compatible with the reviewed CPython `3.12.0` / Markdown `3.9`
profile. The Titanoboa/Material metadata constraint is the blocker. The lock
must not be hand-edited or installed in a metadata-inconsistent state.

#### `EX-H01-PYMDOWN-REDOS-01` — retain Pymdown Extensions `10.21.3`

- **Status:** Retained—operative.
- **Finding:** `PYSEC-2026-3654`, alias `GHSA-gm37-52c6-37mw` /
  `CVE-2026-67422`. Affected versions are `<=11.0`; the first fixed release is
  `11.0.1`.
- **Authorization:** Mick Hagen, H-01 owner, explicitly adopted the exact
  independently reviewed containment on 11 August 2026. The exception becomes
  operative only after these exact authorized bytes are integrated into
  authoritative `rh`; neither a feature branch nor a green test run grants
  repository authority.
- **Threat model:** Activation of `pymdownx.caret`, `pymdownx.tilde`,
  `pymdownx.betterem`, `pymdownx.magiclink`, or `pymdownx.extra` against
  attacker-controlled Markdown permits a very short input to monopolize the
  renderer CPU through exponential regular-expression backtracking.
- **Scope:** Exact Pymdown Extensions `10.21.3` under the unchanged
  `titanoboa==0.2.7` / `mkdocs-material==9.5.41` graph. The repository has no
  affected extension activation, MkDocs configuration or build, documentation
  renderer, or untrusted Markdown input path. The first fixed release is
  `11.0.1`, which is not resolver-valid under the unchanged graph.
- **Compensating controls:** Do not enable any affected extension or
  `pymdownx.extra`; do not render untrusted Markdown; preserve the bounded
  scanner, which rejects literal affected names in supported configuration and
  Markdown API shapes plus direct Pymdown imports; treat any Markdown API call
  with a runtime-computed extension value as a manual re-review trigger because
  the AST gate cannot prove that value; do not add a MkDocs/docs-render path
  while the affected pin remains; do not run the exponential-time proof of
  concept in CI.
- **Re-review/invalidation triggers:** Any affected extension, Pymdown import
  or configuration, MkDocs/docs pipeline, Markdown-rendering API, untrusted
  Markdown, advisory/exploit change, Titanoboa/Material/Pymdown/Markdown/Python
  movement, scanner-boundary change, scheduled review, or hard expiry.
- **Review/expiry:** Governed by the common retained-exception schedule above.
- **Integration boundary:** This authorization permits publication and review
  of this exact amendment. The exception becomes operative only when these
  bytes are integrated into authoritative `rh`; dependent requirements changes
  must not integrate before that boundary is satisfied.

### Pre-authorization Pymdown ReDoS containment validation

This amendment was prepared from exact `origin/rh` commit
`02468586d710e2cce2360c2bc07e94de6ebdab29` / tree
`082a460d0ee190ac74a87ab29828d9c867ddff06`. With repository `addopts`
cleared, RPC and credential variables unset, and all generated state under an
external mode-`0700` parent, the dependency gate collected and passed all 56
tests. The focused bounded fail-closed selection passed 13 cases: seven root
configuration activations, five affected Markdown API activations, and the
then-pending exception evidence check. No exponential-time input was executed.

The requirements inputs remained byte-identical to the base: `requirements.in`
has Git blob `85bacd1b372b167c825497e06cf7751a432bc212` and SHA-256
`1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9`;
`requirements.txt` has Git blob `eaf12f774a108a100696a5c77d8a9dec9617ed1e`
and SHA-256
`214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010`.
The amended gate SHA-256 was
`d68dfa6cb7744ca236b6cef61ae81e8e99f71b4e204e8663b10b0690bb49bae1`.
These green results established internal consistency and fail-closed
containment only. They did not authorize the exception at that checkpoint;
the later explicit owner authorization above controls the current target
status.

### Owner authorization and current-`rh` reconciliation — 11 August 2026

Mick Hagen, H-01 owner, explicitly authorized the bounded
`EX-H01-PYMDOWN-REDOS-01` containment in the current Codex task on 11 August
2026. The independently reviewed containment patch was replayed without scope
expansion onto exact authoritative `rh` commit
`3a4cac429a860ffc95bd85612d9e345108332833`, tree
`0bc766984da112d8bde3b499e763f31b192eb591`. Integration of the exact resulting
two-file patch remains the effectivity boundary.

The authorization changes no dependency byte. `requirements.in` remains
SHA-256
`1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9`, and
`requirements.txt` remains SHA-256
`214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010`.
The authorized dependency-gate source is SHA-256
`2fcb7f1084e2e9a3d7d2e98b9da37a8a5b0372f26acf7eeb60dfc03c24ad58bd`.

With repository `addopts` cleared, RPC and credential variables unset, and all
generated state under an external mode-`0700` parent, the first full gate run
passed 55 of 56 cases and exposed one evidence-only duplicate schedule phrase.
The phrase was reduced to the common retained-exception schedule; the final
complete replay passed all 56 cases. No exponential-time proof of concept,
network request, dependency resolution, alert mutation, deployment, or live
chain action was performed.

### Validation inheritance and alert-state boundary

The retirement basis is the exact integrated lock, raw no-ignore package
audit, reviewed package behavior, complete H-01/H-02/S1/S2/S3 and serial-suite
results, compiler/ABI identity, and real-worktree rollback recorded above. The
final reviewed interval passed H-01 45 cases with `NO_COLOR` absent and
present, H-02 99, S1 57, S2 60 with `CLOCK_INVENTORY_OK`, Lootbox 175,
Switchboard Charlie 91, collection 2,866 of 3,008 with 142 expected
deselections, and the complete 2,866-case serial suite with zero skip or
xfail.

The Pygments scanner still does not claim exhaustive runtime/plugin selection
coverage; the patched package and retained scanner are separate controls. The
procedural Click trigger is not relied upon after effective retirement. The
scanner root/symlink boundary and pinned pytest private API remain disclosed;
the latter remains governed by `EX-H01-PYTEST-01`.

Package remediation and repository exception retirement are distinct from
GitHub/Dependabot alert closure. This transition does not claim that any
GitHub or Dependabot alert is closed, dismissed, resolved, or otherwise
changed. No authenticated alert-state query was required or performed. Any
future alert-state statement requires separate authority and fresh
authenticated evidence.

### Post-retirement CCIP CLI surface review

`scripts/ccip_send.py` uses Click only for a bounded command and option
declaration surface. It does not import, reference, or invoke `click.edit`,
wildcard Click imports, or shell execution. The reachability gate therefore
includes it in the reviewed CLI allowlist while continuing to reject the
editor surface. This defense-in-depth update does not reopen the retired Click
exception.

## Declared Web3 operator dependency prerequisite — 11 August 2026

**Status:** Local candidate pending independent review. This section records a
four-file prerequisite only; it is not operative on `rh`, merge approval, H-06
requalification, deployment authorization, or evidence that any external alert
was closed.

### Immutable candidate boundary

The isolated implementation worktree was created mode `0700` from the exact
cached `origin/rh` commit requested by the owner:

```text
base commit:
  02468586d710e2cce2360c2bc07e94de6ebdab29
base tree:
  082a460d0ee190ac74a87ab29828d9c867ddff06
branch:
  codex/rh-declare-web3-dependency
worktree:
  /private/tmp/rh-declare-web3-dependency.ch0yCQ/worktree
```

The exact file ceiling is:

```text
requirements.in
requirements.txt
tests/deployment/test_dependency_gate.py
docs/chains/rh/evidence/dependency-security-gate.md
```

No workflow, operator script, migration, H-06 runbook, historical measurement,
PR87 byte, contract, interface, RPC setting, branch setting, or secret was
changed. No RPC, explorer, chain, hardware wallet, Safe service, push, PR,
merge, deployment, or external alert-state mutation was performed.

### Why Web3 is a required direct dependency

The exact base and PR87 head
`4b60cffbb0613efd7e628bdbaa9f644af71dd744` had byte-identical requirement
files and did not declare Web3. The clean pinned RH Python 3.12 validation
environment therefore failed at `from web3 import Web3` while exercising
PR87's defaults snapshot path. The syntax-limited AST inventory described
below measured these ten current-tree production/operator files using its
supported import forms:

```text
migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py
migrations/base-mainnet/2026080701_CcipWire.py
migrations/robinhood-mainnet/0001_Registries.py
migrations/robinhood-mainnet/0009_RedeployStaleContracts.py
migrations/robinhood-mainnet/0010_RedeployLedger.py
migrations/robinhood-mainnet/2026080701_CcipWire.py
scripts/ledger_signing_smoke.py
scripts/prepare_defaults.py
scripts/utils/ledger_account.py
scripts/utils/safe_account.py
```

These are known production/operator callers, not one optional test extra. The
list is a bounded current-tree measurement, not whole-program Python import
reachability. An exact main-lock pin gives local developers, CI, migrations,
and operator scripts one reproducible environment. A separate ops lock would
duplicate and drift the same Vyper/Boa/eth graph, while replacing Web3 in ten
historical and current callers would be a larger behavioral change. The
smallest reviewed fix is therefore an exact direct main-lock dependency.

### Pin selection and primary-source security review

The review was refreshed at `2026-08-11T18:42:39Z` using primary official
package and upstream security sources only:

- [PyPI release metadata for Web3 7.16.0](https://pypi.org/pypi/web3/7.16.0/json)
  reported exact version `7.16.0`, `yanked: false`, Python `>=3.8,<4`, and an
  empty release vulnerability list.
- [PyPI's Web3 project page](https://pypi.org/project/web3/) reported `7.16.0`
  as the latest stable release; the newer `8.0.0b3` is a prerelease and was
  not selected.
- [The upstream v7.16.0 release](https://github.com/ApeWorX/web3.py/releases/tag/v7.16.0)
  is a verified release for commit `efbc6eb`.
- The upstream security page and the official GitHub global-advisory API
  returned one Web3 advisory,
  [GHSA-5hr4-253g-cpx2 / CVE-2026-40072](https://github.com/advisories/GHSA-5hr4-253g-cpx2).
  Its stable affected range is `>=6.0.0b3,<7.15.0`, and `7.15.0` is the first
  stable patched version. The issue is default-on CCIP Read SSRF.

Consequently, `web3==7.12.0` is rejected even though it passed an earlier
local compatibility probe. Exact `web3==7.16.0` is the latest non-yanked
stable Python 3.12-compatible release, is beyond the advisory's stable patch
boundary, and passed the repository compatibility checks below. This review
does not claim future advisories cannot appear.

### Deterministic seeded resolution

Two independent mode-`0700` disposable resolver environments used exact
CPython `3.12.0`, interpreter SHA-256
`d23fa2c326127c9590d097603f105d69e68774968f46246fc7a8a80103600765`,
pip `23.2.1`, pip-tools `7.4.1`, build `1.5.0`, Click `8.4.2`, packaging
`26.3`, pyproject-hooks `1.2.0`, setuptools `84.0.0`, and wheel `0.47.0`.
Each resolver had its own private cache and its own copy of the exact old
output lock. Both used public `https://pypi.org/simple` only, with no extra or
private index:

```text
PIP_CONFIG_FILE=/dev/null
PIP_INDEX_URL=https://pypi.org/simple
PIP_EXTRA_INDEX_URL=
PIP_NO_CACHE_DIR=1
pip-compile \
  --cache-dir=PRIVATE_DISPOSABLE_CACHE \
  --index-url=https://pypi.org/simple \
  --no-emit-index-url \
  --output-file=requirements.txt requirements.in
```

The truthful generated header remains:

```text
#    pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in
```

One non-authoritative preflight mistakenly passed the display-only header
value `--cert=None` back to pip-tools. It stopped before resolution with
`OSError: Could not find a suitable TLS CA certificate bundle, invalid path:
None` and did not change the seeded output. The two authoritative runs used
the documented invocation above and completed in 19.29 s and 11.49 s wall.

Both candidate inputs and generated locks were byte-identical:

| Artifact | Old RH SHA-256 | Candidate SHA-256 |
|---|---|---|
| `requirements.in` | `1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9` | `77768a6e25a4eac86afa88492c5e21d8609c3c5aee469846067e5c8c2b896e72` |
| `requirements.txt` | `214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010` | `3a75970898ff917f508c8ac40046d41eee91646bc83af8bb87d0fd7217e3e569` |
| `tests/deployment/test_dependency_gate.py` | not an input to resolution | `06433cf502c3cb46f82757f2f6c8f137b0e350bdecc6d79426000033d24320e3` |

Normalized comparison found zero version change among the 92 existing lock
pin lines. The candidate adds exactly eleven distributions:

```text
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
frozenlist==1.8.0
multidict==6.7.1
propcache==0.5.2
pyunormalize==17.0.0
types-requests==2.33.0.20260712
web3==7.16.0
websockets==15.0.1
yarl==1.24.5
```

Every remaining literal lock change is a resolver annotation adding Web3 or
one of those eleven packages to an existing package's `via` list. Neither
input nor lock contains a direct URL, VCS URL, editable path, find-links,
extra index, or private index.

### Fresh installation, size, and advisory evidence

Separate fresh mode-`0700` CPython `3.12.0` environments installed the exact
old and candidate locks from public PyPI with `--no-cache-dir`. These are
single cold-install samples, not performance benchmarks:

| Measurement | Old RH lock | Candidate lock | Delta |
|---|---:|---:|---:|
| installation wall time | 20.87 s | 26.26 s | +5.39 s |
| installed distributions, including environment tooling | 93 | 104 | +11 |
| site-packages disk allocation | 219,772 KiB | 234,144 KiB | +14,372 KiB (14.04 MiB) |

Both installations passed `python -m pip check`. The candidate inventory
differed only by the exact eleven-package closure above. No installed
distribution contained `direct_url.json`; install logs resolved artifacts from
public `files.pythonhosted.org` under the explicit public PyPI index.

A separate CPython `3.12.0` / pip `23.2.1` environment installed exact
`pip-audit==2.10.1`. A fresh raw no-ignore audit used `--no-deps`,
`--disable-pip`, no fix, no suppression, and no `--ignore-vuln` flags. Its raw
JSON SHA-256 is
`5581a4c9316cc50901b83dbb31b2af092a22d53d5432c2220492c52ea2942cde`.
All eleven new closure packages, including Web3, had zero findings.

The full unchanged-plus-new lock currently reports five rows in three
pre-existing packages:

| Package | Finding | Current disposition |
|---|---|---|
| Pymdown Extensions `10.21.3` | `PYSEC-2026-3609`, aliases `CVE-2026-61632` and `GHSA-9xwg-3r6f-jcx2`; fixed `11.0.0` | existing `EX-H01-PYMDOWN-B64-01` record |
| Pymdown Extensions `10.21.3` | `PYSEC-2026-3654`, aliases `CVE-2026-67422` and `GHSA-gm37-52c6-37mw`; fixed `11.0.1` | **separate H-01 review blocker**; newly observed and not accepted by this prerequisite |
| pytest `8.4.2` | `PYSEC-2026-1845`; fixed `9.0.3` | existing `EX-H01-PYTEST-01` record |
| Vyper `0.4.3` | `PYSEC-2023-142` | existing authoritative range exclusion; not an exception |
| Vyper `0.4.3` | `PYSEC-2025-33` | existing authoritative range exclusion; not an exception |

The newly published Pymdown ReDoS row is outside the Web3 dependency closure
and exact four-file remediation authority. This candidate does not suppress,
accept, retire, reclassify, or fix it. Its owner must review it separately
before integration; floating Pymdown would violate the zero-drift lock scope
and may conflict with the retained Titanoboa/docs graph.

### Offline regressions and focused validation

Reviewer hardening began from local commit
`202f97c11960ab1a4327dc57aefacf4877c231bc`; this final simplicity amendment
began from local commit `9f37272f3d438a8d4afee880c5f43308beb7c870` in the same fresh
mode-`0700` worktree
`/private/tmp/rh-declare-web3-dependency-hardened.5vIdYY/worktree` on branch
`codex/rh-declare-web3-dependency-hardened`. The two requirement files remain
byte-identical across both amendments. The final test hash is recorded in the
artifact table above; the immediate parent test hash was
`beda706d1bb67e478295e85e849e9276aa97bfa98079ace164fb25538faf2bfa`.

The dependency gate asserts the two candidate requirement hashes and the exact
direct `web3==7.16.0` pin. It defines the complete eleven-package Web3 closure
above as an exact name/version mapping. Every closure member must match the
lock and installed runtime version and must have no `direct_url.json`;
per-package mutation regressions prove that a changed lock version, changed
runtime version, or direct-URL installation record is rejected.

The syntax-limited inventory scans `migrations/**/*.py` and `scripts/**/*.py`.
It rejects a symlink anywhere in those roots and rejects a matching `.py` path
that is not a regular file. Its supported syntax is direct `import web3` /
`from web3`, literal `__import__("web3")`, and literal
`importlib.import_module("web3")`, including ordinary aliases introduced by
the `import importlib as ...` and `from importlib import import_module as ...`
statements themselves. Regressions exercise every supported form and the
symlink/nonregular failures. Equality with the ten-file list is only a drift
check over that supported syntax and is not whole-program Python import
reachability.

Callable assignment such as `loader = importlib.import_module`, builtins
aliases such as `import builtins as python_builtins` followed by
`python_builtins.__import__`, and module-name aliases or other dataflow-derived
call targets are deliberately outside the static inventory. Regression cases
make that boundary visible. Any such construct in operator or migration code
is a code-review trigger for an explicit dependency/inventory update; this
gate does not implement callable assignment, builtins, scope, or dataflow
alias analysis.

The checksum/Keccak regression imports Web3, then replaces `socket.socket`,
`socket.create_connection`, and the low-level DNS lookup functions with
denial hooks. The EIP-55 checksum and Keccak operations complete with an empty
attempt log. That proves only that this executed offline regression made no
socket or DNS attempt; it does not claim that every possible provider
construction or arbitrary Web3 caller is statically prohibited. The gate
still has no subprocess, audit-service, GitHub API, or direct external-query
implementation.

All validation unset RPC/provider credentials, private keys, mnemonic and AWS
credentials; used only an explorer placeholder for collection-time guards;
redirected bytecode, Boa, pytest, XDG, and Hypothesis state to private
disposable paths; and made no live query.

| Validation | Result |
|---|---|
| Web3 `7.16.0` import, `scripts.utils.safe_account` import, EIP-55 checksum, and Keccak smoke | pass; no provider constructed |
| exact PR87 head `4b60cffbb0613efd7e628bdbaa9f644af71dd744`, `tests/test_prepare_defaults_snapshot.py`, addopts cleared | 30 passed in 0.27 s; 2.06 s wall; PR87 worktree clean before and after |
| default lean collection | 3,550 selected of 3,832 total; 282 expected deselections; 7.08 s pytest / 8.93 s wall |
| comprehensive collection with addopts cleared | 4,523 selected of 4,666 total; 143 expected safe-default deselections; 7.26 s pytest / 9.46 s wall |
| dependency gate with addopts cleared | 47 passed in 2.91 s; 4.84 s wall |
| reviewer-hardening Web3 selection | 47 passed, 45 deselected in 0.76 s |
| reviewer-hardened dependency gate with addopts cleared | 92 passed in 3.70 s; 6.35 s wall |
| reviewer-hardened PR87 snapshot recheck at exact `4b60cffbb0613efd7e628bdbaa9f644af71dd744` | 30 passed in 0.29 s; 2.23 s wall; detached worktree clean |
| final simplicity-amendment Web3 selection | 49 passed, 45 deselected in 0.74 s |
| final simplicity-amendment dependency gate with addopts cleared | 94 passed in 3.32 s; 5.51 s wall |
| final simplicity-amendment PR87 snapshot recheck at exact `4b60cffbb0613efd7e628bdbaa9f644af71dd744` | 30 passed in 0.31 s; 2.35 s wall; detached worktree clean |

Web3 import and the PR87 snapshot suite emit one dependency-specific warning:
`websockets.legacy is deprecated` from Websockets `15.0.1`. It is not hidden or
suppressed. It does not affect the synchronous checksum, Keccak, or HTTPProvider
callers under review, but it remains an upstream compatibility/deprecation
signal for a future Web3/Websockets update.

An attempted broad operator-helper import progressed past Web3 and then failed
at `scripts/utils/ledger_account.py:4` because `hid` is also undeclared;
`ledgerblue` and `ledgereth` are further module-level imports in that helper.
Those hardware-wallet dependencies predate this candidate and are not needed
by PR87's snapshot path. They require a separate operator-dependency decision;
this prerequisite does not claim every optional Ledger helper is importable
from the main lock.

### Effectivity and H-06 boundary

This candidate changes the dependency input and lock identities. Therefore no
historical H-06, fork, deployment, or full-suite result recorded against old
lock `214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010`
transfers to the candidate. The focused offline PR87 result proves only that
the missing Web3 dependency is resolved and its 30 snapshots remain stable.

Before merge or deployment reliance, the separate Pymdown H-01 blocker must be
disposed by its owner, this candidate must pass independent review, and the
final integrated PR87-plus-prerequisite tree must repeat the required H-06
qualification under the new lock. No H-06 runbook or historical measurement
was edited to imply otherwise.

## Declared migration runtime dependencies — 11 August 2026

**Status:** Local stacked candidate pending independent review. This section
records dependency declarations only. It is not operative on `rh`, does not
authorize the pending Pymdown exception, and does not transfer H-06,
deployment, or release evidence.

### Bound scope and runtime reachability

The candidate began from exact Web3 prerequisite commit
`85af5fc437367b378d437c6201ce3c31256e8a08` / tree
`70b1707ef1566affcbafe74f65aa8595fe3f48a8` in a fresh mode-`0700`
worktree on branch `codex/rh-declare-runtime-transitives`. Its exact file
ceiling is:

```text
requirements.in
requirements.txt
tests/deployment/test_dependency_gate.py
docs/chains/rh/evidence/dependency-security-gate.md
```

Two migration runtime imports were installed only as transitive dependencies
of Titanoboa's documentation graph:

- `scripts/utils/log.py` directly imports `colorama`; the lock already selected
  `colorama==0.4.6` through MkDocs Material.
- `scripts/utils/migration.py` directly imports `mergedeep`; the lock already
  selected `mergedeep==1.3.4` through MkDocs and MkDocs Get Deps.

The candidate declares exact direct roots `colorama==0.4.6` and
`mergedeep==1.3.4`. It does not change either operator module, migration merge
semantics, logging behavior, Web3 closure, or any selected version. A narrow
AST check reads only those two exact paths and verifies each exact current
absolute import statement in the module's leading import-only block after an
optional module docstring and any `from __future__` imports. It preserves
statement order, imported names, aliases, and repeated occurrences. It ignores
nested or dead-code imports and relative imports. It does not expand the Web3
directory scanner or claim dynamic or whole-program import analysis.

### Reproducible zero-drift lock

Two independent private resolver roots used CPython `3.12.0`, pip-tools
`7.4.1`, the exact candidate input, their own cache, and a seeded copy of the
Web3 output lock. RPC/provider variables, keys, mnemonic, and AWS credentials
were unset. Resolution used public PyPI only:

```text
PIP_CONFIG_FILE=/dev/null
PIP_INDEX_URL=https://pypi.org/simple
PIP_EXTRA_INDEX_URL=
PIP_NO_CACHE_DIR=1
pip-compile \
  --cache-dir=PRIVATE \
  --index-url=https://pypi.org/simple \
  --no-emit-index-url \
  --output-file=requirements.txt requirements.in
```

The documented `CUSTOM_COMPILE_COMMAND` preserved the exact pre-existing
generated-header text; the display-only `--cert=None`, `--client-cert=None`,
and `--pip-args=None` values in that header were not passed to pip. The final
independent regenerations completed in 6.42 s and 6.39 s wall and produced
byte-identical lock SHA-256
`781f6e04d0df489d27772bf68077f39458b7e16a0cbdf62ae10d1a3dfb2b4007`.

| Artifact | Web3 prerequisite SHA-256 | Candidate SHA-256 |
|---|---|---|
| `requirements.in` | `77768a6e25a4eac86afa88492c5e21d8609c3c5aee469846067e5c8c2b896e72` | `56023a39105dd39ce9caad356ea2b11dc3843d7bf72482aa54414163c5f0cfcf` |
| `requirements.txt` | `3a75970898ff917f508c8ac40046d41eee91646bc83af8bb87d0fd7217e3e569` | `781f6e04d0df489d27772bf68077f39458b7e16a0cbdf62ae10d1a3dfb2b4007` |
| `tests/deployment/test_dependency_gate.py` | `06433cf502c3cb46f82757f2f6c8f137b0e350bdecc6d79426000033d24320e3` | `fa1d9269bdbf4d85de0189a9a3d417b56f25ff0a5abfd49114480541477af29d` |

PEP 508-normalized comparison found 103 exact pin lines on each side and zero
package additions, removals, or version changes. The generated header is
byte-identical. The only lock changes are `-r requirements.in` annotations for
Colorama and Mergedeep.

### Focused offline validation and boundaries

The existing clean Web3 CPython `3.12.0` environment already contained the
exact unchanged candidate versions and had no direct-URL metadata for either
package. With generated state redirected to a private external root and RPC,
provider, key, mnemonic, and AWS variables unset:

| Validation | Result |
|---|---|
| `python -m pip check` | pass; no broken requirements; 0.64 s wall |
| import smoke for `scripts.utils.log` and `scripts.utils.migration` | pass from the candidate paths; 1.75 s wall |
| exact PR87 `4b60cffbb0613efd7e628bdbaa9f644af71dd744` defaults snapshots | 30 passed, one preserved Websockets deprecation warning, in 0.43 s; 2.73 s wall; detached worktree clean before and after |
| dependency-gate module compilation | pass; 0.09 s wall |
| complete dependency gate with repository addopts cleared | 95 passed, one preserved Websockets deprecation warning, in 3.46 s; 6.00 s wall |

An initial dependency-gate run passed 94 cases and failed only the new evidence
assertion because the recorded zero-drift sentence wrapped across a Markdown
line. The assertion now normalizes evidence whitespace; the dependency,
runtime-import, and security checks were not loosened.

No package version moved, so this declaration-only candidate does not alter or
refresh the existing advisory dispositions. In particular, the Pymdown ReDoS
finding remains a separate pending, non-operative H-01 blocker; this candidate
does not accept, suppress, extend, or retire it. The Web3 prerequisite remains
stacked and non-operative until its own owner/security/integration conditions
are satisfied. No RPC, explorer query, hardware wallet, Safe service, push,
PR, merge, deployment, settings change, or external alert mutation was
performed.

### Independent-review amendment — exact import boundary

Independent review found that the first candidate helper used `ast.walk()` and
accepted any `ImportFrom` node. That proved syntax presence but also counted
imports nested under dead code and relative imports, which are not the runtime
dependency relationship this declaration is intended to preserve.

The first additive amendment changed only the dependency gate and this
candidate evidence. It iterated the parsed module's top-level statement list,
accepted `ImportFrom` only when `level == 0`, recorded imported names and
aliases, and required exact equality for the current statements:

```text
scripts/utils/log.py
  from colorama import Fore, Style
scripts/utils/migration.py
  from mergedeep import merge
```

Separate negative mutations prove that the same imports under `if False` and
the corresponding one-dot/two-dot relative imports do not satisfy the gate.
The requirement input and lock remain byte-identical at the hashes above; no
runtime/operator file or dependency version changed.

| Amendment validation | Result |
|---|---|
| focused exact-import and two negative-mutation cases | 3 passed, 94 deselected in 0.18 s; 2.92 s wall |
| import smoke for both unchanged candidate modules, RPC and credential variables unset | pass; 1.74 s wall |
| complete dependency gate with repository addopts cleared | 97 passed, one preserved Websockets deprecation warning, in 3.70 s; 6.24 s wall |
| dependency-gate module compilation and `git diff --check` | pass |

This test-boundary correction does not change the Pymdown blocker, Web3
closure, exception status, H-06 boundary, or any deployment authority.

### Second independent-review amendment — leading block and multiplicity

Second independent review found two residual structural gaps. Iterating the
whole module body still accepted a matching import after an unconditional
`raise` or an `if True` block that raises, and a set erased duplicate exact
import occurrences.

The second additive amendment keeps the same two-file scope. The helper now:

1. skips at most one module docstring;
2. skips the following zero or more absolute `from __future__` imports;
3. reads only the consecutive import statements before the first non-import
   module statement;
4. records only absolute imports; and
5. returns an ordered list, so one exact expected occurrence is distinct from
   zero, two, or differently ordered occurrences.

The regression matrix retains nested/dead-code, relative, aliased, and wrong
module/member-name cases. It adds exact failures for a matching import after a
module-level `raise`, after an `if True` block that raises, and for two matching
imports in the leading block. A positive case preserves the optional
docstring/`from __future__` allowance.

This is a structural source assertion only. It proves exact placement and
multiplicity in the leading import block; it does not prove that earlier
imports succeed, that the whole module finishes importing, or general runtime
control flow. Requirement and operator/migration bytes remain unchanged.

| Second-amendment validation | Result |
|---|---|
| focused declared-import matrix | 10 passed, 94 deselected in 0.18 s; 2.57 s wall |
| import smoke for both unchanged modules with RPC and credential variables unset | pass; 1.69 s wall |
| complete dependency gate with repository addopts cleared | 104 passed, one preserved Websockets deprecation warning, in 3.62 s; 6.11 s wall |
| dependency-gate module compilation and `git diff --check` | pass |

The amendment does not change dependency selection, Web3 closure, the pending
Pymdown disposition, exception authority, H-06, deployment, or release state.

## Non-operative dependency-train integration rehearsal — 11 August 2026

**Status:** Local integration candidate only. This record is not an H-01 owner
decision, accepted exception, merge proposal, release approval, H-06
qualification, deployment artifact, or alert-state update. The rehearsal is
bound to exact local `origin/rh` commit
`02468586d710e2cce2360c2bc07e94de6ebdab29`; it changes no authoritative ref.

This candidate rehearses the required semantic order without replacing the
three short landing units:

1. pending Pymdown ReDoS containment at
   `de0d46728b9341d3f0e36554a765d841ef1b0aa7`;
2. reviewed Web3 `7.16.0` closure at
   `85af5fc437367b378d437c6201ce3c31256e8a08`; and
3. reviewed direct Colorama/Mergedeep declarations and final import guards at
   `f6686caa3a79dd44afe4dd23ff703853dc4c325a`.

The last input already descends from the Web3 input. The rehearsal merged its
content with the independent Pymdown input against exact `origin/rh` base
`02468586d710e2cce2360c2bc07e94de6ebdab29` / tree
`082a460d0ee190ac74a87ab29828d9c867ddff06`. The resulting reconciled
pre-record tree was `820f951fb03b9b42f48d5066d754cd6eab3579c3` and changed exactly
`requirements.in`, `requirements.txt`,
`tests/deployment/test_dependency_gate.py`, and this evidence path.

### Intentional shared-surface reconciliation

The Pymdown aliases and `EX-H01-PYMDOWN-REDOS-01` remain in the pending set,
which is disjoint from the operative and retired sets. The Web3 prerequisite's
separate review-blocker assertion also remains: it prevents that prerequisite
from treating the pending H-01 proposal as disposed. The two controls are
complementary. Neither converts the proposal into an operative exception or
represents owner adoption.

All inherited candidate records and their standalone artifact hashes above
remain historical descriptions of those exact candidates. They were not
silently rebound to this composite. The reconciled inherited evidence prefix
immediately before this section has SHA-256
`36bf25ec26f55a3b8e311daf9920e42b471bea9a7b9e402c3150d954fd3f42fa`.
That digest excludes the single Markdown separator line before this heading.
This section alone records the composite identities and results.

### Final lock reproduction and delta

Two isolated mode-`0700` resolver roots used CPython `3.12.0`, pip `23.2.1`,
pip-tools `7.4.1`, build `1.5.0`, Click `8.4.2`, packaging `26.3`,
pyproject-hooks `1.2.0`, setuptools `84.0.0`, and wheel `0.47.0`. Each began
with its own copy of the exact candidate input and seeded output, used its own
private cache, and resolved from public `https://pypi.org/simple` only:

```text
PIP_CONFIG_FILE=/dev/null
PIP_INDEX_URL=https://pypi.org/simple
PIP_EXTRA_INDEX_URL=
PIP_NO_CACHE_DIR=1
CUSTOM_COMPILE_COMMAND='pip-compile --cert=None --client-cert=None --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt --pip-args=None requirements.in'
pip-compile --quiet --cache-dir=PRIVATE --index-url=https://pypi.org/simple --no-emit-index-url --output-file=requirements.txt requirements.in
```

The two authoritative public-PyPI resolutions completed in `19.13 s` and
`19.15 s` wall and reproduced byte-identical output. An earlier sandboxed
attempt could not resolve public-PyPI DNS, stopped at Titanoboa before
producing a resolved output, and is not counted as either authoritative
regeneration.

| Composite artifact | SHA-256 |
|---|---|
| `requirements.in` | `56023a39105dd39ce9caad356ea2b11dc3843d7bf72482aa54414163c5f0cfcf` |
| `requirements.txt` | `781f6e04d0df489d27772bf68077f39458b7e16a0cbdf62ae10d1a3dfb2b4007` |
| `tests/deployment/test_dependency_gate.py` | `1b017ed881dc2468af20fe7181aaccafb5ac64ac4cf484939fa31261ab875d7f` |

Normalized lock comparison against the exact base found 92 prior pin lines
and 103 final pin lines. Every prior pin is unchanged; there are no removals
or version changes. The eleven additions are exactly the reviewed Web3
closure. Colorama `0.4.6` and Mergedeep `1.3.4` were already transitive lock
members, so making them direct roots changes only their `via` annotations.
The direct input and lock contain no direct, VCS, editable, file, private-index,
extra-index, or find-links source.

### Offline rehearsal results

All validation used the exact final lock, unset RPC/provider, private-key,
mnemonic, and AWS credential variables, redirected generated state to
mode-`0700` disposable roots, and made no live query.

| Validation | Result |
|---|---|
| initial composite dependency gate before this record | 115 passed, one preserved Websockets deprecation warning, in 3.59 s |
| final evidence-bound dependency gate and module compilation | 115 passed, one preserved warning, in 3.52 s; 6.07 s wall; compile pass |
| pending Pymdown control, seven root-configuration cases, and five affected Markdown activation cases | 14 passed, 101 deselected in 0.20 s |
| final Web3 selection, including exact closure and network-deny regressions | 49 passed, 66 deselected, one preserved warning, in 0.81 s |
| final runtime-import guard selection | 10 passed, 105 deselected in 0.18 s |
| `python -m pip check` and offline Web3/operator import smoke | pass; no broken requirements and no provider construction |
| exact PR87 head `4b60cffbb0613efd7e628bdbaa9f644af71dd744`, `tests/test_prepare_defaults_snapshot.py` | 30 passed, one preserved warning, in 0.35 s; detached worktree clean before and after |
| default lean collection | 3,550 selected of 3,832 total; 282 expected deselections; 8.17 s |
| addopts-cleared collection with only `fork_qualification` deselected | 4,591 selected of 4,734 total; 143 expected safe-default deselections; 8.72 s |

The first collection attempt did not call Boa's cache setter and failed closed
on two attempts to use the inaccessible default user cache. The recorded
collections explicitly called `boa.interpret.set_cache_dir` before invoking
pytest and completed cleanly. This execution correction changed no repository
byte.

### Landing, qualification, and rollback boundary

This composite is an integration rehearsal, not a request to publish a single
large pull request. Preserve the three short units and their review history.
Pymdown containment remains pending owner authorization; downstream Web3 and
runtime-declaration candidates cannot treat it as accepted or bypass that
landing gate. If any input changes, discard this rehearsal result and rebuild
the train from the newly reviewed exact commits.

The lock identity differs from authoritative `rh`, so every H-06 result tied
to the old lock requires prescribed requalification after an authorized final
integration. PR87 snapshots and collection prove bounded compatibility only;
they do not establish downstream remediation, fork qualification, deployment
readiness, or release authority. No push, PR, merge, settings change, RPC,
deployment, device action, or owner acceptance occurred.

## Authorized Web3 and runtime dependency candidate — 11 August 2026

This latest section supersedes only the publication disposition of the
non-operative rehearsal immediately above. Mick Hagen's explicit H-01 owner
authorization is recorded in the controlling transition section, and the
containment branch remains the required integration parent. The historical
standalone and rehearsal records remain exact descriptions of their named
candidate bytes and checkpoints.

The bounded follow-on candidate combines two already independent-reviewed
dependency units because they share the same four files and exact lock:

1. declare `web3==7.16.0` and its reviewed eleven-distribution public-PyPI
   closure; and
2. declare already-locked `colorama==0.4.6` and `mergedeep==1.3.4` as honest
   direct runtime inputs without changing either installed version.

The exact scope remains `requirements.in`, `requirements.txt`,
`tests/deployment/test_dependency_gate.py`, and this evidence record. No
contract, migration, operator implementation, workflow, generated file,
manifest, deployment, or alert state changes. The branch may be published and
reviewed in parallel, but it must not integrate before the exact owner-
authorized containment bytes are authoritative in `rh`.

The resulting input and lock identities remain:

```text
requirements.in
  56023a39105dd39ce9caad356ea2b11dc3843d7bf72482aa54414163c5f0cfcf
requirements.txt
  781f6e04d0df489d27772bf68077f39458b7e16a0cbdf62ae10d1a3dfb2b4007
```

The normalized lock retains every prior version, adds exactly the reviewed
eleven-package Web3 closure, and changes Colorama/Mergedeep only from
transitive to direct-input provenance. Public-source, exact-closure,
direct-URL, supported import-syntax, low-level network-deny, direct-runtime-
import, and Pymdown reachability controls remain fail closed.

Fresh validation of the final stacked bytes is required before publication.
The candidate does not transfer H-06 qualification, authorize PR 87, release,
deployment, connected-device use, RPC access, or alert dismissal. Any
dependency, resolver, containment, or scanner change invalidates this record
and requires a new bounded review.
