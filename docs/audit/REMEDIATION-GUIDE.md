# Ripe Protocol audit remediation index

## Document status

- **Purpose:** preserve a durable, source-bound index from the Auditor B findings to the remediation evidence integrated on `rh-audit-remediation`.
- **Audited candidate:** commit `6ce9c6a8813e9ba9bcf5f9a810af1e8bc86b05e8`, tree `6a0aa2a24b4d89e0d1106045423c766a58936410`.
- **Contract reconciliation snapshot:** remediation branch commit `a2d6e43f67b7c66bc5b232e3b4a06171a094d980`.
- **Artifact alignment:** commit `6646dec` refreshes the governed identities required by the formatting-only SwitchboardBravo and Lootbox commits.
- **Classification:** remediation index, not a final audit report, readiness decision, deployment plan, or release authorization.

> **Current process note:** the artifact-identity and headroom-waiver
> dispositions below are historical. The headroom floor and its exact-identity
> pins were retired; the only enforced size rule is the EIP-170 ceiling, and
> what a PR must pass is defined by root `pytest.ini` and
> `.github/workflows/python-tests.yml`. Nothing below creates a per-PR gate.

The original Auditor B guide mixed confirmed findings, operationally sensitive
proof detail, uncompiled fix sketches, historical bytecode measurements, and
references to three companion reports that are not present in this repository.
That full narrative remains frozen in owner-controlled private audit evidence.
This repository version keeps the durable finding map and points to current
source, tests, artifact identities, and owner decisions instead.

## How to use this index

`Integrated` means the cited remediation is present in this branch history. It
does **not** mean the change was independently retested, deployed, activated, or
released. The audit completion rules in
[`AUDIT_PROCESS_PLAN.md`](AUDIT_PROCESS_PLAN.md) remain controlling:

- later contract changes reopen only affected conclusions;
- remediations require regression evidence and independent retest;
- unresolved exposure and unchecked surfaces remain explicit;
- a green test suite is not a security certification.

Sizes and hashes quoted below are historical measurements from the audit
snapshot. Do not carry one into a new decision; measure the current tree
instead.

## Confirmed finding disposition map

| Finding | Severity at audit snapshot | Surface | Remediation-branch evidence | Repository disposition |
| --- | --- | --- | --- | --- |
| `B-AUD-001` | Medium | BasicVault custody shortfall | PR #97, merge `fae4a70` | Integrated; subsequently refined by the B-AUD-008 reward treatment and RH-D028/RH-D029 evidence. |
| `B-AUD-002` | Low | Asset-admission validation | Commit `5f9d072` | Integrated execution-time asset-addition revalidation; admission policy remains an operational control. |
| `B-AUD-003` | Low | Debt-term governance rails | PR #110, merge `ff20669` | Integrated proposal- and execution-time directional rails. |
| `B-AUD-004` | Medium | Stability Pool dependency isolation | PR #130, merge `250f4eb` | Integrated fail-soft liquidation and readiness handling; exact artifact and parity evidence remain required. |
| `B-AUD-005` | Low | RIPE price-source posture | PR #113, merge `b6d8df3` | Integrated monitoring-only behavior. |
| `B-AUD-006` | Low | Ledger action-block deployment validation | PR #111, merge `d30c983` | Integrated shared deployment validation; this does not replace chain-specific preflight evidence. |
| `B-AUD-007` | High | SavingsGreen zero-supply initialization | No contract remediation required by the audit disposition | Operational closure is not proven by this branch. Live-state readback and the authorized seed/burn migration remain separate evidence. |
| `B-AUD-008` | Medium | BasicVault reward accounting during custody shortfall | PR #112, merge `f937cba` | Integrated; owner decisions and the exact combined CreditEngine identity are recorded in RH-D028 and RH-D029. |
| `B-AUD-009` | Low on RH; higher where configured live | Blue-chip clean-zero price handling | PR #127, merge `b5d4879` | Integrated with the B-AUD-021 price-integrity remediation. |
| `B-AUD-010` | Medium | Stability Pool keeper-fee accounting | PR #106, merge `b7c2e46` | Integrated accounting correction. |
| `B-AUD-011` | High | PriceDesk source-failure isolation | PR #96, merge `2d52796` | Integrated per-source failure isolation. |
| `B-AUD-012` | Low | Empty Teller batches | PR #105, merge `ce54130` | Integrated empty-batch rejection. |
| `B-AUD-013` | Low | SwitchboardAlpha target MissionControl validation | PR #104, merge `20d08ce`; refinement `6636806` | Integrated target-aware proposal/execution validation; the refinement removes the single-consumer MissionControl flags getter and restores 108 bytes of deployed headroom. |
| `B-AUD-014` | High if enabled | Partner-liquidity reserve accounting | PR #100, merge `086cc06` | Integrated reserve-isolation correction; feature activation remains separate authority. |
| `B-AUD-015` | Low-Medium | VaultBook confirmation-time custody checks | PR #98, merge `f44cdbe` | Integrated confirmation-time recheck. |
| `B-AUD-016` | Medium latent | Stability Pool RIPE-mint authorization | PR #108, merge `1ad443c` | Integrated caller and dependency binding. |
| `B-AUD-017` | Medium | SavingsGreen exit controls | PR #99, merge `2c4fc9a` | Integrated blacklist and pause enforcement on exits. |
| `B-AUD-018` | Medium latent | HumanResources Lootbox checkpoints | PR #101, merge `919cbd6` | Integrated source-position checkpointing. |
| `B-AUD-019` | Low | Contributor ownership handoff | PR #102, merge `0339751` | Integrated pending-state guard. |
| `B-AUD-020` | Low | Borrower reward precision | PR #107, merge `b877fdc` | Integrated precision correction. |
| `B-AUD-021` | Medium where configured live | Delayed price-configuration snapshots | PR #127, merge `b5d4879` | Integrated BlueChip and Undy price-integrity correction. |

