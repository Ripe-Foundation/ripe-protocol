# SwitchboardAlpha exact headroom waiver

**Decision:** RH-D030
**Owner disposition:** replacement accepted on 13 August 2026
**Scope:** exact trimmed audit-remediation SwitchboardAlpha artifact only

## Decision

The normal production-contract rule requires at least 200 bytes of deployed
EIP-170 headroom. The prior 2-byte RH-D030 identity reopened when
SwitchboardAlpha changed. The owner explicitly accepts the replacement exact
artifact below at 24,468 deployed bytes, leaving 108 bytes.

This artifact completes the symmetric cross-field debt-config invariant:
`setBorrowIntervalConfig` and `setGlobalDebtLimits` both enforce
`minDebtAmount <= maxBorrowPerInterval` against the resolved MissionControl
target at proposal time and revalidate the invariant at execution time. Removing
either validation to recover size is not accepted.

The replacement keeps priority-vault validity policy in SwitchboardAlpha and
revalidates pending priority liquidation entries at execution. It removes the
single-consumer `MissionControl.getVaultConfigFlags()` helper, reads the three
existing vault predicates directly, and validates each priority-vault list in
one pass. Removing validation to recover more size is not accepted.

## Exact identity

| Identity | Value |
| --- | --- |
| Source SHA-256 | `51aab6ff276c9fe85f323899356f6bf7e722782cd969e30d3719612677fa24d5` |
| Runtime-template SHA-256 | `eec69265f4cfa7157bcf97b16ab05ec8cd3721a04d2659ea0d25bf16f5dce7c9` |
| Runtime-template bytes | 24,244 |
| Immutable bytes | 224 (seven words) |
| Deployed runtime bytes | 24,468 |
| EIP-170 headroom | 108 bytes |
| Deterministic deployed-runtime SHA-256 | `475d777c48ab2671e6f19967db1ebb8304de590a3e71413da2fec84acff59055` |

The deterministic identity deployment uses RipeHq
`0x00000000000000000000000000000000000000A1`, temporary governance
`0x00000000000000000000000000000000000000A2`, governance
`0x00000000000000000000000000000000000000A3`, stale-block bounds 1 and 2,
governance timelock bounds 1 and 2, and config timelock bounds 1 and 2. These
values bind the reproducibility test only; they are not production deployment
authority.

The source digest above corrects a transcription error in the original record.
The source introduced by waiver commit `6636806960c65a34bf724af110a2fdd340bebbe6`
has this digest; the runtime-template and deterministic deployed-runtime
identities are unchanged. This correction does not expand the waiver.

## Boundary and reopening rule

- The 200-byte rule remains unchanged for every non-waived contract.
- This waiver permits zero bytes of SwitchboardAlpha growth.
- Any source change, runtime-template change, complete deployed-byte change, or
  size change invalidates this waiver, even when the remaining headroom is still
  108 bytes.
- A later SwitchboardAlpha change must first recover at least 200 bytes or obtain
  a new exact owner waiver.
- Updating the pinned hashes solely to make CI pass is prohibited.

No deployment, configuration, activation, or release authority is granted by
this record.
