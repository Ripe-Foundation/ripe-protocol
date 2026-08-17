# Lootbox: portable per-deployment Underscore send floor

> **11 August 2026 CCIP currentness note:** “owner-parked” CCIP statements below
> are historical scope labels for this Lootbox review. GREEN/RIPE CCIP topology
> is now confirmed live; see
> [`../ccip-live-state.md`](../ccip-live-state.md). No further transaction or
> release is implied.

> **Path note (8 August 2026):** some paths cited below no longer exist in the
> active tree — the block-clock inventory, the `contracts/testing/` probes, and
> the extracted deploy manifests and review records were removed. The citations
> were accurate when written and are left intact. See
> [`REMOVED.md`](../../../simplification/REMOVED.md) for the full index; everything is
> recoverable from git history. No production contract was modified.

> **Draft and authority banner.** This explanatory owner-review record was
> prepared against the immutable snapshot below. It explains integrated source;
> it does not authorize a migration, deployment, registry or capability change,
> reward enablement, signer, address, configuration, or release.
>
> **Authority rule.** Contract source and Git objects establish integrated facts.
> Dated implementation records establish historical evidence. Results explicitly
> marked “independently reproduced” were rerun at the reviewed snapshot. A modeled
> cadence is never represented as a chain guarantee.

## Current `rh` rebind

The current authority for this page is `rh` commit
`0642f086d19e3cc62faaf67da096b6511e405320`, tree
`d869d4149380b368f9678ed03efc0b59a6c804e2`. The 28 July snapshot and
validation results remain dated historical evidence below.

| Current identity | Value |
| --- | --- |
| Lootbox source Git blob / SHA-256 | `12d7b6afcc660bc502ad749b7d624fe8f38ab0cb` / `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` |
| Creation artifact | 21,911 bytes; SHA-256 `0222bd8f06f226cff079c5798df5fe7fd5d97d722bc2132c454865c7c8853e09` |
| Runtime template | 21,569 bytes; SHA-256 `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097`; 3,007 bytes EIP-170 headroom |
| [`test_underscore_rewards.py`](../../../../tests/core/lootbox/test_underscore_rewards.py) | Git blob `b2b23f3b7683534c7a492d1461bc8991d0d65050`; SHA-256 `e670b36ae68f2ceeee1b3c0c6a0e663213172b1aa27b7203e02ab6a400e0b7d3` |
| `Deployment-profile test` (retired) | Git blob `d082c315a12f4fdb6136b34925e335250fec9a91`; SHA-256 `e929e6c7f91e6d73ba0b2c96bd7cdb4d69d28db2ad0def700863190d86245a6c` |
| Contract-artifact test (retired) | Git blob `30e56a30e803e6030abb321b7dd593f08ac83f04`; SHA-256 `e821112fe1c2ac6e1091605f0b20f6c498d0e8d41914d07e196d3fc1be6b6cf8` |

Later integrated tests now pin exact five-argument manifest order, both local
deployment postures and readbacks, historical Base arity incompatibility,
initially-disabled/later-enabled first-send behavior, and the accepted
max-minus-one checked-addition overflow boundary. Current `rh` also integrates
a deterministic Lootbox deployment/registration migration source and the
transaction executor, but the plan remains blocked and non-executable. These
facts do not establish migration execution, deployment, registration, reward
activation, or release. No behavioral suite was rerun for this
documentation-only refresh.

The owner-approved launch product values and reward packet are now integrated:
DP15 and P-H04-399 are approved, Stock rewards remain disabled, and
`B-REWARD-PROMOTION` remains open for identities, initial checkpoints,
monitoring, rehearsal, and release prerequisites. Product-value approval is not
an onchain configuration or activation record.

## Reviewed implementation snapshot

