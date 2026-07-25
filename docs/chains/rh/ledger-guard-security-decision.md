# Track 6 S5 Ledger Guard Security and Architecture Decision

**Status:** Frozen Stage A evidence recreated on the integrated owner/H-01
baseline; required local validation and live-proof authorization-packet
preparation are complete; independent security review and every remaining
Checkpoint 0 gate stay open; Stage B and Stage C are not authorized

**Prepared:** 24 July 2026

**Recreation branch:** `rh-track-6-s5-ledger-guard-recreation`

**Recreation worktree:**
`/Users/wigglez/dev/ripe-protocol-track-6-s5-ledger-guard-recreation`

**Exact recreation baseline:**
`02787d351a3064e35d627e8fbc44150770e61c73`

**Frozen historical evidence branch/commit:**
`rh-track-6-s5-ledger-guard` at
`6652a10e4de2a74ca27be0da94be4331aeef18f6`

**Task contract:** `docs/chains/rh/track-6-s5-ledger-guard.md`

### Current recreation authority and provenance

This record was recreated, not rebased in place. The historical evidence
branch remains unchanged at commit
`6652a10e4de2a74ca27be0da94be4331aeef18f6`, tree
`c21fdef7f6156abac1da606492c7e0329315b693`. Its parent is
`de9ee3cd21977c67457a16ce333a15d92e9424df`; its original Stage A baseline is
`4966969265c6056bc7f3f139dc1a2437ef553c9f`.

The current owner instruction authorized a fresh recreation from exact
integrated `rh` commit. The controlling language was:

> The approved S5 owner/checkpoint documentation is integrated on `rh` at
> `02787d351a3064e35d627e8fbc44150770e61c73`.
>
> Preserve the old `6652a10` branch as frozen historical evidence. Following
> the brief’s default rule, create a fresh S5 recreation branch/worktree from
> exact `02787d3`; do not rewrite or silently rebase the frozen evidence
> branch.
>
> Recreate exactly the five Stage A evidence/probe files from the reviewed
> frozen package, then:

Exact baseline
`02787d351a3064e35d627e8fbc44150770e61c73` has tree
`38996e251cd3298e8f5ff5d0a5a23ee047863f69`. Before recreation, local `rh` and
the local `origin/rh` tracking ref both resolved to that commit. No live remote
query was made, because this pass prohibits RPC/external access. The
integration worktree's only observed pre-existing change was the unrelated,
untracked Track 8 owner packet
`docs/chains/rh/track-8-m0-owner-decision-packet.md`; it was not read, changed,
staged, or copied.

During the validation run, a concurrent owner workflow advanced both local
`rh` and the local `origin/rh` tracking ref to
`252ed96c5d0790463c6ba2ab5fdd40bab163943c`,
`merge: integrate Track 8 M0 owner decision packet`. Its complete committed
delta from `02787d3` adds only
`docs/chains/rh/track-8-m0-owner-decision-packet.md`; it changes no contract,
interface, ABI, dependency, migration, manifest, inventory, default, Teller,
or S5-owned path. No M0 closure is inferred without reviewing that separate
workstream. The integration worktree later showed two unrelated modified
Track 7 planning files and one untracked Track 7 H3 brief; their contents were
not read or changed. The S5 recreation branch remains based exactly on
`02787d3`, and this concurrent movement is not authority to rebase it.

The five reviewed Stage A files were restored byte-for-byte from `6652a10`
before this provenance update. The integrated S5 task contract and owner
packet were then re-read at `02787d3`. The owner packet records Mick Hagen's
owner approval and direct row 7/9 risk acceptances, but does not close the
independent-security, operations, live-proof, deployment, final-evidence, or
external-review gates. This addendum and the current sections below supersede
the historical frozen package only for current baseline, dependency,
validation, and Checkpoint 0 state. Historical observations remain labeled
and are not rewritten as if they occurred at `02787d3`.

At `02787d3`, H-01 is integrated at merge
`575d47b82055b42da2bddf1535d8076cd7cf4c63`, with its post-integration evidence
at `26eb3a78668d623be40ed2b6e16f52c919906a12`. S4 remains the approved no-code
initial-launch disposition. The delta from frozen `6652a10` to `02787d3`
changes no S5 production contract, interface, ABI, migration, manifest,
inventory, default, Teller, MissionControl, or SwitchboardDelta surface.
`contracts/data/Ledger.vy` retains Git blob
`ef02462508e01f59e8f8112ffce0ca8d17d4d0b8` and SHA-256
`00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0`
at the frozen package, recreation baseline, current branch, and working tree.

## 0. Decision summary and stop condition

The owner-selected property is one checked action per actual execution block.
For an ordinary EVM deployment, the action-block identity is native
`block.number`. For Robinhood, native `block.number` is an approximate
non-Arbitrum ancestor height and is not the required identity. The expected
Robinhood identity is the child-chain execution block returned by
`ArbSys(0x0000000000000000000000000000000000000064).arbBlockNumber()`.

The smallest recommended forward design is a single canonical Ledger source
with an immutable internal native/ArbSys action-block helper:

- one immutable source discriminator is zero for native execution
  `block.number` and exactly
  `0x0000000000000000000000000000000000000064` for ArbSys;
- every other address is rejected by the constructor;
- the `0x64` source path uses only the reviewed `arbBlockNumber()` ABI;
- the `0x64` constructor path must prove that the call succeeds and its return
  value decodes as the expected ABI;
- a read-only immutable getter exposes the selected source;
- source failure, absent code/precompile behavior, a revert, malformed return,
  or wrong ABI reverts with no fallback;
- no `chain.id` dispatch exists;
- the selected identity is read for every housekeeping call because current
  semantics write `lastTouch` even when the Boolean policy or higher-risk check
  is false;
- the existing lower-risk arming and checked-higher-risk ordering remains
  unchanged;
- the existing high-risk classification remains unchanged;
- `MissionControl.shouldCheckLastTouch` remains the enable/disable Boolean for
  the same assertion, not a source selector;
- the currently deployed Base Ledger remains untouched indefinitely; and
- Robinhood receives only a fresh Ledger deployment before any state-bearing
  user action.

This recommendation is not implementation authority. Confidence is **high**
that the single-discriminator shape is the smallest design satisfying the
owner-selected requirements, and **insufficient for Stage B** because no
owner-approved Robinhood testnet transaction was run. The isolated probe and
controlled-double tests described in section 10 establish local construction,
decoding, and fail-closed behavior. Committed official documentation and pinned
Offchain Labs source still do not prove that Robinhood's deployed `0x64`
precompile returns the receipt/RPC child block number in the exact
same-child/successive-child transaction cases. Checkpoint 0 therefore remains
open and the default is no Stage B.

The recommended helper is smaller than an external generic provider: it avoids
one deployed contract, one registry/manifest artifact, one call frame on every
native action, and one additional call frame on every Robinhood action. It also
has only one configuration value. The generic-provider alternative is rejected
for S5 because its replaceable implementation artifact does not offset that
additional deployment, manifest, call, and failure surface under the
owner-selected minimum-change requirement.

### 0.1 Verbatim owner direction and provenance

Phase A0 requires the controlling owner direction verbatim. The source is
`docs/chains/rh/minimal-contract-change-reassessment.md` as committed at the
frozen Stage A parent
`4966969265c6056bc7f3f139dc1a2437ef553c9f` (Git blob
`a50d54c702c8c9ada68a6b55e4f85bb85040e629`, SHA-256
`72c2d1fe13b6f551712935ff78eba0f801f56d80965f3f449a726c74e4a40186`).
Its program-wide minimum-change directive is:

> Deploy Robinhood with the absolute minimum necessary production
> smart-contract changes. Prefer configuration, omission, disabled features,
> existing behavior, and explicit risk acceptance over broad portability or
> future-proofing changes.

Its S5-specific owner decision, dated 24 July 2026, is:

> **Owner-selected shared-source direction — portable action-block identity
> (24 July 2026):**
>
> - update the canonical Ledger implementation to obtain a narrow
>   `ActionBlockClock` identity through a reviewed abstraction;
> - use native EVM `block.number` for future ordinary-EVM deployments;
> - use `ArbSys(0x64).arbBlockNumber()` for Robinhood's Arbitrum child-chain
>   block identity;
> - preserve the existing any-touch/checked-higher-risk ordering semantics unless
>   Stage A finds an independent defect and returns it for separate approval;
> - prohibit `chain.id` branching and prohibit using this action-block identity
>   for durations, rates, timelocks, auctions, emissions, or oracle freshness;
> - make Robinhood the first production deployment of the revised Ledger; and
> - leave the current Base Ledger deployed indefinitely because migrating its
>   extensive accounting state creates more risk than live-bytecode parity.

The same source limits the authority granted:

> **Owner decision:** the security property, Robinhood clock source, canonical
> source direction, Robinhood-first rollout, and permanent Base live-version
> exception are approved for Stage A specification work. Production
> implementation, provider shape, file set, ABI, deployment, and activation
> remain unapproved.

The quotation adds only Markdown quote prefixes; its wording is unchanged.
Sections 3–16 test and refine that direction without converting it into Stage B
authority.

## 1. Authority, historical bootstrap, and recreated evidence

### 1.1 Historical frozen-package bootstrap gates

The following table is retained as historical evidence of the original
`4966969` bootstrap. It is not the recreation bootstrap at `02787d3`.

| Gate | Frozen result |
| --- | --- |
| Integration repository | `/Users/wigglez/dev/ripe-protocol` |
| Integration worktree | Clean; `## rh...origin/rh` |
| Local `rh` | `4966969265c6056bc7f3f139dc1a2437ef553c9f` |
| Local `origin/rh` | `4966969265c6056bc7f3f139dc1a2437ef553c9f` |
| Live `git ls-remote origin refs/heads/rh` | `4966969265c6056bc7f3f139dc1a2437ef553c9f` |
| Task contract in frozen commit | Present |
| Requested branch before creation | Absent |
| Requested worktree path before creation | Absent |
| Active branch ownership of this record | None |
| Creation command | Exact `git worktree add -b ... rh` command from the task contract |
| New worktree branch | `rh-track-6-s5-ledger-guard` |
| New worktree HEAD | `4966969265c6056bc7f3f139dc1a2437ef553c9f` |
| New worktree initial state | Clean |

The first worktree-add attempt was denied by the managed filesystem when Git
tried to create a ref lock. A read-only recheck proved the branch and path were
still absent; the identical command then ran with approved Git-metadata access
and succeeded. No existing branch, worktree, or file was reused, reset,
deleted, or overwritten.

Integrated Track 6 prerequisites at the frozen commit were:

| Slice | Reviewed/integrated evidence |
| --- | --- |
| S1 clock harness | reviewed head `868e46ee03a934245df36752a96d41a7333c0091`; integration `f03e128905de395b7162110cab42582866e7ccc4` |
| S2 checked inventory | reviewed head `f0e556ce20bd21622752d441b358d23cb2b17ec2`; integration `454fbeb8e1bc1401fe1db0c44b98e9c487f3c504` |
| S3 Gate 1 | `db7ae895d1b32ae6708f2405274c32c1e3f5222e` |
| S3 inventory | `51e5c5a47ac74083affb16516cd07dd8321c0fbb` |
| S3 Gate 2 | evidence `c823300c7af418a7b226093e3a9ddf1d970e1998`; approval tip `6f4264528bf54554020d3b44a6bb232619879ea2` |
| S3 integration | `3e6e6f230169fc445d0b29454457480c62efd89a` |

### 1.2 Historical concurrent integration movement

This evidence branch remains intentionally frozen at the exact owner-specified
commit. After worktree creation and both isolated baseline runs, a separate
owner workflow advanced local `rh`, local `origin/rh`, and the live remote to
`dd51c637f1462bede7529a53427bfb4327dbfb12` at 24 July 2026 15:32 MDT,
`docs(rh): close S4 no-code checkpoint`.

The entire committed difference from `4966969` is the addition of
`docs/chains/rh/deleverage-cooldown-security-decision.md`. No production
contract, interface, ABI, test, dependency, migration, inventory, or S5-owned
path changed. That later record closes S4's no-code initial-launch disposition
with owner and independent-security approval and still forbids S4 Stage B/C.
It selects unchanged Deleverage/SwitchboardDelta/Teller source, Robinhood
cooldown zero, and mandatory S4 reopening before Underscore inclusion or any
nonzero cooldown.

This Stage A record does not silently rebase across that movement. Any Stage B
must be recreated or explicitly reconciled on the then-approved baseline,
re-read the integrated S4 record, reproduce all evidence, and obtain renewed
Checkpoint 0 approval. The post-S4 `rh` movement is not a reason to change this
record's production-source findings because its delta is documentation-only.

During the reviewer-correction pass, local `rh`, local `origin/rh`, and the
live remote advanced again to
`063d9459c4c0acf29a4d4e59251ad32bf2d71184` at 24 July 2026 16:01 MDT,
`docs: reconcile S4 and add Track 7 H-02 brief`. Relative to `dd51c637`, that
commit changes five shared planning documents and adds
`docs/chains/rh/track-7-h2-network-profiles-cli.md`; it changes no contract,
interface, ABI, test, dependency, migration, inventory, or S5-owned path. Its
S5 owner direction, Ledger disposition, and Checkpoint 0 boundary are
unchanged. It reconciles the already-consumed S4 no-code decision into shared
planning and assigns later S4 assertions to Track 7 H-08; the new H-02 brief is
Track 7-owned. This evidence branch remains on the required frozen parent, and
the same Stage B recreate/reconcile requirement applies.

During this uncommitted correction/probe pass, local `rh` and the cached
`origin/rh` tracking ref had advanced to
`2517eeb0013cdb277dc4815db4b524d7a090d682`,
`merge: integrate Track 8 stock token vault specification`. No live remote
query was made in this pass. The local committed difference from `063d945`
adds only `docs/chains/rh/stock-token-vault-change-specification.md` and
`docs/chains/rh/stock-token-vault-change-validation-plan.md`; it changes no
production contract, interface, ABI, test, dependency, migration, inventory,
or S5-owned path. This does not relax the requirement to recreate or expressly
reconcile Stage B on its then-approved baseline.

