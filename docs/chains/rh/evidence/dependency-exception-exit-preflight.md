# H-01 bounded-exception exit preflight

**Status:** Historical documentation-only preflight plus the owner-authorized
three-file transition record at the end of this document. The target
retirement split becomes effective only when the exact independently approved
transition commit is integrated into authoritative `rh`; an uncommitted or
feature-branch candidate does not itself retire an exception.

**Evidence date:** 25 July 2026

**Reconciliation date:** 26 July 2026

**Historical preflight baseline commit:**
`332ae2bc8e0ce4b694766d6d20759295d9267ec3`

**Historical preflight baseline tree:**
`f67dc91e47331785837de879b6557b285aec3b1b`

**Current transition baseline commit:**
`d62777646cba1ae448fb9e26519c6fa295f437df`

**Current transition baseline tree:**
`01b1d7c8fc7bdf5163e20efe1f61b53db2b01a61`

**Historical isolated branch:** `codex/rh-h01-exception-exit-preflight`

**Historical isolated worktree:**
`/Users/wigglez/dev/ripe-protocol-h01-exception-exit-preflight`

## Decision summary

The minimum-change recommendation is not a five-package immediate upgrade.
The five exceptions have different reachability and compatibility profiles and
should not be forced into one resolver or reviewer event.

| Exception | Current disposition | Recommended timing | Smallest candidate | Recommendation |
|---|---|---|---|---|
| `EX-H01-CLICK-01` | The affected `click.edit()` function remains unreachable, but integrated H-02 materially expanded Click use inside all three allowlisted CLI files. The exception's “any new Click import/call surface” invalidation trigger therefore fired even though the mechanical gate still passes. | **Immediate owner/security disposition is mandatory.** | `click==8.3.3` | Either approve a current-baseline replacement exception immediately or authorize the approval-safe bundle containing Click `8.3.3`. Until one occurs, do not rely on the old Click exception for deployment rehearsal or untrusted/shared-host CLI use. |
| `EX-H01-PYTEST-01` | Applicable whenever pytest runs on Unix. The exact pinned profile and S1 gate remain unchanged. Private-basetemp/single-tenant controls remain available but are procedural, not repository-wide enforced. | 15 August review; never later than hard expiry. | `pytest==9.0.3` | Retain `8.4.2` until the scheduled review unless a compatible Vyper/Titanoboa path is approved sooner. Do not cross to pytest 9 merely to clear the finding while Vyper 0.4.3's optional test/dev metadata still requires `pytest<9`. |
| `EX-H01-PYGMENTS-01` | The affected Archetype/`AdlLexer` remains unreachable from current repository source and configuration. | Approval-safe bundle, after explicit owner authorization. | `Pygments==2.20.0` | Include exact `2.20.0` in the approval-safe bundle; the later study resolved and validated it without transitive version change. |
| `EX-H01-PYMDOWN-SNIPPETS-01` | No repository docs build, MkDocs configuration, Pymdown import, snippets activation, or untrusted Markdown rendering path exists. The later isolated study resolved and validated exact `10.21.3`. | Approval-safe bundle, after explicit owner authorization. | `pymdown-extensions==10.21.3` | Include exact `10.21.3` in the approval-safe bundle. It retires only the Snippets exception; the b64 exception remains active. |
| `EX-H01-PYMDOWN-B64-01` | No repository docs build, Pymdown import/configuration, b64 activation, or untrusted Markdown rendering path exists. Pymdown `11.0.0` is the first patch but is not resolver-valid in the current Titanoboa graph. | **Retain; separate dependency-graph study required.** | None inside the current graph | `mkdocs-material==9.5.41`, pinned through `titanoboa==0.2.7`, requires `pymdown-extensions>=10.2,<11`; the exact `11.0.0` attempt produced `ResolutionImpossible`. Retain the b64 exception unless a separately authorized Titanoboa/docs-graph change becomes resolver-valid and fully approved. |

The reconciled decision sequence is:

1. obtain an immediate owner/security disposition for the already-invalidated
   Click exception;
2. if separately authorized, implement and independently review the
   approval-safe bundle: Click `8.3.3`, Pygments `2.20.0`, and Pymdown
   Extensions `10.21.3`, while retaining pytest `8.4.2` and the Pymdown b64
   exception;
3. keep pytest `9.0.3` as a separate S1/Vyper/Track 6 owner decision; and
4. keep Pymdown b64 outside the current implementation boundary until a
   separate Titanoboa/docs-graph study produces a resolver-valid candidate.

No implementation is authorized by this preflight. A future approval-safe
bundle must recreate the later study's exact three-version delta and stop on
any transitive or unrelated lock drift.

### Minimum-change and no-change alternatives

| Exception | Minimum-change exit | No-change alternative | No-change limit and residual risk |
|---|---|---|---|
| `EX-H01-CLICK-01` | Trial only `click==8.3.3`, hold every unrelated lock version, and re-prove H-02. | Make no package change only if owner/security issues a replacement exception against the exact current source and controls. | The old exception cannot be reused because its call-surface trigger fired. A replacement may run only to its new explicit review/expiry and leaves the risk that future allowlisted Click APIs are not mechanically detected. |
| `EX-H01-PYTEST-01` | Trial only `pytest==9.0.3` after resolving or explicitly accepting the Vyper optional-metadata conflict and reapproving S1. | Retain exact `8.4.2` under fresh private per-command basetemps, trusted tests/plugins, a single-tenant runner, and a fresh explicit disposition. | Procedural controls can fail and pytest remains directly reachable. No-change may not pass hard expiry without a newly approved exception; it does not authorize rehearsal or merge after expiry. |
| `EX-H01-PYGMENTS-01` | Trial only `Pygments==2.20.0` with output/lexer checks. | Retain exact `2.19.2` under the no-Archetype/no-untrusted-highlight/no-docs-build controls until the scheduled review. | Dynamic or plugin lexer selection is not exhaustively gate-enforced. Any new lexer or untrusted-content path ends no-change authority immediately. |
| `EX-H01-PYMDOWN-SNIPPETS-01` | Use exact `pymdown-extensions==10.21.3` in the approval-safe bundle; close only Snippets and retain b64. | Retain exact `10.16.1` with snippets disabled, no docs build, no untrusted Markdown, and current source/config scanning. | Programmatic activation is not mechanically covered. Any snippets import/activation, docs pipeline, or untrusted Markdown ends no-change authority. |
| `EX-H01-PYMDOWN-B64-01` | No resolver-valid package-only exit exists in the current graph. A future candidate requires a separately authorized Titanoboa/docs-graph study. | Retain the b64 exception under disabled-extension/no-docs-build/no-untrusted-Markdown controls. | Pymdown `11.0.0` cannot resolve against `mkdocs-material==9.5.41`. Any b64/Pymdown activation or docs pipeline invalidates retention and blocks the workflow; it does not authorize forcing an invalid graph. |

No-change means no dependency, source, or test mutation. It never means silent
renewal: it requires an explicit still-valid exception and is bounded by the
earliest reachability/control trigger, scheduled review, or hard expiry.

## Authority and evidence boundary

This preflight uses only committed public repository evidence and current
repository source. It does not access the retained private H-01 alert/audit
records and does not make a fresh GitHub alert-state claim.

The controlling H-01 record says:

- Candidate A is integrated with exact direct-input and lock hashes
  `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d`
  and
  `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce`;
