# RH Lootbox distribution monitoring

> **DRAFT — no distribution, configuration, pause, or deployment authority.**
> The canonical offline profiles keep RH rewards disabled at construction with
> floor `7_200`, interval `0`, flag `false`, and stored amounts zero
> ([lootbox-deployment-profiles.json](../../../../scripts/proposals/lootbox-deployment-profiles.json),
> [test_lootbox_deployment_profiles.py](../../../../tests/deployment_profiles/test_lootbox_deployment_profiles.py)).

## 1. Signals and exact sources

| Signal | Exact source and dated reference | Required capture |
| --- | --- | --- |
| Immutable floor | `Lootbox.minUnderscoreSendInterval()` returns the constructor-bound floor ([Lootbox.vy:196-215](../../../../contracts/core/Lootbox.vy#L196), [Lootbox.vy:1288-1291](../../../../contracts/core/Lootbox.vy#L1288)) | Lootbox address/code hash, value, block/hash |
| Governed posture | `hasUnderscoreRewards()`, `underscoreSendInterval()`, `undyDepositRewardsAmount()`, and `undyYieldBonusAmount()` public getters ([Lootbox.vy:179-193](../../../../contracts/core/Lootbox.vy#L179)) | All five configuration/readback values at one block/hash |
| Last distribution identity | `lastUnderscoreSend()` public getter; success stores the EVM `block.number` used by the interval gate ([Lootbox.vy:1211-1215](../../../../contracts/core/Lootbox.vy#L1211), [Lootbox.vy:1257-1258](../../../../contracts/core/Lootbox.vy#L1257)) | Value before/after, receipt block/hash |
| Distribution event | `UnderscoreRewardsDistributed(address,uint256,uint256,uint256)` with distributor, deposit amount, yield amount, and emitted `blockNumber` ([Lootbox.vy:161-165](../../../../contracts/core/Lootbox.vy#L161), [Lootbox.vy:1264-1269](../../../../contracts/core/Lootbox.vy#L1264)) | Emitter, topics/data, decoded fields, transaction/log index |
| Configuration events | `HasUnderscoreRewardsUpdated`, `UnderscoreSendIntervalUpdated`, `UndyDepositRewardsAmountUpdated`, and `UndyYieldBonusAmountUpdated` ([Lootbox.vy:167-177](../../../../contracts/core/Lootbox.vy#L167)) | Transaction/log evidence and post-event getter readbacks |
| EVM-number domain | Contract `block.number`; Offchain Labs documents that on Arbitrum chains it is an approximate first non-Arbitrum ancestor value that may repeat and jump ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | EVM number observed by event/getter plus receipt child number |
| Wall-time domain | Receipt timestamp and monitor clock, kept separate from the EVM-number gate; Offchain Labs documents short-term block-number/time assumptions as unreliable and timestamp rules separately ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | UTC receipt time, observation time, elapsed seconds |
| Failure | Revert reason/bytes for no permissions, pause, disabled rewards, zero interval, strict boundary, no available rewards, zero reward total, distributor absence, approval/transfer failure, or checked arithmetic ([Lootbox.vy:1203-1256](../../../../contracts/core/Lootbox.vy#L1203)) | Selector/sender, pre-state getters, receipt/trace |

## 2. Threshold logic

The protocol gate is exact
([Lootbox.vy:1211-1215](../../../../contracts/core/Lootbox.vy#L1211)):

```text
eligible_number = lastUnderscoreSend + underscoreSendInterval + 1
eligible        = block.number >= eligible_number
equivalently    = block.number > lastUnderscoreSend + interval
```

| Condition | Concrete threshold/formula and derivation | Classification |
| --- | --- | --- |
| RH disabled posture | `floor == 7_200`, `interval == 0`, `hasRewards == false`, and both amounts `== 0` ([lootbox-deployment-profiles.json](../../../../scripts/proposals/lootbox-deployment-profiles.json)) | Expected before separately authorized enablement |
| Misconfiguration | `hasRewards == true && interval == 0`; distribution then fails the explicit nonzero-interval guard ([Lootbox.vy:1209-1214](../../../../contracts/core/Lootbox.vy#L1209)) | Critical configuration alert |
| Below-floor interval | `interval != 0 && interval < floor`; constructor/setter reject this relation ([Lootbox.vy:208-215](../../../../contracts/core/Lootbox.vy#L208), [Lootbox.vy:1303-1311](../../../../contracts/core/Lootbox.vy#L1303)) | Critical if observed |
| Repeat/equality | `block.number <= last + interval` remains too early; equality is not eligible ([test_underscore_rewards.py:240-341](../../../../tests/core/lootbox/test_underscore_rewards.py#L240)) | Expected gate rejection |
| First eligible | `block.number == last + interval + 1`; tests pin both the existing-send and initially-disabled/later-enabled `last==0` cases ([test_underscore_rewards.py:240-341](../../../../tests/core/lootbox/test_underscore_rewards.py#L240), [test_underscore_rewards.py:1329-1458](../../../../tests/core/lootbox/test_underscore_rewards.py#L1329)) | Expected success if every other condition is valid |
| EVM-number jump | A jump that lands at or above `eligible_number` legitimately opens the gate; representative and stress jumps are tested without changing the formula ([test_underscore_rewards.py:344-430](../../../../tests/core/lootbox/test_underscore_rewards.py#L344)) | Topology alert only; not automatically misconfiguration |
| EVM-number halt/repeat | Repeated number cannot advance eligibility; Offchain Labs documents repeated ancestor estimates as expected topology ([test_underscore_rewards.py:329-341](../../../../tests/core/lootbox/test_underscore_rewards.py#L329), [Arbitrum reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | No protocol alert by count alone; wall-time paging threshold **UNRESOLVED — owner decision** |
| Event/state mismatch | After success, event `blockNumber != lastUnderscoreSend` or either differs from the EVM number used by the call ([Lootbox.vy:1257-1269](../../../../contracts/core/Lootbox.vy#L1257), [test_underscore_rewards.py:305-327](../../../../tests/core/lootbox/test_underscore_rewards.py#L305)) | Critical immediately |
| Extreme interval | `max_value(uint256)` is rejected; `max-1` is settable, and a later checked `last + interval` can revert on overflow without changing `last` ([Lootbox.vy:1303-1311](../../../../contracts/core/Lootbox.vy#L1303), [test_underscore_rewards.py:1426-1458](../../../../tests/core/lootbox/test_underscore_rewards.py#L1426)) | Warn on unusually high value; sane upper bound **UNRESOLVED — owner decision** |
| Missed distribution in wall time | Enabled, otherwise healthy, EVM-eligible, but no success event after an owner grace period | Grace period and paging destination **UNRESOLVED — owner decision** |

No fixed seconds-per-block conversion is an alert invariant. The contract uses
the EVM-number domain, while the chain documentation says short-term timing
assumptions are unreliable
([Lootbox.vy:1211-1215](../../../../contracts/core/Lootbox.vy#L1211),
[Arbitrum reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)).

## 3. Expected and anomalous states

| State | Expected | Anomalous |
| --- | --- | --- |
| RH draft/offline | Rewards disabled, interval/amounts zero, immutable floor `7_200`; distribution reverts `no underscore rewards` ([test_underscore_rewards.py:128-159](../../../../tests/core/lootbox/test_underscore_rewards.py#L128)) | Any enabled flag or nonzero stored amount without a separately authorized configuration record |
| Enabled and waiting | `interval >= floor`, positive intended amounts, and `block.number <= last + interval`; repeated ancestor estimates simply extend wall time ([Lootbox.vy:1209-1229](../../../../contracts/core/Lootbox.vy#L1209), [Arbitrum reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Success before the strict boundary, or a configuration getter/event mismatch |
| Enabled and eligible | `block.number >= last + interval + 1`; success updates `last`, emits the same number, and accounts for the minted rewards ([Lootbox.vy:1231-1269](../../../../contracts/core/Lootbox.vy#L1231)) | No event/state update after a successful receipt, amount reconciliation failure, or repeated operational failure after eligibility |
| Jump | A native-number jump can cross the threshold in one observation and permit one distribution ([test_underscore_rewards.py:344-430](../../../../tests/core/lootbox/test_underscore_rewards.py#L344)) | Monitor labels the jump as a below-floor bypass, or multiple distributions reuse one EVM number |
| Halt | No eligibility progress while the native EVM number repeats; elapsed wall time is recorded separately ([Arbitrum reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Monitor silently converts wall time to block eligibility or suppresses an owner-defined wall-time availability alert |
| Misconfiguration/failure | Contract rejects invalid floor/interval, disabled state, insufficient rewards, missing distributor, and checked overflow ([Lootbox.vy:196-215](../../../../contracts/core/Lootbox.vy#L196), [Lootbox.vy:1203-1256](../../../../contracts/core/Lootbox.vy#L1203)) | Retrying without identifying which precondition failed, or treating an arithmetic revert as cadence waiting |

## 4. Pause, escalation, and recovery

| Step | Required action and evidence | Authority |
| --- | --- | --- |
| 1. Confirm | At one block/hash read code hash, floor, interval, flag, amounts, last send, available rewards, distributor address, receipt child number, EVM number, and wall time; preserve raw responses and relevant configuration events. Sources are listed in Section 1. | Read authority: **UNRESOLVED — owner decision** |
| 2. Classify | Distinguish repeat, positive jump, native-number halt, disabled posture, flag/interval mismatch, amount/reward shortage, missing distributor, transfer failure, and checked overflow using the exact guards ([Lootbox.vy:1203-1256](../../../../contracts/core/Lootbox.vy#L1203)). | Incident classifier: **UNRESOLVED — owner decision** |
| 3. Contain | Stop automated distribution submissions and prepare the smallest applicable pause/disable action; do not change cadence or amount merely to clear an alert. Setters are Switchboard-only and pause-gated ([Lootbox.vy:1294-1311](../../../../contracts/core/Lootbox.vy#L1294)). | Pause/config signer and quorum: **UNRESOLVED — owner decision** |
| 4. Escalate | Supply configuration/event history, last successful distribution, first failure, raw revert/trace, EVM-number and wall-time series, available rewards, distributor/allowance/balance evidence, and affected downstream operation. | Rewards/protocol/security owners and distributor operator: **UNRESOLVED — owner decision** |
| 5. Recover | Require owner-approved configuration/cause correction; re-read every constructor/config field, prove the strict `last + interval + 1` boundary, execute an authorized canary only if separately approved, and reconcile event, state, minted amount, deposit reward, and yield transfer ([Lootbox.vy:1211-1269](../../../../contracts/core/Lootbox.vy#L1211)). | Recovery/distribution/unpause signer and quorum: **UNRESOLVED — owner decision** |
| 6. Close | Attach before/after config, code hashes, event/state arithmetic, failed and successful receipts, commands/environment, and restored monitor evidence. | Closure approver/retention: **UNRESOLVED — owner decision** |

## 5. Residual risk after recovery

The cadence is tied to native EVM-number behavior, not a wall-clock service
level, so repeats and jumps can change elapsed real time without violating the
contract formula
([Arbitrum reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)).
The source has no owner-approved sane upper bound below `max-1`; choosing one is
a separate owner decision
([Lootbox.vy:1303-1311](../../../../contracts/core/Lootbox.vy#L1303),
[test_underscore_rewards.py:1426-1458](../../../../tests/core/lootbox/test_underscore_rewards.py#L1426)).
Local profile and boundary tests do not constitute live deployment,
configuration, monitoring, or distributor evidence
([lootbox.md, recommendations](../smart-contract-changes/lootbox.md#recommendations)).