Before this five-file Stage A package was committed locally, local `rh` and the
cached `origin/rh` tracking ref advanced to
`03c07f01dda03a5529c602aafbfe5545ae86df69`,
`merge: integrate Track 8 M0 evidence`. Relative to `2517eeb`, the merge adds
only `docs/chains/rh/stock-token-m0-evidence.md` and
`docs/chains/rh/stock-token-m0-raw-evidence.json`. This
documentation/evidence-only Track 8 M0 merge changes no S5 production
contract, interface, ABI, dependency, migration, or inventory surface and does
not close M0. No live remote query was made. It does not relax the requirement
to integrate H-01 first or to recreate or expressly reconcile Stage B on its
then-approved baseline.

The current recreation supersedes those stale-baseline stops without rewriting
them: branch `rh-track-6-s5-ledger-guard-recreation` was created directly from
exact `02787d351a3064e35d627e8fbc44150770e61c73`. The frozen branch remains at
`6652a10`; it was not reset, rebased, amended, or otherwise changed.

### 1.3 Current integrated dependency state

| Workstream | Integrated state at recreation baseline `02787d3` | S5 consequence |
| --- | --- | --- |
| H-01 dependency security | integrated at merge `575d47b82055b42da2bddf1535d8076cd7cf4c63`; post-integration evidence at `26eb3a78668d623be40ed2b6e16f52c919906a12`; approved Candidate A lock hashes are recorded below | use the integrated environment without changing dependencies; rerun the gate, focused tests, S1/S2, targeted regressions, collection, and full suite |
| S4 deleverage cooldown | integrated owner/security-approved no-code disposition; no S4 Stage B/C | no production overlap; unchanged zero-cooldown launch posture remains a separate S4 handoff |
| Track 7 deployment support | owns migration namespace, manifest, activation, and later proof operations | S5 prepares evidence only; no migration, signer, RPC, or deployment action |
| Track 8 | documentation/evidence-only integrations are present, including M0; M0 is not closed | no current production overlap and no authority to touch Track 8 |

H-01's five bounded exceptions and their expiry/review controls remain in
force. Recreating S5 does not close, waive, extend, or modify them.

### 1.3.1 Historical adjacent dependency snapshot

State was rechecked at 24 July 2026 15:38 MDT. This table is the
contemporaneous snapshot, not a claim of current `rh`.
Section 1.2 records the superseding 16:01 MDT documentation-only movement to
`063d9459c4c0acf29a4d4e59251ad32bf2d71184` and the later local/cached-ref
movements through `2517eeb0013cdb277dc4815db4b524d7a090d682` and
`03c07f01dda03a5529c602aafbfe5545ae86df69`.

| Workstream | Exact observed state | S5 consequence |
| --- | --- | --- |
| H-01 dependency security | local branch `rh-track-7-h1-dependency-security` at `789a8df27cea479e477ff1323b0a7d83b554d441`; only `docs/chains/rh/evidence/dependency-security-gate.md` differs from current `rh`; not integrated; its refreshed minimum-candidate owner/security authorization packet remains pending | Stage B remains blocked until H-01 is approved, integrated, and the exact toolchain is reproduced |
| S4 deleverage cooldown | integrated on `rh` at `dd51c637f1462bede7529a53427bfb4327dbfb12`; no-code initial-launch disposition owner- and security-approved; Stage B/C forbidden | no current production-file overlap; future S4 reopening would overlap Teller/Delta review and requires fresh reconciliation |
| Track 7 deployment support | branch `rh-track-7-deployment-support` at `d4805439cc55816df48340a53305d216419e5fc8`; ancestor of frozen `rh` | owns reservation `0030_Track6S5LedgerGuard.py` and fresh RH deployment integration |
| Track 8 stock-token vault | remote branch `origin/rh-track-8-stock-token-vault-change` at `7122d0dd1304a4d6189901cb3fbfcfae72fff2f4`; two documentation records differ; not integrated | no current S5 file overlap; Stock Token value paths remain disabled pending their own complete containment approval, implementation, and audit |

Floating branches are time-qualified evidence, not integration truth.

### 1.4 Historical frozen hashes

All values below are SHA-256 at
`4966969265c6056bc7f3f139dc1a2437ef553c9f`.

| Input | SHA-256 |
| --- | --- |
| `docs/chains/rh/track-6-s5-ledger-guard.md` | `266112d5ee1cb0f261d4d3b833ea6c5911d4b62c5646718063e6808a2c1a4dd5` |
| `docs/chains/rh/shared-block-clock-specification.md` | `9c501491c8a96a08ef5136f836baea04ea041eb525a703862d3925e19c7afec4` |
| `docs/chains/rh/block-clock-validation-plan.md` | `b6891973cea3cb72dade1975f443b49b7ef5c210c481ac62472d07f15ed8e5bc` |
| `docs/chains/rh/block-number-inventory.md` | `d6f5e89a673bf74f6ebd68033348e48ba295cd2c5c0c903869a8b339a10699d4` |
| `docs/chains/rh/component-matrix.md` | `bea64119069943534d6b877c04f453f82f8560540099593841c4c770706764c7` |
| `contracts/data/Ledger.vy` | `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0` |
| `contracts/core/Teller.vy` | `51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198` |
| `contracts/core/TellerUtils.vy` | `c6351363db4f77318584dfc60b868f847ec894221ada37007b118881e254ecfe` |
| `contracts/data/MissionControl.vy` | `5110d7ccea635b96fd88fe818afd97494cfe9d47648cd09f4632e8c68d0f19a1` |
| `contracts/config/SwitchboardDelta.vy` | `2c76e1a2b985884adc2db1b419776eddf7bd6c355268dc527d573453421bfbe1` |
| `scripts/abis/Ledger.json` | `80ffdd691f25ae5e6feba917ec6c5fa6f6e95a6ea321b46cad3de735c1710fbd` |
| `scripts/abis/Teller.json` | `e5b696f0e22c2196806cd84f27a037d21ca567d702a357f3a61a574fd514e1f4` |
| `scripts/abis/TellerUtils.json` | `728a02157129e67eaa9567c587e2869586b8fc5de5d1542a83ed69432d295d3f` |
| `scripts/abis/MissionControl.json` | `a10868fa4bc861c233a8e995844339bf98b8a3d045feb1aed98a1d1731821b03` |
| `scripts/abis/SwitchboardDelta.json` | `461275efff3493e0787f63b6b9756e3557801093df25b7ed1df5f04098421147` |
| `config/block-clock-inventory.json` | `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb` |

### 1.4.1 Recreated-baseline hashes

The following SHA-256 values were recomputed from exact baseline `02787d3`
before any Stage A file was changed:

| Input | SHA-256 |
| --- | --- |
| `docs/chains/rh/track-6-s5-ledger-guard.md` | `5a67ddc86dcd81f8b416b8749d5bec158bdb7e409a92ef2b0d618ad16c6e822c` |
| `docs/chains/rh/track-6-s5-checkpoint-0-owner-decision-packet.md` | `4ae312fd210abce7f428ac54e1bd41156f9eafa0cc254f46c7b5bb40aa3e4e8b` |
| `docs/chains/rh/evidence/dependency-security-gate.md` | `5cb0d37aa50ab66b13d8389eecafd2bcd1f47dd7a3fd6fb6648e34470393fa87` |
| `docs/chains/rh/deleverage-cooldown-security-decision.md` | `98cbe896e502ad280f4b3de74e45181937b5085988dd9c6d45d2ce0e167a755b` |
| `docs/chains/rh/shared-block-clock-specification.md` | `7afcd89fe4b07c597ae1670f453010c66bbceaa7659cd7411ad2eb01b342a4cf` |
| `docs/chains/rh/block-clock-validation-plan.md` | `b6891973cea3cb72dade1975f443b49b7ef5c210c481ac62472d07f15ed8e5bc` |
| `docs/chains/rh/block-number-inventory.md` | `d6f5e89a673bf74f6ebd68033348e48ba295cd2c5c0c903869a8b339a10699d4` |
| `docs/chains/rh/component-matrix.md` | `33747982b11a1f9430619710b8b2007113dfb5961a90162def4c852c1b6b18e6` |
| `contracts/data/Ledger.vy` | `00d86847273621857b80701be5faf7ca88ff9505f68671d5b6ab3c8b4ec972e0` |
| `contracts/core/Teller.vy` | `51cf13e3c9d58262ba446a462332d8f4f181c07ce689031b2398c20137f04198` |
| `contracts/core/TellerUtils.vy` | `c6351363db4f77318584dfc60b868f847ec894221ada37007b118881e254ecfe` |
| `contracts/data/MissionControl.vy` | `5110d7ccea635b96fd88fe818afd97494cfe9d47648cd09f4632e8c68d0f19a1` |
| `contracts/config/SwitchboardDelta.vy` | `2c76e1a2b985884adc2db1b419776eddf7bd6c355268dc527d573453421bfbe1` |
| `scripts/abis/Ledger.json` | `80ffdd691f25ae5e6feba917ec6c5fa6f6e95a6ea321b46cad3de735c1710fbd` |
| `scripts/abis/Teller.json` | `e5b696f0e22c2196806cd84f27a037d21ca567d702a357f3a61a574fd514e1f4` |
| `scripts/abis/TellerUtils.json` | `728a02157129e67eaa9567c587e2869586b8fc5de5d1542a83ed69432d295d3f` |
| `scripts/abis/MissionControl.json` | `a10868fa4bc861c233a8e995844339bf98b8a3d045feb1aed98a1d1731821b03` |
| `scripts/abis/SwitchboardDelta.json` | `461275efff3493e0787f63b6b9756e3557801093df25b7ed1df5f04098421147` |
| `config/block-clock-inventory.json` | `cebc434d4e2628afd404ff3c76874e26d6e947783dd75ec74dd10001458df6fb` |
| `requirements.in` | `2523c04409946a6625e30e5e4aa4f711663924f4a674f4cfd5fee5b7bbb3b80d` |
| `requirements.txt` | `d2e12a6f0cfd128c3891634efafbba8305878bef7a7c5db33e25ebe93b0d2bce` |
| `tests/deployment/test_dependency_gate.py` | `d8f4c504623a7393c0e53cafdb9c81288981d655c329582eb70be1accc64e2aa` |

### 1.5 Toolchain and baseline validation

| Tool | Version |
| --- | --- |
| Python | `3.12.0` |
| Vyper package | `0.4.3` |
| Vyper compiler | `0.4.3+commit.bff19ea2` |
| Titanoboa | `0.2.7` |
| pytest | `8.4.2` |

The test environment requires `ETHERSCAN_API_KEY` at plugin import even for the
local in-memory profile. All authoritative local runs used the non-secret value
`local-placeholder`; no RPC URL was supplied and no live fork was used.

Both the clean integration worktree before S5 creation and the isolated S5
worktree reproduced:

| Baseline | Integration result | Isolated S5 result |
| --- | --- | --- |
| S1 clock profiles | 57 passed in 28.04 s | 57 passed in 29.40 s |
| S2 checker | clean; exact counts below | clean; same exact counts |
| S2 inventory tests | 60 passed in 26.33 s | 60 passed in 26.65 s |
| collection | 2,722 selected / 2,864 total; 142 deselected in 1.43 s | 2,722 selected / 2,864 total; 142 deselected in 1.60 s |
| full suite | 2,722 passed, 142 deselected in 302.36 s | 2,722 passed, 142 deselected in 299.32 s |

Exact checker output in both worktrees:

```text
CLOCK_INVENTORY_OK schema=1 production_occurrences=100 production_lines=95 production_files=17 bn_ids=32 bn_records=100 indirect_ids=1 cadence_candidates=455 seconds_unit_candidates=58 timestamp_ids=11 timestamp_occurrences=37 mixed_clock_functions=4 vyper_paths=92
CLOCK_INVENTORY_NONPROD mock=0/0/0 testing=0/0/0 test=31/29/5
CLOCK_INVENTORY_NONPROD_CADENCE mock=0 testing=0 test=159
```

The first sandboxed isolated collection attempt could not write two Titanoboa
compiler-cache files under the user cache and ended with 2 collection errors
after reporting 2,562 selected / 2,704 total and 142 deselected. The same
unchanged command was rerun with local compiler-cache write access and produced
the authoritative 2,722/2,864 result above. This was an environment permission
failure, not a source or test failure. A separate accidental direct targeted
invocation omitted the contract-required `PYTHONPATH=.` and failed at plugin
import with `No module named 'config.BluePrint'`; the exact authorized command
then passed. The first Base-enabled reproduction attempt encountered the same
local compiler-cache permission boundary; the identical local-only run passed
after cache-write access was granted. Repeated shell startup also printed a
non-fatal pyenv rehash warning because its shared shim directory was read-only.
No authoritative run reported a skip or xfail; the 142 full-suite deselections
are the repository's normal local-profile selection.

### 1.5.1 `02787d3` recreation audit-point validation

The authoritative recreation used retained approved H-01 Candidate A
interpreter
`/private/tmp/h01-final-review.dL2pqo/candidate/bin/python`: Python `3.12.0`,
Vyper `0.4.3` / compiler `0.4.3+commit.bff19ea2`, Titanoboa `0.2.7`, pytest
`8.4.2`, and locked `cbor2 5.9.0`. `python -m pip check` reported no broken
requirements. No dependency was installed, refreshed, or modified.

The exact independently reviewed five-file bytes were committed locally,
without push, at audit point
`2f6a49b6c82e69bda54f2fd64d2fe03132e0db21`. The table below records the
validation of that audit point.