| Identity | Reviewed value |
| --- | --- |
| Branch | `rh` |
| Dated reviewed `HEAD`, local `rh`, cached `origin/rh` | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Dated credential-disabled live `origin/rh` | `cca60bb85c772c977bb9fb62c1c6c5252c3a1438` |
| Dated reviewed `HEAD` tree | `161fb828f3bbf4cb12596a5dfaf6c9bf1e153381` |
| Production implementation | `f40dc25ff0352b6ce79944fb28c37499da7bf0f0` |
| Implementation parent | `f0bfd0fd5ac2be1d27321463b77248c7cd91d829` |
| Current `Lootbox.vy` SHA-256 / Git blob | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` / `12d7b6afcc660bc502ad749b7d624fe8f38ab0cb` |
| Starting draft provenance | Initially untracked; treated as input rather than authority |

**Integrated fact.** The current source is byte-identical to the version in the
implementation commit. Later commits added test/inventory evidence but did not
change [`Lootbox.vy`](../../../../contracts/core/Lootbox.vy).

**Snapshot caveat.** “Current” below means this exact Git snapshot and the local
validation run described here. Historical live-chain reads are dated and are not
silently promoted to present-day chain facts.

## Direct answers for the owner

1. **What changed?** A Base-specific constant became one nonzero, non-maximum
   constructor-selected immutable floor. The constructor gained one argument, the
   setter now checks the immutable, and a getter exposes it.
2. **What did not change?** The strict distribution expression, persistent storage
   slots, all nine events, every pre-existing method selector, reward calculations,
   points, claims, and authorization checks.
3. **Why?** The intended nominal-day floor is `43_200` EVM numbers under the
   approved Base planning quantum and `7_200` under the approved Robinhood
   planning quantum. One source constant cannot express both without materially
   changing one chain’s modeled wall-time intent.
4. **Why an immutable?** It keeps one source, removes runtime chain branching,
   preserves an unweakenable deployment floor, and adds no persistent storage.
5. **What happens to Base?** Nothing happened to the deployed Base Lootbox. A
   future deployment can preserve prior cadence with floor `43_200`, but needs a
   new explicit five-argument deployment path; the historical migrations were
   deliberately not rewritten.
6. **What happens to Robinhood?** The floor remains `7_200` and the initial
   mutable Underscore interval remains `0`. The repository now contains the
   deterministic deployment source and owner-approved general reward product
   values, while the executable plan, exact runtime bindings, authority
   sequence, initial checkpoint procedure, monitoring, migration execution,
   and post-deployment evidence remain blocked or absent.
7. **Can a bad floor be fixed in place?** No. The mutable interval can be raised
   or lowered no further than the floor, but the floor itself requires redeployment.
8. **Is the checked-in ABI correct?** Yes for the integrated source. It is not a
   claim that the old deployed Base runtime implements the new getter.
9. **Is source integration release readiness?** No. Configuration, migration,
   authority, disabled-state, monitoring, and release-time clock revalidation
   remain gates. (Static artifact binding was retired with the
   artifact-expectations pipeline.)
10. **Was a source defect found?** No defect was found in the approved narrow
    design. Important configuration and test gaps are recorded below.

## Executive verdict

> **Integrated fact.** The selected per-deployment immutable is the smallest
> compatible shared-source change that can preserve Base’s approved floor while
> selecting a different Robinhood floor. Its security benefit is the absence of
> an ongoing governance path that can weaken that minimum.

> **Deployment or release gate.** The design moves one material risk from source
> selection to constructor configuration. A wrong nonzero floor can deploy
> successfully and cannot be corrected in place. Exact constructor manifests,
> artifact hashes, disabled-state assertions, and post-deployment getter checks
> are therefore release requirements, not optional bookkeeping.

The owner already accepted the product direction. Nothing in this review reopens
that decision or requests another Lootbox source change.

## Problem before the change

Before `f40dc25f`, the source declared:

```vyper
ONE_DAY: constant(uint256) = 43_200 # on Base
```

That constant was used as the constructor and setter minimum. It was not portable:

| Profile | Approved planning quantum | Count | Modeled duration |
| --- | ---: | ---: | ---: |
| Base | about 2 seconds per committed EVM `NUMBER` | `43_200` | `86_400` seconds |
| Robinhood | about 12 seconds per ancestor-estimate EVM `NUMBER` | `7_200` | `86_400` seconds |

Using `43_200` under the Robinhood planning model would represent about six days,
not one. Replacing the shared constant with `7_200` would represent about four
hours under the Base model. Configuration alone could not solve the old source:
its setter rejected any interval below the hardcoded `43_200`.

**Owner-approved direction.** The S3-only conversion is
`43_200 / 6 = 7_200`. The repository specification explicitly limits that approval
to this Lootbox floor; it is not a general license to divide every block parameter
by six ([model and approval](../shared-block-clock-specification.md#conversion-rule)).

**Historical evidence.** The clock specification records:

- Base documentation describing approximately two-second committed blocks;
- Arbitrum semantics in which Robinhood’s EVM `NUMBER` is an estimate of the
  non-Arbitrum ancestor number and may repeat or jump; and
- a dated 128-child-block Robinhood sample in which the ancestor estimate repeated
  for 88 child blocks and then jumped by two
  ([evidence boundary](../shared-block-clock-specification.md#observed-number-models-and-evidence)).

**Important distinction.** `43_200` and `7_200` are approved configuration values
under a model. The sample is empirical historical evidence. Neither is a guarantee
of block production, elapsed wall time, maximum jump, or future chain behavior.
No live chain was queried for this review.

## Exact source delta

The implementation commit’s production numstat is `12` additions and `3`
deletions in one file. Source identities are:

| Version | Commit | Tree | SHA-256 | Git blob | Bytes / lines |
| --- | --- | --- | --- | --- | ---: |
| Before | `f0bfd0fd5ac2be1d27321463b77248c7cd91d829` | `3f1b95b7f1cda9b8f48f272fafd1830e69598764` | `3c8a011b9c56c953281d3a6b2e13aa2c11a9e57026709252c5e62690122f2d00` | `30a8652dc557d08bf653ce077f226b908d3180df` | 47,364 / 1,322 |
| After | `f40dc25ff0352b6ce79944fb28c37499da7bf0f0` | `f55bb6d46fcd61f28f2ffcd5b1167c967459c432` | `669c2857e2402ef0e8f9a508dd6f342426ffbd1affce11dd429e5b5b0129ae65` | `12d7b6afcc660bc502ad749b7d624fe8f38ab0cb` | 47,731 / 1,331 |

The complete production logic patch is:

```diff
-ONE_DAY: constant(uint256) = 43_200 # on Base
+MIN_UNDERSCORE_SEND_INTERVAL: immutable(uint256)

 def __init__(
     _ripeHq: address,
+    _minUnderscoreSendInterval: uint256,
     _underscoreSendInterval: uint256,
     _undyDepositRewardsAmount: uint256,
     _undyYieldBonusAmount: uint256,
 ):
