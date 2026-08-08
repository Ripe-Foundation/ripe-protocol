# Robinhood PSM lite-permission split decision and evidence

- **Decision date:** 31 July 2026
- **Current repository authority:** `rh` commit
  `967a618922be0acd9fa434c7d0c937d9620e1541`, tree
  `528f35efa6a74787773afa671874c531b2ab067d`
- **Prototype evidence authority:** commit
  `3d60a8d081ee2f0ae866143d8d810cbfa1e50ca7`, tree
  `b8616795314664e5ba3b405f8086506d6a3b2619`
- **Lifecycle effect:** decision/evidence integration only

## Decision

Do not adopt the pause-only production-contract prototype. Retain **zero
non-governance lite or pause signers**. `PSM-OD-12` remains unresolved, and
governance/operations remain the preferred mitigation until measured response
time proves them insufficient. The prototype is retained only as recoverable
future research.

The triggering premise remains unproven. The approved no-lite posture carries
governance response-latency risk, but no bound emergency-pause response
objective, measured governance/Safe performance, signer thresholds, or
incident ownership has established that the operational path misses an
accepted objective. [PSM-OD-12](../qualification/psm-liquidity-activation.md#12-owner-decisions)
still requires governance, treasury, recovery, liquidity, and monitoring
identities, thresholds, response times, and incident owners. Without that
evidence, the prototype's new shared-code, ABI, storage, deployment, audit,
signer-compromise, and denial-of-service risks cannot be shown to produce a
lower total risk than unchanged source plus monitoring, rehearsed Safe
transactions, explicit incident ownership, and bound response times.

Granting the existing general-lite role is not an alternative: it couples
Charlie pause authority to Echo reserve movement and the broader shared lite
surface. The correct current answer is no non-governance signer, not a broad
signer.

## Current operational posture

At the current authority:

- `contracts/config/DefaultsRobinhood.vy::liteSigners()` returns `[]`;
- `config/BluePrint.py` binds PSM constructor mint and redeem to `False`, keeps
  pre-activation auto-deposit disabled and yield at `(0, zero)`, and leaves the
  later PSM parameter and execution bindings blocked;
- `config/robinhood-parameters.json` records both the source default
  (`P-H04-305`) and deployment input (`P-H04-412`) as exact empty lite-signer
  collections;
- `docs/chains/rh/status.yaml` excludes PSM parameters and activation from the
  current Profile 1 reconciliation and preserves the PSM disabled; and
- the approved future PSM posture remains allowlisted and canary-gated, with
  redemption proved before mint and every activation step under separate
  authority, as specified in the
  [PSM activation proposal](../qualification/psm-liquidity-activation.md).

Accordingly, the PSM remains disabled, allowlisted for any future canary,
canary-gated, and outside the current launch configuration. No deployed-state
claim is made by this repository-only record.

## Exact prototype scope

The archived unstaged prototype changed exactly seven paths: 870 insertions
and 2 deletions. None is copied into this candidate.

1. `contracts/data/MissionControl.vy`
2. `contracts/config/SwitchboardAlpha.vy`
3. `contracts/config/SwitchboardCharlie.vy`
4. `tests/data/test_mission_control.py`
5. `tests/config/test_switchboard_alpha.py`
6. `tests/config/test_switchboard_charlie.py`
7. `tests/config/test_switchboard_echo.py`

`contracts/config/SwitchboardEcho.vy` was a byte-identical compatibility
control, not a modified prototype path. The prototype added an initially empty,
enumerable pause-only role, timelocked additions and immediate removals through
Alpha, and Charlie admission only for `pause(target, true)`. Governance and
general-lite behavior were preserved; the new role could not unpause or reach
reserve, yield, oracle, upkeep, recovery, sweep, configuration, or other lite
actions. A compromised pause signer could still deny service across any
compatible target accepted by Charlie.

## Compiler, ABI, and storage evidence

The archived compiler is Vyper `0.4.3+commit.bff19ea2`.

| Contract | Creation bytes before -> after | Runtime bytes before -> after | Runtime delta | EIP-170 headroom after | Repository-gate headroom after |
| --- | ---: | ---: | ---: | ---: | ---: |
| MissionControl | 21,199 -> 21,699 | 15,616 -> 16,109 | +493 | 8,467 | 8,043 |
| SwitchboardAlpha | 24,479 -> 25,145 | 23,144 -> 23,804 | +660 | 772 | 348 |
| SwitchboardCharlie | 21,908 -> 22,189 | 20,649 -> 20,930 | +281 | 3,646 | 3,222 |
| SwitchboardEcho | 21,047 -> 21,047 | 19,788 -> 19,788 | 0 | 4,788 | 4,364 |

The enumerable design added five MissionControl functions and three Alpha
functions plus two Alpha events. Charlie and Echo external ABIs were unchanged;
no selector or event was removed. Storage additions were append-only:
MissionControl slots 167 (`pauseSigners`), 168 (`indexOfPauseSigner`), and 169
(`numPauseSigners`), plus Alpha slot 23 (`pendingCanPerformPauseAction`). The
Alpha action-type flag was appended. No existing storage entry moved or
disappeared, and constructor, code/immutable, and transient-storage layouts
remained structurally equal.

A measured non-enumerable MissionControl alternative cost +136 runtime bytes,
357 fewer than the enumerable design, and used three fewer public selectors.
It did not satisfy the prototype requirement for on-chain enumeration and
swap-and-pop removal. It also would not reduce Alpha's +660-byte cost or its
348-byte repository-gate headroom. These costs reinforce non-adoption; layout
compatibility evidence is not deployment or upgrade authorization.

## Validation and mutation evidence

Historical validation against the prototype authority recorded:

- 12 focused permission tests passed, with 365 deselected;
- all 377 changed-module tests passed;
- 545 unchanged-consumer/downstream tests passed, with 44 fork-only deselected;
- the untouched baseline control passed 239 tests;
- two fresh-process collections matched at 4,071 local node IDs, with 142
  fork-only deselected, SHA-256
  `3a3f4e092b93c8273b44a9aff361e1ea1e415beec4e805e3597af6eae7f28d11`;
- the network-free serial run recorded 4,064 passed, 7 failed, and 142
  fork-only deselected; the seven failures were expected forbidden rebindings:
  one old coupled-permission assertion and six moved block-clock inventory
  anchors; and
- the direct artifact checker returned `CONTRACT_ARTIFACTS_OK`.

All six disposable mutations were killed: restoring the old coupled predicate,
reversing pause polarity, making pause inherit general lite, removing
governance access, letting unchanged consumers inherit pause authority, and
reversing legacy/new selector order. This supports the prototype's technical
conclusion but does not establish its operational need or authorize adoption.

## Durable archive and hashes

Recoverable evidence is at:

`/Users/wigglez/dev/ripe-protocol-review-archives/candidates/psm-lite-permission-split`

SHA-256 was recomputed over exact bytes. The manifest's 70 archived-evidence
rows all match, and both patches reproduce from the retained prototype
worktree.

| Archive item | SHA-256 |
| --- | --- |
| `candidate.patch` | `ba930d4b0641ecf15990e5dcefab34cfe53e3d9badbce4eea837c985417934ad` |
| `candidate-full-index.patch` | `c33787381d37b901b3a40da3e845cb8825d05412ac1827cd5a92e3335d6dd49f` |
| `manifest.tsv` | `c9a9383bd0823e0f6e9a38915a36ebb0fcb75bb7c7385f868e81871bbd40db0e` |
| `validation-summary.md` | `c982002266aab6bcc65ec32e66ea27846083479d4d6cdf99250c7c75658c816c` |
| `compiler-artifacts/compiler-version.txt` | `851e0f3bc8d03ca619c953e91b6647fbfee74800458e39668e1cc73aaf6813d7` |
| `compiler-artifacts/abi-layout-delta.json` | `9da92d019610e0bf4d98d88b7eb6fa49bf3953ea74c251665289691dfb89f1a1` |
| `compiler-artifacts/sizes.tsv` | `72b94e0119bf2b5cf9b8b72d7b7e4c8116e4e8756689564cf81e1acc1aa44f0d` |
| `compiler-artifacts/validation-results.tsv` | `3c65e1b0af00e251b10fda8f02578c72c62a7d78e263b9d5835f16dadc2b6876` |
| `compiler-artifacts/mutation-kills.tsv` | `608bf2ea4b34c1d0daeac1d0279fbb8adcc0b1b3a7f1816edcfadfa2942c4984` |

The manifest is the complete per-file hash inventory; this table identifies
the decision-bearing patch, summary, and primary compiler/validation evidence.

## Reopening conditions and authority boundary

Reopen the production change only if all of the following occur:

1. `PSM-OD-12` binds the exact governance and incident owners, signer
   identities and thresholds, accepted emergency-pause objective, measurement
   method, and rehearsal/incident response evidence.
2. Measured governance/operations performance fails that accepted objective,
   and improved monitoring, prepared Safe transactions, staffing, rehearsal,
   or other configuration/operational mitigations are shown insufficient.
3. A fresh owner decision concludes that a non-governance pause capability's
   total-risk reduction exceeds its shared-code, ABI/storage, code-size,
   deployment, audit, compromise, and denial-of-service risks.
4. The exact current `rh` authority is rebound and the smallest candidate is
   independently re-reviewed, recompiled, remeasured, mutation-tested, and
   reconciled with current inventories and tests.
5. Separate authorities approve source adoption and, later, every required ABI,
   artifact, configuration, deployment, migration, role, monitoring, and
   activation change. Passing source review alone is not later-phase authority.

This record authorizes **no source, configuration, deployment, role, migration,
or activation change**. It also authorizes no staging, commit, push,
integration, publication, funding, RPC, signer/account use, or external-state
action. The seven production/test modifications remain outside this candidate.