| Validation | Audit-point recreation result |
| --- | --- |
| Python compilation | runner and focused test compiled; exit `0` |
| local dry-run | exit `0`; no RPC/secret read; artifact hashes exactly reproduce section 2.1 |
| H-01 dependency gate | 16 passed in 1.46 s |
| focused action-block probe | 30 passed in 27.35 s; 64.23 s wall |
| all probe suites | 70 passed in 31.65 s; 73.79 s wall |
| `tests/data/test_ledger.py` | 101 passed in 28.53 s; 65.69 s wall |
| `tests/config/test_switchboard_delta.py` | 109 passed in 113.05 s; 150.48 s wall; 3 cache-redirection assert-rewrite warnings |
| `tests/core/teller/test_teller_deposit.py` | 26 passed in 28.89 s; 66.21 s wall |
| `tests/core/teller/test_teller_withdraw.py` | 32 passed in 32.05 s; 68.86 s wall |
| `tests/core/teller/test_teller_rebalance.py` | 22 passed in 28.98 s; 65.82 s wall |
| `tests/core/creditEngine/test_credit_borrow.py` | 39 passed in 30.96 s; 68.19 s wall |
| `tests/core/creditEngine/test_credit_repay.py` | 17 passed in 29.96 s; 67.97 s wall |
| `tests/vaults/modules/test_stab_vault_claims.py` | 51 passed in 33.01 s; 71.41 s wall |
| S1 clock profiles | 57 passed in 28.47 s; 69.08 s wall |
| S2 inventory tests | 60 passed in 26.74 s; 27.96 s wall |
| collection | 2,768 selected / 2,910 total; 142 deselected in 5.07 s; 6.51 s wall |
| complete serial suite | 2,768 passed, 142 deselected, 3 cache-redirection assert-rewrite warnings in 313.58 s; 373.49 s wall |

The S2 checker exited `1` on exactly seven `INV-CADENCE-NEW` findings and one
`INV-PATH-NEW` finding, all caused by the authorized non-production probe
source/runner/test identifiers. This is a real expected Stage A finding:
inventory editing is prohibited until Stage C, so the result is recorded
rather than bypassed.

Two non-authoritative environment diagnostics preceded the passing reruns. The
inherited `ripe-lite` interpreter failed one of 16 H-01 cases because installed
`cbor2 5.7.0` did not match locked `5.9.0`; no dependency was changed, and the
retained approved Candidate A environment passed 16/16. A first
`switchboard_delta` collection attempt could not write the protected default
Titanoboa cache; the identical source then passed with Boa explicitly directed
to `/private/tmp/s5-recreation-cache/titanoboa`. That preload accounts for the
three `PytestAssertRewriteWarning` lines in the switchboard, collection, and
full-suite reports and changes no contract/test semantics.

### 1.5.2 Uncommitted post-review hardening validation

After the audit-point commit, the runner and focused tests received a separate,
uncommitted hardening delta. It disables HTTP redirects, adds explicit
preflight rejection coverage for nonce mismatch, an occupied predicted address,
and insufficient balance, and persists the final result and fee projection
before stopping on an observation-burst total-fee-cap violation. Documentation
was updated to distinguish the frozen, audit-point, and hardening evidence.
The test-only Vyper probe and all of its compiler artifacts remain unchanged.

| Validation | Post-review hardening result |
| --- | --- |
| Python compilation | runner and focused test compiled; exit `0` |
| local dry-run | exit `0`; no RPC/secret read; all source and artifact hashes unchanged |
| H-01 dependency gate | 16 passed in 1.49 s; 2.37 s wall |
| focused action-block probe | 35 passed in 26.90 s; 63.98 s wall |
| all probe suites | 75 passed in 31.24 s; 73.04 s wall |
| S1 clock profiles | 57 passed in 27.18 s; 64.62 s wall |
| S2 inventory tests | 60 passed in 26.08 s; 26.97 s wall |
| eight required targeted regression files | 397 passed, 3 cache-redirection assert-rewrite warnings in 52.59 s; 91.64 s wall |
| collection | 2,773 selected / 2,915 total; 142 deselected, 3 cache-redirection assert-rewrite warnings in 1.23 s; 2.36 s wall |
| complete serial suite | 2,773 passed, 142 deselected, 3 cache-redirection assert-rewrite warnings in 297.06 s; 352.63 s wall |

The post-hardening S2 checker again exited `1` with exactly the same seven
`INV-CADENCE-NEW` findings and one `INV-PATH-NEW` finding caused solely by the
authorized test-only probe package. A future merge is prohibited until the
owner approves either the Stage C inventory treatment or removal of the probe
package, because merging while those findings remain would break the clean-S2
gate used by other workstreams.

## 2. External source authority

External sources were retrieved read-only on 24 July 2026. No live RPC, testnet
transaction, explorer mutation, GitHub mutation, or other external write was
performed.

