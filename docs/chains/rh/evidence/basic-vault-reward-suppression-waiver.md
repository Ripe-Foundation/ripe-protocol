# BasicVault reward suppression and replacement exact CreditEngine waiver

**Decision:** owner accepted B-AUD-008 on 13 August 2026 and granted the latest
replacement exact RH-D029 waiver on 13 August 2026 for the combined B-AUD-008,
B-OBS-045 / AUD-010, and CreditRedeem price-isolation CreditEngine artifact.

**Scope:** exact current CreditEngine artifact after integration of PR #131 at
`778cf2a5b3f59199971f0a5b60527af42150894e`.

**Original review base:** `f9152f27ab8b14ede0ce562974430d57168960b0`

**Original B-AUD-008 PR target base:**
`c3bc780d5b3b59193389c917fd6543312f5ee6c3`

**Replacement composition base:** `f937cbae239913e448c61abfdb0e8f561cdd9ee8`

**Lifecycle authority:** the owner's 13 August 2026 express grant of the latest
replacement ten-byte waiver authorizes these governing-record updates and the
branch push for this exact artifact. It does not authorize deployment,
configuration, activation, or release.

## Accepted behavior

When a BasicVault's actual token custody is below its nominal total balances,
`getUserLootBoxShare` returns zero for every affected user without mutating the
nominal user or vault ledger. Restoring custody automatically restores the
current reward share. Configured reward allocations and points already recorded
in Lootbox are not rewritten.

CreditEngine does not use the suppressed reward getter as a position oracle.
For a zero usable amount, it requires both a vault-wide zero usable amount and a
nominal position reported by `doesUserHaveBalance` before marking the account as
having quarantined collateral. This preserves quarantine behavior while keeping
reward accounting separate from collateral and forced-action eligibility.

Standard repayments distinguish the debtor from the payer supplying GREEN or
sGREEN. When repayment is capped at the debtor's outstanding debt, the exact
surplus returns to the payer. Self-repayment, auction repayment, department
repayment, permission checks, refund-token selection, event ABI, ordering, and
atomic rollback remain unchanged.

CreditRedeem requests non-strict borrower terms so one unpriceable entry does
not abort the full batch. CreditEngine marks a positive debt-bearing collateral
position with no usable price as quarantined, causing CreditRedeem to skip that
entry while preserving strict final debt-health recalculation and all-skipped
rollback.

## Exact production-source identities

| Source | SHA-256 |
| --- | --- |
| `contracts/vaults/modules/BasicVault.vy` | `414d4565a07d0b4042c356a6f383d4c5ba968781e6202a262b28a9017c7e38c0` |
| `contracts/core/CreditEngine.vy` | `98001bce0f07992bdc51e4dede81fce5fbccbdaf9862c3ecef7694f6a2bd4f3f` |

## Exact CreditEngine size waiver

The standard 200-byte headroom policy remains unchanged. The owner accepted a
replacement exception for this exact combined CreditEngine version. It
supersedes the prior four-byte identity and is not cumulative:

| Identity | Value |
| --- | --- |
| EIP-170 limit | 24,576 bytes |
| Runtime template | 24,470 bytes |
| Runtime-template SHA-256 | `0cf18bd4121836b960abff777f3bca468c7fbaaad7b18e5601c9d5e5af870d91` |
| Deployed runtime, including 96 immutable bytes | 24,566 bytes |
| Remaining headroom | **10 bytes** |
| Complete deployed-runtime SHA-256 at deterministic HQ `0x00000000000000000000000000000000000000A1` | `4f410105098b45e93a418afbbc6f49b4154528cdc8253543f37b271b6ba03820` |

The deterministic HQ is a reproducibility input, not a production address. The
waiver permits zero growth. Any source, compiler-output, runtime-template,
deployed-size, constructor-bound deployed-code, or relevant toolchain change
invalidates this identity and requires either restoration of at least 200 bytes
of headroom or another express owner decision.

## Governed artifact refresh

The current integration artifact was captured from its clean rebased source using the
repository's deterministic 18-contract Boa deployment graph. The targeted
artifact updater regenerated the CreditEngine record from that captured runtime;
the governed-ledger CreditEngine record binds that captured runtime. The
ledger's captured CreditEngine deployed hash uses its declared
production-capture HQ; the waiver hash above uses the separate deterministic
`0x…00A1` HQ required by the exact-waiver test.

The controlling machine records are:

- `config/contract-artifact-expectations.json`;
- `tests/inventory/test_contract_artifacts.py`; and
- `tests/test_vault_pointer_runtime_sizes.py`.

## Validation boundary

The focused package covers current reward-share suppression and recovery,
nominal-state preservation, zero-LTV reward-only shortfall behavior, normalized
share checkpointing, configured-allocation preservation, quarantine detection
and recovery, borrow/withdraw/liquidation/redemption/deleverage containment,
healthy-asset continuity, rounding dust, backing-observation failures, and the
bounded-gas zero-amount path. The combined gate also covers payer-directed
GREEN/sGREEN refunds, maximum-payment handling, interest, permissions, complete
refund-failure rollback, real-auction behavior, and department repayment. Exact
command results are recorded in the task handoff; this record does not convert
local test evidence into deployment or release authority.
