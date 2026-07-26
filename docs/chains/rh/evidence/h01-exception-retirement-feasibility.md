# H-01 bounded-exception retirement feasibility

Date: 2026-07-25

Study baseline: `332ae2bc8e0ce4b694766d6d20759295d9267ec3`

Study worktree: detached, mode-`0700`, created from the exact baseline under
`/private/tmp`

Integration worktree: `/Users/wigglez/dev/ripe-protocol`, branch `rh`, left
unchanged at the exact baseline

Status: independent feasibility evidence only; untracked and uncommitted

## Decision summary

This study does not retire an exception, approve a dependency change, update an
alert, or authorize a deployment.

| Exception | Feasibility disposition | Smallest candidate | Approval consequence |
|---|---|---|---|
| `EX-H01-CLICK-01` | **retirable now** | `click==8.3.3` | No S1 or prior production approval reopens. A separately authorized lock, gate, exception-record, audit, and review change is still required. |
| `EX-H01-PYGMENTS-01` | **retirable now** | `Pygments==2.20.0` | No S1 or prior production approval reopens. A separately authorized lock, gate, exception-record, audit, and review change is still required. |
| `EX-H01-PYMDOWN-SNIPPETS-01` | **retirable now** | `pymdown-extensions==10.21.3` | No S1 or prior production approval reopens. The separate b64 exception remains. |
| `EX-H01-PYMDOWN-B64-01` | **retain** | No resolver-valid candidate inside this study's boundaries | The first patch, `11.0.0`, conflicts with Titanoboa's pinned `mkdocs-material==9.5.41` graph. Retirement would require a separately authorized Titanoboa/docs-graph change. |
| `EX-H01-PYTEST-01` | **technically viable but requires separate approval** | `pytest==9.0.3` | Reopen S1/Track 6 exact-runtime approval. Vyper 0.4.3's optional test/dev metadata says `pytest>=8,<9`, even though that extra is not installed and the repository runtime evidence is otherwise compatible. |

The smallest resolver-valid, approval-safe bundle that retires the maximum
number without reopening S1 is:

```text
click==8.3.3
Pygments==2.20.0
pymdown-extensions==10.21.3
pytest==8.4.2                 # retained
titanoboa==0.2.7              # unchanged
vyper==0.4.3                  # unchanged
```

It changes exactly three package versions and no transitive version. Its fresh
serial result was `1 failed, 2836 passed, 142 deselected`; the one failure was
the deliberate policy assertion comparing the candidate runtime to the
unchanged repository lock, not a runtime or compatibility failure. S1 passed
all 57 tests.

The smallest resolver-valid maximum technical bundle changes the same three
packages plus `pytest==9.0.3`. It can clear four of the five audit findings,
but cannot authorize retirement of the pytest exception: all 57 S1 cases stop
at S1's unchanged exact `pytest==8.4.2` approval gate. No test or approval file
was edited to bypass that stop.

## Authority and isolation

The following files were read completely before candidate work:

- `docs/chains/rh/track-7-h1-dependency-security-preflight.md`
- `docs/chains/rh/evidence/dependency-security-gate.md`
- `requirements.in`
- `requirements.txt`
- `tests/deployment/test_dependency_gate.py`
- `tests/clock/test_clock_profiles.py`

The integration `rh` worktree was clean at the requested commit before the
study and remained clean at that commit after evidence collection. Candidate
locks, environments, resolver caches, audit caches, Boa caches, pytest
basetemps, generated ABIs, and probe inputs were created only in a private
mode-`0700` task root under `/private/tmp`. The only repository artifact is
this untracked report in the detached study worktree.

The study did not:

- access the private H-01 evidence directory;
- query or mutate GitHub or Dependabot alerts;
- alter the active Python environment;
- edit a requirement, lock, test, contract, migration, manifest, production
  source file, existing evidence file, or committed ABI;
- contact a live chain or explorer;
- commit, stage, push, merge, deploy, sign, or broadcast.

`ETHERSCAN_API_KEY=local-placeholder` satisfied the repository's
collection-time guard only. No explorer request was made.

## Fresh upstream verification

The affected ranges and first patched versions below were rechecked against
public upstream advisory/package metadata on 2026-07-25. Existing H-01 evidence
was not treated as the authority for these values.

