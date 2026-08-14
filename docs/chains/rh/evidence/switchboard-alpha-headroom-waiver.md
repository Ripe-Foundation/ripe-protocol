# SwitchboardAlpha exact headroom waiver

**Decision:** RH-D030
**Owner disposition:** accepted on 13 August 2026
**Scope:** exact audit-remediation SwitchboardAlpha artifact only

## Decision

The normal production-contract rule requires at least 200 bytes of deployed
EIP-170 headroom. The owner explicitly accepts the exact SwitchboardAlpha
artifact below at 24,536 deployed bytes, leaving 40 bytes.

This artifact completes the symmetric cross-field debt-config invariant:
`setBorrowIntervalConfig` and `setGlobalDebtLimits` both enforce
`minDebtAmount <= maxBorrowPerInterval` against the resolved MissionControl
target at proposal time and revalidate the invariant at execution time. Removing
either validation to recover size is not accepted.

## Exact identity

| Identity | Value |
| --- | --- |
| Source SHA-256 | `15b1e727a4235ac2f16dd93c6fb0cc991d4ee96a3ac8d4cf4ac41d71e0e7f19d` |
| Runtime-template SHA-256 | `7e117940f163fc2205fa43beeedb4b71cfea70e9d0bc9304eb909cce76e65dab` |
| Runtime-template bytes | 24,312 |
| Immutable bytes | 224 (seven words) |
| Deployed runtime bytes | 24,536 |
| EIP-170 headroom | 40 bytes |
| Deterministic deployed-runtime SHA-256 | `450ac384bf51aa63e882f51dd042803dff8390739c98eaac2d421a208bb3dbac` |

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
  40 bytes.
- A later SwitchboardAlpha change must first recover at least 200 bytes or obtain
  a new exact owner waiver.
- Updating the pinned hashes solely to make CI pass is prohibited.

No deployment, configuration, activation, or release authority is granted by
this record.
