# SwitchboardAlpha exact headroom waiver

**Decision:** RH-D030
**Owner disposition:** replacement accepted on 13 August 2026
**Scope:** exact aggregate audit-remediation SwitchboardAlpha artifact only

## Decision

The normal production-contract rule requires at least 200 bytes of deployed
EIP-170 headroom. The prior 40-byte RH-D030 identity reopened when
SwitchboardAlpha changed. After reviewing the aggregate CI result, the owner
explicitly accepts the replacement exact artifact below at 24,574 deployed
bytes, leaving 2 bytes.

This artifact completes the symmetric cross-field debt-config invariant:
`setBorrowIntervalConfig` and `setGlobalDebtLimits` both enforce
`minDebtAmount <= maxBorrowPerInterval` against the resolved MissionControl
target at proposal time and revalidate the invariant at execution time. Removing
either validation to recover size is not accepted.

The aggregate artifact also keeps priority-vault validity policy in
SwitchboardAlpha and revalidates pending priority liquidation entries at
execution. Removing that validation to recover size is likewise not accepted.

## Exact identity

| Identity | Value |
| --- | --- |
| Source SHA-256 | `a967459ca6711cb67f66af6bbdb8c7a7af517a1587b7ca0aa5146ad318efcfa9` |
| Runtime-template SHA-256 | `e378970cbf4ea05049dfcb45e2d542f05720fddfd133482418c47590afe7f4b0` |
| Runtime-template bytes | 24,350 |
| Immutable bytes | 224 (seven words) |
| Deployed runtime bytes | 24,574 |
| EIP-170 headroom | 2 bytes |
| Deterministic deployed-runtime SHA-256 | `32787aab311b5535e57492437a0c51e31f8c5226f8c205dc953d6111c05ba6c4` |

The deterministic identity deployment uses RipeHq
`0x00000000000000000000000000000000000000A1`, temporary governance
`0x00000000000000000000000000000000000000A2`, governance
`0x00000000000000000000000000000000000000A3`, stale-block bounds 1 and 2,
governance timelock bounds 1 and 2, and config timelock bounds 1 and 2. These
values bind the reproducibility test only; they are not production deployment
authority.

## Boundary and reopening rule

- The 200-byte rule remains unchanged for every non-waived contract.
- This waiver permits zero bytes of SwitchboardAlpha growth.
- Any source change, runtime-template change, complete deployed-byte change, or
  size change invalidates this waiver, even when the remaining headroom is still
  2 bytes.
- A later SwitchboardAlpha change must first recover at least 200 bytes or obtain
  a new exact owner waiver.
- Updating the pinned hashes solely to make CI pass is prohibited.

No deployment, configuration, activation, or release authority is granted by
this record.