- all five exceptions retain a scheduled security review on 15 August 2026;
- all five hard-expire at `2026-08-31T23:59:59Z`;
- the earlier of a finding-specific invalidation trigger or hard expiry ends
  the authorization;
- expiry blocks deployment rehearsal and merge; and
- candidate-lock remediation and GitHub-observed alert closure are distinct.

The later version-exact feasibility study supersedes this preflight's original
Pymdown resolver assumption. Its reviewed report was preserved on local branch
`rh-track-7-h1-exception-retirement` at commit
`37a85b8078f798466f0a315b273a667ad72b02e3`, with reviewed report SHA-256
`0309004064b3642ab18b848c7935711a3ea3346748b0d601e10271639a31c04d`.
The study established:

- an approval-safe exact bundle of Click `8.3.3`, Pygments `2.20.0`, and
  Pymdown Extensions `10.21.3`, with pytest held at `8.4.2`;
- no transitive version change in that valid candidate;
- continued retention of the Pymdown b64 exception; and
- `ResolutionImpossible` for Pymdown Extensions `11.0.0` because unchanged
  `titanoboa==0.2.7` pins `mkdocs-material==9.5.41`, which requires
  `pymdown-extensions>=10.2,<11`.

Those candidate results are feasibility evidence, not dependency approval,
integrated lock bytes, or GitHub/Dependabot alert closure. This reconciliation
does not query alert state and makes no claim that any alert closed, changed,
or disappeared.

Current file identities are:

| Path | SHA-256 |
|---|---|
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa` |
| `docs/chains/rh/evidence/dependency-security-gate.md` | `5cb0d37aa50ab66b13d8389eecafd2bcd1f47dd7a3fd6fb6648e34470393fa87` |
| `docs/chains/rh/evidence/network-profile-cli-implementation.md` | `79cf2f7e5c362b8880f2c460abac946126bf2f329425a82e3c8f5bd4da9a8de7` |
| `config/network_profiles.py` | `9c19d237eaa049a9d521fc3ab8ef868e6ee35ab6ba48c45e61180fa2daf8c42a` |
| `scripts/migrate.py` | `6401e3fe35f29981378bb187a4070b1b0a75e6f7105204269e65aeef4aa6a12c` |
| `scripts/console.py` | `a7f0c2b15db0634398dbf975bd40fe5cb449a96e7da6ff5a1c9159df75ec5f6a` |
| `scripts/verify.py` | `5db7f0f50d509ca96560a22534647e0c36109dc8232a1bc790c8e7ddd4237edb` |

The post-H-01 first-parent integration sequence relevant to this preflight is:

```text
575d47b  merge: integrate Track 7 H-01 dependency security
26eb3a7  Record H-01 post-integration K-02 evidence
6c30526  merge: integrate Track 7 H-02 network profiles and CLI safety
e1f14dd  merge: integrate Track 8 M0 closure
cb3fe73  merge: integrate H-02 post-integration corrections
332ae2b  docs: add Track 8 M1 exact-receipt brief
```

Between H-01 integration and the current baseline, the only executable Python
or activation-capable configuration changes are the H-02 registry, its three
CLI/helper surfaces, and its three test modules. Requirements, the compiled
lock, the H-01 gate test, S1 source, and S1 exact versions did not change.

## Current source reachability and control audit

The current dependency gate's five reachability cases pass:

```text
5 passed, 11 deselected
```

That result proves the current scanner sees no present violation and that its
four mutation shapes still fail closed. It is not an exact-environment H-01
gate result. The shared ambient environment is not an exact Candidate A
installation:

```text
cbor2           expected 5.9.0 installed 5.7.0
idna            expected 3.15  installed 3.10
python-dotenv   expected 1.2.2 installed 1.1.0
requests        expected 2.33.0 installed 2.32.5
urllib3         expected 2.7.0 installed 2.5.0
wheel           expected 0.46.2 installed 0.45.1
```

Accordingly, the complete gate produced `15 passed, 1 failed`; the failure was
the expected exact-runtime mismatch at the first package above. `pip check`
reported no broken requirements, but that does not make the ambient
environment lock-exact. No package was installed or changed to alter this
result.

The reachability controls have these exact strengths and gaps:

| Surface | Current repository fact | Mechanical control | Residual enforcement gap |
|---|---|---|---|
| Click | Direct imports exist only in `scripts/migrate.py`, `scripts/console.py`, and `scripts/verify.py`; no `click.edit()` or editor launch exists. | AST scan rejects Click imports outside those three files and rejects direct/aliased `click.edit`. | It allows any other new Click API inside the three allowlisted files. H-02 added `ClickException`, `echo`, `IntRange`, choices, options, and commands without tripping the gate, so the exception's broader “new call surface” trigger is not mechanically enforced. |
| Pygments | No repository production/test import selects `AdlLexer`, Archetype, `adl`, or `archetype`; only the H-01 mutation fixture contains such source as a string. | AST/config scan rejects direct or aliased `AdlLexer`/Archetype use and literal `get_lexer_by_name("adl"|"archetype")`. | Dynamic lexer names or plugin-based selection are not exhaustively proven absent by the gate; the current repository-wide source search found none. |
| Pymdown snippets | No MkDocs file, Pymdown import, snippets activation, or docs-build command exists. | Configuration scan rejects `pymdownx.snippets` in `.cfg`, `.ini`, `.json`, `.toml`, `.yaml`, or `.yml`. | Python-source Pymdown imports or programmatic extension-name construction are not scanned mechanically. The current repository-wide source search found none. |
| Pymdown b64 | No MkDocs file, Pymdown import, b64 activation, or docs-build command exists. | Configuration scan rejects `pymdownx.b64` in the same configuration suffixes. | The same Python/programmatic activation gap applies. |
| pytest | pytest is directly reachable as the repository-wide validation runner; S1 requires exact `8.4.2`. No committed GitHub workflow exists. | Exact lock/runtime/S1 assertions fail closed. H-01 records private mode-`0700` per-command basetemps and single-tenant execution as controls. | The repository has no universal pytest wrapper that enforces a new private basetemp for every invocation. Several documentation command examples omit the flag. Compliance remains an operator/reviewer obligation. |

## Exception analysis

### `EX-H01-CLICK-01`

**Applicability and reachability.** Click `8.2.1` is inside the affected
`<8.3.3` range. The vulnerable `click.edit()` behavior is not reachable from
current source. Click itself is deployment-tooling reachable: all three H-02
CLIs use commands/options, and current code also uses `ClickException`,
`Choice`, `IntRange`, `echo`, and `prompt`.

**Compensating controls.** The no-`click.edit`, no untrusted plugin, no
untrusted `EDITOR`/`VISUAL`, owner-controlled host, and source-scan controls
remain factually true. They are sufficient for the affected function's current
non-reachability, but the scan does not fully enforce the exception's stated
“any new call surface” trigger.

**Integrated invalidation.** H-02 changed every allowlisted Click file after
H-01. Relative to H-01 integration, current source adds or changes Click
choices, options, exceptions, output, integer-range validation, and call
paths. The explicit invalidation trigger fired. This is a procedural expiry of
the old authorization, not evidence that `click.edit()` became reachable.

**Smallest candidate.** Add exact direct pin `click==8.3.3` and regenerate from
the frozen current lock. No unrelated package version may change.

**Compatibility.**

- Vyper and S1 compiler behavior: no direct effect expected.
- Titanoboa: Click is transitive through Titanoboa's MkDocs stack; imports and
  metadata still require clean-environment proof.
- pytest: no runner-version change, but all tests must remain green.
- H-02: highest compatibility surface; CLI parsing, choices, help wrapping,
  exceptions, prompts, `CliRunner`, and captured output must be re-proved.
- complete suite: mandatory because Click is directly used by deployment
  entrypoints and indirectly by documentation tooling.

**Timing.** Immediate owner/security re-review is mandatory because the
invalidation trigger already occurred. The recommended implementation path is
the approval-safe three-package bundle containing Click `8.3.3`. A replacement
current-baseline Click exception is only the no-package-change alternative; it
must be explicit and bounded and does not make a Click-only trial preferable
to the bundle. Until either disposition is approved, do not use the old
exception for H-02 CLI use or rehearsal.

**Retain versus upgrade risk.** Retention has low exploitability while
`click.edit()` and untrusted editor/plugin inputs remain absent, but relying on
an already-invalidated exception is a governance failure. Upgrade risk is
concentrated in the newly integrated H-02 CLI behavior and is materially
larger than the vulnerable-function reachability; the approval-safe bundle's
exact H-02 validation keeps that risk reviewable.

**Rollback and stop.** Roll back by recreating the prior exact lock, never by
in-place downgrade. Stop on any extra lock delta, H-02 help/output/choice
change, new Click import or plugin, `click.edit` reachability, raw RPC leakage,
test skip/xfail/warning suppression, or full-suite regression.

### `EX-H01-PYTEST-01`

**Applicability and reachability.** pytest `8.4.2` is inside the `<9.0.3`
affected range and is directly reachable on every test run. It is not deployed
contract runtime. Exposure is local Unix temporary-directory handling.

**Compensating controls.** Trusted tests/plugins, owner-controlled
single-tenant runners, a fresh mode-`0700` task parent, a dedicated
`--basetemp` child for each invocation, immediate exact-parent cleanup, serial
execution, and no skip/xfail/warning suppression remain the approved controls.
H-02's recorded validation followed those controls. The current source and
lock preserve exact pytest `8.4.2`, Titanoboa `0.2.7`, Vyper `0.4.3`, and S1's
exact equality gate.

**Integrated invalidation.** No pytest, Vyper, Titanoboa, Python, plugin, or S1
profile version changed after H-01. H-02 and later tracks expanded the trusted
test corpus, but did not introduce an untrusted-test or shared-runner path.
No version/profile invalidation trigger is established. The absence of a
repository-wide basetemp wrapper remains a pre-existing control-discipline
risk.

**Smallest candidate.** Change the existing direct pin to
`pytest==9.0.3`. Do not substitute a later pytest release without a new
release-note, resolver, and compatibility decision.

**Compatibility.**

- Vyper: **blocking metadata conflict.** Vyper `0.4.3` optional `test` and
  `dev` metadata requires `pytest>=8,<9`. The protocol lock resolves pytest 9
  only because those extras are not selected; resolver success is not support
  evidence.
- Titanoboa: `0.2.7` has no pytest upper bound, but its fixtures, compiler
  wrapper, pytest-cov interaction, and teardown behavior require proof.
- pytest: major-version changes affect collection, configuration, plugins,
  fixtures, warnings, assertion rendering, exception groups, and teardown.
- H-02: all current profile/secret/Base CLI tests and their Click output
  assertions must be re-proved.
- S1: the unchanged test must first fail on exact `8.4.2`; only then may the
  exact expectation change to `9.0.3`, followed by complete primitive,
  profile, isolation, and artifact proof.
- complete suite: mandatory serially, including current collection equality
  against the candidate's own frozen count.

**Timing.** Do not upgrade immediately on current evidence. Reassess at the
15 August review with a primary-supported Vyper/Titanoboa path or an explicit
owner/security/Track 6 acceptance of the optional-metadata conflict. If no
compatible, approved path exists by `2026-08-31T23:59:59Z`, the exception
expires and rehearsal/merge remains blocked; the deadline does not authorize a
forced unsupported upgrade.

**Retain versus upgrade risk.** Retention risk is a local cross-user
denial-of-service/possible privilege effect if private single-tenant basetemp
controls fail. Upgrade risk is repository-wide and includes knowingly
departing Vyper's optional supported test profile, invalidating S1, and
changing all H-02 and protocol test semantics. On current evidence, controlled
retention until the scheduled review is the smaller risk.

**Rollback and stop.** Roll back by recreating the exact pytest `8.4.2`
environment from the prior lock and rerunning the old gate. Stop on a resolver
delta beyond pytest, any need to loosen S1, Vyper/Titanoboa metadata drift,
collection/plugin/fixture/warning/teardown drift without explicit review,
artifact inequality, or any skipped/suppressed test.

### `EX-H01-PYGMENTS-01`

**Applicability and reachability.** Pygments `2.19.2` is inside the `<2.20.0`
affected range. Pygments is transitive through IPython, pytest, Rich, and
Titanoboa's documentation stack. The vulnerable Archetype `AdlLexer` is not
selected by current repository source or configuration.

**Compensating controls.** No `AdlLexer`/Archetype selection, no untrusted
highlighted content, no docs build, owner-controlled tooling, and
repository-wide source/config scanning remain intact. Dynamic/plugin selection
is a residual limitation, but no such path is present.

**Integrated invalidation.** H-02 added no Pygments import, lexer selection,
docs build, or untrusted content path. Later integrated changes are
documentation or H-02 source/tests without affected-lexer use. No trigger
fired.

**Smallest candidate.** Add exact direct pin `Pygments==2.20.0`; regenerate
with no other version delta.

**Compatibility.**

- Vyper: no direct effect.
- Titanoboa: transitive console/docs/Rich output may change.
- pytest: assertion and terminal rendering may change even though the runner
  version stays fixed.
- H-02: console/help output and captured redaction assertions are the relevant
  surface.
- S1: exact runtime versions remain unchanged; diagnostics still need review.
- complete suite: mandatory; terminal-output differences must not be hidden by
  brittle normalization.

**Timing.** Include exact `2.20.0` in the approval-safe three-package bundle
only after explicit owner/security authorization. Re-review sooner if a
Pygments import, Archetype selection, untrusted highlighted content, or docs
build becomes reachable.

**Retain versus upgrade risk.** Current exploitability is low because the
affected lexer is absent and the finding is local denial of service. Upgrade
risk is low-to-moderate output/lexer churn across IPython, pytest, Rich, and
Titanoboa. The later exact bundle evidence bounds that risk without authorizing
implementation.

**Rollback and stop.** Recreate the prior `2.19.2` lock/environment. Stop on
any extra resolver change, console/redaction assertion drift, new lexer
activation, unexpected test-output semantics, or full-suite regression.

### `EX-H01-PYMDOWN-SNIPPETS-01`

**Applicability and reachability.** Pymdown Extensions `10.16.1` is inside the
snippets affected range. It is transitive through
`titanoboa -> mkdocs-material -> pymdown-extensions`. No repository docs
configuration, Pymdown import, snippets activation, Markdown build, or
untrusted Markdown rendering path exists.

**Compensating controls.** Do not enable `pymdownx.snippets`, do not process
untrusted Markdown, do not run docs builds with readable secrets, and scan for
activation. Those factual controls remain intact. The mechanical scanner
covers configuration but not Python programmatic activation; the present
manual source scan closes only the current-baseline observation.

**Integrated invalidation.** No post-H-01 integrated code/configuration enables
snippets or a documentation pipeline. No trigger fired.

**Smallest candidate.** `pymdown-extensions==10.21.3` fixes this finding alone,
but it remains affected by `EX-H01-PYMDOWN-B64-01`.

**Compatibility.** There is no Vyper, pytest-runner, H-02, or S1 direct
behavioral dependency. Titanoboa's MkDocs/material documentation stack is the
parent compatibility surface. The later feasibility study resolved
`10.21.3` with every transitive held, passed `pip check`, and found the
Snippets traversal proof blocked while the b64 proof remained vulnerable. A
future implementation still requires a fresh lock-specific complete suite,
import checks, and offline Snippets traversal-negative test.

**Timing.** Include exact `10.21.3` in the approval-safe three-package bundle
only after explicit owner/security authorization. Close only the Snippets
exception and retain the b64 exception. Any new docs pipeline, snippets
activation, untrusted Markdown, or Pymdown Python import requires immediate
stop and remediation.

**Retain versus upgrade risk.** Retention risk is currently dormant but could
become file disclosure if an untrusted docs build is introduced. Exact
`10.21.3` leaves b64 vulnerable but is resolver-valid, removes the Snippets
finding in the later no-ignore audit, and changed no transitive version.
Upgrade risk is bounded Markdown behavior churn; b64 residual risk remains
explicit rather than being hidden behind an unresolved joint-exit claim.

**Rollback and stop.** Recreate `10.16.1` from the prior lock. Stop on a major
resolver delta beyond Pymdown, MkDocs/material incompatibility, traversal-test
failure, output outside a disposable root, any readable-secret dependency, or
full-suite regression.

### `EX-H01-PYMDOWN-B64-01`

**Applicability and reachability.** Pymdown Extensions `10.16.1` is inside the
`<=10.21.3` affected range. No repository `pymdownx.b64`, docs configuration,
Pymdown import, Markdown renderer, or untrusted Markdown path exists.

**Compensating controls.** Do not enable b64, do not render untrusted Markdown,
do not run docs builds with readable secrets, and scan for activation. Current
source satisfies the controls; the Python-programmatic scanner gap remains.

**Integrated invalidation.** No post-H-01 integrated source/configuration
enables b64 or a docs build. No trigger fired.

**Smallest candidate.** No resolver-valid candidate exists inside the current
graph. `pymdown-extensions==11.0.0` is the first recorded b64 patch, but the
later exact resolver attempt stopped with:

```text
pymdown-extensions==11.0.0
mkdocs-material==9.5.41 -> pymdown-extensions>=10.2,<11
```

`mkdocs-material==9.5.41` is pinned through unchanged
`titanoboa==0.2.7`; no Pymdown 11 lock or candidate environment exists.

**Compatibility.**

- Vyper, pytest runner, H-02, and S1: no current candidate exists to validate.
- Titanoboa/MkDocs Material: the current graph rejects Pymdown 11; changing
  Titanoboa or its docs graph is a separate dependency and S1 approval event.
- docs behavior: Pymdown 11 is a major-version boundary and cannot be assessed
  as current-graph compatibility evidence without a valid lock/environment.
- complete suite and artifact proof become mandatory only after a separately
  authorized graph study produces an exact resolver-valid candidate.

**Timing.** Retain the b64 exception. Do not trial or recommend Pymdown 11
inside the current graph. A separate Titanoboa/docs-graph feasibility study
requires explicit authorization. If b64, any docs build, programmatic Pymdown
activation, or untrusted Markdown becomes reachable, the exception
invalidates and the workflow stops; that trigger does not authorize forcing an
unresolved dependency graph.

**Retain versus upgrade risk.** Current exploitability is dormant; activation
could disclose readable image-extension files outside the intended base path.
Retention remains bounded by reachability controls and expiry. Forcing
Pymdown 11 would violate the current Titanoboa dependency graph and has
unbounded installation, docs-tooling, S1, and suite risk. On current evidence,
explicit retention is safer than treating an unresolved version as viable.

**Rollback and stop.** There is no current implementation to roll back. A
future graph study must start from the approved lock in a disposable
environment and stop on any unapproved Titanoboa/MkDocs/Pymdown transitive
change, resolver failure, import failure, traversal escape, unexpected
filesystem read, or suite/artifact regression.

## Cross-package compatibility matrix

| Candidate | Vyper | Titanoboa | pytest behavior | H-02 | S1 | Complete suite |
|---|---|---|---|---|---|---|
| Click `8.3.3` | No direct compiler effect | MkDocs transitive metadata/import | Runner held | **High:** all three CLIs | Versions held; diagnostics check | Mandatory |
| pytest `9.0.3` | **High:** optional `test`/`dev` says `<9` | Fixtures/plugins/pytest-cov | **Major boundary** | **High:** 99 H-02 cases and Click runner assertions | **High:** intentional exact failure and reapproval | Mandatory serial |
| Pygments `2.20.0` | No direct compiler effect | IPython/Rich/MkDocs output | Terminal/assertion rendering | Console/help capture | Versions held; diagnostic text check | Mandatory |
| Pymdown `10.21.3` | No direct compiler effect | Resolver-valid with `mkdocs-material==9.5.41`; Snippets only | Runner held at `8.4.2` | No direct path | Versions held | Later study green outside expected lock-policy gate; fresh implementation replay mandatory |
| Pymdown `11.0.0` | No candidate: `ResolutionImpossible` | **Blocked by `mkdocs-material`'s Pymdown `>=10.2,<11` requirement** | Not installed | Not run | Not run | No compatibility claim |

No candidate authorizes a Vyper or Titanoboa change. If any candidate cannot
resolve while holding `vyper==0.4.3`, `titanoboa==0.2.7`, and all unrelated
versions, stop and return to owner/security review.

## Exact future file ownership

A future exception-exit implementation may own only:

| Path | Ownership rule |
|---|---|
| `requirements.in` | Add or change only the exact direct pin for the active candidate group. |
| `requirements.txt` | Deterministically regenerate from the approved input and frozen prior lock; never hand-edit. |
| `tests/deployment/test_dependency_gate.py` | Update selected/held/residual ledgers, close only the active exception(s), strengthen the Click/Pymdown reachability gaps, and add package-specific offline behavior tests. |
| `docs/chains/rh/evidence/dependency-security-gate.md` | Append exact current-baseline resolver/audit/validation/approval evidence; do not rewrite historical records. |
| `docs/chains/rh/evidence/dependency-exception-exit-preflight.md` | Append the implemented group, results, remaining exceptions, and next review state. |
| `tests/clock/test_clock_profiles.py` | **Conditional pytest group only:** replace exact `8.4.2` expectations with exact `9.0.3` after recording the intentional unchanged-test failure. No other S1 behavior may change. |

The future slice does not own H-02 production source, H-02 tests, Vyper,
Titanoboa, contracts, migrations, histories, ABIs, configuration, CI, or
another track's evidence. H-02 tests are mandatory validation consumers, not
editable compatibility targets. A demonstrated incompatibility requiring one
of those files is a stop and brief-amendment condition.

## Proposed implementation grouping

### Group 0 — immediate Click disposition, documentation only

Record whether owner/security:

1. replaces the invalidated Click exception against exact current baseline
   `332ae2b` through the scheduled review under unchanged controls; or
2. declines replacement and authorizes Group 1 immediately.

No package or test edit belongs in Group 0.

### Group 1 — approval-safe three-package bundle

Exact direct-input deltas:

```text
click==8.3.3
Pygments==2.20.0
pymdown-extensions==10.21.3
pytest==8.4.2                 # retained
titanoboa==0.2.7              # unchanged
vyper==0.4.3                  # unchanged
```

Expected lock-version deltas: exactly Click `8.2.1 -> 8.3.3`, Pygments
`2.19.2 -> 2.20.0`, and Pymdown Extensions `10.16.1 -> 10.21.3`. No
transitive or other version may change.

After final lock-specific approval, this group may close only
`EX-H01-CLICK-01`, `EX-H01-PYGMENTS-01`, and
`EX-H01-PYMDOWN-SNIPPETS-01`. It must retain `EX-H01-PYTEST-01` at pytest
`8.4.2` and `EX-H01-PYMDOWN-B64-01`. Re-prove every H-02
import/help/CLI/redaction case, Pygments output, Snippets traversal behavior,
S1, the complete suite, and artifact equality.

### Group 2 — pytest major boundary

Direct-input delta:

```text
pytest==9.0.3
```

Expected lock-version delta: exactly `pytest 8.4.2 -> 9.0.3`.

This group is conditional on the owner/security/Track 6 disposition of Vyper
0.4.3's optional `pytest<9` metadata. Run the unchanged S1 test first and
require its exact-version failure before editing only the exact pytest
expectations. Close `EX-H01-PYTEST-01` only after independent Track 6 and
security approval.

### Group 3 — Pymdown b64 dependency-graph study

This is not a current implementation group. Pymdown `11.0.0` is the first b64
patch, but it has no valid lock under unchanged `titanoboa==0.2.7` and
`mkdocs-material==9.5.41`. Retain `EX-H01-PYMDOWN-B64-01`.

Only a separate owner/security/Track 6 authorization may open a feasibility
study for a Titanoboa or docs-graph change. Resolver success, full
compatibility evidence, and a new exact approval boundary are prerequisites
before any future implementation proposal.

## Exact validation matrix

Definitions for the command matrix:

- `<candidate-python>` is the exact CPython 3.12.0 interpreter in a newly
  created lock-exact candidate environment.
- `<old-python>` is a separate exact prior-lock environment; never upgrade or
  downgrade either environment in place.
- `<task-parent>` is newly created, owner-only mode `0700`, used for one pytest
  command only, and removed immediately after that command.
- `<boa-cache>` is a new task-specific mode-`0700` cache installed with
  `from boa.interpret import set_cache_dir`; it is removed after validation.
- Every pytest command includes
  `ETHERSCAN_API_KEY=local-placeholder PYTHONPATH=.` and an explicit
  `--basetemp=<task-parent>/basetemp`.
- Relevant RPC, explorer, deployer-key, vendor-token, and test-key variables
  are absent. No `.env`, external RPC, explorer, verifier, or live fork is
  used.

| Order | Gate | Exact command or proof | Required result |
|---:|---|---|---|
| 1 | Baseline | `git status --short --branch`; local/cached/live `rh`; commit/tree/hash freeze | Exact approved baseline; clean integration and implementation worktrees |
| 2 | Resolver | Approved pip-tools 7.4.1 command with CPython 3.12.0, pip 23.2.1, public PyPI only, no extra/private index, a private resolver-only cache, `--no-cache-dir` candidate installs, and a frozen-output seed | Two resolutions byte-identical; full literal diff has only the active group's approved version deltas. Group 1 has exactly three package-version deltas and no transitive change. Pymdown 11 remains a resolver stop, not a candidate. |
| 3 | Clean installs | `<old-python> -m pip check`; `<candidate-python> -m pip check`; complete inventory comparison | Both clean; no local/editable/URL/private source; inventory delta exactly matches the active group: three packages for Group 1 or pytest alone for Group 2 |
| 4 | Security reconciliation | Approved raw no-ignore `pip-audit==2.10.1` command against old and candidate locks; any K-02 refresh requires separate authority | Group 1 removes the Click, Pygments, and Snippets candidate rows while pytest and Pymdown b64 remain explicitly exception-governed; candidate remediation is not GitHub/Dependabot alert closure |
| 5 | H-01 gate | `<candidate-python> -m pytest -q tests/deployment/test_dependency_gate.py --basetemp=<task-parent>/basetemp` | All cases pass; current reachability and mutation cases included |
| 6 | Click-specific | H-02 combined command below plus all three `python -m scripts.{migrate,console,verify} --help` routes with relevant env absent | Exact choices/help/errors/redaction preserved; no `click.edit`, editor, plugin, or raw RPC path |
| 7 | Pygments-specific | Offline dependency-gate cases covering package version, normal lexer/highlight output, IPython/Rich/pytest rendering, and continued rejection of direct/aliased/dynamic literal Archetype selection | Patched version exact; no untrusted content; current normal output reviewed |
| 8 | Pymdown-specific | Offline Snippets cases against disposable roots, including shared-prefix, `..`, and absolute-path negative cases; b64 reachability and exception-ledger checks | Exact `10.21.3` blocks the Snippets traversal cases; b64 remains affected, unreachable from repository configuration, and governed by `EX-H01-PYMDOWN-B64-01`. No b64 remediation claim is made. |
| 9 | H-02 | `<candidate-python> -m pytest -q tests/deployment/test_network_profiles.py tests/deployment/test_secret_handling.py tests/deployment/test_base_profile_regression.py --basetemp=<task-parent>/basetemp` | Current 99-case H-02 surface passes with no skip/xfail/warning suppression |
| 10 | S1 | `<candidate-python> -m pytest -q tests/clock/test_clock_profiles.py --basetemp=<task-parent>/basetemp` | Exact Titanoboa/pytest profile, independent NUMBER/timestamp, repeated/jump profiles, anchor restoration, isolation, artifacts pass |
| 11 | S2 | `<candidate-python> scripts/check_block_clock_inventory.py --check`; then `<candidate-python> -m pytest -q tests/inventory/test_block_clock_inventory.py --basetemp=<task-parent>/basetemp` | `CLOCK_INVENTORY_OK`; all inventory tests pass |
| 12 | S3 | `<candidate-python> -m pytest -q tests/core/lootbox/test_underscore_rewards.py --basetemp=<task-parent>/basetemp`; then `tests/config/test_switchboard_charlie.py` in a fresh parent | Both exact current targets pass |
| 13 | Collection | `<candidate-python> -m pytest --collect-only -q --basetemp=<task-parent>/basetemp` | Frozen candidate count explained; no unexpected add/drop/deselect |
| 14 | Complete suite | `<candidate-python> -m pytest -q -p no:cacheprovider --basetemp=<task-parent>/basetemp` | Complete serial suite passes; no skip/xfail/warning suppression added |
| 15 | Artifacts | Old and candidate compile S1 `ClockObserver` and S3 `Lootbox`; export ABIs into separate empty disposable roots | ABI, creation bytecode, runtime bytecode, combined fingerprints, 49-file ABI inventory, and committed `Lootbox.json` are byte-identical |
| 16 | Scope | `git diff --check`; exact changed/untracked/staged path checks; repeat reachability scan; compare local/cached/live `rh` | Only future-owned files; no branch drift, private evidence, cache, environment, artifact, or generated output |
| 17 | Review | Independent security/Track 6 review; H-02 owner additionally reviews Groups 1 and 2 | Exact-byte approval after all evidence; any later byte or baseline change reopens review |

For Group 2 only, add this mandatory step before changing S1:

```text
run unchanged tests/clock/test_clock_profiles.py under pytest 9.0.3
expected result: fail only at the exact pytest-version assertion
```

Any other failure blocks the S1 edit. The later exact-version edit may not
change a profile, fixture, patch mechanism, diagnostic, assertion category, or
artifact definition.

## Review, rollback, and stop requirements

### Review requirements

- Freeze local, cached remote, and live remote `rh` before each group and again
  immediately before independent review.
- Re-read primary advisories, affected ranges, first-patch records, and
  release notes at each group; a changed range or fix version invalidates this
  candidate selection.
- Use a fresh no-ignore audit and authorized K-02 observation; do not access or
  relocate historical private evidence without separate authority.
- Security reviews every group. Track 6 reviews all groups and must explicitly
  approve Group 2. The H-02 owner reviews the approval-safe bundle and pytest
  group.
- Never infer current GitHub alert closure from a candidate or merged lock.

### Rollback requirements

- The rollback anchor is the exact prior approved commit, direct input, and
  compiled lock for the active group.
- Prove rollback by recreating a new environment from the old lock, running
  `pip check`, the H-01 gate, S1, H-02, collection, and the complete suite.
- Do not upgrade then downgrade the same environment and call it rollback.
- Before merge, abandon a failed candidate by discarding only its validated
  disposable environment and restoring prior reviewed bytes.
- After merge, rollback requires a separately reviewed revert/new lock commit;
  no destructive reset is authorized.

### Stop conditions

Stop the active group on:

- any selected package, direct input, lock line, command header, dependency
  path, or transitive version outside the approved group delta;
- a changed advisory range, newly surfaced finding, or expired/review-missed
  exception;
- loss of a compensating control or new reachability;
- a Vyper, Titanoboa, pytest-plugin, S1, H-02, collection, or artifact
  incompatibility;
- any need to edit a file outside future ownership;
- any skipped, xfailed, deselected, or warning-suppressed test introduced to
  obtain green;
- a dirty integration worktree, branch movement, or current/live `rh`
  disagreement;
- any secret/private-index/private-evidence dependency;
- any external write, alert mutation, production RPC, signing, deployment, or
  verification action; or
- an incomplete independent review.

## Scheduled review and hard-expiry handling

### 15 August 2026 scheduled review

The review is not a calendar reminder that silently renews risk. It must:

1. verify current local/cached/live baseline identity;
2. refresh current public advisory and authorized alert/audit evidence;
3. repeat repository reachability and compensating-control checks;
4. decide each exception independently;
5. approve an exact candidate group, replace the exception with a new explicit
   owner/scope/control/expiry record, or block;
6. record whether the Click invalidation was already cured by upgrade or by a
   replacement current-baseline exception; and
7. preserve private-evidence custody without reading or moving it unless that
   access is separately authorized.

Missing the scheduled review makes the relevant exception stale for rehearsal
and merge. It does not defer automatically to 31 August.

### `2026-08-31T23:59:59Z` hard expiry

At hard expiry, every unclosed exception blocks deployment rehearsal and merge.
There is no automatic grace period and no forced-upgrade authority. The only
valid states are:

- the finding is absent under an independently approved, integrated, and
  observed dependency profile;
- a new explicit exception is approved before the old one expires, with a
  fresh owner, scope, controls, trigger, and expiry; or
- the workflow remains blocked.

## Residual risks

1. The current ambient Python environment is internally consistent but is not
   lock-exact for Candidate A's six upgraded packages. It must not be used as
   implementation or compatibility evidence.
2. The Click exception's invalidation trigger fired when H-02 expanded the
   allowlisted CLI call surface. The current gate does not encode that broader
   trigger.
3. Pymdown's mechanical scan covers configuration activation but not Python
   programmatic imports/activation.
4. Pygments dynamic/plugin lexer selection is not exhaustively excluded by the
   current literal/AST checks.
5. pytest private-basetemp/single-tenant controls are procedural; no universal
   repository runner enforces them.
6. This preflight does not refresh authenticated alert or private audit
   evidence. The H-01 committed record remains the last authority read here.
7. Package first-patch candidates are current only to the committed evidence.
   Future implementation must recheck primary sources and stop on drift.
8. A docs-toolchain package can be unreachable in current production source
   yet still affect Titanoboa installation/import metadata and developer
   tooling.
9. This documentation-only reconciliation did not rerun resolution or package
   tests. It relies on the later version-exact feasibility study: the
   approval-safe three-package bundle resolved and passed its recorded
   compatibility interval, while Pymdown 11 stopped at resolution. A future
   implementation must recreate those results against its final bytes.

No residual risk is accepted by this preflight.

## Copy-ready owner/security decision packet

```text
H-01 BOUNDED-EXCEPTION EXIT DECISION

