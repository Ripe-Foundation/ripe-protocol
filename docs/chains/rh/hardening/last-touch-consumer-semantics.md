# `lastTouch` consumer semantics

> **DRAFT — consumer sign-off aid, not a deployment or interface change.**
> `lastTouch(address)` retains a `uint256` getter but its meaning depends on the
> immutable source selected when Ledger is deployed
> ([Ledger.vy:130-135](../../../../contracts/data/Ledger.vy#L130),
> [Ledger.vy:225-245](../../../../contracts/data/Ledger.vy#L225)).

## Semantic contract

`lastTouch[user]` is the **deployment-selected action-block identity**:

| Deployment mode | Stored identity | Source |
| --- | --- | --- |
| `ACTION_BLOCK_SOURCE == 0x0000000000000000000000000000000000000000` | Native EVM `block.number` ([Ledger.vy:225-230](../../../../contracts/data/Ledger.vy#L225)) | Current native-mode test proves getter zero and stored native number ([test_ledger_action_block.py:79-99](../../../../tests/data/test_ledger_action_block.py#L79)) |
| `ACTION_BLOCK_SOURCE == 0x0000000000000000000000000000000000000064` | Exact 32-byte decoded `ArbSys.arbBlockNumber()` child-chain number ([Ledger.vy:211-230](../../../../contracts/data/Ledger.vy#L211)) | Current ArbSys-mode test proves a held child number controls equality even while the native number advances ([test_ledger_action_block.py:141-162](../../../../tests/data/test_ledger_action_block.py#L141)) |

It is therefore **not universally the EVM `NUMBER` opcode**. Offchain Labs
documents `block.number` on an Arbitrum chain as an approximate first
non-Arbitrum ancestor number, while `ArbSys(100).arbBlockNumber()` returns the
child-chain number
([Arbitrum block-number reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time)).

The value is equality-bucket identity, not elapsed time, duration, or guaranteed
monotonic application state. Ledger rejects a checked action only when the
stored identity equals the current selected identity, and the maintained test
intentionally proves a different lower ArbSys value is accepted
([Ledger.vy:238-245](../../../../contracts/data/Ledger.vy#L238),
[test_ledger_action_block.py:165-177](../../../../tests/data/test_ledger_action_block.py#L165)).

Unchecked touches still write the current selected identity; a later checked
touch for the same user in the same identity rejects. Different users have
independent mapping keys
([Ledger.vy:233-245](../../../../contracts/data/Ledger.vy#L233),
[test_ledger_action_block.py:180-218](../../../../tests/data/test_ledger_action_block.py#L180)).

## Consumer requirements

Every in-repository or external consumer must:

- read `ACTION_BLOCK_SOURCE()` before interpreting `lastTouch`, because the
  getter value alone does not encode its domain
  ([Ledger.vy:130-135](../../../../contracts/data/Ledger.vy#L130));
- compare identities only for the one-action equality policy and never convert
  `lastTouch` to seconds, wall time, or an ancestor-chain height
  ([Ledger.vy:233-245](../../../../contracts/data/Ledger.vy#L233));
- in RH mode, label the value `ArbSys child action block`, not `EVM block
  number`, `parent block`, or `timestamp`
  ([Ledger.vy:211-230](../../../../contracts/data/Ledger.vy#L211),
  [pinned ArbSys interface](https://github.com/OffchainLabs/nitro-precompile-interfaces/blob/e7e6566ae5b0efa0ad4d779138f64ead11928c66/ArbSys.sol));
- tolerate repeated identities for multiple transactions in one child block
  and reject assumptions that native ancestor estimates and child numbers move
  one-for-one
  ([Arbitrum reference, accessed 2026-07-29](https://docs.arbitrum.io/arbitrum-essentials/arbitrum-vs-ethereum/block-numbers-and-time));
- treat a failed/malformed ArbSys read as a failed Ledger action with no native
  fallback or successful touch
  ([Ledger.vy:211-230](../../../../contracts/data/Ledger.vy#L211),
  [test_ledger_action_block.py:221-251](../../../../tests/data/test_ledger_action_block.py#L221)); and
- preserve both existing `checkAndUpdateLastTouch(address,bool)` and
  `checkAndUpdateLastTouch(address,bool,address)` selectors; both reach the same
  Teller-gated body in current source and are pinned by the dual-selector test
  ([Ledger.vy:233-248](../../../../contracts/data/Ledger.vy#L233),
  [test_ledger_action_block.py:450-481](../../../../tests/data/test_ledger_action_block.py#L450)).

## Owner gate

Consumer-owner sign-off is **UNRESOLVED — owner decision**. Before release,
each owner must identify its consumer, version, displayed/derived field,
selected Ledger deployment mode, interpretation, alert behavior, and evidence
that no universal-EVM-`NUMBER` assumption remains. The Ledger record identifies
external consumer assumptions as a release confirmation item
([ledger.md, ABI and storage](../smart-contract-changes/ledger.md#abi-and-storage)).