## Additional remediation and hardening evidence

The branch also contains related findings, observations, and integration
follow-ups that were not separate entries in the 21-finding Auditor B headline:

| Change | Evidence |
| --- | --- |
| Reject zero-share vault deposits | PR #103, merge `f9152f2` |
| Resolve TellerUtils default MissionControl correctly | PR #114, merge `9c63976` |
| Return third-party repayment excess to the payer | PR #115, merge `4821728`; included in RH-D029 |
| Restrict Boardroom callbacks to registered RipeGov vaults | PR #116, merge `aa899f1` |
| Reject a 100% auction maximum discount | PR #117, merge `64a6207` |
| Clean up expired fungible auctions | PR #118, merge `292b636` |
| Guard zero GREEN ratios in Endaoment | PR #119, merge `000a13a` |
| Reject zero bond epoch lengths | PR #120, merge `353a56a` |
| Enforce exact SharesVault withdrawal delivery | PR #121, merge `3368e2d` |
| Conserve fractional bond payments | PR #122, merge `5423800` |
| Harden asset deregistration and allocation retirement | PR #123, merge `f018642` |
| Correct HumanResources cancellation confirmation events | PR #124, merge `a4ec5a3` |
| Correct Contributor terminal vesting views | PR #125, merge `c7c583b` |
| Enforce the global debt-limit invariant | PR #128, merge `3c8b7fb` |
| Harden residual arithmetic guards | PR #129, merge `35aa010` |
| Isolate CreditRedeem price failures per entry | Commit `778cf2a` / PR #131 |
| Record the Deleverage withdrawal-binding assessment | PR #132, merge `c927c0f` |
| Suppress third-party Teller last-touch writes | PR #133, merge `031a8b8`; exact RH-D031 identity |

## Evidence rules

### Regression tests

Repository tests must assert the intended post-remediation behavior. Tests that
merely demonstrate that a vulnerability exists belong in isolated assessment
evidence, not the active regression suite. When a finding is remediated, its
regression should cover the negative boundary, exact revert reason where
applicable, state rollback, and the positive path that must remain available.

### Runtime size

Use measured deployed runtime, including immutable code data. Never carry a
historical size from this index into a new decision. The enforced rule is
EIP-170: the deployed runtime must fit in 24,576 bytes. The former 200-byte
headroom floor and its per-contract exact-identity waivers were retired; sizes
recorded in the dispositions below are historical, not gates.

### Operational findings

An on-chain operational action is not closed by a contract commit. In
particular, B-AUD-007 requires live-state and migration evidence outside this
branch. Configuration, deployment, activation, and release each require their
own explicit authority.

### Delta review

This index binds the audit snapshot to integrated remediation history; it does
not silently carry the original audit conclusions across later source changes.
For every later contract delta, identify affected contracts, callers, storage or
interface changes, value and authority flows, relevant findings, and composed
transaction permutations. Reopen only those conclusions, then record the newest
commit against which they are valid.

## Frozen private source artifacts

The owner-controlled private evidence archive preserves the exact pre-cleanup
inputs below. Hashes are recorded here so a later review can prove which local
artifacts this sanitized index replaced without publishing their sensitive
contents.

| Artifact | SHA-256 | Repository treatment |
| --- | --- | --- |
| Full Auditor B remediation guide | `b623b4740479ca7897ff543e0fbc96be8394153489de4c5529060028b3e874fc` | Retained privately; replaced here by this current index. |
| B-AUD-001 quarantine spike report | `dc72c9bbb4af30cefa9a0f406864280298bb967974c727d13cf024ca5ab5552e` | Retained privately as historical measurement/design evidence. |
| B-AUD-001 prototype patch | `6eb6951049579beb96e7eadbcd3875d9a96d6b50fb4b8afc9cd7d8f851becb39` | Retained privately for provenance; excluded because it was explicitly not the final implementation. |
| Assessment-only token proof tests | `211cbacae5805c6a4c0c77079fa147738fd0f5837bbc5af09b14b08f63a226cb` | Retained privately; excluded because they assert vulnerable behavior rather than regressions. |

No raw exploit playbook, uncompiled remediation sketch, or stale bytecode table
is published by this document. No deployment, configuration, activation,
release, or disclosure authority is granted by this index.