+    assert _minUnderscoreSendInterval != 0 and _minUnderscoreSendInterval != max_value(uint256) # dev: invalid floor
+    MIN_UNDERSCORE_SEND_INTERVAL = _minUnderscoreSendInterval
     if _underscoreSendInterval != 0:
-        assert _underscoreSendInterval >= ONE_DAY # dev: invalid interval
+        assert _underscoreSendInterval >= MIN_UNDERSCORE_SEND_INTERVAL # dev: invalid interval

+@view
+@external
+def minUnderscoreSendInterval() -> uint256:
+    return MIN_UNDERSCORE_SEND_INTERVAL

 def setUnderscoreSendInterval(_numBlocks: uint256):
-    assert _numBlocks >= ONE_DAY # dev: invalid interval
+    assert _numBlocks >= MIN_UNDERSCORE_SEND_INTERVAL # dev: invalid interval
```

The live integrated lines are the [immutable and constructor validation
lines](../../../../contracts/core/Lootbox.vy#L193-L215) and the [getter/setter
lines](../../../../contracts/core/Lootbox.vy#L1288-L1311).

**Integrated fact.**

- The constructor changed from four to five inputs after adding the floor
  immediately after `_ripeHq`.
- A zero or `max_value(uint256)` floor reverts.
- A zero initial mutable interval remains allowed and leaves rewards disabled.
- A nonzero initial interval must be at least the floor; it stores the reward
  amounts and sets `hasUnderscoreRewards = True`.
- Later setter calls cannot set zero, max, or a value below the immutable floor.
- The distribution condition at
  [`Lootbox.vy:1214`](../../../../contracts/core/Lootbox.vy#L1211-L1215) did not
  change in the implementation patch.
- No event, existing external function, output, or named interface was removed.

## Complete execution and boundary semantics

The gate is:

```text
block.number > lastUnderscoreSend + underscoreSendInterval
```

The three stored concepts must not be conflated:

| Value | Meaning | Units / mutability |
| --- | --- | --- |
| `MIN_UNDERSCORE_SEND_INTERVAL` | Lower bound for this deployment | EVM `NUMBER` units; immutable code value |
| `underscoreSendInterval` | Selected duration between sends | EVM `NUMBER` units; persistent and Switchboard-mutable, never below floor |
| `lastUnderscoreSend` | Absolute EVM number of the last successful send | EVM `NUMBER`; persistent, written after distribution |

For `lastUnderscoreSend = 100` and `underscoreSendInterval = 10`:

- `109` is one block-number unit before the boundary and fails;
- `110` is exact equality and still fails; and
- `111` is the first allowed EVM number.

The strict `>` therefore enforces `interval + 1` in integer `NUMBER` terms. It is
not equivalent to `>=`, and “at the interval” is too early. Tests deliberately
cover all three points for both parameter profiles
([strict matrix](../../../../tests/core/lootbox/test_underscore_rewards.py#L232-L341)).

Construction starts `lastUnderscoreSend` at zero. For an enabled deployment with
interval `7_200`, the first time boundary is `block.number > 7_200`. A disabled
deployment has interval zero and `hasUnderscoreRewards = False`, so distribution
fails earlier at the feature flag. Setting the interval later does not enable the
flag. If separate approved actions later configure amounts and enable rewards at a
chain number already above the floor, the zero `lastUnderscoreSend` means the time
gate is already open. That first-enable sequencing needs explicit operational
control.

**Integrated fact.** The expression reads `block.number`, not `block.timestamp`.
On Base this is the sequential committed L2 number under the documented model. On
Robinhood/Arbitrum it is the ancestor estimate, which can repeat or jump. Repeats
can delay eligibility; jumps can pass the first eligible number. Neither behavior
creates catch-up distributions: one successful call sends one configured amount
and resets `lastUnderscoreSend` to the observed number.

**Independently reproduced result.** Vyper 0.4.3 uses checked `uint256` addition:
an overflowing `last + interval` reverts rather than wrapping. The floor rejects
zero and max, and the setter rejects exact max, but `max - 1` remains technically
settable. After a nonzero last-send value, such an interval can overflow the gate
until governance lowers the mutable interval. Approved `43_200`/`7_200` values are
nowhere near that limit; the edge is nevertheless an untested configuration gap.

## Why the selected design was chosen

The immutable separates chain-specific configuration from shared protocol logic:

1. one audited source and one constructor interface serve Base, Robinhood, and a
   future chain;
2. the deployment selects the cadence floor explicitly;
3. no `chain.id` or token/address conditional enters runtime control flow;
4. governance retains the useful mutable interval but cannot weaken the deployment
   floor; and
5. the new value occupies immutable code layout, not a persistent storage slot.

**Integrated fact.** Existing Base is preserved by non-action, not by upgrading it.
A future Base deployment preserves the old floor only by explicitly passing
`43_200`.

**Design conclusion.** This is the smallest compatible change because the old
hardcoded validation made configuration-only Robinhood support impossible, while
every design with correction-in-place, chain branching, or source duplication
adds a larger authority or audit surface.

## Alternatives considered

| Alternative | Correctness and portability | Storage / ABI | Governance and configuration risk | Migration, audit, and Base impact |
| --- | --- | --- | --- | --- |
| Keep global `43_200` | Correct for Base model; wrong nominal duration for Robinhood model | No change | Low configuration risk, known semantic mismatch | No source rollout, but Robinhood intent is unmet |
| Replace globally with `7_200` | Correct for Robinhood model; weakens Base model to about four hours | No storage; runtime source changes | Low configuration risk, wrong Base policy | Requires shared rollout and breaks future Base equivalence |
| Branch on `chain.id` | Can encode both known chains but requires source edits for future chains and embeds chain identity in logic | No storage needed; ABI can stay stable | No mutable floor, but hardcoded chain-map risk | More branch testing/audit; still requires new deployments; existing Base remains old until rollout |
| Mutable governance floor | Portable and correctable | Adds persistent state and floor setter/event/permissions to ABI | Misconfiguration can be repaired, but governance can also weaken the safety floor forever | Larger authority, storage, test, audit, and migration surface; Base can be preserved only by configuration |
| Robinhood-specific Lootbox | Can be correct per chain | Separate ABI/source can drift | Configuration isolated, divergence risk permanent | Duplicates audit and migration paths; Base stays untouched but one-canonical-source policy fails |
| Per-deployment immutable | Correct when constructor input is approved; portable without branching | One constructor input/getter; no persistent slot | One-time high-consequence input; no governance downgrade or in-place correction | Small source delta; shared audit; new deployments required; future Base can pass `43_200` |

**Explicitly not recommended.** A no-change configuration workaround does not
exist: the old setter itself enforced the Base constant. The chosen design is not
perfectly risk-free; it deliberately accepts redeployment as the remedy for a bad
floor in exchange for removing governance weakening.

## Base impact

> **Integrated fact.** No Base migration, registry transaction, capability change,
> state write, or deployed bytecode change is caused by merging source. The
> historical migration files are byte-identical at the implementation parent,
> implementation commit, and reviewed `HEAD`.

**Historical evidence.** The implementation record’s 24 July 2026 read-only Base
snapshot found the old 21,637-byte runtime and interval `43_200`. This review
reproduced that old runtime offline from the pre-change source and documented
constructor inputs. It did not refresh live Base state.

Existing Base and a hypothetical future Base are separate:

- **Existing deployment:** remains the old runtime, has old persistent state, and
  does not implement `minUnderscoreSendInterval()`.
- **Future deployment:** the shared current source can preserve the Base floor by
  passing `43_200`; a nonzero interval `43_200` preserves enabled constructor
  behavior, while interval zero is a deliberately disabled rollout posture.
- **State continuity:** a new contract begins with fresh storage, including
  `lastUnderscoreSend = 0`; there is no state-import setter.
- **Checked-in ABI:** exactly matches current source. Its existing selectors remain
  compatible with the old runtime, but its new getter must not be treated as
  supported by the old deployed contract.

> **Deployment or release gate.** Any Base convergence requires a new numbered
> forward migration, current live-state/code revalidation, explicit registry and
> mint-capability sequencing, reward-window continuity policy, rollback analysis,
> and owner approval. Source integration supplies none of those permissions.

## Robinhood impact

**Owner-approved direction.** The S3 deployment posture is:

```text
_minUnderscoreSendInterval = 7_200
_underscoreSendInterval    = 0
hasUnderscoreRewards        = false
```

The specification also requires the Underscore route to be absent and reward mint
capability disabled at launch
([component row](../robinhood-deployment-support-specification.md#L1098)).
The constructor’s reward-amount arguments are still required ABI inputs, but when
the initial interval is zero the constructor deliberately leaves both stored
amounts at zero.

**Current fact.** `DefaultsRobinhood.vy`, `config/BluePrint.py`, the derived
parameter ledger, Lootbox deployment-profile evidence, and a deterministic
Robinhood deployment/registration migration source now exist. The migration
plan remains blocked and non-executable, and there is no migration history,
execution, onchain deployment, or registration. The reserved
`0010_Track6S3LootboxFloor.py` step is a planning assertion rather than an
onchain upgrade
([reservation](../robinhood-deployment-support-specification.md#L1213)).

> **Deployment or release gate.** The deployment owner must supply and approve
> every constructor input in exact order, bind it to the reviewed creation
> artifact, and prove after deployment:
>
> - getter floor `7_200`, interval zero, rewards disabled, and reward amounts zero;
> - the actual runtime hash including all immutables;
> - the intended registry position and absence of unintended mint capability;
> - no Underscore distributor route; and
> - the approved authority path before any later configuration or enablement.

No address, signer, role assignment, reward amount, or deployment actor is inferred
by this document.

If the wrong floor is supplied:

- zero or max reverts construction;
- a smaller nonzero floor with interval zero deploys but permits a later unsafe
  lower interval;
- a larger floor deploys but can prevent selecting the intended cadence;
- a nonzero interval below the floor reverts;
- a nonzero interval at or above the floor enables rewards during construction;
  and
- the floor has no corrective setter; replacement is required.

Getter/runtime/manifest comparison detects a bad floor immediately. Interval,
feature-flag, reward-amount, capability, and registry checks detect the surrounding
bad posture. Distribution events, `lastUnderscoreSend`, event `blockNumber`, and
offchain elapsed-time observations can detect operational cadence drift after
activation, but monitoring cannot turn the modeled cadence into a guarantee.

## Deployment and migration implications

All four Base migration call sites were inspected:

| Historical file | Current call shape | Current-source result |
| --- | --- | --- |
| [`1016_Lootbox.py`](../../../../migrations/base-mainnet/1016_Lootbox.py#L5-L20) | `Lootbox(hq)` | Missing four current arguments |
| [`2025071801_LootBoxPointsRefresh.py`](../../../../migrations/base-mainnet/2025071801_LootBoxPointsRefresh.py#L28-L59) | `Lootbox(hq)` | Missing four current arguments |
| [`2025080900_Lootbox.py`](../../../../migrations/base-mainnet/2025080900_Lootbox.py#L6-L11) | `Lootbox(hq)` | Missing four current arguments |
| [`2025112500_New_Endaoment_Features.py`](../../../../migrations/base-mainnet/2025112500_New_Endaoment_Features.py#L80-L86) | Old four-argument constructor | Missing the new floor argument |

The migration helper loads the currently mapped source and forwards the script’s
arguments ([deployment helper](../../../../scripts/utils/migration.py#L166-L176)).
Therefore, loading current `Lootbox.vy` through those old Python call sites is not
a reproducible deployment: constructor arity is wrong. Historical execution can
only be reproduced from its pinned historical source/artifact/manifest context.

**Integrated fact.** Not rewriting those files is correct historical-integrity
policy. It does not make them forward-compatible.

> **Deployment or release gate.** A future Base replacement and the initial
> Robinhood deployment each need a new explicit current-constructor path. Local
> profile tests prove constructor order and readback, and the integrated
> Robinhood migration source consumes the five bindings. Unresolved plan inputs
> prevent execution, and no migration has run.

## Test-to-invariant matrix

| Invariant | Exact test evidence | Genuine sensitivity and result |
| --- | --- | --- |
| Zero/max floors reject; Base/RH below/exact/above cases; constructor preserves values | [`test_constructor_floor_interval_matrix`](../../../../tests/core/lootbox/test_underscore_rewards.py#L75-L125) | Reads both getters/flag and expects exact reverts; sensitive to validation, argument order, and immutable preservation. Passed inside the reviewed-snapshot 175-test run. |
| Robinhood interval zero retains floor and disables rewards | [`test_robinhood_disabled_deployment_retains_floor_without_rewards`](../../../../tests/core/lootbox/test_underscore_rewards.py#L128-L159) | Proves floor `7_200`, zero interval/amounts, false flag, rejected distribution, bounded later setter, and no implicit enable. Passed. |
| Both floors bind later governance updates | [`test_setter_matrix_uses_deployment_floor`](../../../../tests/core/lootbox/test_underscore_rewards.py#L162-L230) | Covers unauthorized, floor-minus-one, max, exact floor, floor-plus-one, no-change, paused, state, and event. Sensitive to replacing immutable check with a global constant. Passed. |
| One-before and equality fail; plus one succeeds for Base and RH | [`test_distribution_strict_boundary_under_both_parameter_profiles`](../../../../tests/core/lootbox/test_underscore_rewards.py#L232-L341) | Directly kills a `>` to `>=` mutation, checks state/event observation, and rejects repeated number. Passed. |
| Representative/stress jumps do not bypass the interval and later succeed | [`test_representative_and_stress_jumps_do_not_bypass_interval`](../../../../tests/core/lootbox/test_underscore_rewards.py#L344-L428) | Tests `+2/+4` and `+60` synthetic profiles under both floors; post-review commit `3c1fea8` added the success landing. Passed. |
| First send uses zero initial checkpoint | [`test_first_distribution_timing`](../../../../tests/core/lootbox/test_underscore_rewards.py#L752-L775) | Checks `last = 0` and advances to `interval + 1`; sensitive to first-send boundary. Passed. It does not cover later enablement of an initially disabled deployment at a high chain number. |
| The gate is NUMBER, not timestamp | [independent clock control](../../../../tests/clock/test_clock_profiles.py#L329-L347) plus [strict matrix](../../../../tests/core/lootbox/test_underscore_rewards.py#L259-L341) | Boundary tests move NUMBER explicitly while the harness proves timestamp independence. A timestamp substitution would not satisfy the observed state/event expectations. All 57 harness tests passed. |
| Governance forwarding preserves rejected action/state | [`test_switchboard_three_forwards_below_floor_rejection`](../../../../tests/config/test_switchboard_charlie.py#L1797-L1823) | Executes the timelocked forwarded value, expects Lootbox revert, and checks interval plus pending action remain intact. Passed in the reviewed-snapshot two-test run. |
| Authorized timelocked interval update still works | [`test_switchboard_three_set_underscore_send_interval_timelock`](../../../../tests/config/test_switchboard_charlie.py#L1746-L1794) | Covers caller, pending action, timelock, execution, state, event, and cleanup. Passed in the same reviewed-snapshot run. |
| Claims, deposit/borrow points, and RIPE rewards remain unchanged by the floor source change | [borrow points](../../../../tests/core/lootbox/test_loot_borrow_points.py#L6-L49), [claims](../../../../tests/core/lootbox/test_loot_claim.py#L7-L61), [deposit points](../../../../tests/core/lootbox/test_loot_deposit_points.py#L7-L64), [RIPE rewards](../../../../tests/core/lootbox/test_loot_ripe_rewards.py#L9-L56) | These suites do not isolate the new floor. They were included in the reviewed-snapshot 175-pass run; later reward-launch tests changed the current suite and were not rerun for this refresh. |
| Inventory classifies and content-pins production source | `path/content pin`, BN-025 rows | Checker validates exact path/hash/occurrences. Current checker is green. |
| Floor discovery fails on delete/rename/move | `exact pattern and mutations` | Explicit mutation-sensitive tests; all four cases passed within the reviewed-snapshot 95-test inventory run. |
| Local deployment profile supplies five correct arguments | ``test_lootbox_deployment_profiles.py`` (retired) | Tests pin canonical draft profiles, constructor ABI order, deployment/readback, and historical Base incompatibility. Current `rh` now also has a deterministic Robinhood migration source; no migration has executed. |
| Max-minus-one interval overflows `last + interval` | [`test_x3_max_minus_one_interval_is_settable_but_gate_addition_overflows`](../../../../tests/core/lootbox/test_underscore_rewards.py) | Current test establishes the accepted fail-closed checked-addition boundary; a sane upper limit would require a separate source/configuration decision. |
| General mutation testing | No mutation framework run | **Gap:** boundary and inventory tests are demonstrably mutation-sensitive, but there is no broad compiler/source mutation score. |

## Historical versus current validation evidence

### Historical implementation evidence

**Historical evidence.** The S3 implementation record reports, at its reconciled
commit `51e5c5a`:

- 59 Underscore tests passed;
- 91 SwitchboardCharlie tests passed;
- all 175 Lootbox tests passed;
- 57 clock-profile tests passed;
- 60 then-current inventory tests passed;
- the then-current checker reported `100/95/17`; and
- the full suite reported 2,722 passed and 142 deselected.

Those counts belong to that historical snapshot
([recorded results](../lootbox-floor-implementation-record.md#final-validation-after-phase-g)).
They are not current integrated inventory or full-suite results.

### Independently reproduced at the reviewed snapshot

**Independently reproduced result.**

| Reviewed-snapshot command scope | Result |
| --- | --- |
| `tests/core/lootbox/` | `175 passed` in 121.92 s |
| `tests/clock/test_clock_profiles.py` | `57 passed` in 106.66 s |
| Inventory collection | `95 tests collected` |
| `tests/inventory/test_block_clock_inventory.py` | `95 passed` in 45.57 s |
| Two named interval-governance Switchboard tests | `2 passed` in 108.09 s |
| `scripts/check_block_clock_inventory.py --check` | Clean; `99` production occurrences, `94` production lines, `17` production files, `474` cadence candidates |
| ABI/compiler/runtime analysis | Reproduced with Vyper 0.4.3 / Titanoboa 0.2.7; checked-in ABI byte-for-byte semantic match |

The first sandboxed Lootbox attempt could not bind the suite’s localhost Anvil
fixture and produced setup errors before executing tests. The identical offline
command was rerun with localhost-bind permission and passed. No public RPC, secret,
account, signer, fork, or authenticated service was used.

**Not rerun.** The complete repository suite was not needed to resolve a
contradiction and was not run. The `2,722` figure remains historical only.

## Compiler, ABI, storage, bytecode, and artifact analysis

**Independently reproduced result.** Existing environment:

```text
Vyper       0.4.3 commit bff19ea2
Titanoboa   0.2.7
pytest      8.4.2
settings    optimize=codesize, experimental_codegen=false
```

The checked-in [`Lootbox.json`](../../../../scripts/abis/Lootbox.json) has SHA-256
`33aadc219718332ef9163f0b85c8e6fba93735d149db3fb0bb2e3fab814db17c`.
Fresh compiler output exactly equals that JSON semantically.

| ABI property | Before | After |
| --- | ---: | ---: |
| Entries / functions / events | 50 / 40 / 9 | 51 / 41 / 9 |
| Constructor | `(address,uint256,uint256,uint256)` | `(address,uint256,uint256,uint256,uint256)` |
| Added selector | — | `minUnderscoreSendInterval()` = `0x20682f44` |
| Removed or changed existing selector | None | None |
| Changed event definition | None | None |
| Canonical ABI SHA-256 | `5529602a50f22396d9af92ac108582e8c22ea0463be1d330c50b63aa4ffd2cc7` | `e752a206ba5c78cb573c734c7bfd1c407f1cb98898d3d8e9d3513836c56f5fb2` |

Persistent storage layout is identical:

| Slot | Value |
| ---: | --- |
| 0 | `deptBasics.isPaused` |
| 1 | `hasUnderscoreRewards` |
| 2 | `underscoreSendInterval` |
| 3 | `lastUnderscoreSend` |
| 4 | `undyDepositRewardsAmount` |
| 5 | `undyYieldBonusAmount` |

Code/immutable layout adds only
`MIN_UNDERSCORE_SEND_INTERVAL: uint256` at offset 96. Existing immutable values
remain at offsets 0, 32, and 64. This is why persistent state slots do not move
while deployed runtime changes.

Exact artifacts reproduced from Git archives of the implementation parent and
implementation commit:

| Artifact | Before | After |
| --- | --- | --- |
| Compiler source SHA-256 | `3d7fdd84ec2ed9e4f2008e5b104b73f7ed55a3f24ba988e38aa7b626f544d33e` | `ebb4dcca8fa95bafe8e38ddc1d01886bfaceaf06302fe195f63db0bb7b3ef1da` |
| Compiler integrity | `d968edd935c3f2d321690a5693471c74868a55615cd7439675511e4d33968ded` | `83995dbf831851f53870db14fec4daaea419fb036b7d081a1948ed02222974e1` |
| Creation bytes | 21,799 | 21,911 |
| Creation SHA-256 | `756ea05256de11539786d68ff2ccf1fc48d25f9ff73c2e97832c5d46e32d60b9` | `9246a6d9dbee596750dc3a50d27d4418f318a62b7b4826a13f76aee37621e6ce` |
| Creation Keccak-256 | `05b44353899b59584d548cfcb91dc82a2763f343bd305a165c6bda777f611c99` | `eac656469e5c692146b583e6047d0df3e6792b6fb55a3cfb79c821d599cdea6d` |
| Runtime-template bytes | 21,541 | 21,569 |
| Runtime-template SHA-256 | `62d5c161a7e00709b58593581ee66ef3437cfc23c9e5c2b6311685bb741582d5` | `db9c2b91497a6e11191a181c9cbe1776e96532e50ff3e60e17f0bd447354e097` |
| Runtime-template Keccak-256 | `a00bf2fb14db4a8d8ca345201739d536df80772a39e3cb004dc5785ea0ac624f` | `52bac86d5299ed7625f548a69057d02971630c39b269e06782131a8d8c9ad909` |

Offline deployments holding the documented historical Base HQ immutable constant
isolated the source/floor change:

| Local candidate | Bytes | SHA-256 | Keccak-256 |
| --- | ---: | --- | --- |
| Pre-change Base-compatible | 21,637 | `db139674e84185d013b77211eb769631a9d3c0b5cc45ff90a00e0086095843da` | `b3a2f6516aab23a9842e504b8cc8140167369b84d4f1f4fe787d76078019c6eb` |
| New Base floor-isolation | 21,697 | `fa638d6a25a1386a6afd18afccab2ece9f04029088556b3acc33163a374c7673` | `ce618917599928903b0233cb400fe28a61bbda45d3417aecff14eda417b4136d` |
| New Robinhood floor-isolation | 21,697 | `a992e766fd5e8252ded0b2da6e2b1f90ace39a4644936065f1240f17ea65809d` | `9ea55bcdff1d8b39c9db8d89e5cab5b540f83a146904f6998df53ffb5b5f74dc` |

These are reproducible comparison candidates, not a Robinhood deployment claim.
The actual runtime also embeds the approved HQ immutable, so a final Robinhood
runtime hash cannot be known until that input is owner-approved and bound.

## Known gaps and residual risks

| Risk | Classification | Assessment / control |
| --- | --- | --- |
| Wrong floor input | Deployment/configuration gate | Nonzero wrong values can deploy; exact manifest, constructor decode, getter, and runtime comparison required |
| Immutable misconfiguration | Accepted design tradeoff plus deployment gate | Removes governance weakening but makes replacement the correction path |
| Wrong nonzero initial interval | Deployment/configuration gate | Can enable rewards at construction; require interval-zero and flag/amount/capability assertions for RH launch |
| `last = 0` on later enablement | Monitoring concern / deployment gate | Time gate may already be open; explicitly control first-enable and first-send sequence |
| Block-time/model drift | Accepted design tradeoff plus monitoring concern | Revalidate assumptions at release and monitor event wall-time; do not promise a day |
| Repeated numbers, jumps, bursts, or halt | Accepted design tradeoff | Repeats/halts delay; jumps may cross boundary; no catch-up; operational alerts should distinguish chain behavior from contract failure |
| Strict-`>` misunderstanding | Monitoring/documentation concern | Equality fails; runbook and post-deploy probe must use `last + interval + 1` |
| Extreme interval checked-add overflow | Covered accepted boundary / configuration gate | Max-minus-one remains allowed and its checked-addition revert is pinned; an approved sane maximum would be a separate source decision |
| Historical migration replay | Deployment/configuration gate | Old scripts are intentionally immutable but incompatible with current constructor; use new forward paths |
| Blocked executable deployment path | Deployment/configuration gate | Robinhood migration source and a deterministic executor are integrated, but unresolved bindings keep the plan non-executable; there is no migration history, execution, deployment, or new Base migration |
| Inadequate monitoring | Monitoring concern | Observe immutable, mutable state, feature flag, capability, registry, distribution events, and elapsed wall time |
| Future-chain reuse | Future hardening | New chain needs approved empirical/model evidence and explicit constructor value; do not reuse `7_200` by analogy |
| Stale test/evidence counts | Monitoring/documentation concern | Pin commit and command output; the reviewed-snapshot 95-test/99-94-17 evidence must not be presented as the current inventory. The fresh current checker reports 102 production occurrences, 97 production lines, 18 production files, and 640 cadence candidates. |
| Deleverage, CCIP, zero-backing settlement | Not applicable / owner-parked | Outside Lootbox scope and not Lootbox blockers |

No residual listed here grants authority to modify Lootbox source in this task.

## Recommendations

### Currently required

> **Deployment or release gate.**

1. Pin the exact reviewed source, ABI, Vyper settings, creation hash, and ordered
   constructor manifest before any deployment rehearsal.
2. For Robinhood, encode the approved floor `7_200` and interval zero only in a
   separately reviewed deployment path; obtain explicit approval for every other
   input without inferring addresses, actors, or reward values.
3. Verify the deployed getter, interval, amounts, flag, runtime, registry, and
   capability posture before considering enablement.
4. Revalidate the Robinhood EVM-number model and observed cadence at release time.
   Treat changes as configuration/release evidence, not automatic source changes.
5. Keep rewards, Underscore routes, and mint capability disabled until their
   separate owner gates close.
6. If Base convergence is pursued, use a new forward migration and a separately
   approved state-window, authority, registry, rollback, and temporary-drift plan.
7. Retain the integrated migration/executor tests and add exact-runtime
   Lootbox execution evidence only when a fully bound plan and rehearsal are
   separately authorized; draft-profile tests do not replace that evidence.

### Recommended hardening

> **Agent recommendation — unapproved.**

1. Retain the current constructor-order/readback, later-enable, and
   max-minus-one overflow regressions when a future deployment path is added.
2. Consider a separately approved sane upper bound if governance should never
   select impractical intervals.
3. Monitor distribution event gaps in both EVM-number and wall-time domains, with
   alerts that distinguish repeat/jump/halt behavior from wrong configuration.
4. Regenerate snapshot-specific evidence counts in every release packet rather
   than copying historical totals.

### Owner-parked

> **Owner-parked work.** Further Deleverage work, CCIP workflows,
> zero-backing settlement, loss allocation, and bad-debt policy are outside this
> process. They are neither Lootbox blockers nor current assignments.

### Explicitly not recommended

- Do not rewrite historical Base migrations.
- Do not introduce `chain.id` branching or a Robinhood-only Lootbox.
- Do not make the safety floor governance-mutable merely to repair deployment
  process risk.
- Do not replay old migration call sites against current source.
- Do not infer a Robinhood address, signer, role, reward amount, or final runtime.
- Do not treat a green source/test review as deployment, activation, or release
  approval.
- Do not turn integrated planning, configuration, or test evidence into a claim
  of migration execution, deployment, activation, or release.

## Primary sources and reproducible commands

Primary repository evidence:

- [Production source](../../../../contracts/core/Lootbox.vy#L193-L215)
- [Distribution gate and state update](../../../../contracts/core/Lootbox.vy#L1203-L1258)
- [Checked-in ABI](../../../../scripts/abis/Lootbox.json#L1510-L1521)
- [Central Base fixture](../../../../tests/conf_core.py#L428-L438)
- [Underscore floor/boundary tests](../../../../tests/core/lootbox/test_underscore_rewards.py#L70-L428)
- [Clock profiles and evidence labels](../../../../tests/utils/clock_profiles.py#L29-L93)
- [Clock harness tests](../../../../tests/clock/test_clock_profiles.py#L109-L222)
- Inventory checker pattern
- Current-state inventory bindings
- [Lootbox implementation record](../lootbox-floor-implementation-record.md)
- [Shared clock specification](../shared-block-clock-specification.md)
- Track 6 source specification
- [Validation plan](../block-clock-validation-plan.md)
- S3 controlling brief
- [Directory documentation standard](README.md#documentation-standard)

Core identity and patch commands:

```bash
git branch --show-current
git rev-parse HEAD^{commit} HEAD^{tree} refs/heads/rh refs/remotes/origin/rh
GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c core.askPass= \
  ls-remote --heads origin refs/heads/rh
