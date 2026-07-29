# RH Ledger action-block monitoring runbook

> **DRAFT — offline release support, not monitoring deployment or pause
> authority.** Ledger selects one immutable action-block source at deployment:
> zero uses native `block.number`; exact `0x64` uses
> `ArbSys.arbBlockNumber()`; all other sources fail construction
> ([Ledger.vy:130-132](../../../../contracts/data/Ledger.vy#L130),
> [Ledger.vy:189-230](../../../../contracts/data/Ledger.vy#L189)).

## 1. Signals and exact sources

| Signal | Exact source and dated reference | Required capture |
| --- | --- | --- |
| Selected mode | `Ledger.ACTION_BLOCK_SOURCE()` immutable getter; RH profile requires exact `0x0000000000000000000000000000000000000064` ([ledger-robinhood-profile.json](../../../../scripts/proposals/ledger-robinhood-profile.json), [test_ledger_robinhood_profile.py:76-96](../../../../tests/deployment_profiles/test_ledger_robinhood_profile.py#L76)) | Ledger address/code hash, getter result, chain/block hash |
| Stored user identity | `Ledger.lastTouch(user)`; successful calls write the selected action-block identity ([Ledger.vy:233-245](../../../../contracts/data/Ledger.vy#L233)) | User, value, transaction/block hash |
| ArbSys child number | Exact raw call to `arbBlockNumber()` at `0x64`, with exactly 32 returned bytes ([Ledger.vy:211-222](../../../../contracts/data/Ledger.vy#L211)); Offchain Labs' pinned interface defines `arbBlockNumber()` as the Arbitrum block number ([ArbSys.sol at `e7e6566`](https://github.com/OffchainLabs/nitro-precompile-interfaces/blob/e7e6566ae5b0efa0ad4d779138f64ead11928c66/ArbSys.sol)) | Calldata, raw response/length, decoded value, block/hash |
| Native ancestor estimate | EVM `NUMBER`/`block.number`; Offchain Labs documents it as an approximate first non-Arbitrum ancestor number and shows repeats and jumps ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Native value observed in the same transaction/block context |
| Child receipt number | Standard transaction receipt `blockNumber`; Offchain Labs documents that RPC receipt field as the child-chain block number ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Receipt block number/hash and transaction index |
| Guard rejection | Revert `one action per block` from `checkAndUpdateLastTouch(user,true,...)` when stored identity equals current selected identity ([Ledger.vy:233-245](../../../../contracts/data/Ledger.vy#L233)) | Caller, user, selector, revert bytes, receipt/trace |
| Source failure | Revert/missing/malformed `0x64` response; the implementation has no native fallback and local tests require rollback ([Ledger.vy:211-230](../../../../contracts/data/Ledger.vy#L211), [test_ledger_action_block.py:221-251](../../../../tests/data/test_ledger_action_block.py#L221)) | Raw call result, Ledger transaction receipt/trace, unchanged `lastTouch` |
| Pause/authority/lock | Ledger pause state, Teller caller binding, `isLockedAccount(user)`, and failed call evidence ([Ledger.vy:233-248](../../../../contracts/data/Ledger.vy#L233), [test_ledger_action_block.py:254-318](../../../../tests/data/test_ledger_action_block.py#L254)) | Getter values and complete call evidence |

## 2. Threshold logic

| Condition | Concrete threshold/formula and derivation | Severity |
| --- | --- | --- |
| RH source mismatch | `ACTION_BLOCK_SOURCE != 0x64`; the draft RH profile gate accepts only exact `0x64` ([ledger_robinhood_profile.py:169-177](../../../../scripts/proposals/ledger_robinhood_profile.py#L169)) | Critical immediately |
| ArbSys malformed/unavailable | One failure, revert, or response length other than 32; Ledger requires exact success on every ArbSys-mode read ([Ledger.vy:211-222](../../../../contracts/data/Ledger.vy#L211)) | Critical immediately |
| Child regression | For finalized observations ordered by chain position: `child[i] < child[i-1]`; official documentation says child block numbers update sequentially ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Critical immediately |
| Child repeat | `child[i] == child[i-1]` is expected for multiple transactions observed in one child block; a second checked action for the same user must reject, while different users remain independent ([Ledger.vy:240-245](../../../../contracts/data/Ledger.vy#L240), [test_ledger_action_block.py:180-218](../../../../tests/data/test_ledger_action_block.py#L180)) | Alert only if contract outcome contradicts the equality rule |
| Child jump | `child[i] > child[i-1] + 1` means the monitor missed one or more child blocks unless the node itself reports inconsistent ancestry; child blocks are sequential but production depends on chain usage ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Sampling warning; page-size/time threshold **UNRESOLVED — owner decision** |
| Native repeat/jump | No fixed ratio threshold: official examples show repeated ancestor estimates and later jumps while multiple child blocks can correspond to one parent block ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Informational unless native value is used as RH `lastTouch` |
| Stored identity mismatch | After a successful RH touch, `lastTouch(user) != ArbSys child number observed by the transaction` ([Ledger.vy:238-245](../../../../contracts/data/Ledger.vy#L238), [test_ledger_action_block.py:141-162](../../../../tests/data/test_ledger_action_block.py#L141)) | Critical immediately |
| Unexpected success/revert | Same user + same child + checked call succeeds, or different child + otherwise valid checked call reverts `one action per block` ([Ledger.vy:240-245](../../../../contracts/data/Ledger.vy#L240)) | Critical immediately |
| Error volume | Count/window for otherwise expected same-child guard reverts is operational, not a protocol invariant | **UNRESOLVED — owner decision** |

## 3. Expected chain topology and anomalous states

As checked on 29 July 2026, Offchain Labs' primary documentation states that child
blocks have their own sequential numbers, that multiple child blocks may occur
within one parent block, that one child block cannot span parent blocks, and
that `block.number` is only an approximate first non-Arbitrum ancestor value
([Arbitrum block-number reference](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)).
The expected topology is therefore:

```text
transaction order:       t0   t1   t2   t3   t4
child receipt / ArbSys:  700  700  701  702  703
native ancestor estimate:900  900  900  904  904
```

The repeated child value represents multiple transactions in one child block;
the child sequence advances one per distinct child block; the native ancestor
estimate may repeat and then jump
([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)).
Ledger RH intentionally stores the child value, not the native estimate
([Ledger.vy:225-245](../../../../contracts/data/Ledger.vy#L225)).

| Expected | Anomalous |
| --- | --- |
| Multiple transactions share one child identity; one checked action per user succeeds and another for that user rejects, while users are isolated ([test_ledger_action_block.py:180-218](../../../../tests/data/test_ledger_action_block.py#L180)) | Same-user same-child checked success, cross-user coupling, or a stored native ancestor estimate in RH mode |
| Distinct finalized child blocks increase sequentially; missed sampling can appear as a positive gap ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Finalized child regression, ArbSys/receipt disagreement in one transaction, or an unexplained gap reproduced from a complete node range |
| Native ancestor estimates repeat/jump and need not equal child numbers ([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)) | Monitoring treats native `NUMBER` as the RH guard identity or pages merely because it repeats |
| An ArbSys error reverts with no write and no native fallback ([test_ledger_action_block.py:221-251](../../../../tests/data/test_ledger_action_block.py#L221)) | A failed/malformed ArbSys read is followed by successful housekeeping or changed `lastTouch` |

Local tests simulate topology and malformed responses; they are not
real-network ArbSys/topology qualification
([ledger.md, test invariant matrix](../smart-contract-changes/ledger.md#test-invariant-matrix)).

## 4. Pause, escalation, and recovery

| Step | Required action and evidence | Authority |
| --- | --- | --- |
| 1. Confirm | Pin Ledger code hash/source getter, then collect the Ledger call/receipt, `lastTouch`, raw ArbSys response, receipt child number, and native ancestor estimate at the same block context. Sources are listed in Section 1. | Read authority: **UNRESOLVED — owner decision** |
| 2. Classify | Separate source failure, topology anomaly, same-child expected guard rejection, pause/lock, unauthorized caller, and monitor sampling gaps. The contract has distinct guards for source, Teller, pause, equality, and lock ([Ledger.vy:211-248](../../../../contracts/data/Ledger.vy#L211)). | Incident classifier: **UNRESOLVED — owner decision** |
| 3. Contain | Stop affected submissions and prepare the smallest applicable pause; never substitute native `NUMBER` or change the immutable in place. The implementation deliberately has no native fallback ([Ledger.vy:225-230](../../../../contracts/data/Ledger.vy#L225), [test_ledger_action_block.py:221-251](../../../../tests/data/test_ledger_action_block.py#L221)). | Pause signer/quorum: **UNRESOLVED — owner decision** |
| 4. Escalate | Preserve endpoint/node identity, finalized range, raw RPC responses, block/transaction hashes, Ledger inputs/revert bytes, affected users/actions, and whether repayment/liquidation paths were blocked. Runtime source failure can block housekeeping-dependent actions ([ledger.md, ArbSys mode](../smart-contract-changes/ledger.md#arbsys-mode)). | Protocol/security/chain-provider contacts: **UNRESOLVED — owner decision** |
| 5. Recover | Require an owner-approved chain/source remedy, then replay exact-response, repeated-child, next-child, user-isolation, pause/lock, and full route checks against the intended release snapshot before proposing unpause. The local invariant set is enumerated in the Ledger record ([ledger.md, test invariant matrix](../smart-contract-changes/ledger.md#test-invariant-matrix)). | Recovery and unpause signer/quorum: **UNRESOLVED — owner decision** |
| 6. Close | Attach before/after code/source identities, range evidence, commands/environment, all failed/successful receipts, and restored monitors. | Closure approver/retention: **UNRESOLVED — owner decision** |

## 5. Residual risk after recovery

Constructor probing proves only that `0x64` responded correctly at deployment;
a later system-contract outage or chain upgrade can still break runtime reads
([Ledger.vy:189-222](../../../../contracts/data/Ledger.vy#L189),
[ledger.md, ArbSys mode](../smart-contract-changes/ledger.md#arbsys-mode)).
Ledger enforces equality, not monotonicity, so it relies on the selected source
and chain topology being truthful
([Ledger.vy:240-245](../../../../contracts/data/Ledger.vy#L240),
[test_ledger_action_block.py:165-177](../../../../tests/data/test_ledger_action_block.py#L165)).
Offline doubles do not replace live-network qualification, monitoring
installation, authority binding, or consumer-owner sign-off
([ledger.md, recommended changes](../smart-contract-changes/ledger.md#recommended-changes)).