Reviewed baseline:
  commit 332ae2bc8e0ce4b694766d6d20759295d9267ec3
  tree   f67dc91e47331785837de879b6557b285aec3b1b

1. MANDATORY CLICK DISPOSITION — select exactly one:
   [ ] Replace EX-H01-CLICK-01 immediately against the exact current baseline
       with explicit controls/review/expiry; do not rely on the invalidated
       prior exception.
   [ ] Authorize a separate implementation and independent review of the
       approval-safe bundle below, including Click 8.3.3.
   [ ] Block rehearsal/merge and provide another exact disposition.

2. APPROVAL-SAFE BUNDLE — no box is preselected:
   [ ] Authorize a separate implementation/review interval for exactly:
         click==8.3.3
         Pygments==2.20.0
         pymdown-extensions==10.21.3
         pytest==8.4.2 retained
         titanoboa==0.2.7 unchanged
         vyper==0.4.3 unchanged
       Require zero transitive version change, the complete validation matrix,
       and closure only of Click, Pygments, and Pymdown Snippets exceptions.

3. RETAINED EXCEPTIONS:
   [ ] Retain EX-H01-PYTEST-01 at pytest==8.4.2 under private-basetemp and
       trusted single-tenant controls. Treat pytest 9.0.3 as a separate
       S1/Vyper/Track 6 owner decision.
   [ ] Retain EX-H01-PYMDOWN-B64-01. Acknowledge that Pymdown 11.0.0 is
       unresolved under titanoboa==0.2.7 -> mkdocs-material==9.5.41 ->
       pymdown-extensions>=10.2,<11. Any graph study needs separate authority.