| Finding | Independently verified affected range | First verified patch | Exact candidate wheel SHA-256 | Primary sources |
|---|---|---|---|---|
| Click command injection, `PYSEC-2026-2132`, CVE-2026-7246 / GHSA-47fr-3ffg-hgmw | versions before `8.3.3` | `8.3.3` | `a2bf429bb3033c89fa4936ffb35d5cb471e3719e1f3c8a7c3fff0b8314305613` | [PyPA advisory YAML](https://raw.githubusercontent.com/pypa/advisory-database/main/vulns/click/PYSEC-2026-2132.yaml), [Click 8.3.3 on PyPI](https://pypi.org/project/click/8.3.3/) |
| Pygments Archetype lexer ReDoS, `PYSEC-2026-2987`, CVE-2026-4539 / GHSA-5239-wwwm-4pmq | `<2.20.0` | `2.20.0` | `81a9e26dd42fd28a23a2d169d86d7ac03b46e2f8b59ed4698fb4785f946d0176` | [GitHub advisory](https://github.com/advisories/GHSA-5239-wwwm-4pmq), [Pygments 2.20.0 on PyPI](https://pypi.org/project/Pygments/2.20.0/) |
| Pymdown Snippets base-path bypass, `PYSEC-2026-2999`, GHSA-62q4-447f-wv8h | `>=10.0.1,<=10.21.2` | `10.21.3` | `d7a5d08014fc571e80ca21dd6f854e31f94c489800350564d55d15b3c41e76b6` | [GitHub advisory](https://github.com/advisories/GHSA-62q4-447f-wv8h), [Pymdown Extensions 10.21.3 on PyPI](https://pypi.org/project/pymdown-extensions/10.21.3/) |
| Pymdown b64 local-file disclosure, CVE-2026-61632 / GHSA-9xwg-3r6f-jcx2 | `<=10.21.3` | `11.0.0` | `fbc4acb641814fa9d17521bbd21a5240ef739a662f11c06330c4b78c93e954d6` | [GitHub advisory](https://github.com/advisories/GHSA-9xwg-3r6f-jcx2), [Pymdown Extensions 11.0.0 on PyPI](https://pypi.org/project/pymdown-extensions/11.0.0/) |
| pytest predictable temporary directory, `PYSEC-2026-1845`, CVE-2025-71176 / GHSA-6w46-j5rx-g56g | `<9.0.3` | `9.0.3` | `2c5efc453d45394fdd706ade797c0a81091eccd1d6e4bccfcd476e2b8e0ab5d9` | [GitHub advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g), [pytest 9.0.3 on PyPI](https://pypi.org/project/pytest/9.0.3/) |

The downloaded Pymdown 11.0 wheel was also inspected directly. Its b64
implementation defaults `restrict_path` to true and introduces `root_path`,
which addresses the recorded unrestricted path behavior. That source fact does
not overcome the resolver conflict described below.

The fresh no-ignore audits also emitted two scanner rows against
`vyper==0.4.3`. They are not H-01 surviving exceptions and are not applicable
to 0.4.3 according to the primary upstream ranges:

- [GHSA-5824-cm3x-3c38](https://github.com/vyperlang/vyper/security/advisories/GHSA-5824-cm3x-3c38)
  affects only 0.2.15, 0.2.16, and 0.3.0; 0.3.1 is the patch.
- [GHSA-vgf2-gvx8-xwc3](https://github.com/vyperlang/vyper/security/advisories/GHSA-vgf2-gvx8-xwc3)
  affects versions through 0.4.0; 0.4.1 is the patch.

The installed and compiled Vyper remained exactly 0.4.3 throughout.

## Toolchain and exact identities

### Host and tools

| Identity | Exact value |
|---|---|
| Host | macOS 26.5.2, build 25F84, arm64 |
| Seed interpreter | CPython 3.12.0, Clang 17.0.0 |
| Seed interpreter path | `/Users/wigglez/.pyenv/versions/3.12.0/bin/python3.12` |
| Seed interpreter SHA-256 | `d23fa2c326127c9590d097603f105d69e68774968f46246fc7a8a80103600765` |
| Candidate pip | 23.2.1 in every environment |
| Resolver | pip 23.2.1; pip-tools 7.4.1; build 1.5.0; Click 8.4.2; packaging 26.2; pyproject-hooks 1.2.0; setuptools 83.0.0; wheel 0.47.0 |
| Auditor | pip 23.2.1; pip-audit 2.10.1; CacheControl 0.14.4; cyclonedx-python-lib 11.11.0; packaging 26.2; pip-api 0.0.34; pip-requirements-parser 32.0.1; requests 2.34.2; rich 15.0.0 |
| Package source | public `https://pypi.org/simple` only; no extra/private index, local path, VCS, or editable distribution |

The resolver was seeded with the exact current output lock. The material
command was:

```text
pip-compile \
  --cache-dir=<private-candidate-cache> \
  --index-url=https://pypi.org/simple \
  --no-emit-index-url \
  --output-file=<private-candidate>/requirements.txt \
  <private-candidate>/requirements.in
```

Every valid candidate was installed into a new CPython 3.12.0 virtual
environment with public PyPI and `--no-cache-dir`; every environment then ran
`python -m pip check`. The no-ignore audit command was:

```text
pip-audit \
  --cache-dir <private-audit-cache> \
  --no-deps \
  --disable-pip \
  --format json \
  --output <private-candidate>/audit.json \
  --requirement <private-candidate>/requirements.txt
```

There was no `--ignore-vuln`. `--no-deps --disable-pip` made the fully pinned
resolver lock the audit subject and prevented a second implicit resolution.

### Candidate lock and installed-graph identities

Each valid environment contained exactly 93 distributions. The inventory hash
is SHA-256 of canonical JSON containing every normalized
`(distribution-name, version)` pair in sort order. Because every candidate lock
diff was mechanically reduced to the named rows below, the exact identity of
all transitives is the committed control lock plus those rows; no transitive
version changed.

| Candidate, in required order | Exact selected versions | Input SHA-256 | Output lock SHA-256 | Installed inventory SHA-256 |
|---|---|---|---|---|
| Control | Click 8.2.1; Pygments 2.19.2; Pymdown 10.16.1; pytest 8.4.2 | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` | `dd7409860ff2f014fc607c77c57ce56df4d1da3175f381fa54eed9644fe50e59` |
| Click | Click 8.3.3 only | `61064759ccc49801d6f3a886039ead6f327d5643a576ce79fd5873ec8cbc3b3b` | `1e68c0de5f82221392810b7ac3a0584c5f2bb15f8c7a776df4557e369ca7b98b` | `eadbed1f949bbdfc5c55cf5f707059edb3cf23604227350fd171344b4406414f` |
| Pygments | Pygments 2.20.0 only | `6e999f3762f76c562ee39ac37e10bc37a851518c06975fd83f4a248909630462` | `c76b385041263b191167a07f7b52601af25ab29ad04f3cc5408f729311ee9c69` | `ba7b787f4c3595daac13e83561d2c96c78bdab31ce65b9d84edf3a25c145b54c` |
| Pymdown Snippets | Pymdown 10.21.3 only | `a24300dcb09026bd1c5742a8e1d51c991cac68847f4dff18792931798335ceb1` | `2ecf8e5386028c4743217a729a6a1c03977adda200ee756960c7b63da4a8042f` | `8112287a53407ec9f35c00999b8c97ab8336006bbefa32658bf0cef6328821de` |
| Pymdown both findings | Pymdown 11.0.0 requested | `78d2683846a8a62b06295346cb030cfa3ebf754521d728f4a8a5ccd52264ea77` | **No valid output lock** | **No environment installed** |
| pytest | pytest 9.0.3 only | `2b19212edd68b20efba3d9e1a9d87f927dd9330635c2c55bc6d728fdb56182de` | `e2af4c1452869aca5f63ffa22e2ac64397cdc929a6e7036a858d08890f0f5c07` | `03a6f53fcc689e13e52314d4b52cc73c2230f856db8a44e84bcd527db03cb0bd` |
| Maximum technical combined | Click 8.3.3; Pygments 2.20.0; Pymdown 10.21.3; pytest 9.0.3 | `f539b2123dd08e21ae4f10a6f3455e6b475ee0ded0eed366634f772fa81188d7` | `f519e2266cc71120d088538aef637464795083dbb63dd168906ec7de98181c09` | `ed8b5ee197eac9b385f06bee9b5f0c395af6d4f2534a2908a0ccc1867b4cbddc` |
| Approval-safe combined supplement | Click 8.3.3; Pygments 2.20.0; Pymdown 10.21.3; pytest 8.4.2 | `1227d9681d8b37f6820a7c09fa33b87798229e613748085e45454efea962a2b9` | `854468a7d29c496e007890231ab865e01843fc943285c996590c0f905cb18f65` | `1f60250c51822ad4e033ed729563ff8f2625a05e93730116c55477e97dae3688` |

All valid rows preserved `titanoboa==0.2.7` and `vyper==0.4.3`. Their public
wheel SHA-256 identities were, respectively,
`75771f5e8183c073f2c37d8925f583abd2c6b56eae4d087dbf1e33f809ea7ca5`
and
`3b9671727c888363740dc678e60336759871487d0e4e9fdd973048fa9635c4fd`.
No installed distribution carried `direct_url.json`.

The exact normalized version deltas were:

```diff
-click==8.2.1
+click==8.3.3

-pygments==2.19.2
+pygments==2.20.0

-pymdown-extensions==10.16.1
+pymdown-extensions==10.21.3

-pytest==8.4.2
+pytest==9.0.3
```

Individual locks contain only their one applicable hunk. The approval-safe
combined lock contains the first three hunks. The maximum technical lock
contains all four. All other normalized pins are byte-for-byte version
identical to control.

### Pymdown 11 resolver stop

Pymdown 11.0.0 was tested only after the Pymdown 10.21.3 candidate. The
resolver produced `ResolutionImpossible`:

```text
pymdown-extensions==11.0.0
mkdocs-material==9.5.41 -> pymdown-extensions~=10.2
```

`mkdocs-material==9.5.41` is required by unchanged
`titanoboa==0.2.7`. Therefore no valid lock, install, `pip check`, runtime
suite, or production artifact comparison exists for Pymdown 11 inside the
authorized boundary. A synthetic lock audit was used only to confirm that
11.0.0 is recognized as patched; it was explicitly excluded from candidate
compatibility evidence.

## Fresh no-ignore audit

| Candidate | Audit result | Relevant remaining rows |
|---|---|---|
| Control | 7 rows in 5 packages | all five H-01 findings plus two non-applicable Vyper scanner rows |
| Click 8.3.3 | 6 rows in 4 packages | Click row removed |
| Pygments 2.20.0 | 6 rows in 4 packages | Pygments row removed |
| Pymdown 10.21.3 | 6 rows in 5 packages | Snippets row removed; b64 remains with fix 11.0.0 |
| pytest 9.0.3 | 6 rows in 4 packages | pytest row removed |
| Maximum technical combined | 3 rows in 2 packages | Pymdown b64 plus two non-applicable Vyper rows |
| Approval-safe combined | 4 rows in 3 packages | Pymdown b64, pytest, and two non-applicable Vyper rows |

The exact audit JSON SHA-256 values were:

| Candidate | Audit JSON SHA-256 |
|---|---|
| Control | `43df8051327ce182fe28bb0ab2fbf2e76dcc9b29a48280d55320907a91f814c9` |
| Click | `bea835bbdf70f3a5325e1455f06e11248dfc82f8cca7ace97214cf339eabcaf1` |
| Pygments | `d6eb8a6d6c2280bfadae86201f5336a1bda759d21ee9f7e60794331b80acefc5` |
| Pymdown 10.21.3 | `3c733c28d58b1502d9d2a00230c2640adee558f434c40ecca033a63fc93ff079` |
| pytest | `e9cdad18d7b1864cb1541c78439ea5dba816e2a0d5ac8a5fad521fc919ccb905` |
| Maximum technical combined | `cda8e97ca2e9b6451ad6b6192f813c2d0394d0ba49e0de6a2afce979268739b7` |
| Approval-safe combined | `d115cfe4c6e6b91f955bc5507e287c1afb9718775bbef124c07dcb6e621b89ef` |

## Reachability and package behavior

### Repository configuration

A repository scan excluding the H-01 evidence/gate text found:

- no `mkdocs.yml` or `mkdocs.yaml`;
- no `pymdownx.snippets` or `pymdownx.b64` configuration;
- no Pymdown `restrict_base_path`, `restrict_path`, or `root_path`
  configuration;
- no `ArchetypeLexer`, `AdlLexer`, or repository `get_lexer_by_name` selection;
- no `click.edit` call or `from click import edit`.

The dependency gate's five dedicated Click/Pygments/Pymdown reachability and
configuration assertions passed in each applicable candidate (`5 passed, 11
deselected`).

Pygments is transitively reachable through IPython, pytest, Rich, and
Titanoboa's MkDocs stack, so a general rendering regression remains possible.
The vulnerable Archetype lexer is not selected by repository code or config.
Pymdown is reachable only through `titanoboa -> mkdocs-material`; the repository
has no applicable docs build/config path. Those reachability facts bound
exposure but do not by themselves patch or retire an exception.

### Click CLI and aliases

Control, Click 8.3.3, the maximum bundle, and the approval-safe bundle ran the
H-02 CLI suite. The Click-specific study also compared eight subprocess cases:

1. `scripts.migrate --help`;
2. `scripts.console --help`;
3. the Etherscan verifier help;
4. the required-profile missing-option path;
5. the deprecated `--chain` alias with uppercase profile text;
6. mixed-case `--profile` selection;
7. migrate with uppercase profile text and a deliberately invalid RPC;
8. console with uppercase profile text and a deliberately invalid RPC.

Return codes and stdout/stderr bytes were identical between control and Click
8.3.3. This covers the canonical `--profile`, deprecated `--chain`, and
case-insensitive `click.Choice` behavior without contacting a live endpoint.
Representative SHA-256 identities were:

| Output | SHA-256 |
|---|---|
| migrate help | `5d346f135681ccf9878522a1fc8ef80aa91dd381e24e537329e1274aef0280a8` |
| console help | `c7008eaa667c1f1cbb96de8e3a60fb6b2b89296a5aef8bbf11747925170437af` |
| verifier help | `ddc4f16e63924ec0f6129d78a9b2ceb0b46bd8f38981717b96b0c17c6b583780` |
| missing-option stderr | `6bb15095ec4ccde89547cdc7c0c8215cf5a3612b64b2aedef0ca13a68145d958` |
| legacy/mixed-case stderr | `0b5a6041c10cf6b5cb78bf2ecf5bb7d8011ed52f7dc9934baae262126d520dba` |
| migrate invalid-RPC stderr | `0305137f69a67568f2d7bd10befd628990bd1fdd8686f1259fc5c71843e7792d` |
| console invalid-RPC stderr | `3c52250c53060958a9af88a9b1736fb5e338d1a4978d1b319f9f24d2e1abe99e` |

Installed-source inspection confirmed that Click 8.2.1's editor helper invokes
`Popen(..., shell=True)`, while 8.3.3 splits the configured editor and passes
an argv list without `shell=True`, matching the advisory's patch mechanism.

### Pygments

A representative `adl` alias resolved to `AdlLexer` in both versions,
generated 50 tokens, and produced the same canonical token hash:

```text
64c5b8c8df6b1da2cf3803d52fc4eb7533ecbefa2ad1e8f1b7463d8c3ad8d34c
```

Representative Python-to-HTML output also matched:

```text
ab40e12a8cdb24b344253b72a5da51ee55590f63eab3200c43a68974ed1bae94
```

Installed-source comparison bounded the security-relevant change to the
Archetype lexer identifier/GUID regex handling. The release still spans normal
lexer fixes and drops Python 3.8 support, so the blast radius is not literally
zero; this repository's verified interpreter is 3.12.

### Pymdown

A safe, temporary local proof used a base directory and a sibling with a
shared prefix:

- Pymdown 10.16.1 allowed the Snippets read; rendered output SHA-256 was
  `8338948e51ff942370f3720bc44574401fccd92c812fedfc12fa52e0ff3a2484`.
- Pymdown 10.21.3 and both combined candidates raised
  `SnippetMissingError`; the sibling content did not render.
- Pymdown 10.16.1, 10.21.3, and both combined candidates still allowed the
  b64 outside-base file to be embedded. Exact output SHA-256 was
  `be6bb604ee1132efec6171900cee0035b7407bce91e7fd260fe81caaa6fb9d85`.

This is direct behavioral evidence that 10.21.3 retires only the Snippets
finding and cannot retire the b64 finding.

### pytest 9, Vyper, and Titanoboa

Installed metadata and behavior were examined rather than inferring
compatibility from resolver success:

- `titanoboa==0.2.7` declares `pytest` without an upper bound and
  `vyper>=0.4.2`.
- `vyper==0.4.3` runtime metadata does not require pytest, but its optional
  `test` and `dev` extras declare `pytest>=8.0,<9.0`. Those extras are not
  selected by this repository lock. The mismatch remains an upstream support
  signal and is why separate approval is required.
- The active plugins were the same under control and pytest 9:
  Hypothesis 6.138.15, pytest-cov 7.0.0, and Titanoboa 0.2.7.
- Fixture resolution for `monkeypatch`, `no_external_network`, and `ripe_hq`
  was equivalent.
- Collection remained exactly 2,837 selected / 2,979 total with 142
  deselected.
- The deliberate dependency-gate failure produced pytest's rewritten rich
  assertion diff, proving assertion rewriting remained active.
- A direct Boa check under pytest 9 compiled, deployed, observed the S1
  contract twice, and restored the clock anchor.
- H-02, S2, production artifact, ABI, and every non-S1 full-suite case passed.

The 57 pytest-candidate S1 setup errors all came from the one module-autouse
fixture:

```text
expected {"titanoboa": "0.2.7", "pytest": "8.4.2"}
actual   {"titanoboa": "0.2.7", "pytest": "9.0.3"}
```

This is a deliberate prior-approval stop, not evidence of a runtime failure.
It also means the study cannot classify the exception as immediately
retirable.

## Compatibility and test record

Every recorded pytest invocation used:

- a distinct mode-`0700` parent;
- a unique explicit `--basetemp`;
- a unique Titanoboa cache installed through a pytest plugin before test
  collection;
- `-p no:cacheprovider`;
- serial execution for complete suites;
- no skip, xfail, warning, assertion, or plugin suppression.

No other full-suite or Boa-heavy process was active when complete serial suites
were started. The H-02 command comprised
`test_base_profile_regression.py`, `test_network_profiles.py`, and
`test_secret_handling.py`.

| Candidate | `pip check` | H-01 dependency gate | H-02 | S1 | S2 test / checker | Collection | Complete serial suite |
|---|---|---|---|---|---|---|---|
| Control | pass | 16 passed | 99 passed | 57 passed in 99.53 s | 60 passed / clean | 2,837 selected; 142 deselected | 2,837 passed, 142 deselected in 318.06 s |
| Click 8.3.3 | pass | 15 passed; 1 exact-lock policy failure | 99 passed | 57 passed in 102.96 s | 60 passed / clean | identical | 1 policy failure, 2,836 passed, 142 deselected in 315.87 s |
| Pygments 2.20.0 | pass | 15 passed; 1 exact-lock policy failure | 99 passed | 57 passed in 102.84 s | 60 passed / clean | identical | 1 policy failure, 2,836 passed, 142 deselected in 315.09 s |
| Pymdown 10.21.3 | pass | 15 passed; 1 exact-lock policy failure | 99 passed | 57 passed in 102.77 s | 60 passed / clean | identical | 1 policy failure, 2,836 passed, 142 deselected in 323.10 s |
| Pymdown 11.0.0 | not applicable | resolver stop | not run | not run | not run | not run | not run |
| pytest 9.0.3 | pass | 15 passed; 1 exact-lock policy failure | 99 passed | 57 deliberate S1 setup errors in 96.08 s | 60 passed / clean | identical | 1 policy failure, 2,779 passed, 57 deliberate S1 errors, 142 deselected in 327.58 s |
| Maximum technical combined | pass | 15 passed; 1 exact-lock policy failure | 99 passed | 57 deliberate S1 setup errors in 106.80 s | 60 passed / clean | identical | 1 policy failure, 2,779 passed, 57 deliberate S1 errors, 142 deselected in 311.95 s |
| Approval-safe combined | pass | 15 passed; 1 exact-lock policy failure | 99 passed in 12.86 s | 57 passed in 101.05 s | 60 passed in 25.24 s / clean | 2,837 selected; 142 deselected in 1.61 s | 1 policy failure, 2,836 passed, 142 deselected in 309.28 s |

For every non-control valid candidate, the dependency-gate failure was
`test_selected_and_held_versions_match_lock_and_runtime`. The unchanged
repository lock correctly expected the old version while the disposable
candidate environment contained the proposed version. Click is checked first,
so combined environments report Click's mismatch before reaching later
candidate rows. No candidate failed a package behavior, deployment, fixture,
collection, compiler, contract, or application assertion outside the exact
policy/S1 gates.

The S2 checker was identical in all environments:

```text
production_occurrences=100
production_lines=95
production_files=17
bn_ids=32
bn_records=100
indirect_ids=1
cadence_candidates=455
seconds_unit_candidates=58
timestamp_ids=11
timestamp_occurrences=37
mixed_clock_functions=4
vyper_paths=92
test_nonproduction=31/29/5
test_cadence_candidates=159
```

## Compiler, ABI, and production artifact identity

Fresh compiler fingerprints were generated independently in control and every
valid candidate, with a unique private Boa cache each time. All seven
environments used `vyper==0.4.3+commit.bff19ea2`; all hashes below were
identical in every environment.

| Artifact | Optimize | Source SHA-256 | ABI SHA-256 | Creation bytecode SHA-256 | Runtime bytecode SHA-256 | Combined fingerprint |
|---|---|---|---|---|---|---|
| S1 `ClockObserver` | GAS | `238b2198a0217158db3f93000da47e4af5535883807e7b39cc3864f8d5b432f7` | `55fd4609d43321ded86224d044944b9a1955be174ca91fd55b75fb179f5090c8` | `b5f9615f2267ede387f99c77873aded9a241d30d0269a6f1df336ed93e454ecd` | `6842b313171e51a6b1b4f99143074e263de3f72d943838a3ec887ad3b1dd16d6` | `9ac4b78267b62fe4a645212b3b2bc83498afcedb7b75804d9449ea2056ce791d` |
| Production `Lootbox` | CODESIZE | `ebb4dcca8fa95bafe8e38ddc1d01886bfaceaf06302fe195f63db0bb7b3ef1da` | `e752a206ba5c78cb573c734c7bfd1c407f1cb98898d3d8e9d3513836c56f5fb2` | `9246a6d9dbee596750dc3a50d27d4418f318a62b7b4826a13f76aee37621e6ce` | `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097` | `263f6e5a75b85763dfed0656b194109512fad6856bc2acf8cccef660586aea0d` |

Each environment separately ran `scripts/export_abis.py` into an empty
disposable directory:

- 49 production ABIs exported;
- 28 mock/testing paths skipped;
- the same nine pre-existing standalone module-initializer failures;
- every relative filename and every output byte equal to control.

SHA-256 of canonical JSON mapping all 49 relative ABI filenames to their file
hashes was
`c49c61ad006d223a1bf13e2d26c5862eda82128f3cc640501c278c28f69b1dde`
in every environment. Generated `Lootbox.json` and the committed production ABI
were byte-identical at
`33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c`.

These results show no candidate compiler output, ABI identity, creation/runtime
bytecode, or committed production artifact drift. They do not authorize a
production change.

## Per-exception feasibility

### `EX-H01-CLICK-01`

**Disposition: retirable now.**

Supporting evidence:

- The fresh advisory range names 8.3.3 as the first patch.
- The one-row resolver delta is valid; all 92 other distribution versions are
  unchanged; `pip check` passes.
- The Click audit row disappears.
- The repository does not call `click.edit`.
- CLI help, failure paths, canonical `--profile`, deprecated `--chain`, mixed
  case, and H-02 behavior match control byte-for-byte.
- S1, S2, H-02, collection, complete serial suite outside the expected lock
  policy gate, all ABI exports, and both compiler fingerprints pass/match.

Required lockfile delta:

- add `click==8.3.3` as an explicit direct policy pin in `requirements.in`;
- change only `click==8.2.1` to `click==8.3.3` in the generated lock, with the
  corresponding resolver annotation/header;
- make no transitive version change.

Approval reopening: S1 does not reopen. The H-01 dependency gate and exception
record must be updated and independently reviewed under separate authorization.

Residual security risk if retained: Click 8.2.1 retains the shell-based editor
invocation. Current repository code does not reach it, so exploitation requires
a future/direct `click.edit` path plus attacker influence over editor or
filename inputs. That is bounded but nonzero developer/tooling risk.

Upgrade regression/blast-radius risk: Click 8.3.3 changes editor process
construction and includes other minor Click behavior fixes. The practical
blast radius is repository CLI parsing/help/failure behavior and transitive
MkDocs CLI use. The full CLI/deployment and serial evidence makes this low.

Smallest safe bundle: Click alone, or the three-package approval-safe bundle.

### `EX-H01-PYGMENTS-01`

**Disposition: retirable now.**

Supporting evidence:

- The fresh advisory range names 2.20.0 as the first patch.
- The one-row resolver delta is valid; all 92 other distribution versions are
  unchanged; `pip check` passes.
- The Pygments audit row disappears.
- No vulnerable Archetype lexer selection/configuration exists in the
  repository.
- Representative ADL tokens and Python HTML are byte-identical.
- S1, S2, H-02, collection, the complete serial suite outside the expected
  lock gate, ABI exports, and compiler fingerprints pass/match.

Required lockfile delta:

- add `Pygments==2.20.0` as an explicit direct policy pin in
  `requirements.in`;
- change only `pygments==2.19.2` to `pygments==2.20.0` in the generated lock;
- make no transitive version change.

Approval reopening: S1 does not reopen. H-01 gate/exception evidence still
requires separate authorization and review.

Residual security risk if retained: crafted attacker-controlled Archetype
lexer input can cause pathological regex work. No current repository path
selects that lexer, but Pygments is transitively installed and a future docs or
console path could activate it.

Upgrade regression/blast-radius risk: 2.20.0 contains lexer changes beyond the
security regex and drops Python 3.8. It can affect console/test/docs
highlighting. The project uses Python 3.12; representative rendering and the
full suite matched, so risk is low but broader than the one regex.

Smallest safe bundle: Pygments alone, or the three-package approval-safe
bundle.

### `EX-H01-PYMDOWN-SNIPPETS-01`

**Disposition: retirable now.**

Supporting evidence:

- The fresh advisory range names 10.21.3 as the first patch.
- The one-row resolver delta is valid under
  `mkdocs-material==9.5.41`; all 92 other distribution versions are unchanged;
  `pip check` passes.
- The Snippets audit row disappears while the separate b64 row remains.
- The shared-prefix traversal proof leaks under 10.16.1 and raises
  `SnippetMissingError` under 10.21.3.
- The repository has no Pymdown config or MkDocs build file.
- S1, S2, H-02, collection, the complete serial suite outside the expected
  lock gate, ABI exports, and compiler fingerprints pass/match.

Required lockfile delta:

- add `pymdown-extensions==10.21.3` as an explicit direct policy pin in
  `requirements.in`;
- change only `pymdown-extensions==10.16.1` to 10.21.3 in the generated lock;
- make no transitive version change.

Approval reopening: S1 does not reopen. H-01 gate/exception evidence requires
separate authorization and review. `EX-H01-PYMDOWN-B64-01` remains active.

Residual security risk if retained: if Snippets is enabled later with a base
path and attacker-controlled include syntax, 10.16.1's prefix comparison can
read a sibling path outside the intended base. Current configuration does not
activate the extension.

Upgrade regression/blast-radius risk: releases between 10.16.1 and 10.21.3
include Markdown block, caption, quote, emoji, critic, highlight, and regex
changes. There is no repository Pymdown configuration, and full compatibility
evidence is green, so current blast radius is low.

Smallest safe bundle: Pymdown 10.21.3 alone, or the three-package
approval-safe bundle.

### `EX-H01-PYMDOWN-B64-01`

**Disposition: retain.**

Supporting evidence:

- The fresh advisory range includes 10.21.3 and names 11.0.0 as the first
  patch.
- The local behavior proof shows the outside-base file still embeds under
  10.16.1 and 10.21.3.
- 11.0.0 contains the new restriction but cannot resolve with unchanged
  `titanoboa==0.2.7 -> mkdocs-material==9.5.41 ->
  pymdown-extensions~=10.2`.
- Changing Titanoboa or that docs graph is outside this study's authorization.

Required lockfile delta: none is safe or resolver-valid within scope. A future
retirement would require a separately approved Titanoboa/docs dependency
candidate, likely including Pymdown 11.0.0, then the complete H-01/S1/S2/H-02,
collection, suite, ABI, compiler, and artifact replay.

Approval reopening: a Titanoboa change would reopen S1's exact runtime approval
and any evidence tied to Titanoboa/Vyper/compiler behavior. Even a transitive
docs-graph override requires independent dependency/security approval.

Residual security risk if retained: if `pymdownx.b64` is enabled against
attacker-influenced Markdown/configuration, a local file outside the intended
base can be read and embedded in rendered output. The extension is installed
transitively but no current repository config enables it. The exception should
retain its reachability guard and event-driven review trigger.

Upgrade regression/blast-radius risk: Pymdown 11 is a major release with a
breaking default path restriction, new path configuration, and a Python 3.9
support drop. More importantly, forcing it would violate the installed
Titanoboa dependency graph. Risk is high and unbounded without a separate
Titanoboa candidate.

Smallest safe bundle: retain this exception while landing none, one, or all
three immediately feasible upgrades. It is the only recorded H-01 exception
that cannot be removed by a resolver-valid package-only delta under the stated
boundaries.

### `EX-H01-PYTEST-01`

**Disposition: technically viable but requires separate approval.**

Supporting evidence:

- The fresh advisory range names 9.0.3 as the first patch.
- The one-row resolver delta is valid; all 92 other distribution versions are
  unchanged; `pip check` passes.
- The pytest audit row disappears.
- Titanoboa metadata has no pytest upper bound; plugins, fixtures, collection,
  assertion rewriting, direct Boa behavior, H-02, S2, non-S1 full-suite tests,
  ABI exports, and compiler artifacts are compatible.
- Vyper 0.4.3's optional test/dev metadata explicitly caps pytest below 9.
- All 57 S1 cases correctly fail closed at the existing exact pytest 8.4.2
  approval fixture.

Required lockfile delta:

- change the existing direct input from `pytest==8.4.2` to `pytest==9.0.3`;
- change only that version in the generated lock;
- make no transitive version change.

Approval reopening: **yes**. The Track 6/S1 owner and dependency/security
reviewer must explicitly approve pytest 9, update the exact S1 expectation,
and require a fresh green 57-test S1 replay. Because Vyper's supported optional
test profile says `<9`, that approval must accept the upstream-support
deviation based on repository evidence or wait for an upstream-compatible
Vyper/Titanoboa profile. This study did not edit S1.

Residual security risk if retained: pytest 8.4.2 uses a predictable per-user
temporary base on Unix, permitting local cross-user denial of service and
possible privilege effects in a hostile multi-user environment. Private
mode-`0700` basetemps mitigate this study and should remain mandatory, but do
not patch every future pytest invocation.

Upgrade regression/blast-radius risk: this is a test-runner major-version
boundary affecting temp handling, collection, fixtures, plugins, assertion
rewriting, warnings, and teardown. It also crosses Vyper's declared optional
support bound and invalidates a prior exact S1 approval. Runtime evidence is
strong, but governance blast radius is material; classification below
`retirable now` is required.

Smallest safe bundle: pytest 9.0.3 alone after separate reapproval, or the
four-package maximum technical bundle after the same reapproval. It is not
part of the approval-safe three-package bundle.

## Smallest safe landing choices

No landing is authorized here. If the owner later authorizes implementation,
the evidence supports these bounded choices:

1. Land each of Click, Pygments, or Pymdown 10.21.3 independently. Each retires
   one exception with one version delta and no S1 reopening.
2. Land the approval-safe three-package bundle. It retires three exceptions
   with three direct pins, no transitive churn, a green S1, and no
   compatibility failure.
3. Do not include pytest 9 until the separate S1/Track 6 decision is recorded.
4. Retain Pymdown b64 until a separate Titanoboa/docs-graph study is authorized.

Any authorized implementation must regenerate the lock in its final path,
update the exact dependency gate and exception records, run a fresh no-ignore
audit, repeat the relevant suite/artifact interval, and receive independent
review. Candidate success in this report is not a substitute for that
lock-specific approval.

## Owner decision form

Complete exactly one action for each exception. Blank boxes mean no decision.

Study baseline:
`332ae2bc8e0ce4b694766d6d20759295d9267ec3`

Owner name: ____________________________________

Decision date/time and timezone: ____________________________________

Independent reviewer: ____________________________________

### Click

- [ ] Authorize a separate implementation/review change for
  `click==8.3.3`, and retire `EX-H01-CLICK-01` only after the final lock,
  gate, audit, and evidence are approved.
- [ ] Retain `EX-H01-CLICK-01`; record owner acceptance of the residual
  `click.edit` risk and keep its freshness triggers.

### Pygments

- [ ] Authorize a separate implementation/review change for
  `Pygments==2.20.0`, and retire `EX-H01-PYGMENTS-01` only after the final
  lock, gate, audit, and evidence are approved.
- [ ] Retain `EX-H01-PYGMENTS-01`; record owner acceptance of the residual
  Archetype lexer risk and keep its freshness triggers.

### Pymdown Snippets

- [ ] Authorize a separate implementation/review change for
  `pymdown-extensions==10.21.3`, and retire
  `EX-H01-PYMDOWN-SNIPPETS-01` only after final approval; explicitly retain
  the separate b64 exception.
- [ ] Retain `EX-H01-PYMDOWN-SNIPPETS-01`; record owner acceptance of the
  residual shared-prefix file-read risk and keep its freshness triggers.

### Pymdown b64

- [ ] Retain `EX-H01-PYMDOWN-B64-01` under its existing bounded controls
  because no candidate resolves within scope.
- [ ] Authorize a separate Titanoboa/docs-dependency feasibility study. This
  does not authorize Pymdown 11, a Titanoboa change, or retirement.

### pytest

- [ ] Retain `EX-H01-PYTEST-01` and continue mandatory private basetemps plus
  freshness/event review.
- [ ] Separately authorize reopening S1/Track 6 for `pytest==9.0.3`, including
  acceptance or resolution of Vyper 0.4.3's optional `<9` support bound. Do
  not retire the exception until the revised S1 gate and complete final
  evidence are independently approved.

### Bundle selection, if implementation is separately authorized

- [ ] Implement the approval-safe three-package bundle: Click 8.3.3,
  Pygments 2.20.0, Pymdown 10.21.3; retain pytest 8.4.2 and Pymdown b64.
- [ ] Implement selected immediately feasible packages separately:
  _________________________________________________________________.
- [ ] After the separate S1 approval above, evaluate the four-package maximum
  technical bundle in a final implementation interval.
- [ ] Make no dependency change; retain all five exceptions with explicit
  residual-risk ownership.

Owner acknowledgements:

- [ ] I understand that this report itself retires no exception and authorizes
  no dependency or production change.
- [ ] I understand that candidate audit remediation is not GitHub/Dependabot
  alert closure and no alert state was queried in this study.
- [ ] I understand that no Vyper, Titanoboa, production contract, deployment
  behavior, migration, manifest, or committed artifact change was tested or
  authorized.
- [ ] I accept that every retained exception remains subject to its existing
  expiry, event trigger, reachability guard, and independent review policy.

Owner decision/signature: _______________________________________________

## Evidence-quality notes and cleanup

Only clean reruns are reported above. Output-capture interruptions and early
pytest wrappers that imported Boa before assertion rewriting were replaced
with fresh, unique private runs. One supplemental safe-bundle wrapper attempt
stopped at `KeyError: RUN_DIR` before pytest initialized; its new corrected
run is the recorded result. One Pygments collection parent was not explicitly
created at mode `0700`; it was invalidated and repeated in a correctly private
parent. None of those orchestration-only attempts was treated as package
compatibility evidence.

A one-line compiler API-shape probe instantiated a Boa compiler before the
private cache setter. Inspection found no file modified in the default
Titanoboa cache during that window. It was excluded from evidence. Every
recorded compiler and pytest run used a distinct private `/private/tmp` Boa
cache.

After this report recorded the reproducible identities and results, the private
resolver, audit, install, download, ABI, pytest, pip, and Boa task root
`/private/tmp/h01-retirement-study.ARKr37` was resolved as a mode-`0700`
non-symlink directory, deleted recursively, and verified absent. The detached
worktree's ignored `.hypothesis`, `__pycache__`, and bytecode outputs were also
deleted and verified absent. The detached exact-baseline worktree remains only
because it contains this authorized untracked evidence artifact.

Cleanup status: **complete and verified**