| Source | Exact evidence | Authority and limitation |
| --- | --- | --- |
| [Robinhood Chain full-node guide](https://docs.robinhood.com/chain/run-a-full-node/) | Robinhood is an Arbitrum Chain using Nitro; published node image `offchainlabs/nitro-node:v3.11.2-3599aca`; published ArbOS 61 profile | official RH configuration, not an in-contract precompile probe |
| [Robinhood Chain network guide](https://docs.robinhood.com/chain/connecting/) | mainnet chain ID 4663; testnet 46630 | network identity only; no production `chain.id` branch is proposed |
| [Arbitrum block-number guide](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time) | native `block.number` on an Arbitrum chain is an approximate ancestor-chain height; multiple child blocks can share it; receipt/RPC `blockNumber` is child-chain height; `ArbSys(100).arbBlockNumber()` returns child-chain block height | official semantic contract; page last updated 20 July 2026; does not prove RH deployment |
| [Offchain Labs Nitro commit `3599acae`](https://github.com/OffchainLabs/nitro/commit/3599acae1ad2fab4059fc46453c9cd3294126641) | exact full commit `3599acae1ad2fab4059fc46453c9cd3294126641`, signed merge dated 1 July 2026 | matches RH's published image suffix |
| [Pinned Nitro `ArbSys.go`](https://github.com/OffchainLabs/nitro/blob/3599acae1ad2fab4059fc46453c9cd3294126641/precompiles/ArbSys.go) | `ArbSys.Address` is `0x64`; `ArbBlockNumber` returns `evm.Context.BlockNumber`; `ArbOSVersion` returns `55 + c.State.ArbOSVersion()` | implementation source pinned to the published Nitro commit; therefore Robinhood's published ArbOS profile `61` implies raw precompile return `61 + 55 = 116` |
| [Pinned Nitro precompile interface](https://github.com/OffchainLabs/nitro-precompile-interfaces/blob/7e88c8cc53c2e96201a23c638f1536557b9cb68b/ArbSys.sol) | Nitro commit pins submodule `7e88c8cc53c2e96201a23c638f1536557b9cb68b`; interface says the precompile exists on every Arbitrum chain at address 100/`0x64`, `arbBlockNumber()` returns the Arbitrum block number, and `arbOSVersion()` is the internal build number `55 +` the Nitro ArbOS version | authoritative interface for the published Nitro source and independent confirmation of the offset; selectors independently reproduced as `0xa3b1b31d` and `0x051038f2` |

The evidence distinguishes four values that must not be conflated:

1. native in-contract `block.number` on Robinhood: approximate ancestor height;
2. receipt/RPC `blockNumber`: Robinhood child-chain execution block;
3. RPC `l1BlockNumber`: ancestor height; and
4. in-contract `ArbSys(0x64).arbBlockNumber()`: expected child-chain execution
   block.

Only item 4 can satisfy the selected in-contract property on Robinhood.
Documentation and pinned source are necessary but insufficient: an
owner-approved testnet probe must prove that items 2 and 4 agree for a
transaction, that two calls/transactions in one child block share the value,
and that successive child blocks advance even when item 1 repeats.

The version gate separately distinguishes the **published Robinhood ArbOS
profile** (`61`) from the raw **`ArbSys.arbOSVersion()` return** (`116`). The
relationship is derived from the pinned implementation and interface:
`61 + 55 = 116`. Approval records both values and the offset; preflight accepts
only a well-formed 32-byte return equal to `116`. Raw `61`, any other value,
malformed data, and reversion all fail closed.

### 2.1 Owner-authorized isolated probe status

The owner subsequently authorized a Robinhood-testnet-only proof but did not
provide the exact approved endpoint, signer, signer-fund approval, nonce, or
maximum total fee. The new isolated package therefore stopped at local dry-run:

- `contracts/testing/ActionBlockIdentityProbe.vy`;
- `scripts/probes/action_block_identity_probe.py`;
- `tests/probes/test_action_block_identity_probe.py`; and
- `docs/chains/rh/evidence/ledger-action-block-testnet-proof.md`.

The focused local slice passed 30 tests, including compatible and
missing/reverting/malformed/incompatible `0x64` doubles, constructor and
postdeployment fail-closed behavior, approval/preflight logic, bounded topology
analysis, exact artifact hashing, production migration/ABI-export exclusion,
published-profile/derived-raw-ArbSys-version matching, separate
endpoint/signing-secret evidence, deterministic pre-broadcast transaction
journaling, RPC hash matching, ambiguous acceptance, and second-burst failure
handling. The dry-run
compiled creation hash
`0x835fdafe8f7e61253237837ae17cf7985a3cef2eb7e1c274ba2f98f8ea044333`
and runtime hash
`0xd4114b7780177700bfac10a60e77a4ca49a4ad10a92f01685ea72bbd1c54ab56`.
It reported `rpc_contacted=false`, `rpc_endpoint_read=false`,
`signing_secret_read=false`, and `broadcast_enabled=false`.

This is non-production evidence only. All five live topology requirements
remain not attempted and inconclusive, and the sanitized evidence record names
every input required before read-only preflight. The package neither implements
the production Ledger nor changes the recommendation solely because a local
double passes.

## 3. Current behavior and provenance

### 3.1 Current Ledger/Teller contract

`Ledger.checkAndUpdateLastTouch` currently:

1. accepts calls only from the RipeHq-registered Teller;
2. rejects while Ledger is paused;
3. if `_shouldCheck` is true, rejects when `lastTouch[_user] == block.number`;
4. always writes `lastTouch[_user] = block.number`; and
5. then rejects a locked user.

Any later revert rolls back the write. The zero address is not rejected by
Ledger. The direct zero-address test deliberately accepts either outcome and
therefore does not itself enforce the now-selected preservation requirement.

`Teller._performHousekeeping` currently:

1. reads `MissionControl.shouldCheckLastTouch`;
2. if enabled, classifies the supplied canonical `_user` through
   `TellerUtils.isUnderscoreWalletOrVault`;
3. sets `shouldCheckLastTouch = _isHigherRisk and not isUnderscore`;
4. calls Ledger;
5. updates the Curve green-reference-pool snapshot if configured; and
6. optionally updates debt, requiring a true result only for a higher-risk
   call.

Therefore the protected ordering is **any successful housekeeping touch arms;
only the later higher-risk, non-Underscore touch checks**. The policy is not
"one transaction per block," not "one high-risk action only regardless of
lower-risk touches," and not a reentrancy lock.

`DefaultsBase.shouldCheckLastTouch()` returns true.
`DefaultsLocal.shouldCheckLastTouch()` returns false. MissionControl copies the
default at construction, and SwitchboardDelta can timelock a later Boolean
change. The Boolean controls only the equality assertion; every housekeeping
call still writes `lastTouch`.

### 3.2 Current sequence table

An additional local, in-memory reproduction loaded the committed
`DefaultsBase.vy`, asserted that `shouldCheckLastTouch()` returned true, and
used that returned value—not a hard-coded true—for checked Ledger calls. A
minimal in-memory RipeHq/Switchboard supplied only Teller and lock authority;
no source file or RPC was used. The 4.11-second run printed:

```text
BASE_GUARD_REPRO_OK low_high=reject high_low=allow high_low_high=reject next_block=allow underscore_equivalent_unchecked=allow locked_flag_false=reject two_users=isolated zero_user=accepted block=2
```

The Underscore case is labeled "equivalent unchecked" because Teller's
committed classification source, not the minimal harness, derives the false
check. Together the Base default, Teller classification source, and direct
Ledger execution reproduce the current contract without pretending the harness
is a full Teller graph.

For reproducibility, the same Python program from the successful local run is
preserved below with whitespace normalized out of its original `python -c`
shell wrapper. It can be executed from this worktree with the shown environment
and does not configure or use an RPC:

```bash
PYTHONPATH=. ETHERSCAN_API_KEY=local-placeholder python - <<'PY'
import boa

ZERO = "0x0000000000000000000000000000000000000000"
TELLER = "0x0000000000000000000000000000000000000017"
ADMIN = "0x00000000000000000000000000000000000000a1"

switchboard = boa.loads(
    """# @version 0.4.3
ADMIN: immutable(address)
@deploy
def __init__(_admin: address):
    ADMIN = _admin
@view
@external
def isSwitchboardAddr(_addr: address) -> bool:
    return _addr == ADMIN
""",
    ADMIN,
)

# Frozen Addys.vy IDs: Teller = 17; Switchboard = 6.
hq = boa.loads(
    """# @version 0.4.3
TELLER: immutable(address)
SWITCHBOARD: immutable(address)
@deploy
def __init__(_teller: address, _switchboard: address):
    TELLER = _teller
    SWITCHBOARD = _switchboard
@view
@external
def getAddr(_regId: uint256) -> address:
    if _regId == 17:
        return TELLER
    if _regId == 6:
        return SWITCHBOARD
    return empty(address)
@view
@external
def isValidAddr(_addr: address) -> bool:
    return False
""",
    TELLER,
    switchboard.address,
)

defaults_base = boa.load("contracts/config/DefaultsBase.vy")
assert defaults_base.shouldCheckLastTouch() is True
guard_enabled = defaults_base.shouldCheckLastTouch()
ledger = boa.load("contracts/data/Ledger.vy", hq.address, ZERO)
users = [f"0x{i:040x}" for i in range(1001, 1009)]

ledger.checkAndUpdateLastTouch(users[0], False, sender=TELLER)
with boa.reverts("one action per block"):
    ledger.checkAndUpdateLastTouch(users[0], guard_enabled, sender=TELLER)

ledger.checkAndUpdateLastTouch(users[1], guard_enabled, sender=TELLER)
ledger.checkAndUpdateLastTouch(users[1], False, sender=TELLER)

ledger.checkAndUpdateLastTouch(users[2], guard_enabled, sender=TELLER)
ledger.checkAndUpdateLastTouch(users[2], False, sender=TELLER)
with boa.reverts("one action per block"):
    ledger.checkAndUpdateLastTouch(users[2], guard_enabled, sender=TELLER)

ledger.checkAndUpdateLastTouch(users[3], False, sender=TELLER)
with boa.reverts("one action per block"):
    ledger.checkAndUpdateLastTouch(users[3], guard_enabled, sender=TELLER)
boa.env.time_travel(blocks=1)
ledger.checkAndUpdateLastTouch(users[3], guard_enabled, sender=TELLER)

ledger.checkAndUpdateLastTouch(users[4], False, sender=TELLER)
ledger.checkAndUpdateLastTouch(users[4], False, sender=TELLER)

ledger.setLockedAccount(users[5], True, sender=ADMIN)
with boa.reverts("account locked"):
    ledger.checkAndUpdateLastTouch(users[5], False, sender=TELLER)

ledger.checkAndUpdateLastTouch(users[6], guard_enabled, sender=TELLER)
ledger.checkAndUpdateLastTouch(users[7], guard_enabled, sender=TELLER)
ledger.checkAndUpdateLastTouch(ZERO, guard_enabled, sender=TELLER)
assert ledger.lastTouch(ZERO) == boa.env.evm.patch.block_number

print(
    "BASE_GUARD_REPRO_OK "
    "low_high=reject "
    "high_low=allow "
    "high_low_high=reject "
    "next_block=allow "
    "underscore_equivalent_unchecked=allow "
    "locked_flag_false=reject "
    "two_users=isolated "
    "zero_user=accepted "
    "block="
    + str(boa.env.evm.patch.block_number)
)
PY
```

The canonical embedded program body has SHA-256
`684ea2b90043221009cd8ce23792b128fb70c38886806a40f55072e1827e9642`.
The hash includes the provenance-only registry-ID comment added during
re-review.

The executable statements, values, and assertions are semantically identical
to the original run. The program proves a direct Ledger call with the check
disabled; it does **not** independently execute or prove Teller's Underscore
classification. That exemption conclusion remains the combination of the
separately inspected Teller classification source and this equivalent unchecked
Ledger path. Any completion summary should preserve that distinction.

These are reproduced/source-proven current results under a Base-enabled
Boolean:

| Sequence for one ordinary user in one native `NUMBER` | Current result |
| --- | --- |
| first checked higher-risk action | succeeds and writes current `NUMBER` |
| checked higher-risk, then checked higher-risk | second rejects |
| lower-risk, then checked higher-risk | checked action rejects because the lower-risk touch armed the key |
| checked higher-risk, then lower-risk | lower-risk touch succeeds and rewrites the same value |
| checked higher-risk, lower-risk, checked higher-risk | final checked action rejects |
| repeated lower-risk touches | succeed and retain the same value |
| rejected sequence, then `NUMBER + 1` | checked action can proceed if no other condition blocks |
| two different users in one `NUMBER` | isolated keys; each user's first checked action can succeed |
| Underscore-classified user | assertion is skipped; write still occurs |
| locked user with Boolean false | rejects; reverted call leaves no partial write |
| zero-address user | currently succeeds and writes `lastTouch[address(0)]`; S5 preserves this behavior subject to explicit risk acceptance |
| Ledger paused | rejects before comparison/write |
| Teller paused on normal Teller path | rejects before housekeeping |

The committed direct Ledger tests prove first use, equality rejection, next
native block, multiple-user isolation, Teller-only authorization, pause
behavior, repeated unchecked calls, and checked-then-unchecked ordering.
Source inspection proves lower-then-checked and checked-unchecked-checked from
the same equality/write order. Existing tests do not explicitly exercise those
two sequences through Teller with `DefaultsBase` enabled; this gap must be
closed in Stage B.

The selected portable Robinhood result, not yet implemented, is:

| Sequence | Selected portable result |
| --- | --- |
| two checked actions for one user in the same Robinhood child block | second action rejects |
| checked actions in successive child blocks sharing one ancestor `block.number` | second action may proceed |
| unchecked lower-risk touch then checked higher-risk action in one child block | higher-risk action rejects |
| checked higher-risk touch then unchecked lower-risk touch in one child block | lower-risk action may proceed |
| two users in one child block | per-user keys remain isolated |
| configured source reverts, is malformed, repeats contrary to observed child blocks, or violates monotonic assumptions | fail closed; never use ancestor `block.number` |

The very next child block clears the equality guard regardless of elapsed wall
time, oracle state, price snapshots, or ancestor-height movement.

### 3.3 Historical intent reconstruction

| Commit | Actual contribution |
| --- | --- |
| `4ac5449` (`last touch`) | introduced Ledger `lastTouch` and Teller classification plus direct Ledger tests; also changed adjacent CreditEngine/AuctionHouse behavior, so the message alone is not a complete threat specification |
| `3deb55894f3c6418e85ddce78a4489006625e8c1` | introduced Base `true` / local `false` default split and Defaults interface support |
| `a62309c4eae5e98216712c5cfd05f5f58f25e2e1` (`bug fix`) | removed caller input from housekeeping classification and changed the exemption to the canonical `_user` wallet/vault classification |

The current source, not old test headings or commit messages, is authority.
The AuctionHouse hunk in `4ac5449` only added a graceful early return when an
auction's `_recipient` equals `_liqUser`; it did not add housekeeping.
Notably, liquidation housekeeping touches the keeper (`msg.sender`) as a
lower-risk action after liquidation; it does not apply the checked action to
the liquidated user. The guard is therefore not a general liquidation-target
guard.

## 4. Complete Teller housekeeping call graph

The canonical high-risk set is exactly: `withdraw`, `withdrawMany`,
`rebalance`, `borrow`, `claimFromStabilityPool`, and
`claimManyFromStabilityPool`. No other static Teller call site supplies
`True`. "Before" and "after" below refer to the material external/accounting
effects in the same entry point; a later guard revert reverts the entire EVM
transaction.

| ID | External path to housekeeping | Risk / identity / debt | Reentrancy and ordering |
| --- | --- | --- | --- |
| LG-A01 | `deposit` -> `_deposit` -> housekeeping | low; `_user`; update debt | `@nonreentrant`; after transfer, vault deposit, participation, and lootbox updates; before final asset price snapshot |
| LG-A02 | `depositMany` -> direct housekeeping after loop | low; `_user`; update debt | `@nonreentrant`; after every deposit and each deposit's asset price snapshot |
| LG-A03 | `convertToSavingsGreenAndDepositIntoStabPool` -> `_deposit` | low; `_user`; update debt | `@nonreentrant`; after GREEN transfer/conversion and vault deposit; before final price snapshot |
| LG-A04 | `depositIntoGovVault` -> `_deposit` | low; `_user`; update debt | **not** `@nonreentrant`; after transfer/vault/points effects; before final price snapshot; delegated user requires Underscore owner/lego permission |
| LG-A05 | `withdraw` | **high**; `_user`; update debt | `@nonreentrant`; after vault withdrawal, points/participation and price-related effects |
| LG-A06 | `withdrawMany` | **high**; `_user`; update debt | `@nonreentrant`; after all withdrawals |
| LG-A07 | `rebalance` | **high**; `_user`; update debt | `@nonreentrant`; after the deposit leg and withdrawal leg |
| LG-A08 | `borrow` | **high**; `_user`; do not pre-update debt | `@nonreentrant`; housekeeping is before `CreditEngine.borrowForUser` |
| LG-A09 | `repay` | low; `_user`; do not pre-update debt | `@nonreentrant`; housekeeping is before payment conversion and `CreditEngine.repayForUser` |
| LG-A10 | `redeemCollateral` | low; `_recipient`; update debt | `@nonreentrant`; after collateral redemption for `_user`; the touched identity is recipient, not redeemed user |
| LG-A11 | `redeemCollateralFromMany` | low; `_recipient`; update debt | `@nonreentrant`; after all redemptions; touched identity is recipient |
| LG-A12 | `liquidateUser` | low; keeper `msg.sender`; update debt | `@nonreentrant`; after AuctionHouse liquidation; liquidated user is not the touched identity |
| LG-A13 | `liquidateManyUsers` | low; keeper `msg.sender`; update debt | `@nonreentrant`; after all liquidations |
| LG-A14 | `buyFungibleAuction` | low; `_recipient`; update debt | `@nonreentrant`; after payment and AuctionHouse purchase |
| LG-A15 | `buyManyFungibleAuctions` | low; `_recipient`; update debt | `@nonreentrant`; after all purchases |
| LG-A16 | `claimFromStabilityPool` | **high**; `_user`; update debt | `@nonreentrant`; after Stability Pool claim |
| LG-A17 | `claimManyFromStabilityPool` | **high**; `_user`; update debt | `@nonreentrant`; after all claims |
| LG-A18 | `redeemFromStabilityPool` | low; `_recipient`; update debt | `@nonreentrant`; after redemption |
| LG-A19 | `redeemManyFromStabilityPool` | low; `_recipient`; update debt | `@nonreentrant`; after all redemptions |
| LG-A20 | `claimLoot` | low; `_user`; update debt | `@nonreentrant`; after Lootbox claim |
| LG-A21 | `claimLootForManyUsers` | low; caller `msg.sender`; update debt | `@nonreentrant`; after claims for the supplied users; per-beneficiary keys are not touched |
| LG-A22 | `adjustLock` | low; `_user`; update debt | `@nonreentrant`; after RipeGovVault lock change |
| LG-A23 | `releaseLock` | low; `_user`; update debt | `@nonreentrant`; after RipeGovVault release and fee effects |
| LG-A24 | `purchaseRipeBond` | low; `_recipient`; update debt | `@nonreentrant`; after payment transfer and BondRoom purchase |
| LG-A25 | external `performHousekeeping` | caller supplies risk, `_user`, debt flag, and optional Addys bundle | **not** `@nonreentrant`; accepts any `addys._isValidRipeAddr`; only current production source call is Deleverage collateral swap, after withdrawal/deposit effects, with `(False, _user, True, a)` |

`depositFromTrusted` deliberately calls `_deposit` with housekeeping false and
does not independently reach Ledger. The Teller deleverage wrappers delegate
to Deleverage and do not themselves run housekeeping. A repository-wide source
search found only Deleverage's collateral-swap path calling external
`Teller.performHousekeeping`.

This corrects a stale statement in the task contract: at the frozen source,
the sole production call is
`Deleverage.swapCollateral` at `contracts/core/Deleverage.vy:460`, not
`Deleverage.deleverageForWithdrawal`. The latter begins at line 480 and has no
`performHousekeeping` call. The caller change is material to authorization and
effect-order analysis, but does not change the literal
`(False, _user, True, a)` parameters.

### 4.1 Authorization, value identities, tests, and cross-cutting behavior

| IDs | Caller/value roles and current authorization | Relevant committed test authority |
| --- | --- | --- |
| LG-A01–A03 | public caller is depositor/payer; vault receives for `_user`; MissionControl deposit permissions apply, and a different user requires `canAnyoneDeposit`, a valid Ripe department, or Underscore wallet-owner authority | `tests/core/teller/test_teller_deposit.py`; Stability Pool conversion coverage in `tests/vaults/modules/test_stab_vault.py` |
| LG-A04 | caller is payer/depositor; `_user` is beneficiary; a different user must be an Underscore owner/lego-authorized relation | deposit suite and `tests/vaults/test_ripe_gov_vault.py` |
| LG-A05–A07 | caller requests withdrawal/rebalance; `_user` owns and receives withdrawn collateral; different-user withdrawal requires governed `canWithdrawForUser` or Underscore wallet-owner authority | required targeted withdraw/rebalance suites |
| LG-A08 | caller is borrow initiator/receiver path input to CreditEngine; `_user` is debtor and guard key; downstream CreditEngine enforces borrow/delegation terms | `tests/core/creditEngine/test_credit_borrow.py` |
| LG-A09 | caller is payer; `_user` is debtor; downstream CreditEngine applies repayment/refund rules | `tests/core/creditEngine/test_credit_repay.py` and refund suite |
| LG-A10–A11 | caller is payer; `_user`/redemption rows are collateral subjects; `_recipient` receives collateral and is the guard key | `tests/core/creditEngine/test_credit_redemptions.py` |
| LG-A12–A13 | public caller is keeper and guard key/reward recipient; supplied `_liqUser` values are liquidation subjects | `tests/core/auctionHouse/test_ah_liquidation.py` and related liquidation suites |
| LG-A14–A15 | caller is payer; supplied liquidation users/assets are auction subjects; `_recipient` receives purchase and is guard key; delegated deposit permission is enforced downstream | `tests/core/auctionHouse/test_ah_auctions.py` and auction-management suite |
| LG-A16–A17 | caller initiates claim; `_user` is Stability Pool subject and guard key; claim receiver/auto-deposit behavior is downstream | `tests/vaults/modules/test_stab_vault_claims.py` |
| LG-A18–A19 | caller is payer; `_recipient` receives redemption and is guard key | `tests/vaults/modules/test_stab_vault_redemptions.py` |
| LG-A20 | caller initiates claim for `_user`; `_user` is beneficiary and guard key | `tests/core/lootbox/test_loot_claim.py` and Underscore rewards suite |
| LG-A21 | caller claims for supplied beneficiaries but `msg.sender`, not each beneficiary, is the single guard key | Lootbox claim/reward suites |
| LG-A22–A23 | caller acts for self, is Switchboard, or must satisfy Underscore owner/lego authority; `_user` owns lock and is guard key | `tests/vaults/test_ripe_gov_vault.py` |
| LG-A24 | caller pays BondRoom; `_recipient` receives bond and is guard key | `tests/core/bondRoom/test_ripe_bonds.py` |
| LG-A25 | caller must satisfy broad `addys._isValidRipeAddr`; caller chooses user/risk/debt/Addys; current source caller is governance-or-valid-Ripe-authorized Deleverage collateral swap | `tests/core/deleverage/test_deleverage_swap_collateral.py`; no exhaustive broad-caller victim matrix |

For every ID, a successful lower-risk call can arm a later checked action for
the same guard key. If MissionControl identifies that guard key as an
Underscore wallet/vault, only the equality assertion is skipped. Ledger lock
enforcement still applies after the write, and a lock or any later failure
reverts the entire call. The high-risk label in the table is the current source
literal; Stage A does not re-rank actions using a new economic judgment.

### 4.2 External-housekeeping authority

`addys._isValidRipeAddr` accepts:

- every RipeHq-registered core department;
- every VaultBook-recognized address; and
- every Switchboard-recognized address.

Those callers can choose a victim `_user`, choose `_isHigherRisk`, choose debt
update behavior, and pass a nonempty Addys struct that `_getAddys` accepts
without regenerating it. Supplying `_isHigherRisk=False` does not clear or
bypass the guard: it writes/arms the user's key, so a later checked action in
the same action block rejects. It can nevertheless availability-grief a victim
by arming the key, force snapshot/debt work, or route the housekeeping bundle
through caller-supplied addresses. Ledger's own Teller-only check constrains a
call that targets the genuine Ledger, but it does not make the broad Teller
surface harmless.

The minimum-change recommendation preserves this existing surface only with an
explicit owner/security risk acceptance. Narrowing it to Deleverage, removing
caller-supplied risk, or validating the Addys bundle would touch Teller and
expand the Stage B/audit boundary. If the reviewer does not accept the current
surface, this proposed Stage B file set is rejected and must be replaced rather
than expanded silently.

## 5. Ledger state and enumerability

`RIPE_HQ_FOR_ADDYS`, `CAN_MINT_GREEN`, and `CAN_MINT_RIPE` are immutables in
code, not enumerable storage. Ledger also inherits the stored
`DeptBasics.isPaused` Boolean. The proposed single source discriminator is
likewise immutable; it does not add an accounting storage slot. Every stored
Ledger field is classified below.

All Vyper mappings return zero for an absent key. Depending on the field, zero
means never touched, not locked, no debt/points/auction/pool debt, or "not in
the one-based index"; those meanings are not interchangeable. Indexed
collections couple count, forward index, and reverse index, so duplicate,
omitted, zero-indexed, or stale replay can corrupt enumeration even when a
single copied value looks plausible.

| State | Enumeration / coupling | Migration consequence if a replacement were attempted |
| --- | --- | --- |
| `isPaused` | single scalar | readable, but copying it does not solve any accounting key discovery |
| `lastTouch[user]` | no user-key list | historical/current nonzero keys cannot be proven complete; omission weakens or changes first-action behavior |
| `isLockedAccount[wallet]` | no wallet-key list | omitted lock can release a restricted account |
| `userVaults[user][index]`, `indexOfVault[user][vaultId]`, `numUserVaults[user]` | vaults enumerable only after a user is known; no global user list; three-way index invariant | omitted user/vault loses participation and breaks index coupling |
| `userDebt[user]` | mapping has no independent global key list | omission loses debt terms, principal, liquidation state, and timestamps |
| `totalDebt`, `unrealizedYield` | scalars | copying scalars without every user row makes totals inconsistent |
| `borrowers[index]`, `indexOfBorrower[user]`, `numBorrowers` | current borrower list is enumerable and coupled | covers current indexed borrowers only; does not establish all other user-keyed state or historical rows |
| `borrowIntervals[user]` | no complete user-key list; a user can leave current borrower enumeration | omission changes interval enforcement/accounting |
| `ripeRewards`, `ripeAvailForRewards` | scalars/struct | readable, but dependent user/point rows still incomplete |
| `globalDepositPoints` | scalar struct | must agree with all asset/user point records |
| `assetDepositPoints[vaultId][asset]` | no complete vault/asset key list in Ledger | omitted key changes rewards |
| `userDepositPoints[user][vaultId][asset]` | no complete user/vault/asset key list | omitted key changes rewards |
| `userBorrowPoints[user]` | no complete user list | omitted key changes rewards |
| `globalBorrowPoints` | scalar struct | inconsistent if user rows are incomplete |
| `fungibleAuctions[user][index]`, `fungibleAuctionIndex[user][vaultId][asset]`, `numFungibleAuctions[user]` | enumerable only after liquidation user is known; coupled indexes | omission or stale index can lose/alias auction state |
| `fungLiqUsers[index]`, `indexOfFungLiqUser[user]`, `numFungLiqUsers` | current liquidation-user list is enumerable and coupled | useful for active/current rows, not proof of all historical or other state keys |
| `ripeAvailForHr` | scalar | readable |
| `contributors[index]`, `indexOfContributor[address]`, `numContributors` | current list enumerable and coupled | copy must preserve one-based/index invariants exactly |
| `epochStart`, `epochEnd`, `badDebt`, `ripePaidOutForBadDebt`, `paymentAmountAvailInEpoch`, `ripeAvailForBonds` | scalars | readable but economically coupled to debt/reward/accounting state |
| `greenPoolDebt[pool]` | no pool-key list | omitted pool debt changes solvency/accounting |

No committed event/indexer artifact proves a complete key set for the
non-enumerable mappings. Public getters prove a value only for a known key.
Current borrower, auction-user, contributor, and per-known-user vault indexes
do not discover locks, `lastTouch`, all point keys, all interval keys, all
green pools, or debt-free historical users. An event-log reconstruction would
also require a separately reviewed canonical start block, complete event
coverage for every mutation, reorg/finality policy, runtime/source identity,
and state-root reconciliation; those conditions are not established here.

The omission cost is not limited to lost balances. A partial copy can unlock an
account, forgive or distort debt, change rewards, orphan auctions, break index
invariants, or change action-guard state. This is why replacing the live Base
Ledger is categorically less safe than permanent forward-version divergence.

## 6. Threat matrix

| Scenario | Current native guard | RH using native ancestor `block.number` | RH using verified ArbSys child block | Residual boundary |
| --- | --- | --- | --- | --- |
| two checked actions for one ordinary user in one execution block | second rejects | second rejects if ancestor number is same | second rejects | assumes both paths reach housekeeping with canonical identity |
| low-risk then checked action in one execution block | checked action rejects | rejects, but may also reject in later child blocks sharing ancestor | rejects only in same child block | lower-risk arming is intentional and pending explicit approval |
| checked, low, checked | final checked action rejects | can over-throttle later child blocks | final rejects only in same child block | low middle action succeeds |
| successive child blocks with same ancestor height | not applicable | false-positive rejection | next checked action allowed | live RH proof still missing |
| multiple child blocks in one ancestor block | not applicable | all share one key, causing extended denial | each child block has a distinct identity | requires correct ArbSys source |
| two separate Base transactions mined in one native block | second checked action rejects | not applicable | not applicable | intended Base semantics retained only in live old Ledger |
| two users interleaved | per-user isolation | isolated but each can be over-throttled | isolated | external caller can target a victim key |
| nested/reentrant call | Teller `@nonreentrant` blocks most listed paths; guard adds per-user equality where reached | same plus false positives | same-child equality | several entry points and external housekeeping are not `@nonreentrant`; guard is not a universal reentrancy primitive |
| delegated call | key is supplied canonical `_user` or listed recipient/keeper identity | same with ancestor key | same with child key | identity choices differ by action and require approval |
| recipient/keeper/liquidator differences | redemptions/purchases touch recipient; liquidations touch keeper, not liquidated user | same | same | guard does not protect every economic subject |
| valid Ripe caller targets victim through external housekeeping | can arm/check victim and force later availability failure | can extend grief across many child blocks | grief limited to one child block per returned identity | broad caller and Addys-bundle surface remains |
| valid Ripe caller chooses risk false | cannot bypass; writes and arms | can over-arm across repeated ancestor height | arms only current child block | can still grief and force debt/snapshot work |
| Underscore wallet/vault | equality assertion skipped; write retained | skipped | skipped | RH launch omits Underscore, but forward shared source retains compatibility |
| flash-loan-funded compound sequence | blocks only when the sequence reaches multiple housekeeping calls for same key and the later call is checked | may over-block unrelated later transactions | same-child protection only | one checked action alone is allowed; no price/freshness theorem follows |
| price/snapshot update ordering | varies by action; full revert is atomic | same | same | guard does not prove oracle freshness; some effects occur before guard |
| lock added/removed between actions | Ledger lock is asserted after write and revert rolls back; governance lock state remains separate | same | same | lock policy is not replaced by the action guard |
| Boolean toggled | false skips equality but still writes; true resumes checking against last write | same | same | governance/timelock authority remains |
| Ledger/Teller paused | Teller pause rejects normal entry; Ledger pause rejects every housekeeping call | same | same | MissionControl pause alone does not gate its public Boolean getter; unavailable/reverting dependencies fail earlier |
| source missing/reverting/malformed | not applicable to current native code | not applicable | recommended helper reverts, no fallback | full housekeeping availability is lost until deployment abort/repair |
| source repeats a child identity | not applicable | ancestor repetition is normal and unsafe for selected property | checked action rejects, failing closed on availability | repetition across distinct child blocks must abort activation |
| source regresses | native execution number is assumed monotonic | ancestor height is nondecreasing but wrong granularity | pinned ArbSys is expected monotonic | abort preactivation/soak and investigate; do not add a Ledger nondecrease assertion |
| permanent old Base and new RH runtimes coexist | live Base keeps current behavior | not applicable | RH uses new fresh Ledger | intentional operational divergence must be recorded forever |

The security property is deliberately narrow. It does not rate-limit
lower-risk actions, guarantee one total action per user, prove price freshness,
prevent all flash loans, protect a liquidated user's key, replace Teller
nonreentrancy, or make broad external-housekeeping authority safe.

### 6.1 Actor, ordering, false-positive, and evidence detail

| Required scenario | Attacker/caller capability and ordering | Affected key, prevention/bypass, and false-positive impact | Required closure evidence |
| --- | --- | --- | --- |
| nested/reentrant higher-risk composition | malicious callback attempts to reenter the same Teller during an external effect | `@nonreentrant` prevents most listed Teller reentry before BN-002; non-annotated entry points and calls through other departments require separate analysis | nested-call tests for every callback-capable protected path and the external route |
| two separate Base transactions in one native block | ordinary/delegated caller submits two transactions for one user; builder mines both together | live Base native key makes the second checked action reject; intentional availability cost | Base-profile two-transaction test and retained live artifact proof |
| two separate RH transactions in one child block | caller/sequencer includes both for one user in one child block | verified ArbSys identity should reject second; ancestor identity would also reject but for the wrong reason | owner-approved same-child testnet construction and receipt/in-contract comparison |
| successive RH child blocks sharing ancestor height | caller submits one checked action in each child block | ancestor key false-positively rejects; ArbSys should allow the second | repeated-ancestor/successive-child test |
| many RH child blocks under one ancestor height | caller/users transact across all child blocks | ancestor key can deny every later checked action for each touched user; ArbSys isolates each child block | cadence observation plus multi-child functional test, never treated as a maximum |
| low then high | any permitted low-risk caller touches a user's key before checked action | high action rejects; deliberate arming can also availability-grief | native-zero-source and ArbSys-`0x64` low/high tests through Teller |
| high then low then high | permitted callers sequence three actions for one key | middle low succeeds; final high rejects | explicit order test under both permitted source selections |
| delegated identity substitution | authorized delegate chooses or is passed another user/recipient | current per-entry canonical identity controls key; incorrect identity can bypass intended user or grief another | every delegation branch and caller/user distinction |
| receiver/recipient/keeper/liquidator difference | payer/keeper chooses recipient or liquidation subject | current recipient/keeper key may differ from economic subject; no claim of protection for untouched subject | stable-ID assertions for every row in section 4 |
| valid Ripe caller targets victim | any core/vault/switchboard accepted by `_isValidRipeAddr` calls external housekeeping | can arm/check victim and force debt/snapshot work; no privilege escalation is needed beyond valid-Ripe status | enumerate valid caller classes and victim tests with canonical Addys |
| valid Ripe caller chooses risk false | same authority supplies false before victim's high action | cannot clear/bypass; arms key; on ancestor source can extend denial across child blocks | false-flag low/high test and explicit accepted-risk decision |
| Underscore wallet/vault composition | registered wallet/vault or its permitted lego composes Teller actions | assertion skipped while write remains; no false-positive throttle but no equality protection | wallet, vault, ordinary user, owner/lego, and caller/user tests |
| flash-loan-funded compound action | user funds borrow/withdraw/rebalance/claim composition within one execution block | only a later checked housekeeping call for same key is stopped; one checked call and unguarded external finance remain possible | property-specific exploit/negative tests; no "flash-loan proof" overclaim |
| price/snapshot ordering | caller exploits external price/vault effect before or after guard | later revert is atomic, but guard does not establish external price freshness; ancestor source adds availability false positives | per-entry trace/order assertions and oracle-state-independent child-block test |
| lock added/removed between actions | Switchboard changes lock around user calls | locked call reverts and write rolls back; unlock can later allow action under ordinary guard rules | lock true/false under both permitted source selections and Boolean states |
| Boolean policy change between actions | governance executes timelocked true/false change | false skips equality but still writes; later true can check the stored identity | Switchboard/MissionControl transition tests; no source selection through Boolean |
| failed/reverted action | caller deliberately triggers failure after Ledger write | transaction rollback removes `lastTouch` and all earlier effects; no partial arm | failure injected after Ledger, snapshot, and debt calls |
| two users in one transaction | batch/multi-user path touches distinct users or caller only | separate keys isolate only identities actually passed; `claimLootForManyUsers` touches caller, not beneficiaries | two-user interleaving and multi-user identity tests |
| zero-address user | valid Teller route supplies zero | current Ledger accepts/writes zero; shared key can create surprising cross-path coupling | explicit preservation/risk-acceptance decision and exact regression test |
| Ledger/Teller/guard/MissionControl paused or unavailable | governance pause or dependency failure occurs before/between calls | Teller pause blocks normal entry and Ledger pause blocks housekeeping; there is no separate guard pause; MissionControl pause alone does not gate its public Boolean getter, while a reverting/unavailable MissionControl or source fails the call | pause/failure matrix for every dependency and both permitted source selections |
| source revert/malformed/repeat/`+1`/nonmonotonic | bad deployment, incompatible precompile, or execution fault controls/changes returned identity | revert/malformed fails closed; repeat rejects checked action; `+1` permits; observed regression aborts preactivation/soak without adding another Ledger assertion | Vyper decode tests, exact compiler output, local doubles, live probe, soak |
| native helper on Base-like profile | ordinary EVM deployment selects zero source | must exactly equal opcode `block.number`, with no external call or chain dispatch | S1 native jumps and artifact trace |
| RH child-block source under dated probe | owner-approved tester calls probe against pinned RH testnet release | must equal receipt child block and differ appropriately from repeated ancestor value | dated tx/receipt, source/runtime/version/hash, same/successive-child cases |
| live Base plus revised RH artifact indefinitely | operators/auditors handle different bytecode on two chains | no mixed graph within a chain; cross-chain tooling can misidentify runtime if chain is omitted | chain+address+runtime inventory, monitoring/runbook ownership, permanent exception approval |

## 7. Architecture comparison

### 7.1 Candidate A — immutable generic `ActionBlockClock` provider

Shape:

- Ledger stores an immutable provider address;
- a provider interface exposes `actionBlockNumber() -> uint256`;
- a native provider returns `block.number`;
- an ArbSys provider staticcalls `0x64.arbBlockNumber()`; and
- Ledger calls the provider on every housekeeping touch.

Advantages:

- Ledger depends on one generic ABI;
- source logic is isolated for unit review;
- future source families can use new provider implementations without changing
  canonical Ledger source, provided a fresh Ledger is deployed; and
- a provider can expose focused diagnostics.

Costs and risks:

- at least one additional production contract and ABI;
- an additional deployment, artifact, constructor input, runtime hash, manifest
  assertion, and verification target;
- one extra external call on ordinary EVM paths and two on Robinhood
  (`Ledger -> provider -> ArbSys`);
- an additional address/code-substitution and gas/availability boundary;
- failure of the provider makes every housekeeping path unavailable because
  even unchecked touches must write the selected identity; and
- immutability means correcting a bad provider after state exists still
  requires a new Ledger or an independently reviewed migration.

The provider is not safer merely because it is replaceable at deployment time.
A mutable provider would allow the meaning of stored `lastTouch` values to
change after accounting state exists and is rejected. Even immutable, Candidate
A is rejected for S5: the extra deployment, ABI, manifest object, call frame,
code-substitution boundary, and failure surface are not the smallest
owner-selected design.

### 7.2 Candidate B — one immutable source discriminator

Shape:

- Ledger has one immutable `ACTION_BLOCK_SOURCE`;
- source zero returns `block.number` without an external call;
- source exactly `0x0000000000000000000000000000000000000064`
  staticcalls only `arbBlockNumber() -> uint256`;
- the constructor rejects every other address;
- the `0x64` constructor path performs the same non-mutating call and ABI
  decode used at runtime, so a missing, reverting, malformed, or incompatible
  precompile prevents deployment; and
- a public immutable getter exposes the configured source.

Advantages:

- one canonical Ledger source for ordinary EVM and Nitro child chains;
- no `chain.id` branch and no Robinhood-branded production logic;
- no provider deployment, registry entry, or provider ABI;
- no external call for source zero and only one precompile call for source
  `0x64`;
- one configuration value with only two valid values;
- fewer failure, gas, artifact, manifest, and audit surfaces; and
- the source immutable does not perturb existing accounting storage slots.

Costs and risks:

- Ledger source contains the minimal ArbSys ABI and source-discriminator
  branch;
- a future non-ArbSys external source requires a new reviewed Ledger version;
- constructor and Ledger ABI/runtime change;
- every `0x64`-source housekeeping action depends on the precompile, including
  lower-risk and Boolean-disabled calls; and
- test doubles must faithfully model precompile return/revert/malformed cases.

**Recommendation:** Candidate B with exactly one immutable source
discriminator, conditional on independent-security approval plus successful
live/testnet source evidence and all remaining Checkpoint 0 decisions. This is
the smallest boundary that satisfies the owner-selected two-source contract.

### 7.3 Candidate C — generic immutable address and selector

A raw immutable source address plus arbitrary immutable selector would avoid a
new provider while pretending to support any source ABI. It is rejected: it
expands invalid configuration combinations, complicates return-data validation,
weakens semantic review of what the selector means, and provides no current
need beyond native and the pinned ArbSys ABI.

### 7.4 Candidate D — duplicate native and Robinhood Ledger sources

Separate chain-branded Ledger files are rejected. They increase drift across
all accounting code, obscure which fixes apply to which chain, and violate the
owner's canonical-source/minimum-change direction.

### 7.5 Candidate E — unconditional direct ArbSys read

Calling `ArbSys(0x64)` unconditionally with no zero-source native selection is
the smallest Robinhood-only line count but is rejected because the shared
forward Ledger would no longer be correct on ordinary EVM chains. Adding a
`chain.id` escape would merely replace that defect with prohibited runtime
chain dispatch. The recommended single discriminator is the minimum
abstraction needed for both source families.

## 8. Recommended policy contract

Every line remains pending Checkpoint 0 approval.

### 8.1 Action identity and ordering

- An "action block" is the actual EVM execution block of the current
  deployment.
- Source zero uses the opcode result `block.number`.
- Source exactly `0x0000000000000000000000000000000000000064`
  uses only `ArbSys(0x64).arbBlockNumber()`.
- No other source value is constructible.
- `lastTouch[_user]` stores that selected action-block identity, not time,
  ancestor height, batch number, or transaction number.
- The helper runs before equality evaluation.
- If `_shouldCheck` is true, equality with the stored identity rejects.
- On every otherwise successful call, including low-risk, Underscore-exempt,
  Boolean-disabled, and repeated-low-risk calls, Ledger writes the current
  identity.
- Lock validation remains after the write in source order; a lock failure
  reverts the whole call and write.
- Teller's guard-before-snapshot/debt ordering and each entry point's
  before/after positioning remain unchanged.

### 8.2 High-risk classification and identity

The exact six high-risk actions remain:

1. `withdraw`;
2. `withdrawMany`;
3. `rebalance`;
4. `borrow`;
5. `claimFromStabilityPool`; and
6. `claimManyFromStabilityPool`.

All other current call sites remain lower risk. Canonical `_user`,
`_recipient`, keeper/caller, and multi-user choices remain exactly as section 4
records. This is preservation, not an endorsement that every current identity
is ideal. Current zero-address behavior also remains unchanged for S5; any
later rejection or identity-policy change requires a separate scope and
approval.

### 8.3 Policy/configuration compatibility

- `shouldCheckLastTouch` remains in MissionControl with the same
  SwitchboardDelta timelock route and current DefaultsBase/DefaultsLocal
  meanings.
- It does not select a clock, source, duration, or freshness window.
- No MissionControl, SwitchboardDelta, DefaultsBase, DefaultsLocal,
  Defaults interface, or config-struct change is recommended.
- Ledger exposes the selected source through one read-only immutable getter
  and adds no separate current-action-block view.
- No per-touch event is recommended: it would add persistent log/gas behavior
  to every housekeeping path without being necessary to enforce the invariant.
  Constructor/configuration provenance belongs in the artifact/manifest record.

### 8.4 Failure table

| Condition | Recommended result |
| --- | --- |
| source zero | valid; return native `block.number` without an external call |
| source exact `0x64`, constructor call succeeds with valid ABI return | valid; decode child block |
| source any other address | constructor reject |
| `0x64` missing or call reverts during construction | constructor reject |
| `0x64` returns malformed/incompatible data during construction | constructor reject |
| source/precompile later becomes unavailable or reverts | housekeeping reverts; no fallback or partial write |
| short or otherwise invalid runtime ABI return | decode reverts; no fallback |
| overlong return data | Stage B compiler/raw-call evidence must determine whether the selected integration rejects or accepts ABI-valid trailing data; exact-length enforcement is pending approval |
| source returns same value | later checked action for same user rejects; repeated lower-risk behavior remains as approved |
| source observed to disagree with receipt child block | preactivation/soak abort; no activation |
| source observed nonmonotonic across child blocks | preactivation/soak abort; no activation |

The design preserves only the current equality semantics and leaves source
monotonicity as a deployment, probe, soak, and monitoring invariant. A
per-user nondecrease assertion is explicitly outside S5: it is a new runtime
rejection condition, is not needed for the selected equality property, and
must not be added to Stage B.

The fail-closed availability consequence is severe and intentional, not merely
a diagnostic inconvenience. If the configured ArbSys call fails, every one of
the 24 internally routed Teller housekeeping paths and the external
`performHousekeeping` entry point reverts at Ledger. This includes `repay`,
`liquidateUser`, and `liquidateManyUsers`; because transaction rollback is
atomic, both liquidation transactions unwind even though their housekeeping
call occurs after AuctionHouse work. Robinhood can therefore lose debt-repayment
and liquidation/solvency-defense availability exactly when the precompile
misbehaves. Checkpoint 0 row 9 must accept that trade-off explicitly; ancestor
`block.number` fallback remains prohibited.

## 9. Underscore compatibility

The local read-only Underscore checkout was inspected at committed HEAD
`5b0a6354caf102865ab173aaa0c6bab0b492030f` on branch
`wallets-v3...origin/wallets-v3`. It had no tracked modifications and three
unrelated untracked documentation files, which were ignored. No Underscore
file, index, branch, or remote was modified.

Committed `contracts/legos/RipeLego.vy` calls Teller for:

- collateral deposit and governance-vault deposit;
- collateral withdrawal;
- borrow;
- repay;
- deleverage paths;
- rewards claim; and
- user-wallet/leverage-vault compositions through Ripe Lego.

The calls pass the wallet/vault or recipient as Teller's canonical user. The
committed user-wallet and leverage-vault tests compose repeated Ripe deposit,
withdraw, borrow, repayment, and deleverage behavior. The present exemption
therefore has real Base/shared-forward compatibility value: an
Underscore-classified wallet/vault skips the equality assertion while still
writing `lastTouch`.

The selected initial Robinhood launch omits Underscore, so a correct initial RH
MissionControl/default graph must not register an Underscore registry. That
omission does not justify deleting the exemption from the shared forward
source. The recommendation preserves it under the same native/child action
identity. Enabling Underscore on Robinhood later requires its own S4 reopening,
S5 compatibility rereview, deployment/configuration approval, and downstream
Underscore validation. Any Underscore source change belongs to a separate
brief, branch, review, and rollout.

## 10. Test authority and gaps

### 10.1 Frozen Stage A targeted results

All authoritative commands used `PYTHONPATH=.` and the local non-secret
Etherscan placeholder.

| Command | Result |
| --- | --- |
| `pytest -q tests/data/test_ledger.py` | 101 passed in 29.63 s |
| `pytest -q tests/config/test_switchboard_delta.py` | 109 passed in 28.91 s |
| `pytest -q tests/core/teller/test_teller_deposit.py` | 26 passed in 29.50 s |
| `pytest -q tests/core/teller/test_teller_withdraw.py` | 32 passed in 32.92 s |
| `pytest -q tests/core/teller/test_teller_rebalance.py` | 22 passed in 30.89 s |
| `pytest -q tests/core/creditEngine/test_credit_borrow.py` | 39 passed in 32.42 s |
| `pytest -q tests/core/creditEngine/test_credit_repay.py` | 17 passed in 29.37 s |
| `pytest -q tests/vaults/modules/test_stab_vault_claims.py` | 51 passed in 32.50 s |
| local `DefaultsBase` guard reproduction | `BASE_GUARD_REPRO_OK`; direct-Ledger sequences reproduced in 4.11 s; Underscore classification is separate source evidence plus the equivalent unchecked path |
| `pytest -q tests/clock/test_clock_profiles.py` | 57 passed in 29.40 s |
| `python scripts/check_block_clock_inventory.py --check` | frozen Stage A before the owner-authorized probe: clean with exact section 1.5 counts |
| `pytest -q tests/inventory/test_block_clock_inventory.py` | frozen Stage A: 60 passed in 26.65 s |
| `pytest --collect-only -q` | 2,722 selected / 2,864 total; 142 deselected in 1.60 s |
| `pytest -q` | 2,722 passed, 142 deselected in 299.32 s |

### 10.1.1 Recreated five-file audit point

These results bind to the exact reviewed bytes committed locally at
`2f6a49b6c82e69bda54f2fd64d2fe03132e0db21`.

| Command | Result |
| --- | --- |
| `python -m py_compile scripts/probes/action_block_identity_probe.py tests/probes/test_action_block_identity_probe.py` | exit 0 |
| `pytest -q tests/probes/test_action_block_identity_probe.py` | 30/30 passed, exit 0; includes profile `61` / offset `55` / raw return `116`, raw `61`, incompatible `117`, malformed response, and reversion cases |
| `python scripts/probes/action_block_identity_probe.py --dry-run` | local-only success; chain `46630`; exact artifact hashes reproduced; profile `61`, pinned offset `55`, and derived raw return `116` recorded; `rpc_contacted=false`, `rpc_endpoint_read=false`, `signing_secret_read=false`, `broadcast_enabled=false` |
| `pytest -q tests/probes` | 70/70 passed, exit 0; complete probe set after version-gate correction |
| `pytest -q tests/probes/test_probe_tooling.py tests/probes/test_stock_token_transfer_probe.py` | 40/40 passed, exit 0; existing probe suites remain green |
| `python scripts/check_block_clock_inventory.py --check` after adding the probe | expected fail: eight `INV-CADENCE-NEW`/`INV-PATH-NEW` findings for the authorized but deliberately uninventoryed test-only contract/runner/test; no inventory file was edited |
| `pytest -q tests/inventory/test_block_clock_inventory.py` after version-gate correction | 60 passed in 26.78 s; the committed S2 inventory rules remain internally green |
| `pytest --collect-only -q` | 2,768 selected / 2,910 total; 142 deselected in 5.07 s; 6.51 s wall |
| complete serial `pytest -q -p no:cacheprovider` | 2,768 passed, 142 deselected, 3 cache-redirection assert-rewrite warnings in 313.58 s; 373.49 s wall |

### 10.1.2 Uncommitted post-review hardening delta

| Command | Result |
| --- | --- |
| `python -m py_compile scripts/probes/action_block_identity_probe.py tests/probes/test_action_block_identity_probe.py` | exit 0 |
| `pytest -q tests/probes/test_action_block_identity_probe.py` | 35/35 passed in 26.90 s; 63.98 s wall |
| `pytest -q tests/probes` | 75/75 passed in 31.24 s; 73.04 s wall |
| `python scripts/probes/action_block_identity_probe.py --dry-run` | local-only success; no RPC/secret read; exact source and artifact hashes unchanged |
| `pytest -q tests/deployment/test_dependency_gate.py` | 16/16 passed in 1.49 s; 2.37 s wall |
| `pytest -q tests/clock/test_clock_profiles.py` | 57/57 passed in 27.18 s; 64.62 s wall |
| `python scripts/check_block_clock_inventory.py --check` | expected fail: the same seven `INV-CADENCE-NEW` findings and one `INV-PATH-NEW` finding, all caused by the authorized test-only probe package |
| `pytest -q tests/inventory/test_block_clock_inventory.py` | 60/60 passed in 26.08 s; 26.97 s wall |
| eight required targeted regression files | 397/397 passed, 3 cache-redirection assert-rewrite warnings in 52.59 s; 91.64 s wall |
| `pytest --collect-only -q` | 2,773 selected / 2,915 total; 142 deselected, 3 cache-redirection assert-rewrite warnings in 1.23 s; 2.36 s wall |
| complete serial `pytest -q -p no:cacheprovider` | 2,773 passed, 142 deselected, 3 cache-redirection assert-rewrite warnings in 297.06 s; 352.63 s wall |

The hardening delta does not change the probe source or bytecode. It remains
uncommitted for independent re-review. The exact clean-S2 disposition remains
an owner-gated prerequisite to any future merge; no inventory change or Stage C
work is authorized here.

### 10.2 What those tests do and do not prove

They prove that the exact frozen source compiles, existing native/local
behavior remains internally consistent, the six high-risk domain suites are
green, S1/S2 inventory authority is unchanged, and no existing local test
regressed before any S5 code exists.

The owner-authorized non-production probe now separately proves with controlled
local doubles that the exact `arbBlockNumber()` call and ABI decode succeed for
a compatible `0x64` runtime and that missing, reverting, malformed, or
incompatible responses fail both construction and later observation without
falling back to native `block.number`. It also proves that the probe paths are
excluded from production migration discovery and ABI export. Runner tests
additionally prove that read-only preflight requires the published Robinhood
ArbOS profile `61`, derives the raw expected `ArbSys.arbOSVersion()` return as
`61 + 55 = 116` from the pinned Nitro semantics, and accepts only observed raw
`116`. Raw `61`, another incompatible value, malformed data, and reversion stop
before nonce/address or signing checks. The runner keeps observed
`web3_clientVersion` non-authoritative, does not read the signing secret during
preflight, and journals every signed deployment/observation transaction with
local hash, nonce, and action before broadcast. An ambiguous send result,
RPC/local hash disagreement, or failure on a burst's second send leaves
sanitized evidence and stops. The probe does **not** implement or test the
production Ledger.

The combined local evidence does **not** prove the selected live Robinhood
property:

- local fixtures use `DefaultsLocal.shouldCheckLastTouch = False`;
- the direct Ledger tests pass `_shouldCheck` explicitly and do not exercise a
  Base-enabled Teller graph;
- no existing test explicitly covers low -> high or high -> low -> high through
  Teller with the Boolean enabled;
- no current test models receipt child block, ancestor `block.number`, and
  `ArbSys.arbBlockNumber()` as distinct values;
- no test executes two transactions in the same RH child block;
- no test proves the next RH child block is allowed while ancestor height
  repeats;
- no production-Ledger source-failure/malformed-return/wrong-discriminator
  test exists;
- broad external-housekeeping victim grief and arbitrary Addys bundles are not
  exhaustively tested;
- locked behavior is not combined with both permitted source selections and
  every policy state;
- current tests do not strictly assert the selected zero-address preservation;
  and
- a passing full suite cannot prove live Base or Robinhood runtime identity.

### 10.3 Required Stage B matrix

Before implementation can be accepted, the approved test slice must cover:

- native identity repeats and `+1`, `+2`, `+4`, and `+60`;
- same RH child block across calls and transactions;
- successive RH child blocks while ancestor `block.number` repeats;
- receipt child block equals in-contract ArbSys value;
- source missing, reverting, malformed, unsupported discriminator, repeated, and
  observed-regressing behavior with no fallback;
- low -> high, high -> low, high -> low -> high, and high -> high;
- every one of the six high-risk Teller actions;
- all section 4 canonical identities, delegated callers, recipient/keeper/
  liquidator differences, two-user interleaving, and zero-address preservation;
- ordinary user, Underscore wallet, Underscore vault, and caller/user
  distinction;
- Teller internal route, Deleverage external route, every approved valid-caller
  class, and invalid caller;
- locked and paused behavior under zero and `0x64` source selections with the
  Boolean at both values;
- nested call, revert rollback, and no partial `lastTouch`;
- retained live Base artifact versus fresh RH artifact; and
- constructor, immutable, manifest, gas, storage-layout, creation/runtime
  bytecode, selector/calldata/return-decode evidence.

The same-child/successive-child test must use an environment capable of
faithfully producing that block topology. A generic local counter or ancestor
height mock alone cannot close it.

## 11. Base and Robinhood rollout decision

### 11.1 Base permanent live-version exception

The committed current Base manifest has SHA-256
`06ac6dcf3d5c3d2366bd33118023fd6603fc4d759a7a5103901b29ae67007b00`
and last changed in commit `cbf7ea8264abbf81ea2becd616c8d79843a44b0f`.

| Component | Committed Base address | Manifest compiler-input integrity |
| --- | --- | --- |
| Ledger | `0x365256e322a47Aa2015F6724783F326e9B24fA47` | `1aa27005edd424133a707695d47e31866d1ab4e7016ac328c2a3f96a4b142535` |
| Teller | `0xae87deB25Bc5030991Aa5E27Cbab38f37a112C13` | `b3b25ea75591d6deaa307a728928f1a229f17d163b938112ed766bd592273968` |
| MissionControl | `0x559E53F42b68b4995732Dba4aF300796761DBC19` | `0e7ad25d2aad4d1f32885dfe3cc0eaff22b00eed9c8e6fa358ae87e9fbec261d` |
| SwitchboardDelta | `0xCdD15077231FEbe9e6393cf91d500984973FFcA0` | `ee5bb5bc2eaa9cbd1247c17248f1f2b7237faba7353d2520deddcf722dd4e40a` |

All four manifest entries name the corresponding current repository path and
compiler `v0.4.3+commit.bff19ea2`, but the manifest-embedded source is the
deployed artifact authority. The frozen forward-source integrity values are
Ledger
`78d1e5c6d0fdc5ec8f8aeada465a090f09e523ef34bd7d2aee8c21025541413f`,
Teller
`ae5ab1888fa6a7136fb113d6969acbb145b78468307f0f0c6118c3f9ff3ce12f`,
MissionControl
`9899ba3550b294c346ecdba63dc47bd07a1c6d29e31a7a34b0fb47883ddfe497`,
and SwitchboardDelta
`ee5bb5bc2eaa9cbd1247c17248f1f2b7237faba7353d2520deddcf722dd4e40a`.
The differences are why a file path alone must not be treated as proof that
live Base runs the forward source.

The manifest records address, ABI/compiler input, constructor args, source, and
compiler output but not a complete live transaction/block/deployer/runtime
attestation. The shared Track 6 record contains a dated, owner-approved
read-only Base RPC observation from 23 July 2026: Ledger runtime 12,970 bytes,
keccak
`0xdcb94574dd9e625451c96086c7a03c2516457e7ced0b9d3545bab4a005921b7d`
at observed block 49,026,989. This Stage A did not repeat that RPC and treats it
as dated committed evidence, not current live verification.

Because section 5 proves that a complete Ledger state export cannot be
established from committed enumerators, Base must retain the currently deployed
Ledger indefinitely:

- no Base Ledger contract change;
- no ABI replacement presented as live;
- no registry/governance action;
- no state export/import;
- no convergence deadline;
- no compatibility shim that changes stored-key meaning; and
- no claim that a fresh local deployment is migration evidence.

Operationally, Base and Robinhood will intentionally run different Ledger
runtime versions. Monitoring, incident response, artifact registries, and
future audits must identify chain plus runtime hash rather than assuming one
globally deployed bytecode. A later Base vulnerability remains a separate
owner/security problem; this decision does not pre-authorize migration.

### 11.2 Fresh Robinhood deployment

Robinhood must receive a fresh Ledger before any state-bearing user action:

1. Track 7's `0030_Track6S5LedgerGuard.py` remains a mandatory pre-deploy
   artifact/source/constructor assertion, not an independent upgrade
   transaction.
2. Track 7's `0200_DataAndConfigRegistries.py` owns the fresh Ledger deployment
   after RipeHq and before dependent registries/departments.
3. The manifest must bind the one source discriminator at exact value `0x64`,
   the fixed `arbBlockNumber()` ABI/selector, creation/runtime hash, compiler
   inputs, and constructor args; it must contain no separate mode value.
4. An in-contract RH testnet probe and deployment-time read-only assertion must
   agree with receipt child block; preflight must also record the explicitly
   approved Robinhood ArbOS profile `61`, derive the expected raw
   `ArbSys(0x64).arbOSVersion()` return as `61 + 55 = 116` from the pinned
   Nitro source, and require the observed raw return to equal `116`.
   Observed `web3_clientVersion` is supporting evidence, not proof of the pinned
   Nitro build.
5. The Ledger may be registered only while dependent user entry points remain
   paused/disabled; no mixed old/new active graph is permitted.
6. The single activation boundary is the first enabling/unpausing action that
   makes a user path reachable after all source, runtime, registry, Boolean,
   pause/lock, empty-state, and dependency assertions pass.
7. Deployment operators must ensure no user transaction is in flight or
   accepted before that boundary; a transaction assembled against a pre-final
   graph is invalidated rather than carried across activation.
8. Abort and redeploy before the first state-bearing action if any assertion
   differs.
9. After the first state-bearing action, "rollback" cannot mean swapping Ledger
   without a separately reviewed complete state migration; the honest response
   is pause/incident containment.
10. Monitor the configured source discriminator, Ledger runtime hash,
    precompile failures, receipt/ArbSys agreement in approved probes, and
    chain-specific artifact identity; no per-touch event is required.
11. The same canonical Ledger source is parameterized for native or ArbSys
    mechanics; no permanent Robinhood-specific source file is created.
12. No Base state is imported.

S6 owns the final Robinhood Defaults/parameter manifest. S5 supplies only the
approved Ledger source discriminator and compatibility constraints.

## 12. Proposed exact Stage B file set

This is a recommendation for Checkpoint 0, not authority.

### 12.1 Recommended owned files

| File | Exact reason |
| --- | --- |
| `contracts/data/Ledger.vy` | add one immutable source discriminator, minimal inline ArbSys interface/helper, constructor validation/call/decode, its read-only getter, and preserved equality behavior |
| `tests/conf_core.py` | pass explicit zero source for ordinary local fixtures and provide approved source doubles |
| `tests/data/test_ledger.py` | preserve/restate the current sequence, lock, pause, authorization, revert, identity, and native-mode contract |
| `tests/core/teller/test_teller_deposit.py` | prove low-risk arming through actual Teller path |
| `tests/core/teller/test_teller_withdraw.py` | prove checked withdraw and order/identity behavior |
| `tests/core/teller/test_teller_rebalance.py` | prove checked post-two-leg behavior |
| `tests/core/creditEngine/test_credit_borrow.py` | prove checked guard precedes borrow |
| `tests/core/creditEngine/test_credit_repay.py` | prove lower-risk repay arming/order |
| `tests/vaults/modules/test_stab_vault_claims.py` | prove both checked Stability Pool claim paths |
| `tests/data/test_ledger_action_block.py` | proposed owner-approved focused native/ArbSys/source-failure/security matrix |
| `scripts/abis/Ledger.json` | regenerate only the changed Ledger ABI |
| `docs/chains/rh/ledger-guard-implementation-record.md` | artifact, storage, gas, tests, rollout, audit, and approval evidence |

The minimal ArbSys interface should be defined inside Ledger so no new
production interface file or provider contract is needed. If Vyper artifact
inspection proves that an external interface file is required, Stage B must
stop and return the exact proposed path to Checkpoint 0; it may not be added
implicitly.

### 12.2 Explicitly excluded

No Stage B edit is recommended for:

- `contracts/core/Teller.vy`;
- `contracts/core/TellerUtils.vy`;
- `contracts/data/MissionControl.vy`;
- `contracts/config/SwitchboardDelta.vy`;
- `contracts/config/DefaultsBase.vy`;
- `contracts/config/DefaultsLocal.vy`;
- `interfaces/Defaults.vyi` or `interfaces/ConfigStructs.vyi`;
- any provider contract or provider ABI;
- `tests/config/test_switchboard_delta.py`;
- `tests/clock/test_clock_profiles.py`;
- S2 inventory files before separately approved Stage C;
- historical migrations or Base manifests;
- Track 7's reserved migration file;
- S4 code or records;
- dependency files;
- `rh-summary.md`, component matrix, shared planning documents, or decision
  register during Stage B;
- Underscore source/tests; or
- any live system.

All excluded tests still run for validation. If external housekeeping is
narrowed, Teller becomes necessary and the entire proposed file set must return
to the owner/security reviewer because Teller also intersects the future S4
review boundary.

## 13. Review, audit, and Track 7 handoff

Required independent slices:

1. **Source semantics review:** official RH/Nitro/ArbOS pin, exact ArbSys
   interface and Vyper staticcall decode, same-child/successive-child proof.
2. **Ledger security review:** immutables, constructor validation, preserved
   equality logic, write/revert/lock/pause behavior, storage layout, ABI,
   bytecode, gas, and fail-closed availability; confirm no nondecrease
   assertion was added.
3. **Teller policy review:** every section 4 call, risk classification,
   identity, effect ordering, Underscore exemption, and external housekeeping.
4. **State/rollout review:** Base non-enumerability and permanent exception,
   fresh RH initialization, activation/abort/rollback boundary, S6 values, and
   Track 7 reservation.
5. **Dependency/toolchain review:** H-01 closes and integrates first, followed
   by exact clean-environment artifact/test reproduction.
6. **External audit decision:** the owner and independent security reviewer
   must explicitly decide whether a dedicated external audit is required. This
   record recommends one because the change affects a protocol-wide Ledger
   gate, every Teller housekeeping path, and a chain-specific precompile
   availability boundary even though the code delta is small.

Track 7, not S5, owns migration sequencing. Its final plan must assert the
reviewed S5 artifact before `0200`, verify constructor/source values and runtime
after deployment, prove zero state before activation, and record that `0030`
does not mutate Base or independently upgrade Robinhood.

Stage C inventory reconciliation remains separate and owner-gated after
implementation and review. Later owner-approved updates would be needed for
BN-002 and component rows CM-008/CM-034 plus the decision register; Stage A
does not edit them.

The isolated probe package must not merge into `rh` while the standalone S2
checker reports its eight expected findings. That is a technical integration
gate, not merely a process preference: landing the files without a reviewed
probe-inventory disposition would break the clean-S2 invariant consumed by
other workstreams. The owner must decide the probe package's inventory or
removal disposition before any future merge, most naturally after the live
proof is complete so the evidence can integrate once. This statement does not
authorize Stage C or an inventory edit now.

## 14. Evidence limitations and unresolved decisions

### 14.1 Evidence limitations

- The owner authorized a Robinhood-testnet-only proof, but did not provide or
  approve the exact RPC endpoint, signer, signer funding, nonce, published
  Robinhood ArbOS profile / expected raw ArbSys-version return pair
  (`61`/`116`), or maximum total fee.
  The runner therefore stopped at local dry-run; no RPC or approved signing
  secret was read and no live transaction was signed or broadcast. Journal
  tests used only ephemeral in-memory keys and made no network call.
- No two-transaction same-child-block execution was reproduced.
- No in-contract ArbSys value was compared with a Robinhood receipt block.
- Official RH documentation and pinned Offchain Labs source do not prove the
  exact deployed precompile/runtime configuration.
- The task contract's named external caller was stale: current source routes
  external housekeeping from `Deleverage.swapCollateral`, not
  `deleverageForWithdrawal`; this record uses the current graph, and Stage B
  must reverify it after reconciliation.
- No production Ledger implementation exists, so its constructor validation,
  staticcall return decoding, creation/runtime bytecode, storage layout, ABI,
  and gas have not been inspected. The isolated test-only Vyper probe exercises
  the call/decode and fail-closed boundary but is not production-Ledger
  evidence.
- Existing local defaults disable the Boolean; full-suite green is not
  Base-enabled end-to-end evidence.
- Existing production tests omit several required ordering, external-caller,
  identity, malformed-source, and source-selection cases.
- Base runtime evidence is dated committed evidence from 23 July 2026, not a
  fresh live observation.
- The committed Base manifest does not contain a complete live provenance
  attestation.
- H-01 is integrated, and this Stage A package has been recreated directly on
  exact `02787d351a3064e35d627e8fbc44150770e61c73`. Its bounded dependency
  exceptions remain active; S5 does not close or alter them.
- The inherited `ripe-lite` interpreter is not the authoritative H-01
  environment: the dependency gate correctly found installed `cbor2 5.7.0`
  instead of locked `5.9.0`. The retained approved H-01 Candidate A
  environment has `cbor2 5.9.0`, passes `pip check`, and is the environment
  used for authoritative recreation validation.
- Local `rh` and the local `origin/rh` tracking ref resolved to exact
  `02787d351a3064e35d627e8fbc44150770e61c73` at bootstrap. No live remote
  refresh was performed, and the unrelated untracked Track 8 owner packet in
  the integration worktree was left untouched.
- Integrated Track 8 remains documentation-only; its future production graph
  may require a new compatibility review.
- Underscore compatibility is read-only committed-source analysis; no
  downstream test suite was run.

### 14.2 Unresolved policy/architecture items

- independent-security approval of the owner-selected one-immutable internal
  helper over the rejected generic provider;
- exact immutable/getter naming, constructor argument position, and strict ABI
  return handling;
- live RH ArbSys/receipt agreement and source version pin;
- explicit acceptance of lower-risk arming and all six high-risk actions;
- independent-security acceptance of all preserved canonical identity choices,
  especially recipient/keeper/liquidated user, multi-user claims, delegation,
  and current zero-address behavior;
- independent-security acceptance of the preserved Underscore exemption;
- explicit risk acceptance for preserved external housekeeping and its
  caller-supplied Addys/risk/debt controls; any narrowing requires a separate
  rescope;
- explicit acceptance that source failure blocks even lower-risk and
  Boolean-disabled housekeeping because writes are preserved, including repay
  and both liquidation entry points;
- immutable/getter naming and manifest/monitoring diagnostics; no per-touch
  event or current-action-block view;
- permanent Base live-version exception and operational ownership;
- independent-security confirmation that the `02787d3` recreation and
  authoritative validation satisfy row 11; S4 remains no-code;
- exact Stage B file set;
- dedicated external audit and testnet-soak requirement;
- Track 7 manifest/activation/abort/rollback signers and reviewers; and
- later S2/component/decision-register reconciliation ownership.

## 15. Explicitly rejected alternatives

| Alternative | Disposition |
| --- | --- |
| Keep native `block.number` on Robinhood | rejected: it is ancestor height and can repeat across many child blocks |
| Disable `shouldCheckLastTouch` on Robinhood | rejected: removes the selected protection |
| Use timestamp, elapsed seconds, cooldown, ancestor block, batch number, or transaction count | rejected: different policy/property |
| Runtime `chain.id` branch | rejected: unnecessary chain coupling and explicitly prohibited |
| `tx.origin` identity or dispatch | rejected: unsafe caller semantics and unrelated to execution-block identity |
| Unconditional direct ArbSys read with no zero-source native selection | rejected: breaks ordinary-EVM portability |
| Separate mode and source immutables | rejected: redundant invalid configuration surface; one address discriminator fully expresses the two permitted selections |
| Per-user nondecrease assertion | rejected for S5: changes preserved equality semantics and is unnecessary for the selected property |
| Fallback from ArbSys failure to native `block.number` | rejected: silently changes the security identity exactly when source integrity fails |
| Mutable provider/source | rejected: can change the meaning of stored `lastTouch` after Ledger has state |
| Arbitrary immutable selector/source | rejected: excess invalid configuration and weak semantics |
| Chain-branded duplicate Ledger source | rejected: accounting drift and larger audit surface |
| Migrate/replace deployed Base Ledger | rejected: committed state is not completely enumerable and omission can be economically/security critical |
| Future Base convergence deadline | rejected: creates pressure toward an unsafe state migration without evidence |
| Import Base Ledger state into RH | rejected: RH is a fresh deployment |
| Change high-risk classification/order as part of clock portability | rejected unless separately returned to Checkpoint 0 |
| Let an arbitrary caller self-select whether protection applies | rejected as a selected design; current external Teller authority requires explicit separate acceptance or narrowing |
| Reuse action identity for durations, freshness, capacity, auctions, rewards, or timelocks | rejected: outside the selected property |
| Treat passing local/full tests as RH source proof | rejected |
| Treat floating H-01/Track 8 branches as integrated authority | rejected |

## 16. Checkpoint 0 approval table

The integrated owner packet records owner approval or in-principle approval as
shown below. **No row is closed.** Recommendations and owner approval do not
replace the missing independent-security, operations, deployment, live-proof,
final-evidence, or external-review gates. Final closure must name the decision,
date, owner, independent security reviewer, evidence commit, and conditions.

Rows 8, 10, and 13 intentionally add operations or deployment-owner sign-off
for configuration, permanent live-version, activation, and evidence facts they
must own. These are additive operational approvals; they neither replace nor
weaken the task contract's mandatory owner and independent-security approval.

| # | Mandatory decision | Stage A recommendation | Required approvers / evidence | Status |
| --- | --- | --- | --- | --- |
| 0 | Owner-direction validation | confirm same actual execution block, native ordinary EVM, ArbSys child block on RH, and listed non-goals | owner plus independent security reviewer against this exact recreation | **OWNER APPROVED; SECURITY PENDING** |
| 1 | Abstraction shape | one immutable internal source discriminator: zero native, exact `0x64` ArbSys, every other address rejected; no separate mode/provider | independent security reviewer confirms owner-selected correction against sections 7.1/7.2 | **OWNER APPROVED; SECURITY PENDING** |
| 2 | Clock-source contract | zero returns native `block.number`; exact `0x64` calls only pinned `arbBlockNumber()`; ArbSys construction calls/decodes successfully; read-only source getter; no fallback | owner + security; official source plus owner-approved endpoint/signer/funding/fee-cap and published-profile `61` / expected-raw-return `116` live RH proof | **OWNER APPROVED IN PRINCIPLE; LIVE PROOF AND SECURITY PENDING** |
| 3 | Current arming semantics | preserve any-touch write and later checked-higher-risk rejection | owner + security; explicit low/high matrix | **OWNER APPROVED; SECURITY PENDING** |
| 4 | High-risk set | preserve exact six actions | owner + security; complete call graph rereview | **OWNER APPROVED; SECURITY PENDING** |
| 5 | Underscore policy | preserve exemption in shared source; omit registry from initial RH | owner + security; downstream compatibility review and explicit preserved-behavior acceptance | **OWNER APPROVED; SECURITY PENDING** |
| 6 | Identity policy | preserve all current per-entry identities and current zero-address behavior | owner + security; delegated/recipient/keeper/liquidator/zero-address matrix and mandatory Stage B reachability evidence | **OWNER APPROVED; SECURITY AND STAGE B REACHABILITY EVIDENCE PENDING** |
| 7 | External housekeeping | minimum-change preserve only with explicit risk acceptance; otherwise return with expanded Teller scope | owner + security; valid-caller grief/Addys/Deleverage tests | **OWNER DIRECTLY ACCEPTED RISK; SECURITY PENDING** |
| 8 | Configuration/compatibility | keep Boolean/governance/defaults unchanged; expose only the one immutable source getter; no per-touch event | owner + security + operations | **OWNER APPROVED; SECURITY AND OPERATIONS PENDING** |
| 9 | Lock/pause/failure | preserve lock/pause; source failure blocks all housekeeping, including repay and both liquidation entries; no per-user nondecrease assertion | owner + security; explicit solvency-defense availability acceptance | **OWNER DIRECTLY ACCEPTED RISK; SECURITY PENDING** |
| 10 | Base live-version exception | permanent no-migration/no-convergence exception | owner + independent security + operations; exact address/runtime/artifact record | **OWNER APPROVED; SECURITY AND OPERATIONS PENDING** |
| 11 | H-01/S4 sequence | H-01 integrated; S4 no-code; fresh S5 recreation and authoritative validation on exact `02787d3` | H-01 security reviewer + independent S5 reviewer against this exact five-file recreation | **INTEGRATION AND RECREATION SATISFIED; INDEPENDENT S5 REVIEW PENDING** |
| 12 | Stage B ownership | approve exactly section 12 or return it; no implicit file expansion | owner + independent security reviewer | **OWNER APPROVED; SECURITY PENDING** |
| 13 | Evidence bar | local isolated probe/doubles are necessary but insufficient; require pre-broadcast signed-transaction journal/hash verification, approved published ArbOS profile / observed derived raw ArbSys-version match, live RH receipt agreement and bounded topology proof, faithful same-child production tests, artifacts/storage/gas, targeted/S1/S2/full suite, testnet soak, and explicit external-audit decision | owner + independent security reviewer + deployment owner; exact endpoint, signer, funding, nonce/address, profile `61`, derived raw return `116`, and total-fee-cap approval still required | **OWNER APPROVED IN PRINCIPLE; LIVE/FINAL EVIDENCE, SECURITY, DEPLOYMENT, AND EXTERNAL-REVIEW DECISION PENDING** |

Until every row closes, the mandatory result is:

- no Stage B or Stage C;
- no production Ledger implementation or production contract, interface,
  fixture, ABI, inventory, dependency, migration, default, shared-plan, or
  external-repository change beyond the isolated test-only probe package
  already authorized here;
- no merge or push;
- no Base or Robinhood deployment;
- no governance/registry action;
- no live RPC/probe/transaction until the exact testnet endpoint, signer,
  funding, nonce/predicted address, bytecode hashes, published ArbOS profile
  `61`, pinned-source-derived raw `arbOSVersion()` return `116`, observation
  bound, and maximum total fee are approved and preflight cleanly;
- no ancestor-number fallback;
- no disabled Robinhood guard; and
- no claim that the recommended architecture is approved.