git show --format=fuller --stat f40dc25ff0352b6ce79944fb28c37499da7bf0f0
git diff --no-ext-diff f0bfd0fd5ac2be1d27321463b77248c7cd91d829 \
  f40dc25ff0352b6ce79944fb28c37499da7bf0f0 -- contracts/core/Lootbox.vy
git show f0bfd0fd5ac2be1d27321463b77248c7cd91d829:contracts/core/Lootbox.vy \
  | shasum -a 256
shasum -a 256 contracts/core/Lootbox.vy scripts/abis/Lootbox.json
git hash-object contracts/core/Lootbox.vy scripts/abis/Lootbox.json
```

Current bounded validation used `PYTHONDONTWRITEBYTECODE=1`,
`ETHERSCAN_API_KEY=local-placeholder`, pytest cache disabled, a mode-0700 private
Boa cache, and a private `--basetemp`. The logical commands were:

```bash
pytest -q -p no:cacheprovider tests/core/lootbox
pytest -q -p no:cacheprovider tests/clock/test_clock_profiles.py
pytest --collect-only -q -p no:cacheprovider \
  tests/inventory/test_block_clock_inventory.py
pytest -q -p no:cacheprovider tests/inventory/test_block_clock_inventory.py
pytest -q -p no:cacheprovider \
  tests/config/test_switchboard_charlie.py::test_switchboard_three_set_underscore_send_interval_timelock \
  tests/config/test_switchboard_charlie.py::test_switchboard_three_forwards_below_floor_rejection
python scripts/check_block_clock_inventory.py --check
```

Exact historical artifact reproduction used read-only Git archives in private
temporary directories, the installed Vyper/Boa environment, raw byte-array
SHA-256/Keccak-256, canonical sorted ABI JSON, and local Boa deployments only. It
did not install dependencies, query RPC, or mutate repository state.

## Final owner-facing conclusion

> **Integrated fact.** `f40dc25f` converted exactly one Base-specific Lootbox
> policy floor into a validated constructor immutable, retained the strict
> distribution boundary, preserved persistent layout and every existing
> selector/event, and added only the constructor input plus a getter.

The design is appropriate because the floor is chain-deployment configuration
with safety significance: it must vary across approved cadence models, but it
should not become an ordinary mutable governance parameter. Base’s deployed
contract remains untouched; Robinhood’s intended `7_200`/zero disabled posture
remains a deployment input, not a deployed fact.

The integrated source and current focused validation are strong enough to explain
the change. They are not enough to deploy or release it. The next legitimate
owner decision is the separately gated deployment/configuration package with exact
constructor inputs, disabled-state proof, authority sequencing,
monitoring, and release-time cadence revalidation—not another Lootbox source edit.