4. EVIDENCE AND STATE:
   [ ] Acknowledge that candidate lock/audit remediation is not
       GitHub/Dependabot alert closure and authorizes no alert-state claim.
   [ ] Require final exact-byte resolver, audit, H-01/H-02/S1/S2/S3, complete
       suite, ABI/bytecode, scope, rollback, and independent-review evidence.
   [ ] Confirm the 15 August review and 2026-08-31T23:59:59Z hard-expiry
       boundaries; no missed review, expiry, or resolver failure authorizes a
       forced upgrade.

Owner:
  name:
  decision:
  UTC timestamp:

Security reviewer:
  name:
  decision:
  UTC timestamp:

Track 6 reviewer:
  name:
  pytest/S1 decision:
  UTC timestamp:

H-02 owner:
  name:
  Click/pytest compatibility decision:
  UTC timestamp:

Blank, unchecked, or ambiguous items grant no dependency implementation,
rehearsal, merge, alert-state, or exception-retirement authority.
```

## Preflight validation record

Performed from the isolated worktree at the verified baseline:

| Check | Result |
|---|---|
| Integration worktree status | Clean on `rh`; no tracked, staged, or untracked change |
| Local `rh` | `332ae2bc8e0ce4b694766d6d20759295d9267ec3` |
| Cached `origin/rh` | `332ae2bc8e0ce4b694766d6d20759295d9267ec3` |
| Live `origin/rh` | `332ae2bc8e0ce4b694766d6d20759295d9267ec3` |
| Baseline tree | `f67dc91e47331785837de879b6557b285aec3b1b` |
| H-01/H-02 ancestry | H-01 merge `575d47b`, H-02 merge `6c30526`, and H-02 correction commit `5c1ba54` are ancestors |
| Current source/config delta since H-01 | Only integrated H-02 Python/config/test files; no requirement, lock, S1, or H-01 gate-test change |
| Click reachability | Three approved files only; no `click.edit`, editor, or `VISUAL`/`EDITOR` use; H-02 call-surface trigger identified |
| Pygments reachability | No affected lexer import/selection/configuration |
| Pymdown reachability | No import, MkDocs configuration, snippets/b64 activation, or docs-build path |
| Later feasibility identity | Reviewed report preserved at `37a85b8078f798466f0a315b273a667ad72b02e3`; report SHA-256 `0309004064b3642ab18b848c7935711a3ea3346748b0d601e10271639a31c04d` |
| Approval-safe bundle evidence | Exact Click `8.3.3`, Pygments `2.20.0`, and Pymdown `10.21.3`; pytest `8.4.2`, Titanoboa `0.2.7`, and Vyper `0.4.3` held; no transitive version change |
| Pymdown 11 evidence | `ResolutionImpossible`; no valid lock or installed candidate under `mkdocs-material==9.5.41 -> pymdown-extensions>=10.2,<11` |
| H-01 reachability cases | `5 passed, 11 deselected` |
| Complete ambient H-01 gate | `15 passed, 1 failed`; exact-runtime failure because ambient Candidate A packages do not match the lock |
| Ambient `python -m pip check` | No broken requirements; explicitly not lock-exact evidence |
| Dependency/package mutation | None |
| External/private evidence access | None |
| GitHub/alert mutation or public report | None |
| Production/live action | None |

The only repository change produced by this task is this new untracked
document. It is intentionally unstaged and uncommitted for independent review.

## 26 July 2026 implementation checkpoint

This later checkpoint records execution under the owner's separate exact
authorization. It does not alter the historical blank proposed-authorization
form above and does not itself approve exception retirement.

**Superseded status:** The owner did not approve this checkpoint's first Gate
1 verdict. Its 24-case H-01 and 2,845-case full-suite results below are
historical, non-authoritative inputs to a bounded F1/F3 correction. Only a
later corrected validation record may state the current Gate 1 result.

The implementation branch
`rh-track-7-h1-exception-retirement-implementation` was created in the fresh
isolated worktree
`/Users/wigglez/dev/ripe-protocol-track-7-h1-exception-retirement-implementation`
from exact commit `c0d0e708ae4a89ed730615c9eaf2d23a4fecc05d`, tree
`b2c2358f565e27ad6a5c787a9a0d1396af513076`. The preserved feasibility
report remains byte-identical at SHA-256
`9b9ad56d73d8a7418dcc0e452b3affb927979ce53fd90fcd5f84f9b9dfcfbfec`.

Two independent approved-seed resolutions produced byte-identical candidate
inputs at
`1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9`
and byte-identical locks at
`214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010`.
The exact version delta is only:

```text
click                 8.2.1  -> 8.3.3
pygments              2.19.2 -> 2.20.0
pymdown-extensions    10.16.1 -> 10.21.3
```

There is no fourth direct or transitive change. Exact pytest `8.4.2`,
Titanoboa `0.2.7`, Vyper `0.4.3`, and all other dependency versions are
unchanged. Separate fresh control and candidate environments both passed
`pip check`; their 93-distribution inventories differed only in the three
authorized packages and contained no direct/local/editable source.

A fresh raw no-ignore `pip-audit==2.10.1` candidate audit reported only
Pymdown b64 `CVE-2026-61632`, pytest `PYSEC-2026-1845`, and the two
range-excluded Vyper rows. The Click, Pygments, and Pymdown Snippets rows were
absent. This is candidate audit remediation only, not evidence of GitHub or
Dependabot alert closure.

The exact validation matrix completed as follows:

| Gate | Result |
|---|---|
| H-01 dependency gate | 24 passed |
| Click behavior | 14 control/candidate CLI cases byte-identical; secret URL absent from output |
| Pygments behavior | Python tokens plus HTML, terminal, IPython, pytest, and Rich rendering byte-identical |
| Pymdown behavior | `10.21.3` blocked shared-prefix, parent, and absolute Snippets traversal; b64 outside-base encoding persisted |
| H-02 | 99 passed |
| S1 | 57 passed |
| S2 | `CLOCK_INVENTORY_OK`; 60 passed |
| S3 / Lootbox | complete Lootbox directory, 175 passed |
| S3 / Switchboard | Charlie target, 91 passed |
| Collection | 2,845 selected; 142 pre-existing deselected |
| Complete candidate suite | 2,845 passed; 142 deselected |
| Compiler artifacts | ClockObserver and Lootbox ABI, creation/runtime bytecode, settings, version, and combined fingerprints byte-identical |
| ABI inventory | 49 byte-identical files; committed Lootbox ABI byte-identical |
| Rollback | fresh old-lock environment: `pip check`, baseline H-01 16, H-02 99, S1 57, 2,837 selected, and complete 2,837-pass suite all clean |

All pytest commands used an external single-use mode-`0700` basetemp parent
and a private Boa cache, and each parent was removed after its command. The
candidate adds exactly eight H-01 cases and introduces no skip, xfail,
deselection, warning suppression, or relaxation.

The proposed disposition, pending final independent review and owner approval,
is retirement only of `EX-H01-CLICK-01`, `EX-H01-PYGMENTS-01`, and
`EX-H01-PYMDOWN-SNIPPETS-01`. Retain `EX-H01-PYTEST-01` and
`EX-H01-PYMDOWN-B64-01`. All five remain operative at this Gate 1 stop. The
implementation is intentionally unstaged and uncommitted; no alert query or
mutation, private retained-evidence access, external write, deployment,
signing, verification submission, or live-chain action was performed.

## 26 July 2026 corrected Gate 1 checkpoint

The first 24-case / 2,845-case verdict above remains superseded. After normal
conflict-free reconciliation of the `rh` snapshot observed as `8e4a965f...`
on 26 July 2026 in local merge
`9aedbbbf13f8f60e0bd816d6493e310cacbfbbda`, the bounded correction:

- set Rich `Console(no_color=False, force_terminal=True,
  color_system="standard")`, asserted ANSI output, and reproduced colored hash
  `4a98e8fea362182468a3d6c34cc22bdbc6efb5c4a293833960a382bdaf9afdd5`;
- made direct `markdown.markdown(..., extensions=...)` Pymdown b64/Snippets
  literal and bounded-concatenation activation fail closed;
- added four positive and two negative focused F3 cases;
- passed H-01 30/30 both with `NO_COLOR` absent and with `NO_COLOR=1`;
- recollected exactly 2,851 selected / 142 pre-existing deselected and passed
  all 2,851 selected cases;
- reproduced H-02 99, S1 57, S2 60 plus `CLOCK_INVENTORY_OK`, Lootbox 175,
  Switchboard Charlie 91, compiler/ABI identities, and the 49-file ABI
  inventory; and
- reproduced the fresh old-lock rollback suite at 2,837 passed / 142
  deselected.

Pygments runtime/plugin selection, the scanner root/symlink boundary, and the
pinned-pytest private terminal-writer dependency remain explicitly disclosed.
The procedural Click trigger is not relied upon after any later separately
reviewed retirement transition. The exact compiler-data canonicalization
command and residual boundaries are in the latest
`dependency-security-gate.md` section.

No exception is retired. All five remain operative, and
`PROPOSED_RETIREMENTS` remains proposed only pending another fresh exact-hash
review, independent approval, and separate owner authorization. The package
remains unstaged and uncommitted; nothing was pushed or merged into `rh`.

## 27 July 2026 final bounded-correction checkpoint

The five-file package began this correction at approved full-index patch
SHA-256
`9c075c4f6f2a69bd5a56eab79fee44fb53669b83a0df69b4fcc9cffa6ade93cf`
and the five approved hashes recorded in the latest
`dependency-security-gate.md` section. The lock and direct input did not move.

The Python reachability scanner now evaluates each statically resolvable
extension element independently, so a dynamic sibling cannot hide direct
`pymdownx.b64` or `pymdownx.snippets` activation. The bounded check covers
`markdown.markdown`, `markdown.Markdown`, and `markdown.markdownFromFile`
through direct imports, module aliases, imported function/class aliases,
direct static alias assignments, static string/sequence concatenation, and
direct or bounded named `**` mappings. It does not infer unrestricted runtime
dataflow, and the behavior-test allowlist remains exact.

The expanded scanner matrix passed 21 focused cases. Complete H-01 passed all
45 cases both with ambient `NO_COLOR` absent and with `NO_COLOR=1`. H-02
passed 99, S1 passed 57, S2 passed 60 with `CLOCK_INVENTORY_OK`, Lootbox
passed 175, and Switchboard Charlie passed 91. Collection is exactly 2,866
selected of 3,008, with the same 142 expected deselections; the 15-case
increase is twelve new fail-closed scanner parameters and three new bounded
negative parameters. The complete serial candidate suite passed all 2,866
selected cases with zero skip or xfail.

Both 93-distribution inventories now have exact reproducible command and byte
serialization provenance. Independent reruns produced control SHA-256
`9e30800bec2f4d9a784314b6a3d3d25a37ee7c994a022366a577966a698abfa2`
and candidate SHA-256
`f0393df6e4c1728b28d95e5034fee7b6ca4c5463df8fb387dbae839e15b87e4d`,
with only the three authorized rows different. The older undocumented
aggregate inventory digests are historical and non-load-bearing. Independent
control/candidate 49-file ABI exports reproduced compact sorted-JSON mapping
SHA-256
`c49c61ad006d223a1bf13e2d26c5862eda82128f3cc640501c278c28f69b1dde`
from the exact command and serialization recorded in the security-gate
evidence.

Rollback is authoritative only from a real Git worktree. The Base-history test
explicitly self-skips when `.git` is unavailable, so a `git archive` result of
2,836 passed plus one skip is not equivalent and is non-load-bearing. The
fresh old-lock replay from the clean integration Git worktree passed
`pip check`, H-01 16, H-02 99, S1 57, collection 2,837/2,979 with 142
deselected, and the complete serial suite at 2,837 passed / 142 deselected
with no skip or xfail.

At `2026-07-27T03:30:58Z`, the final validation-freeze read observed local,
cached, and live `rh` at
`7a3a36666f277277fa08b55081b3f58c7cd3ba64`, with a clean integration
worktree. This is a timestamped observation, not continuing candidate
authority. Local, cached, and live refs plus integration cleanliness must be
recomputed immediately before any later commit-time reconciliation. This
correction performs no reconciliation.

No exception is retired. All five remain operative, and
`PROPOSED_RETIREMENTS` remains proposed only. The package remains unstaged and
uncommitted pending narrow delta re-review.

## H-01 three-exception retirement transition authorization record

The owner adopted verbatim the frozen
`H-01 THREE-EXCEPTION RETIREMENT TRANSITION AUTHORIZATION` against exact
integrated `rh` commit
`d62777646cba1ae448fb9e26519c6fa295f437df`, tree
`01b1d7c8fc7bdf5163e20efe1f61b53db2b01a61`.

The transition file ceiling is exactly:

```text
tests/deployment/test_dependency_gate.py
docs/chains/rh/evidence/dependency-security-gate.md
docs/chains/rh/evidence/dependency-exception-exit-preflight.md
```

The dependency inputs and feasibility evidence are immutable:

```text
requirements.in
  1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9
requirements.txt
  214f6c32c628df1eb2bbb1979b3bae8147ceaf338e68959dd58d82394b9be010
docs/chains/rh/evidence/h01-exception-retirement-feasibility.md
  9b9ad56d73d8a7418dcc0e452b3affb927979ce53fd90fcd5f84f9b9dfcfbfec
```

### Final target dispositions

| Exception | Final target disposition |
|---|---|
| `EX-H01-CLICK-01` | **Retired—historical and non-operative.** Exact `click==8.3.3` supplies the reviewed remediation. |
| `EX-H01-PYGMENTS-01` | **Retired—historical and non-operative.** Exact `Pygments==2.20.0` supplies the reviewed remediation. |
| `EX-H01-PYMDOWN-SNIPPETS-01` | **Retired—historical and non-operative.** Exact `pymdown-extensions==10.21.3` remediates Snippets only. |
| `EX-H01-PYTEST-01` | **Retained—operative.** Exact pytest `8.4.2`, private-basetemp/single-tenant controls, review, expiry, and triggers remain in force. |
| `EX-H01-PYMDOWN-B64-01` | **Retained—operative.** Exact Pymdown Extensions `10.21.3` remains affected; first patch `11.0.0` remains outside the resolver-valid current graph. |

The unchecked decision forms above and in the immutable feasibility report are
historical proposals against earlier baselines. They remain unchecked and
unchanged. This current record resolves those decisions without rewriting
their chronology.

### Effectivity and alert-state boundary

The three retirement dispositions become effective only when the exact
independently approved transition commit containing this record is integrated
into authoritative `rh`. Until that event, all five prior exceptions remain
operative on authoritative `rh`. The two retained exceptions remain operative
both before and after the transition.

Package remediation and repository exception retirement do not establish
GitHub/Dependabot alert closure. No authenticated GitHub or Dependabot query is
required or authorized for this transition. No alert may be described as
closed, dismissed, resolved, or changed without separate authority and fresh
authenticated evidence.

### Transition validation and rollback requirements

The transition candidate must preserve the exact dependency and feasibility
hashes above; pass `pip check`; reconcile a fresh raw no-ignore package audit
without GitHub access; pass the focused retirement/retention assertions and
complete H-01 gate with `NO_COLOR` absent and present; reproduce H-02, S1, S2,
Lootbox, Switchboard Charlie, compiler/ABI, collection, and complete serial
suite identities; add no skip, xfail, warning suppression, relaxation, or
unexplained deselection; and pass whitespace and exact-scope checks.

The expected unchanged counts are H-01 45, H-02 99, S1 57, S2 60,
Lootbox 175, Switchboard Charlie 91, collection 2,866 of 3,008 with 142
deselected, and complete serial 2,866 passed. Any count change stops the
transition.

Rollback before integration restores only the three transition files to their
exact `d627776...` bytes and discards only disposable validation environments.
After any later transition commit or integration, rollback requires a
separately reviewed normal revert. No dependency downgrade, reset, rebase, or
history rewrite is authorized.
